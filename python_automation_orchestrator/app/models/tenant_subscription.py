"""
Tenant subscription model for tracking tenant subscription details.

This module defines the TenantSubscription model for managing subscription 
lifecycle and payment details of tenants in the orchestration system.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, UUID, Integer, Float, ForeignKey, Boolean, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.session import Base

class TenantSubscription(Base):
    """
    Tenant subscription model.
    
    Tracks subscription details for a tenant, including billing cycle,
    payment status, and subscription history.
    """
    
    __tablename__ = "tenant_subscriptions"
    
    # Primary key
    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id", ondelete="CASCADE"), nullable=False)
    tier_id = Column(UUID(as_uuid=True), ForeignKey("subscription_tiers.tier_id"), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="subscription")
    tier = relationship("SubscriptionTier")
    
    # Subscription details
    status = Column(String(20), nullable=False, default="active")  # active, canceled, past_due, trialing
    billing_cycle = Column(String(10), nullable=False, default="monthly")  # monthly, yearly
    
    # Dates
    start_date = Column(DateTime, nullable=False, default=func.now())
    end_date = Column(DateTime, nullable=True)  # Null for auto-renewing subscriptions
    trial_end_date = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    
    # Billing details
    next_billing_date = Column(DateTime, nullable=True)
    last_billing_date = Column(DateTime, nullable=True)
    
    # Custom overrides (allows for custom pricing/limits for specific tenants)
    price_override = Column(Float, nullable=True)
    max_agents_override = Column(Integer, nullable=True)
    max_concurrent_jobs_override = Column(Integer, nullable=True)
    
    # Feature overrides as JSON
    feature_overrides = Column(JSON, nullable=True)
    
    # Payment and external references
    payment_provider = Column(String(50), nullable=True)  # e.g., "stripe", "paypal"
    external_subscription_id = Column(String(255), nullable=True)  # ID in the payment provider's system
    external_customer_id = Column(String(255), nullable=True)  # Customer ID in payment provider
    
    # Flags
    auto_renew = Column(Boolean, nullable=False, default=True)
    is_trial = Column(Boolean, nullable=False, default=False)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        """String representation of the tenant subscription"""
        return f"<TenantSubscription {self.tenant_id} - {self.tier_id} ({self.status})>"