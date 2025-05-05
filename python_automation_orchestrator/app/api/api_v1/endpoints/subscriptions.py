"""
Subscription management endpoints for the orchestrator API.

This module provides endpoints for managing subscription tiers and tenant subscriptions.
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user, get_current_active_superuser
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Tenant, SubscriptionTier, TenantSubscription
from ....schemas.subscription import (
    SubscriptionTierCreate,
    SubscriptionTierUpdate,
    SubscriptionTierResponse,
    TenantSubscriptionCreate,
    TenantSubscriptionUpdate,
    TenantSubscriptionResponse,
    SubscriptionSummary,
    FeatureAccess,
    OrganizationRegistration
)
from ....services.subscription_service import SubscriptionService
from ....services.tenant_service import TenantService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_subscription_read = PermissionChecker(["subscription:read"])
require_subscription_create = PermissionChecker(["subscription:create"])
require_subscription_update = PermissionChecker(["subscription:update"])
require_subscription_delete = PermissionChecker(["subscription:delete"])

# -----------------
# Public endpoints
# -----------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_organization(
    registration: OrganizationRegistration,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new organization with a user and subscription.
    
    This is a public endpoint that doesn't require authentication.
    
    Args:
        registration: Registration data
        db: Database session
        
    Returns:
        dict: Registration result
    """
    # Create services
    subscription_service = SubscriptionService(db)
    
    # Register organization
    result = subscription_service.register_organization(
        organization_name=registration.organization_name,
        full_name=registration.full_name,
        email=registration.email,
        password=registration.password,
        subscription_tier=registration.subscription_tier
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Organization registration failed")
        )
    
    return {
        "message": "Organization registered successfully",
        "tenant_id": result["tenant_id"],
        "user_id": result["user_id"]
    }

@router.get("/tiers/public", response_model=List[SubscriptionTierResponse])
def list_public_subscription_tiers(
    db: Session = Depends(get_db)
) -> Any:
    """
    List all public subscription tiers.
    
    This is a public endpoint that doesn't require authentication.
    
    Args:
        db: Database session
        
    Returns:
        List[SubscriptionTierResponse]: List of public subscription tiers
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # List tiers
    tiers = subscription_service.list_subscription_tiers(public_only=True)
    
    return tiers

# -----------------
# Tenant subscription endpoints
# -----------------

@router.get("/current", response_model=SubscriptionSummary)
def get_current_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get the current tenant's subscription summary.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        SubscriptionSummary: Subscription summary
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Get subscription summary
    summary = subscription_service.get_subscription_summary(str(current_user.tenant_id))
    
    return summary

@router.get("/access/{feature}", response_model=FeatureAccess)
def check_feature_access(
    feature: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Check if the current tenant has access to a specific feature.
    
    Args:
        feature: Feature name
        db: Database session
        current_user: Current user
        
    Returns:
        FeatureAccess: Feature access information
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Check feature access
    access = subscription_service.check_feature_access(
        tenant_id=str(current_user.tenant_id),
        feature=feature
    )
    
    return access

@router.post("/change-tier", response_model=TenantSubscriptionResponse)
def change_subscription_tier(
    tier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_subscription_update)
) -> Any:
    """
    Change the current tenant's subscription tier.
    
    Args:
        tier_id: New tier ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        TenantSubscriptionResponse: Updated subscription
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Check if tier exists
    tier = subscription_service.get_subscription_tier(tier_id)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier with ID {tier_id} not found"
        )
    
    # Change tier
    subscription = subscription_service.change_subscription_tier(
        tenant_id=str(current_user.tenant_id),
        new_tier_id=tier_id
    )
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found for tenant"
        )
    
    return subscription

