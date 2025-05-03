"""
Tenant schemas for the orchestrator API.

This module defines Pydantic models for tenant-related API requests and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator

class TenantBase(BaseModel):
    """Base schema for tenant data"""
    name: str
    subscription_tier: Optional[str] = "standard"
    max_concurrent_jobs: Optional[int] = 50
    max_agents: Optional[int] = 10
    settings: Optional[Dict[str, Any]] = None

    @validator("subscription_tier")
    def validate_subscription_tier(cls, v):
        """Validate subscription tier"""
        valid_tiers = ["free", "standard", "professional", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f"Invalid subscription tier. Must be one of: {', '.join(valid_tiers)}")
        return v

class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""
    status: Optional[str] = "active"

    @validator("status")
    def validate_status(cls, v):
        """Validate tenant status"""
        valid_statuses = ["active", "suspended", "pending", "archived"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class TenantUpdate(BaseModel):
    """Schema for updating a tenant"""
    name: Optional[str] = None
    status: Optional[str] = None
    subscription_tier: Optional[str] = None
    max_concurrent_jobs: Optional[int] = None
    max_agents: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None

    @validator("status")
    def validate_status(cls, v):
        """Validate tenant status"""
        if v is not None:
            valid_statuses = ["active", "suspended", "pending", "archived"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

    @validator("subscription_tier")
    def validate_subscription_tier(cls, v):
        """Validate subscription tier"""
        if v is not None:
            valid_tiers = ["free", "standard", "professional", "enterprise"]
            if v not in valid_tiers:
                raise ValueError(f"Invalid subscription tier. Must be one of: {', '.join(valid_tiers)}")
        return v

    @validator("max_concurrent_jobs")
    def validate_max_concurrent_jobs(cls, v):
        """Validate max concurrent jobs"""
        if v is not None and v < 1:
            raise ValueError("Max concurrent jobs must be at least 1")
        return v

    @validator("max_agents")
    def validate_max_agents(cls, v):
        """Validate max agents"""
        if v is not None and v < 1:
            raise ValueError("Max agents must be at least 1")
        return v

class TenantInDB(TenantBase):
    """Base schema for tenant in database"""
    tenant_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        orm_mode = True

class TenantResponse(TenantInDB):
    """Schema for tenant response"""
    pass

class TenantUsageResponse(BaseModel):
    """Schema for tenant resource usage response"""
    users: Dict[str, Any]
    agents: Dict[str, Any]
    jobs: Dict[str, Any]

class TenantStats(BaseModel):
    """Schema for tenant statistics"""
    tenant_id: UUID
    name: str
    user_count: int
    agent_count: int
    active_job_count: int
    running_job_count: int
    status: str
    subscription_tier: str