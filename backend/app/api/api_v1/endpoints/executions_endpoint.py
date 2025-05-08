"""
Job execution endpoints for the orchestrator API.

This module provides endpoints for managing job executions.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, JobExecution, Job
from ....schemas.job import (
    JobExecutionResponse,
    JobExecutionFilter,
    JobStartRequest,
)
from ....services.job_service import JobService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_execution_read = PermissionChecker(["job:read"])
require_execution_start = PermissionChecker(["job:execute"])
require_execution_update = PermissionChecker(["job:update"])

@router.get("/", response_model=List[JobExecutionResponse])
async def list_executions(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_execution_read),
    job_id: Optional[uuid.UUID] = None,
    status: Optional[List[str]] = Query(None),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[uuid.UUID] = None,
    package_id: Optional[uuid.UUID] = None,
    trigger_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List job executions with optional filtering.
    """
    # Create filter params
    filter_params = JobExecutionFilter(
        status=status,
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id,
        package_id=package_id,
        trigger_type=trigger_type
    )
    
    # Create job service
    job_service = JobService(db)
    
    # List executions
    executions, total = job_service.list_executions(
        tenant_id=current_user.tenant_id,
        job_id=job_id,
        filter_params=filter_params,
        skip=skip,
        limit=limit
    )
    
    # Convert to response models and add additional info
    result = []
    for execution in executions:
        response = JobExecutionResponse.from_orm(execution)
        
        # Add job and agent info if available
        if execution.job:
            response.job_name = execution.job.name
            
            # Add package name if available
            if hasattr(execution.job, "package") and execution.job.package:
                response.package_name = execution.job.package.name
                
        if execution.agent:
            response.agent_name = execution.agent.name
            
        result.append(response)
    
    return result

@router.get("/{execution_id}", response_model=JobExecutionResponse)
async def get_execution(
    execution_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_execution_read),
) -> Any:
    """
    Get job execution by ID.
    """
    # Create job service
    job_service = JobService(db)
    
    # Get execution
    execution = job_service.get_execution(
        execution_id=execution_id,
        tenant_id=current_user.tenant_id
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job execution not found"
        )
    
    # Convert to response model
    response = JobExecutionResponse.from_orm(execution)
    
    # Add job and agent info if available
    if execution.job:
        response.job_name = execution.job.name
        
        # Add package name if available
        if hasattr(execution.job, "package") and execution.job.package:
            response.package_name = execution.job.package.name
            
    if execution.agent:
        response.agent_name = execution.agent.name
    
    return response

@router.post("/jobs/{job_id}/start", response_model=JobExecutionResponse)
async def start_job(
    job_id: uuid.UUID,
    start_request: JobStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_execution_start),
) -> Any:
    """
    Start a job execution.
    """
    # Create job service
    job_service = JobService(db)
    
    try:
        # Start job
        execution = await job_service.start_job(
            job_id=job_id,
            tenant_id=current_user.tenant_id,
            start_request=start_request
        )
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        # Convert to response model
        response = JobExecutionResponse.from_orm(execution)
        
        # Add job info if available
        job = job_service.get_job(job_id, current_user.tenant_id)
        if job:
            response.job_name = job.name
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{execution_id}/cancel", response_model=JobExecutionResponse)
async def cancel_execution(
    execution_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_execution_update),
) -> Any:
    """
    Cancel a job execution.
    """
    # Create job service
    job_service = JobService(db)
    
    # Cancel execution
    execution = await job_service.cancel_execution(
        execution_id=execution_id,
        tenant_id=current_user.tenant_id
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job execution not found or cannot be cancelled"
        )
    
    # Convert to response model
    response = JobExecutionResponse.from_orm(execution)
    
    # Add job and agent info if available
    if execution.job:
        response.job_name = execution.job.name
        
    if execution.agent:
        response.agent_name = execution.agent.name
    
    return response

@router.get("/{execution_id}/logs")
async def get_execution_logs(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_execution_read),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get job execution logs.
    """
    # Create job service
    job_service = JobService(db)
    
    # Get execution to verify it exists and belongs to tenant
    execution = job_service.get_execution(
        execution_id=execution_id,
        tenant_id=current_user.tenant_id
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job execution not found"
        )
    
    # Get logs from object storage or database
    # This is placeholder - in a real implementation, we'd fetch logs
    # from wherever they're stored
    
    return {
        "execution_id": str(execution_id),
        "logs": [
            {"timestamp": execution.created_at, "level": "INFO", "message": "Execution started"},
            {"timestamp": execution.updated_at, "level": "INFO", "message": f"Execution status: {execution.status}"}
        ]
    }

@router.get("/{execution_id}/playback")
async def get_execution_playback(
    execution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_execution_read),
) -> Any:
    """
    Get job execution playback data (steps, screenshots, recordings).
    """
    # Create job service
    job_service = JobService(db)
    
    # Get execution to verify it exists and belongs to tenant
    execution = job_service.get_execution(
        execution_id=execution_id,
        tenant_id=current_user.tenant_id
    )
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job execution not found"
        )
    
    # Placeholder for real implementation that would:
    # 1. Get execution steps from storage
    # 2. Get screenshots/recording metadata
    # 3. Generate URLs for resources
    
    return {
        "execution_id": str(execution_id),
        "job_id": str(execution.job_id),
        "job_name": execution.job.name if execution.job else "Unknown Job",
        "status": execution.status,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "execution_time_ms": execution.execution_time_ms,
        "steps": [],
        "screenshots": [],
        "has_recording": False,
        "recording_url": None
    }