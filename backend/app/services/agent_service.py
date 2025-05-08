"""
Agent service for managing agent operations.

This module provides services for managing agents, agent logs, and agent commands.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models import Agent, AgentLog, AuditLog, Tenant
from ..schemas.agent import AgentCreate, AgentUpdate, AgentHeartbeatRequest
from ..messaging.producer import get_message_producer


logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing agents"""
    
    def __init__(self, db: Session):
        """
        Initialize the agent service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def register_agent(self, agent_in: AgentCreate, tenant_id: str) -> Agent:
        """
        Register a new agent or update existing agent.
        
        Args:
            agent_in: Agent data
            tenant_id: Tenant ID
            
        Returns:
            Agent: Created or updated agent
        """
        # Validate tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")
        
        # Check if agent already exists by machine_id
        existing_agent = self.db.query(Agent).filter(
            Agent.machine_id == agent_in.machine_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if existing_agent:
            # Update existing agent
            for key, value in agent_in.dict(exclude_unset=True, exclude={"tenant_id"}).items():
                setattr(existing_agent, key, value)
                
            # Update status and heartbeat
            existing_agent.status = "online"
            existing_agent.last_heartbeat = datetime.utcnow()
            existing_agent.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(existing_agent)
            
            # Log agent update
            self.log_agent_activity(
                existing_agent.agent_id,
                tenant_id,
                "info",
                f"Agent updated: {existing_agent.name}",
                {
                    "ip_address": existing_agent.ip_address,
                    "version": existing_agent.version
                }
            )
            
            # Send agent event - moved to sync version
            # We'll log this action but skip sending the event for now
            logger.info(f"Agent updated: {existing_agent.agent_id} for tenant {tenant_id}")
            
            return existing_agent
            
        else:
            # Create new agent
            agent_data = agent_in.dict(exclude_unset=True, exclude={"tenant_id"})
            agent_data["tenant_id"] = tenant_id
            agent_data["status"] = "online"
            agent_data["last_heartbeat"] = datetime.utcnow()
            
            new_agent = Agent(**agent_data)
            self.db.add(new_agent)
            self.db.commit()
            self.db.refresh(new_agent)
            
            # Log agent creation
            self.log_agent_activity(
                new_agent.agent_id,
                tenant_id,
                "info",
                f"Agent registered: {new_agent.name}",
                {
                    "machine_id": new_agent.machine_id,
                    "ip_address": new_agent.ip_address,
                    "version": new_agent.version
                }
            )
            
            # Send agent event - moved to sync version
            # We'll log this action but skip sending the event for now
            logger.info(f"Agent registered: {new_agent.agent_id} for tenant {tenant_id}")
            
            return new_agent
    
    def create_agent(self, agent_in: AgentCreate, tenant_id: str, user_id: str) -> Agent:
        """
        Create a new agent (admin function).
        
        Args:
            agent_in: Agent data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Agent: Created agent
        """
        # Validate tenant
        tenant = self.db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant not found: {tenant_id}")
        
        # Check if agent already exists by machine_id
        existing_agent = self.db.query(Agent).filter(
            Agent.machine_id == agent_in.machine_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if existing_agent:
            raise ValueError(f"Agent with machine_id {agent_in.machine_id} already exists")
        
        # Create new agent
        agent_data = agent_in.dict(exclude_unset=True, exclude={"tenant_id"})
        agent_data["tenant_id"] = tenant_id
        
        new_agent = Agent(**agent_data)
        self.db.add(new_agent)
        self.db.commit()
        self.db.refresh(new_agent)
        
        # Create audit log
        audit_log = AuditLog(
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
        self.db.add(audit_log)
        self.db.commit()
        
        return new_agent
    
    def update_agent(self, agent_id: str, agent_in: AgentUpdate, tenant_id: str, user_id: str) -> Agent:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            agent_in: Agent update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Agent: Updated agent
        """
        # Get agent
        agent = self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Update agent
        for key, value in agent_in.dict(exclude_unset=True).items():
            setattr(agent, key, value)
            
        agent.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_agent",
            entity_type="agent",
            entity_id=agent.agent_id,
            details={
                "name": agent.name,
                "status": agent.status
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        # Log agent update
        self.log_agent_activity(
            agent.agent_id,
            tenant_id,
            "info",
            f"Agent updated: {agent.name}",
            agent_in.dict(exclude_unset=True)
        )
        
        return agent
    
    def delete_agent(self, agent_id: str, tenant_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get agent
        agent = self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        # Delete agent logs
        self.db.query(AgentLog).filter(
            AgentLog.agent_id == agent_id
        ).delete()
        
        # Delete agent
        self.db.delete(agent)
        self.db.commit()
        
        return True
    
    def get_agent(self, agent_id: str, tenant_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
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
    
    def list_agents(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Agent]:
        """
        List agents with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
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
                    Agent.ip_address.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        query = query.order_by(Agent.name).offset(skip).limit(limit)
        
        return query.all()
    
    def count_agents(self, tenant_id: str, status: Optional[str] = None) -> int:
        """
        Count agents with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            
        Returns:
            int: Number of agents
        """
        query = self.db.query(func.count(Agent.agent_id)).filter(Agent.tenant_id == tenant_id)
        
        # Apply status filter
        if status:
            query = query.filter(Agent.status == status)
        
        return query.scalar()
    
    async def update_heartbeat(self, agent_id: str, tenant_id: str, metrics: Dict[str, Any]) -> Optional[Agent]:
        """
        Update agent heartbeat.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            metrics: Heartbeat metrics
            
        Returns:
            Optional[Agent]: Updated agent or None if not found
        """
        # Get agent
        agent = await self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if not agent:
            logger.warning(f"Agent not found for heartbeat: {agent_id}")
            return None
        
        # Check if status changed
        old_status = agent.status
        
        # Update agent
        agent.last_heartbeat = datetime.utcnow()
        agent.status = metrics.get("status", "online")
        agent.updated_at = datetime.utcnow()
        
        # Update capabilities if provided
        if "capabilities" in metrics:
            agent.capabilities = metrics["capabilities"]
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Log status change if needed
        if old_status != agent.status:
            self.log_agent_activity(
                agent.agent_id,
                tenant_id,
                "info",
                f"Agent status changed from {old_status} to {agent.status}",
                {"old_status": old_status, "new_status": agent.status}
            )
            
            # Send agent event
            await self._send_agent_event(
                "agent_status_change",
                agent.agent_id,
                tenant_id,
                {
                    "old_status": old_status,
                    "new_status": agent.status
                }
            )
        
        return agent
    
    def update_agent_status(self, agent_id: str, tenant_id: str, status: str) -> Optional[Agent]:
        """
        Update agent status.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            status: New status
            
        Returns:
            Optional[Agent]: Updated agent or None if not found
        """
        # Get agent
        agent = self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if not agent:
            return None
        
        # Check if status changed
        old_status = agent.status
        
        # Update agent
        agent.status = status
        agent.updated_at = datetime.utcnow()
        agent.last_heartbeat = datetime.utcnow()  # Update heartbeat time as well
        
        self.db.commit()
        self.db.refresh(agent)
        
        # Log status change if needed
        if old_status != status:
            self.log_agent_activity(
                agent.agent_id,
                tenant_id,
                "info",
                f"Agent status changed from {old_status} to {status}",
                {"old_status": old_status, "new_status": status}
            )
            
            # Log agent event instead of sending it asynchronously
            logger.info(f"Agent status changed: {agent.agent_id} from {old_status} to {status}")
            
        return agent
        
        return agent
    
    def check_stale_agents(self, max_silence_minutes: int = 5) -> int:
        """
        Check for stale agents and mark them as offline.
        
        Args:
            max_silence_minutes: Maximum silence time in minutes
            
        Returns:
            int: Number of agents marked offline
        """
        cutoff_time = datetime.utcnow().timestamp() - (max_silence_minutes * 60)
        cutoff_datetime = datetime.fromtimestamp(cutoff_time)
        
        # Find stale agents
        stale_agents = self.db.query(Agent).filter(
            Agent.status == "online",
            Agent.last_heartbeat < cutoff_datetime
        ).all()
        
        # Update status to offline
        count = 0
        for agent in stale_agents:
            agent.status = "offline"
            agent.updated_at = datetime.utcnow()
            
            # Log status change
            self.log_agent_activity(
                agent.agent_id,
                str(agent.tenant_id),
                "warning",
                f"Agent marked offline due to inactivity: {agent.name}",
                {
                    "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
                    "silence_minutes": max_silence_minutes
                }
            )
            
            count += 1
        
        self.db.commit()
        
        return count
    
    def log_agent_activity(
        self,
        agent_id: uuid.UUID,
        tenant_id: str,
        log_level: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentLog:
        """
        Log agent activity.
        
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
            agent_id=agent_id,
            tenant_id=tenant_id,
            log_level=log_level,
            message=message,
            metadata=metadata or {}
        )
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        
        return log
    
    def get_agent_logs(
        self,
        agent_id: str,
        tenant_id: str,
        log_level: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AgentLog]:
        """
        Get agent logs.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            log_level: Optional log level filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AgentLog]: List of agent logs
        """
        query = self.db.query(AgentLog).filter(
            AgentLog.agent_id == agent_id,
            AgentLog.tenant_id == tenant_id
        )
        
        # Apply log level filter
        if log_level:
            query = query.filter(AgentLog.log_level == log_level)
        
        # Apply pagination
        query = query.order_by(AgentLog.created_at.desc()).offset(skip).limit(limit)
        
        return query.all()
    
    async def send_agent_command(
        self,
        agent_id: str,
        tenant_id: str,
        command_type: str,
        command_parameters: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Optional[Agent]:
        """
        Send a command to an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            command_type: Command type
            command_parameters: Optional command parameters
            user_id: Optional user ID
            
        Returns:
            Optional[Agent]: Agent or None if not found
        """
        # Get agent
        agent = await self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if not agent:
            return None
        
        # Create command
        command = {
            "type": command_type,
            "parameters": command_parameters or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Send command to messaging system
        message_producer = get_message_producer()
        await message_producer.send_message(
            exchange="agents",
            routing_key=f"agent.{agent_id}.command",
            message_data={
                "agent_id": str(agent_id),
                "tenant_id": tenant_id,
                "command": command
            }
        )
        
        # Log command
        await self.log_agent_activity(
            agent.agent_id,
            tenant_id,
            "info",
            f"Command sent to agent: {command_type}",
            {
                "command_type": command_type,
                "parameters": command_parameters,
                "user_id": user_id
            }
        )
        
        # Create audit log if user_id provided
        if user_id:
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action="send_agent_command",
                entity_type="agent",
                entity_id=agent.agent_id,
                details={
                    "command_type": command_type,
                    "parameters": command_parameters
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return agent
    
    async def process_heartbeat(self, agent_id: str, tenant_id: str, heartbeat: AgentHeartbeatRequest) -> Dict[str, Any]:
        """
        Process agent heartbeat and return commands.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            heartbeat: Heartbeat data
            
        Returns:
            Dict[str, Any]: Response with commands
        """
        # Update agent heartbeat
        await self.update_heartbeat(agent_id, tenant_id, heartbeat.dict())
        
        # Get pending commands for agent
        # In a real implementation, this would retrieve commands from queue or database
        commands = []
        
        return {
            "commands": commands,
            "server_time": datetime.utcnow()
        }
    
    async def _send_agent_event(
        self,
        event_type: str,
        agent_id: uuid.UUID,
        tenant_id: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Send agent event to messaging system.
        
        Args:
            event_type: Event type
            agent_id: Agent ID
            tenant_id: Tenant ID
            data: Event data
        """
        message_producer = get_message_producer()
        await message_producer.send_message(
            exchange="events",
            routing_key=f"agent.{event_type}",
            message_data={
                "event_type": f"agent_{event_type}",
                "agent_id": str(agent_id),
                "tenant_id": tenant_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
        )