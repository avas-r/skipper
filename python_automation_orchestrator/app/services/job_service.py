"""
Job service for managing automation jobs.

This module provides services for managing jobs, job executions, and related operations.
"""

import logging
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from fastapi import UploadFile
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session, joinedload

from ..db.session import SessionLocal
from ..models import Job, JobExecution, JobDependency, Package, Agent, User, Queue, QueueItem, Schedule
from ..schemas.job import JobCreate, JobUpdate, JobStartRequest, JobExecutionFilter
from ..messaging.producer import get_message_producer
from ..utils.object_storage import ObjectStorage
from ..config import settings

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
        
    def create_job(self, job_in: JobCreate, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Job:
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
        if job_in.package_id:
            package = self.db.query(Package).filter(
                Package.package_id == job_in.package_id,
                Package.tenant_id == tenant_id
            ).first()
            
            if not package:
                raise ValueError(f"Package {job_in.package_id} not found")
        
        # Validate schedule exists and belongs to tenant
        if job_in.schedule_id:
            schedule = self.db.query(Schedule).filter(
                Schedule.schedule_id == job_in.schedule_id,
                Schedule.tenant_id == tenant_id
            ).first()
            
            if not schedule:
                raise ValueError(f"Schedule {job_in.schedule_id} not found")
        
        # Create job
        job_data = job_in.dict(exclude_unset=True)
        job_data["tenant_id"] = tenant_id
        job_data["created_by"] = user_id
        job_data["updated_by"] = user_id
        
        job = Job(**job_data)
        
        # Add job to database
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def update_job(self, job_id: uuid.UUID, job_in: JobUpdate, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Job]:
        """
        Update a job.
        
        Args:
            job_id: Job ID
            job_in: Job update data
            tenant_id: Tenant ID
            user_id: User ID updating the job
            
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
        
        # Validate package exists and belongs to tenant
        if job_in.package_id:
            package = self.db.query(Package).filter(
                Package.package_id == job_in.package_id,
                Package.tenant_id == tenant_id
            ).first()
            
            if not package:
                raise ValueError(f"Package {job_in.package_id} not found")
        
        # Validate schedule exists and belongs to tenant
        if job_in.schedule_id:
            schedule = self.db.query(Schedule).filter(
                Schedule.schedule_id == job_in.schedule_id,
                Schedule.tenant_id == tenant_id
            ).first()
            
            if not schedule:
                raise ValueError(f"Schedule {job_in.schedule_id} not found")
        
        # Update job
        job_data = job_in.dict(exclude_unset=True)
        
        for key, value in job_data.items():
            setattr(job, key, value)
        
        # Update audit fields
        job.updated_at = datetime.utcnow()
        job.updated_by = user_id
        
        # Update database
        self.db.commit()
        self.db.refresh(job)
        
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
    
    def get_job_with_executions(self, job_id: uuid.UUID, tenant_id: uuid.UUID, limit: int = 10) -> Optional[Dict[str, Any]]:
        """
        Get a job with its recent executions.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            limit: Maximum number of executions to return
            
        Returns:
            Optional[Dict[str, Any]]: Job with executions or None if not found
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            return None
        
        # Get recent executions
        executions = self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id,
            JobExecution.tenant_id == tenant_id
        ).order_by(JobExecution.started_at.desc()).limit(limit).all()
        
        # Return job with executions
        return {
            "job": job,
            "executions": executions
        }
    
    def list_jobs(
        self,
        tenant_id: uuid.UUID,
        status: Optional[str] = None,
        package_id: Optional[uuid.UUID] = None,
        schedule_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Job]:
        """
        List jobs with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            package_id: Optional package ID filter
            schedule_id: Optional schedule ID filter
            search: Optional search term for name/description
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Job]: List of jobs
        """
        # Base query
        query = self.db.query(Job).filter(Job.tenant_id == tenant_id)
        
        # Apply filters
        if status:
            query = query.filter(Job.status == status)
            
        if package_id:
            query = query.filter(Job.package_id == package_id)
            
        if schedule_id:
            query = query.filter(Job.schedule_id == schedule_id)
            
        if search:
            query = query.filter(
                or_(
                    Job.name.ilike(f"%{search}%"),
                    Job.description.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination and sorting
        query = query.order_by(Job.name).offset(skip).limit(limit)
        
        return query.all()
    
    def delete_job(self, job_id: uuid.UUID, tenant_id: uuid.UUID) -> bool:
        """
        Delete a job.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If there are active schedules or executions
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            return False
        
        # Check if job has scheduled executions
        if job.schedule_id and job.status == "active":
            raise ValueError("Cannot delete job with active schedule")
        
        # Check if job has running executions
        running_executions = self.db.query(JobExecution).filter(
            JobExecution.job_id == job_id,
            JobExecution.status.in_(["queued", "running"])
        ).count()
        
        if running_executions > 0:
            raise ValueError(f"Cannot delete job with {running_executions} running executions")
        
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
    
    def update_job_status(self, job_id: uuid.UUID, tenant_id: uuid.UUID, status: str, user_id: Optional[uuid.UUID] = None) -> Optional[Job]:
        """
        Update job status.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            status: New status
            user_id: User ID updating the status
            
        Returns:
            Optional[Job]: Updated job or None if not found
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            return None
        
        # Update status
        job.status = status
        
        # Update audit fields
        job.updated_at = datetime.utcnow()
        if user_id:
            job.updated_by = user_id
        
        # Update database
        self.db.commit()
        self.db.refresh(job)
        
        return job
    
    def start_job(
        self, 
        job_id: uuid.UUID, 
        tenant_id: uuid.UUID, 
        user_id: uuid.UUID,
        parameters: Optional[Dict[str, Any]] = None,
        agent_id: Optional[uuid.UUID] = None,
        background_tasks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Start a job manually.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            user_id: User ID starting the job
            parameters: Optional parameters to pass to the job
            agent_id: Optional agent ID to run the job on
            background_tasks: Optional background tasks to run
            
        Returns:
            Dict[str, Any]: Job execution information
            
        Raises:
            ValueError: If job not found or invalid
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Get package if specified
        package = None
        if job.package_id:
            package = self.db.query(Package).filter(
                Package.package_id == job.package_id,
                Package.tenant_id == tenant_id
            ).first()
            
            if not package:
                raise ValueError(f"Package {job.package_id} not found")
        
        # Get agent if specified
        if agent_id:
            agent = self.db.query(Agent).filter(
                Agent.agent_id == agent_id,
                Agent.tenant_id == tenant_id
            ).first()
            
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
        else:
            # Auto-select agent if not specified
            agent = self._select_agent_for_job(job)
            if not agent:
                raise ValueError("No suitable agent found for job")
            
            agent_id = agent.agent_id
        
        # Create execution record
        execution = JobExecution(
            execution_id=uuid.uuid4(),
            job_id=job_id,
            tenant_id=tenant_id,
            agent_id=agent_id,
            package_id=job.package_id,
            parameters=parameters or job.parameters or {},
            status="queued",
            created_by=user_id,
            priority=job.priority or 1
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        # Send job to queue
        if background_tasks:
            background_tasks.add_task(
                self._send_job_to_agent,
                execution_id=execution.execution_id,
                agent_id=agent_id,
                tenant_id=tenant_id
            )
        else:
            # Execute immediately (synchronously)
            self._send_job_to_agent(
                execution_id=execution.execution_id,
                agent_id=agent_id,
                tenant_id=tenant_id
            )
        
        return {
            "execution_id": execution.execution_id,
            "status": "queued",
            "agent_id": agent_id
        }
        
    def create_package_execution(
        self,
        agent_id: uuid.UUID,
        tenant_id: uuid.UUID,
        package_id: uuid.UUID,
        parameters: Optional[Dict[str, Any]] = None
    ) -> JobExecution:
        """
        Create a package execution.
        
        This is used for direct package executions from agents without a parent job.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            package_id: Package ID
            parameters: Optional parameters
            
        Returns:
            JobExecution: Created execution record
            
        Raises:
            ValueError: If package not found or invalid
        """
        # Validate package
        package = self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            raise ValueError(f"Package {package_id} not found")
            
        # Create execution record (without a job)
        execution = JobExecution(
            execution_id=uuid.uuid4(),
            job_id=None,  # No parent job
            tenant_id=tenant_id,
            agent_id=agent_id,
            package_id=package_id,
            parameters=parameters or {},
            status="queued",
            is_direct_execution=True  # Flag to indicate direct package execution
        )
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        return execution
        
    def update_execution_status(
        self,
        execution_id: uuid.UUID,
        agent_id: uuid.UUID,
        tenant_id: uuid.UUID,
        status: str,
        progress: Optional[float] = None,
        results: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[JobExecution]:
        """
        Update execution status.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            tenant_id: Tenant ID
            status: New status
            progress: Optional progress (0-100)
            results: Optional results data
            error: Optional error message
            
        Returns:
            Optional[JobExecution]: Updated execution or None if not found
        """
        # Get execution
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).first()
        
        if not execution:
            return None
            
        # Verify agent matches
        if execution.agent_id != agent_id:
            logger.warning(f"Agent {agent_id} tried to update execution {execution_id} belonging to agent {execution.agent_id}")
            return None
            
        # Update status
        execution.status = status
        
        # Update progress if provided
        if progress is not None:
            execution.progress = progress
            
        # Update results if provided
        if results:
            execution.results = results
            
        # Update error if provided
        if error:
            execution.error = error
            
        # Update timestamps
        if status == "running" and not execution.started_at:
            execution.started_at = datetime.utcnow()
        elif status in ["completed", "failed", "cancelled"]:
            execution.ended_at = datetime.utcnow()
            
        # Save changes
        self.db.commit()
        self.db.refresh(execution)
        
        return execution
        
    def get_execution(self, execution_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[JobExecution]:
        """
        Get a job execution.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[JobExecution]: Execution or None if not found
        """
        return self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).first()
        
    def save_execution_result(
        self,
        execution_id: uuid.UUID,
        file: UploadFile,
        result_type: str
    ) -> str:
        """
        Save a file from an execution.
        
        Args:
            execution_id: Execution ID
            file: Uploaded file
            result_type: Type of result file
            
        Returns:
            str: Path to the saved file
            
        Raises:
            ValueError: If execution not found or invalid
        """
        # Get execution
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id
        ).first()
        
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
            
        # Create result directory if it doesn't exist
        result_dir = os.path.join(settings.EXECUTIONS_FOLDER, str(execution_id), "results")
        os.makedirs(result_dir, exist_ok=True)
        
        # Generate file name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        file_name = f"{timestamp}_{result_type}{file_extension}"
        file_path = os.path.join(result_dir, file_name)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(file.file.read())
            
        # Store reference in results
        if not execution.results:
            execution.results = {}
            
        if "files" not in execution.results:
            execution.results["files"] = []
            
        execution.results["files"].append({
            "type": result_type,
            "path": file_path,
            "name": file_name,
            "timestamp": timestamp
        })
        
        # Save changes
        self.db.commit()
        
        return file_path
    
    def list_job_executions(
        self,
        tenant_id: uuid.UUID,
        filter: JobExecutionFilter,
        skip: int = 0,
        limit: int = 100
    ) -> List[JobExecution]:
        """
        List job executions with filtering.
        
        Args:
            tenant_id: Tenant ID
            filter: Filter criteria
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[JobExecution]: List of job executions
        """
        # Base query
        query = self.db.query(JobExecution).filter(JobExecution.tenant_id == tenant_id)
        
        # Apply filters
        if filter.job_id:
            query = query.filter(JobExecution.job_id == filter.job_id)
            
        if filter.agent_id:
            query = query.filter(JobExecution.agent_id == filter.agent_id)
            
        if filter.status:
            query = query.filter(JobExecution.status == filter.status)
            
        if filter.from_date:
            try:
                from_date = datetime.fromisoformat(filter.from_date)
                query = query.filter(JobExecution.created_at >= from_date)
            except ValueError:
                pass
                
        if filter.to_date:
            try:
                to_date = datetime.fromisoformat(filter.to_date)
                query = query.filter(JobExecution.created_at <= to_date)
            except ValueError:
                pass
        
        # Apply pagination and sorting
        query = query.order_by(JobExecution.created_at.desc()).offset(skip).limit(limit)
        
        return query.all()
    
    def get_job_execution(self, execution_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[JobExecution]:
        """
        Get a job execution by ID.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[JobExecution]: Job execution or None if not found
        """
        return self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).first()
    
    def stop_job(
        self, 
        job_id: uuid.UUID, 
        tenant_id: uuid.UUID, 
        user_id: uuid.UUID,
        execution_id: Optional[uuid.UUID] = None,
        background_tasks: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Stop a running job.
        
        Args:
            job_id: Job ID
            tenant_id: Tenant ID
            user_id: User ID stopping the job
            execution_id: Optional specific execution ID to stop
            background_tasks: Optional background tasks to run
            
        Returns:
            Dict[str, Any]: Stop result information
            
        Raises:
            ValueError: If job not found or not running
        """
        # Get job
        job = self.db.query(Job).filter(
            Job.job_id == job_id,
            Job.tenant_id == tenant_id
        ).first()
        
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Get running executions
        if execution_id:
            executions = self.db.query(JobExecution).filter(
                JobExecution.execution_id == execution_id,
                JobExecution.job_id == job_id,
                JobExecution.tenant_id == tenant_id,
                JobExecution.status.in_(["queued", "running"])
            ).all()
        else:
            # Get all running executions for the job
            executions = self.db.query(JobExecution).filter(
                JobExecution.job_id == job_id,
                JobExecution.tenant_id == tenant_id,
                JobExecution.status.in_(["queued", "running"])
            ).all()
        
        if not executions:
            raise ValueError(f"No running executions found for job {job_id}")
        
        # Stop each execution
        stopped_count = 0
        
        for execution in executions:
            # Update status to cancelled
            execution.status = "cancelled"
            execution.ended_at = datetime.utcnow()
            
            # Send stop command to agent
            if background_tasks:
                background_tasks.add_task(
                    self._send_stop_command,
                    execution_id=execution.execution_id,
                    agent_id=execution.agent_id,
                    tenant_id=tenant_id
                )
            else:
                # Execute immediately (synchronously)
                self._send_stop_command(
                    execution_id=execution.execution_id,
                    agent_id=execution.agent_id,
                    tenant_id=tenant_id
                )
                
            stopped_count += 1
        
        # Save changes
        self.db.commit()
        
        return {
            "success": True,
            "stopped_count": stopped_count,
            "message": f"Stopped {stopped_count} executions"
        }
    
    def get_execution_logs(self, execution_id: uuid.UUID, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get logs for a job execution.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            Dict[str, Any]: Log information
            
        Raises:
            ValueError: If execution not found
        """
        # Get execution
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).first()
        
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Get logs from storage or database
        logs = {
            "execution_id": str(execution_id),
            "status": execution.status,
            "logs": []  # Placeholder for log entries
        }
        
        # Implement log retrieval from storage or database
        # This is a placeholder - actual implementation would depend on
        # how logs are stored
        
        return logs
    
    def get_execution_screenshots(self, execution_id: uuid.UUID, tenant_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Get screenshots for a job execution.
        
        Args:
            execution_id: Execution ID
            tenant_id: Tenant ID
            
        Returns:
            List[Dict[str, Any]]: Screenshot information
            
        Raises:
            ValueError: If execution not found
        """
        # Get execution
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id,
            JobExecution.tenant_id == tenant_id
        ).first()
        
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Get screenshots from storage or database
        screenshots = []
        
        # Check if execution has results with screenshots
        if execution.results and "screenshots" in execution.results:
            screenshots = execution.results["screenshots"]
        
        return screenshots
    
    def _select_agent_for_job(self, job: Job) -> Optional[Agent]:
        """
        Select a suitable agent for a job.
        
        Args:
            job: Job to select agent for
            
        Returns:
            Optional[Agent]: Selected agent or None if none available
        """
        # Get online agents for tenant
        agents = self.db.query(Agent).filter(
            Agent.tenant_id == job.tenant_id,
            Agent.status == "online"
        ).all()
        
        # Filter agents by capabilities if job requires specific capabilities
        if job.required_capabilities:
            eligible_agents = []
            for agent in agents:
                if not agent.capabilities:
                    continue
                    
                matches = True
                for cap_name, cap_value in job.required_capabilities.items():
                    if cap_name not in agent.capabilities:
                        matches = False
                        break
                        
                    if agent.capabilities[cap_name] != cap_value:
                        matches = False
                        break
                        
                if matches:
                    eligible_agents.append(agent)
                    
            agents = eligible_agents
        
        # Return first suitable agent (or implement more sophisticated selection)
        if agents:
            return agents[0]
        else:
            return None
    
    async def _send_job_to_agent(self, execution_id: uuid.UUID, agent_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        """
        Send a job to an agent.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            tenant_id: Tenant ID
        """
        # Get execution details
        execution = self.db.query(JobExecution).filter(
            JobExecution.execution_id == execution_id
        ).first()
        
        if not execution:
            logger.error(f"Cannot send job: execution {execution_id} not found")
            return
        
        # Get job details
        job = None
        if execution.job_id:
            job = self.db.query(Job).filter(
                Job.job_id == execution.job_id
            ).first()
        
        # Get package details
        package = None
        if execution.package_id:
            package = self.db.query(Package).filter(
                Package.package_id == execution.package_id
            ).first()
        
        # Create command message
        command = {
            "type": "execute_job",
            "execution_id": str(execution_id),
            "job_id": str(execution.job_id) if execution.job_id else None,
            "package_id": str(execution.package_id) if execution.package_id else None,
            "parameters": execution.parameters,
            "timeout_seconds": job.timeout_seconds if job else 3600,
            "priority": execution.priority
        }
        
        # Update execution status
        execution.status = "sent"
        execution.sent_at = datetime.utcnow()
        self.db.commit()
        
        # Send message to agent
        message_producer = get_message_producer()
        await message_producer.send_message(
            exchange="agents",
            routing_key=f"agent.{agent_id}.command",
            message_data={
                "agent_id": str(agent_id),
                "tenant_id": str(tenant_id),
                "command": command
            }
        )
    
    async def _send_stop_command(self, execution_id: uuid.UUID, agent_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        """
        Send a stop command to an agent.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            tenant_id: Tenant ID
        """
        # Create command message
        command = {
            "type": "stop_job",
            "execution_id": str(execution_id)
        }
        
        # Send message to agent
        message_producer = get_message_producer()
        await message_producer.send_message(
            exchange="agents",
            routing_key=f"agent.{agent_id}.command",
            message_data={
                "agent_id": str(agent_id),
                "tenant_id": str(tenant_id),
                "command": command
            }
        )