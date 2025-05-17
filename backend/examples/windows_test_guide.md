# Windows Agent Communication Testing Guide

## Overview
This guide helps you test communication between a Windows agent and the Skipper orchestrator server.

## Prerequisites
- Python 3.7+ installed on Windows
- Access to orchestrator server (either local or remote)
- Valid tenant ID

## Step 1: Quick Start with Mock Server

For immediate testing without full infrastructure:

```python
# simple_mock_server.py
from fastapi import FastAPI
import uvicorn
import uuid
from datetime import datetime

app = FastAPI()

@app.post("/api/v1/agents/register")
async def register_agent(body: dict):
    return {
        "agent_id": str(uuid.uuid4()),
        "api_key": f"test_key_{uuid.uuid4().hex[:8]}",
        "status": "registered"
    }

@app.post("/api/v1/agents/{agent_id}/heartbeat")
async def heartbeat(agent_id: str, body: dict):
    print(f"Heartbeat from {agent_id}: CPU={body.get('cpu_percent')}%")
    return {"commands": [], "server_time": datetime.utcnow().isoformat()}

@app.get("/api/v1/agents/{agent_id}/jobs")
async def get_jobs(agent_id: str):
    return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run the mock server:
```bash
python simple_mock_server.py
```

## Step 2: Register Windows Agent

```bash
# Register the agent
python windows_agent_fix.py http://localhost:8000 test-tenant

# Or for remote server
python windows_agent_fix.py https://your-server.com your-tenant-id
```

## Step 3: Run the Agent

```bash
# Start the agent
python run_agent.py --server http://localhost:8000 --tenant test-tenant

# For headless mode (no GUI)
python run_agent.py --server http://localhost:8000 --tenant test-tenant --headless
```

## Step 4: Monitor Communication

### Check Agent Logs
```bash
# View agent.log in the current directory
type agent.log
```

### Expected Log Entries
```
INFO - Registering agent with orchestrator...
INFO - Agent registered successfully
INFO - Starting heartbeat thread...
INFO - Agent running. Press Ctrl+C to stop.
```

### Verify Server Receives Data
- Registration creates new agent record
- Heartbeats received every 30 seconds
- Job polling occurs every 15 seconds

## Step 5: Troubleshooting

### Common Windows Issues

1. **Firewall Blocking**
   - Add Python to Windows Defender Firewall exceptions
   - Allow outbound connections on port 8000

2. **SSL Certificate Errors**
   ```bash
   # Disable SSL verification for testing
   python run_agent.py --server https://server --tenant id --no-verify-ssl
   ```

3. **Permission Errors**
   - Run command prompt as Administrator
   - Check write permissions for log files

4. **Network Connectivity**
   ```bash
   # Test connection
   ping your-server.com
   curl http://your-server:8000/docs
   ```

## Step 6: Advanced Testing

### Test with Job Execution
Add a test job endpoint to mock server:

```python
@app.get("/api/v1/agents/{agent_id}/jobs")
async def get_jobs(agent_id: str):
    # Return a test job every 3rd call
    if random.randint(1, 3) == 1:
        return [{
            "execution_id": str(uuid.uuid4()),
            "job_id": "test-job",
            "name": "Test Windows Job",
            "package_id": "test-package",
            "parameters": {"message": "Hello from Windows"},
            "timeout_seconds": 300
        }]
    return []
```

### Monitor System Resources
The agent reports system metrics in heartbeats:
- CPU usage
- Memory usage  
- Disk usage
- Active jobs count

## Security Considerations

1. **API Keys**: Store securely in agent_config.json
2. **SSL/TLS**: Use HTTPS in production
3. **Firewall**: Restrict to necessary ports only
4. **Service Account**: Run agent with limited privileges

## Example Test Script

```bash
# test_communication.bat
@echo off
echo Starting communication test...

REM Start mock server in background
start /B python simple_mock_server.py

REM Wait for server to start
timeout /t 3

REM Register agent
python windows_agent_fix.py http://localhost:8000 test-tenant

REM Run agent for 60 seconds
timeout /t 60 python run_agent.py --server http://localhost:8000 --tenant test-tenant

echo Test completed. Check agent.log for results.
```

## Next Steps

1. Test with real orchestrator server
2. Configure auto-start on Windows boot
3. Set up monitoring and alerts
4. Implement custom job packages
5. Test error recovery scenarios