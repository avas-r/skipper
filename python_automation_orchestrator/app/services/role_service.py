"""
Role service for managing role operations.

This module provides services for managing roles, including CRUD operations
and role-permission relationships.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import Role, Permission, RolePermission, UserRole, User
from ..schemas.user import RoleCreate, RoleUpdate

logger = logging.getLogger(__name__)

class RoleService:
    """Service for managing roles"""
    
    def __init__(self, db: Session):
        """
        Initialize the role service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def create_role(self, role_in: RoleCreate, tenant_id: str, created_by: Optional[str] = None) -> Role:
        """
        Create a new role.
        
        Args:
            role_in: Role creation data
            tenant_id: Tenant ID
            created_by: Optional creator user ID
            
        Returns:
            Role: Created role
        """
        # Create role
        db_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            name=role_in.name,
            description=role_in.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        
        # Add permissions
        if role_in.permissions:
            for permission_name in role_in.permissions:
                # Find permission by name
                permission = self.db.query(Permission).filter(
                    Permission.name == permission_name
                ).first()
                
                if permission:
                    # Add permission to role
                    role_permission = RolePermission(
                        role_id=db_role.role_id,
                        permission_id=permission.permission_id,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(role_permission)
            
            self.db.commit()
            self.db.refresh(db_role)
        
        # Create audit log
        if created_by:
            from ..models import AuditLog
            audit_log = AuditLog(
                log_id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                user_id=uuid.UUID(created_by),
                action="create_role",
                entity_type="role",
                entity_id=db_role.role_id,
                created_at=datetime.utcnow(),
                details={
                    "name": db_role.name,
                    "description": db_role.description
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return db_role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """
        Get a role by ID.
        
        Args:
            role_id: Role ID
            
        Returns:
            Optional[Role]: Role or None if not found
        """
        return self.db.query(Role).filter(Role.role_id == role_id).first()
    
    def get_role_by_name(self, name: str, tenant_id: str) -> Optional[Role]:
        """
        Get a role by name within a tenant.
        
        Args:
            name: Role name
            tenant_id: Tenant ID
            
        Returns:
            Optional[Role]: Role or None if not found
        """
        return self.db.query(Role).filter(
            Role.name == name,
            Role.tenant_id == tenant_id
        ).first()
    
    def list_roles(
        self,
        tenant_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Role]:
        """
        List roles with filtering.
        
        Args:
            tenant_id: Tenant ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Role]: List of roles
        """
        query = self.db.query(Role).filter(Role.tenant_id == tenant_id)
        
        # Apply pagination
        query = query.order_by(Role.name).offset(skip).limit(limit)
        
        return query.all()
    
    def update_role(self, role_id: str, role_in: RoleUpdate) -> Optional[Role]:
        """
        Update a role.
        
        Args:
            role_id: Role ID
            role_in: Role update data
            
        Returns:
            Optional[Role]: Updated role or None if not found
        """
        # Get role
        role = self.db.query(Role).filter(Role.role_id == role_id).first()
        
        if not role:
            return None
        
        # Update fields
        update_data = role_in.dict(exclude_unset=True)
        
        # Update permissions if provided
        if "permissions" in update_data:
            # Get current permissions
            current_permissions = set(
                permission_id for permission_id, in self.db.query(RolePermission.permission_id).filter(
                    RolePermission.role_id == role_id
                )
            )
            
            # Get new permissions
            new_permissions = set()
            for permission_name in update_data["permissions"]:
                permission = self.db.query(Permission).filter(
                    Permission.name == permission_name
                ).first()
                
                if permission:
                    new_permissions.add(permission.permission_id)
            
            # Remove permissions
            permissions_to_remove = current_permissions - new_permissions
            if permissions_to_remove:
                self.db.query(RolePermission).filter(
                    RolePermission.role_id == role_id,
                    RolePermission.permission_id.in_(permissions_to_remove)
                ).delete(synchronize_session=False)
                
            # Add permissions
            permissions_to_add = new_permissions - current_permissions
            for permission_id in permissions_to_add:
                role_permission = RolePermission(
                    role_id=uuid.UUID(role_id),
                    permission_id=permission_id,
                    created_at=datetime.utcnow()
                )
                self.db.add(role_permission)
                
            # Remove permissions from update data
            del update_data["permissions"]
        
        # Update role attributes
        for key, value in update_data.items():
            setattr(role, key, value)
            
        # Update timestamp
        role.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(role)
        
        return role
    
    def delete_role(self, role_id: str) -> bool:
        """
        Delete a role.
        
        Args:
            role_id: Role ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get role
        role = self.db.query(Role).filter(Role.role_id == role_id).first()
        
        if not role:
            return False
        
        # Remove role permissions
        self.db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
        
        # Remove role from users
        self.db.query(UserRole).filter(UserRole.role_id == role_id).delete()
        
        # Delete role
        self.db.delete(role)
        self.db.commit()
        
        return True
    
    def is_role_in_use(self, role_id: str) -> bool:
        """
        Check if a role is in use.
        
        Args:
            role_id: Role ID
            
        Returns:
            bool: True if role is in use
        """
        count = self.db.query(func.count(UserRole.user_id)).filter(
            UserRole.role_id == role_id
        ).scalar()
        
        return count > 0
    
    def get_role_permissions(self, role_id: str) -> List[str]:
        """
        Get permissions for a role.
        
        Args:
            role_id: Role ID
            
        Returns:
            List[str]: List of permission names
        """
        permissions = []
        permission_query = (
            self.db.query(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
            .filter(RolePermission.role_id == role_id)
        )
        
        for permission_name, in permission_query:
            permissions.append(permission_name)
        
        return permissions
    
    def assign_permission_to_role(self, role_id: str, permission_id: str) -> bool:
        """
        Assign a permission to a role.
        
        Args:
            role_id: Role ID
            permission_id: Permission ID
            
        Returns:
            bool: True if assignment successful
        """
        # Check if already assigned
        existing = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).first()
        
        if existing:
            return True
        
        # Assign permission
        role_permission = RolePermission(
            role_id=uuid.UUID(role_id),
            permission_id=uuid.UUID(permission_id),
            created_at=datetime.utcnow()
        )
        
        self.db.add(role_permission)
        self.db.commit()
        
        return True
    
    def remove_permission_from_role(self, role_id: str, permission_id: str) -> bool:
        """
        Remove a permission from a role.
        
        Args:
            role_id: Role ID
            permission_id: Permission ID
            
        Returns:
            bool: True if removal successful
        """
        # Remove permission
        result = self.db.query(RolePermission).filter(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id
        ).delete()
        
        self.db.commit()
        
        return result > 0
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """
        Get roles for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List[Role]: List of roles
        """
        roles = (
            self.db.query(Role)
            .join(UserRole, UserRole.role_id == Role.role_id)
            .filter(UserRole.user_id == user_id)
            .all()
        )
        
        return roles
    
    def get_role_users(self, role_id: str) -> List[User]:
        """
        Get users for a role.
        
        Args:
            role_id: Role ID
            
        Returns:
            List[User]: List of users
        """
        users = (
            self.db.query(User)
            .join(UserRole, UserRole.user_id == User.user_id)
            .filter(UserRole.role_id == role_id)
            .all()
        )
        
        return users