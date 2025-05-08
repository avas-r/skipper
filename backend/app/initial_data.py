"""
Initial data setup for the application.

This script creates default subscription tiers.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .db.session import SessionLocal
from .models import SubscriptionTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_subscription_tiers(db: Session) -> None:
    """
    Create default subscription tiers.
    """
    # Check if tiers already exist
    if db.query(SubscriptionTier).count() > 0:
        logger.info("Subscription tiers already exist. Skipping creation.")
        return
    
    # Create free tier
    free_tier = SubscriptionTier(
        name="free",
        display_name="Free",
        description="Limited resources for evaluation purposes",
        price_monthly=0.0,
        price_yearly=0.0,
        is_public=True,
        max_agents=2,
        max_concurrent_jobs=5,
        max_schedules=2,
        max_queues=2,
        storage_gb=5,
        max_api_calls_daily=1000,
        enable_api_access=True,
        enable_schedules=True,
        enable_queues=True,
        enable_analytics=False,
        enable_custom_branding=False,
        enable_sla_support=False,
        enable_audit_logs=False,
        features={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(free_tier)
    
    # Create standard tier
    standard_tier = SubscriptionTier(
        name="standard",
        display_name="Standard",
        description="For small businesses with moderate resource needs",
        price_monthly=49.99,
        price_yearly=499.90,  # 2 months free
        is_public=True,
        max_agents=10,
        max_concurrent_jobs=25,
        max_schedules=10,
        max_queues=5,
        storage_gb=20,
        max_api_calls_daily=5000,
        enable_api_access=True,
        enable_schedules=True,
        enable_queues=True,
        enable_analytics=True,
        enable_custom_branding=False,
        enable_sla_support=False,
        enable_audit_logs=False,
        features={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(standard_tier)
    
    # Create professional tier
    professional_tier = SubscriptionTier(
        name="professional",
        display_name="Professional",
        description="For medium-sized companies with advanced automation needs",
        price_monthly=199.99,
        price_yearly=1999.90,  # 2 months free
        is_public=True,
        max_agents=50,
        max_concurrent_jobs=100,
        max_schedules=50,
        max_queues=20,
        storage_gb=100,
        max_api_calls_daily=20000,
        enable_api_access=True,
        enable_schedules=True,
        enable_queues=True,
        enable_analytics=True,
        enable_custom_branding=True,
        enable_sla_support=False,
        enable_audit_logs=True,
        features={
            "priority_support": True,
            "custom_notifications": True
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(professional_tier)
    
    # Create enterprise tier
    enterprise_tier = SubscriptionTier(
        name="enterprise",
        display_name="Enterprise",
        description="For large organizations with high-volume automation requirements",
        price_monthly=999.99,
        price_yearly=9999.90,  # 2 months free
        is_public=True,
        max_agents=250,
        max_concurrent_jobs=500,
        max_schedules=100,
        max_queues=50,
        storage_gb=500,
        max_api_calls_daily=100000,
        enable_api_access=True,
        enable_schedules=True,
        enable_queues=True,
        enable_analytics=True,
        enable_custom_branding=True,
        enable_sla_support=True,
        enable_audit_logs=True,
        features={
            "priority_support": True,
            "custom_notifications": True,
            "dedicated_account_manager": True,
            "custom_integrations": True,
            "ha_deployment": True,
            "disaster_recovery": True
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(enterprise_tier)
    
    # Commit changes
    db.commit()
    logger.info("Created default subscription tiers")

def init() -> None:
    """
    Initialize the database with default data.
    """
    db = SessionLocal()
    try:
        create_subscription_tiers(db)
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")