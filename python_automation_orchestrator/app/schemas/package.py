"""
Package schemas for the orchestrator API.

This module defines Pydantic models for package-related API requests and responses.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator

class PackageBase(BaseModel):
    """Base schema for package data"""
    name: str
    description: Optional[str] = None
    version: str
    main_file_path: str
    entry_point: str
    tags: Optional[List[str]] = None
    dependencies: Optional[Dict[str, str]] = None

class PackageCreate(PackageBase):
    """Schema for creating a new package"""
    tenant_id: Optional[uuid.UUID] = None
    status: Optional[str] = "development"

class PackageUpdate(BaseModel):
    """Schema for updating a package"""
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    main_file_path: Optional[str] = None
    entry_point: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[Dict[str, str]] = None

class PackageInDBBase(PackageBase):
    """Base schema for package in database"""
    package_id: uuid.UUID
    tenant_id: uuid.UUID
    storage_path: str
    md5_hash: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        orm_mode = True

class PackageResponse(PackageInDBBase):
    """Schema for package response"""
    pass

class PackageWithPermissions(PackageResponse):
    """Schema for package with permissions"""
    permissions: Dict[str, bool] = {}

class PackageUpload(BaseModel):
    """Schema for package upload"""
    name: str
    description: Optional[str] = None
    version: str
    entry_point: str
    overwrite: Optional[bool] = False

class PackageDeployment(BaseModel):
    """Schema for package deployment"""
    package_id: uuid.UUID
    environment: str
    agents: Optional[List[uuid.UUID]] = None
    deploy_all: Optional[bool] = False
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment"""
        valid_environments = ["development", "testing", "production"]
        if v not in valid_environments:
            raise ValueError(f"Invalid environment. Must be one of: {', '.join(valid_environments)}")
        return v

class PackageExecutionRequest(BaseModel):
    """Schema for package execution request"""
    package_id: uuid.UUID
    parameters: Optional[Dict[str, Any]] = None
    agent_id: Optional[uuid.UUID] = None
    priority: Optional[int] = 1
    timeout_seconds: Optional[int] = 3600
    
class PackageVersionResponse(BaseModel):
    """Schema for package version response"""
    package_id: uuid.UUID
    name: str
    version: str
    created_at: datetime
    status: str
    created_by: Optional[uuid.UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        orm_mode = True

class PackageDeployRequest(BaseModel):
    """Schema for package deployment request"""
    target_environment: str = Field(..., description="Target environment for deployment")
    agent_ids: Optional[List[uuid.UUID]] = Field(None, description="Specific agents to deploy to")
    deploy_to_all_agents: bool = Field(False, description="Whether to deploy to all available agents")
    settings: Optional[Dict[str, Any]] = Field(None, description="Deployment-specific settings")
    
    @validator("target_environment")
    def validate_environment(cls, v):
        """Validate environment name"""
        valid_environments = ["development", "testing", "production"]
        if v not in valid_environments:
            raise ValueError(f"Invalid environment. Must be one of: {', '.join(valid_environments)}")
        return v