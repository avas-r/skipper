"""
User management endpoints for the orchestrator API.

This module provides endpoints for managing users, including CRUD operations
and role management.
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user, get_current_active_superuser
from ....auth.auth import get_password_hash, verify_permissions
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Role, Tenant, UserRole
from ....schemas.user import (
    UserCreate, 
    UserUpdate, 
    UserResponse, 
    UserWithPermissions,
    RoleCreate,
    RoleUpdate,
    RoleResponse
)
from ....services.user_service import UserService
from ....services.role_service import RoleService
from ....services.tenant_service import TenantService
from ..dependencies import get_multi_tenant_filter

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_user_read = PermissionChecker(["user:read"])
require_user_create = PermissionChecker(["user:create"])
require_user_update = PermissionChecker(["user:update"])
require_user_delete = PermissionChecker(["user:delete"])
require_role_read = PermissionChecker(["role:read"])
require_role_create = PermissionChecker(["role:create"])
require_role_update = PermissionChecker(["role:update"])
require_role_delete = PermissionChecker(["role:delete"])

@router.get("/", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_read),
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all users with optional filtering.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        skip: Number of users to skip
        limit: Maximum number of users to return
        tenant_id: Optional tenant filter
        status: Optional status filter
        search: Optional search term
        
    Returns:
        List[UserResponse]: List of users
    """
    # Create user service
    user_service = UserService(db)
    
    # Determine tenant filter
    if tenant_id:
        # Check if user has access to tenant
        if str(current_user.tenant_id) != tenant_id:
            # Allow superusers to access any tenant
            has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
            if not has_superuser_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to users from other tenants is not allowed"
                )
    else:
        # Default to user's tenant
        tenant_id = str(current_user.tenant_id)
        
    # List users
    users = user_service.list_users(
        tenant_id=tenant_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return users

@router.post("/", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_create)
) -> Any:
    """
    Create a new user.
    
    Args:
        user_in: User creation data
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        UserResponse: Created user
    """
    # Create user service
    user_service = UserService(db)
    
    # Determine tenant ID
    tenant_id = user_in.tenant_id if user_in.tenant_id else current_user.tenant_id
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(tenant_id):
        # Allow superusers to create users in any tenant
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create users in other tenants"
            )
    
    # Check if email already exists
    existing_user = user_service.get_user_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email {user_in.email} already exists"
        )
    
    # Create user
    user = user_service.create_user(
        user_in=user_in,
        tenant_id=str(tenant_id),
        created_by=str(current_user.user_id)
    )
    
    return user

@router.get("/me", response_model=UserWithPermissions)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user with permissions.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        UserWithPermissions: Current user with permissions
    """
    # Create user service
    user_service = UserService(db)
    
    # Get user with permissions
    user = user_service.get_user_with_permissions(str(current_user.user_id))
    
    return user

@router.put("/me", response_model=UserResponse)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Update current user.
    
    Args:
        user_in: User update data
        db: Database session
        current_user: Current user
        
    Returns:
        UserResponse: Updated user
    """
    # Create user service
    user_service = UserService(db)
    
    # Update user
    user = user_service.update_user(
        user_id=str(current_user.user_id),
        user_in=user_in
    )
    
    return user

