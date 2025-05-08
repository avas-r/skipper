# Python Automation Orchestrator Examples

This directory contains examples to help you test and understand the Python Automation Orchestrator.

## Simple Mock Server

The simplest way to test the agent is with the `simple_mock_server.py` script, which provides a basic HTTP server that responds to agent requests:

```bash
# Run the simple mock server
python examples/simple_mock_server.py
```

This will start a server on port 8081 that can handle agent registration and heartbeats.

In a new terminal, you can run the agent:

```bash
# Run the agent against the mock server
python run_agent.py --server http://localhost:8081 --tenant mock-tenant
```

The simple mock server:
- Registers new agents and returns an agent ID
- Processes heartbeats
- Returns empty job lists
- Provides mock credentials

## Full Mock Server

For more advanced testing, use the `mock_server.py` script, which provides a more complete mock server using FastAPI:

```bash
# Run the full mock server
python examples/mock_server.py
```

This requires FastAPI and Uvicorn to be installed:

```bash
pip install fastapi uvicorn
```

The full mock server provides:
- Agent registration and management
- Heartbeat processing
- Mock job assignments
- Job status updates
- Simulated commands
- API documentation at /docs

## Agent Test Script

For the simplest possible test, you can use the `agent_test.sh` script:

```bash
# Run the agent test script
./examples/agent_test.sh
```

This script:
1. Creates a mock response file
2. Starts a simple HTTP server
3. Waits for you to test the agent
4. Cleans up when done

## Running the Real System

To run the full orchestrator system:

1. Start the orchestrator server:
```bash
uvicorn app.main:app --reload
```

2. Create a test tenant through the API:
```bash
curl -X POST "http://localhost:8000/api/v1/tenants/" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Tenant", "subscription_tier": "standard", "settings": {}}'
```

3. Run the agent with your tenant ID:
```bash
python run_agent.py --server http://localhost:8000 --tenant YOUR_TENANT_ID
```

Refer to `local_testing.md` for more detailed instructions.