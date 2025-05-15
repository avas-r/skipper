"""
Permissions module for role-based access control.

This module provides permission checking and role-based access control
for API endpoints and resources.
"""

from functools import wraps
from typing import List, Callable, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.user import User
from .jwt import get_current_active_user


class PermissionChecker:
    """Permission checker for role-based access control"""
    
    def __init__(self, required_permissions: List[str]):
        """
        Initialize the permission checker.
        
        Args:
            required_permissions: List of required permission names
        """
        self.required_permissions = required_permissions
    
    def __call__(
        self, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
    ) -> bool:
        """
        Check if user has required permissions.
        
        Args:
            user: Current authenticated user
            db: Database session
            
        Returns:
            bool: True if user has all required permissions
            
        Raises:
            HTTPException: If user doesn't have required permissions
        """
        # Get all permissions from user roles
        user_permissions = set()
        for role in user.roles:  # user.roles gives us Role objects directly
            for permission in role.permissions:  # access permissions directly from Role
                user_permissions.add(permission.name)
        
        # Check if user has all required permissions
        missing_permissions = set(self.required_permissions) - user_permissions
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}",
            )
            
        return True


def has_permission(permission_name: str) -> Callable:
    """
    Dependency for checking a single permission.
    
    Args:
        permission_name: Name of the permission to check
        
    Returns:
        Callable: Dependency function for FastAPI
    """
    return PermissionChecker([permission_name])


def has_permissions(permission_names: List[str]) -> Callable:
    """
    Dependency for checking multiple permissions.
    
    Args:
        permission_names: List of permission names to check
        
    Returns:
        Callable: Dependency function for FastAPI
    """
    return PermissionChecker(permission_names)


