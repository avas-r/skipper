"""
Message handlers for asynchronous message processing.

This module contains handler functions for processing messages
from different queues.
"""

import logging
import json
from typing import Any, Dict

import aio_pika
from sqlalchemy.orm import Session

from ..db.session import SessionLocal
from ..services.job_service import JobService
from ..services.agent_service import AgentService
from ..services.notification_service import NotificationService
from ..services.queue_service import QueueService

logger = logging.getLogger(__name__)

async def job_execution_handler(data: Dict[str, Any], message: aio_pika.IncomingMessage):
    """
    Handler for job execution messages.
    
    Args:
        data: Message data
        message: RabbitMQ message object
    """
    action = data.get("action")
    execution_id = data.get("execution_id")
    job_id = data.get("job_id")
    tenant_id = data.get("tenant_id")
    
    if not action or not execution_id or not tenant_id:
        logger.error(f"Missing required fields in job execution message: {data}")
        return
        
    logger.info(f"Processing job execution message: {action} for job {job_id}, execution {execution_id}")
    
    # Create database session
    db = SessionLocal()
    try:
        # Create job service
        job_service = JobService(db)
        
        if action == "new_execution":
            # Process new job execution
            await job_service.process_execution(execution_id, tenant_id)
            
        elif action == "cancel_execution":
            # Cancel job execution
            await job_service.cancel_execution(execution_id, tenant_id)
            
        elif action == "update_execution":
            # Update job execution status
            status = data.get("status")
            error_message = data.get("error_message")
            results = data.get("results")
            
            if status:
                await job_service.update_execution_status(
                    execution_id,
                    tenant_id,
                    status,
                    error_message,
                    results
                )
            
    except Exception as e:
        logger.exception(f"Error processing job execution message: {e}")
        
    finally:
        db.close()

async def agent_message_handler(data: Dict[str, Any], message: aio_pika.IncomingMessage):
    """
    Handler for agent messages.
    
    Args:
        data: Message data
        message: RabbitMQ message object
    """
    action = data.get("action")
    agent_id = data.get("agent_id")
    tenant_id = data.get("tenant_id")
    
    if not action or not agent_id or not tenant_id:
        logger.error(f"Missing required fields in agent message: {data}")
        return
        
    logger.info(f"Processing agent message: {action} for agent {agent_id}")
    
    # Create database session
    db = SessionLocal()
    try:
        # Create agent service
        agent_service = AgentService(db)
        
        if action == "heartbeat":
            # Process agent heartbeat
            metrics = data.get("metrics", {})
            await agent_service.update_heartbeat(agent_id, tenant_id, metrics)
            
        elif action == "registration":
            # Process agent registration
            agent_data = data.get("agent_data", {})
            if agent_data:
                await agent_service.register_agent(agent_data, tenant_id)
            
        elif action == "status_change":
            # Update agent status
            status = data.get("status")
            if status:
                await agent_service.update_agent_status(agent_id, tenant_id, status)
            
    except Exception as e:
        logger.exception(f"Error processing agent message: {e}")
        
    finally:
        db.close()

async def notification_handler(data: Dict[str, Any], message: aio_pika.IncomingMessage):
    """
    Handler for notification messages.
    
    Args:
        data: Message data
        message: RabbitMQ message object
    """
    notification_id = data.get("notification_id")
    tenant_id = data.get("tenant_id")
    
    if not notification_id or not tenant_id:
        logger.error(f"Missing required fields in notification message: {data}")
        return
        
    logger.info(f"Processing notification message for notification {notification_id}")
    
    # Create database session
    db = SessionLocal()
    try:
        # Create notification service
        notification_service = NotificationService(db)
        
        # Send notification
        await notification_service.send_notification(notification_id, tenant_id)
        
    except Exception as e:
        logger.exception(f"Error processing notification message: {e}")
        
    finally:
        db.close()

async def queue_item_handler(data: Dict[str, Any], message: aio_pika.IncomingMessage):
    """
    Handler for queue item messages.
    
    Args:
        data: Message data
        message: RabbitMQ message object
    """
    action = data.get("action")
    queue_id = data.get("queue_id")
    item_id = data.get("item_id")
    tenant_id = data.get("tenant_id")
    
    if not action or not queue_id or not tenant_id:
        logger.error(f"Missing required fields in queue item message: {data}")
        return
        
    logger.info(f"Processing queue item message: {action} for queue {queue_id}, item {item_id}")
    
    # Create database session
    db = SessionLocal()
    try:
        # Create queue service
        queue_service = QueueService(db)
        
        if action == "new_item":
            # Process new queue item
            await queue_service.process_queue_item(item_id, tenant_id)
            
        elif action == "update_item":
            # Update queue item status
            status = data.get("status")
            error_message = data.get("error_message")
            
            if status:
                await queue_service.update_queue_item_status(
                    item_id,
                    tenant_id,
                    status,
                    error_message
                )
            
    except Exception as e:
        logger.exception(f"Error processing queue item message: {e}")
        
    finally:
        db.close()

async def event_handler(data: Dict[str, Any], message: aio_pika.IncomingMessage):
    """
    Handler for system events.
    
    Args:
        data: Message data
        message: RabbitMQ message object
    """
    event_type = data.get("event_type")
    
    if not event_type:
        logger.error(f"Missing event_type in event message: {data}")
        return
        
    logger.info(f"Processing event: {event_type}")
    
    # Create database session
    db = SessionLocal()
    try:
        # Handle different event types
        if event_type == "job_execution_status_change":
            # Process job execution status change event
            execution_id = data.get("execution_id")
            tenant_id = data.get("tenant_id")
            status = data.get("status")
            
            if execution_id and tenant_id and status:
                # Check if this should trigger a notification
                notification_service = NotificationService(db)
                await notification_service.check_notification_triggers(
                    "job_execution_status_change",
                    {
                        "execution_id": execution_id,
                        "tenant_id": tenant_id,
                        "status": status,
                        "additional_data": data.get("additional_data", {})
                    }
                )
                
        elif event_type == "agent_status_change":
            # Process agent status change event
            agent_id = data.get("agent_id")
            tenant_id = data.get("tenant_id")
            status = data.get("status")
            
            if agent_id and tenant_id and status:
                # Check if this should trigger a notification
                notification_service = NotificationService(db)
                await notification_service.check_notification_triggers(
                    "agent_status_change",
                    {
                        "agent_id": agent_id,
                        "tenant_id": tenant_id,
                        "status": status,
                        "additional_data": data.get("additional_data", {})
                    }
                )
            
    except Exception as e:
        logger.exception(f"Error processing event message: {e}")
        
    finally:
        db.close()