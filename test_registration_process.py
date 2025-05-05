#!/usr/bin/env python3
import sys
import os
import uuid
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project directory to Python path
sys.path.append('/home/vboxuser/orch/skipper/python_automation_orchestrator')

# Import project modules
from app.config import settings
from app.models import User, Tenant, TenantSubscription, SubscriptionTier
from app.services.subscription_service import SubscriptionService

def main():
    # Get database URL from config
    database_url = str(settings.SQLALCHEMY_DATABASE_URI)
    logger.info(f"Using database URL: {database_url}")
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create subscription service
        subscription_service = SubscriptionService(db)
        
        # Check if free tier exists
        free_tier = subscription_service.get_subscription_tier_by_name("free")
        if not free_tier:
            logger.error("Free tier not found! Registration will fail.")
            return
        
        logger.info(f"Found free tier with ID: {free_tier.tier_id}")
        
        # Register a test organization
        test_org_name = f"Test Org {uuid.uuid4()}"
        test_email = f"test_{uuid.uuid4()}@example.com"
        
        logger.info(f"Registering organization: {test_org_name}, email: {test_email}")
        
        result = subscription_service.register_organization(
            organization_name=test_org_name,
            full_name="Test User",
            email=test_email,
            password="password123",
            subscription_tier="free"
        )
        
        if result["success"]:
            logger.info("Registration successful!")
            logger.info(f"Tenant ID: {result['tenant_id']}")
            logger.info(f"User ID: {result['user_id']}")
            logger.info(f"Subscription ID: {result['subscription_id']}")
            
            # Verify tenant was created
            tenant = db.query(Tenant).filter(Tenant.tenant_id == uuid.UUID(result['tenant_id'])).first()
            logger.info(f"Tenant: {tenant.name}, ID: {tenant.tenant_id}")
            
            # Verify user was created
            user = db.query(User).filter(User.user_id == uuid.UUID(result['user_id'])).first()
            logger.info(f"User: {user.email}, ID: {user.user_id}")
            
            # Verify subscription was created
            subscription = db.query(TenantSubscription).filter(
                TenantSubscription.subscription_id == uuid.UUID(result['subscription_id'])
            ).first()
            logger.info(f"Subscription: {subscription.subscription_id}, status: {subscription.status}")
            
            # Clean up
            logger.info("Cleaning up test data...")
            # Delete user roles
            db.execute("DELETE FROM user_roles WHERE user_id = :user_id", {"user_id": user.user_id})
            # Delete subscription
            db.query(TenantSubscription).filter(TenantSubscription.subscription_id == subscription.subscription_id).delete()
            # Delete user
            db.query(User).filter(User.user_id == user.user_id).delete()
            # Delete tenant
            db.query(Tenant).filter(Tenant.tenant_id == tenant.tenant_id).delete()
            db.commit()
            logger.info("Test data cleaned up")
            
        else:
            logger.error(f"Registration failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        db.rollback()
        raise
    
    finally:
        # Close session
        db.close()

if __name__ == "__main__":
    main()