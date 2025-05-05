"""
Subscription tier model for multi-tenancy pricing tiers.

This module defines the SubscriptionTier model for managing subscription 
levels and feature access in the orchestration system.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, UUID, Integer, Float, JSON, Boolean
from sqlalchemy.sql import func
from ..db.session import Base

class SubscriptionTier(Base):
    """
    Subscription tier model.
    
    Defines the available subscription tiers, their pricing, and resource limits.
    """
    
    __tablename__ = "subscription_tiers"
    
    # Primary key
    tier_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tier information
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    
    # Pricing
    price_monthly = Column(Float, nullable=False, default=0.0)  # $0 for free tier
    price_yearly = Column(Float, nullable=False, default=0.0)
    is_public = Column(Boolean, nullable=False, default=True)   # False for custom enterprise tiers
    
    # Resource limits
    max_agents = Column(Integer, nullable=False)
    max_concurrent_jobs = Column(Integer, nullable=False)
    max_schedules = Column(Integer, nullable=False)
    max_queues = Column(Integer, nullable=False)
    storage_gb = Column(Integer, nullable=False, default=5)
    max_api_calls_daily = Column(Integer, nullable=False, default=1000)
    
    # Feature flags
    enable_api_access = Column(Boolean, nullable=False, default=True)
    enable_schedules = Column(Boolean, nullable=False, default=True)
    enable_queues = Column(Boolean, nullable=False, default=True)
    enable_analytics = Column(Boolean, nullable=False, default=False)
    enable_custom_branding = Column(Boolean, nullable=False, default=False)
    enable_sla_support = Column(Boolean, nullable=False, default=False)
    enable_audit_logs = Column(Boolean, nullable=False, default=False)
    
    # Extra features as JSON to allow for flexible extension
    features = Column(JSON, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        """String representation of the subscription tier"""
        return f"<SubscriptionTier {self.name} ({self.tier_id})>"