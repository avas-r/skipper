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
import json
import asyncio
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
    AgentResponse,
    AgentCommandRequest,
    AgentLogResponse,
    AgentHeartbeatResponse
)
from app.messaging.producer import MessageProducer

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent manager service for handling agent operations"""
    
    def __init__(self, db: Session, message_producer: Optional[MessageProducer] = None):
        self.db = db
        self.message_producer = message_producer
        
    def get_agents(self, tenant_id: str, status: Optional[str] = None, 
                   search: Optional[str] = None, tags: Optional[List[str]] = None,
                   skip: int = 0, limit: int = 100) -> List[Agent]:
        query = self.db.query(Agent).filter(Agent.tenant_id == tenant_id)
        if status:
            query = query.filter(Agent.status == status)
        if search:
            query = query.filter(
                or_(
                    Agent.name.ilike(f"%{search}%"),
                    Agent.machine_id.ilike(f"%{search}%"),
                    Agent.ip_address.ilike(f"%{search}%")
                )
            )
        if tags:
            for tag in tags:
                query = query.filter(Agent.tags.contains([tag]))
        return query.order_by(Agent.name).offset(skip).limit(limit).all()
        
    def get_agent(self, agent_id: str, tenant_id: str) -> Optional[Agent]:
        return self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
    def create_agent(self, agent_data: AgentCreate, tenant_id: str, user_id: str) -> Agent:
        existing = self.db.query(Agent).filter(
            Agent.machine_id == agent_data.machine_id,
            Agent.tenant_id == tenant_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with machine_id {agent_data.machine_id} already exists"
            )
        agent_dict = agent_data.dict(exclude_unset=True)
        agent_dict.update({
            "tenant_id": tenant_id,
            "status": "offline",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "api_key": self._generate_api_key()
        })
        agent = Agent(**agent_dict)
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        self._log_agent_activity(
            agent.agent_id,
            tenant_id,
            "info",
            f"Agent created: {agent.name}",
            {"creator_id": user_id}
        )
        self._create_audit_log(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_agent",
            entity_type="agent",
            entity_id=agent.agent_id,
            details={"name": agent.name, "machine_id": agent.machine_id}
        )
        return agent
    
    def update_agent(self, agent_id: str, agent_data: AgentUpdate, 
                     tenant_id: str, user_id: str) -> Agent:
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent not found: {agent_id}"
            )
        original = {k: getattr(agent, k) for k in [
            "name","status","tags","settings","auto_login_enabled",
            "service_account_id","session_type"
        ]}
        updates = agent_data.dict(exclude_unset=True)
        for key, val in updates.items(): setattr(agent, key, val)
        agent.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(agent)
        self._log_agent_activity(
            agent.agent_id, tenant_id, "info",
            f"Agent updated: {agent.name}", {"updater_id": user_id, "fields": list(updates.keys())}
        )
        self._create_audit_log(
            tenant_id=tenant_id, user_id=user_id,
            action="update_agent", entity_type="agent", entity_id=agent.agent_id,
            details={"original": original, "updated": updates}
        )
        return agent
    
    def delete_agent(self, agent_id: str, tenant_id: str, user_id: str) -> bool:
        agent = self.get_agent(agent_id, tenant_id)
        if not agent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Agent not found: {agent_id}")
        active = self.db.query(AgentSession).filter(
            AgentSession.agent_id == agent_id,
            AgentSession.ended_at.is_(None)
        ).all()
        now = datetime.now(timezone.utc)
        # Close any active sessions
        for sess in active:
            sess.ended_at = now
            self.db.add(sess)
        # Remove the agent
        self.db.delete(agent)
        self.db.commit()
        self._log_agent_activity(
            agent.agent_id, tenant_id, "warning",
            f"Agent deleted: {agent.name}", {"deleter_id": user_id}
        )
        self._create_audit_log(
            tenant_id=tenant_id, user_id=user_id,
            action="delete_agent", entity_type="agent", entity_id=agent_id,
            details={"name": agent.name, "machine_id": agent.machine_id}
        )
        return True
    
    def record_heartbeat(
        self, heartbeat: AgentHeartbeatRequest, tenant_id: str
    ) -> AgentResponse:
        agent = self.get_agent(heartbeat.agent_id, tenant_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not registered")
        now = datetime.now(timezone.utc)
        agent.last_heartbeat = now
        agent.status = heartbeat.status
        agent.updated_at = now
        # Manage session
        session = self.db.query(AgentSession).filter(
            AgentSession.agent_id == agent.agent_id,
            AgentSession.ended_at.is_(None)
        ).first()
        if not session:
            session = AgentSession(
                session_id=str(uuid.uuid4()),
                agent_id=agent.agent_id,
                start_time=now
            )
            self.db.add(session)
        self.db.commit()
        self.db.refresh(agent)
        return AgentResponse.from_orm(agent)
    
    async def send_command(
        self, cmd: AgentCommandRequest, tenant_id: str, user_id: str
    ) -> None:
        agent = self.get_agent(cmd.agent_id, tenant_id)
        if not agent:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Agent not found")
        payload = {
            "command_id": str(uuid.uuid4()),
            "agent_id": cmd.agent_id,
            "action": cmd.action,
            "params": cmd.params or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if not self.message_producer:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                "Message producer not configured")
        await self.message_producer.send(json.dumps(payload))
        self._log_agent_activity(
            agent.agent_id, tenant_id, "info",
            f"Command sent: {cmd.action}", {"user_id": user_id, "command_id": payload["command_id"]}
        )
        self._create_audit_log(
            tenant_id=tenant_id, user_id=user_id,
            action="send_command", entity_type="agent", entity_id=agent.agent_id,
            details={"action": cmd.action, "params": cmd.params}
        )
    
    def get_agent_logs(
        self, agent_id: str, tenant_id: str, skip: int = 0, limit: int = 100
    ) -> List[AgentLogResponse]:
        logs = (
            self.db.query(AgentLog)
            .filter(AgentLog.agent_id == agent_id,
                    AgentLog.tenant_id == tenant_id)
            .order_by(AgentLog.timestamp.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [AgentLogResponse.from_orm(l) for l in logs]
    
    def get_health_metrics(
        self, agent_id: str, tenant_id: str
    ) -> AgentHealthMetrics:
        # Most recent heartbeat
        latest = (
            self.db.query(func.max(Agent.last_heartbeat)).filter(
                Agent.agent_id == agent_id,
                Agent.tenant_id == tenant_id
            ).scalar()
        )
        # Count heartbeats in last 24h
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        count = (
            self.db.query(AgentLog)
            .filter(AgentLog.agent_id == agent_id,
                    AgentLog.level == 'heartbeat',
                    AgentLog.timestamp >= since)
            .count()
        )
        # Approximate interval
        interval = None
        if count > 1:
            # TODO: compute average diff
            interval = round(24 * 3600 / count)
        return AgentHealthMetrics(
            last_heartbeat=latest,
            heartbeat_count=count,
            average_interval_seconds=interval
        )
    
    def _generate_api_key(self) -> str:
        return uuid.uuid4().hex
    
    def _log_agent_activity(
        self, agent_id: str, tenant_id: str, level: str,
        message: str, metadata: Dict[str, Any]
    ) -> None:
        log = AgentLog(
            log_id=str(uuid.uuid4()),
            agent_id=agent_id,
            tenant_id=tenant_id,
            level=level,
            message=message,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(log)
        self.db.commit()
    
    def _create_audit_log(
        self, tenant_id: str, user_id: str,
        action: str, entity_type: str, entity_id: str,
        details: Dict[str, Any]
    ) -> None:
        audit = AuditLog(
            audit_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit)
        self.db.commit()
