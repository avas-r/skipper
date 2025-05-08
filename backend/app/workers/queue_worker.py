"""
Queue worker for processing items in job queues.

This worker periodically checks for pending queue items and processes them.
"""

import asyncio
import logging
from datetime import datetime, timedelta
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..config import settings
from ..db.session import SessionLocal
from ..models import Queue, QueueItem, Agent
from ..messaging.producer import get_message_producer

logger = logging.getLogger(__name__)

class QueueWorker:
    """Worker for processing queue items"""
    
    def __init__(self):
        """Initialize the worker"""
        self.check_interval = 10  # Check every 10 seconds
        self.running = False
        self.db = None
        self.batch_size = 20  # Process up to 20 items at a time
    
    async def run(self):
        """Run the worker in a loop"""
        logger.info("Starting queue worker")
        self.running = True
        
        try:
            while self.running:
                try:
                    # Create a new database session for each check
                    self.db = SessionLocal()
                    
                    # Process pending queue items
                    await self._process_queue_items()
                    
                finally:
                    # Close database session
                    if self.db:
                        self.db.close()
                        self.db = None
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Queue worker cancelled")
            self.running = False
            
        except Exception as e:
            logger.exception(f"Unexpected error in queue worker: {e}")
            self.running = False
            
        finally:
            # Clean up
            if self.db:
                self.db.close()
                
            logger.info("Queue worker stopped")
    
    async def _process_queue_items(self):
        """Process pending queue items"""
        if not self.db:
            logger.error("No database session available")
            return
        
        try:
            # Get current time
            now = datetime.utcnow()
            
            # Find pending queue items that are ready for processing
            pending_items = self.db.query(QueueItem).filter(
                QueueItem.status == "pending",
                QueueItem.assigned_to.is_(None),
                or_(
                    QueueItem.next_processing_time.is_(None),
                    QueueItem.next_processing_time <= now
                )
            ).order_by(
                QueueItem.priority.desc(),  # Higher priority first
                QueueItem.created_at        # Older items first
            ).limit(self.batch_size).all()
            
            if not pending_items:
                return
                
            logger.info(f"Found {len(pending_items)} pending queue items")
            
            # Find available agents
            available_agents = self.db.query(Agent).filter(
                Agent.status == "online"
            ).all()
            
            # Group agents by tenant
            tenant_agents = {}
            for agent in available_agents:
                tenant_id = str(agent.tenant_id)
                if tenant_id not in tenant_agents:
                    tenant_agents[tenant_id] = []
                tenant_agents[tenant_id].append(agent)
            
            # Process each pending item
            for item in pending_items:
                tenant_id = str(item.tenant_id)
                
                # Check if there are available agents for this tenant
                if tenant_id not in tenant_agents or not tenant_agents[tenant_id]:
                    # No available agents for this tenant
                    continue
                    
                # Assign to first available agent
                agent = tenant_agents[tenant_id][0]
                
                # Remove agent from available list (simple round-robin)
                tenant_agents[tenant_id] = tenant_agents[tenant_id][1:] + [agent]
                
                # Assign item to agent
                await self._assign_item_to_agent(item, agent)
                
        except Exception as e:
            logger.error(f"Error processing queue items: {e}")
            # Roll back transaction
            self.db.rollback()
    
    async def _assign_item_to_agent(self, item, agent):
        """
        Assign a queue item to an agent.
        
        Args:
            item: Queue item to assign
            agent: Agent to assign the item to
        """
        try:
            # Update item
            item.status = "assigned"
            item.assigned_to = agent.agent_id
            item.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Send message to agent
            message_producer = get_message_producer()
            
            await message_producer.send_message(
                exchange="agents",
                routing_key=f"agent.{agent.agent_id}.job",
                message_data={
                    "action": "process_queue_item",
                    "queue_item_id": str(item.item_id),
                    "agent_id": str(agent.agent_id),
                    "tenant_id": str(item.tenant_id),
                    "payload": item.payload,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Assigned queue item {item.item_id} to agent {agent.name} ({agent.agent_id})")
            
        except Exception as e:
            logger.error(f"Error assigning queue item {item.item_id} to agent {agent.agent_id}: {e}")
            # Roll back transaction
            self.db.rollback()