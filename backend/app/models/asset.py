"""
Asset model for secure credential and configuration storage.

This module defines the Asset, AssetType, and AssetFolder models for managing
secure storage of credentials and configurations.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..db.session import Base

class AssetType(Base):
    """
    Asset type model.
    
    Defines the types of assets that can be stored in the system,
    such as credentials, configurations, tokens, etc.
    """
    
    __tablename__ = "asset_types"
    
    # Primary key
    asset_type_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Asset type information
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    assets = relationship("Asset", back_populates="asset_type")
    
    def __repr__(self):
        """String representation of the asset type"""
        return f"<AssetType {self.name} ({self.asset_type_id})>"

class AssetFolder(Base):
    """
    Asset folder model.
    
    Organizes assets in a hierarchical folder structure for easier management.
    """
    
    __tablename__ = "asset_folders"
    
    # Primary key
    folder_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="asset_folders")
    
    # Folder information
    name = Column(String(255), nullable=False)
    
    # Parent folder (for hierarchical structure)
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("asset_folders.folder_id"), nullable=True)
    parent_folder = relationship("AssetFolder", remote_side=[folder_id], backref="subfolders")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    creator = relationship("User", foreign_keys=[created_by])
    
    # Assets in this folder
    assets = relationship("Asset", back_populates="folder")
    
    # Unique constraint for tenant + name + parent_folder
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "parent_folder_id", name="uq_folder_tenant_name_parent"),
    )
    
    def __repr__(self):
        """String representation of the asset folder"""
        return f"<AssetFolder {self.name} ({self.folder_id})>"

class Asset(Base):
    """
    Asset model for secure credential and configuration storage.
    
    Assets store sensitive information like credentials, tokens, and configurations
    used by automation jobs.
    """
    
    __tablename__ = "assets"
    
    # Primary key
    asset_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="assets")
    
    # Asset type foreign key
    asset_type_id = Column(UUID(as_uuid=True), ForeignKey("asset_types.asset_type_id"), nullable=False)
    asset_type = relationship("AssetType", back_populates="assets")
    
    # Folder foreign key
    folder_id = Column(UUID(as_uuid=True), ForeignKey("asset_folders.folder_id"), nullable=True)
    folder = relationship("AssetFolder", back_populates="assets")
    
    # Asset information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Asset value (can be encrypted)
    is_encrypted = Column(Boolean, nullable=False, default=True)
    value = Column(Text, nullable=True)
    
    # Versioning
    version = Column(Integer, nullable=False, default=1)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    permissions = relationship("AssetPermission", back_populates="asset", cascade="all, delete-orphan")
    
    # Unique constraint for tenant + name
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_asset_tenant_name"),
    )
    
    def __repr__(self):
        """String representation of the asset"""
        return f"<Asset {self.name} ({self.asset_id})>"

class AssetPermission(Base):
    """
    Asset permission model.
    
    Controls which roles have access to which assets and what operations
    they can perform on them.
    """
    
    __tablename__ = "asset_permissions"
    
    # Composite primary key
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets.asset_id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"), primary_key=True)
    
    # Permissions
    can_view = Column(Boolean, nullable=False, default=False)
    can_edit = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    asset = relationship("Asset", back_populates="permissions")
    role = relationship("Role")
    
    def __repr__(self):
        """String representation of the asset permission"""
        return f"<AssetPermission {self.asset_id} - {self.role_id}>"