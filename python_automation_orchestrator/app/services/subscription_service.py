"""
Subscription service for managing subscription operations.

This module provides services for managing subscription tiers, tenant subscriptions,
and feature access based on subscription tiers.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models import Tenant, SubscriptionTier, TenantSubscription, User
from ..schemas.subscription import (
    SubscriptionTierCreate,
    SubscriptionTierUpdate,
    TenantSubscriptionCreate,
    TenantSubscriptionUpdate,
    FeatureAccess,
    SubscriptionSummary
)
from ..schemas.tenant import TenantCreate, TenantUpdate

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing subscriptions"""
    
    def __init__(self, db: Session):
        """
        Initialize the subscription service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    # Subscription tier management
    
    def create_subscription_tier(self, tier_in: SubscriptionTierCreate) -> SubscriptionTier:
        """
        Create a new subscription tier.
        
        Args:
            tier_in: Tier creation data
            
        Returns:
            SubscriptionTier: Created tier
        """
        # Create tier
        db_tier = SubscriptionTier(
            tier_id=uuid.uuid4(),
            name=tier_in.name,
            display_name=tier_in.display_name,
            description=tier_in.description,
            price_monthly=tier_in.price_monthly,
            price_yearly=tier_in.price_yearly,
            is_public=tier_in.is_public,
            max_agents=tier_in.max_agents,
            max_concurrent_jobs=tier_in.max_concurrent_jobs,
            max_schedules=tier_in.max_schedules,
            max_queues=tier_in.max_queues,
            storage_gb=tier_in.storage_gb,
            max_api_calls_daily=tier_in.max_api_calls_daily,
            enable_api_access=tier_in.enable_api_access,
            enable_schedules=tier_in.enable_schedules,
            enable_queues=tier_in.enable_queues,
            enable_analytics=tier_in.enable_analytics,
            enable_custom_branding=tier_in.enable_custom_branding,
            enable_sla_support=tier_in.enable_sla_support,
            enable_audit_logs=tier_in.enable_audit_logs,
            features=tier_in.features or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_tier)
        self.db.commit()
        self.db.refresh(db_tier)
        
        return db_tier
    
    def get_subscription_tier(self, tier_id: str) -> Optional[SubscriptionTier]:
        """
        Get a subscription tier by ID.
        
        Args:
            tier_id: Tier ID
            
        Returns:
            Optional[SubscriptionTier]: Tier or None if not found
        """
        return self.db.query(SubscriptionTier).filter(SubscriptionTier.tier_id == tier_id).first()
    
    def get_subscription_tier_by_name(self, name: str) -> Optional[SubscriptionTier]:
        """
        Get a subscription tier by name.
        
        Args:
            name: Tier name
            
        Returns:
            Optional[SubscriptionTier]: Tier or None if not found
        """
        return self.db.query(SubscriptionTier).filter(SubscriptionTier.name == name).first()
    
    def list_subscription_tiers(self, public_only: bool = False) -> List[SubscriptionTier]:
        """
        List all subscription tiers.
        
        Args:
            public_only: Whether to return only public tiers
            
        Returns:
            List[SubscriptionTier]: List of tiers
        """
        query = self.db.query(SubscriptionTier)
        
        if public_only:
            query = query.filter(SubscriptionTier.is_public == True)
        
        return query.order_by(SubscriptionTier.price_monthly).all()
    
    def update_subscription_tier(self, tier_id: str, tier_in: SubscriptionTierUpdate) -> Optional[SubscriptionTier]:
        """
        Update a subscription tier.
        
        Args:
            tier_id: Tier ID
            tier_in: Tier update data
            
        Returns:
            Optional[SubscriptionTier]: Updated tier or None if not found
        """
        # Get tier
        tier = self.db.query(SubscriptionTier).filter(SubscriptionTier.tier_id == tier_id).first()
        
        if not tier:
            return None
        
        # Update fields
        update_data = tier_in.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(tier, key, value)
            
        # Update timestamp
        tier.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(tier)
        
        return tier
    
    def delete_subscription_tier(self, tier_id: str) -> bool:
        """
        Delete a subscription tier.
        
        Args:
            tier_id: Tier ID
            
        Returns:
            bool: True if deletion successful
        """
        # Check if tier is in use
        subscription_count = self.db.query(TenantSubscription).filter(
            TenantSubscription.tier_id == tier_id
        ).count()
        
        if subscription_count > 0:
            logger.warning(f"Cannot delete tier {tier_id} as it is being used by {subscription_count} tenants")
            return False
        
        # Get tier
        tier = self.db.query(SubscriptionTier).filter(SubscriptionTier.tier_id == tier_id).first()
        
        if not tier:
            return False
        
        # Delete tier
        self.db.delete(tier)
        self.db.commit()
        
        return True
    
    # Tenant subscription management
    
    def create_tenant_subscription(self, subscription_in: TenantSubscriptionCreate) -> TenantSubscription:
        """
        Create a new tenant subscription.
        
        Args:
            subscription_in: Subscription creation data
            
        Returns:
            TenantSubscription: Created subscription
        """
        # Calculate dates
        start_date = datetime.utcnow()
        next_billing_date = None
        end_date = None
        
        # For trial subscriptions
        if subscription_in.is_trial:
            trial_days = 14  # Default trial period
            trial_end_date = start_date + timedelta(days=trial_days)
            next_billing_date = trial_end_date
        else:
            # Calculate next billing date based on billing cycle
            if subscription_in.billing_cycle == "monthly":
                next_billing_date = start_date + timedelta(days=30)
            elif subscription_in.billing_cycle == "yearly":
                next_billing_date = start_date + timedelta(days=365)
        
        # Create subscription
        db_subscription = TenantSubscription(
            subscription_id=uuid.uuid4(),
            tenant_id=subscription_in.tenant_id,
            tier_id=subscription_in.tier_id,
            billing_cycle=subscription_in.billing_cycle,
            status=subscription_in.status,
            start_date=start_date,
            end_date=end_date,
            trial_end_date=subscription_in.trial_end_date,
            next_billing_date=next_billing_date,
            auto_renew=subscription_in.auto_renew,
            is_trial=subscription_in.is_trial,
            price_override=subscription_in.price_override,
            max_agents_override=subscription_in.max_agents_override,
            max_concurrent_jobs_override=subscription_in.max_concurrent_jobs_override,
            feature_overrides=subscription_in.feature_overrides,
            payment_provider=subscription_in.payment_provider,
            external_subscription_id=subscription_in.external_subscription_id,
            external_customer_id=subscription_in.external_customer_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_subscription)
        self.db.commit()
        self.db.refresh(db_subscription)
        
        # Update tenant resource limits based on tier
        self._update_tenant_resource_limits(db_subscription)
        
        return db_subscription
    
    def get_tenant_subscription(self, subscription_id: str) -> Optional[TenantSubscription]:
        """
        Get a tenant subscription by ID.
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Optional[TenantSubscription]: Subscription or None if not found
        """
        return self.db.query(TenantSubscription).filter(
            TenantSubscription.subscription_id == subscription_id
        ).first()
    
    def get_subscription_by_tenant(self, tenant_id: str) -> Optional[TenantSubscription]:
        """
        Get a tenant's active subscription.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Optional[TenantSubscription]: Subscription or None if not found
        """
        return self.db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status.in_(["active", "trialing"])
        ).first()
    
    def update_tenant_subscription(
        self, 
        subscription_id: str, 
        subscription_in: TenantSubscriptionUpdate
    ) -> Optional[TenantSubscription]:
        """
        Update a tenant subscription.
        
        Args:
            subscription_id: Subscription ID
            subscription_in: Subscription update data
            
        Returns:
            Optional[TenantSubscription]: Updated subscription or None if not found
        """
        # Get subscription
        subscription = self.db.query(TenantSubscription).filter(
            TenantSubscription.subscription_id == subscription_id
        ).first()
        
        if not subscription:
            return None
        
        # Update fields
        update_data = subscription_in.model_dump(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(subscription, key, value)
            
        # Handle tier change
        if "tier_id" in update_data:
            # Recalculate next billing date if needed
            if subscription.status == "active":
                if subscription.billing_cycle == "monthly":
                    subscription.next_billing_date = datetime.utcnow() + timedelta(days=30)
                elif subscription.billing_cycle == "yearly":
                    subscription.next_billing_date = datetime.utcnow() + timedelta(days=365)
        
        # Handle status change
        if "status" in update_data:
            if update_data["status"] == "canceled":
                subscription.canceled_at = datetime.utcnow()
                
        # Update timestamp
        subscription.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(subscription)
        
        # Update tenant resource limits based on tier
        self._update_tenant_resource_limits(subscription)
        
        return subscription
    
    def cancel_subscription(self, subscription_id: str, cancel_immediately: bool = False) -> Optional[TenantSubscription]:
        """
        Cancel a tenant subscription.
        
        Args:
            subscription_id: Subscription ID
            cancel_immediately: Whether to cancel immediately or at the end of the billing period
            
        Returns:
            Optional[TenantSubscription]: Updated subscription or None if not found
        """
        # Get subscription
        subscription = self.db.query(TenantSubscription).filter(
            TenantSubscription.subscription_id == subscription_id
        ).first()
        
        if not subscription:
            return None
        
        # Update subscription
        subscription.auto_renew = False
        subscription.canceled_at = datetime.utcnow()
        
        if cancel_immediately:
            subscription.status = "canceled"
            subscription.end_date = datetime.utcnow()
        else:
            # Will be canceled at the end of the billing period
            subscription.end_date = subscription.next_billing_date
        
        subscription.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(subscription)
        
        return subscription
    
    def change_subscription_tier(
        self, 
        tenant_id: str, 
        new_tier_id: str,
        prorate: bool = True
    ) -> Optional[TenantSubscription]:
        """
        Change a tenant's subscription tier.
        
        Args:
            tenant_id: Tenant ID
            new_tier_id: New tier ID
            prorate: Whether to prorate the billing
            
        Returns:
            Optional[TenantSubscription]: Updated subscription or None if not found
        """
        # Get subscription
        subscription = self.get_subscription_by_tenant(tenant_id)
        
        if not subscription:
            return None
        
        # Update tier
        old_tier_id = subscription.tier_id
        subscription.tier_id = uuid.UUID(new_tier_id)
        
        # Handle proration
        if prorate and subscription.status == "active":
            # Proration logic would go here
            # This could involve calculating a credit or additional charge
            pass
        
        # Adjust billing date if necessary
        # For simplicity, we'll keep the same billing cycle
        
        subscription.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(subscription)
        
        # Update tenant resource limits based on new tier
        self._update_tenant_resource_limits(subscription)
        
        # Record tier change in audit log
        from ..models import AuditLog
        audit_log = AuditLog(
            log_id=uuid.uuid4(),
            tenant_id=subscription.tenant_id,
            action="change_subscription_tier",
            entity_type="subscription",
            entity_id=subscription.subscription_id,
            created_at=datetime.utcnow(),
            details={
                "old_tier_id": str(old_tier_id),
                "new_tier_id": new_tier_id,
                "prorate": prorate
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return subscription
    
    def get_subscription_summary(self, tenant_id: str) -> SubscriptionSummary:
        """
        Get a summary of a tenant's subscription.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            SubscriptionSummary: Subscription summary
        """
        # Get subscription with tier
        subscription = self.get_subscription_by_tenant(tenant_id)
        
        if not subscription:
            # Return free tier summary
            free_tier = self.get_subscription_tier_by_name("free")
            if not free_tier:
                # If no free tier is defined in the database, use defaults
                return SubscriptionSummary(
                    tier_name="free",
                    tier_display_name="Free",
                    status="active",
                    billing_cycle="monthly",
                    price=0.0,
                    next_billing_date=None,
                    max_agents=2,
                    max_concurrent_jobs=5,
                    max_schedules=2,
                    max_queues=2,
                    features={
                        "api_access": True,
                        "schedules": True,
                        "queues": True,
                        "analytics": False,
                        "custom_branding": False,
                        "sla_support": False,
                        "audit_logs": False
                    }
                )
            else:
                # Use the free tier defined in the database
                return SubscriptionSummary(
                    tier_name=free_tier.name,
                    tier_display_name=free_tier.display_name,
                    status="active",
                    billing_cycle="monthly",
                    price=0.0,
                    next_billing_date=None,
                    max_agents=free_tier.max_agents,
                    max_concurrent_jobs=free_tier.max_concurrent_jobs,
                    max_schedules=free_tier.max_schedules,
                    max_queues=free_tier.max_queues,
                    features={
                        "api_access": free_tier.enable_api_access,
                        "schedules": free_tier.enable_schedules,
                        "queues": free_tier.enable_queues,
                        "analytics": free_tier.enable_analytics,
                        "custom_branding": free_tier.enable_custom_branding,
                        "sla_support": free_tier.enable_sla_support,
                        "audit_logs": free_tier.enable_audit_logs
                    }
                )
        
        # Get tier
        tier = self.get_subscription_tier(str(subscription.tier_id))
        
        if not tier:
            logger.error(f"Tier {subscription.tier_id} not found for subscription {subscription.subscription_id}")
            return None
        
        # Get price based on billing cycle and overrides
        price = subscription.price_override or (
            tier.price_yearly if subscription.billing_cycle == "yearly" else tier.price_monthly
        )
        
        # Build feature map
        features = {
            "api_access": tier.enable_api_access,
            "schedules": tier.enable_schedules,
            "queues": tier.enable_queues,
            "analytics": tier.enable_analytics,
            "custom_branding": tier.enable_custom_branding,
            "sla_support": tier.enable_sla_support,
            "audit_logs": tier.enable_audit_logs
        }
        
        # Apply feature overrides
        if subscription.feature_overrides:
            for key, value in subscription.feature_overrides.items():
                if key in features:
                    features[key] = value
        
        # Apply resource limit overrides
        max_agents = subscription.max_agents_override or tier.max_agents
        max_concurrent_jobs = subscription.max_concurrent_jobs_override or tier.max_concurrent_jobs
        
        # Create summary
        summary = SubscriptionSummary(
            tier_name=tier.name,
            tier_display_name=tier.display_name,
            status=subscription.status,
            billing_cycle=subscription.billing_cycle,
            price=price,
            next_billing_date=subscription.next_billing_date,
            max_agents=max_agents,
            max_concurrent_jobs=max_concurrent_jobs,
            max_schedules=tier.max_schedules,
            max_queues=tier.max_queues,
            features=features,
            is_trial=subscription.is_trial,
            trial_end_date=subscription.trial_end_date
        )
        
        return summary
    
    def check_feature_access(self, tenant_id: str, feature: str) -> FeatureAccess:
        """
        Check if a tenant has access to a specific feature based on their subscription.
        
        Args:
            tenant_id: Tenant ID
            feature: Feature name
            
        Returns:
            FeatureAccess: Feature access information
        """
        # Get subscription and tier
        subscription = self.get_subscription_by_tenant(tenant_id)
        
        if not subscription:
            # Default to free tier
            free_tier = self.get_subscription_tier_by_name("free")
            if not free_tier:
                # No free tier defined, deny access
                return FeatureAccess(
                    feature=feature,
                    has_access=False,
                    reason="No active subscription",
                    upgrade_to=["standard", "professional", "enterprise"]
                )
            
            # Check free tier access
            return self._check_tier_feature_access(free_tier, feature)
        
        # Get tier
        tier = self.get_subscription_tier(str(subscription.tier_id))
        
        if not tier:
            logger.error(f"Tier {subscription.tier_id} not found for subscription {subscription.subscription_id}")
            return FeatureAccess(
                feature=feature,
                has_access=False,
                reason="Subscription tier not found",
                upgrade_to=["standard", "professional", "enterprise"]
            )
        
        # Check for feature overrides
        if subscription.feature_overrides and feature in subscription.feature_overrides:
            has_access = subscription.feature_overrides.get(feature, False)
            if has_access:
                return FeatureAccess(feature=feature, has_access=True)
            else:
                return FeatureAccess(
                    feature=feature,
                    has_access=False,
                    reason="Feature not available in your subscription",
                    upgrade_to=self._get_upgrade_tiers(tier.name, feature)
                )
        
        # Check tier access
        return self._check_tier_feature_access(tier, feature)
    
    def _check_tier_feature_access(self, tier: SubscriptionTier, feature: str) -> FeatureAccess:
        """
        Check if a tier has access to a specific feature.
        
        Args:
            tier: Subscription tier
            feature: Feature name
            
        Returns:
            FeatureAccess: Feature access information
        """
        # Map feature names to tier attributes
        feature_map = {
            "api_access": "enable_api_access",
            "schedules": "enable_schedules",
            "queues": "enable_queues",
            "analytics": "enable_analytics",
            "custom_branding": "enable_custom_branding",
            "sla_support": "enable_sla_support",
            "audit_logs": "enable_audit_logs"
        }
        
        # Check tier attribute
        if feature in feature_map:
            tier_attr = feature_map[feature]
            has_access = getattr(tier, tier_attr, False)
            
            if has_access:
                return FeatureAccess(feature=feature, has_access=True)
            else:
                return FeatureAccess(
                    feature=feature,
                    has_access=False,
                    reason=f"Feature '{feature}' not available in your subscription tier",
                    upgrade_to=self._get_upgrade_tiers(tier.name, feature)
                )
        
        # Check custom features in JSON
        if tier.features and feature in tier.features:
            has_access = tier.features.get(feature, False)
            
            if has_access:
                return FeatureAccess(feature=feature, has_access=True)
            else:
                return FeatureAccess(
                    feature=feature,
                    has_access=False,
                    reason=f"Feature '{feature}' not available in your subscription tier",
                    upgrade_to=self._get_upgrade_tiers(tier.name, feature)
                )
        
        # Feature not found
        return FeatureAccess(
            feature=feature,
            has_access=False,
            reason=f"Unknown feature '{feature}'",
            upgrade_to=self._get_upgrade_tiers(tier.name, feature)
        )
    
    def _get_upgrade_tiers(self, current_tier: str, feature: str) -> List[str]:
        """
        Get a list of tiers that have access to a feature and are upgrades from the current tier.
        
        Args:
            current_tier: Current tier name
            feature: Feature name
            
        Returns:
            List[str]: List of tier names
        """
        # Map feature names to tier attributes
        feature_map = {
            "api_access": "enable_api_access",
            "schedules": "enable_schedules",
            "queues": "enable_queues",
            "analytics": "enable_analytics",
            "custom_branding": "enable_custom_branding",
            "sla_support": "enable_sla_support",
            "audit_logs": "enable_audit_logs"
        }
        
        # Tier hierarchy
        tier_levels = {
            "free": 0,
            "standard": 1,
            "professional": 2,
            "enterprise": 3
        }
        
        current_level = tier_levels.get(current_tier, 0)
        upgrade_tiers = []
        
        # Check which higher tiers have the feature
        for tier in self.list_subscription_tiers(public_only=True):
            tier_level = tier_levels.get(tier.name, 0)
            
            # Only consider higher tiers
            if tier_level <= current_level:
                continue
            
            # Check if tier has the feature
            has_feature = False
            
            if feature in feature_map:
                # Check attribute
                tier_attr = feature_map[feature]
                has_feature = getattr(tier, tier_attr, False)
            
            if not has_feature and tier.features and feature in tier.features:
                # Check custom features
                has_feature = tier.features.get(feature, False)
            
            if has_feature:
                upgrade_tiers.append(tier.name)
        
        return upgrade_tiers
    
    def _update_tenant_resource_limits(self, subscription: TenantSubscription) -> None:
        """
        Update a tenant's resource limits based on their subscription.
        
        Args:
            subscription: Tenant subscription
        """
        # Get tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == subscription.tenant_id).first()
        
        if not tenant:
            logger.error(f"Tenant {subscription.tenant_id} not found for subscription {subscription.subscription_id}")
            return
        
        # Get tier
        tier = self.get_subscription_tier(str(subscription.tier_id))
        
        if not tier:
            logger.error(f"Tier {subscription.tier_id} not found for subscription {subscription.subscription_id}")
            return
        
        # Update tenant resource limits
        tenant.max_agents = subscription.max_agents_override or tier.max_agents
        tenant.max_concurrent_jobs = subscription.max_concurrent_jobs_override or tier.max_concurrent_jobs
        
        # Update subscription_tier field for backwards compatibility
        tenant.subscription_tier = tier.name
        
        # Save changes
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
    
    # Organization registration
    
    def register_organization(
        self, 
        organization_name: str, 
        full_name: str, 
        email: str, 
        password: str, 
        subscription_tier: str = "free"
    ) -> Dict[str, Any]:
        """
        Register a new organization with a user and subscription.
        
        Args:
            organization_name: Organization name
            full_name: User's full name
            email: User's email
            password: User's password
            subscription_tier: Subscription tier name
            
        Returns:
            Dict[str, Any]: Registration result
        """
        # Import services
        from ..services.tenant_service import TenantService
        from ..services.user_service import UserService
        
        # Create services
        tenant_service = TenantService(self.db)
        user_service = UserService(self.db)
        
        # Begin transaction
        try:
            logger.info(f"Starting registration for organization: {organization_name}, user: {email}")
            
            # 1. Create tenant
            tenant_in = TenantCreate(
                name=organization_name,
                subscription_tier=subscription_tier
            )
            
            logger.info(f"Creating tenant with data: {tenant_in}")
            tenant = tenant_service.create_tenant(tenant_in=tenant_in)
            logger.info(f"Tenant created with ID: {tenant.tenant_id}")
            
            # 2. Create admin user
            from ..schemas.user import UserCreate
            
            # Create UserCreate object
            user_in = UserCreate(
                email=email,
                password=password,
                full_name=full_name,
                roles=["admin"],  # Set admin role
                tenant_id=tenant.tenant_id  # Include the tenant_id in UserCreate
            )
            
            logger.info(f"Creating user with data: {user_in.email}, tenant_id: {user_in.tenant_id}, roles: {user_in.roles}")
            
            # Create the user - tenant_id is already in user_in
            user = user_service.create_user(
                user_in=user_in,
                tenant_id=str(tenant.tenant_id)  # This is expected by the service
            )
            logger.info(f"User created with ID: {user.user_id}")
            
            # 3. Create subscription
            tier = self.get_subscription_tier_by_name(subscription_tier)
            
            if not tier:
                logger.error(f"Subscription tier '{subscription_tier}' not found")
                # Roll back transaction
                self.db.rollback()
                return {
                    "success": False,
                    "error": f"Subscription tier '{subscription_tier}' not found"
                }
            
            logger.info(f"Found subscription tier: {tier.name}, ID: {tier.tier_id}")
            
            # Determine if this should be a trial
            is_trial = subscription_tier != "free"
            trial_end_date = None
            
            if is_trial:
                trial_days = 14  # Default trial period
                trial_end_date = datetime.utcnow() + timedelta(days=trial_days)
            
            # Create subscription
            subscription_in = TenantSubscriptionCreate(
                tenant_id=tenant.tenant_id,
                tier_id=tier.tier_id,
                status="trialing" if is_trial else "active",
                is_trial=is_trial,
                trial_end_date=trial_end_date,
                billing_cycle="monthly"  # Default to monthly billing
            )
            
            logger.info(f"Creating subscription with data: {subscription_in}")
            subscription = self.create_tenant_subscription(subscription_in)
            logger.info(f"Subscription created with ID: {subscription.subscription_id}")
            
            # Commit transaction
            self.db.commit()
            logger.info(f"Registration completed successfully for organization: {organization_name}")
            
            # Return success
            return {
                "success": True,
                "tenant_id": str(tenant.tenant_id),
                "user_id": str(user.user_id),
                "subscription_id": str(subscription.subscription_id)
            }
            
        except Exception as e:
            # Roll back transaction on error
            self.db.rollback()
            logger.exception(f"Error registering organization: {str(e)}")
            
            return {
                "success": False,
                "error": str(e)
            }