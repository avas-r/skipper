"""
User service for managing user operations.

This module provides services for managing users, including CRUD operations
and user-role relationships.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models import User, Role, Tenant, UserRole, Permission, RolePermission
from ..schemas.user import UserCreate, UserUpdate
from ..auth.auth import get_password_hash, verify_password

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users"""
    
    def __init__(self, db: Session):
        """
        Initialize the user service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def create_user(self, user_in: UserCreate, tenant_id: str, created_by: Optional[str] = None) -> User:
        """
        Create a new user.
        
        Args:
            user_in: User creation data
            tenant_id: Tenant ID
            created_by: Optional creator user ID
            
        Returns:
            User: Created user
        """
        # Hash the password
        hashed_password = get_password_hash(user_in.password)
        
        # Create user
        db_user = User(
            user_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            status=user_in.status if user_in.status else "active",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        # Add user to roles
        if user_in.roles:
            for role_name in user_in.roles:
                # Find role by name
                role = self.db.query(Role).filter(
                    Role.name == role_name,
                    Role.tenant_id == uuid.UUID(tenant_id)
                ).first()
                
                if role:
                    # Add user to role
                    user_role = UserRole(
                        user_id=db_user.user_id,
                        role_id=role.role_id,
                        created_at=datetime.utcnow()
                    )
                    self.db.add(user_role)
            
            self.db.commit()
            self.db.refresh(db_user)
        
        # Create audit log
        if created_by:
            from ..models import AuditLog
            audit_log = AuditLog(
                log_id=uuid.uuid4(),
                tenant_id=uuid.UUID(tenant_id),
                user_id=uuid.UUID(created_by),
                action="create_user",
                entity_type="user",
                entity_id=db_user.user_id,
                created_at=datetime.utcnow(),
                details={
                    "email": db_user.email,
                    "full_name": db_user.full_name,
                    "status": db_user.status
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return db_user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[User]: User or None if not found
        """
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: User email
            
        Returns:
            Optional[User]: User or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def list_users(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        List users with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of users
        """
        query = self.db.query(User).filter(User.tenant_id == tenant_id)
        
        # Apply status filter
        if status:
            query = query.filter(User.status == status)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        query = query.order_by(User.email).offset(skip).limit(limit)
        
        return query.all()
    
    def update_user(self, user_id: str, user_in: UserUpdate) -> Optional[User]:
        """
        Update a user.
        
        Args:
            user_id: User ID
            user_in: User update data
            
        Returns:
            Optional[User]: Updated user or None if not found
        """
        # Get user
        user = self.db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return None
        
        # Update fields
        update_data = user_in.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            update_data["hashed_password"] = hashed_password
            del update_data["password"]
        
        # Update roles if provided
        if "roles" in update_data:
            # Get current roles
            current_roles = set(
                role_id for role_id, in self.db.query(UserRole.role_id).filter(
                    UserRole.user_id == user_id
                )
            )
            
            # Get new roles
            new_roles = set()
            for role_name in update_data["roles"]:
                role = self.db.query(Role).filter(
                    Role.name == role_name,
                    Role.tenant_id == user.tenant_id
                ).first()
                
                if role:
                    new_roles.add(role.role_id)
            
            # Remove roles
            roles_to_remove = current_roles - new_roles
            if roles_to_remove:
                self.db.query(UserRole).filter(
                    UserRole.user_id == user_id,
                    UserRole.role_id.in_(roles_to_remove)
                ).delete(synchronize_session=False)
                
            # Add roles
            roles_to_add = new_roles - current_roles
            for role_id in roles_to_add:
                user_role = UserRole(
                    user_id=uuid.UUID(user_id),
                    role_id=role_id,
                    created_at=datetime.utcnow()
                )
                self.db.add(user_role)
                
            # Remove roles from update data
            del update_data["roles"]
        
        # Update user attributes
        for key, value in update_data.items():
            setattr(user, key, value)
            
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get user
        user = self.db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return False
        
        # Remove user from roles
        self.db.query(UserRole).filter(UserRole.user_id == user_id).delete()
        
        # Delete user
        self.db.delete(user)
        self.db.commit()
        
        return True
    
    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            bool: True if assignment successful
        """
        # Check if already assigned
        existing = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).first()
        
        if existing:
            return True
        
        # Assign role
        user_role = UserRole(
            user_id=uuid.UUID(user_id),
            role_id=uuid.UUID(role_id),
            created_at=datetime.utcnow()
        )
        
        self.db.add(user_role)
        self.db.commit()
        
        return True
    
    def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        Remove a role from a user.
        
        Args:
            user_id: User ID
            role_id: Role ID
            
        Returns:
            bool: True if removal successful
        """
        # Remove role
        result = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id
        ).delete()
        
        self.db.commit()
        
        return result > 0
    
    def get_user_with_permissions(self, user_id: str) -> Dict[str, Any]:
        """
        Get user with permissions.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: User with permissions
        """
        # Get user
        user = self.db.query(User).filter(User.user_id == user_id).first()
        
        if not user:
            return None
        
        # Get roles
        roles = []
        for user_role in self.db.query(UserRole).join(Role).filter(UserRole.user_id == user_id).all():
            roles.append(user_role.role.name)
        
        # Get permissions
        permissions = []
        permission_query = (
            self.db.query(Permission.name)
            .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .filter(UserRole.user_id == user_id)
            .distinct()
        )
        
        for permission_name, in permission_query:
            permissions.append(permission_name)
        
        # Create response
        result = {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": user.tenant_id,
            "status": user.status,
            "roles": roles,
            "permissions": permissions,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        
        return result