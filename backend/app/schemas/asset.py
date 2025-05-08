"""
Asset schemas for the orchestrator API.

This module defines Pydantic models for asset-related API requests and responses,
including credentials, configurations, and other sensitive data.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

class AssetTypeBase(BaseModel):
    """Base schema for asset type data"""
    name: str
    description: Optional[str] = None

class AssetTypeResponse(AssetTypeBase):
    """Schema for asset type response"""
    asset_type_id: UUID
    created_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class AssetFolderBase(BaseModel):
    """Base schema for asset folder data"""
    name: str
    parent_folder_id: Optional[UUID] = None

class AssetFolderCreate(AssetFolderBase):
    """Schema for creating a new asset folder"""
    pass

class AssetFolderUpdate(BaseModel):
    """Schema for updating an asset folder"""
    name: Optional[str] = None

class AssetFolderInDB(AssetFolderBase):
    """Base schema for asset folder in database"""
    folder_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class AssetFolderResponse(AssetFolderInDB):
    """Schema for asset folder response"""
    pass

class AssetBase(BaseModel):
    """Base schema for asset data"""
    name: str
    description: Optional[str] = None
    asset_type_id: UUID
    folder_id: Optional[UUID] = None
    is_encrypted: bool = True

class AssetCreate(AssetBase):
    """Schema for creating a new asset"""
    value: Optional[str] = None

    @validator("value")
    def validate_value(cls, v, values):
        """Validate that value is provided if is_encrypted is True"""
        if values.get("is_encrypted", True) and not v:
            raise ValueError("Value is required for encrypted assets")
        return v

class AssetUpdate(BaseModel):
    """Schema for updating an asset"""
    name: Optional[str] = None
    description: Optional[str] = None
    asset_type_id: Optional[UUID] = None
    folder_id: Optional[UUID] = None
    is_encrypted: Optional[bool] = None
    value: Optional[str] = None

class AssetInDB(AssetBase):
    """Base schema for asset in database"""
    asset_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    version: int = 1
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class AssetResponse(AssetInDB):
    """Schema for asset response"""
    # Remove sensitive value from response
    value: Optional[str] = None

class AssetValueResponse(BaseModel):
    """Schema for asset value response"""
    asset_id: UUID
    name: str
    description: Optional[str] = None
    asset_type_id: UUID
    is_encrypted: bool
    value: Optional[str] = None
    version: int

class AssetPermissionBase(BaseModel):
    """Base schema for asset permission data"""
    role_id: UUID
    can_view: bool = False
    can_edit: bool = False
    can_delete: bool = False

class AssetPermissionCreate(AssetPermissionBase):
    """Schema for creating a new asset permission"""
    pass

class AssetPermissionUpdate(BaseModel):
    """Schema for updating an asset permission"""
    can_view: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_delete: Optional[bool] = None

class AssetPermissionInDB(AssetPermissionBase):
    """Base schema for asset permission in database"""
    asset_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class AssetPermissionResponse(AssetPermissionInDB):
    """Schema for asset permission response"""
    role_name: str

class AssetTreeItem(BaseModel):
    """Schema for asset tree item (for hierarchical views)"""
    id: str
    name: str
    type: str  # "folder" or "asset"
    parent_id: Optional[str] = None
    asset_type_id: Optional[UUID] = None
    is_encrypted: Optional[bool] = None
    children: Optional[List["AssetTreeItem"]] = None

# Update forward reference for nested models
AssetTreeItem.update_forward_refs()

class AssetAuditLogEntry(BaseModel):
    """Schema for asset audit log entry"""
    timestamp: datetime
    user_id: UUID
    user_email: str
    action: str
    details: Dict[str, Any]

class AssetHistoryEntry(BaseModel):
    """Schema for asset history entry"""
    version: int
    updated_at: datetime
    updated_by: Optional[UUID] = None
    updated_by_email: Optional[str] = None
    changes: Dict[str, Any]