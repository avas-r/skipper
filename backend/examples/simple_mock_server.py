#!/usr/bin/env python3
"""
Simple Mock Server for Windows Agent Testing

This lightweight mock server simulates the orchestrator API
for testing Windows agent communication.
"""

from fastapi import FastAPI, HTTPException
import uvicorn
import uuid
import random
from datetime import datetime
from typing import Dict, Any, List

app = FastAPI(title="Mock Orchestrator for Windows Testing")

# In-memory storage
agents = {}
metrics_history = {}

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "server": "Mock Orchestrator",
        "time": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/agents/register")
async def register_agent(body: Dict[str, Any]):
    """Register a new agent"""
    agent_id = str(uuid.uuid4())
    api_key = f"test_key_{uuid.uuid4().hex[:8]}"
    
    # Store agent info
    agents[agent_id] = {
        "agent_id": agent_id,
        "machine_id": body.get("machine_id"),
        "name": body.get("name"),
        "ip_address": body.get("ip_address"),
        "tenant_id": body.get("tenant_id"),
        "registered_at": datetime.utcnow().isoformat(),
        "status": "online"
    }
    
    print(f"✓ Agent registered: {body.get('name')} ({agent_id})")
    print(f"  Machine ID: {body.get('machine_id')}")
    print(f"  IP Address: {body.get('ip_address')}")
    
    return {
        "agent_id": agent_id,
        "api_key": api_key,
        "status": "registered"
    }

@app.post("/api/v1/agents/{agent_id}/heartbeat")
async def heartbeat(agent_id: str, body: Dict[str, Any]):
    """Receive heartbeat from agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Update agent status
    agents[agent_id]["last_heartbeat"] = datetime.utcnow().isoformat()
    agents[agent_id]["status"] = "online"
    
    # Store metrics
    metrics = {
        "timestamp": body.get("timestamp"),
        "cpu_percent": body.get("cpu_percent"),
        "memory_percent": body.get("memory_percent"),
        "disk_percent": body.get("disk_percent"),
        "active_jobs": body.get("active_jobs")
    }
    
    if agent_id not in metrics_history:
        metrics_history[agent_id] = []
    
    metrics_history[agent_id].append(metrics)
    
    # Keep only last 10 metrics
    if len(metrics_history[agent_id]) > 10:
        metrics_history[agent_id] = metrics_history[agent_id][-10:]
    
    print(f"♥ Heartbeat from {agents[agent_id]['name']}: CPU={metrics['cpu_percent']}%, MEM={metrics['memory_percent']}%")
    
    return {
        "commands": [],
        "server_time": datetime.utcnow().isoformat()
    }

@app.get("/api/v1/agents/{agent_id}/jobs")
async def get_jobs(agent_id: str):
    """Get pending jobs for agent"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Simulate job assignment (1 in 5 chance)
    if random.randint(1, 5) == 1:
        job = {
            "execution_id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
            "name": "Test Windows Job",
            "package_id": "test-package",
            "parameters": {
                "message": "Hello from Windows test job",
                "duration": 10
            },
            "timeout_seconds": 300,
            "assigned_at": datetime.utcnow().isoformat()
        }
        
        print(f"→ Assigning job to {agents[agent_id]['name']}: {job['name']}")
        return [job]
    
    return []

@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get agent details"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return agents[agent_id]

@app.get("/api/v1/agents")
async def list_agents():
    """List all registered agents"""
    return list(agents.values())

@app.get("/api/v1/agents/{agent_id}/metrics")
async def get_agent_metrics(agent_id: str):
    """Get agent metrics history"""
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "metrics": metrics_history.get(agent_id, [])
    }

@app.get("/api/v1/dashboard")
async def dashboard():
    """Simple dashboard data"""
    online_agents = len([a for a in agents.values() if a["status"] == "online"])
    
    return {
        "total_agents": len(agents),
        "online_agents": online_agents,
        "offline_agents": len(agents) - online_agents,
        "server_time": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Starting Mock Orchestrator Server")
    print("📍 Server URL: http://localhost:8000")
    print("📄 API Docs: http://localhost:8000/docs")
    print("✓ Ready for Windows agent testing\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)