@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_read)
) -> Any:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        UserResponse: User
    """
    # Create user service
    user_service = UserService(db)
    
    # Get user
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(user.tenant_id):
        # Allow superusers to access any user
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to users from other tenants is not allowed"
            )
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_update)
) -> Any:
    """
    Update a user.
    
    Args:
        user_id: User ID
        user_in: User update data
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        UserResponse: Updated user
    """
    # Create user service
    user_service = UserService(db)
    
    # Get user
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(user.tenant_id):
        # Allow superusers to update any user
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update users from other tenants"
            )
    
    # Prevent changing email to an existing one
    if user_in.email and user_in.email != user.email:
        existing_user = user_service.get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email {user_in.email} already exists"
            )
    
    # Update user
    updated_user = user_service.update_user(
        user_id=user_id,
        user_in=user_in
    )
    
    return updated_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_delete)
) -> None:
    """
    Delete a user.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current user
        _: Permission check
    """
    # Create user service
    user_service = UserService(db)
    
    # Get user
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(user.tenant_id):
        # Allow superusers to delete any user
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete users from other tenants"
            )
    
    # Prevent deleting self
    if str(user.user_id) == str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete self"
        )
    
    # Delete user
    user_service.delete_user(user_id)

@router.get("/{user_id}/roles", response_model=List[RoleResponse])
def get_user_roles(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_read)
) -> Any:
    """
    Get roles assigned to a user.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        List[RoleResponse]: List of roles
    """
    # Create user service and role service
    user_service = UserService(db)
    role_service = RoleService(db)
    
    # Get user
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(user.tenant_id):
        # Allow superusers to access any user
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to users from other tenants is not allowed"
            )
    
    # Get user roles
    roles = role_service.get_user_roles(user_id)
    
    return roles

@router.post("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_role_to_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_update)
) -> None:
    """
    Assign a role to a user.
    
    Args:
        user_id: User ID
        role_id: Role ID
        db: Database session
        current_user: Current user
        _: Permission check
    """
    # Create user service and role service
    user_service = UserService(db)
    role_service = RoleService(db)
    
    # Get user
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(user.tenant_id):
        # Allow superusers to update any user
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update users from other tenants"
            )
    
    # Get role
    role = role_service.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if role belongs to same tenant
    if str(role.tenant_id) != str(user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign role from different tenant"
        )
    
    # Assign role to user
    user_service.assign_role_to_user(user_id, role_id)

@router.delete("/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_role_from_user(
    user_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_user_update)
) -> None:
    """
    Remove a role from a user.
    
    Args:
        user_id: User ID
        role_id: Role ID
        db: Database session
        current_user: Current user
        _: Permission check
    """
    # Create user service
    user_service = UserService(db)
    
    # Get user
    user = user_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(user.tenant_id):
        # Allow superusers to update any user
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update users from other tenants"
            )
    
    # Remove role from user
    user_service.remove_role_from_user(user_id, role_id)

@router.get("/roles/", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_role_read),
    skip: int = 0,
    limit: int = 100,
    tenant_id: Optional[str] = None
) -> Any:
    """
    List all roles with optional filtering.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        skip: Number of roles to skip
        limit: Maximum number of roles to return
        tenant_id: Optional tenant filter
        
    Returns:
        List[RoleResponse]: List of roles
    """
    # Create role service
    role_service = RoleService(db)
    
    # Determine tenant filter
    if tenant_id:
        # Check if user has access to tenant
        if str(current_user.tenant_id) != tenant_id:
            # Allow superusers to access any tenant
            has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
            if not has_superuser_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to roles from other tenants is not allowed"
                )
    else:
        # Default to user's tenant
        tenant_id = str(current_user.tenant_id)
        
    # List roles
    roles = role_service.list_roles(
        tenant_id=tenant_id,
        skip=skip,
        limit=limit
    )
    
    return roles

@router.post("/roles/", response_model=RoleResponse)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_role_create)
) -> Any:
    """
    Create a new role.
    
    Args:
        role_in: Role creation data
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        RoleResponse: Created role
    """
    # Create role service
    role_service = RoleService(db)
    
    # Check if role already exists
    existing_role = role_service.get_role_by_name(
        name=role_in.name, 
        tenant_id=str(current_user.tenant_id)
    )
    
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name {role_in.name} already exists"
        )
    
    # Create role
    role = role_service.create_role(
        role_in=role_in,
        tenant_id=str(current_user.tenant_id),
        created_by=str(current_user.user_id)
    )
    
    return role

@router.get("/roles/{role_id}", response_model=RoleResponse)
def read_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_role_read)
) -> Any:
    """
    Get role by ID.
    
    Args:
        role_id: Role ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        RoleResponse: Role
    """
    # Create role service
    role_service = RoleService(db)
    
    # Get role
    role = role_service.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(role.tenant_id):
        # Allow superusers to access any role
        has_superuser_role = any(user_role.name == "superuser" for user_role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to roles from other tenants is not allowed"
            )
    
    return role

@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: str,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_role_update)
) -> Any:
    """
    Update a role.
    
    Args:
        role_id: Role ID
        role_in: Role update data
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        RoleResponse: Updated role
    """
    # Create role service
    role_service = RoleService(db)
    
    # Get role
    role = role_service.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(role.tenant_id):
        # Allow superusers to update any role
        has_superuser_role = any(user_role.name == "superuser" for user_role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update roles from other tenants"
            )
    
    # Prevent changing name to an existing one
    if role_in.name and role_in.name != role.name:
        existing_role = role_service.get_role_by_name(
            name=role_in.name, 
            tenant_id=str(role.tenant_id)
        )
        
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name {role_in.name} already exists"
            )
    
    # Update role
    updated_role = role_service.update_role(
        role_id=role_id,
        role_in=role_in
    )
    
    return updated_role

@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_role_delete)
) -> None:
    """
    Delete a role.
    
    Args:
        role_id: Role ID
        db: Database session
        current_user: Current user
        _: Permission check
    """
    # Create role service
    role_service = RoleService(db)
    
    # Get role
    role = role_service.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(role.tenant_id):
        # Allow superusers to delete any role
        has_superuser_role = any(user_role.name == "superuser" for user_role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete roles from other tenants"
            )
    
    # Check if role is in use
    if role_service.is_role_in_use(role_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete role that is assigned to users"
        )
    
    # Delete role
    role_service.delete_role(role_id)

@router.get("/roles/{role_id}/users", response_model=List[UserResponse])
def get_role_users(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_role_read)
) -> Any:
    """
    Get users assigned to a role.
    
    Args:
        role_id: Role ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        List[UserResponse]: List of users
    """
    # Create role service
    role_service = RoleService(db)
    
    # Get role
    role = role_service.get_role(role_id)
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if user has access to tenant
    if str(current_user.tenant_id) != str(role.tenant_id):
        # Allow superusers to access any role
        has_superuser_role = any(user_role.name == "superuser" for user_role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to roles from other tenants is not allowed"
            )
    
    # Get role users
    users = role_service.get_role_users(role_id)
    
    return users