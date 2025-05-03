"""
Notification endpoints for the orchestrator API.

This module provides endpoints for managing notifications and notification rules.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Notification, NotificationRule, NotificationChannel, NotificationType
from ....schemas.notification import (
    NotificationResponse, 
    NotificationRuleCreate,
    NotificationRuleUpdate,
    NotificationRuleResponse,
    NotificationChannelCreate,
    NotificationChannelUpdate,
    NotificationChannelResponse
)
from ....services.notification_service import NotificationService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_notification_read = PermissionChecker(["notification:read"])
require_notification_create = PermissionChecker(["notification:create"])
require_notification_update = PermissionChecker(["notification:update"])
require_notification_delete = PermissionChecker(["notification:delete"])

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
    status: Optional[str] = None,
    reference_type: Optional[str] = None,
    reference_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List notifications with optional filtering.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # List notifications
    notifications, total = notification_service.list_notifications(
        tenant_id=current_user.tenant_id,
        status=status,
        reference_type=reference_type,
        reference_id=reference_id,
        skip=skip,
        limit=limit
    )
    
    return notifications

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
) -> Any:
    """
    Get notification by ID.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Get notification
    notification = notification_service.get_notification(
        notification_id=notification_id,
        tenant_id=current_user.tenant_id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification

@router.post("/{notification_id}/mark-read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_update),
) -> Any:
    """
    Mark a notification as read.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Mark notification as read
    notification = notification_service.mark_notification_read(
        notification_id=notification_id,
        tenant_id=current_user.tenant_id
    )
    
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return notification

@router.get("/types", response_model=List[Dict[str, Any]])
async def list_notification_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
) -> Any:
    """
    List available notification types.
    """
    # Query notification types
    types = db.query(NotificationType).all()
    
    return [{"id": str(t.type_id), "name": t.name, "description": t.description} for t in types]

@router.get("/rules", response_model=List[NotificationRuleResponse])
async def list_notification_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List notification rules.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # List rules
    rules, total = notification_service.list_notification_rules(
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )
    
    return rules

@router.post("/rules", response_model=NotificationRuleResponse)
async def create_notification_rule(
    rule_in: NotificationRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_create),
) -> Any:
    """
    Create a new notification rule.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    try:
        # Create rule
        rule = notification_service.create_notification_rule(
            rule_in=rule_in,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id
        )
        
        return rule
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def get_notification_rule(
    rule_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
) -> Any:
    """
    Get notification rule by ID.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Get rule
    rule = notification_service.get_notification_rule(
        rule_id=rule_id,
        tenant_id=current_user.tenant_id
    )
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification rule not found"
        )
    
    return rule

@router.put("/rules/{rule_id}", response_model=NotificationRuleResponse)
async def update_notification_rule(
    rule_id: uuid.UUID,
    rule_in: NotificationRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_update),
) -> Any:
    """
    Update a notification rule.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    try:
        # Update rule
        rule = notification_service.update_notification_rule(
            rule_id=rule_id,
            rule_in=rule_in,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id
        )
        
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification rule not found"
            )
        
        return rule
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_rule(
    rule_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_delete),
) -> None:
    """
    Delete a notification rule.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Delete rule
    result = notification_service.delete_notification_rule(
        rule_id=rule_id,
        tenant_id=current_user.tenant_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification rule not found"
        )

@router.get("/channels", response_model=List[NotificationChannelResponse])
async def list_notification_channels(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List notification channels.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # List channels
    channels, total = notification_service.list_notification_channels(
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )
    
    return channels

@router.post("/channels", response_model=NotificationChannelResponse)
async def create_notification_channel(
    channel_in: NotificationChannelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_create),
) -> Any:
    """
    Create a new notification channel.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    try:
        # Create channel
        channel = notification_service.create_notification_channel(
            channel_in=channel_in,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id
        )
        
        return channel
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/channels/{channel_id}", response_model=NotificationChannelResponse)
async def get_notification_channel(
    channel_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_read),
) -> Any:
    """
    Get notification channel by ID.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Get channel
    channel = notification_service.get_notification_channel(
        channel_id=channel_id,
        tenant_id=current_user.tenant_id
    )
    
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found"
        )
    
    return channel

@router.put("/channels/{channel_id}", response_model=NotificationChannelResponse)
async def update_notification_channel(
    channel_id: uuid.UUID,
    channel_in: NotificationChannelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_update),
) -> Any:
    """
    Update a notification channel.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    try:
        # Update channel
        channel = notification_service.update_notification_channel(
            channel_id=channel_id,
            channel_in=channel_in,
            tenant_id=current_user.tenant_id,
            user_id=current_user.user_id
        )
        
        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification channel not found"
            )
        
        return channel
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_channel(
    channel_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_delete),
) -> None:
    """
    Delete a notification channel.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Delete channel
    result = notification_service.delete_notification_channel(
        channel_id=channel_id,
        tenant_id=current_user.tenant_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found"
        )

@router.post("/channels/{channel_id}/test", status_code=status.HTTP_200_OK)
async def test_notification_channel(
    channel_id: uuid.UUID = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_notification_update),
) -> Dict[str, Any]:
    """
    Test a notification channel by sending a test notification.
    """
    # Create notification service
    notification_service = NotificationService(db)
    
    # Test channel
    result = notification_service.test_notification_channel(
        channel_id=channel_id,
        tenant_id=current_user.tenant_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification channel not found or test failed"
        )
    
    return {"success": True, "message": "Test notification sent successfully"}