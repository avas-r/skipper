#!/usr/bin/env python
"""
Windows Agent Fix

This script corrects the agent configuration and directly registers with the orchestrator.
"""

import sys
import os
import requests
import json
import uuid
import socket
import configparser
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent-fix")

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

def generate_machine_id():
    """Generate a unique machine ID"""
    try:
        import platform
        if platform.system() == "Windows":
            # Get Windows machine GUID
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(registry, r"SOFTWARE\\Microsoft\\Cryptography")
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                return value
            except:
                pass
                
        # Fallback: Generate UUID based on hostname and MAC address
        mac = uuid.getnode()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{socket.gethostname()}-{mac}"))
        
    except Exception as e:
        logger.warning(f"Error generating machine ID: {e}")
        # Last resort: random UUID
        return str(uuid.uuid4())

def register_agent_directly(server_url, tenant_id):
    """Register the agent directly with the orchestrator server"""
    logger.info(f"Registering agent with {server_url}")
    logger.info(f"Using tenant ID: {tenant_id}")
    
    # Generate a machine ID
    machine_id = generate_machine_id()
    logger.info(f"Generated machine ID: {machine_id}")
    
    # Prepare registration data
    data = {
        "machine_id": machine_id,
        "name": f"Agent-{socket.gethostname()}",
        "ip_address": get_ip_address(),
        "version": "1.0.0",
        "tenant_id": tenant_id,
        "capabilities": {
            "packages": ["python"],
            "system": {
                "platform": "windows",
                "display_available": True,
                "auto_login": {
                    "enabled": False
                }
            }
        },
        "tags": ["windows", "auto-configured"]
    }
    
    # Build request URL
    url = f"{server_url}/api/v1/agents/register"
    
    try:
        # Send registration request
        response = requests.post(url, json=data)
        
        # Check if successful
        if response.status_code == 200:
            result = response.json()
            logger.info("Agent registered successfully!")
            logger.info(f"Agent ID: {result.get('agent_id')}")
            
            # Save configuration
            home_dir = str(Path.home())
            config_dir = os.path.join(home_dir, ".orchestrator")
            os.makedirs(config_dir, exist_ok=True)
            
            config_path = os.path.join(config_dir, "agent_config.json")
            
            config = {
                "agent_id": result.get("agent_id"),
                "api_key": result.get("api_key"),
                "server_url": server_url,
                "tenant_id": tenant_id,
                "machine_id": machine_id,
                "name": f"Agent-{socket.gethostname()}",
                "settings": {
                    "log_level": "INFO",
                    "heartbeat_interval": 30,
                    "job_poll_interval": 15,
                    "headless": False
                }
            }
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
                
            logger.info(f"Configuration saved to {config_path}")
            logger.info("\nYou can now run the agent with:")
            logger.info(f"python run_agent.py")
            
            return True
        else:
            logger.error(f"Registration failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python windows_agent_fix.py http://server-url tenant-id")
        sys.exit(1)
        
    server_url = sys.argv[1]
    tenant_id = sys.argv[2]
    
    success = register_agent_directly(server_url, tenant_id)
    if not success:
        sys.exit(1)