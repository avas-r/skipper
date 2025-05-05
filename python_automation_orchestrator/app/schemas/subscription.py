"""
Subscription schemas for the orchestrator API.

This module defines Pydantic models for subscription-related API requests and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

# Subscription Tier Schemas

class SubscriptionTierBase(BaseModel):
    """Base schema for subscription tier data"""
    name: str
    display_name: str
    description: Optional[str] = None
    price_monthly: float
    price_yearly: float
    is_public: bool = True
    
    # Resource limits
    max_agents: int
    max_concurrent_jobs: int
    max_schedules: int
    max_queues: int
    storage_gb: int
    max_api_calls_daily: int
    
    # Feature flags
    enable_api_access: bool = True
    enable_schedules: bool = True
    enable_queues: bool = True
    enable_analytics: bool = False
    enable_custom_branding: bool = False
    enable_sla_support: bool = False
    enable_audit_logs: bool = False
    
    features: Optional[Dict[str, Any]] = None

class SubscriptionTierCreate(SubscriptionTierBase):
    """Schema for creating a new subscription tier"""
    pass

class SubscriptionTierUpdate(BaseModel):
    """Schema for updating a subscription tier"""
    display_name: Optional[str] = None
    description: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    is_public: Optional[bool] = None
    
    # Resource limits
    max_agents: Optional[int] = None
    max_concurrent_jobs: Optional[int] = None
    max_schedules: Optional[int] = None
    max_queues: Optional[int] = None
    storage_gb: Optional[int] = None
    max_api_calls_daily: Optional[int] = None
    
    # Feature flags
    enable_api_access: Optional[bool] = None
    enable_schedules: Optional[bool] = None
    enable_queues: Optional[bool] = None
    enable_analytics: Optional[bool] = None
    enable_custom_branding: Optional[bool] = None
    enable_sla_support: Optional[bool] = None
    enable_audit_logs: Optional[bool] = None
    
    features: Optional[Dict[str, Any]] = None

class SubscriptionTierInDB(SubscriptionTierBase):
    """Base schema for subscription tier in database"""
    tier_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class SubscriptionTierResponse(SubscriptionTierInDB):
    """Schema for subscription tier response"""
    pass

# Tenant Subscription Schemas

class TenantSubscriptionBase(BaseModel):
    """Base schema for tenant subscription data"""
    tenant_id: UUID
    tier_id: UUID
    billing_cycle: str = "monthly"
    status: str = "active"
    auto_renew: bool = True
    is_trial: bool = False
    trial_end_date: Optional[datetime] = None
    
    # Custom overrides
    price_override: Optional[float] = None
    max_agents_override: Optional[int] = None
    max_concurrent_jobs_override: Optional[int] = None
    feature_overrides: Optional[Dict[str, Any]] = None
    
    # Payment info
    payment_provider: Optional[str] = None
    external_subscription_id: Optional[str] = None
    external_customer_id: Optional[str] = None
    
    @validator("billing_cycle")
    def validate_billing_cycle(cls, v):
        """Validate billing cycle"""
        valid_cycles = ["monthly", "yearly"]
        if v not in valid_cycles:
            raise ValueError(f"Invalid billing cycle. Must be one of: {', '.join(valid_cycles)}")
        return v
    
    @validator("status")
    def validate_status(cls, v):
        """Validate subscription status"""
        valid_statuses = ["active", "canceled", "past_due", "trialing"]
        if v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class TenantSubscriptionCreate(TenantSubscriptionBase):
    """Schema for creating a new tenant subscription"""
    pass

class TenantSubscriptionUpdate(BaseModel):
    """Schema for updating a tenant subscription"""
    tier_id: Optional[UUID] = None
    billing_cycle: Optional[str] = None
    status: Optional[str] = None
    auto_renew: Optional[bool] = None
    is_trial: Optional[bool] = None
    trial_end_date: Optional[datetime] = None
    
    # Custom overrides
    price_override: Optional[float] = None
    max_agents_override: Optional[int] = None
    max_concurrent_jobs_override: Optional[int] = None
    feature_overrides: Optional[Dict[str, Any]] = None
    
    # Payment info
    payment_provider: Optional[str] = None
    external_subscription_id: Optional[str] = None
    external_customer_id: Optional[str] = None
    
    @validator("billing_cycle")
    def validate_billing_cycle(cls, v):
        """Validate billing cycle"""
        if v is not None:
            valid_cycles = ["monthly", "yearly"]
            if v not in valid_cycles:
                raise ValueError(f"Invalid billing cycle. Must be one of: {', '.join(valid_cycles)}")
        return v
    
    @validator("status")
    def validate_status(cls, v):
        """Validate subscription status"""
        if v is not None:
            valid_statuses = ["active", "canceled", "past_due", "trialing"]
            if v not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class TenantSubscriptionInDB(TenantSubscriptionBase):
    """Base schema for tenant subscription in database"""
    subscription_id: UUID
    start_date: datetime
    end_date: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    last_billing_date: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class TenantSubscriptionResponse(TenantSubscriptionInDB):
    """Schema for tenant subscription response"""
    tier: Optional[SubscriptionTierResponse] = None

# Registration schema
class OrganizationRegistration(BaseModel):
    """Schema for registering a new organization"""
    organization_name: str
    full_name: str
    email: str
    password: str
    subscription_tier: str = "free"  # free, standard, professional, enterprise
    
    @validator("subscription_tier")
    def validate_tier(cls, v):
        """Validate subscription tier"""
        valid_tiers = ["free", "standard", "professional", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f"Invalid subscription tier. Must be one of: {', '.join(valid_tiers)}")
        return v

# Subscription summary for tenant details
class SubscriptionSummary(BaseModel):
    """Summary of subscription information for tenant details"""
    tier_name: str
    tier_display_name: str
    status: str
    billing_cycle: str
    price: float
    next_billing_date: Optional[datetime] = None
    max_agents: int
    max_concurrent_jobs: int
    max_schedules: int
    max_queues: int
    features: Dict[str, bool]
    is_trial: bool = False
    trial_end_date: Optional[datetime] = None
    
# Feature access
class FeatureAccess(BaseModel):
    """Schema for checking feature access"""
    feature: str
    has_access: bool
    reason: Optional[str] = None
    upgrade_to: Optional[List[str]] = None