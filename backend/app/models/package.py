"""
Package model for automation package management.

This module defines the Package and PackagePermission models for managing
automation packages that contain the actual automation logic.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..db.session import Base

class Package(Base):
    """
    Package model for automation package management.
    
    Packages contain the actual automation code and scripts that are executed by agents.
    """
    
    __tablename__ = "packages"
    
    # Primary key
    package_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="packages")
    
    # Package information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    
    # Package content
    main_file_path = Column(String(255), nullable=False)
    storage_path = Column(String(255), nullable=False)
    entry_point = Column(String(255), nullable=False)
    md5_hash = Column(String(32), nullable=True)
    
    # Package metadata
    dependencies = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="development")
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    permissions = relationship("PackagePermission", back_populates="package", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="package")
    
    # Unique constraint for tenant + name + version
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", "version", name="uq_package_tenant_name_version"),
    )
    
    def __repr__(self):
        """String representation of the package"""
        return f"<Package {self.name} v{self.version} ({self.package_id})>"

class PackagePermission(Base):
    """
    Package permission model.
    
    Controls which roles have access to which packages and what operations
    they can perform on them.
    """
    
    __tablename__ = "package_permissions"
    
    # Composite primary key
    package_id = Column(UUID(as_uuid=True), ForeignKey("packages.package_id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"), primary_key=True)
    
    # Permissions
    can_view = Column(Boolean, nullable=False, default=False)
    can_execute = Column(Boolean, nullable=False, default=False)
    can_edit = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    package = relationship("Package", back_populates="permissions")
    role = relationship("Role")
    
    def __repr__(self):
        """String representation of the package permission"""
        return f"<PackagePermission {self.package_id} - {self.role_id}>"