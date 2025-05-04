#!/bin/bash

# Simple test script for the agent
# This script simulates a working endpoint for the agent to register with

# Step 1: Create a mock response file
cat > mock_response.json << EOF
{
  "agent_id": "00000000-0000-0000-0000-000000000001",
  "api_key": "mock-api-key-1234",
  "status": "registered"
}
EOF

# Step 2: Start a simple HTTP server on port 8081
echo "Starting a simple HTTP server on port 8081..."
# This uses Python's built-in HTTP server
python3 -m http.server 8081 &
SERVER_PID=$!

# Step 3: Wait for user to press Enter
echo ""
echo "The mock server is now running on port 8081."
echo "In a new terminal, you can run the agent with:"
echo "  python run_agent.py --server http://localhost:8081 --tenant mock-tenant"
echo ""
echo "Press Enter to stop the server..."
read

# Step 4: Clean up
kill $SERVER_PID
rm mock_response.json

echo "Server stopped."