@router.post("/cancel", status_code=status.HTTP_200_OK)
def cancel_subscription(
    immediately: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_subscription_update)
) -> Any:
    """
    Cancel the current tenant's subscription.
    
    Args:
        immediately: Whether to cancel immediately or at the end of the billing period
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        dict: Cancellation result
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Get subscription
    subscription = subscription_service.get_subscription_by_tenant(str(current_user.tenant_id))
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found for tenant"
        )
    
    # Cancel subscription
    result = subscription_service.cancel_subscription(
        subscription_id=str(subscription.subscription_id),
        cancel_immediately=immediately
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel subscription"
        )
    
    return {
        "message": "Subscription canceled successfully",
        "immediately": immediately,
        "end_date": result.end_date
    }

# -----------------
# Admin endpoints for subscription tiers
# -----------------

@router.get("/tiers", response_model=List[SubscriptionTierResponse])
def list_subscription_tiers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    List all subscription tiers.
    
    Only superusers can access this endpoint.
    
    Args:
        db: Database session
        current_user: Current superuser
        
    Returns:
        List[SubscriptionTierResponse]: List of subscription tiers
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # List tiers
    tiers = subscription_service.list_subscription_tiers()
    
    return tiers

@router.post("/tiers", response_model=SubscriptionTierResponse, status_code=status.HTTP_201_CREATED)
def create_subscription_tier(
    tier_in: SubscriptionTierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Create a new subscription tier.
    
    Only superusers can access this endpoint.
    
    Args:
        tier_in: Tier creation data
        db: Database session
        current_user: Current superuser
        
    Returns:
        SubscriptionTierResponse: Created tier
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Check if tier already exists
    existing_tier = subscription_service.get_subscription_tier_by_name(tier_in.name)
    if existing_tier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subscription tier with name {tier_in.name} already exists"
        )
    
    # Create tier
    tier = subscription_service.create_subscription_tier(tier_in)
    
    return tier

@router.get("/tiers/{tier_id}", response_model=SubscriptionTierResponse)
def read_subscription_tier(
    tier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get a subscription tier by ID.
    
    Only superusers can access this endpoint.
    
    Args:
        tier_id: Tier ID
        db: Database session
        current_user: Current superuser
        
    Returns:
        SubscriptionTierResponse: Subscription tier
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Get tier
    tier = subscription_service.get_subscription_tier(tier_id)
    
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier with ID {tier_id} not found"
        )
    
    return tier

@router.put("/tiers/{tier_id}", response_model=SubscriptionTierResponse)
def update_subscription_tier(
    tier_id: str,
    tier_in: SubscriptionTierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Update a subscription tier.
    
    Only superusers can access this endpoint.
    
    Args:
        tier_id: Tier ID
        tier_in: Tier update data
        db: Database session
        current_user: Current superuser
        
    Returns:
        SubscriptionTierResponse: Updated tier
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Update tier
    tier = subscription_service.update_subscription_tier(tier_id, tier_in)
    
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier with ID {tier_id} not found"
        )
    
    return tier

@router.delete("/tiers/{tier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription_tier(
    tier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> None:
    """
    Delete a subscription tier.
    
    Only superusers can access this endpoint.
    
    Args:
        tier_id: Tier ID
        db: Database session
        current_user: Current superuser
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Check if tier exists
    tier = subscription_service.get_subscription_tier(tier_id)
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier with ID {tier_id} not found"
        )
    
    # Delete tier
    result = subscription_service.delete_subscription_tier(tier_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete tier as it is being used by one or more tenants"
        )

# -----------------
# Admin endpoints for managing tenant subscriptions
# -----------------

@router.get("/tenants/{tenant_id}", response_model=TenantSubscriptionResponse)
def read_tenant_subscription(
    tenant: Tenant = Depends(get_tenant_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Get a tenant's subscription.
    
    Only superusers can access this endpoint.
    
    Args:
        tenant: Tenant (from path dependency)
        db: Database session
        current_user: Current superuser
        
    Returns:
        TenantSubscriptionResponse: Tenant subscription
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Get subscription
    subscription = subscription_service.get_subscription_by_tenant(str(tenant.tenant_id))
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active subscription found for tenant {tenant.tenant_id}"
        )
    
    return subscription

@router.post("/tenants/{tenant_id}", response_model=TenantSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_tenant_subscription(
    tenant_id: str,
    subscription_in: TenantSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Create a new subscription for a tenant.
    
    Only superusers can access this endpoint.
    
    Args:
        tenant_id: Tenant ID
        subscription_in: Subscription creation data
        db: Database session
        current_user: Current superuser
        
    Returns:
        TenantSubscriptionResponse: Created subscription
    """
    # Create service
    subscription_service = SubscriptionService(db)
    tenant_service = TenantService(db)
    
    # Check if tenant exists
    tenant = tenant_service.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with ID {tenant_id} not found"
        )
    
    # Check if tier exists
    tier = subscription_service.get_subscription_tier(str(subscription_in.tier_id))
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier with ID {subscription_in.tier_id} not found"
        )
    
    # Check if tenant already has an active subscription
    existing_subscription = subscription_service.get_subscription_by_tenant(tenant_id)
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant already has an active subscription"
        )
    
    # Create subscription
    subscription = subscription_service.create_tenant_subscription(subscription_in)
    
    return subscription

@router.put("/tenants/{tenant_id}", response_model=TenantSubscriptionResponse)
def update_tenant_subscription(
    tenant: Tenant = Depends(get_tenant_from_path),
    subscription_in: TenantSubscriptionUpdate = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> Any:
    """
    Update a tenant's subscription.
    
    Only superusers can access this endpoint.
    
    Args:
        tenant: Tenant (from path dependency)
        subscription_in: Subscription update data
        db: Database session
        current_user: Current superuser
        
    Returns:
        TenantSubscriptionResponse: Updated subscription
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Get subscription
    subscription = subscription_service.get_subscription_by_tenant(str(tenant.tenant_id))
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active subscription found for tenant {tenant.tenant_id}"
        )
    
    # Update subscription
    updated_subscription = subscription_service.update_tenant_subscription(
        subscription_id=str(subscription.subscription_id),
        subscription_in=subscription_in
    )
    
    return updated_subscription

@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_tenant_subscription(
    tenant: Tenant = Depends(get_tenant_from_path),
    immediately: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
) -> None:
    """
    Cancel a tenant's subscription.
    
    Only superusers can access this endpoint.
    
    Args:
        tenant: Tenant (from path dependency)
        immediately: Whether to cancel immediately or at the end of the billing period
        db: Database session
        current_user: Current superuser
    """
    # Create service
    subscription_service = SubscriptionService(db)
    
    # Get subscription
    subscription = subscription_service.get_subscription_by_tenant(str(tenant.tenant_id))
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active subscription found for tenant {tenant.tenant_id}"
        )
    
    # Cancel subscription
    result = subscription_service.cancel_subscription(
        subscription_id=str(subscription.subscription_id),
        cancel_immediately=immediately
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel subscription"
        )