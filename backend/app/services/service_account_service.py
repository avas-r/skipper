"""
Service account service for managing service account operations.

This module provides services for managing service accounts.
"""

import uuid
import logging
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models import ServiceAccount, Agent, AgentSession, AuditLog, Tenant
from ..schemas.service_account import ServiceAccountCreate, ServiceAccountUpdate
from ..auth.auth import get_password_hash

logger = logging.getLogger(__name__)

class ServiceAccountService:
    """Service for managing service accounts"""
    
    def __init__(self, db: Session):
        """
        Initialize the service account service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def create_service_account(
        self, 
        service_account_in: ServiceAccountCreate, 
        tenant_id: str, 
        user_id: str
    ) -> ServiceAccount:
        """
        Create a new service account.
        
        Args:
            service_account_in: Service account data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            ServiceAccount: Created service account
        """
        # Validate tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")
        
        # Check if username already exists for tenant
        existing = self.db.query(ServiceAccount).filter(
            ServiceAccount.tenant_id == tenant_id,
            ServiceAccount.username == service_account_in.username
        ).first()
        
        if existing:
            raise ValueError(f"Service account with username '{service_account_in.username}' already exists")
        
        # Extract service account data
        service_account_data = service_account_in.dict(exclude={"password"})
        service_account_data["tenant_id"] = tenant_id
        service_account_data["created_by"] = user_id
        
        # Generate password if not provided
        password = service_account_in.password
        if not password:
            # Generate a secure random password
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create configuration with auto login settings
        service_account_data["configuration"] = {
            "auto_login": {},
            "creation_date": datetime.utcnow().isoformat(),
            "password_updated_at": datetime.utcnow().isoformat()
        }
        
        # Create service account
        service_account = ServiceAccount(**service_account_data)
        service_account.hashed_password = hashed_password
        
        self.db.add(service_account)
        self.db.commit()
        self.db.refresh(service_account)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_service_account",
            entity_type="service_account",
            entity_id=service_account.account_id,
            details={
                "username": service_account.username,
                "display_name": service_account.display_name,
                "account_type": service_account.account_type
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        # Temporarily attach the plain password to return to the client
        # This will be the only time the password is visible
        service_account.password = password
        
        return service_account
    
    def get_service_account(self, service_account_id: str, tenant_id: str) -> Optional[ServiceAccount]:
        """
        Get a service account by ID.
        
        Args:
            service_account_id: Service account ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[ServiceAccount]: Service account or None if not found
        """
        return self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == service_account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
    
    def list_service_accounts(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ServiceAccount]:
        """
        List service accounts with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ServiceAccount]: List of service accounts
        """
        query = self.db.query(ServiceAccount).filter(ServiceAccount.tenant_id == tenant_id)
        
        # Apply status filter
        if status:
            query = query.filter(ServiceAccount.status == status)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    ServiceAccount.username.ilike(f"%{search}%"),
                    ServiceAccount.display_name.ilike(f"%{search}%"),
                    ServiceAccount.description.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        query = query.order_by(ServiceAccount.username).offset(skip).limit(limit)
        
        return query.all()
    
    def update_service_account(
        self, 
        service_account_id: str, 
        service_account_in: ServiceAccountUpdate, 
        tenant_id: str, 
        user_id: str
    ) -> ServiceAccount:
        """
        Update a service account.
        
        Args:
            service_account_id: Service account ID
            service_account_in: Service account update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            ServiceAccount: Updated service account
        """
        # Get service account
        service_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == service_account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not service_account:
            raise ValueError(f"Service account not found: {service_account_id}")
        
        # Extract password before updating
        password = service_account_in.password
        update_data = service_account_in.dict(exclude={"password"}, exclude_unset=True)
        
        # Update service account fields
        for key, value in update_data.items():
            setattr(service_account, key, value)
            
        # Update password if provided
        if password:
            hashed_password = get_password_hash(password)
            service_account.hashed_password = hashed_password
            
            # Update password timestamp in configuration
            config = service_account.configuration or {}
            config["password_updated_at"] = datetime.utcnow().isoformat()
            service_account.configuration = config
            
        service_account.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(service_account)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_service_account",
            entity_type="service_account",
            entity_id=service_account.account_id,
            details={
                "username": service_account.username,
                "display_name": service_account.display_name,
                "password_changed": password is not None
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return service_account
    
    def delete_service_account(self, service_account_id: str, tenant_id: str, user_id: str) -> bool:
        """
        Delete a service account.
        
        Args:
            service_account_id: Service account ID
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get service account
        service_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == service_account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not service_account:
            raise ValueError(f"Service account not found: {service_account_id}")
        
        # Check if this account is used by any agents
        agent_count = self.db.query(Agent).filter(
            Agent.service_account_id == service_account_id
        ).count()
        
        if agent_count > 0:
            raise ValueError(f"Cannot delete service account that is used by {agent_count} agents")
            
        # Store details for audit log
        account_details = {
            "username": service_account.username,
            "display_name": service_account.display_name
        }
        
        # Delete service account
        self.db.delete(service_account)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete_service_account",
            entity_type="service_account",
            entity_id=service_account_id,
            details=account_details
        )
        self.db.add(audit_log)
        
        self.db.commit()
        
        return True
        
    def count_service_accounts(self, tenant_id: str, status: Optional[str] = None) -> int:
        """
        Count service accounts with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            
        Returns:
            int: Number of service accounts
        """
        query = self.db.query(func.count(ServiceAccount.account_id)).filter(
            ServiceAccount.tenant_id == tenant_id
        )
        
        # Apply status filter
        if status:
            query = query.filter(ServiceAccount.status == status)
        
        return query.scalar()
        
    def get_account_credentials(self, service_account_id: str, tenant_id: str, user_id: str = None):
        """
        Get service account credentials.
        
        Args:
            service_account_id: Service account ID
            tenant_id: Tenant ID
            user_id: Optional user ID for audit logging
            
        Returns:
            dict: Service account credentials
        """
        service_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == service_account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not service_account:
            return None
            
        # Create audit log for access if user ID provided
        if user_id:
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action="access_service_account_credentials",
                entity_type="service_account",
                entity_id=service_account_id,
                details={
                    "username": service_account.username
                }
            )
            self.db.add(audit_log)
            self.db.commit()
            
        # Create credentials response
        return {
            "username": service_account.username,
            "display_name": service_account.display_name,
            "configuration": service_account.configuration
        }