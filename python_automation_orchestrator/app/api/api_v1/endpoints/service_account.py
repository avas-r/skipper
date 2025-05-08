"""
Service account management endpoints for the orchestrator API.

This module provides endpoints for managing service accounts.
"""

import logging
import uuid
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

# Use absolute imports
from app.auth.jwt import get_current_active_user
from app.auth.permissions import PermissionChecker
from app.db.session import get_db
from app.models import User, ServiceAccount
from app.schemas.service_account import (
    ServiceAccountCreate, 
    ServiceAccountUpdate, 
    ServiceAccountResponse
)
from app.services.service_account_service import ServiceAccountService
from app.api.api_v1.dependencies import get_service_account_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_service_account_read = PermissionChecker(["service_account:read"])
require_service_account_create = PermissionChecker(["service_account:create"])
require_service_account_update = PermissionChecker(["service_account:update"])
require_service_account_delete = PermissionChecker(["service_account:delete"])

@router.get("/", response_model=List[ServiceAccountResponse])
def list_service_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_service_account_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all service accounts with optional filtering.
    """
    # Create service account service
    service_account_service = ServiceAccountService(db)
    
    # List service accounts for the current user's tenant
    result = service_account_service.list_service_accounts(
        tenant_id=str(current_user.tenant_id),
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return result

@router.post("/", response_model=ServiceAccountResponse)
def create_service_account(
    service_account_in: ServiceAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_service_account_create)
) -> Any:
    """
    Create a new service account.
    """
    # Create service account service
    service_account_service = ServiceAccountService(db)
    
    try:
        # Create service account
        service_account = service_account_service.create_service_account(
            service_account_in=service_account_in,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        return service_account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{service_account_id}", response_model=ServiceAccountResponse)
def get_service_account(
    service_account: ServiceAccount = Depends(get_service_account_from_path),
    _: bool = Depends(require_service_account_read)
) -> Any:
    """
    Get service account by ID.
    """
    return service_account

@router.put("/{service_account_id}", response_model=ServiceAccountResponse)
def update_service_account(
    service_account_in: ServiceAccountUpdate,
    service_account: ServiceAccount = Depends(get_service_account_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_service_account_update)
) -> Any:
    """
    Update a service account.
    """
    # Create service account service
    service_account_service = ServiceAccountService(db)
    
    try:
        # Update service account
        updated_service_account = service_account_service.update_service_account(
            service_account_id=str(service_account.account_id),
            service_account_in=service_account_in,
            tenant_id=str(service_account.tenant_id),
            user_id=str(current_user.user_id)
        )
        
        return updated_service_account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{service_account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service_account(
    service_account: ServiceAccount = Depends(get_service_account_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_service_account_delete)
) -> None:
    """
    Delete a service account.
    """
    # Create service account service
    service_account_service = ServiceAccountService(db)
    
    try:
        # Delete service account
        service_account_service.delete_service_account(
            service_account_id=str(service_account.account_id),
            tenant_id=str(service_account.tenant_id),
            user_id=str(current_user.user_id)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )