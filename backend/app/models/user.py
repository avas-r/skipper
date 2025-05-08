"""
User model for authentication and authorization.

This module defines the User, Role, and Permission models for
managing authentication and role-based access control.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Table, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..db.session import Base

# Association table for user-role relationship
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.role_id"), primary_key=True),
    Column("created_at", DateTime, nullable=False, default=func.now()),
)

# Association table for role-permission relationship
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.role_id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.permission_id"), primary_key=True),
    Column("created_at", DateTime, nullable=False, default=func.now()),
)

class User(Base):
    """
    User model for authentication and access control.
    
    Users are associated with a tenant and have roles that determine their permissions.
    """
    
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    
    # Primary key
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="users")
    
    # User information
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Status and audit fields
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    def __repr__(self):
        """String representation of the user"""
        return f"<User {self.email} ({self.user_id})>"

class Role(Base):
    """
    Role model for role-based access control.
    
    Roles are collections of permissions that can be assigned to users.
    """
    
    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}
    
    # Primary key
    role_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key (roles are tenant-specific)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="roles")
    
    # Role information
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    # Unique constraint for tenant + role name
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
    )
    
    def __repr__(self):
        """String representation of the role"""
        return f"<Role {self.name} ({self.role_id})>"

class Permission(Base):
    """
    Permission model for defining access rights.
    
    Permissions define what actions users can perform on resources.
    """
    
    __tablename__ = "permissions"
    
    # Primary key
    permission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Permission information
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    # Resource and action
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    # Unique constraint for resource + action
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permission_resource_action"),
    )
    
    def __repr__(self):
        """String representation of the permission"""
        return f"<Permission {self.name} ({self.permission_id})>"

# Classes for the association tables to make them accessible in queries
class UserRole(Base):
    """Association model for user-role relationship"""
    
    __tablename__ = "user_roles"
    __table_args__ = {"extend_existing": True}
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    user = relationship("User", overlaps="roles,users")
    role = relationship("Role", overlaps="roles,users")

class RolePermission(Base):
    """Association model for role-permission relationship"""
    
    __tablename__ = "role_permissions"
    __table_args__ = {"extend_existing": True}
    
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.role_id"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.permission_id"), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    # Relationships
    role = relationship("Role", overlaps="permissions,roles")
    permission = relationship("Permission", overlaps="permissions,roles")