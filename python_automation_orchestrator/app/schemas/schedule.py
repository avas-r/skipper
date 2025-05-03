"""
Schedule schemas for the orchestrator API.

This module defines Pydantic models for schedule-related API requests and responses.
"""

import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator
from croniter import croniter

class ScheduleBase(BaseModel):
    """Base schema for schedule data"""
    name: str
    description: Optional[str] = None
    cron_expression: str
    timezone: str = "UTC"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    @validator("cron_expression")
    def validate_cron_expression(cls, v):
        """Validate cron expression format"""
        if not croniter.is_valid(v):
            raise ValueError("Invalid cron expression format")
        return v

class ScheduleCreate(ScheduleBase):
    """Schema for creating a new schedule"""
    pass

class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule"""
    name: Optional[str] = None
    description: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    
    @validator("cron_expression")
    def validate_cron_expression(cls, v):
        """Validate cron expression format"""
        if v is not None and not croniter.is_valid(v):
            raise ValueError("Invalid cron expression format")
        return v
    
    @validator("status")
    def validate_status(cls, v):
        """Validate status"""
        valid_statuses = ["active", "inactive"]
        if v is not None and v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class ScheduleInDBBase(ScheduleBase):
    """Base schema for schedule in database"""
    schedule_id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    
    class Config:
        """Configuration for Pydantic model"""
        orm_mode = True

class ScheduleResponse(ScheduleInDBBase):
    """Schema for schedule response"""
    pass

class JobInfoResponse(BaseModel):
    """Schema for basic job information"""
    job_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    
    class Config:
        """Configuration for Pydantic model"""
        orm_mode = True

class ScheduleWithJobsResponse(ScheduleResponse):
    """Schema for schedule with associated jobs"""
    jobs: List[JobInfoResponse] = []

class ScheduleExecutionInfo(BaseModel):
    """Schema for schedule execution information"""
    execution_time: datetime
    trigger_type: str = "scheduled"  # "scheduled", "manual"
    triggered_by: Optional[uuid.UUID] = None

class ScheduleTriggerResponse(BaseModel):
    """Schema for schedule trigger response"""
    schedule_id: uuid.UUID
    name: str
    jobs_triggered: int
    jobs: List[Dict[str, Any]] = []