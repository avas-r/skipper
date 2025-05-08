"""
Schedule management endpoints for the orchestrator API.

This module provides endpoints for managing job schedules.
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Schedule
from ....schemas.schedule import (
    ScheduleCreate, 
    ScheduleUpdate, 
    ScheduleResponse,
    ScheduleWithJobsResponse
)
from ....services.schedule_service import ScheduleService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_schedule_read = PermissionChecker(["schedule:read"])
require_schedule_create = PermissionChecker(["schedule:create"])
require_schedule_update = PermissionChecker(["schedule:update"])
require_schedule_delete = PermissionChecker(["schedule:delete"])

@router.get("/", response_model=List[ScheduleResponse])
def list_schedules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all schedules with optional filtering.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # List schedules
    schedules = schedule_service.list_schedules(
        tenant_id=str(current_user.tenant_id),
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return schedules

@router.post("/", response_model=ScheduleResponse)
def create_schedule(
    schedule_in: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_create)
) -> Any:
    """
    Create a new schedule.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    try:
        # Create schedule
        schedule = schedule_service.create_schedule(
            schedule_in=schedule_in,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        
        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_read)
) -> Any:
    """
    Get a schedule by ID.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # Get schedule
    schedule = schedule_service.get_schedule(
        schedule_id=schedule_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )
    
    return schedule

@router.get("/{schedule_id}/with-jobs", response_model=ScheduleWithJobsResponse)
def get_schedule_with_jobs(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_read)
) -> Any:
    """
    Get a schedule with its associated jobs.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # Get schedule with jobs
    schedule = schedule_service.get_schedule_with_jobs(
        schedule_id=schedule_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )
    
    return schedule

@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: str,
    schedule_in: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_update)
) -> Any:
    """
    Update a schedule.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    try:
        # Update schedule
        schedule = schedule_service.update_schedule(
            schedule_id=schedule_id,
            schedule_in=schedule_in,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        
        if not schedule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule {schedule_id} not found"
            )
        
        return schedule
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_delete)
) -> None:
    """
    Delete a schedule.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # Check if schedule exists
    schedule = schedule_service.get_schedule(
        schedule_id=schedule_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )
    
    # Delete schedule
    try:
        deleted = schedule_service.delete_schedule(
            schedule_id=schedule_id,
            tenant_id=str(current_user.tenant_id)
        )
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete schedule {schedule_id}"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{schedule_id}/activate", response_model=ScheduleResponse)
def activate_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_update)
) -> Any:
    """
    Activate a schedule.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # Activate schedule
    schedule = schedule_service.update_schedule_status(
        schedule_id=schedule_id,
        tenant_id=str(current_user.tenant_id),
        status="active",
        user_id=str(current_user.user_id)
    )
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )
    
    return schedule

@router.post("/{schedule_id}/deactivate", response_model=ScheduleResponse)
def deactivate_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_update)
) -> Any:
    """
    Deactivate a schedule.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # Deactivate schedule
    schedule = schedule_service.update_schedule_status(
        schedule_id=schedule_id,
        tenant_id=str(current_user.tenant_id),
        status="inactive",
        user_id=str(current_user.user_id)
    )
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found"
        )
    
    return schedule

@router.post("/{schedule_id}/trigger", response_model=dict[str, Any])
def trigger_schedule(
    schedule_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_schedule_update)
) -> Any:
    """
    Trigger a schedule manually.
    """
    # Create schedule service
    schedule_service = ScheduleService(db)
    
    # Trigger schedule
    result = schedule_service.trigger_schedule(
        schedule_id=schedule_id,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id),
        background_tasks=background_tasks
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule {schedule_id} not found or has no jobs"
        )
    
    return result