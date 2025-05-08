"""
Tenant service for managing tenant operations.

This module provides services for managing tenants, including CRUD operations
and tenant configuration.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models import Tenant, User, Role, Permission, RolePermission
from ..schemas.tenant import TenantCreate, TenantUpdate
from ..auth.permissions import SUPERUSER_PERMISSIONS, ADMIN_PERMISSIONS, USER_PERMISSIONS

logger = logging.getLogger(__name__)

class TenantService:
    """Service for managing tenants"""
    
    def __init__(self, db: Session):
        """
        Initialize the tenant service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def create_tenant(self, tenant_in: TenantCreate, created_by: Optional[str] = None) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            tenant_in: Tenant creation data
            created_by: Optional creator user ID
            
        Returns:
            Tenant: Created tenant
        """
        # Create tenant
        db_tenant = Tenant(
            tenant_id=uuid.uuid4(),
            name=tenant_in.name,
            status=tenant_in.status if tenant_in.status else "active",
            subscription_tier=tenant_in.subscription_tier if tenant_in.subscription_tier else "standard",
            max_concurrent_jobs=tenant_in.max_concurrent_jobs if tenant_in.max_concurrent_jobs else 50,
            max_agents=tenant_in.max_agents if tenant_in.max_agents else 10,
            settings=tenant_in.settings if tenant_in.settings else {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_tenant)
        self.db.commit()
        self.db.refresh(db_tenant)
        
        # Create default roles
        self._create_default_roles(db_tenant.tenant_id)
        
        # Create audit log
        if created_by:
            from ..models import AuditLog
            audit_log = AuditLog(
                log_id=uuid.uuid4(),
                tenant_id=db_tenant.tenant_id,
                user_id=uuid.UUID(created_by),
                action="create_tenant",
                entity_type="tenant",
                entity_id=db_tenant.tenant_id,
                created_at=datetime.utcnow(),
                details={
                    "name": db_tenant.name,
                    "subscription_tier": db_tenant.subscription_tier
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return db_tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Optional[Tenant]: Tenant or None if not found
        """
        return self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        """
        Get a tenant by name.
        
        Args:
            name: Tenant name
            
        Returns:
            Optional[Tenant]: Tenant or None if not found
        """
        return self.db.query(Tenant).filter(Tenant.name == name).first()
    
    def list_tenants(
        self,
        status: Optional[str] = None,
        subscription_tier: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Tenant]:
        """
        List tenants with filtering.
        
        Args:
            status: Optional status filter
            subscription_tier: Optional subscription tier filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Tenant]: List of tenants
        """
        query = self.db.query(Tenant)
        
        # Apply status filter
        if status:
            query = query.filter(Tenant.status == status)
        
        # Apply subscription tier filter
        if subscription_tier:
            query = query.filter(Tenant.subscription_tier == subscription_tier)
        
        # Apply search filter
        if search:
            query = query.filter(Tenant.name.ilike(f"%{search}%"))
        
        # Apply pagination
        query = query.order_by(Tenant.name).offset(skip).limit(limit)
        
        return query.all()
    
    def update_tenant(self, tenant_id: str, tenant_in: TenantUpdate, updated_by: Optional[str] = None) -> Optional[Tenant]:
        """
        Update a tenant.
        
        Args:
            tenant_id: Tenant ID
            tenant_in: Tenant update data
            updated_by: Optional updater user ID
            
        Returns:
            Optional[Tenant]: Updated tenant or None if not found
        """
        # Get tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        
        if not tenant:
            return None
        
        # Update fields
        update_data = tenant_in.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(tenant, key, value)
            
        # Update timestamp
        tenant.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(tenant)
        
        # Create audit log
        if updated_by:
            from ..models import AuditLog
            audit_log = AuditLog(
                log_id=uuid.uuid4(),
                tenant_id=tenant.tenant_id,
                user_id=uuid.UUID(updated_by),
                action="update_tenant",
                entity_type="tenant",
                entity_id=tenant.tenant_id,
                created_at=datetime.utcnow(),
                details={
                    "name": tenant.name,
                    "status": tenant.status,
                    "subscription_tier": tenant.subscription_tier,
                    "max_concurrent_jobs": tenant.max_concurrent_jobs,
                    "max_agents": tenant.max_agents,
                    "updated_fields": list(update_data.keys())
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        
        if not tenant:
            return False
        
        # Delete tenant
        self.db.delete(tenant)
        self.db.commit()
        
        return True
    
    def get_tenant_users(self, tenant_id: str) -> List[User]:
        """
        Get users for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List[User]: List of users
        """
        return self.db.query(User).filter(User.tenant_id == tenant_id).all()
    
    def get_tenant_user_count(self, tenant_id: str) -> int:
        """
        Get user count for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            int: User count
        """
        return self.db.query(func.count(User.user_id)).filter(User.tenant_id == tenant_id).scalar()
    
    def get_tenant_resource_usage(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get resource usage for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Dict[str, Any]: Resource usage statistics
        """
        # Get tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        
        if not tenant:
            return {}
        
        # Get user count
        user_count = self.get_tenant_user_count(tenant_id)
        
        # Get agent count
        from ..models import Agent
        agent_count = self.db.query(func.count(Agent.agent_id)).filter(Agent.tenant_id == tenant_id).scalar()
        
        # Get active job count
        from ..models import Job
        active_job_count = self.db.query(func.count(Job.job_id)).filter(
            Job.tenant_id == tenant_id,
            Job.status == "active"
        ).scalar()
        
        # Get running job count
        from ..models import JobExecution
        running_job_count = self.db.query(func.count(JobExecution.execution_id)).filter(
            JobExecution.tenant_id == tenant_id,
            JobExecution.status == "running"
        ).scalar()
        
        # Build usage data
        usage = {
            "users": {
                "count": user_count,
            },
            "agents": {
                "count": agent_count,
                "limit": tenant.max_agents,
                "usage_percentage": (agent_count / tenant.max_agents * 100) if tenant.max_agents > 0 else 0
            },
            "jobs": {
                "active_count": active_job_count,
                "running_count": running_job_count,
                "concurrent_limit": tenant.max_concurrent_jobs,
                "usage_percentage": (running_job_count / tenant.max_concurrent_jobs * 100) if tenant.max_concurrent_jobs > 0 else 0
            }
        }
        
        return usage
    
    def _create_default_roles(self, tenant_id: uuid.UUID) -> None:
        """
        Create default roles for a new tenant.
        
        Args:
            tenant_id: Tenant ID
        """
        # Get or create permissions
        permission_map = {}
        for permission_name in set(SUPERUSER_PERMISSIONS + ADMIN_PERMISSIONS + USER_PERMISSIONS):
            # Split into resource and action
            if ":" in permission_name:
                resource, action = permission_name.split(":", 1)
            else:
                resource = "system"
                action = permission_name
                
            # Check if permission exists
            permission = self.db.query(Permission).filter(
                Permission.name == permission_name
            ).first()
            
            if not permission:
                # Create permission
                permission = Permission(
                    permission_id=uuid.uuid4(),
                    name=permission_name,
                    resource=resource,
                    action=action,
                    created_at=datetime.utcnow()
                )
                self.db.add(permission)
                self.db.flush()
                
            permission_map[permission_name] = permission.permission_id
                
        # Create superuser role
        superuser_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="superuser",
            description="Super administrator with all permissions",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(superuser_role)
        self.db.flush()
        
        # Assign permissions to superuser
        for permission_name in SUPERUSER_PERMISSIONS:
            if permission_name in permission_map:
                role_permission = RolePermission(
                    role_id=superuser_role.role_id,
                    permission_id=permission_map[permission_name],
                    created_at=datetime.utcnow()
                )
                self.db.add(role_permission)
        
        # Create admin role
        admin_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="admin",
            description="Administrator with tenant management permissions",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(admin_role)
        self.db.flush()
        
        # Assign permissions to admin
        for permission_name in ADMIN_PERMISSIONS:
            if permission_name in permission_map:
                role_permission = RolePermission(
                    role_id=admin_role.role_id,
                    permission_id=permission_map[permission_name],
                    created_at=datetime.utcnow()
                )
                self.db.add(role_permission)
        
        # Create user role
        user_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="user",
            description="Standard user with basic permissions",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(user_role)
        self.db.flush()
        
        # Assign permissions to user
        for permission_name in USER_PERMISSIONS:
            if permission_name in permission_map:
                role_permission = RolePermission(
                    role_id=user_role.role_id,
                    permission_id=permission_map[permission_name],
                    created_at=datetime.utcnow()
                )
                self.db.add(role_permission)
        
        # Create viewer role
        viewer_role = Role(
            role_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name="viewer",
            description="Read-only access",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.db.add(viewer_role)
        self.db.flush()
        
        # Assign permissions to viewer
        for permission_name in ["job:read", "asset:read", "package:read", "queue:read", "schedule:read"]:
            if permission_name in permission_map:
                role_permission = RolePermission(
                    role_id=viewer_role.role_id,
                    permission_id=permission_map[permission_name],
                    created_at=datetime.utcnow()
                )
                self.db.add(role_permission)
        
        self.db.commit()