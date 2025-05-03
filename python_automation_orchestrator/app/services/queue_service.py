"""
Queue service for managing job queues and queue items.

This module provides services for managing queues, queue items,
and queue operations.
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc

from ..models import Queue, QueueItem, AuditLog
from ..schemas.queue import QueueCreate, QueueUpdate, QueueItemCreate, QueueItemUpdate, QueueStats
from ..messaging.producer import get_message_producer

logger = logging.getLogger(__name__)

class QueueService:
    """Service for managing queues and queue items"""
    
    def __init__(self, db: Session):
        """
        Initialize the queue service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def create_queue(self, queue_in: QueueCreate, tenant_id: str, user_id: str) -> Queue:
        """
        Create a new queue.
        
        Args:
            queue_in: Queue data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Queue: Created queue
            
        Raises:
            ValueError: If queue with same name exists
        """
        # Check if queue with same name exists
        existing = self.db.query(Queue).filter(
            Queue.tenant_id == tenant_id,
            Queue.name == queue_in.name
        ).first()
        
        if existing:
            raise ValueError(f"Queue with name '{queue_in.name}' already exists")
        
        # Create queue
        db_queue = Queue(
            queue_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=queue_in.name,
            description=queue_in.description,
            max_retries=queue_in.max_retries,
            retry_delay_seconds=queue_in.retry_delay_seconds,
            priority=queue_in.priority,
            settings=queue_in.settings,
            status="active",
            created_by=user_id
        )
        
        self.db.add(db_queue)
        self.db.commit()
        self.db.refresh(db_queue)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_queue",
            entity_type="queue",
            entity_id=db_queue.queue_id,
            details={
                "name": db_queue.name
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return db_queue
    
    def update_queue(self, queue_id: str, queue_in: QueueUpdate, tenant_id: str, user_id: str) -> Optional[Queue]:
        """
        Update a queue.
        
        Args:
            queue_id: Queue ID
            queue_in: Queue update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Optional[Queue]: Updated queue or None if not found
            
        Raises:
            ValueError: If queue not found
        """
        # Get queue
        queue = self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
        
        if not queue:
            return None
        
        # Update fields
        update_data = queue_in.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(queue, key, value)
            
        # Update audit fields
        queue.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(queue)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_queue",
            entity_type="queue",
            entity_id=queue.queue_id,
            details=update_data
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return queue
    
    def delete_queue(self, queue_id: str, tenant_id: str) -> bool:
        """
        Delete a queue.
        
        Args:
            queue_id: Queue ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ValueError: If queue not found or has active items
        """
        # Get queue
        queue = self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
        
        if not queue:
            return False
        
        # Check if queue has active items
        active_items = self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status.in_(["pending", "processing"])
        ).count()
        
        if active_items > 0:
            raise ValueError(f"Cannot delete queue with {active_items} active items")
        
        # Delete queue items
        self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id
        ).delete()
        
        # Delete queue
        self.db.delete(queue)
        self.db.commit()
        
        return True
    
    def get_queue(self, queue_id: str, tenant_id: str) -> Optional[Queue]:
        """
        Get a queue by ID.
        
        Args:
            queue_id: Queue ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Queue]: Queue or None if not found
        """
        return self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
    
    def list_queues(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Queue]:
        """
        List queues with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Queue]: List of queues
        """
        # Build base query
        query = self.db.query(Queue).filter(Queue.tenant_id == tenant_id)
        
        # Apply filters
        if status:
            query = query.filter(Queue.status == status)
            
        if search:
            query = query.filter(
                or_(
                    Queue.name.ilike(f"%{search}%"),
                    Queue.description.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        query = query.order_by(Queue.name).offset(skip).limit(limit)
        
        return query.all()
    
    def get_queue_stats(self, queue_id: str, tenant_id: str) -> QueueStats:
        """
        Get queue statistics.
        
        Args:
            queue_id: Queue ID
            tenant_id: Tenant ID
            
        Returns:
            QueueStats: Queue statistics
            
        Raises:
            ValueError: If queue not found
        """
        # Get queue
        queue = self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
        
        if not queue:
            raise ValueError(f"Queue not found: {queue_id}")
        
        # Count items by status
        total_items = self.db.query(func.count(QueueItem.item_id)).filter(
            QueueItem.queue_id == queue_id
        ).scalar()
        
        pending_items = self.db.query(func.count(QueueItem.item_id)).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "pending"
        ).scalar()
        
        processing_items = self.db.query(func.count(QueueItem.item_id)).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "processing"
        ).scalar()
        
        completed_items = self.db.query(func.count(QueueItem.item_id)).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "completed"
        ).scalar()
        
        failed_items = self.db.query(func.count(QueueItem.item_id)).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "failed"
        ).scalar()
        
        cancelled_items = self.db.query(func.count(QueueItem.item_id)).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "cancelled"
        ).scalar()
        
        # Calculate average processing time
        avg_processing_time = self.db.query(func.avg(QueueItem.processing_time_ms)).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.processing_time_ms.isnot(None)
        ).scalar()
        
        # Get oldest and newest pending items
        oldest_pending = self.db.query(QueueItem.created_at).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "pending"
        ).order_by(QueueItem.created_at).first()
        
        newest_pending = self.db.query(QueueItem.created_at).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.status == "pending"
        ).order_by(desc(QueueItem.created_at)).first()
        
        # Create stats object
        stats = QueueStats(
            queue_id=queue.queue_id,
            tenant_id=queue.tenant_id,
            name=queue.name,
            total_items=total_items or 0,
            pending_items=pending_items or 0,
            processing_items=processing_items or 0,
            completed_items=completed_items or 0,
            failed_items=failed_items or 0,
            cancelled_items=cancelled_items or 0,
            average_processing_time_ms=float(avg_processing_time) if avg_processing_time else None,
            oldest_pending_item=oldest_pending[0] if oldest_pending else None,
            newest_pending_item=newest_pending[0] if newest_pending else None
        )
        
        return stats
    
    def add_queue_item(
        self,
        queue_id: str,
        item_in: QueueItemCreate,
        tenant_id: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Optional[QueueItem]:
        """
        Add an item to a queue.
        
        Args:
            queue_id: Queue ID
            item_in: Queue item data
            tenant_id: Tenant ID
            background_tasks: Optional FastAPI background tasks
            
        Returns:
            Optional[QueueItem]: Added queue item or None if failed
            
        Raises:
            ValueError: If queue not found
        """
        # Get queue
        queue = self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
        
        if not queue:
            raise ValueError(f"Queue not found: {queue_id}")
        
        # Create queue item
        db_item = QueueItem(
            item_id=uuid.uuid4(),
            queue_id=queue_id,
            tenant_id=tenant_id,
            status="pending",
            priority=item_in.priority or queue.priority,
            reference_id=item_in.reference_id,
            payload=item_in.payload,
            due_date=item_in.due_date,
            retry_count=0
        )
        
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        
        # Send message to broker for processing
        if background_tasks:
            # Get message producer
            message_producer = get_message_producer()
            
            # Add task to send message
            background_tasks.add_task(
                message_producer.send_message,
                "jobs",
                "queue.item.new",
                {
                    "action": "new_item",
                    "queue_id": queue_id,
                    "item_id": str(db_item.item_id),
                    "tenant_id": tenant_id,
                    "priority": db_item.priority
                }
            )
        
        return db_item
    
    def get_queue_item(self, queue_id: str, item_id: str, tenant_id: str) -> Optional[QueueItem]:
        """
        Get a queue item by ID.
        
        Args:
            queue_id: Queue ID
            item_id: Item ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[QueueItem]: Queue item or None if not found
        """
        return self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.item_id == item_id,
            QueueItem.tenant_id == tenant_id
        ).first()
    
    def list_queue_items(
        self,
        queue_id: str,
        tenant_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[QueueItem]:
        """
        List items in a queue with filtering.
        
        Args:
            queue_id: Queue ID
            tenant_id: Tenant ID
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[QueueItem]: List of queue items
        """
        # Build base query
        query = self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.tenant_id == tenant_id
        )
        
        # Apply status filter
        if status:
            query = query.filter(QueueItem.status == status)
        
        # Apply pagination and sort by priority and creation time
        query = query.order_by(
            desc(QueueItem.priority),
            QueueItem.created_at
        ).offset(skip).limit(limit)
        
        return query.all()
    
    def update_queue_item(
        self,
        queue_id: str,
        item_id: str,
        item_in: QueueItemUpdate,
        tenant_id: str
    ) -> Optional[QueueItem]:
        """
        Update a queue item.
        
        Args:
            queue_id: Queue ID
            item_id: Item ID
            item_in: Queue item update data
            tenant_id: Tenant ID
            
        Returns:
            Optional[QueueItem]: Updated queue item or None if not found
            
        Raises:
            ValueError: If item not found or invalid status transition
        """
        # Get queue item
        item = self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.item_id == item_id,
            QueueItem.tenant_id == tenant_id
        ).first()
        
        if not item:
            return None
        
        # Check status transition
        if item_in.status and item_in.status != item.status:
            # Validate status transition
            if item.status == "completed" and item_in.status != "completed":
                raise ValueError(f"Cannot change status from 'completed' to '{item_in.status}'")
            
            if item.status == "cancelled" and item_in.status != "cancelled":
                raise ValueError(f"Cannot change status from 'cancelled' to '{item_in.status}'")
            
            # Update status-related fields
            if item_in.status == "completed" and not item.processed_at:
                item.processed_at = datetime.utcnow()
                
                # Calculate processing time if started
                if item.status == "processing":
                    # Calculate time since status change
                    processing_time = (datetime.utcnow() - item.updated_at).total_seconds() * 1000
                    item.processing_time_ms = int(processing_time)
        
        # Update fields
        update_data = item_in.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(item, key, value)
            
        # Update timestamp
        item.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(item)
        
        return item
    
    def delete_queue_item(self, queue_id: str, item_id: str, tenant_id: str) -> bool:
        """
        Delete a queue item.
        
        Args:
            queue_id: Queue ID
            item_id: Item ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ValueError: If item not found or in processing state
        """
        # Get queue item
        item = self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.item_id == item_id,
            QueueItem.tenant_id == tenant_id
        ).first()
        
        if not item:
            return False
        
        # Check if item is in processing state
        if item.status == "processing":
            raise ValueError("Cannot delete queue item in 'processing' state")
        
        # Delete item
        self.db.delete(item)
        self.db.commit()
        
        return True
    
    def retry_queue_item(self, queue_id: str, item_id: str, tenant_id: str) -> Optional[QueueItem]:
        """
        Retry a failed queue item.
        
        Args:
            queue_id: Queue ID
            item_id: Item ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[QueueItem]: Updated queue item or None if not found or cannot be retried
            
        Raises:
            ValueError: If item not found or cannot be retried
        """
        # Get queue item
        item = self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.item_id == item_id,
            QueueItem.tenant_id == tenant_id
        ).first()
        
        if not item:
            return None
        
        # Check if item can be retried
        if item.status != "failed":
            raise ValueError(f"Cannot retry item with status '{item.status}'")
        
        # Get queue for retry settings
        queue = self.db.query(Queue).filter(Queue.queue_id == queue_id).first()
        
        if not queue:
            raise ValueError(f"Queue not found: {queue_id}")
        
        # Check max retries
        if item.retry_count >= queue.max_retries:
            raise ValueError(f"Maximum retry count ({queue.max_retries}) exceeded")
        
        # Update item for retry
        item.status = "pending"
        item.retry_count += 1
        item.error_message = None
        item.assigned_to = None
        item.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(item)
        
        return item
    
    def clear_queue(self, queue_id: str, tenant_id: str, status: Optional[str] = None) -> int:
        """
        Clear all items from a queue.
        
        Args:
            queue_id: Queue ID
            tenant_id: Tenant ID
            status: Optional status filter
            
        Returns:
            int: Number of items deleted
            
        Raises:
            ValueError: If queue not found
        """
        # Get queue
        queue = self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
        
        if not queue:
            raise ValueError(f"Queue not found: {queue_id}")
        
        # Build delete query
        query = self.db.query(QueueItem).filter(
            QueueItem.queue_id == queue_id,
            QueueItem.tenant_id == tenant_id
        )
        
        # Apply status filter
        if status:
            query = query.filter(QueueItem.status == status)
        else:
            # Never delete processing items
            query = query.filter(QueueItem.status != "processing")
        
        # Delete items
        count = query.delete(synchronize_session=False)
        self.db.commit()
        
        return count
    
    def update_queue_item_status(
        self,
        item_id: str,
        tenant_id: str,
        status: str,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> Optional[QueueItem]:
        """
        Update queue item status after processing.
        
        Args:
            item_id: Item ID
            tenant_id: Tenant ID
            status: New status
            error_message: Optional error message
            processing_time_ms: Optional processing time in milliseconds
            results: Optional processing results
            
        Returns:
            Optional[QueueItem]: Updated queue item or None if not found
            
        Raises:
            ValueError: If item not found
        """
        # Get queue item
        item = self.db.query(QueueItem).filter(
            QueueItem.item_id == item_id,
            QueueItem.tenant_id == tenant_id
        ).first()
        
        if not item:
            return None
        
        # Get queue for retry settings
        queue = self.db.query(Queue).filter(Queue.queue_id == item.queue_id).first()
        
        if not queue:
            raise ValueError(f"Queue not found: {item.queue_id}")
        
        # Update status
        item.status = status
        item.updated_at = datetime.utcnow()
        
        if status == "completed":
            # Mark as processed
            item.processed_at = datetime.utcnow()
            
            # Set processing time if provided
            if processing_time_ms is not None:
                item.processing_time_ms = processing_time_ms
            
            # Clear agent assignment
            item.assigned_to = None
            
            # Store results in payload
            if results:
                item.payload = {
                    **item.payload,
                    "results": results
                }
                
        elif status == "failed":
            # Set error message
            item.error_message = error_message
            
            # Check if should retry
            if item.retry_count < queue.max_retries:
                # Calculate next retry time with exponential backoff
                retry_delay = queue.retry_delay_seconds * (2 ** item.retry_count)
                item.next_processing_time = datetime.utcnow() + timedelta(seconds=retry_delay)
                
                # Increment retry count
                item.retry_count += 1
                
                # Reset status to pending
                item.status = "pending"
                
                # Clear agent assignment
                item.assigned_to = None
                
        elif status == "cancelled":
            # Clear agent assignment
            item.assigned_to = None
        
        self.db.commit()
        self.db.refresh(item)
        
        return item
    
    def get_next_queue_items(
        self,
        tenant_id: str,
        agent_id: str,
        max_items: int = 1,
        capabilities: Optional[List[str]] = None
    ) -> List[QueueItem]:
        """
        Get next items from queues for processing.
        
        Args:
            tenant_id: Tenant ID
            agent_id: Agent ID
            max_items: Maximum number of items to return
            capabilities: Optional list of agent capabilities
            
        Returns:
            List[QueueItem]: List of queue items
        """
        # Get current time
        now = datetime.utcnow()
        
        # Build query for pending items
        query = self.db.query(QueueItem).filter(
            QueueItem.tenant_id == tenant_id,
            QueueItem.status == "pending",
            QueueItem.assigned_to.is_(None),
            or_(
                QueueItem.next_processing_time.is_(None),
                QueueItem.next_processing_time <= now
            ),
            or_(
                QueueItem.due_date.is_(None),
                QueueItem.due_date >= now
            )
        )
        
        # Join with queue to get active queues
        query = query.join(Queue, QueueItem.queue_id == Queue.queue_id).filter(
            Queue.status == "active"
        )
        
        # Order by priority and creation time
        query = query.order_by(
            desc(QueueItem.priority),
            QueueItem.created_at
        ).limit(max_items)
        
        # Get items
        items = query.all()
        
        # Assign items to agent
        for item in items:
            item.status = "processing"
            item.assigned_to = agent_id
            item.updated_at = now
        
        self.db.commit()
        
        # Refresh items
        for i in range(len(items)):
            self.db.refresh(items[i])
        
        return items
    
    def bulk_operation(
        self,
        queue_id: str,
        tenant_id: str,
        item_ids: List[str],
        operation: str
    ) -> Dict[str, Any]:
        """
        Perform bulk operation on queue items.
        
        Args:
            queue_id: Queue ID
            tenant_id: Tenant ID
            item_ids: List of item IDs
            operation: Operation to perform (cancel, retry, delete)
            
        Returns:
            Dict[str, Any]: Operation results
            
        Raises:
            ValueError: If queue not found
        """
        # Get queue
        queue = self.db.query(Queue).filter(
            Queue.queue_id == queue_id,
            Queue.tenant_id == tenant_id
        ).first()
        
        if not queue:
            raise ValueError(f"Queue not found: {queue_id}")
        
        # Initialize counters and errors
        success_count = 0
        failure_count = 0
        errors = {}
        
        # Process each item
        for item_id in item_ids:
            try:
                if operation == "cancel":
                    # Cancel item
                    item = self.db.query(QueueItem).filter(
                        QueueItem.queue_id == queue_id,
                        QueueItem.item_id == item_id,
                        QueueItem.tenant_id == tenant_id,
                        QueueItem.status.in_(["pending", "processing"])
                    ).first()
                    
                    if item:
                        item.status = "cancelled"
                        item.updated_at = datetime.utcnow()
                        item.assigned_to = None
                        success_count += 1
                    else:
                        errors[item_id] = "Item not found or cannot be cancelled"
                        failure_count += 1
                
                elif operation == "retry":
                    # Retry item
                    try:
                        retried_item = self.retry_queue_item(queue_id, item_id, tenant_id)
                        if retried_item:
                            success_count += 1
                        else:
                            errors[item_id] = "Item not found or cannot be retried"
                            failure_count += 1
                    except ValueError as e:
                        errors[item_id] = str(e)
                        failure_count += 1
                
                elif operation == "delete":
                    # Delete item
                    try:
                        deleted = self.delete_queue_item(queue_id, item_id, tenant_id)
                        if deleted:
                            success_count += 1
                        else:
                            errors[item_id] = "Item not found or cannot be deleted"
                            failure_count += 1
                    except ValueError as e:
                        errors[item_id] = str(e)
                        failure_count += 1
                
                else:
                    errors[item_id] = f"Invalid operation: {operation}"
                    failure_count += 1
            
            except Exception as e:
                errors[item_id] = str(e)
                failure_count += 1
        
        # Commit changes
        self.db.commit()
        
        return {
            "success_count": success_count,
            "failure_count": failure_count,
            "errors": errors if errors else None
        }