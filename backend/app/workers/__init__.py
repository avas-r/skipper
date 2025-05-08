"""
Workers package for the orchestrator application.

This package contains background worker processes for handling asynchronous tasks.
"""

import asyncio
import logging
from typing import Dict, List

from ..messaging.consumer import get_message_consumer, close_all_consumers
from ..messaging.handlers import (
    job_execution_handler,
    agent_message_handler,
    notification_handler,
    queue_item_handler,
    event_handler
)

logger = logging.getLogger(__name__)

# Store background tasks
_background_tasks: List[asyncio.Task] = []

async def run_agent_monitor_worker():
    """Run the agent monitor worker"""
    from .agent_monitor_worker import AgentMonitorWorker
    
    worker = AgentMonitorWorker()
    await worker.run()

async def run_scheduler_worker():
    """Run the scheduler worker"""
    from .scheduler_worker import SchedulerWorker
    
    worker = SchedulerWorker()
    await worker.run()

async def run_queue_worker():
    """Run the queue worker"""
    from .queue_worker import QueueWorker
    
    worker = QueueWorker()
    await worker.run()

async def run_notification_worker():
    """Run the notification worker"""
    from .notification_worker import NotificationWorker
    
    worker = NotificationWorker()
    await worker.run()

async def run_messaging_consumer():
    """Run the messaging consumer"""
    # Create message consumer
    consumer = get_message_consumer("orchestrator")
    
    # Register handlers
    await consumer.connect()
    
    # Job execution messages
    await consumer.declare_queue(
        queue_name="job-executions",
        exchange_name="jobs",
        routing_keys=["job.execution.*"],
        durable=True
    )
    await consumer.register_handler(
        queue_name="job-executions",
        handler=job_execution_handler
    )
    
    # Agent messages
    await consumer.declare_queue(
        queue_name="agent-messages",
        exchange_name="agents",
        routing_keys=["agent.*"],
        durable=True
    )
    await consumer.register_handler(
        queue_name="agent-messages",
        handler=agent_message_handler
    )
    
    # Notification messages
    await consumer.declare_queue(
        queue_name="notifications",
        exchange_name="notifications",
        routing_keys=["notification.*"],
        durable=True
    )
    await consumer.register_handler(
        queue_name="notifications",
        handler=notification_handler
    )
    
    # Queue item messages
    await consumer.declare_queue(
        queue_name="queue-items",
        exchange_name="jobs",
        routing_keys=["queue.item.*"],
        durable=True
    )
    await consumer.register_handler(
        queue_name="queue-items",
        handler=queue_item_handler
    )
    
    # Event messages
    await consumer.declare_queue(
        queue_name="events",
        exchange_name="events",
        routing_keys=["#"],  # Catch all events
        durable=True
    )
    await consumer.register_handler(
        queue_name="events",
        handler=event_handler
    )
    
    # Start consuming
    await consumer.start_consuming()
    
    # Run consumer
    await consumer.run()

def start_workers():
    """Start all background worker processes"""
    logger.info("Starting background workers")
    
    # Start agent monitor worker
    agent_monitor_task = asyncio.create_task(run_agent_monitor_worker())
    _background_tasks.append(agent_monitor_task)
    
    # Start scheduler worker
    scheduler_task = asyncio.create_task(run_scheduler_worker())
    _background_tasks.append(scheduler_task)
    
    # Start queue worker
    queue_task = asyncio.create_task(run_queue_worker())
    _background_tasks.append(queue_task)
    
    # Start notification worker
    notification_task = asyncio.create_task(run_notification_worker())
    _background_tasks.append(notification_task)
    
    # Start messaging consumer
    messaging_task = asyncio.create_task(run_messaging_consumer())
    _background_tasks.append(messaging_task)
    
    logger.info(f"Started {len(_background_tasks)} background workers")

async def stop_workers():
    """Stop all background worker processes"""
    logger.info("Stopping background workers")
    
    # Cancel all tasks
    for task in _background_tasks:
        task.cancel()
        
    # Wait for all tasks to complete
    if _background_tasks:
        await asyncio.gather(*_background_tasks, return_exceptions=True)
        
    # Close message consumers
    await close_all_consumers()
    
    logger.info("All background workers stopped")