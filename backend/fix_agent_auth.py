#!/usr/bin/env python
"""
Fix agent authentication issues

This script ensures the agent properly saves and loads the API key after registration.
"""

import os
import sys
import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("auth-fix")

def fix_agent_auth():
    """Fix authentication issues in agent configuration"""
    
    # Find config file
    config_paths = [
        os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json"),
        "agent_config.json"
    ]
    
    config_path = None
    for path in config_paths:
        if os.path.exists(path):
            config_path = path
            break
    
    if not config_path:
        logger.error("No agent configuration file found!")
        return False
    
    logger.info(f"Found config at: {config_path}")
    
    # Load config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False
    
    # Check current state
    logger.info("\nCurrent configuration:")
    logger.info(f"Server URL: {config.get('server_url')}")
    logger.info(f"Tenant ID: {config.get('tenant_id')}")
    logger.info(f"Agent ID: {config.get('agent_id')}")
    logger.info(f"API Key: {'*' * 20 if config.get('api_key') else 'Not set'}")
    
    # If API key is missing, inform user to re-register
    if not config.get('api_key'):
        logger.warning("\nAPI key is missing from configuration!")
        logger.warning("The agent needs to re-register to get a new API key.")
        logger.warning("\nRun the following command to re-register:")
        logger.warning(f"python windows_agent_fix.py {config.get('server_url')} {config.get('tenant_id')}")
        
        # Clear agent_id to force re-registration
        if config.get('agent_id'):
            logger.info("\nClearing agent_id to force re-registration...")
            config.pop('agent_id', None)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration updated. Agent will re-register on next run.")
    else:
        logger.info("\nAPI key is properly configured.")
        logger.info("If you're still getting authentication errors, try:")
        logger.info("1. Check if the server is reachable")
        logger.info("2. Verify the API key is valid on the server")
        logger.info("3. Re-register the agent if needed")
    
    return True

def check_server_auth(config):
    """Test authentication with the server"""
    import requests
    
    server_url = config.get('server_url')
    agent_id = config.get('agent_id')
    api_key = config.get('api_key')
    
    if not all([server_url, agent_id, api_key]):
        logger.warning("Missing required configuration for auth test")
        return False
    
    try:
        # Test heartbeat endpoint
        url = f"{server_url}/api/v1/agents/{agent_id}/heartbeat"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "status": "online",
            "metrics": {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "active_jobs": 0,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        logger.info(f"\nTesting authentication with: {url}")
        response = requests.post(url, json=data, headers=headers, timeout=5)
        
        if response.status_code == 200:
            logger.info("✓ Authentication successful!")
            return True
        else:
            logger.error(f"✗ Authentication failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing authentication: {e}")
        return False

if __name__ == "__main__":
    logger.info("Agent Authentication Fix Tool")
    logger.info("=" * 30)
    
    if fix_agent_auth():
        # Try to load config and test auth
        config_path = os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if config.get('api_key'):
                logger.info("\nTesting server authentication...")
                if check_server_auth(config):
                    logger.info("\n✓ Agent authentication is working properly!")
                else:
                    logger.info("\n✗ Authentication test failed. Please check the logs above.")
        
        logger.info("\nFix complete.")
    else:
        logger.error("\nFix failed.")
        sys.exit(1)