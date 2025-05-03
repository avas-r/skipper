"""
Schedule model for job scheduling.

This module defines the Schedule model for automating job execution
based on time schedules.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from ..db.session import Base

class Schedule(Base):
    """
    Schedule model for job scheduling.
    
    Schedules define when jobs should be automatically executed using cron expressions
    or other scheduling patterns.
    """
    
    __tablename__ = "schedules"
    
    # Primary key
    schedule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant", backref="schedules")
    
    # Schedule information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Schedule definition
    cron_expression = Column(String(100), nullable=False)
    timezone = Column(String(50), nullable=False, default="UTC")
    
    # Schedule validity period
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="active")
    
    # Execution tracking
    last_execution = Column(DateTime, nullable=True)
    next_execution = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    jobs = relationship("Job", back_populates="schedule")
    
    # Unique constraint for tenant + name
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_schedule_tenant_name"),
    )
    
    def __repr__(self):
        """String representation of the schedule"""
        return f"<Schedule {self.name} ({self.schedule_id})>"