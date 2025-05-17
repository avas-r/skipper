#!/usr/bin/env python
"""
Quick fix script to ensure agent configuration has required directories set
"""

import os
import sys
import json
from pathlib import Path

def fix_agent_config():
    """Fix the agent configuration to include required directory settings"""
    
    # Find the config file
    config_paths = [
        os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json"),
        "agent_config.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.json")
    ]
    
    config_path = None
    for path in config_paths:
        if os.path.exists(path):
            config_path = path
            break
    
    if not config_path:
        print("No agent configuration file found!")
        return False
    
    print(f"Found config at: {config_path}")
    
    # Load existing config
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return False
    
    # Ensure settings section exists
    if 'settings' not in config:
        config['settings'] = {}
    
    # Get base directory
    base_dir = os.path.join(os.path.expanduser("~"), ".orchestrator")
    
    # Set default directory paths if not present
    if 'packages_dir' not in config['settings'] or config['settings']['packages_dir'] is None:
        config['settings']['packages_dir'] = os.path.join(base_dir, "packages")
        print(f"Set packages_dir to: {config['settings']['packages_dir']}")
    
    if 'working_dir' not in config['settings'] or config['settings']['working_dir'] is None:
        config['settings']['working_dir'] = os.path.join(base_dir, "work")
        print(f"Set working_dir to: {config['settings']['working_dir']}")
    
    # Ensure other essential settings
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
            print(f"Set {key} to: {value}")
    
    # Create directories if they don't exist
    for dir_key in ['packages_dir', 'working_dir']:
        dir_path = config['settings'].get(dir_key)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
    
    # Save updated config
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print("Configuration updated successfully!")
        
        # Show the final configuration
        print("\nFinal configuration:")
        print(json.dumps(config, indent=2))
        
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

if __name__ == "__main__":
    if fix_agent_config():
        print("\nConfiguration fixed! You can now run the agent with:")
        print("python run_agent.py --server <server-url> --tenant <tenant-id>")
    else:
        print("\nFailed to fix configuration.")
        sys.exit(1)