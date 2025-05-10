"""
Message producer module for asynchronous messaging.

This module provides a message producer for sending messages
to RabbitMQ or other message brokers.
"""

import json
import logging
import uuid
from typing import Any, Dict, Optional

import aio_pika
from aio_pika import Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection

from ..config import settings

logger = logging.getLogger(__name__)

class MessageProducer:
    """Message producer for sending messages to message broker"""
    
    def __init__(self):
        """Initialize the message producer"""
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.exchanges: Dict[str, aio_pika.abc.AbstractExchange] = {}
        
    async def connect(self):
        """Connect to the message broker"""
        try:
            # Create connection
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URI,
                client_properties={
                    "connection_name": "orchestrator_producer"
                }
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Declare exchanges
            exchanges = {
                "jobs": "direct",
                "agents": "direct",
                "notifications": "topic",
                "events": "topic"
            }
            
            for exchange_name, exchange_type in exchanges.items():
                self.exchanges[exchange_name] = await self.channel.declare_exchange(
                    exchange_name,
                    exchange_type,
                    durable=True
                )
                
            logger.info("Message producer connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def close(self):
        """Close the connection to the message broker"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("Message producer disconnected from RabbitMQ")
    
    async def send_message(
        self, 
        exchange: str, 
        routing_key: str, 
        message_data: Dict[str, Any],
        persistent: bool = True,
        message_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send a message to the message broker.
        
        Args:
            exchange: Exchange name
            routing_key: Routing key for the message
            message_data: Message data (will be converted to JSON)
            persistent: Whether the message should persist in the broker
            message_id: Optional message ID (if not provided, a UUID will be generated)
            correlation_id: Optional correlation ID for message tracking
            headers: Optional message headers
            
        Returns:
            str: Message ID
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        if exchange not in self.exchanges:
            raise ValueError(f"Exchange '{exchange}' not declared")
            
        # Generate message ID if not provided
        if not message_id:
            message_id = str(uuid.uuid4())
            
        # Prepare message
        message_body = json.dumps(message_data).encode()
        
        # Set delivery mode based on persistence
        delivery_mode = DeliveryMode.PERSISTENT if persistent else DeliveryMode.NOT_PERSISTENT
        
        # Create message
        message = Message(
            body=message_body,
            delivery_mode=delivery_mode,
            message_id=message_id,
            correlation_id=correlation_id,
            headers=headers
        )
        
        # Send message
        try:
            await self.exchanges[exchange].publish(
                message,
                routing_key=routing_key
            )
            logger.debug(f"Sent message to {exchange}:{routing_key}, ID: {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Failed to send message to {exchange}:{routing_key}: {e}")
            raise
    
    def send_message_sync(
        self, 
        exchange: str, 
        routing_key: str, 
        message_data: Dict[str, Any]
    ) -> bool:
        """
        Synchronous version of send_message for use in synchronous code.
        
        This should only be used when async/await cannot be used.
        
        Args:
            exchange: Exchange name
            routing_key: Routing key for the message
            message_data: Message data (will be converted to JSON)
            
        Returns:
            bool: True if message was sent successfully
        """
        import pika
        
        try:
            # Connect to RabbitMQ
            parameters = pika.URLParameters(settings.RABBITMQ_URI)
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Declare exchange
            channel.exchange_declare(
                exchange=exchange,
                exchange_type='direct' if exchange in ['jobs', 'agents'] else 'topic',
                durable=True
            )
            
            # Prepare message
            message_id = str(uuid.uuid4())
            message_body = json.dumps(message_data).encode()
            
            # Publish message
            channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    message_id=message_id,
                    content_type='application/json'
                )
            )
            
            # Close connection
            connection.close()
            
            logger.debug(f"Sent sync message to {exchange}:{routing_key}, ID: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send sync message to {exchange}:{routing_key}: {e}")
            return False


# Singleton instance of message producer
_message_producer = None

def get_message_producer() -> MessageProducer:
    """
    Get the singleton message producer instance.
    
    Returns:
        MessageProducer: Message producer instance
    """
    global _message_producer
    if _message_producer is None:
        _message_producer = MessageProducer()
    return _message_producer