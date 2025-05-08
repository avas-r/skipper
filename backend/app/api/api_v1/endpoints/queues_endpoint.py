"""
Queue management endpoints for the orchestrator API.

This module provides endpoints for managing job queues and queue items.
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Queue, QueueItem
from ....schemas.queue import (
    QueueCreate, 
    QueueUpdate, 
    QueueResponse,
    QueueItemCreate,
    QueueItemUpdate,
    QueueItemResponse,
    QueueStats
)
from ....services.queue_service import QueueService
from ..dependencies import get_tenant_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_queue_read = PermissionChecker(["queue:read"])
require_queue_create = PermissionChecker(["queue:create"])
require_queue_update = PermissionChecker(["queue:update"])
require_queue_delete = PermissionChecker(["queue:delete"])

@router.get("/", response_model=List[QueueResponse])
def list_queues(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all queues with optional filtering.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # List queues
    queues = queue_service.list_queues(
        tenant_id=str(current_user.tenant_id),
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return queues

@router.post("/", response_model=QueueResponse)
def create_queue(
    queue_in: QueueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_create)
) -> Any:
    """
    Create a new queue.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Create queue
    queue = queue_service.create_queue(
        queue_in=queue_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    return queue

@router.get("/{queue_id}", response_model=QueueResponse)
def get_queue(
    queue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_read)
) -> Any:
    """
    Get a queue by ID.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Get queue
    queue = queue_service.get_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    return queue

@router.put("/{queue_id}", response_model=QueueResponse)
def update_queue(
    queue_id: str,
    queue_in: QueueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_update)
) -> Any:
    """
    Update a queue.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Update queue
    queue = queue_service.update_queue(
        queue_id=queue_id,
        queue_in=queue_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    return queue

@router.delete("/{queue_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_queue(
    queue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_delete)
) -> None:
    """
    Delete a queue.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Check if queue exists
    queue = queue_service.get_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    # Delete queue
    deleted = queue_service.delete_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete queue {queue_id}"
        )

@router.get("/{queue_id}/stats", response_model=QueueStats)
def get_queue_stats(
    queue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_read)
) -> Any:
    """
    Get queue statistics.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Get queue
    queue = queue_service.get_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    # Get stats
    stats = queue_service.get_queue_stats(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    return stats

@router.get("/{queue_id}/items", response_model=List[QueueItemResponse])
def list_queue_items(
    queue_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> Any:
    """
    List items in a queue with optional filtering.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Check if queue exists
    queue = queue_service.get_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    # List queue items
    items = queue_service.list_queue_items(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id),
        status=status,
        skip=skip,
        limit=limit
    )
    
    return items

@router.post("/{queue_id}/items", response_model=QueueItemResponse)
def add_queue_item(
    queue_id: str,
    item_in: QueueItemCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_update)
) -> Any:
    """
    Add an item to a queue.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Check if queue exists
    queue = queue_service.get_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    # Add item to queue
    item = queue_service.add_queue_item(
        queue_id=queue_id,
        item_in=item_in,
        tenant_id=str(current_user.tenant_id),
        background_tasks=background_tasks
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add item to queue {queue_id}"
        )
    
    return item

@router.get("/{queue_id}/items/{item_id}", response_model=QueueItemResponse)
def get_queue_item(
    queue_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_read)
) -> Any:
    """
    Get a queue item by ID.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Get queue item
    item = queue_service.get_queue_item(
        queue_id=queue_id,
        item_id=item_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue item {item_id} not found"
        )
    
    return item

@router.put("/{queue_id}/items/{item_id}", response_model=QueueItemResponse)
def update_queue_item(
    queue_id: str,
    item_id: str,
    item_in: QueueItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_update)
) -> Any:
    """
    Update a queue item.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Update queue item
    item = queue_service.update_queue_item(
        queue_id=queue_id,
        item_id=item_id,
        item_in=item_in,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue item {item_id} not found"
        )
    
    return item

@router.delete("/{queue_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_queue_item(
    queue_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_update)
) -> None:
    """
    Delete a queue item.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Delete queue item
    deleted = queue_service.delete_queue_item(
        queue_id=queue_id,
        item_id=item_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue item {item_id} not found"
        )

@router.post("/{queue_id}/items/{item_id}/retry", response_model=QueueItemResponse)
def retry_queue_item(
    queue_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_update)
) -> Any:
    """
    Retry a failed queue item.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Retry queue item
    item = queue_service.retry_queue_item(
        queue_id=queue_id,
        item_id=item_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue item {item_id} not found or cannot be retried"
        )
    
    return item

@router.post("/{queue_id}/clear", status_code=status.HTTP_204_NO_CONTENT)
def clear_queue(
    queue_id: str,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_queue_delete)
) -> None:
    """
    Clear all items from a queue.
    """
    # Create queue service
    queue_service = QueueService(db)
    
    # Check if queue exists
    queue = queue_service.get_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not queue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Queue {queue_id} not found"
        )
    
    # Clear queue
    queue_service.clear_queue(
        queue_id=queue_id,
        tenant_id=str(current_user.tenant_id),
        status=status_filter
    )