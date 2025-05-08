"""
Queue model for job prioritization and transaction handling.

This module defines the Queue and QueueItem models for managing
job prioritization, queuing, and execution.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..db.session import Base

class Queue(Base):
    """
    Queue model for job prioritization.
    
    Queues are used to organize and prioritize jobs for execution.
    """
    
    __tablename__ = "queues"
    
    # Primary key
    queue_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="queues")
    
    # Queue information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Queue settings
    max_retries = Column(Integer, nullable=False, default=3)
    retry_delay_seconds = Column(Integer, nullable=False, default=60)
    priority = Column(Integer, nullable=False, default=1)
    
    # Status
    status = Column(String(20), nullable=False, default="active")
    
    # Additional settings
    settings = Column(JSON, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    creator = relationship("User", foreign_keys=[created_by])
    
    # Relationships
    items = relationship("QueueItem", back_populates="queue", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="queue")
    
    # Unique constraint for tenant + name
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_queue_tenant_name"),
    )
    
    def __repr__(self):
        """String representation of the queue"""
        return f"<Queue {self.name} ({self.queue_id})>"

class QueueItem(Base):
    """
    Queue item model.
    
    Queue items represent individual tasks in a queue awaiting execution.
    """
    
    __tablename__ = "queue_items"
    
    # Primary key
    item_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Queue foreign key
    queue_id = Column(UUID(as_uuid=True), ForeignKey("queues.queue_id"), nullable=False)
    queue = relationship("Queue", back_populates="items")
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant")
    
    # Item information
    status = Column(String(20), nullable=False, default="pending")
    priority = Column(Integer, nullable=False, default=1)
    reference_id = Column(String(255), nullable=True)
    
    # Payload (contains job-specific data)
    payload = Column(JSON, nullable=False)
    
    # Processing information
    processing_time_ms = Column(Integer, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    next_processing_time = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Agent assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True)
    agent = relationship("Agent")
    
    # Scheduling
    due_date = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # Relationships
    job_executions = relationship("JobExecution", back_populates="queue_item")
    
    def __repr__(self):
        """String representation of the queue item"""
        return f"<QueueItem {self.item_id} - {self.status}>"