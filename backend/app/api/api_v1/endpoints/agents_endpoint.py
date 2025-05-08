"""
Agent management endpoints for the orchestrator API.

This module provides endpoints for managing automation agents.
"""

import logging
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Agent, AgentLog
from ....schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
    AgentLogResponse,
    AgentCommandRequest
)
from ....services.agent_service import AgentService
from ....services.agent_manager import AgentManager
from ..dependencies import get_agent_from_path

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_agent_read = PermissionChecker(["agent:read"])
require_agent_create = PermissionChecker(["agent:create"])
require_agent_update = PermissionChecker(["agent:update"])
require_agent_delete = PermissionChecker(["agent:delete"])

@router.get("/", response_model=List[AgentResponse])
def list_agents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all agents with optional filtering.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Determine tenant filter
    if tenant_id:
        # Check if user has access to tenant
        if str(current_user.tenant_id) != tenant_id:
            # Allow superusers to access any tenant
            has_superuser_role = any(role.name == "superuser" for role in current_user.roles)
            if not has_superuser_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access to agents from other tenants is not allowed"
                )
    else:
        # Default to user's tenant
        tenant_id = str(current_user.tenant_id)
        
    # List agents
    result = agent_service.list_agents(
        tenant_id=tenant_id,
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    agent_manager = AgentManager(db)
    
    # List agents
    result = agent_manager.get_agents(
        tenant_id=str(current_user.tenant_id),
        status=status,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return result

@router.post("/", response_model=AgentResponse)
def create_agent(
    agent_in: AgentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_create)
) -> Any:
    """
    Create a new agent.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Create agent
    agent = agent_service.create_agent(
        agent_in=agent_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    return agent

@router.get("/{agent_id}", response_model=AgentResponse)
def get_agent(
    agent: Agent = Depends(get_agent_from_path),
    _: bool = Depends(require_agent_read)
) -> Any:
    """
    Get agent by ID.
    """
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
def update_agent(
    agent_in: AgentUpdate,
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_update)
) -> Any:
    """
    Update an agent.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Update agent
    updated_agent = agent_service.update_agent(
        agent_id=str(agent.agent_id),
        agent_in=agent_in,
        tenant_id=str(agent.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    return updated_agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    _: bool = Depends(require_agent_delete)
) -> None:
    """
    Delete an agent.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Delete agent
    agent_service.delete_agent(
        agent_id=str(agent.agent_id),
        tenant_id=str(agent.tenant_id)
    )

@router.get("/{agent_id}/logs", response_model=List[AgentLogResponse])
def get_agent_logs(
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    _: bool = Depends(require_agent_read),
    skip: int = 0,
    limit: int = 100,
    log_level: Optional[str] = None
) -> Any:
    """
    Get agent logs.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Get agent logs
    logs = agent_service.get_agent_logs(
        agent_id=str(agent.agent_id),
        tenant_id=str(agent.tenant_id),
        log_level=log_level,
        skip=skip,
        limit=limit
    )
    
    return logs

@router.post("/{agent_id}/command", response_model=AgentResponse)
def send_agent_command(
    command: AgentCommandRequest,
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_update)
) -> Any:
    """
    Send a command to an agent.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Send command
    result = agent_service.send_agent_command(
        agent_id=str(agent.agent_id),
        tenant_id=str(agent.tenant_id),
        command_type=command.command_type,
        command_parameters=command.parameters,
        user_id=str(current_user.user_id)
    )
    
    return result

@router.post("/{agent_id}/auto-login/enable", response_model=AgentResponse)
def enable_agent_auto_login(
    agent: Agent = Depends(get_agent_from_path),
    service_account_id: str = Query(..., description="Service account ID to use for auto-login"),
    session_type: str = Query("windows", description="Type of session (windows, web, etc.)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_update)
) -> Any:
    """
    Enable auto-login for an agent with a specific service account.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Enable auto-login
    agent_update = AgentUpdate(
        service_account_id=service_account_id,
        auto_login_enabled=True,
        session_type=session_type
    )
    
    # Update agent
    updated_agent = agent_service.update_agent(
        agent_id=str(agent.agent_id),
        agent_in=agent_update,
        tenant_id=str(agent.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    return updated_agent

@router.post("/{agent_id}/auto-login/disable", response_model=AgentResponse)
def disable_agent_auto_login(
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_update)
) -> Any:
    """
    Disable auto-login for an agent.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Disable auto-login
    agent_update = AgentUpdate(
        auto_login_enabled=False
    )
    
    # Update agent
    updated_agent = agent_service.update_agent(
        agent_id=str(agent.agent_id),
        agent_in=agent_update,
        tenant_id=str(agent.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    return updated_agent

@router.post("/register", response_model=AgentResponse)
def register_agent(
    agent_in: AgentCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new agent. This endpoint is used by agents to register themselves.
    No authentication is required, but the machine_id is used for verification.
    """
    # Create agent service
    agent_service = AgentService(db)
    
    # Check if machine_id is provided
    if not agent_in.machine_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="machine_id is required"
        )
        
    # Check if tenant_id is provided
    if not agent_in.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required"
        )
        
    # Register agent
    agent = agent_service.register_agent(
        agent_in=agent_in,
        tenant_id=agent_in.tenant_id
    )
    
    return agent

@router.post("/{agent_id}/heartbeat", response_model=dict)
def agent_heartbeat(
    agent_id: str,
    heartbeat_data: dict,
    db: Session = Depends(get_db)
) -> Any:
    """
    Update agent heartbeat. This endpoint is used by agents to send heartbeat signals.
    """
    # Extract tenant_id from headers if possible
    tenant_id = heartbeat_data.get("tenant_id")
    
    # If not in data, try to get from agent record
    if not tenant_id:
        # Find agent without tenant filter first
        # This query is less restrictive - find by agent_id only
        agent_query = db.query(Agent).filter(Agent.agent_id == agent_id)
        agent = agent_query.first()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Agent not found"
            )
            
        tenant_id = str(agent.tenant_id)
    
    # Create agent service
    agent_service = AgentService(db)
    
    # Update heartbeat - using the extracted tenant_id
    try:
        agent_service.update_agent_status(
            agent_id=agent_id,
            tenant_id=tenant_id,
            status="online"
        )
        
        # Return empty response
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logging.error(f"Error updating agent status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent status: {str(e)}"
        )
