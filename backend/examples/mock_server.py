#!/usr/bin/env python
"""
Mock Orchestrator Server

This script provides a simple mock server to test agent functionality
without needing to run the full orchestrator stack.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, UUID4
from typing import Dict, Any, Optional, List
import uvicorn
import uuid
from datetime import datetime

app = FastAPI(title="Mock Orchestrator API")

# Mock storage
agents = {}
heartbeats = {}
jobs = {}

class AgentRegistration(BaseModel):
    machine_id: str
    name: str
    ip_address: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    tags: Optional[list] = None
    service_account_id: Optional[UUID4] = None
    session_type: Optional[str] = None
    auto_login_enabled: Optional[bool] = False

class Heartbeat(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_jobs: int
    timestamp: str
    session_status: Optional[str] = None

class JobStatus(BaseModel):
    status: str
    timestamp: str
    error_message: Optional[str] = None
    results: Optional[Dict[str, Any]] = None

class SessionStatus(BaseModel):
    status: str
    timestamp: str

class JobStep(BaseModel):
    step_id: str
    description: str
    status: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None
    screenshot: Optional[str] = None

@app.post("/api/v1/agents/register")
async def register_agent(agent: AgentRegistration):
    agent_id = str(uuid.uuid4())
    api_key = f"mock_api_key_{agent_id[:8]}"
    
    agents[agent_id] = {
        "agent_id": agent_id,
        "api_key": api_key,
        "machine_id": agent.machine_id,
        "name": agent.name,
        "status": "online",
        "registered_at": datetime.utcnow().isoformat(),
        "last_heartbeat": None,
        "capabilities": agent.capabilities,
        "tags": agent.tags or []
    }
    
    print(f"Agent registered: {agent.name} ({agent_id})")
    
    return {
        "agent_id": agent_id,
        "api_key": api_key,
        "status": "registered"
    }

@app.post("/api/v1/agents/{agent_id}/heartbeat")
async def agent_heartbeat(agent_id: str, heartbeat: Heartbeat):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    agents[agent_id]["last_heartbeat"] = heartbeat.timestamp
    agents[agent_id]["status"] = "online"
    
    heartbeats.setdefault(agent_id, []).append(heartbeat.dict())
    
    # Limit stored heartbeats to last 10
    if len(heartbeats[agent_id]) > 10:
        heartbeats[agent_id] = heartbeats[agent_id][-10:]
    
    print(f"Heartbeat from agent {agent_id}: CPU {heartbeat.cpu_percent}%, Memory {heartbeat.memory_percent}%")
    
    # Create a mock job assignment every 5 heartbeats
    commands = []
    heartbeat_count = len(heartbeats[agent_id])
    if heartbeat_count > 0 and heartbeat_count % 5 == 0:
        print(f"Assigning a mock job to agent {agent_id}")
        
        # Add a mock command to run a task
        commands.append({
            "command": "test_heartbeat",
            "parameters": {
                "message": f"This is heartbeat #{heartbeat_count}"
            }
        })
    
    return {
        "commands": commands,
        "server_time": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/agents/{agent_id}/credentials")
async def get_agent_credentials(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "username": "mock_user",
        "password": "mock_password",
        "domain": "mock_domain"
    }

@app.get("/api/v1/agents/{agent_id}/jobs")
async def get_pending_jobs(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Create a mock job every 5 heartbeats
    heartbeat_count = len(heartbeats.get(agent_id, []))
    if heartbeat_count > 0 and heartbeat_count % 5 == 0:
        execution_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        job = {
            "execution_id": execution_id,
            "job_id": job_id,
            "name": "Mock Test Job",
            "package_id": "mock-package-id",
            "parameters": {
                "test_param": "test_value",
                "heartbeat_count": heartbeat_count
            },
            "timeout_seconds": 3600,
            "assigned_at": datetime.utcnow().isoformat()
        }
        
        # Store job in jobs dict
        jobs[execution_id] = job
        
        return [job]
    
    return []

@app.put("/api/v1/job-executions/{execution_id}/status")
async def update_job_status(execution_id: str, status_update: JobStatus):
    if execution_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job execution {execution_id} not found")
    
    jobs[execution_id]["status"] = status_update.status
    jobs[execution_id]["updated_at"] = status_update.timestamp
    
    if status_update.error_message:
        jobs[execution_id]["error_message"] = status_update.error_message
        
    if status_update.results:
        jobs[execution_id]["results"] = status_update.results
    
    print(f"Job {execution_id} status updated to {status_update.status}")
    
    return {
        "status": "updated",
        "execution_id": execution_id
    }

@app.post("/api/v1/job-executions/{execution_id}/steps")
async def log_job_step(execution_id: str, step: JobStep):
    if execution_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job execution {execution_id} not found")
    
    if "steps" not in jobs[execution_id]:
        jobs[execution_id]["steps"] = []
    
    jobs[execution_id]["steps"].append(step.dict())
    
    print(f"Job {execution_id} step logged: {step.description} ({step.status})")
    
    return {
        "status": "logged",
        "execution_id": execution_id,
        "step_id": step.step_id
    }

@app.put("/api/v1/agents/{agent_id}/session-status")
async def update_session_status(agent_id: str, status: SessionStatus):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    agents[agent_id]["session_status"] = status.status
    agents[agent_id]["session_updated_at"] = status.timestamp
    
    print(f"Agent {agent_id} session status updated to {status.status}")
    
    return {
        "status": "updated",
        "agent_id": agent_id
    }

@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agents[agent_id]

@app.get("/api/v1/agents")
async def list_agents():
    return list(agents.values())

@app.get("/api/v1/jobs")
async def list_jobs():
    return list(jobs.values())

@app.get("/")
async def root():
    return {
        "name": "Mock Orchestrator API",
        "version": "1.0.0",
        "description": "A simple mock server for testing Python Automation Orchestrator agents",
        "endpoints": [
            "/api/v1/agents/register",
            "/api/v1/agents/{agent_id}/heartbeat",
            "/api/v1/agents/{agent_id}/jobs",
            "/api/v1/agents/{agent_id}/credentials",
            "/api/v1/job-executions/{execution_id}/status",
            "/api/v1/job-executions/{execution_id}/steps"
        ]
    }

if __name__ == "__main__":
    # Use port 8081 to avoid conflicts with uvicorn app server
    PORT = 8081
    print(f"Starting Mock Orchestrator Server on http://localhost:{PORT}")
    print(f"Visit http://localhost:{PORT}/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=PORT)