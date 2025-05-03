"""
Authentication and authorization module.

This module provides functions for user authentication, password hashing,
and general authentication utilities.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import bcrypt

from ..db.session import get_db
from ..models.user import User
from .jwt import get_current_active_user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if password matches hash
    """
    if not plain_password or not hashed_password:
        return False
        
    # Ensure hashed_password is bytes
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
        
    # Ensure plain_password is bytes
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
        
    return bcrypt.checkpw(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Generate a password hash.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    # Generate salt and hash
    if isinstance(password, str):
        password = password.encode('utf-8')
        
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    
    # Return hash as string
    return hashed.decode('utf-8')


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User email
        password: User password
        
    Returns:
        Optional[User]: User if authentication successful, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
        
    if not user.hashed_password:
        return None
        
    if not verify_password(password, user.hashed_password):
        return None
        
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


def get_tenant_id_from_user(user: User = Depends(get_current_active_user)) -> str:
    """
    Get the tenant ID for the current user.
    
    Args:
        user: Current authenticated user
        
    Returns:
        str: Tenant ID
    """
    return str(user.tenant_id)


def verify_permissions(required_permissions, user: User = Depends(get_current_active_user)):
    """
    Verify user has required permissions.
    
    Args:
        required_permissions: List of required permission names
        user: User to check permissions for
        
    Returns:
        bool: True if user has all required permissions
        
    Raises:
        HTTPException: If user doesn't have required permissions
    """
    # Get all permissions from user roles
    user_permissions = set()
    for user_role in user.roles:
        for role_permission in user_role.role.permissions:
            user_permissions.add(role_permission.permission.name)
    
    # Check if user has all required permissions
    missing_permissions = set(required_permissions) - user_permissions
    if missing_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permissions: {', '.join(missing_permissions)}",
        )
        
    return True


def has_permission(permission_name, user: User) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        permission_name: Name of the permission to check
        user: User to check permission for
        
    Returns:
        bool: True if user has the permission
    """
    # Get all permissions from user roles
    for user_role in user.roles:
        for role_permission in user_role.role.permissions:
            if role_permission.permission.name == permission_name:
                return True
                
    return False


def has_owner_access(obj, user: User) -> bool:
    """
    Check if user has owner access to an object.
    
    Args:
        obj: Object to check access for
        user: User to check access for
        
    Returns:
        bool: True if user has owner access
    """
    # If object has a tenant_id and it doesn't match the user's tenant_id, deny access
    if hasattr(obj, "tenant_id") and obj.tenant_id != user.tenant_id:
        return False
        
    # If object has a created_by and it matches the user's ID, grant access
    if hasattr(obj, "created_by") and obj.created_by == user.user_id:
        return True
        
    # If user has superuser role, grant access
    for user_role in user.roles:
        if user_role.role.name == "superuser":
            return True
            
    return False