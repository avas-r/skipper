"""
Job management endpoints for the orchestrator API.

This module provides endpoints for managing automation jobs.
"""

import logging
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Query
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Job, JobExecution
from ....schemas.job import (
    JobCreate, 
    JobUpdate, 
    JobResponse,
    JobExecutionResponse,
    JobStartRequest,
    JobExecutionFilter,
    JobWithExecutionsResponse
)
from ....services.job_service import JobService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_job_read = PermissionChecker(["job:read"])
require_job_create = PermissionChecker(["job:create"])
require_job_update = PermissionChecker(["job:update"])
require_job_delete = PermissionChecker(["job:delete"])
require_job_execute = PermissionChecker(["job:execute"])

@router.get("/", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    package_id: Optional[str] = None,
    schedule_id: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all jobs with optional filtering.
    """
    # Create job service
    job_service = JobService(db)
    
    # List jobs
    jobs = job_service.list_jobs(
        tenant_id=str(current_user.tenant_id),
        status=status,
        package_id=package_id,
        schedule_id=schedule_id,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return jobs

@router.post("/", response_model=JobResponse)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_create)
) -> Any:
    """
    Create a new job.
    """
    # Create job service
    job_service = JobService(db)
    
    try:
        # Create job
        job = job_service.create_job(
            job_in=job_in,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        
        return job
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read)
) -> Any:
    """
    Get a job by ID.
    """
    # Create job service
    job_service = JobService(db)
    
    # Get job
    job = job_service.get_job(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job

@router.get("/{job_id}/with-executions", response_model=JobWithExecutionsResponse)
def get_job_with_executions(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read),
    limit: int = 10
) -> Any:
    """
    Get a job with its recent executions.
    """
    # Create job service
    job_service = JobService(db)
    
    # Get job with executions
    job = job_service.get_job_with_executions(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id),
        limit=limit
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_update)
) -> Any:
    """
    Update a job.
    """
    # Create job service
    job_service = JobService(db)
    
    try:
        # Update job
        job = job_service.update_job(
            job_id=job_id,
            job_in=job_in,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return job
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_delete)
) -> None:
    """
    Delete a job.
    """
    # Create job service
    job_service = JobService(db)
    
    # Check if job exists
    job = job_service.get_job(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Delete job
    try:
        deleted = job_service.delete_job(
            job_id=job_id,
            tenant_id=str(current_user.tenant_id)
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete job {job_id}"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{job_id}/start", response_model=Dict[str, Any])
def start_job(
    job_id: str,
    start_request: Optional[JobStartRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_execute)
) -> Any:
    """
    Start a job manually.
    """
    # Create job service
    job_service = JobService(db)
    
    # Check if job exists
    job = job_service.get_job(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Start job
    try:
        parameters = start_request.parameters if start_request else None
        agent_id = start_request.agent_id if start_request else None
        
        result = job_service.start_job(
            job_id=job_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            parameters=parameters,
            agent_id=agent_id,
            background_tasks=background_tasks
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{job_id}/stop", response_model=Dict[str, Any])
def stop_job(
    job_id: str,
    execution_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_execute)
) -> Any:
    """
    Stop a running job.
    """
    # Create job service
    job_service = JobService(db)
    
    # Check if job exists
    job = job_service.get_job(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Stop job
    try:
        result = job_service.stop_job(
            job_id=job_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            execution_id=execution_id,
            background_tasks=background_tasks
        )
        
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/executions/", response_model=List[JobExecutionResponse])
def list_job_executions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read),
    job_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    List job executions with filtering.
    """
    # Create job service
    job_service = JobService(db)
    
    # Create filter
    filter = JobExecutionFilter(
        job_id=job_id,
        agent_id=agent_id,
        status=status,
        from_date=from_date,
        to_date=to_date
    )
    
    # List executions
    executions = job_service.list_job_executions(
        tenant_id=str(current_user.tenant_id),
        filter=filter,
        skip=skip,
        limit=limit
    )
    
    return executions

@router.get("/executions/{execution_id}", response_model=JobExecutionResponse)
def get_job_execution(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read)
) -> Any:
    """
    Get a job execution by ID.
    """
    # Create job service
    job_service = JobService(db)
    
    # Get execution
    execution = job_service.get_job_execution(
        execution_id=execution_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job execution {execution_id} not found"
        )
    
    return execution

@router.get("/executions/{execution_id}/logs", response_model=Dict[str, Any])
def get_job_execution_logs(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read)
) -> Any:
    """
    Get logs for a job execution.
    """
    # Create job service
    job_service = JobService(db)
    
    # Check if execution exists
    execution = job_service.get_job_execution(
        execution_id=execution_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job execution {execution_id} not found"
        )
    
    # Get logs
    logs = job_service.get_execution_logs(
        execution_id=execution_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    return logs

@router.get("/executions/{execution_id}/screenshots", response_model=List[Dict[str, Any]])
def get_job_execution_screenshots(
    execution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_read)
) -> Any:
    """
    Get screenshots for a job execution.
    """
    # Create job service
    job_service = JobService(db)
    
    # Check if execution exists
    execution = job_service.get_job_execution(
        execution_id=execution_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job execution {execution_id} not found"
        )
    
    # Get screenshots
    screenshots = job_service.get_execution_screenshots(
        execution_id=execution_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    return screenshots

@router.post("/{job_id}/activate", response_model=JobResponse)
def activate_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_update)
) -> Any:
    """
    Activate a job.
    """
    # Create job service
    job_service = JobService(db)
    
    # Activate job
    job = job_service.update_job_status(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id),
        status="active",
        user_id=str(current_user.user_id)
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job

@router.post("/{job_id}/deactivate", response_model=JobResponse)
def deactivate_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_job_update)
) -> Any:
    """
    Deactivate a job.
    """
    # Create job service
    job_service = JobService(db)
    
    # Deactivate job
    job = job_service.update_job_status(
        job_id=job_id,
        tenant_id=str(current_user.tenant_id),
        status="inactive",
        user_id=str(current_user.user_id)
    )
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return job