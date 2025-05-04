"""
Queue schemas for the orchestrator API.

This module defines Pydantic models for queue-related API requests and responses.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator

class QueueBase(BaseModel):
    """Base schema for queue data"""
    name: str
    description: Optional[str] = None
    max_retries: Optional[int] = 3
    retry_delay_seconds: Optional[int] = 60
    priority: Optional[int] = 1
    settings: Optional[Dict[str, Any]] = None

class QueueCreate(QueueBase):
    """Schema for creating a new queue"""
    pass

class QueueUpdate(BaseModel):
    """Schema for updating a queue"""
    name: Optional[str] = None
    description: Optional[str] = None
    max_retries: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    priority: Optional[int] = None
    status: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class QueueInDBBase(QueueBase):
    """Base schema for queue in database"""
    queue_id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class QueueResponse(QueueInDBBase):
    """Schema for queue response"""
    pass

class QueueItemBase(BaseModel):
    """Base schema for queue item data"""
    priority: Optional[int] = None
    reference_id: Optional[str] = None
    payload: Dict[str, Any]
    due_date: Optional[datetime] = None

class QueueItemCreate(QueueItemBase):
    """Schema for creating a new queue item"""
    pass

class QueueItemUpdate(BaseModel):
    """Schema for updating a queue item"""
    priority: Optional[int] = None
    status: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    due_date: Optional[datetime] = None
    
    @validator("status")
    def validate_status(cls, v):
        """Validate status"""
        valid_statuses = ["pending", "processing", "completed", "failed", "cancelled"]
        if v and v not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return v

class QueueItemInDBBase(QueueItemBase):
    """Base schema for queue item in database"""
    item_id: uuid.UUID
    queue_id: uuid.UUID
    tenant_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
    retry_count: int = 0
    next_processing_time: Optional[datetime] = None
    error_message: Optional[str] = None
    assigned_to: Optional[uuid.UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class QueueItemResponse(QueueItemInDBBase):
    """Schema for queue item response"""
    pass

class QueueStats(BaseModel):
    """Schema for queue statistics"""
    queue_id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    total_items: int
    pending_items: int
    processing_items: int
    completed_items: int
    failed_items: int
    cancelled_items: int
    average_processing_time_ms: Optional[float] = None
    oldest_pending_item: Optional[datetime] = None
    newest_pending_item: Optional[datetime] = None

class QueueBulkOperationRequest(BaseModel):
    """Schema for bulk queue operation request"""
    item_ids: List[uuid.UUID] = Field(..., min_items=1)
    operation: str = Field(..., description="Operation to perform (cancel, retry, delete)")
    
    @validator("operation")
    def validate_operation(cls, v):
        """Validate operation"""
        valid_operations = ["cancel", "retry", "delete"]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation. Must be one of: {', '.join(valid_operations)}")
        return v

class QueueBulkOperationResponse(BaseModel):
    """Schema for bulk queue operation response"""
    success_count: int
    failure_count: int
    errors: Optional[Dict[str, str]] = None