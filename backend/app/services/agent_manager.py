"""
Agent management module for the orchestrator backend.

This module provides functionality for managing agents, including:
- Agent registration and setup
- Status monitoring
- Agent command distribution
- Auto-login configuration
"""

import logging
import uuid
import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models import Agent, AgentLog, AuditLog, ServiceAccount, AgentSession, User
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentHeartbeatRequest,
    AgentCommandRequest,
    AgentLogResponse,
    AgentHeartbeatResponse
)
from app.messaging.producer import MessageProducer

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent manager service for handling agent operations"""
    
    def __init__(self, db: Session, message_producer: Optional[MessageProducer] = None):
        """
        Initialize the agent manager.
        
        Args:
            db: Database session
            message_producer: Optional message producer for agent commands
        """
        self.db = db
        self.message_producer = message_producer
        
    def get_agents(self, tenant_id: str, status: Optional[str] = None, 
                   search: Optional[str] = None, tags: Optional[List[str]] = None,
                   skip: int = 0, limit: int = 100) -> List[Agent]:
        """
        Get list of agents with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            tags: Optional tags to filter
            skip: Number of records to skip (pagination)
            limit: Maximum records to return (pagination)
            
        Returns:
            List[Agent]: List of agents
        """
        query = self.db.query(Agent).filter(Agent.tenant_id == tenant_id)
        
        # Apply status filter
        if status:
            query = query.filter(Agent.status == status)
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Agent.name.ilike(f"%{search}%"),
                    Agent.machine_id.ilike(f"%{search}%"),
                    func.cast(Agent.ip_address, type_=str).ilike(f"%{search}%")
                )
            )
        
        # Apply tags filter
        if tags:
            for tag in tags:
                query = query.filter(Agent.tags.contains([tag]))
        
        # Apply pagination
        query = query.order_by(Agent.name).offset(skip).limit(limit)
        
        return query.all()
        
    def get_agent(self, agent_id: str, tenant_id: str) -> Optional[Agent]:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Agent]: Agent or None if not found
        """
        return self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
    def create_agent(self, agent_data: AgentCreate, tenant_id: str, user_id: str) -> Agent:
        """
        Create a new agent.
        
        Args:
            agent_data: Agent creation data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Agent: Created agent
            
        Raises:
            HTTPException: If agent with same machine_id already exists
        """
        # Check if agent already exists
        existing_agent = self.db.query(Agent).filter(
            Agent.machine_id == agent_data.machine_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with machine_id {agent_data.machine_id} already exists"
            )
            
        # Create new agent
        agent_dict = agent_data.dict(exclude_unset=True, exclude={"tenant_id"})
        agent_dict["tenant_id"] = tenant_id
        agent_dict["status"] = "offline"  # Initial status
        agent_dict["created_at"] = datetime.now(timezone.utc)
        agent_dict["updated_at"] = datetime.now(timezone.utc)
        
        # Generate API key for agent authentication
        api_key = self._generate_api_key()
        agent_dict["api_key"] = api_key
        
        new_agent = Agent(**agent_dict)
        self.db.add(new_agent)
        self.db.commit()
        self.db.refresh(new_agent)
        
        # Log agent creation
        self._log_agent_activity(
            new_agent.agent_id,
            tenant_id,
            "info",
            f"Agent created by user: {new_agent.name}",
            {"creator_id": user_id}
        )
        
        # Create audit log
        self._create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_agent",
            entity_type="agent",
            entity_id=new_agent.agent_id,
            details={
                "name": new_agent.name,
                "machine_id": new_agent.machine_id
            }
        )
        
        return new_agent
    
    def update_agent(self, agent_id: str, agent_data: AgentUpdate, 
                     tenant_id: str, user_id: str) -> Agent:
        """
        Update an existing agent.
        
        Args:
            agent_id: Agent ID
            agent_data: Agent update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Agent: Updated agent
            
        Raises:
            HTTPException: If agent not found
        """
        # Get agent
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        # Store original values for audit log
        original_values = {
            "name": agent.name,
            "status": agent.status,
            "tags": agent.tags,
            "settings": agent.settings,
            "auto_login_enabled": agent.auto_login_enabled,
            "service_account_id": agent.service_account_id,
            "session_type": agent.session_type
        }
        
        # Update fields
        update_data = agent_data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(agent, key, value)
            
        agent.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Log agent update
        self._log_agent_activity(
            agent.agent_id,
            tenant_id,
            "info",
            f"Agent updated by user: {agent.name}",
            {"updater_id": user_id, "updated_fields": list(update_data.keys())}
        )
        
        # Create audit log
        self._create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_agent",
            entity_type="agent",
            entity_id=agent.agent_id,
            details={
                "name": agent.name,
                "original_values": original_values,
                "updated_fields": update_data
            }
        )
        
        return agent
    
    def delete_agent(self, agent_id: str, tenant_id: str, user_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            HTTPException: If agent not found
        """
        # Get agent
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        
        # Store agent info for audit log
        agent_info = {
            "name": agent.name,
            "machine_id": agent.machine_id,
            "ip_address": agent.ip_address,
            "version": agent.version,
            "status": agent.status,
            "created_at": agent.created_at.isoformat() if agent.created_at else None
        }
        
        # Check if agent has active sessions
        active_sessions = self.db.query(AgentSession).filter(
            AgentSession.agent_id == agent_id,
            AgentSession.ended_at.is_(None)
        ).count()
        
        if active_sessions > 0:
            # End active sessions
            self.db.query(AgentSession).filter(
                AgentSession.agent_id == agent_id,
                AgentSession.ended_at.is_(None)
            ).update({
                "ended_at": datetime.now(timezone.utc),
                "status": "terminated"
            })
        
        # Delete agent logs
        self.db.query(AgentLog).filter(
            AgentLog.agent_id == agent_id
        ).delete()
        
        # Delete agent
        self.db.delete(agent)
        
        # Create audit log
        self._create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete_agent",
            entity_type="agent",
            entity_id=agent_id,
            details=agent_info
        )
        
        self.db.commit()
        
        return True
    
    def get_agent_logs(self, agent_id: str, tenant_id: str, 
                       log_level: Optional[str] = None,
                       skip: int = 0, limit: int = 100) -> List[AgentLog]:
        """
        Get logs for a specific agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            log_level: Optional log level filter
            skip: Number of records to skip (pagination)
            limit: Maximum records to return (pagination)
            
        Returns:
            List[AgentLog]: List of agent logs
        """
        query = self.db.query(AgentLog).filter(
            AgentLog.agent_id == agent_id,
            AgentLog.tenant_id == tenant_id
        )
        
        if log_level:
            query = query.filter(AgentLog.log_level == log_level)
            
        # Order by most recent first
        query = query.order_by(AgentLog.created_at.desc())
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        return query.all()
    
    def send_command(self, agent_id: str, tenant_id: str, 
                     command: AgentCommandRequest, user_id: str) -> bool:
        """
        Send a command to an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            command: Command to send
            user_id: User ID sending the command
            
        Returns:
            bool: True if command was sent successfully
            
        Raises:
            HTTPException: If agent not found or message producer not available
        """
        # Get agent
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
            
        # Check if message producer is available
        if not self.message_producer:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Command messaging not available"
            )
            
        # Prepare command message
        message = {
            "command_type": command.command_type,
            "parameters": command.parameters or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sender": {
                "user_id": user_id,
                "tenant_id": tenant_id
            }
        }
        
        try:
            # Send command to agent
            self.message_producer.send_message(
                exchange="agents",
                routing_key=f"agent.{agent_id}.command",
                message=message
            )
            
            # Log command
            self._log_agent_activity(
                agent_id,
                tenant_id,
                "info",
                f"Command sent to agent: {command.command_type}",
                {
                    "command_type": command.command_type,
                    "parameters": command.parameters,
                    "sender_id": user_id
                }
            )
            
            # Create audit log
            self._create_audit_log(
                tenant_id=tenant_id,
                user_id=user_id,
                action="send_agent_command",
                entity_type="agent",
                entity_id=agent_id,
                details={
                    "command_type": command.command_type,
                    "parameters": command.parameters,
                    "agent_name": agent.name
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command to agent {agent_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send command: {str(e)}"
            )
    
    def register_agent(self, registration_data: AgentCreate, tenant_id: str) -> Agent:
        """
        Register an agent from an agent itself.
        
        Args:
            registration_data: Agent registration data
            tenant_id: Tenant ID
            
        Returns:
            Agent: Registered agent (new or updated)
        """
        # Check if agent already exists by machine ID
        existing_agent = self.db.query(Agent).filter(
            Agent.machine_id == registration_data.machine_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if existing_agent:
            # Update existing agent
            agent_dict = registration_data.dict(exclude_unset=True, exclude={"tenant_id"})
            
            # Update agent properties
            for key, value in agent_dict.items():
                setattr(existing_agent, key, value)
                
            # Update status and timestamps
            existing_agent.status = "online"
            existing_agent.last_heartbeat = datetime.now(timezone.utc)
            existing_agent.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            self.db.refresh(existing_agent)
            
            # Log agent update
            self._log_agent_activity(
                existing_agent.agent_id,
                tenant_id,
                "info",
                f"Agent self-registered: {existing_agent.name}",
                {
                    "ip_address": existing_agent.ip_address,
                    "version": existing_agent.version,
                    "capabilities": existing_agent.capabilities
                }
            )
            
            return existing_agent
        else:
            # Create new agent
            agent_dict = registration_data.dict(exclude_unset=True, exclude={"tenant_id"})
            agent_dict["tenant_id"] = tenant_id
            agent_dict["status"] = "online"
            agent_dict["last_heartbeat"] = datetime.now(timezone.utc)
            agent_dict["created_at"] = datetime.now(timezone.utc)
            agent_dict["updated_at"] = datetime.now(timezone.utc)
            
            # Generate API key for agent authentication
            api_key = self._generate_api_key()
            agent_dict["api_key"] = api_key
            
            new_agent = Agent(**agent_dict)
            self.db.add(new_agent)
            self.db.commit()
            self.db.refresh(new_agent)
            
            # Log agent creation
            self._log_agent_activity(
                new_agent.agent_id,
                tenant_id,
                "info",
                f"New agent self-registered: {new_agent.name}",
                {
                    "machine_id": new_agent.machine_id,
                    "ip_address": new_agent.ip_address,
                    "version": new_agent.version,
                    "capabilities": new_agent.capabilities
                }
            )
            
            return new_agent
    
    def update_heartbeat(self, agent_id: str, tenant_id: str, 
                        heartbeat: AgentHeartbeatRequest) -> Optional[Agent]:
        """
        Update agent heartbeat.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            heartbeat: Heartbeat data
            
        Returns:
            Optional[Agent]: Updated agent or None if not found
        """
        # Get agent
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            logger.warning(f"Agent not found for heartbeat: {agent_id}")
            return None
        
        # Check if status changed
        old_status = agent.status
        new_status = heartbeat.status if heartbeat.status else "online"
        
        # Update agent
        agent.last_heartbeat = datetime.now(timezone.utc)
        agent.status = new_status
        agent.updated_at = datetime.now(timezone.utc)
        
        # Update capabilities if provided
        if heartbeat.capabilities:
            agent.capabilities = heartbeat.capabilities
            
        # Update IP address if provided
        if heartbeat.ip_address:
            agent.ip_address = heartbeat.ip_address
            
        self.db.commit()
        self.db.refresh(agent)
        
        # Log status change if needed
        if old_status != new_status:
            self._log_agent_activity(
                agent.agent_id,
                tenant_id,
                "info",
                f"Agent status changed from {old_status} to {new_status}",
                {"old_status": old_status, "new_status": new_status}
            )
            
        return agent
    
    def configure_auto_login(self, agent_id: str, tenant_id: str, 
                           service_account_id: str, session_type: str,
                           user_id: str) -> Agent:
        """
        Configure auto-login for an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            service_account_id: Service account ID to use for auto-login
            session_type: Session type (windows, web, etc.)
            user_id: User ID making the change
            
        Returns:
            Agent: Updated agent
            
        Raises:
            HTTPException: If agent or service account not found
        """
        # Get agent
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
            
        # Get service account
        service_account = self.db.query(ServiceAccount).filter(
            ServiceAccount.account_id == service_account_id,
            ServiceAccount.tenant_id == tenant_id
        ).first()
        
        if not service_account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service account not found: {service_account_id}"
            )
            
        # Update agent
        agent.service_account_id = service_account_id
        agent.auto_login_enabled = True
        agent.session_type = session_type
        agent.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Log configuration
        self._log_agent_activity(
            agent.agent_id,
            tenant_id,
            "info",
            f"Auto-login configured for agent: {agent.name}",
            {
                "service_account": service_account.username,
                "session_type": session_type,
                "configured_by": user_id
            }
        )
        
        # Create audit log
        self._create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="configure_auto_login",
            entity_type="agent",
            entity_id=agent_id,
            details={
                "agent_name": agent.name,
                "service_account_id": service_account_id,
                "service_account_username": service_account.username,
                "session_type": session_type
            }
        )
        
        return agent
    
    def disable_auto_login(self, agent_id: str, tenant_id: str, user_id: str) -> Agent:
        """
        Disable auto-login for an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            user_id: User ID making the change
            
        Returns:
            Agent: Updated agent
            
        Raises:
            HTTPException: If agent not found
        """
        # Get agent
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
            
        # Check if auto-login is enabled
        if not agent.auto_login_enabled:
            return agent  # Already disabled
            
        # Store service account info for logging
        service_account_id = agent.service_account_id
        service_account = None
        if service_account_id:
            service_account = self.db.query(ServiceAccount).filter(
                ServiceAccount.account_id == service_account_id
            ).first()
            
        # Update agent
        agent.auto_login_enabled = False
        agent.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Log configuration
        self._log_agent_activity(
            agent.agent_id,
            tenant_id,
            "info",
            f"Auto-login disabled for agent: {agent.name}",
            {
                "service_account": service_account.username if service_account else None,
                "disabled_by": user_id
            }
        )
        
        # Create audit log
        self._create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="disable_auto_login",
            entity_type="agent",
            entity_id=agent_id,
            details={
                "agent_name": agent.name,
                "service_account_id": service_account_id,
                "service_account_username": service_account.username if service_account else None
            }
        )
        
        return agent

    def check_stale_agents(self, max_silence_minutes: int = 5) -> int:
        """Mark agents as offline if no heartbeat received"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=max_silence_minutes)
        
        # Single query to update all stale agents
        result = self.db.query(Agent).filter(
            Agent.status.in_(["online", "busy"]),
            Agent.last_heartbeat < cutoff_time
        ).update(
            {
                Agent.status: "offline", 
                Agent.updated_at: datetime.now(timezone.utc)
            },
            synchronize_session=False
        )
        
        self.db.commit()
        return result    
    
    def _generate_api_key(self) -> str:
        """
        Generate a secure API key for agent authentication.
        
        Returns:
            str: Generated API key
        """
        return ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(40)
        )
    
    def _log_agent_activity(self, agent_id: uuid.UUID, tenant_id: str, 
                          log_level: str, message: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> AgentLog:
        """
        Create an agent activity log.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            log_level: Log level
            message: Log message
            metadata: Optional log metadata
            
        Returns:
            AgentLog: Created log
        """
        # Create log
        log = AgentLog(
            log_id=uuid.uuid4(),
            agent_id=agent_id,
            tenant_id=tenant_id,
            log_level=log_level,
            message=message,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def _create_audit_log(self, tenant_id: str, user_id: Optional[str] = None,
                        action: str = "", entity_type: str = "", 
                        entity_id: Optional[uuid.UUID] = None,
                        details: Optional[Dict[str, Any]] = None) -> AuditLog:
        """
        Create an audit log.
        
        Args:
            tenant_id: Tenant ID
            user_id: Optional user ID
            action: Action performed
            entity_type: Entity type
            entity_id: Optional entity ID
            details: Optional details
            
        Returns:
            AuditLog: Created audit log
        """
        # Create audit log
        audit_log = AuditLog(
            log_id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        return audit_log