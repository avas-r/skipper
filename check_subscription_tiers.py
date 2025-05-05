#!/usr/bin/env python3
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get database URL based on the app's configuration
sys.path.append('/home/vboxuser/orch/skipper/python_automation_orchestrator')
from app.config import settings

database_url = str(settings.SQLALCHEMY_DATABASE_URI)
logger.info(f"Using database URL: {database_url}")

try:
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Check if subscription_tiers table exists
    result = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'subscription_tiers')"))
    table_exists = result.scalar()
    
    if not table_exists:
        logger.error("subscription_tiers table does not exist!")
        sys.exit(1)
    
    # Count tiers
    result = db.execute(text("SELECT COUNT(*) FROM subscription_tiers"))
    tier_count = result.scalar()
    logger.info(f"Found {tier_count} subscription tiers")
    
    # List all tiers
    if tier_count > 0:
        result = db.execute(text("SELECT tier_id, name, display_name, price_monthly, price_yearly FROM subscription_tiers"))
        tiers = result.fetchall()
        
        logger.info("Subscription tiers:")
        for tier in tiers:
            logger.info(f"  - {tier.tier_id}: {tier.name} ({tier.display_name}) - ${tier.price_monthly}/month, ${tier.price_yearly}/year")
    else:
        logger.warning("No subscription tiers found. Creating default tiers...")
        
        # Create default tiers if none exist
        from datetime import datetime
        import uuid
        
        # Insert free tier
        db.execute(text("""
            INSERT INTO subscription_tiers (
                tier_id, name, display_name, description, price_monthly, price_yearly, 
                is_public, max_agents, max_concurrent_jobs, max_schedules, max_queues, 
                storage_gb, max_api_calls_daily, enable_api_access, enable_schedules, enable_queues, 
                enable_analytics, enable_custom_branding, enable_sla_support, enable_audit_logs, 
                features, created_at, updated_at
            ) VALUES (
                :tier_id, 'free', 'Free', 'Limited resources for evaluation purposes', 0, 0, 
                TRUE, 2, 5, 2, 2, 
                1, 1000, TRUE, TRUE, TRUE, 
                FALSE, FALSE, FALSE, FALSE, 
                '{}', :created_at, :updated_at
            )
        """), {
            "tier_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert standard tier
        db.execute(text("""
            INSERT INTO subscription_tiers (
                tier_id, name, display_name, description, price_monthly, price_yearly, 
                is_public, max_agents, max_concurrent_jobs, max_schedules, max_queues, 
                storage_gb, max_api_calls_daily, enable_api_access, enable_schedules, enable_queues, 
                enable_analytics, enable_custom_branding, enable_sla_support, enable_audit_logs, 
                features, created_at, updated_at
            ) VALUES (
                :tier_id, 'standard', 'Standard', 'For small businesses with moderate resource needs', 49.99, 499.99, 
                TRUE, 10, 25, 10, 10, 
                10, 10000, TRUE, TRUE, TRUE, 
                TRUE, FALSE, FALSE, FALSE, 
                '{}', :created_at, :updated_at
            )
        """), {
            "tier_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert professional tier
        db.execute(text("""
            INSERT INTO subscription_tiers (
                tier_id, name, display_name, description, price_monthly, price_yearly, 
                is_public, max_agents, max_concurrent_jobs, max_schedules, max_queues, 
                storage_gb, max_api_calls_daily, enable_api_access, enable_schedules, enable_queues, 
                enable_analytics, enable_custom_branding, enable_sla_support, enable_audit_logs, 
                features, created_at, updated_at
            ) VALUES (
                :tier_id, 'professional', 'Professional', 'For mid-sized companies with advanced automation needs', 199.99, 1999.99, 
                TRUE, 50, 100, 50, 50, 
                50, 50000, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE, FALSE, 
                '{}', :created_at, :updated_at
            )
        """), {
            "tier_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Insert enterprise tier
        db.execute(text("""
            INSERT INTO subscription_tiers (
                tier_id, name, display_name, description, price_monthly, price_yearly, 
                is_public, max_agents, max_concurrent_jobs, max_schedules, max_queues, 
                storage_gb, max_api_calls_daily, enable_api_access, enable_schedules, enable_queues, 
                enable_analytics, enable_custom_branding, enable_sla_support, enable_audit_logs, 
                features, created_at, updated_at
            ) VALUES (
                :tier_id, 'enterprise', 'Enterprise', 'For large organizations with high-volume automation requirements', 999.99, 9999.99, 
                TRUE, 250, 500, 250, 250, 
                500, 1000000, TRUE, TRUE, TRUE, 
                TRUE, TRUE, TRUE, TRUE, 
                '{}', :created_at, :updated_at
            )
        """), {
            "tier_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        db.commit()
        logger.info("Created default subscription tiers")
    
    # Check if roles table exists and has the admin role
    result = db.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'roles')"))
    roles_table_exists = result.scalar()
    
    if roles_table_exists:
        # Count admin roles
        result = db.execute(text("SELECT COUNT(*) FROM roles WHERE name = 'admin'"))
        admin_role_count = result.scalar()
        logger.info(f"Found {admin_role_count} admin roles")
    else:
        logger.error("roles table does not exist!")
    
    # Close the session
    db.close()
    
except Exception as e:
    logger.error(f"Error: {str(e)}")
    sys.exit(1)