#!/usr/bin/env python
"""
Simple Mock Server

A minimal HTTP server that responds to agent requests for testing.
"""

import http.server
import socketserver
import json
import uuid
from datetime import datetime
import threading
import time

# Port to listen on
PORT = 8081

# In-memory storage
agents = {}
heartbeats = {}

class MockServerHandler(http.server.BaseHTTPRequestHandler):
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.end_headers()
        
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/":
            # Root path - show info
            self._set_headers()
            response = {
                "name": "Simple Mock Orchestrator",
                "version": "1.0.0",
                "endpoints": [
                    "/api/v1/agents/register",
                    "/api/v1/agents/{agent_id}/heartbeat"
                ]
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path.startswith("/api/v1/agents/") and "/heartbeat" in self.path:
            # Heartbeat endpoint
            agent_id = self.path.split("/")[4]
            self._set_headers()
            response = {
                "commands": [],
                "server_time": datetime.utcnow().isoformat()
            }
            print(f"Received heartbeat from agent {agent_id}")
            self.wfile.write(json.dumps(response).encode())
        elif self.path.startswith("/api/v1/agents/") and "/jobs" in self.path:
            # Jobs endpoint - return empty list
            self._set_headers()
            response = []
            self.wfile.write(json.dumps(response).encode())
        elif self.path.startswith("/api/v1/agents/") and "/credentials" in self.path:
            # Credentials endpoint
            self._set_headers()
            response = {
                "username": "mock_user",
                "password": "mock_password",
                "domain": "mock_domain"
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            # Unknown endpoint
            self._set_headers()
            response = {"error": "Unknown endpoint"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data)
        except:
            data = {}
        
        if self.path == "/api/v1/agents/register":
            # Agent registration
            agent_id = str(uuid.uuid4())
            api_key = f"mock_api_key_{agent_id[:8]}"
            
            # Store agent info
            agents[agent_id] = {
                "agent_id": agent_id,
                "name": data.get("name", "Unknown Agent"),
                "api_key": api_key,
                "registered_at": datetime.utcnow().isoformat()
            }
            
            # Return response
            self._set_headers()
            response = {
                "agent_id": agent_id,
                "api_key": api_key,
                "status": "registered"
            }
            print(f"Agent registered: {data.get('name', 'Unknown Agent')} ({agent_id})")
            self.wfile.write(json.dumps(response).encode())
        elif self.path.startswith("/api/v1/agents/") and "/heartbeat" in self.path:
            # Heartbeat endpoint
            agent_id = self.path.split("/")[4]
            
            # Store heartbeat
            if agent_id in agents:
                heartbeats.setdefault(agent_id, []).append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                })
                
                # Keep only last 10 heartbeats
                if len(heartbeats[agent_id]) > 10:
                    heartbeats[agent_id] = heartbeats[agent_id][-10:]
            
            # Return response
            self._set_headers()
            response = {
                "commands": [],
                "server_time": datetime.utcnow().isoformat()
            }
            
            # Every 5 heartbeats, send a test command
            count = len(heartbeats.get(agent_id, []))
            if count > 0 and count % 5 == 0:
                response["commands"].append({
                    "command": "test",
                    "parameters": {
                        "message": f"Test command #{count // 5}"
                    }
                })
                print(f"Sending test command to agent {agent_id}")
            
            print(f"Received heartbeat from agent {agent_id}")
            self.wfile.write(json.dumps(response).encode())
        else:
            # Unknown endpoint
            self._set_headers()
            response = {"error": "Unknown endpoint"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_PUT(self):
        """Handle PUT requests"""
        self._set_headers()
        response = {"status": "updated"}
        self.wfile.write(json.dumps(response).encode())
        
    def log_message(self, format, *args):
        """Override to disable logging to stderr"""
        return

def run_server():
    """Run the HTTP server"""
    handler = MockServerHandler
    
    # Try to create server, with port reuse
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        print(f"Visit http://localhost:{PORT} for server info")
        print("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped")

if __name__ == "__main__":
    run_server()