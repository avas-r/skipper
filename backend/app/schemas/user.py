"""
User schemas for the orchestrator API.

This module defines Pydantic models for user-related API requests and responses.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, validator, Field

class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr
    full_name: str
    status: Optional[str] = "active"

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str
    tenant_id: uuid.UUID
    roles: List[str] = []
    
    @validator("password")
    def password_min_length(cls, v):
        """Validate password length"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
        
    @validator("tenant_id")
    def validate_tenant_id(cls, v):
        """Validate tenant ID is a UUID"""
        if v is None:
            raise ValueError("tenant_id is required")
        # If v is already a UUID, return it
        if isinstance(v, uuid.UUID):
            return v
        # If v is a string, convert it to UUID
        try:
            return uuid.UUID(str(v))
        except ValueError:
            raise ValueError("tenant_id must be a valid UUID")

class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[str]] = None
    
    @validator("password")
    def password_min_length(cls, v):
        """Validate password length"""
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

class UserInDBBase(UserBase):
    """Base schema for user in database"""
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class UserResponse(UserInDBBase):
    """Schema for user response"""
    roles: List[str] = []

class UserWithPermissions(UserResponse):
    """Schema for user with permissions"""
    permissions: List[str] = []

class RoleBase(BaseModel):
    """Base schema for role data"""
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    permissions: List[str] = []

class RoleUpdate(BaseModel):
    """Schema for updating a role"""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None

class RoleInDBBase(RoleBase):
    """Base schema for role in database"""
    role_id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class RoleResponse(RoleInDBBase):
    """Schema for role response"""
    permissions: List[str] = []

class PermissionBase(BaseModel):
    """Base schema for permission data"""
    name: str
    description: Optional[str] = None
    resource: str
    action: str

class PermissionCreate(PermissionBase):
    """Schema for creating a new permission"""
    pass

class PermissionResponse(PermissionBase):
    """Schema for permission response"""
    permission_id: uuid.UUID
    created_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True