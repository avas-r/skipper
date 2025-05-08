"""
Job schemas for the orchestrator API.

This module defines Pydantic models for job-related API requests and responses.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator

class JobBase(BaseModel):
    """Base schema for job data"""
    name: str
    description: Optional[str] = None
    priority: Optional[int] = 1
    max_concurrent_runs: Optional[int] = 1
    timeout_seconds: Optional[int] = 3600
    retry_count: Optional[int] = 0
    retry_delay_seconds: Optional[int] = 60
    parameters: Optional[Dict[str, Any]] = None

class JobCreate(JobBase):
    """Schema for creating a new job"""
    package_id: uuid.UUID
    schedule_id: Optional[uuid.UUID] = None
    queue_id: Optional[uuid.UUID] = None
    depends_on_job_ids: Optional[List[uuid.UUID]] = None
    asset_ids: Optional[List[uuid.UUID]] = None
    
    @validator('max_concurrent_runs')
    def validate_max_concurrent_runs(cls, v):
        if v is not None and v < 1:
            raise ValueError('max_concurrent_runs must be at least 1')
        return v

class JobUpdate(BaseModel):
    """Schema for updating a job"""
    name: Optional[str] = None
    description: Optional[str] = None
    package_id: Optional[uuid.UUID] = None
    schedule_id: Optional[uuid.UUID] = None
    queue_id: Optional[uuid.UUID] = None
    priority: Optional[int] = None
    max_concurrent_runs: Optional[int] = None
    timeout_seconds: Optional[int] = None
    retry_count: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class JobResponse(BaseModel):
    """Schema for job response"""
    job_id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str] = None
    package_id: uuid.UUID
    schedule_id: Optional[uuid.UUID] = None
    queue_id: Optional[uuid.UUID] = None
    priority: int
    max_concurrent_runs: int
    timeout_seconds: int
    retry_count: int
    retry_delay_seconds: int
    parameters: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    last_execution_status: Optional[str] = None
    last_execution_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class JobStartRequest(BaseModel):
    """Schema for manually starting a job"""
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    queue_id: Optional[uuid.UUID] = None

class JobExecutionBase(BaseModel):
    """Base schema for job execution"""
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    agent_id: Optional[uuid.UUID] = None
    input_parameters: Optional[Dict[str, Any]] = None
    output_results: Optional[Dict[str, Any]] = None

class JobExecutionResponse(JobExecutionBase):
    """Schema for job execution response"""
    execution_id: uuid.UUID
    job_id: uuid.UUID
    tenant_id: uuid.UUID
    trigger_type: str
    created_at: datetime
    updated_at: datetime
    logs_path: Optional[str] = None
    screenshots_path: Optional[str] = None
    recording_path: Optional[str] = None
    job_name: Optional[str] = None
    package_name: Optional[str] = None
    agent_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class JobExecutionFilter(BaseModel):
    """Schema for filtering job executions"""
    status: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    agent_id: Optional[uuid.UUID] = None
    package_id: Optional[uuid.UUID] = None
    trigger_type: Optional[str] = None

class JobWithExecutionsResponse(JobResponse):
    """Schema for job with executions response"""
    executions: List[JobExecutionResponse] = []
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    average_execution_time_ms: Optional[float] = None