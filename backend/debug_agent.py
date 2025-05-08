#!/usr/bin/env python
"""
Debug script for agent API calls

This script helps debug API connectivity issues with the orchestrator server.
"""

import sys
import requests
import json
import uuid
import socket

def get_ip_address():
    """Get the local machine's IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())

def test_agent_registration(server_url, tenant_id):
    """Test agent registration with the orchestrator server"""
    print(f"Testing connection to {server_url}")
    print(f"Using tenant ID: {tenant_id}")
    
    # Create a session
    session = requests.Session()
    session.headers.update({
        "User-Agent": "OrchestratorAgent/1.0.0",
        "Content-Type": "application/json"
    })
    
    # Prepare registration data
    data = {
        "machine_id": str(uuid.uuid4()),
        "name": f"Debug-Agent-{socket.gethostname()}",
        "ip_address": get_ip_address(),
        "version": "1.0.0",
        # Ensure tenant_id is a valid UUID string and not accidentally turned into an integer
        "tenant_id": tenant_id
    }
    
    print("\nSending registration request with payload:")
    print(json.dumps(data, indent=2))
    
    # Try first with just the basic data
    url = f"{server_url}/api/v1/agents/register"
    try:
        response = session.post(url, json=data)
        print(f"\nResponse status code: {response.status_code}")
        try:
            print("Response content:")
            print(json.dumps(response.json(), indent=2))
        except:
            print("Raw response content:")
            print(response.text)
            
        if response.status_code != 200:
            print("\nTrying with different parameter formats...")
            
            # Try with tenant ID in header
            session.headers.update({
                "X-Tenant-ID": tenant_id
            })
            print("\nAdded X-Tenant-ID header, trying again...")
            response = session.post(url, json=data)
            print(f"Response status code: {response.status_code}")
            try:
                print("Response content:")
                print(json.dumps(response.json(), indent=2))
            except:
                print("Raw response content:")
                print(response.text)
    
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python debug_agent.py http://server-url tenant-id")
        sys.exit(1)
        
    server_url = sys.argv[1]
    tenant_id = sys.argv[2]
    
    test_agent_registration(server_url, tenant_id)