"""
Message consumer module for asynchronous messaging.

This module provides a message consumer for receiving messages
from RabbitMQ or other message brokers.
"""

import json
import logging
import asyncio
from typing import Any, Callable, Dict, List, Optional

import aio_pika
from aio_pika import Message, DeliveryMode
from aio_pika.abc import AbstractRobustConnection

from ..config import settings

logger = logging.getLogger(__name__)

# Type alias for message handler functions
MessageHandler = Callable[[Dict[str, Any], Message], None]

class MessageConsumer:
    """Message consumer for receiving messages from message broker"""
    
    def __init__(self, consumer_name: str):
        """
        Initialize the message consumer.
        
        Args:
            consumer_name: Unique name for this consumer
        """
        self.consumer_name = consumer_name
        self.connection: Optional[AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None
        self.exchanges: Dict[str, aio_pika.abc.AbstractExchange] = {}
        self.queues: Dict[str, aio_pika.abc.AbstractQueue] = {}
        self.handlers: Dict[str, MessageHandler] = {}
        self.running = False
        self.prefetch_count = 10
        
    async def connect(self):
        """Connect to the message broker"""
        try:
            # Create connection
            self.connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URI,
                client_properties={
                    "connection_name": f"orchestrator_consumer_{self.consumer_name}"
                }
            )
            
            # Create channel
            self.channel = await self.connection.channel()
            
            # Set QoS
            await self.channel.set_qos(prefetch_count=self.prefetch_count)
            
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
                
            logger.info(f"Message consumer '{self.consumer_name}' connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def close(self):
        """Close the connection to the message broker"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info(f"Message consumer '{self.consumer_name}' disconnected from RabbitMQ")
            
    async def declare_queue(
        self,
        queue_name: str,
        exchange_name: str,
        routing_keys: List[str],
        durable: bool = True,
        auto_delete: bool = False,
        arguments: Optional[Dict[str, Any]] = None
    ):
        """
        Declare a queue and bind it to an exchange.
        
        Args:
            queue_name: Queue name
            exchange_name: Exchange name
            routing_keys: List of routing keys to bind
            durable: Whether the queue survives broker restarts
            auto_delete: Whether to delete the queue when no consumers
            arguments: Additional queue arguments
            
        Returns:
            aio_pika.abc.AbstractQueue: Declared queue
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        if exchange_name not in self.exchanges:
            raise ValueError(f"Exchange '{exchange_name}' not declared")
            
        # Declare queue
        queue = await self.channel.declare_queue(
            queue_name,
            durable=durable,
            auto_delete=auto_delete,
            arguments=arguments
        )
        
        # Bind queue to exchange with routing keys
        for routing_key in routing_keys:
            await queue.bind(self.exchanges[exchange_name], routing_key)
            
        self.queues[queue_name] = queue
        
        logger.info(f"Declared queue '{queue_name}' bound to exchange '{exchange_name}'")
        
        return queue
    
    async def register_handler(
        self,
        queue_name: str,
        handler: MessageHandler,
        exchange_name: Optional[str] = None,
        routing_keys: Optional[List[str]] = None
    ):
        """
        Register a message handler for a queue.
        
        Args:
            queue_name: Queue name
            handler: Message handler function
            exchange_name: Optional exchange name (if queue needs to be declared)
            routing_keys: Optional routing keys (if queue needs to be declared)
        """
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        # Declare queue if it doesn't exist
        if queue_name not in self.queues and exchange_name and routing_keys:
            await self.declare_queue(queue_name, exchange_name, routing_keys)
        elif queue_name not in self.queues:
            raise ValueError(f"Queue '{queue_name}' not declared")
            
        # Register handler
        self.handlers[queue_name] = handler
        
        logger.info(f"Registered handler for queue '{queue_name}'")
    
    async def start_consuming(self):
        """Start consuming messages from all registered queues"""
        if not self.connection or self.connection.is_closed:
            await self.connect()
            
        # Start consuming from each queue
        for queue_name, handler in self.handlers.items():
            queue = self.queues[queue_name]
            await queue.consume(self._create_consumer_callback(handler))
            
        self.running = True
        logger.info(f"Message consumer '{self.consumer_name}' started consuming")
    
    def _create_consumer_callback(self, handler: MessageHandler):
        """
        Create a callback function for message consumption.
        
        Args:
            handler: Message handler function
            
        Returns:
            Callable: Callback function for message consumption
        """
        async def callback(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    # Decode message body
                    body = message.body.decode()
                    data = json.loads(body)
                    
                    # Call handler
                    await handler(data, message)
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode message: {message.body}")
                    # Reject message
                    await message.reject(requeue=False)
                    
                except Exception as e:
                    logger.exception(f"Error processing message: {e}")
                    # Nack message for requeue
                    await message.nack(requeue=True)
        
        return callback
    
    async def run(self):
        """Run the consumer in a loop"""
        try:
            await self.connect()
            await self.start_consuming()
            
            # Keep running until stopped
            while self.running:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info(f"Message consumer '{self.consumer_name}' cancelled")
            self.running = False
            
        except Exception as e:
            logger.exception(f"Error in message consumer: {e}")
            
        finally:
            await self.close()

# Dictionary of message consumers
_message_consumers: Dict[str, MessageConsumer] = {}

def get_message_consumer(consumer_name: str) -> MessageConsumer:
    """
    Get a message consumer by name.
    
    Args:
        consumer_name: Consumer name
        
    Returns:
        MessageConsumer: Message consumer instance
    """
    global _message_consumers
    if consumer_name not in _message_consumers:
        _message_consumers[consumer_name] = MessageConsumer(consumer_name)
    return _message_consumers[consumer_name]

async def close_all_consumers():
    """Close all message consumers"""
    for consumer in _message_consumers.values():
        await consumer.close()