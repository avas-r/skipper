"""
Service account schemas for the orchestrator API.

This module defines Pydantic models for service account-related API requests and responses.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field

class ServiceAccountBase(BaseModel):
    """Base schema for service account data"""
    username: str
    display_name: str
    description: Optional[str] = None
    account_type: str = "robot"
    status: str = "active"
    configuration: Optional[Dict[str, Any]] = None

class ServiceAccountCreate(ServiceAccountBase):
    """Schema for creating a new service account"""
    password: Optional[str] = None

class ServiceAccountUpdate(BaseModel):
    """Schema for updating a service account"""
    username: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    password: Optional[str] = None

class ServiceAccountInDBBase(ServiceAccountBase):
    """Base schema for service account in database"""
    account_id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    last_used: Optional[datetime] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class ServiceAccountResponse(ServiceAccountInDBBase):
    """Schema for service account response"""
    pass

class ServiceAccountCredentials(BaseModel):
    """Schema for service account credentials"""
    username: str
    password: str = Field(..., exclude=True)
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True