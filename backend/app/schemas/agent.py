"""
Agent schemas for the orchestrator API.

This module defines Pydantic models for agent-related API requests and responses.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator

class AgentBase(BaseModel):
    """Base schema for agent data"""
    name: str
    machine_id: str
    ip_address: Optional[str] = None
    status: Optional[str] = "offline"
    capabilities: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

class AgentCreate(AgentBase):
    """Schema for creating a new agent"""
    name: str
    machine_id: str
    hostname: Optional[str] = None  # Ensure this is included
    tenant_id: Optional[uuid.UUID] = None
    version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    name: Optional[str] = None
    status: Optional[str] = None
    ip_address: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    service_account_id: Optional[uuid.UUID] = None
    auto_login_enabled: Optional[bool] = None
    session_type: Optional[str] = None

class AgentInDBBase(AgentBase):
    """Base schema for agent in database"""
    agent_id: uuid.UUID
    tenant_id: uuid.UUID
    version: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_heartbeat: Optional[datetime] = None
    service_account_id: Optional[uuid.UUID] = None
    auto_login_enabled: Optional[bool] = False
    session_type: Optional[str] = None
    session_status: Optional[str] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class AgentResponse(BaseModel):
    """Schema for agent response."""
    agent_id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    machine_id: str
    hostname: Optional[str] = None  # Make sure hostname is included
    ip_address: Optional[str] = None
    status: str
    last_heartbeat: Optional[datetime] = None
    version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    auto_login_enabled: Optional[bool] = None
    session_type: Optional[str] = None
    #service_account: Optional[ServiceAccountResponse] = None

    class Config:
        """Pydantic config."""
        orm_mode = True

class AgentLogBase(BaseModel):
    """Base schema for agent log data"""
    log_level: str
    message: str
    metadata: Optional[Dict[str, Any]] = None

class AgentLogCreate(AgentLogBase):
    """Schema for creating a new agent log"""
    agent_id: uuid.UUID
    tenant_id: uuid.UUID

class AgentLogResponse(AgentLogBase):
    """Schema for agent log response"""
    log_id: uuid.UUID
    agent_id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class AgentCommandRequest(BaseModel):
    """Schema for agent command request"""
    command_type: str = Field(..., description="Type of command to send to the agent")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Command parameters")
    
    @validator("command_type")
    def validate_command_type(cls, v):
        """Validate command type"""
        valid_commands = ["stop", "restart", "update_config", "clean_packages", "execute_job"]
        if v not in valid_commands:
            raise ValueError(f"Invalid command type. Must be one of: {', '.join(valid_commands)}")
        return v

class AgentHeartbeatRequest(BaseModel):
    """Schema for agent heartbeat request"""
    status: str = "online"
    metrics: Dict[str, Any] = {}
    jobs: Optional[Dict[str, Any]] = None

class AgentHeartbeatResponse(BaseModel):
    """Schema for agent heartbeat response"""
    commands: List[Dict[str, Any]] = []
    server_time: datetime = Field(default_factory=datetime.utcnow)