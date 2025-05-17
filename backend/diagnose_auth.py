#!/usr/bin/env python
"""
Diagnose Agent Authentication Issues

Run this to diagnose why the agent is getting 401 authentication errors.
"""

import os
import sys
import json
import requests
from pathlib import Path

def check_config():
    """Check agent configuration for authentication details"""
    print("Checking agent configuration...")
    print("-" * 40)
    
    # Find config
    config_paths = [
        os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json"),
        os.path.join(os.path.dirname(__file__), "agent_config.json"),
        "agent_config.json"
    ]
    
    config_path = None
    config = None
    
    for path in config_paths:
        if os.path.exists(path):
            config_path = path
            with open(path, 'r') as f:
                config = json.load(f)
            break
    
    if not config:
        print("❌ No configuration file found!")
        return None
    
    print(f"✓ Found config at: {config_path}")
    print(f"  Server URL: {config.get('server_url')}")
    print(f"  Tenant ID: {config.get('tenant_id')}")
    print(f"  Agent ID: {config.get('agent_id')}")
    print(f"  API Key: {'Present' if config.get('api_key') else 'Missing!'}")
    
    return config

def test_registration(config):
    """Test agent registration endpoint"""
    print("\nTesting registration endpoint...")
    print("-" * 40)
    
    url = f"{config['server_url']}/api/v1/agents/register"
    data = {
        "machine_id": config.get("machine_id", "test-machine"),
        "name": config.get("name", "Test Agent"),
        "tenant_id": config.get("tenant_id"),
        "version": "1.0.0",
        "capabilities": {"packages": ["python"], "system": {"platform": "windows"}}
    }
    
    try:
        response = requests.post(url, json=data, timeout=5)
        print(f"Registration response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Registration successful!")
            print(f"  Agent ID: {result.get('agent_id')}")
            print(f"  API Key provided: {'Yes' if result.get('api_key') else 'No!'}")
            
            if not result.get('api_key'):
                print("❌ Server did not provide API key!")
            
            return result
        else:
            print(f"❌ Registration failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return None

def test_heartbeat(config):
    """Test heartbeat with current credentials"""
    print("\nTesting heartbeat with saved credentials...")
    print("-" * 40)
    
    if not config.get('agent_id') or not config.get('api_key'):
        print("❌ Missing agent_id or api_key - cannot test heartbeat")
        return False
    
    url = f"{config['server_url']}/api/v1/agents/{config['agent_id']}/heartbeat"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json"
    }
    data = {
        "status": "online",
        "metrics": {
            "cpu_percent": 50.0,
            "memory_percent": 60.0,
            "disk_percent": 70.0,
            "active_jobs": 0,
            "timestamp": "2025-01-17T12:00:00Z"
        }
    }
    
    print(f"URL: {url}")
    print(f"Authorization: Bearer {'*' * 20}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=5)
        print(f"Response: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Heartbeat successful!")
            return True
        else:
            print(f"❌ Heartbeat failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during heartbeat: {e}")
        return False

def main():
    print("Agent Authentication Diagnostic Tool")
    print("=" * 40)
    
    # Step 1: Check configuration
    config = check_config()
    if not config:
        print("\nPlease run the windows_agent_setup.py script first.")
        return
    
    # Step 2: Check if API key is missing
    if not config.get('api_key'):
        print("\n⚠️ API key is missing from configuration!")
        
        # Try registration
        result = test_registration(config)
        
        if result and result.get('api_key'):
            print("\n✓ Got new API key from registration!")
            print("Saving to configuration...")
            
            config['agent_id'] = result['agent_id']
            config['api_key'] = result['api_key']
            
            # Save updated config
            config_path = os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print("✓ Configuration updated!")
    
    # Step 3: Test heartbeat
    if config.get('api_key'):
        test_heartbeat(config)
    
    # Step 4: Provide solution
    print("\nDiagnosis Complete")
    print("=" * 40)
    
    if config.get('api_key'):
        print("\nAgent has API key. If authentication is still failing:")
        print("1. Check if the server is running")
        print("2. Verify the API key hasn't expired on the server")
        print("3. Check server logs for more details")
    else:
        print("\nAgent needs to be registered to get an API key.")
        print("Run: python windows_agent_fix.py <server-url> <tenant-id>")

if __name__ == "__main__":
    main()