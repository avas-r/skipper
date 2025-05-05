"""
Tenant model for multi-tenancy support.

This module defines the Tenant model for managing multi-tenancy
in the orchestration system.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, UUID, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..db.session import Base

class Tenant(Base):
    """
    Tenant model for multi-tenancy support.
    
    A tenant represents a distinct organizational entity within the system.
    Each tenant has its own resources, users, and configuration.
    """
    
    __tablename__ = "tenants"
    
    # Primary key
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant information
    name = Column(String(255), nullable=False)
    service_accounts = relationship("ServiceAccount", back_populates="tenant", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    agent_sessions = relationship("AgentSession", back_populates="tenant", cascade="all, delete-orphan")
    agent_sessions = relationship("AgentSession", back_populates="tenant", cascade="all, delete-orphan")
    
    # Status and basic subscription info
    status = Column(String(20), nullable=False, default="active")
    subscription_tier = Column(String(20), nullable=False, default="standard")  # Legacy field, kept for backwards compatibility
    
    # Resource limits - these are now managed through the subscription system
    # but kept here for backwards compatibility and quick access
    max_concurrent_jobs = Column(Integer, nullable=False, default=50)
    max_agents = Column(Integer, nullable=False, default=10)
    
    # Subscription relationship
    subscription = relationship("TenantSubscription", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    
    # Additional settings as JSON
    settings = Column(JSON, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        """String representation of the tenant"""
        return f"<Tenant {self.name} ({self.tenant_id})>"