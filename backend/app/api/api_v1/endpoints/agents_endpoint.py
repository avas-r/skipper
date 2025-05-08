"""
API endpoints for agent management.

This module provides API endpoints for managing agents:
- List, create, update, delete agents
- Agent logs
- Agent commands
- Auto-login configuration
- Agent registration and heartbeat
"""

import logging
from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_active_user, get_current_agent
from app.auth.permissions import PermissionChecker
from app.db.session import get_db
from app.models import User, Agent, AgentLog
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
    AgentLogResponse,
    AgentCommandRequest,
    AgentHeartbeatRequest
)
from app.services.agent_manager import AgentManager
from app.messaging.producer import get_message_producer
from app.api.api_v1.dependencies import get_agent_from_path

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
    tenant_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    tags: Optional[List[str]] = Query(None)
) -> Any:
    """
    List all agents with optional filtering.
    """
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
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
    result = agent_manager.get_agents(
        tenant_id=tenant_id,
        status=status,
        search=search,
        tags=tags,
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
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Create agent
    try:
        agent = agent_manager.create_agent(
            agent_data=agent_in,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        return agent
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {str(e)}"
        )

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
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Update agent
    try:
        updated_agent = agent_manager.update_agent(
            agent_id=str(agent.agent_id),
            agent_data=agent_in,
            tenant_id=str(agent.tenant_id),
            user_id=str(current_user.user_id)
        )
        return updated_agent
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to update agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {str(e)}"
        )

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent(
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_delete)
) -> None:
    """
    Delete an agent.
    """
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Delete agent
    try:
        agent_manager.delete_agent(
            agent_id=str(agent.agent_id),
            tenant_id=str(agent.tenant_id),
            user_id=str(current_user.user_id)
        )
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to delete agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {str(e)}"
        )

@router.get("/{agent_id}/logs", response_model=List[AgentLogResponse])
def get_agent_logs(
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_read),
    skip: int = 0,
    limit: int = 100,
    log_level: Optional[str] = None
) -> Any:
    """
    Get agent logs.
    """
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Get logs
    try:
        logs = agent_manager.get_agent_logs(
            agent_id=str(agent.agent_id),
            tenant_id=str(agent.tenant_id),
            log_level=log_level,
            skip=skip,
            limit=limit
        )
        return logs
    except Exception as e:
        logger.error(f"Failed to get agent logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent logs: {str(e)}"
        )

@router.post("/{agent_id}/command", response_model=AgentResponse)
def send_agent_command(
    command: AgentCommandRequest,
    agent: Agent = Depends(get_agent_from_path),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_update),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Send a command to an agent.
    """
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Send command
    try:
        success = agent_manager.send_command(
            agent_id=str(agent.agent_id),
            tenant_id=str(agent.tenant_id),
            command=command,
            user_id=str(current_user.user_id)
        )
        
        if success:
            # Return agent
            return agent
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send command to agent"
            )
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to send command to agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send command to agent: {str(e)}"
        )

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
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Enable auto-login
    try:
        updated_agent = agent_manager.configure_auto_login(
            agent_id=str(agent.agent_id),
            tenant_id=str(agent.tenant_id),
            service_account_id=service_account_id,
            session_type=session_type,
            user_id=str(current_user.user_id)
        )
        return updated_agent
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to enable auto-login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable auto-login: {str(e)}"
        )

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
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Disable auto-login
    try:
        updated_agent = agent_manager.disable_auto_login(
            agent_id=str(agent.agent_id),
            tenant_id=str(agent.tenant_id),
            user_id=str(current_user.user_id)
        )
        return updated_agent
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        logger.error(f"Failed to disable auto-login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable auto-login: {str(e)}"
        )

@router.post("/register", response_model=AgentResponse)
def register_agent(
    agent_in: AgentCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new agent. This endpoint is used by agents to register themselves.
    No authentication is required, but the machine_id is used for verification.
    """
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
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
    try:
        agent = agent_manager.register_agent(
            registration_data=agent_in,
            tenant_id=agent_in.tenant_id
        )
        return agent
    except Exception as e:
        logger.error(f"Agent registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent registration failed: {str(e)}"
        )

@router.post("/{agent_id}/heartbeat")
def agent_heartbeat(
    agent_id: str,
    heartbeat_data: AgentHeartbeatRequest,
    db: Session = Depends(get_db),
    current_agent: Agent = Depends(get_current_agent)
) -> Any:
    """
    Update agent heartbeat. This endpoint is used by agents to send heartbeat signals.
    """
    # Check if agent ID matches
    if str(current_agent.agent_id) != agent_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent ID mismatch"
        )
    
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Update heartbeat
    try:
        agent_manager.update_heartbeat(
            agent_id=agent_id,
            tenant_id=str(current_agent.tenant_id),
            heartbeat=heartbeat_data
        )
        
        # Return success response with timestamp
        return {
            "status": "ok", 
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id
        }
    except Exception as e:
        logger.error(f"Error updating agent heartbeat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating agent heartbeat: {str(e)}"
        )

@router.post("/check-stale", response_model=dict)
def check_stale_agents(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_agent_read),
    max_silence_minutes: int = Query(5, description="Maximum silence time in minutes")
) -> Any:
    """
    Check for stale agents and mark them as offline.
    This endpoint is intended for scheduled calls.
    """
    # Create agent manager
    message_producer = get_message_producer()
    agent_manager = AgentManager(db, message_producer)
    
    # Run check in background task
    def bg_check_stale_agents():
        try:
            count = agent_manager.check_stale_agents(max_silence_minutes)
            logger.info(f"Marked {count} stale agents as offline")
        except Exception as e:
            logger.error(f"Error checking stale agents: {str(e)}")
    
    # Add task to background tasks
    background_tasks.add_task(bg_check_stale_agents)
    
    # Return immediate response
    return {
        "status": "started",
        "message": "Checking stale agents in background"
    }