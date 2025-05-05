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
from .python_automation_orchestrator.app.config import settings
from app.models import User, Tenant, Role, UserRole
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.auth.auth import get_password_hash, verify_password

def main():
    # Get database URL from config
    database_url = str(settings.SQLALCHEMY_DATABASE_URI)
    logger.info(f"Using database URL: {database_url}")
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Create a sample tenant
        tenant_id = uuid.uuid4()
        tenant = Tenant(
            tenant_id=tenant_id,
            name="Test Tenant",
            subscription_tier="free",
            created_at=None,
            updated_at=None
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        logger.info(f"Created test tenant with ID: {tenant.tenant_id}")
        
        # Create user service
        user_service = UserService(db)
        
        # Create test user with tenant_id as UUID
        user_in = UserCreate(
            email="test_uuid@example.com",
            password="password123",
            full_name="Test UUID User",
            tenant_id=tenant.tenant_id,  # This is a UUID object
            roles=["admin"]
        )
        
        logger.info(f"Creating user with tenant_id as UUID: {user_in.tenant_id}, type: {type(user_in.tenant_id)}")
        user = user_service.create_user(
            user_in=user_in,
            tenant_id=str(tenant.tenant_id)
        )
        logger.info(f"Created user with ID: {user.user_id}")
        
        # Create test user with tenant_id as string
        user_in2 = UserCreate(
            email="test_string@example.com",
            password="password123",
            full_name="Test String User",
            tenant_id=str(tenant.tenant_id),  # This is a string
            roles=["admin"]
        )
        
        logger.info(f"Creating user with tenant_id as string: {user_in2.tenant_id}, type: {type(user_in2.tenant_id)}")
        user2 = user_service.create_user(
            user_in=user_in2,
            tenant_id=str(tenant.tenant_id)
        )
        logger.info(f"Created user with ID: {user2.user_id}")
        
        # Verify we can retrieve the created users
        users = db.query(User).filter(User.tenant_id == tenant.tenant_id).all()
        logger.info(f"Found {len(users)} users for tenant")
        for u in users:
            logger.info(f"  - {u.user_id}: {u.email}")
        
        logger.info("Test completed successfully!")
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    
    finally:
        # Clean up - delete test data
        try:
            logger.info("Cleaning up test data...")
            # Delete user roles
            db.query(UserRole).filter(
                UserRole.user_id.in_([u.user_id for u in db.query(User).filter(User.tenant_id == tenant_id).all()])
            ).delete(synchronize_session=False)
            # Delete users
            db.query(User).filter(User.tenant_id == tenant_id).delete(synchronize_session=False)
            # Delete tenant
            db.query(Tenant).filter(Tenant.tenant_id == tenant_id).delete(synchronize_session=False)
            db.commit()
            logger.info("Test data cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up test data: {str(e)}")
            db.rollback()
        
        # Close session
        db.close()

if __name__ == "__main__":
    main()