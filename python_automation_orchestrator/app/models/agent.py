"""
Agent model for machine agent management.

This module defines the Agent and AgentLog models for managing
automation agents that run on client machines.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


from ..db.session import Base

class ServiceAccount(Base):
    """Model for service robot accounts"""
    __tablename__ = "service_accounts"
    
    account_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    username = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    description = Column(Text)
    account_type = Column(String(50), nullable=False, default="robot")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    last_used = Column(DateTime(timezone=True))
    configuration = Column(JSON)
    hashed_password = Column(String(255))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="service_accounts")
    creator = relationship("User", foreign_keys=[created_by])
    agents = relationship("Agent", back_populates="service_account")
    sessions = relationship("AgentSession", back_populates="service_account")

class AgentSession(Base):
    """Model for tracking agent sessions"""
    __tablename__ = "agent_sessions"
    
    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    service_account_id = Column(UUID(as_uuid=True), ForeignKey("service_accounts.account_id"))
    status = Column(String(50), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True))
    info = Column("metadata", JSON)
    
    # Relationships
    agent = relationship("Agent", back_populates="sessions")
    tenant = relationship("Tenant", back_populates="agent_sessions")
    service_account = relationship("ServiceAccount", back_populates="sessions")

class Agent(Base):
    """
    Agent model for machine agent management.
    
    Agents are client-side components that run on machines executing automations.
    They communicate with the orchestrator, execute jobs, and report status.
    """
    
    __tablename__ = "agents"
    
    # Primary key
    agent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    
    # Agent information
    name = Column(String(255), nullable=False)
    machine_id = Column(String(255), nullable=False)
    ip_address = Column(INET, nullable=True)
    
    # Status and version
    status = Column(String(20), nullable=False, default="offline")
    last_heartbeat = Column(DateTime, nullable=True)
    version = Column(String(50), nullable=True)
    
    # Capabilities and tags
    capabilities = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Additional settings
    settings = Column(JSON, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

        # Auto-login related fields
    service_account_id = Column(UUID(as_uuid=True), ForeignKey("service_accounts.account_id"))
    session_type = Column(String(50))
    auto_login_enabled = Column(Boolean, default=False)
    session_status = Column(String(50))
    
    # Relationships
    tenant = relationship("Tenant", back_populates="agents")
    job_executions = relationship("JobExecution", back_populates="agent")
    logs = relationship("AgentLog", back_populates="agent")
    service_account = relationship("ServiceAccount", back_populates="agents")
    sessions = relationship("AgentSession", back_populates="agent")
    
    # # Relationships
    # logs = relationship("AgentLog", back_populates="agent", cascade="all, delete-orphan")
    # job_executions = relationship("JobExecution", back_populates="agent")
    
    def __repr__(self):
        """String representation of the agent"""
        return f"<Agent {self.name} ({self.agent_id})>"

class AgentLog(Base):
    """
    Agent log model for tracking agent activities.
    
    Stores logs generated by agents, including heartbeats, status changes,
    and other events.
    """
    
    __tablename__ = "agent_logs"
    
    # Primary key
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Agent foreign key
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    agent = relationship("Agent", back_populates="logs")
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant")
    
    # Log information
    log_level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    
    # Additional metadata
    info = Column("metadata", JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        """String representation of the agent log"""
        return f"<AgentLog {self.log_id} - {self.agent_id}>"