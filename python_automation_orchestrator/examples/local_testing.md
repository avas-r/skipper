# Local Testing Examples

This document provides examples for local testing of the Python Automation Orchestrator and its agent.

## Testing with Local Server

For local testing, you can run both the server and the agent on the same machine.

### 1. Start the Orchestrator Server

```bash
# Navigate to the project directory
cd python_automation_orchestrator

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be accessible at `http://localhost:8000`.

### 2. Create a Test Tenant

If you're just starting, you'll need to create a tenant through the API:

```bash
# Create a tenant (adjust the JSON as needed)
curl -X POST "http://localhost:8000/api/v1/tenants/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Tenant", "subscription_tier": "standard", "settings": {}}'
```

Note down the `tenant_id` from the response, which you'll need to configure the agent.

### 3. Run the Agent for Local Testing

Now you can run the agent and connect it to your local server:

```bash
# Run the agent with your local server and tenant ID
python run_agent.py --server http://localhost:8000 --tenant YOUR_TENANT_ID
```

Replace `YOUR_TENANT_ID` with the actual tenant ID you obtained when creating the tenant.

## Testing with Mock Server

If you don't want to run the full orchestrator server, you can use a simple mock server for agent testing.

### 1. Create a Mock Server

Create a file named `mock_server.py` in the project root:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, UUID4
from typing import Dict, Any, Optional
import uvicorn
import uuid
from datetime import datetime

app = FastAPI(title="Mock Orchestrator API")

# Mock storage
agents = {}
heartbeats = {}

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
        "last_heartbeat": None
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
    
    return {
        "commands": [],
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

@app.get("/api/v1/agents/{agent_id}")
async def get_agent(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return agents[agent_id]

@app.get("/api/v1/agents")
async def list_agents():
    return list(agents.values())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 2. Run the Mock Server

```bash
python mock_server.py
```

### 3. Run the Agent with the Mock Server

```bash
python run_agent.py --server http://localhost:8081 --tenant mock-tenant-id
```

This will allow you to test agent registration and heartbeats without needing the full orchestrator infrastructure.

## Testing Agent with Simulated Jobs

You can extend the mock server to simulate job assignments and executions if needed. Add the following endpoints to the mock server:

```python
@app.get("/api/v1/agents/{agent_id}/jobs")
async def get_pending_jobs(agent_id: str):
    if agent_id not in agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    # Return a mock job every 5 heartbeats
    heartbeat_count = len(heartbeats.get(agent_id, []))
    if heartbeat_count > 0 and heartbeat_count % 5 == 0:
        return [{
            "execution_id": str(uuid.uuid4()),
            "job_id": str(uuid.uuid4()),
            "name": "Mock Test Job",
            "package_id": "mock-package-id",
            "parameters": {
                "test_param": "test_value"
            },
            "timeout_seconds": 3600,
            "assigned_at": datetime.utcnow().isoformat()
        }]
    
    return []
```

This will simulate job assignments every 5 heartbeats for testing agent job handling capabilities.