"""
Tenant management endpoints for the orchestrator API.

This module provides endpoints for managing tenants, including CRUD operations
and tenant resource management.
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user, get_current_active_superuser
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Tenant
from ....schemas.tenant import (
    TenantCreate, 
    TenantUpdate, 
    TenantResponse,
    TenantUsageResponse,
    TenantStats
)
from ....services.tenant_service import TenantService
from ....services.user_service import UserService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_tenant_read = PermissionChecker(["tenant:read"])
require_tenant_create = PermissionChecker(["tenant:create"])
require_tenant_update = PermissionChecker(["tenant:update"])
require_tenant_delete = PermissionChecker(["tenant:delete"])

@router.get("/", response_model=List[TenantResponse])
def list_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    subscription_tier: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all tenants with optional filtering.
    
    Only superusers can access this endpoint.
    
    Args:
        db: Database session
        current_user: Current superuser
        skip: Number of tenants to skip
        limit: Maximum number of tenants to return
        status: Optional status filter
        subscription_tier: Optional subscription tier filter
        search: Optional search term
        
    Returns:
        List[TenantResponse]: List of tenants
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # List tenants
    tenants = tenant_service.list_tenants(
        status=status,
        subscription_tier=subscription_tier,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return tenants

@router.post("/", response_model=TenantResponse)
def create_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Create a new tenant.
    
    Only superusers can access this endpoint.
    
    Args:
        tenant_in: Tenant creation data
        db: Database session
        current_user: Current superuser
        
    Returns:
        TenantResponse: Created tenant
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # Check if tenant already exists
    existing_tenant = tenant_service.get_tenant_by_name(tenant_in.name)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant with name {tenant_in.name} already exists"
        )
    
    # Create tenant
    tenant = tenant_service.create_tenant(
        tenant_in=tenant_in,
        created_by=str(current_user.user_id)
    )
    
    return tenant

@router.get("/current", response_model=TenantResponse)
def read_current_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user's tenant.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        TenantResponse: Current tenant
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # Get tenant
    tenant = tenant_service.get_tenant(str(current_user.tenant_id))
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    return tenant

@router.get("/current/usage", response_model=TenantUsageResponse)
def read_current_tenant_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_tenant_read)
) -> Any:
    """
    Get current tenant's resource usage.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        TenantUsageResponse: Tenant resource usage
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # Get tenant usage
    usage = tenant_service.get_tenant_resource_usage(str(current_user.tenant_id))
    
    return usage

@router.get("/stats", response_model=List[TenantStats])
def get_tenant_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get statistics for all tenants.
    
    Only superusers can access this endpoint.
    
    Args:
        db: Database session
        current_user: Current superuser
        
    Returns:
        List[TenantStats]: List of tenant statistics
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # List tenants
    tenants = tenant_service.list_tenants()
    
    # Build stats
    result = []
    for tenant in tenants:
        usage = tenant_service.get_tenant_resource_usage(str(tenant.tenant_id))
        
        stats = {
            "tenant_id": tenant.tenant_id,
            "name": tenant.name,
            "user_count": usage["users"]["count"],
            "agent_count": usage["agents"]["count"],
            "active_job_count": usage["jobs"]["active_count"],
            "running_job_count": usage["jobs"]["running_count"],
            "status": tenant.status,
            "subscription_tier": tenant.subscription_tier
        }
        
        result.append(stats)
    
    return result

@router.get("/{tenant_id}", response_model=TenantResponse)
def read_tenant(
    tenant: Tenant = Depends(get_tenant_from_path),
    _: bool = Depends(require_tenant_read)
) -> Any:
    """
    Get tenant by ID.
    
    Args:
        tenant: Tenant (from path dependency)
        _: Permission check
        
    Returns:
        TenantResponse: Tenant
    """
    return tenant

@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_in: TenantUpdate,
    tenant: Tenant = Depends(get_tenant_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_tenant_update)
) -> Any:
    """
    Update a tenant.
    
    Args:
        tenant_in: Tenant update data
        tenant: Tenant (from path dependency)
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        TenantResponse: Updated tenant
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # Check if name is being changed to an existing one
    if tenant_in.name and tenant_in.name != tenant.name:
        existing_tenant = tenant_service.get_tenant_by_name(tenant_in.name)
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tenant with name {tenant_in.name} already exists"
            )
    
    # Update tenant
    updated_tenant = tenant_service.update_tenant(
        tenant_id=str(tenant.tenant_id),
        tenant_in=tenant_in,
        updated_by=str(current_user.user_id)
    )
    
    return updated_tenant

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(
    tenant: Tenant = Depends(get_tenant_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    _: bool = Depends(require_tenant_delete)
) -> None:
    """
    Delete a tenant.
    
    Only superusers can delete tenants.
    
    Args:
        tenant: Tenant (from path dependency)
        db: Database session
        current_user: Current superuser
        _: Permission check
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # Check if tenant has users
    user_count = tenant_service.get_tenant_user_count(str(tenant.tenant_id))
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete tenant with users. Delete all {user_count} users first."
        )
    
    # Delete tenant
    tenant_service.delete_tenant(str(tenant.tenant_id))

@router.get("/{tenant_id}/users", response_model=List[dict])
def read_tenant_users(
    tenant: Tenant = Depends(get_tenant_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_tenant_read),
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get users for a tenant.
    
    Args:
        tenant: Tenant (from path dependency)
        db: Database session
        current_user: Current user
        _: Permission check
        skip: Number of users to skip
        limit: Maximum number of users to return
        
    Returns:
        List[dict]: List of user data
    """
    # Create tenant service and user service
    tenant_service = TenantService(db)
    user_service = UserService(db)
    
    # Get users
    users = user_service.list_users(
        tenant_id=str(tenant.tenant_id),
        skip=skip,
        limit=limit
    )
    
    # Convert to simplified response
    result = []
    for user in users:
        user_data = {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "status": user.status,
            "created_at": user.created_at,
            "last_login": user.last_login
        }
        result.append(user_data)
    
    return result

@router.get("/{tenant_id}/usage", response_model=TenantUsageResponse)
def read_tenant_usage(
    tenant: Tenant = Depends(get_tenant_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_tenant_read)
) -> Any:
    """
    Get resource usage for a tenant.
    
    Args:
        tenant: Tenant (from path dependency)
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        TenantUsageResponse: Tenant resource usage
    """
    # Create tenant service
    tenant_service = TenantService(db)
    
    # Get tenant usage
    usage = tenant_service.get_tenant_resource_usage(str(tenant.tenant_id))
    
    return usage