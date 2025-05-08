"""
Scheduler service for managing job schedules.

This module provides services for managing job schedules,
including cron-based scheduling and manual triggering.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import pytz
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from croniter import croniter

from ..models import Schedule, Job, JobExecution, AuditLog
from ..schemas.schedule import ScheduleCreate, ScheduleUpdate
from ..messaging.producer import get_message_producer

logger = logging.getLogger(__name__)

class ScheduleService:
    """Service for managing job schedules"""
    
    def __init__(self, db: Session):
        """
        Initialize the schedule service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def create_schedule(self, schedule_in: ScheduleCreate, tenant_id: str, user_id: str) -> Schedule:
        """
        Create a new schedule.
        
        Args:
            schedule_in: Schedule data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Schedule: Created schedule
            
        Raises:
            ValueError: If schedule data is invalid
        """
        # Validate cron expression
        if not croniter.is_valid(schedule_in.cron_expression):
            raise ValueError(f"Invalid cron expression: {schedule_in.cron_expression}")
        
        # Check if schedule with same name exists
        existing = self.db.query(Schedule).filter(
            Schedule.tenant_id == tenant_id,
            Schedule.name == schedule_in.name
        ).first()
        
        if existing:
            raise ValueError(f"Schedule with name '{schedule_in.name}' already exists")
        
        # Calculate next execution time
        timezone = pytz.timezone(schedule_in.timezone)
        now = datetime.now(timezone)
        iter = croniter(schedule_in.cron_expression, now)
        next_execution = iter.get_next(datetime)
        
        # Create schedule
        db_schedule = Schedule(
            schedule_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=schedule_in.name,
            description=schedule_in.description,
            cron_expression=schedule_in.cron_expression,
            timezone=schedule_in.timezone,
            start_date=schedule_in.start_date,
            end_date=schedule_in.end_date,
            status="active",
            created_by=user_id,
            updated_by=user_id,
            next_execution=next_execution
        )
        
        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_schedule",
            entity_type="schedule",
            entity_id=db_schedule.schedule_id,
            details={
                "name": db_schedule.name,
                "cron_expression": db_schedule.cron_expression
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return db_schedule
    
    def update_schedule(self, schedule_id: str, schedule_in: ScheduleUpdate, tenant_id: str, user_id: str) -> Optional[Schedule]:
        """
        Update a schedule.
        
        Args:
            schedule_id: Schedule ID
            schedule_in: Schedule update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Optional[Schedule]: Updated schedule or None if not found
            
        Raises:
            ValueError: If schedule data is invalid
        """
        # Get schedule
        schedule = self.db.query(Schedule).filter(
            Schedule.schedule_id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule:
            return None
        
        # Validate cron expression
        if schedule_in.cron_expression and not croniter.is_valid(schedule_in.cron_expression):
            raise ValueError(f"Invalid cron expression: {schedule_in.cron_expression}")
        
        # Check name uniqueness if changing
        if schedule_in.name and schedule_in.name != schedule.name:
            existing = self.db.query(Schedule).filter(
                Schedule.tenant_id == tenant_id,
                Schedule.name == schedule_in.name,
                Schedule.schedule_id != schedule_id
            ).first()
            
            if existing:
                raise ValueError(f"Schedule with name '{schedule_in.name}' already exists")
        
        # Update fields
        update_data = schedule_in.dict(exclude_unset=True)
        
        # Recalculate next execution if cron expression changes
        if "cron_expression" in update_data or "timezone" in update_data:
            cron_expression = update_data.get("cron_expression", schedule.cron_expression)
            timezone_name = update_data.get("timezone", schedule.timezone)
            
            timezone = pytz.timezone(timezone_name)
            now = datetime.now(timezone)
            iter = croniter(cron_expression, now)
            update_data["next_execution"] = iter.get_next(datetime)
        
        for key, value in update_data.items():
            setattr(schedule, key, value)
            
        # Update audit fields
        schedule.updated_at = datetime.utcnow()
        schedule.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(schedule)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_schedule",
            entity_type="schedule",
            entity_id=schedule.schedule_id,
            details=update_data
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return schedule
    
    def delete_schedule(self, schedule_id: str, tenant_id: str) -> bool:
        """
        Delete a schedule.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ValueError: If schedule has active jobs
        """
        # Get schedule
        schedule = self.db.query(Schedule).filter(
            Schedule.schedule_id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule:
            return False
        
        # Check if schedule has active jobs
        active_jobs = self.db.query(Job).filter(
            Job.schedule_id == schedule_id,
            Job.status == "active"
        ).count()
        
        if active_jobs > 0:
            raise ValueError(f"Cannot delete schedule with {active_jobs} active jobs")
        
        # Delete schedule
        self.db.delete(schedule)
        self.db.commit()
        
        return True
    
    def get_schedule(self, schedule_id: str, tenant_id: str) -> Optional[Schedule]:
        """
        Get a schedule by ID.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Schedule]: Schedule or None if not found
        """
        return self.db.query(Schedule).filter(
            Schedule.schedule_id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
    
    def get_schedule_with_jobs(self, schedule_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule with its associated jobs.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Dict[str, Any]]: Schedule with jobs or None if not found
        """
        # Get schedule
        schedule = self.db.query(Schedule).filter(
            Schedule.schedule_id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule:
            return None
        
        # Get jobs
        jobs = self.db.query(Job).filter(
            Job.schedule_id == schedule_id,
            Job.tenant_id == tenant_id
        ).all()
        
        # Convert to dictionary
        result = schedule.__dict__.copy()
        
        # Remove SQLAlchemy state
        if "_sa_instance_state" in result:
            result.pop("_sa_instance_state")
            
        # Add jobs
        result["jobs"] = jobs
        
        return result
    
    def list_schedules(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Schedule]:
        """
        List schedules with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Schedule]: List of schedules
        """
        # Build base query
        query = self.db.query(Schedule).filter(Schedule.tenant_id == tenant_id)
        
        # Apply filters
        if status:
            query = query.filter(Schedule.status == status)
            
        if search:
            query = query.filter(
                or_(
                    Schedule.name.ilike(f"%{search}%"),
                    Schedule.description.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        query = query.order_by(Schedule.name).offset(skip).limit(limit)
        
        return query.all()
    
    def update_schedule_status(self, schedule_id: str, tenant_id: str, status: str, user_id: str) -> Optional[Schedule]:
        """
        Update a schedule's status.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID
            status: New status
            user_id: User ID
            
        Returns:
            Optional[Schedule]: Updated schedule or None if not found
            
        Raises:
            ValueError: If status is invalid
        """
        # Validate status
        valid_statuses = ["active", "inactive"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        # Get schedule
        schedule = self.db.query(Schedule).filter(
            Schedule.schedule_id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule:
            return None
        
        # Update status
        schedule.status = status
        schedule.updated_at = datetime.utcnow()
        schedule.updated_by = user_id
        
        # If activating, recalculate next execution
        if status == "active" and not schedule.next_execution:
            timezone = pytz.timezone(schedule.timezone)
            now = datetime.now(timezone)
            iter = croniter(schedule.cron_expression, now)
            schedule.next_execution = iter.get_next(datetime)
        
        self.db.commit()
        self.db.refresh(schedule)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action=f"schedule_{status}",
            entity_type="schedule",
            entity_id=schedule.schedule_id,
            details={
                "name": schedule.name,
                "status": status
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return schedule
    
    def trigger_schedule(
        self,
        schedule_id: str,
        tenant_id: str,
        user_id: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger a schedule manually.
        
        Args:
            schedule_id: Schedule ID
            tenant_id: Tenant ID
            user_id: User ID
            background_tasks: Optional FastAPI background tasks
            
        Returns:
            Optional[Dict[str, Any]]: Trigger result or None if schedule not found
            
        Raises:
            ValueError: If schedule not found or has no jobs
        """
        # Get schedule
        schedule = self.db.query(Schedule).filter(
            Schedule.schedule_id == schedule_id,
            Schedule.tenant_id == tenant_id
        ).first()
        
        if not schedule:
            return None
        
        # Get active jobs for this schedule
        jobs = self.db.query(Job).filter(
            Job.schedule_id == schedule_id,
            Job.tenant_id == tenant_id,
            Job.status == "active"
        ).all()
        
        if not jobs:
            raise ValueError(f"Schedule {schedule_id} has no active jobs")
        
        # Trigger jobs
        triggered_jobs = []
        
        for job in jobs:
            # Create job execution message
            if background_tasks:
                # Get message producer
                message_producer = get_message_producer()
                
                # Add task to send message
                background_tasks.add_task(
                    message_producer.send_message,
                    "jobs",
                    "job.execution.manual",
                    {
                        "action": "schedule_trigger",
                        "job_id": str(job.job_id),
                        "tenant_id": tenant_id,
                        "schedule_id": schedule_id,
                        "trigger_type": "manual",
                        "triggered_by": user_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            # Add to triggered jobs
            triggered_jobs.append({
                "job_id": str(job.job_id),
                "name": job.name
            })
            
        # Update last execution time
        schedule.last_execution = datetime.utcnow()
        self.db.commit()
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="trigger_schedule",
            entity_type="schedule",
            entity_id=schedule.schedule_id,
            details={
                "name": schedule.name,
                "triggered_jobs": len(triggered_jobs),
                "job_ids": [job["job_id"] for job in triggered_jobs]
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        # Return result
        return {
            "schedule_id": schedule.schedule_id,
            "name": schedule.name,
            "jobs_triggered": len(triggered_jobs),
            "jobs": triggered_jobs
        }
    
    def process_due_schedules(self, background_tasks: Optional[BackgroundTasks] = None) -> int:
        """
        Process schedules that are due for execution.
        
        Args:
            background_tasks: Optional FastAPI background tasks
            
        Returns:
            int: Number of schedules processed
        """
        # Get current time
        now = datetime.utcnow()
        
        # Find schedules that are due
        due_schedules = self.db.query(Schedule).filter(
            Schedule.status == "active",
            Schedule.next_execution <= now,
            or_(
                Schedule.end_date.is_(None),
                Schedule.end_date >= now
            )
        ).all()
        
        if not due_schedules:
            return 0
            
        logger.info(f"Found {len(due_schedules)} due schedules")
        
        # Process each due schedule
        for schedule in due_schedules:
            # Find jobs using this schedule
            jobs = self.db.query(Job).filter(
                Job.schedule_id == schedule.schedule_id,
                Job.status == "active"
            ).all()
            
            if jobs:
                logger.info(f"Triggering {len(jobs)} jobs for schedule {schedule.name} ({schedule.schedule_id})")
                
                # Trigger jobs
                for job in jobs:
                    # Create job execution message
                    if background_tasks:
                        # Get message producer
                        message_producer = get_message_producer()
                        
                        # Add task to send message
                        background_tasks.add_task(
                            message_producer.send_message,
                            "jobs",
                            "job.execution.schedule",
                            {
                                "action": "schedule_trigger",
                                "job_id": str(job.job_id),
                                "tenant_id": str(schedule.tenant_id),
                                "schedule_id": str(schedule.schedule_id),
                                "trigger_type": "scheduled",
                                "timestamp": now.isoformat()
                            }
                        )
            
            # Update schedule execution times
            schedule.last_execution = now
            
            # Calculate next execution time
            timezone = pytz.timezone(schedule.timezone)
            now_tz = datetime.now(timezone)
            iter = croniter(schedule.cron_expression, now_tz)
            schedule.next_execution = iter.get_next(datetime)
            
        # Commit all changes
        self.db.commit()
        
        return len(due_schedules)