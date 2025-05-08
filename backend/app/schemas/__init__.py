"""
Schemas package for the orchestrator application.

This package contains Pydantic models for API request and response schemas.
"""

# Import all schemas to make them available from the package
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserWithPermissions,
    RoleBase, RoleCreate, RoleUpdate, RoleResponse,
    PermissionBase, PermissionCreate, PermissionResponse
)
from .token import Token, TokenPayload
from .agent import (
    AgentBase, AgentCreate, AgentUpdate, AgentResponse,
    AgentLogBase, AgentLogCreate, AgentLogResponse,
    AgentCommandRequest, AgentHeartbeatRequest, AgentHeartbeatResponse
)

# Define exports for easier access
__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserWithPermissions",
    "RoleBase", "RoleCreate", "RoleUpdate", "RoleResponse",
    "PermissionBase", "PermissionCreate", "PermissionResponse",
    
    # Token schemas
    "Token", "TokenPayload",
    
    # Agent schemas
    "AgentBase", "AgentCreate", "AgentUpdate", "AgentResponse",
    "AgentLogBase", "AgentLogCreate", "AgentLogResponse",
    "AgentCommandRequest", "AgentHeartbeatRequest", "AgentHeartbeatResponse",
]