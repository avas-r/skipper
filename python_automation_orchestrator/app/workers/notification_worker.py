"""
Notification worker for sending notifications.

This worker periodically checks for pending notifications and sends them.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import json
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..config import settings
from ..db.session import SessionLocal
from ..models import Notification, NotificationChannel

logger = logging.getLogger(__name__)

class NotificationWorker:
    """Worker for sending notifications"""
    
    def __init__(self):
        """Initialize the worker"""
        self.check_interval = 30  # Check every 30 seconds
        self.running = False
        self.db = None
        self.batch_size = 50  # Process up to 50 notifications at a time
    
    async def run(self):
        """Run the worker in a loop"""
        logger.info("Starting notification worker")
        self.running = True
        
        try:
            while self.running:
                try:
                    # Create a new database session for each check
                    self.db = SessionLocal()
                    
                    # Process pending notifications
                    await self._process_notifications()
                    
                finally:
                    # Close database session
                    if self.db:
                        self.db.close()
                        self.db = None
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Notification worker cancelled")
            self.running = False
            
        except Exception as e:
            logger.exception(f"Unexpected error in notification worker: {e}")
            self.running = False
            
        finally:
            # Clean up
            if self.db:
                self.db.close()
                
            logger.info("Notification worker stopped")
    
    async def _process_notifications(self):
        """Process pending notifications"""
        if not self.db:
            logger.error("No database session available")
            return
        
        try:
            # Find pending notifications
            pending_notifications = self.db.query(Notification).filter(
                Notification.status == "pending"
            ).order_by(
                Notification.created_at  # Oldest first
            ).limit(self.batch_size).all()
            
            if not pending_notifications:
                return
                
            logger.info(f"Found {len(pending_notifications)} pending notifications")
            
            # Process each pending notification
            for notification in pending_notifications:
                await self._send_notification(notification)
                
        except Exception as e:
            logger.error(f"Error processing notifications: {e}")
            # Roll back transaction
            self.db.rollback()
    
    async def _send_notification(self, notification):
        """
        Send a notification.
        
        Args:
            notification: Notification to send
        """
        try:
            # Get notification rule
            rule = notification.rule
            
            # Get notification channel
            channel = rule.channel
            
            # Send notification based on channel type
            result = await self._send_via_channel(
                channel, 
                notification.subject, 
                notification.message, 
                notification.metadata or {}
            )
            
            # Update notification status
            if result:
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = "failed"
                
            self.db.commit()
            
            logger.info(
                f"Notification {notification.notification_id} {notification.status}: "
                f"{notification.subject}"
            )
            
        except Exception as e:
            logger.error(f"Error sending notification {notification.notification_id}: {e}")
            
            # Update notification status
            notification.status = "failed"
            notification.metadata = notification.metadata or {}
            notification.metadata["error"] = str(e)
            
            # Commit changes
            self.db.commit()
    
    async def _send_via_channel(self, channel, subject, message, metadata):
        """
        Send notification via a specific channel.
        
        Args:
            channel: Notification channel
            subject: Notification subject
            message: Notification message
            metadata: Notification metadata
            
        Returns:
            bool: True if notification was sent successfully
        """
        if channel.type == "email":
            return await self._send_email(channel, subject, message, metadata)
        elif channel.type == "slack":
            return await self._send_slack(channel, subject, message, metadata)
        elif channel.type == "webhook":
            return await self._send_webhook(channel, subject, message, metadata)
        else:
            logger.warning(f"Unsupported notification channel type: {channel.type}")
            return False
    
    async def _send_email(self, channel, subject, message, metadata):
        """
        Send notification via email.
        
        Args:
            channel: Email notification channel
            subject: Notification subject
            message: Notification message
            metadata: Notification metadata
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Get channel configuration
            config = channel.configuration
            recipient = config.get("recipient_email")
            
            if not recipient:
                logger.error(f"Missing recipient email in channel configuration: {channel.channel_id}")
                return False
            
            # Create email
            smtp_server = "smtp.example.com"  # Would come from settings
            smtp_port = 587
            smtp_username = "noreply@example.com"
            smtp_password = "password"
            
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = "Orchestrator <noreply@example.com>"
            msg["To"] = recipient
            msg["Subject"] = subject
            
            # Add HTML body
            html_body = f"""
            <html>
                <body>
                    <h2>{subject}</h2>
                    <p>{message}</p>
                </body>
            </html>
            """
            msg.attach(MIMEText(html_body, "html"))
            
            # In a real implementation, we would send the email here
            # For now, just log it
            logger.info(f"Would send email to {recipient}: {subject}")
            
            # Simulate successful sending
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    async def _send_slack(self, channel, subject, message, metadata):
        """
        Send notification via Slack.
        
        Args:
            channel: Slack notification channel
            subject: Notification subject
            message: Notification message
            metadata: Notification metadata
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Get channel configuration
            config = channel.configuration
            webhook_url = config.get("webhook_url")
            
            if not webhook_url:
                logger.error(f"Missing webhook URL in channel configuration: {channel.channel_id}")
                return False
            
            # Create Slack message
            slack_message = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": subject
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            # Add metadata if available
            if metadata:
                slack_message["blocks"].append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Additional Info:* {json.dumps(metadata)}"
                        }
                    ]
                })
            
            # In a real implementation, we would send the Slack message here
            # For now, just log it
            logger.info(f"Would send Slack message: {subject}")
            
            # Simulate successful sending
            return True
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    async def _send_webhook(self, channel, subject, message, metadata):
        """
        Send notification via webhook.
        
        Args:
            channel: Webhook notification channel
            subject: Notification subject
            message: Notification message
            metadata: Notification metadata
            
        Returns:
            bool: True if notification was sent successfully
        """
        try:
            # Get channel configuration
            config = channel.configuration
            url = config.get("url")
            method = config.get("method", "POST")
            
            if not url:
                logger.error(f"Missing URL in channel configuration: {channel.channel_id}")
                return False
            
            # Create webhook payload
            payload = {
                "subject": subject,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata
            }
            
            # In a real implementation, we would send the webhook here
            # For now, just log it
            logger.info(f"Would send webhook ({method}) to {url}: {subject}")
            
            # Simulate successful sending
            return True
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False