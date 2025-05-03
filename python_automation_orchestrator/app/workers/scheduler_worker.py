"""
Scheduler worker for executing scheduled jobs.

This worker periodically checks for scheduled jobs that need to be executed.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..config import settings
from ..db.session import SessionLocal
from ..models import Schedule, Job
from ..messaging.producer import get_message_producer

logger = logging.getLogger(__name__)

class SchedulerWorker:
    """Worker for executing scheduled jobs"""
    
    def __init__(self):
        """Initialize the worker"""
        self.check_interval = 30  # Check every 30 seconds
        self.running = False
        self.db = None
    
    async def run(self):
        """Run the worker in a loop"""
        logger.info("Starting scheduler worker")
        self.running = True
        
        try:
            while self.running:
                try:
                    # Create a new database session for each check
                    self.db = SessionLocal()
                    
                    # Check for due schedules
                    await self._check_schedules()
                    
                finally:
                    # Close database session
                    if self.db:
                        self.db.close()
                        self.db = None
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
        except asyncio.CancelledError:
            logger.info("Scheduler worker cancelled")
            self.running = False
            
        except Exception as e:
            logger.exception(f"Unexpected error in scheduler worker: {e}")
            self.running = False
            
        finally:
            # Clean up
            if self.db:
                self.db.close()
                
            logger.info("Scheduler worker stopped")
    
    async def _check_schedules(self):
        """Check for due schedules and queue jobs for execution"""
        if not self.db:
            logger.error("No database session available")
            return
        
        try:
            # Get current time
            now = datetime.utcnow()
            
            # Find schedules that are due
            due_schedules = self.db.query(Schedule).filter(
                Schedule.status == "active",
                Schedule.next_execution <= now,
                (Schedule.end_date.is_(None)) | (Schedule.end_date >= now)
            ).all()
            
            if not due_schedules:
                return
                
            logger.info(f"Found {len(due_schedules)} due schedules")
            
            # Process each due schedule
            for schedule in due_schedules:
                await self._process_schedule(schedule, now)
                
        except Exception as e:
            logger.error(f"Error checking schedules: {e}")
    
    async def _process_schedule(self, schedule, now):
        """
        Process a due schedule.
        
        Args:
            schedule: Schedule to process
            now: Current time
        """
        try:
            # Get jobs using this schedule
            jobs = self.db.query(Job).filter(
                Job.schedule_id == schedule.schedule_id,
                Job.status == "active"
            ).all()
            
            if not jobs:
                logger.info(f"No active jobs found for schedule {schedule.name} ({schedule.schedule_id})")
            else:
                logger.info(f"Queuing {len(jobs)} jobs for schedule {schedule.name} ({schedule.schedule_id})")
                
                # Queue each job
                message_producer = get_message_producer()
                
                for job in jobs:
                    # Create job execution message
                    await message_producer.send_message(
                        exchange="jobs",
                        routing_key="job.execution.schedule",
                        message_data={
                            "action": "schedule_job",
                            "job_id": str(job.job_id),
                            "tenant_id": str(job.tenant_id),
                            "schedule_id": str(schedule.schedule_id),
                            "timestamp": now.isoformat()
                        }
                    )
                    
                    logger.debug(f"Queued job {job.name} ({job.job_id}) for execution")
            
            # Update schedule
            # This is a simplified version - in a real system we would calculate the next execution
            # time based on the cron expression
            schedule.last_execution = now
            schedule.next_execution = now + timedelta(minutes=60)  # Just use 1 hour for simplicity
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing schedule {schedule.name} ({schedule.schedule_id}): {e}")
            # Roll back transaction
            self.db.rollback()