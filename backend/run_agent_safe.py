#!/usr/bin/env python
"""
Safe Agent Runner Script

This script ensures the agent configuration has all required values before starting.
"""

import os
import sys
import json
import argparse
import urllib.parse
from pathlib import Path

def ensure_config_directories(config_path):
    """Ensure all required directories are configured"""
    
    # Load existing config
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Ensure settings section exists
    if 'settings' not in config:
        config['settings'] = {}
    
    # Get base directory
    base_dir = os.path.dirname(config_path)
    
    # Set default directory paths if not present
    changed = False
    
    if 'packages_dir' not in config['settings'] or config['settings']['packages_dir'] is None:
        config['settings']['packages_dir'] = os.path.join(base_dir, "packages")
        changed = True
    
    if 'working_dir' not in config['settings'] or config['settings']['working_dir'] is None:
        config['settings']['working_dir'] = os.path.join(base_dir, "work")
        changed = True
    
    # Set other defaults
    defaults = {
        'log_level': 'INFO',
        'heartbeat_interval': 30,
        'job_poll_interval': 15,
        'headless': False,
        'verify_ssl': True
    }
    
    for key, value in defaults.items():
        if key not in config['settings']:
            config['settings'][key] = value
            changed = True
    
    # Create directories
    for dir_key in ['packages_dir', 'working_dir']:
        dir_path = config['settings'].get(dir_key)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
    
    # Save if changed
    if changed:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Updated configuration at: {config_path}")
    
    return config

def parse_args():
    """Parse command line arguments and validate them"""
    parser = argparse.ArgumentParser(description='Run the automation agent safely')
    parser.add_argument('--server', required=True, help='Orchestrator server URL')
    parser.add_argument('--tenant', required=True, help='Tenant ID')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--config', help='Path to agent configuration file')
    
    args = parser.parse_args()
    
    # Validate server URL
    try:
        result = urllib.parse.urlparse(args.server)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL")
    except Exception:
        print(f"ERROR: '{args.server}' is not a valid URL.")
        sys.exit(1)
    
    return args

if __name__ == "__main__":
    # Parse arguments
    args = parse_args()
    
    # Determine config path
    if args.config:
        config_path = args.config
    else:
        config_path = os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json")
    
    print(f"Using configuration at: {config_path}")
    
    # Ensure config has all required directories
    config = ensure_config_directories(config_path)
    
    # Update config with command line arguments
    config['server_url'] = args.server
    config['tenant_id'] = args.tenant
    
    if args.headless:
        config['settings']['headless'] = True
        os.environ["AGENT_HEADLESS"] = "1"
    
    # Save updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Now run the agent
    os.environ["AGENT_CONFIG_PATH"] = config_path
    
    from agent.agent_main import main
    
    print("Starting agent...")
    exit_code = main()
    sys.exit(exit_code)