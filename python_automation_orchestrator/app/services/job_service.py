"""
Job service for managing automation jobs.

This module provides services for managing jobs, job executions, and related operations.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from ..db.session import SessionLocal
from ..models import Job, JobExecution, JobDependency, Package, Agent, User, Queue, QueueItem, Schedule
from ..schemas.job import JobCreate, JobUpdate, JobStartRequest, JobExecutionFilter
from ..messaging.producer import get_message_producer
from ..utils.object_storage import ObjectStorage

logger = logging.getLogger(__name__)

class JobService:
    """Service for managing automation jobs"""
    
    def __init__(self, db: Session):
        """
        Initialize the job service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.object_storage = ObjectStorage()
        
    async def create_job(self, job_in: JobCreate, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Job:
        """
        Create a new job.
        
        Args:
            job_in: Job data
            tenant_id: Tenant ID
            user_id: User ID creating the job
            
        Returns:
            Job: Created job
            
        Raises:
            ValueError: If related entities not found or validation fails
        """
        # Validate package exists and belongs to tenant
        package = self.db.query(Package).filter(
            Package.package_id == job_in.package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            raise ValueError(f"Package not found: {job_in.package_id}")
        
        # Validate schedule if provided
        if job_in.schedule_id:
            schedule = self.db.query(Schedule).filter(
                Schedule.schedule_id == job_in.schedule_id,
                Schedule.tenant_id == tenant_id
            ).first()
            
            if not schedule:
                raise ValueError(f"Schedule not found: {job_in.schedule_id}")
        
        # Validate queue if provided
        if job_in.queue_id:
            queue = self.db.query(Queue).filter(
                Queue.queue_id == job_in.queue_id,
                Queue.tenant_id == tenant_id
            ).first()
            
            if not queue:
                raise ValueError(f"Queue not found: {job_in.queue_id}")
        
        # Create job
        job = Job(
            job_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=job_in.name,
            description=job_in.description,
            package_id=job_in.package_id,
            schedule_id=job_in.schedule_id,
            queue_id=job_in.queue_id,
            priority=job_in.priority or 1,
            max_concurrent_runs=job_in.max_concurrent_runs or 1,
            timeout_seconds=job_in.timeout_seconds or 3600,
            retry_count=job_in.retry_count or 0,
            retry_delay_seconds=job_in.retry_delay_seconds or 60,
            parameters=job_in.parameters or {},
            status="active",
            created_by=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        # Add dependencies if provided
        if job_in.depends_on_job_ids:
            for dep_job_id in job_in.depends_on_job_ids:
                # Validate dependency job exists and belongs to tenant
                dep_job = self.db.query(Job).filter(
                    Job.job_id == dep_job_id,
                    Job.tenant_id == tenant_id
                ).first()
                
                if not dep_job:
                    logger.warning(f"Dependency job not found: {dep_job_id}")
                    continue
                
                # Create dependency
                dependency = JobDependency(
                    job_id=job.job_id,
                    depends_on_job_id=dep_job_id,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(dependency)
            
            self.db.commit()
        
        return job
    
    def get_job(self, job_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Job]:
        """
        Get a job by ID.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Job]: Job or None if not found
        """
        return self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
    
    def get_job_with_executions(
        self, 
        job_id: uuid.UUID, 
        tenant_id: uuid.UUID,
        limit: int = 10
    ) -> Optional[Tuple[Job, List[JobExecution]]]:
        """
        Get a job with its recent executions.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            limit: Maximum number of executions to return
            
        Returns:
            Optional[Tuple[Job, List[JobExecution]]]: Job and executions or None if not found
        """
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            return None
        
        # Get recent executions
        executions = self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id
        ).order_by(
            JobExecution.created_at.desc()
        ).limit(limit).all()
        
        return (job, executions)
    
    def list_jobs(
        self,
        tenant_id: uuid.UUID,
        package_id: Optional[uuid.UUID] = None,
        schedule_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Job], int]:
        """
        List jobs with filtering.
        
        Args:
            tenant_id: Tenant ID
            package_id: Optional package filter
            schedule_id: Optional schedule filter
            status: Optional status filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple[List[Job], int]: List of jobs and total count
        """
        query = self.db.query(Job).filter(Job.tenant_id == tenant_id)
        
        # Apply filters
        if package_id:
            query = query.filter(Job.package_id == package_id)
        
        if schedule_id:
            query = query.filter(Job.schedule_id == schedule_id)
        
        if status:
            query = query.filter(Job.status == status)
        
        if search:
            query = query.filter(Job.name.ilike(f"%{search}%"))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.order_by(Job.name).offset(skip).limit(limit)
        
        return query.all(), total_count
    
    def update_job(
        self, 
        job_id: uuid.UUID, 
        job_in: JobUpdate, 
        tenant_id: uuid.UUID
    ) -> Optional[Job]:
        """
        Update a job.
        
        Args:
            job_id: Job ID
            job_in: Job update data
            tenant_id: Tenant ID
            
        Returns:
            Optional[Job]: Updated job or None if not found
            
        Raises:
            ValueError: If related entities not found or validation fails
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            return None
        
        # Validate package if provided
        if job_in.package_id:
            package = self.db.query(Package).filter(
                Package.package_id == job_in.package_id,
                Package.tenant_id == tenant_id
            ).first()
            
            if not package:
                raise ValueError(f"Package not found: {job_in.package_id}")
        
        # Validate schedule if provided
        if job_in.schedule_id:
            schedule = self.db.query(Schedule).filter(
                Schedule.schedule_id == job_in.schedule_id,
                Schedule.tenant_id == tenant_id
            ).first()
            
            if not schedule:
                raise ValueError(f"Schedule not found: {job_in.schedule_id}")
        
        # Validate queue if provided
        if job_in.queue_id:
            queue = self.db.query(Queue).filter(
                Queue.queue_id == job_in.queue_id,
                Queue.tenant_id == tenant_id
            ).first()
            
            if not queue:
                raise ValueError(f"Queue not found: {job_in.queue_id}")
        
        # Update job fields from input data
        update_data = job_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(job, key, value)
        
        # Update timestamp
        job.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def delete_job(self, job_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        """
        Delete a job.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            return False
        
        # Delete job dependencies
        self.db.query(JobDependency).filter(
            or_(
                JobDependency.job_id == job_id,
                JobDependency.depends_on_job_id == job_id
            )
        ).delete(synchronize_session=False)
        
        # Delete job
        self.db.delete(job)
        self.db.commit()
        
        return True
    
    async def start_job(
        self, 
        job_id: uuid.UUID, 
        tenant_id: uuid.UUID, 
        start_request: JobStartRequest
    ) -> Optional[JobExecution]:
        """
        Start a job execution.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            start_request: Job start parameters
            
        Returns:
            Optional[JobExecution]: Created job execution or None if job not found
            
        Raises:
            ValueError: If job cannot be started (e.g., max concurrent runs exceeded)
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id,
            Job.status == "active"
        ).first()
        
        if not job:
            return None
        
        # Check if job already has too many concurrent runs
        running_executions = self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id,
            JobExecution.status.in_(["pending", "running"])
        ).count()
        
        if running_executions >= job.max_concurrent_runs:
            raise ValueError(f"Job already has maximum concurrent runs: {job.max_concurrent_runs}")
        
        # Merge parameters
        merged_params = job.parameters.copy() if job.parameters else {}
        if start_request.parameters:
            merged_params.update(start_request.parameters)
        
        # Determine queue
        queue_id = start_request.queue_id or job.queue_id
        
        # Create job execution
        execution = JobExecution(
            execution_id=uuid.uuid4(),
            job_id=job_id,
            tenant_id=tenant_id,
            status="pending",
            trigger_type="manual",
            input_parameters=merged_params,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        # If queue specified, add to queue
        if queue_id:
            # Create queue item
            queue_item = QueueItem(
                item_id=uuid.uuid4(),
                queue_id=queue_id,
                tenant_id=tenant_id,
                status="pending",
                priority=start_request.priority or job.priority,
                reference_id=str(job_id),
                payload={
                    "execution_id": str(execution.execution_id),
                    "job_id": str(job_id),
                    "parameters": merged_params
                },
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(queue_item)
            self.db.commit()
            
            # Update execution with queue item
            execution.queue_item_id = queue_item.item_id
            self.db.commit()
            
            # Send message to messaging system
            message_producer = get_message_producer()
            await message_producer.send_message(
                exchange="jobs",
                routing_key="queue.item.new",
                message_data={
                    "action": "new_item",
                    "queue_id": str(queue_id),
                    "item_id": str(queue_item.item_id),
                    "tenant_id": str(tenant_id),
                    "priority": queue_item.priority
                }
            )
        else:
            # Send message to directly process execution
            message_producer = get_message_producer()
            await message_producer.send_message(
                exchange="jobs",
                routing_key="job.execution.new",
                message_data={
                    "action": "new_execution",
                    "execution_id": str(execution.execution_id),
                    "job_id": str(job_id),
                    "tenant_id": str(tenant_id)
                }
            )
        
        return execution
    
    async def process_execution(
        self, 
        execution_id: uuid.UUID, 
        tenant_id: uuid.UUID
    ) -> Optional[JobExecution]:
        """
        Process a job execution (worker function).
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[JobExecution]: Updated execution or None if not found
        """
        # Get execution with job
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).join(Job).first()
        
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return None
        
        # Get available agents
        agents = self.db.query(Agent).filter(
            Agent.tenant_id == tenant_id,
            Agent.status == "online"
        ).all()
        
        if not agents:
            logger.warning(f"No available agents for tenant: {tenant_id}")
            execution.status = "pending"  # Keep pending status
            self.db.commit()
            return execution
        
        # Assign to first available agent (simple round-robin)
        agent = agents[0]
        
        # Update execution
        execution.agent_id = agent.agent_id
        execution.status = "assigned"
        execution.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # Send message to agent
        message_producer = get_message_producer()
        await message_producer.send_message(
            exchange="agents",
            routing_key=f"agent.{agent.agent_id}.job",
            message_data={
                "action": "execute_job",
                "execution_id": str(execution_id),
                "job_id": str(execution.job_id),
                "tenant_id": str(tenant_id),
                "parameters": execution.input_parameters
            }
        )
        
        logger.info(f"Job execution {execution_id} assigned to agent {agent.agent_id}")
        
        return execution
    
    async def update_execution_status(
        self,
        execution_id: uuid.UUID,
        tenant_id: uuid.UUID,
        status: str,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> Optional[JobExecution]:
        """
        Update job execution status.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            status: New status
            error_message: Optional error message
            results: Optional execution results
            
        Returns:
            Optional[JobExecution]: Updated execution or None if not found
        """
        # Get execution
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).first()
        
        if not execution:
            logger.warning(f"Execution not found: {execution_id}")
            return None
        
        # Update execution
        execution.status = status
        execution.updated_at = datetime.utcnow()
        
        if status == "running" and not execution.started_at:
            execution.started_at = datetime.utcnow()
        
        if status in ["completed", "failed", "cancelled"]:
            execution.completed_at = datetime.utcnow()
            
            if execution.started_at:
                # Calculate execution time
                delta = execution.completed_at - execution.started_at
                execution.execution_time_ms = int(delta.total_seconds() * 1000)
        
        if error_message:
            execution.error_message = error_message
        
        if results:
            execution.output_results = results
        
        self.db.commit()
        
        # Send event message
        message_producer = get_message_producer()
        await message_producer.send_message(
            exchange="events",
            routing_key=f"job.execution.{status}",
            message_data={
                "event_type": "job_execution_status_change",
                "execution_id": str(execution_id),
                "job_id": str(execution.job_id),
                "tenant_id": str(tenant_id),
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        # If execution completed, process dependencies
        if status == "completed":
            await self.process_job_dependencies(execution.job_id, tenant_id)
        
        return execution
    
    async def cancel_execution(
        self, 
        execution_id: uuid.UUID, 
        tenant_id: uuid.UUID
    ) -> Optional[JobExecution]:
        """
        Cancel a job execution.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[JobExecution]: Updated execution or None if not found
        """
        # Get execution
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id,
            JobExecution.status.in_(["pending", "assigned", "running"])
        ).first()
        
        if not execution:
            return None
        
        # If execution has an agent, send cancel command
        if execution.agent_id:
            message_producer = get_message_producer()
            await message_producer.send_message(
                exchange="agents",
                routing_key=f"agent.{execution.agent_id}.command",
                message_data={
                    "command": "cancel_job",
                    "execution_id": str(execution_id),
                    "job_id": str(execution.job_id),
                    "tenant_id": str(tenant_id)
                }
            )
        
        # Update execution status
        execution.status = "cancelled"
        execution.completed_at = datetime.utcnow()
        execution.updated_at = datetime.utcnow()
        
        if execution.started_at:
            # Calculate execution time
            delta = execution.completed_at - execution.started_at
            execution.execution_time_ms = int(delta.total_seconds() * 1000)
        
        self.db.commit()
        
        return execution
    
    def get_execution(
        self, 
        execution_id: uuid.UUID, 
        tenant_id: uuid.UUID
    ) -> Optional[JobExecution]:
        """
        Get job execution by ID.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[JobExecution]: Job execution or None if not found
        """
        return self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).options(
            joinedload(JobExecution.job),
            joinedload(JobExecution.agent)
        ).first()
    
    def list_executions(
        self,
        tenant_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        filter_params: Optional[JobExecutionFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[JobExecution], int]:
        """
        List job executions with filtering.
        
        Args:
            tenant_id: Tenant ID
            job_id: Optional job filter
            filter_params: Optional filter parameters
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Tuple[List[JobExecution], int]: List of executions and total count
        """
        query = self.db.query(JobExecution).filter(JobExecution.tenant_id == tenant_id)
        
        # Apply job filter
        if job_id:
            query = query.filter(JobExecution.job_id == job_id)
        
        # Apply filter parameters
        if filter_params:
            if filter_params.status:
                query = query.filter(JobExecution.status.in_(filter_params.status))
            
            if filter_params.start_date:
                query = query.filter(JobExecution.created_at >= filter_params.start_date)
            
            if filter_params.end_date:
                query = query.filter(JobExecution.created_at <= filter_params.end_date)
            
            if filter_params.agent_id:
                query = query.filter(JobExecution.agent_id == filter_params.agent_id)
            
            if filter_params.package_id:
                query = query.join(Job).filter(Job.package_id == filter_params.package_id)
            
            if filter_params.trigger_type:
                query = query.filter(JobExecution.trigger_type == filter_params.trigger_type)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination and ordering
        query = query.order_by(JobExecution.created_at.desc()).offset(skip).limit(limit)
        
        # Load related entities
        query = query.options(
            joinedload(JobExecution.job),
            joinedload(JobExecution.agent)
        )
        
        return query.all(), total_count
    
    async def process_job_dependencies(
        self, 
        completed_job_id: uuid.UUID, 
        tenant_id: uuid.UUID
    ) -> int:
        """
        Process jobs that depend on a completed job.
        
        Args:
            completed_job_id: ID of the completed job
            tenant_id: Tenant ID
            
        Returns:
            int: Number of dependent jobs triggered
        """
        # Find jobs that depend on this one
        dependencies = self.db.query(JobDependency).filter(
            JobDependency.depends_on_job_id == completed_job_id
        ).all()
        
        if not dependencies:
            return 0
        
        # Get dependent job IDs
        dependent_job_ids = [dep.job_id for dep in dependencies]
        
        # Get jobs
        jobs = self.db.query(Job).filter(
            Job.job_id.in_(dependent_job_ids),
            Job.tenant_id == tenant_id,
            Job.status == "active"
        ).all()
        
        triggered_count = 0
        
        # Check each job's dependencies
        for job in jobs:
            # Get all dependencies for this job
            job_deps = self.db.query(JobDependency).filter(
                JobDependency.job_id == job.job_id
            ).all()
            
            all_deps_satisfied = True
            
            # Check if all dependencies have recent successful executions
            for dep in job_deps:
                # Find recent successful execution
                recent_success = self.db.query(JobExecution).filter(
                    JobExecution.job_id == dep.depends_on_job_id,
                    JobExecution.status == "completed",
                    JobExecution.completed_at >= datetime.utcnow() - timedelta(hours=24)
                ).first()
                
                if not recent_success:
                    all_deps_satisfied = False
                    break
            
            if all_deps_satisfied:
                # All dependencies met, start job
                try:
                    await self.start_job(
                        job_id=job.job_id,
                        tenant_id=tenant_id,
                        start_request=JobStartRequest(
                            parameters={"triggered_by_dependency": str(completed_job_id)}
                        )
                    )
                    triggered_count += 1
                except Exception as e:
                    logger.error(f"Error triggering dependent job {job.job_id}: {e}")
        
        return triggered_count
    
    def get_job_statistics(
        self,
        tenant_id: uuid.UUID,
        job_id: Optional[uuid.UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get job execution statistics.
        
        Args:
            tenant_id: Tenant ID
            job_id: Optional job filter
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Dict[str, Any]: Job statistics
        """
        query = self.db.query(JobExecution).filter(JobExecution.tenant_id == tenant_id)
        
        # Apply job filter
        if job_id:
            query = query.filter(JobExecution.job_id == job_id)
        
        # Apply date filters
        if start_date:
            query = query.filter(JobExecution.created_at >= start_date)
        
        if end_date:
            query = query.filter(JobExecution.created_at <= end_date)
        
        # Total executions
        total_executions = query.count()
        
        # Count by status
        status_counts = {}
        for status in ["completed", "failed", "cancelled", "running", "pending"]:
            count = query.filter(JobExecution.status == status).count()
            status_counts[status] = count
        
        # Calculate average execution time for completed jobs
        avg_time = self.db.query(func.avg(JobExecution.execution_time_ms)).filter(
            JobExecution.tenant_id == tenant_id,
            JobExecution.status == "completed",
            JobExecution.execution_time_ms.isnot(None)
        )
        
        if job_id:
            avg_time = avg_time.filter(JobExecution.job_id == job_id)
        
        if start_date:
            avg_time = avg_time.filter(JobExecution.created_at >= start_date)
        
        if end_date:
            avg_time = avg_time.filter(JobExecution.created_at <= end_date)
        
        avg_execution_time = avg_time.scalar() or 0
        
        return {
            "total_executions": total_executions,
            "status_counts": status_counts,
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "success_rate": round(status_counts.get("completed", 0) / total_executions * 100, 2) if total_executions > 0 else 0
        }