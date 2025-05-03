"""
Notification service for managing notifications and notification rules.

This module provides services for managing notifications, notification rules,
notification channels, and related operations.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from ..models import Notification, NotificationRule, NotificationChannel, NotificationType
from ..schemas.notification import (
   NotificationChannelCreate, NotificationChannelUpdate,
   NotificationRuleCreate, NotificationRuleUpdate
)
from ..messaging.producer import get_message_producer

logger = logging.getLogger(__name__)

class NotificationService:
   """Service for managing notifications and notification rules"""
   
   def __init__(self, db: Session):
       """Initialize with database session"""
       self.db = db
   
   # Notification methods
   def get_notification(self, notification_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Notification]:
       """Get notification by ID"""
       return self.db.query(Notification).filter(
           Notification.notification_id == notification_id,
           Notification.tenant_id == tenant_id
       ).first()
   
   def list_notifications(
       self,
       tenant_id: uuid.UUID,
       status: Optional[str] = None,
       reference_type: Optional[str] = None,
       reference_id: Optional[uuid.UUID] = None,
       skip: int = 0,
       limit: int = 100
   ) -> Tuple[List[Notification], int]:
       """List notifications with filtering"""
       query = self.db.query(Notification).filter(Notification.tenant_id == tenant_id)
       
       if status:
           query = query.filter(Notification.status == status)
       
       if reference_type:
           query = query.filter(Notification.reference_type == reference_type)
       
       if reference_id:
           query = query.filter(Notification.reference_id == reference_id)
       
       total = query.count()
       notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
       
       return notifications, total
   
   def mark_notification_read(self, notification_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Notification]:
       """Mark notification as read"""
       notification = self.get_notification(notification_id, tenant_id)
       
       if not notification:
           return None
       
       notification.status = "read"
       self.db.commit()
       self.db.refresh(notification)
       
       return notification
   
   async def create_notification(
       self,
       tenant_id: uuid.UUID,
       subject: str,
       message: str,
       reference_type: Optional[str] = None,
       reference_id: Optional[uuid.UUID] = None,
       metadata: Optional[Dict[str, Any]] = None,
       rule_id: Optional[uuid.UUID] = None
   ) -> Notification:
       """Create a new notification"""
       notification = Notification(
           notification_id=uuid.uuid4(),
           tenant_id=tenant_id,
           rule_id=rule_id,
           subject=subject,
           message=message,
           status="pending",
           reference_id=reference_id,
           reference_type=reference_type,
           metadata=metadata or {},
           created_at=datetime.utcnow()
       )
       
       self.db.add(notification)
       self.db.commit()
       self.db.refresh(notification)
       
       # Send notification to messaging system
       message_producer = get_message_producer()
       await message_producer.send_message(
           exchange="notifications",
           routing_key="notification.created",
           message_data={
               "notification_id": str(notification.notification_id),
               "tenant_id": str(tenant_id)
           }
       )
       
       return notification
   
   # Notification Channel methods
   def create_notification_channel(
       self,
       channel_in: NotificationChannelCreate,
       tenant_id: uuid.UUID,
       user_id: uuid.UUID
   ) -> NotificationChannel:
       """Create a new notification channel"""
       # Verify channel type is valid
       valid_types = ["email", "slack", "webhook", "in_app"]
       if channel_in.type not in valid_types:
           raise ValueError(f"Invalid channel type. Must be one of: {', '.join(valid_types)}")
       
       # Validate configuration
       self._validate_channel_config(channel_in.type, channel_in.configuration)
       
       # Create channel
       channel = NotificationChannel(
           channel_id=uuid.uuid4(),
           tenant_id=tenant_id,
           name=channel_in.name,
           type=channel_in.type,
           configuration=channel_in.configuration,
           created_by=user_id,
           created_at=datetime.utcnow(),
           updated_at=datetime.utcnow(),
           status="active"
       )
       
       self.db.add(channel)
       self.db.commit()
       self.db.refresh(channel)
       
       return channel
   
   def update_notification_channel(
       self,
       channel_id: uuid.UUID,
       channel_in: NotificationChannelUpdate,
       tenant_id: uuid.UUID,
       user_id: uuid.UUID
   ) -> Optional[NotificationChannel]:
       """Update a notification channel"""
       channel = self.get_notification_channel(channel_id, tenant_id)
       
       if not channel:
           return None
       
       # Update fields from input
       update_data = channel_in.dict(exclude_unset=True)
       
       # Validate configuration if provided
       if "configuration" in update_data and "type" in update_data:
           self._validate_channel_config(update_data["type"], update_data["configuration"])
       elif "configuration" in update_data:
           self._validate_channel_config(channel.type, update_data["configuration"])
       
       for key, value in update_data.items():
           setattr(channel, key, value)
       
       channel.updated_at = datetime.utcnow()
       
       self.db.commit()
       self.db.refresh(channel)
       
       return channel
   
   def delete_notification_channel(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
       """Delete a notification channel"""
       channel = self.get_notification_channel(channel_id, tenant_id)
       
       if not channel:
           return False
       
       # Check if channel is used by any rules
       rule_count = self.db.query(NotificationRule).filter(
           NotificationRule.channel_id == channel_id
       ).count()
       
       if rule_count > 0:
           raise ValueError(f"Cannot delete channel that is used by {rule_count} rules")
       
       self.db.delete(channel)
       self.db.commit()
       
       return True
   
   def get_notification_channel(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[NotificationChannel]:
       """Get notification channel by ID"""
       return self.db.query(NotificationChannel).filter(
           NotificationChannel.channel_id == channel_id,
           NotificationChannel.tenant_id == tenant_id
       ).first()
   
   def list_notification_channels(
       self,
       tenant_id: uuid.UUID,
       skip: int = 0,
       limit: int = 100
   ) -> Tuple[List[NotificationChannel], int]:
       """List notification channels"""
       query = self.db.query(NotificationChannel).filter(NotificationChannel.tenant_id == tenant_id)
       
       total = query.count()
       channels = query.order_by(NotificationChannel.name).offset(skip).limit(limit).all()
       
       return channels, total
   
   def test_notification_channel(self, channel_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
       """Test a notification channel by sending a test notification"""
       channel = self.get_notification_channel(channel_id, tenant_id)
       
       if not channel:
           return False
       
       # Create test message
       test_message = {
           "subject": "Test Notification",
           "message": "This is a test notification",
           "timestamp": datetime.utcnow().isoformat()
       }
       
       # Send test message (implementation depends on channel type)
       if channel.type == "email":
           # Mock sending email
           recipient = channel.configuration.get("recipient_email")
           if not recipient:
               return False
           
           logger.info(f"Would send test email to {recipient}")
           
       elif channel.type == "slack":
           # Mock sending Slack message
           webhook_url = channel.configuration.get("webhook_url")
           if not webhook_url:
               return False
               
           logger.info(f"Would send test Slack message to webhook")
           
       elif channel.type == "webhook":
           # Mock sending webhook
           url = channel.configuration.get("url")
           if not url:
               return False
               
           logger.info(f"Would send test webhook to {url}")
           
       elif channel.type == "in_app":
           # For in-app, actually create a notification
           self.db.add(Notification(
               notification_id=uuid.uuid4(),
               tenant_id=tenant_id,
               rule_id=None,
               subject="Test Notification",
               message="This is a test notification sent from the notification system.",
               status="pending",
               reference_type="test",
               created_at=datetime.utcnow()
           ))
           self.db.commit()
           
       return True
   
   # Notification Rule methods
   def create_notification_rule(
       self,
       rule_in: NotificationRuleCreate,
       tenant_id: uuid.UUID,
       user_id: uuid.UUID
   ) -> NotificationRule:
       """Create a new notification rule"""
       # Verify notification type exists
       notification_type = self.db.query(NotificationType).filter(
           NotificationType.type_id == rule_in.notification_type_id
       ).first()
       
       if not notification_type:
           raise ValueError("Invalid notification type")
       
       # Verify channel exists and belongs to tenant
       channel = self.db.query(NotificationChannel).filter(
           NotificationChannel.channel_id == rule_in.channel_id,
           NotificationChannel.tenant_id == tenant_id
       ).first()
       
       if not channel:
           raise ValueError("Invalid notification channel")
       
       # Create rule
       rule = NotificationRule(
           rule_id=uuid.uuid4(),
           tenant_id=tenant_id,
           name=rule_in.name,
           notification_type_id=rule_in.notification_type_id,
           channel_id=rule_in.channel_id,
           conditions=rule_in.conditions,
           created_by=user_id,
           created_at=datetime.utcnow(),
           updated_at=datetime.utcnow(),
           status="active"
       )
       
       self.db.add(rule)
       self.db.commit()
       self.db.refresh(rule)
       
       return rule
   
   def update_notification_rule(
       self,
       rule_id: uuid.UUID,
       rule_in: NotificationRuleUpdate,
       tenant_id: uuid.UUID,
       user_id: uuid.UUID
   ) -> Optional[NotificationRule]:
       """Update a notification rule"""
       rule = self.get_notification_rule(rule_id, tenant_id)
       
       if not rule:
           return None
       
       # Update fields from input
       update_data = rule_in.dict(exclude_unset=True)
       
       # Verify notification type if provided
       if "notification_type_id" in update_data:
           notification_type = self.db.query(NotificationType).filter(
               NotificationType.type_id == update_data["notification_type_id"]
           ).first()
           
           if not notification_type:
               raise ValueError("Invalid notification type")
       
       # Verify channel if provided
       if "channel_id" in update_data:
           channel = self.db.query(NotificationChannel).filter(
               NotificationChannel.channel_id == update_data["channel_id"],
               NotificationChannel.tenant_id == tenant_id
           ).first()
           
           if not channel:
               raise ValueError("Invalid notification channel")
       
       for key, value in update_data.items():
           setattr(rule, key, value)
       
       rule.updated_at = datetime.utcnow()
       
       self.db.commit()
       self.db.refresh(rule)
       
       return rule
   
   def delete_notification_rule(self, rule_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
       """Delete a notification rule"""
       rule = self.get_notification_rule(rule_id, tenant_id)
       
       if not rule:
           return False
       
       self.db.delete(rule)
       self.db.commit()
       
       return True
   
   def get_notification_rule(self, rule_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[NotificationRule]:
       """Get notification rule by ID"""
       return self.db.query(NotificationRule).filter(
           NotificationRule.rule_id == rule_id,
           NotificationRule.tenant_id == tenant_id
       ).options(
           joinedload(NotificationRule.notification_type),
           joinedload(NotificationRule.channel)
       ).first()
   
   def list_notification_rules(
       self,
       tenant_id: uuid.UUID,
       skip: int = 0,
       limit: int = 100
   ) -> Tuple[List[NotificationRule], int]:
       """List notification rules"""
       query = self.db.query(NotificationRule).filter(NotificationRule.tenant_id == tenant_id)
       
       total = query.count()
       rules = query.order_by(NotificationRule.name).offset(skip).limit(limit).options(
           joinedload(NotificationRule.notification_type),
           joinedload(NotificationRule.channel)
       ).all()
       
       return rules, total
   
   async def check_notification_triggers(self, event_type: str, event_data: Dict[str, Any]) -> List[Notification]:
       """Check and trigger notifications based on an event"""
       # Get notification type ID for event type
       notification_type = self.db.query(NotificationType).filter(
           NotificationType.name == event_type
       ).first()
       
       if not notification_type:
           return []
       
       # Get tenant ID from event data
       tenant_id = event_data.get("tenant_id")
       if not tenant_id:
           return []
       
       # Find matching rules
       rules = self.db.query(NotificationRule).filter(
           NotificationRule.notification_type_id == notification_type.type_id,
           NotificationRule.tenant_id == tenant_id,
           NotificationRule.status == "active"
       ).options(
           joinedload(NotificationRule.channel)
       ).all()
       
       notifications = []
       
       # Check each rule
       for rule in rules:
           # Check conditions
           if self._check_conditions(rule.conditions, event_data):
               # Create notification
               subject, message = self._generate_notification_message(notification_type.name, event_data)
               
               notification = await self.create_notification(
                   tenant_id=rule.tenant_id,
                   subject=subject,
                   message=message,
                   reference_type=event_type,
                   reference_id=event_data.get("id"),
                   metadata=event_data,
                   rule_id=rule.rule_id
               )
               
               notifications.append(notification)
       
       return notifications
   
   def _validate_channel_config(self, channel_type: str, config: Dict[str, Any]) -> None:
       """Validate channel configuration based on type"""
       if channel_type == "email":
           if "recipient_email" not in config:
               raise ValueError("Email channel requires recipient_email configuration")
               
       elif channel_type == "slack":
           if "webhook_url" not in config:
               raise ValueError("Slack channel requires webhook_url configuration")
               
       elif channel_type == "webhook":
           if "url" not in config:
               raise ValueError("Webhook channel requires url configuration")
           
           if "method" not in config:
               config["method"] = "POST"  # Default to POST
   
   def _check_conditions(self, conditions: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
       """Check if event data matches rule conditions"""
       for key, expected_value in conditions.items():
           # Handle nested keys with dot notation
           if "." in key:
               parts = key.split(".")
               actual_value = event_data
               for part in parts:
                   if isinstance(actual_value, dict) and part in actual_value:
                       actual_value = actual_value[part]
                   else:
                       return False
           else:
               if key not in event_data:
                   return False
               actual_value = event_data[key]
           
           # Compare values
           if isinstance(expected_value, list):
               # If expected value is a list, check if actual value is in the list
               if actual_value not in expected_value:
                   return False
           else:
               # Direct comparison
               if actual_value != expected_value:
                   return False
       
       return True
   
   def _generate_notification_message(self, event_type: str, event_data: Dict[str, Any]) -> Tuple[str, str]:
       """Generate notification subject and message based on event type and data"""
       # Default generic message
       subject = f"Notification: {event_type}"
       message = "An event occurred in the system."
       
       # Customize based on event type
       if event_type == "job_execution_status_change":
           job_id = event_data.get("job_id")
           status = event_data.get("status")
           
           # Get job name if available
           job_name = "Unknown"
           if job_id:
               from ..models import Job
               job = self.db.query(Job).filter(Job.job_id == job_id).first()
               if job:
                   job_name = job.name
           
           if status == "completed":
               subject = f"Job Completed: {job_name}"
               message = f"The job '{job_name}' has completed successfully."
           elif status == "failed":
               subject = f"Job Failed: {job_name}"
               error = event_data.get("error_message", "Unknown error")
               message = f"The job '{job_name}' has failed with the following error: {error}"
           else:
               subject = f"Job Status Update: {job_name}"
               message = f"The job '{job_name}' status has changed to {status}."
       
       elif event_type == "agent_status_change":
           agent_id = event_data.get("agent_id")
           status = event_data.get("status")
           
           # Get agent name if available
           agent_name = "Unknown"
           if agent_id:
               from ..models import Agent
               agent = self.db.query(Agent).filter(Agent.agent_id == agent_id).first()
               if agent:
                   agent_name = agent.name
           
           if status == "offline":
               subject = f"Agent Offline: {agent_name}"
               message = f"The agent '{agent_name}' is now offline."
           else:
               subject = f"Agent Status Update: {agent_name}"
               message = f"The agent '{agent_name}' status has changed to {status}."
       
       return subject, message