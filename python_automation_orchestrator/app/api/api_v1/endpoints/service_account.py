from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.schemas import ServiceAccountCreate, ServiceAccountUpdate, ServiceAccountResponse
from app.services.service_account_service import ServiceAccountService
from app.db.session import get_db
from app.auth.auth import get_current_active_user, verify_permissions

router = APIRouter(prefix="/api/v1/service-accounts", tags=["service-accounts"])

@router.post("/", response_model=ServiceAccountResponse)
async def create_service_account(
    service_account: ServiceAccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Verify permissions
    verify_permissions(current_user, "service_accounts", "create")
    
    # Create service using dependency injection
    service = ServiceAccountService(db)
    
    try:
        result = service.create_service_account(
            service_account, current_user.tenant_id, current_user.user_id
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{account_id}", response_model=ServiceAccountResponse)
async def get_service_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Verify permissions
    verify_permissions(current_user, "service_accounts", "read")
    
    # Get service using dependency injection
    service = ServiceAccountService(db)
    
    result = service.get_service_account(account_id, current_user.tenant_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
        
    return result

@router.put("/{account_id}", response_model=ServiceAccountResponse)
async def update_service_account(
    account_id: uuid.UUID,
    service_account: ServiceAccountUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Verify permissions
    verify_permissions(current_user, "service_accounts", "update")
    
    # Get service using dependency injection
    service = ServiceAccountService(db)
    
    result = service.update_service_account(
        account_id, service_account, current_user.tenant_id, current_user.user_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )
        
    return result

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service_account(
    account_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    # Verify permissions
    verify_permissions(current_user, "service_accounts", "delete")
    
    # Get service using dependency injection
    service = ServiceAccountService(db)
    
    result = service.delete_service_account(account_id, current_user.tenant_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service account not found"
        )