def check_resource_permission(
    resource_type: str,
    action: str,
    tenant_id: Optional[str] = None,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> bool:
    """
    Check if user has permission for a specific resource action.
    
    Args:
        resource_type: Type of resource (e.g., 'job', 'asset')
        action: Action on resource (e.g., 'read', 'create')
        tenant_id: Optional tenant ID for multi-tenancy checks
        user: Current authenticated user
        db: Database session
        
    Returns:
        bool: True if user has permission
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Admin users bypass permission checks
    for role in user.roles:  # user.roles gives us Role objects directly
        if role.name in ["admin", "superuser"]:
            return True
    
    # If tenant_id provided, check tenant access
    if tenant_id and str(user.tenant_id) != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to resources from other tenants is not allowed",
        )
    
    # Check specific resource permission
    permission_name = f"{resource_type}:{action}"
    
    # Get all permissions from user roles
    for role in user.roles:  # user.roles gives us Role objects directly
        for permission in role.permissions:  # access permissions directly from Role
            if permission.name == permission_name:
                return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Missing required permission: {permission_name}",
    )


class ResourcePermission:
    """Resource permission checker for specific resource types"""
    
    def __init__(self, resource_type: str):
        """
        Initialize the resource permission checker.
        
        Args:
            resource_type: Type of resource (e.g., 'job', 'asset')
        """
        self.resource_type = resource_type
    
    def create(
        self, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
    ) -> bool:
        """
        Check create permission for the resource type.
        
        Args:
            user: Current authenticated user
            db: Database session
            
        Returns:
            bool: True if user has permission
        """
        # First check feature access for subscription-limited features
        if self.resource_type in ["analytics", "custom_branding", "schedule", "queue"]:
            if not self._check_feature_access(self.resource_type, user, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your subscription does not include access to this feature: {self.resource_type}",
                )
        
        return check_resource_permission(
            self.resource_type, "create", None, user, db
        )
    
    def read(
        self, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
    ) -> bool:
        """
        Check read permission for the resource type.
        
        Args:
            user: Current authenticated user
            db: Database session
            
        Returns:
            bool: True if user has permission
        """
        # First check feature access for subscription-limited features
        if self.resource_type in ["analytics", "custom_branding"]:
            if not self._check_feature_access(self.resource_type, user, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your subscription does not include access to this feature: {self.resource_type}",
                )
        
        return check_resource_permission(
            self.resource_type, "read", None, user, db
        )
    
    def update(
        self, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
    ) -> bool:
        """
        Check update permission for the resource type.
        
        Args:
            user: Current authenticated user
            db: Database session
            
        Returns:
            bool: True if user has permission
        """
        # First check feature access for subscription-limited features
        if self.resource_type in ["analytics", "custom_branding", "schedule", "queue"]:
            if not self._check_feature_access(self.resource_type, user, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your subscription does not include access to this feature: {self.resource_type}",
                )
        
        return check_resource_permission(
            self.resource_type, "update", None, user, db
        )
    
    def delete(
        self, user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
    ) -> bool:
        """
        Check delete permission for the resource type.
        
        Args:
            user: Current authenticated user
            db: Database session
            
        Returns:
            bool: True if user has permission
        """
        # First check feature access for subscription-limited features
        if self.resource_type in ["analytics", "custom_branding", "schedule", "queue"]:
            if not self._check_feature_access(self.resource_type, user, db):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Your subscription does not include access to this feature: {self.resource_type}",
                )
        
        return check_resource_permission(
            self.resource_type, "delete", None, user, db
        )
    
    def _check_feature_access(self, feature: str, user: User, db: Session) -> bool:
        """
        Check if user's tenant has access to a feature based on their subscription.
        
        Args:
            feature: Feature name
            user: Current user
            db: Database session
            
        Returns:
            bool: True if tenant has access to the feature
        """
        try:
            # Avoid circular import
            from ..services.subscription_service import SubscriptionService
            
            subscription_service = SubscriptionService(db)
            access = subscription_service.check_feature_access(
                tenant_id=str(user.tenant_id),
                feature=feature
            )
            
            return access.has_access
        except ImportError:
            # If service not available, default to permissive behavior
            return True


# Permission dependencies for common resources
class Permissions:
    """Permission dependencies for common resources"""
    
    # Job permissions
    job = ResourcePermission("job")
    
    # Asset permissions
    asset = ResourcePermission("asset")
    
    # Package permissions
    package = ResourcePermission("package")
    
    # Queue permissions
    queue = ResourcePermission("queue")
    
    # Schedule permissions
    schedule = ResourcePermission("schedule")
    
    # Agent permissions
    agent = ResourcePermission("agent")
    
    # User permissions
    user = ResourcePermission("user")
    
    # Role permissions
    role = ResourcePermission("role")
    
    # Tenant permissions
    tenant = ResourcePermission("tenant")
    
    # Subscription permissions
    subscription = ResourcePermission("subscription")
    
    # Notification permissions
    notification = ResourcePermission("notification")


# Define default superuser permissions
SUPERUSER_PERMISSIONS = [
    # Job permissions
    "job:create", "job:read", "job:update", "job:delete", "job:execute",
    
    # Asset permissions
    "asset:create", "asset:read", "asset:update", "asset:delete",
    
    # Package permissions
    "package:create", "package:read", "package:update", "package:delete", "package:deploy",
    
    # Queue permissions
    "queue:create", "queue:read", "queue:update", "queue:delete",
    
    # Schedule permissions
    "schedule:create", "schedule:read", "schedule:update", "schedule:delete",
    
    # Agent permissions
    "agent:create", "agent:read", "agent:update", "agent:delete",
    
    # User permissions
    "user:create", "user:read", "user:update", "user:delete",
    
    # Role permissions
    "role:create", "role:read", "role:update", "role:delete",
    
    # Tenant permissions
    "tenant:create", "tenant:read", "tenant:update", "tenant:delete",
    
    # Subscription permissions
    "subscription:create", "subscription:read", "subscription:update", "subscription:delete",
    
    # Notification permissions
    "notification:create", "notification:read", "notification:update", "notification:delete",
]

# Define default admin permissions
ADMIN_PERMISSIONS = [
    # Job permissions
    "job:create", "job:read", "job:update", "job:delete", "job:execute",
    
    # Asset permissions
    "asset:create", "asset:read", "asset:update", "asset:delete",
    
    # Package permissions
    "package:create", "package:read", "package:update", "package:delete", "package:deploy",
    
    # Queue permissions
    "queue:create", "queue:read", "queue:update", "queue:delete",
    
    # Schedule permissions
    "schedule:create", "schedule:read", "schedule:update", "schedule:delete",
    
    # Agent permissions
    "agent:read", "agent:update",
    
    # User permissions
    "user:create", "user:read", "user:update",
    
    # Role permissions
    "role:read",
    
    # Subscription permissions
    "subscription:read", "subscription:update",
    
    # Notification permissions
    "notification:create", "notification:read", "notification:update",
]

# Define default user permissions
USER_PERMISSIONS = [
    # Job permissions
    "job:create", "job:read", "job:update", "job:execute",
    
    # Asset permissions
    "asset:read",
    
    # Package permissions
    "package:read",
    
    # Queue permissions
    "queue:read",
    
    # Schedule permissions
    "schedule:read",
    
    # Subscription permissions
    "subscription:read",
    
    # Notification permissions
    "notification:read",
]

# Define default viewer permissions
VIEWER_PERMISSIONS = [
    # Job permissions
    "job:read",
    
    # Asset permissions
    "asset:read",
    
    # Package permissions
    "package:read",
    
    # Queue permissions
    "queue:read",
    
    # Schedule permissions
    "schedule:read",
]