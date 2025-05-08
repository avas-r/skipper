"""
API dependencies for the orchestrator application.

This module provides common dependencies for API endpoints,
including database session, authentication, and authorization.
"""

import time
import logging
from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from ...auth.jwt import get_current_user, get_current_active_user
from ...auth.permissions import has_permission, has_permissions, PermissionChecker
from ...db.session import get_db, SessionLocal
from ...models import User, Tenant, Agent, ServiceAccount
from ...utils.logging import log_request, log_response

logger = logging.getLogger(__name__)

class RequestTimer:
    """Middleware for timing API requests"""
    
    async def __call__(self, request: Request, call_next):
        """Time an API request"""
        start_time = time.time()
        
        # Log request
        request_info = log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Log response
        log_response(response, processing_time)
        
        # Add timing header
        response.headers["X-Process-Time"] = str(processing_time)
        
        return response

async def get_tenant_from_path(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Tenant:
    """
    Get tenant from path parameter and verify access.
    
    Args:
        tenant_id: Tenant ID from path
        db: Database session
        current_user: Current user
        
    Returns:
        Tenant: Tenant object
        
    Raises:
        HTTPException: If tenant not found or user doesn't have access
    """
    # Check if user has access to tenant
    if str(current_user.tenant_id) != tenant_id:
        # Allow superusers to access any tenant
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to other tenants is not allowed"
            )
    
    # Get tenant
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
        
    return tenant

async def get_service_account_from_path(
    service_account_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> ServiceAccount:
    """
    Get service account from path parameter and verify access.
    
    Args:
        service_account_id: Service Account ID from path
        db: Database session
        current_user: Current user
        
    Returns:
        ServiceAccount: Service Account object
        
    Raises:
        HTTPException: If service account not found or user doesn't have access
    """
    # Get service account
    service_account = db.query(ServiceAccount).filter(ServiceAccount.account_id == service_account_id).first()
    if not service_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
        
    # Check if user has access to service account's tenant
    if str(current_user.tenant_id) != str(service_account.tenant_id):
        # Allow superusers to access any service account
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to service accounts from other tenants is not allowed"
            )
            
    return service_account

async def get_agent_from_path(
    agent_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Agent:
    """
    Get agent from path parameter and verify access.
    
    Args:
        agent_id: Agent ID from path
        db: Database session
        current_user: Current user
        
    Returns:
        Agent: Agent object
        
    Raises:
        HTTPException: If agent not found or user doesn't have access
    """
    # Get agent
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
        
    # Check if user has access to agent's tenant
    if str(current_user.tenant_id) != str(agent.tenant_id):
        # Allow superusers to access any agent
        has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
        if not has_superuser_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to agents from other tenants is not allowed"
            )
            
    return agent

def get_multi_tenant_filter(user: User = Depends(get_current_active_user)):
    """
    Get filter for multi-tenant queries based on user.
    
    Args:
        user: Current user
        
    Returns:
        dict: Filter dictionary for multi-tenant queries
    """
    # Check if user has superuser role
    has_superuser_role = any(role.name == "superuser" for role in user.roles)
    
    # If superuser, allow access to all tenants
    if has_superuser_role:
        return {}
    else:
        # Otherwise, restrict to user's tenant
        return {"tenant_id": user.tenant_id}

class GetDB:
    """Dependency for getting database session with optional transaction"""
    
    def __init__(self, autocommit: bool = False):
        """
        Initialize the dependency.
        
        Args:
            autocommit: Whether to automatically commit the session
        """
        self.autocommit = autocommit
    
    def __call__(self) -> Generator[Session, None, None]:
        """
        Get database session.
        
        Returns:
            Generator[Session, None, None]: Database session
        """
        db = SessionLocal()
        try:
            yield db
            if self.autocommit:
                db.commit()
        finally:
            db.close()

# Common dependencies
get_db_transactional = GetDB(autocommit=True)