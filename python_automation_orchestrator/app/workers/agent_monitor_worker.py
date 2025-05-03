"""
Agent monitor worker for tracking agent status.

This worker periodically checks for stale agents and marks them as offline.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..config import settings
from ..db.session import SessionLocal
from ..services.agent_service import AgentService

logger = logging.getLogger(__name__)

class AgentMonitorWorker:
    """Worker for monitoring agent status"""
    
    def __init__(self):
        """Initialize the worker"""
        self.check_interval = 60  # Check every 60 seconds
        self.stale_threshold = 300  # 5 minutes without heartbeat
        self.running = False
        self.db = None
    
    async def run(self):
        """Run the worker in a loop"""
        logger.info("Starting agent monitor worker")
        self.running = True
        
        try:
            while self.running:
                try:
                    # Create a new database session for each check
                    self.db = SessionLocal()
                    
                    # Check for stale agents
                    await self._check_stale_agents()
                    
                finally:
                    # Close database session
                    if self.db:
                        self.db.close()
                        self.db = None
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Agent monitor worker cancelled")
            self.running = False
            
        except Exception as e:
            logger.exception(f"Unexpected error in agent monitor worker: {e}")
            self.running = False
            
        finally:
            # Clean up
            if self.db:
                self.db.close()
                
            logger.info("Agent monitor worker stopped")
    
    async def _check_stale_agents(self):
        """Check for stale agents and mark them as offline"""
        if not self.db:
            logger.error("No database session available")
            return
        
        try:
            # Create agent service
            agent_service = AgentService(self.db)
            
            # Check for stale agents
            stale_minutes = self.stale_threshold // 60
            count = agent_service.check_stale_agents(stale_minutes)
            
            if count > 0:
                logger.info(f"Marked {count} stale agents as offline")
                
        except Exception as e:
            logger.error(f"Error checking for stale agents: {e}")