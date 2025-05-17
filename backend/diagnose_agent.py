#!/usr/bin/env python
"""
Agent Diagnostic Script

This script helps diagnose issues with the agent configuration and setup.
"""

import os
import sys
import json
import platform
from pathlib import Path

def check_config():
    """Check agent configuration"""
    print("Checking agent configuration...")
    print("-" * 40)
    
    # Look for config files
    config_paths = [
        os.path.join(os.path.expanduser("~"), ".orchestrator", "agent_config.json"),
        "agent_config.json",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.json")
    ]
    
    found_configs = []
    for path in config_paths:
        if os.path.exists(path):
            found_configs.append(path)
            print(f"✓ Found config: {path}")
        else:
            print(f"✗ Not found: {path}")
    
    if not found_configs:
        print("\nNo configuration files found!")
        return None
    
    # Load and check the first config
    config_path = found_configs[0]
    print(f"\nUsing config: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("\nConfiguration content:")
        print(json.dumps(config, indent=2))
        
        # Check for required settings
        print("\nChecking required settings:")
        required_settings = [
            ('server_url', None),
            ('tenant_id', None),
            ('settings.packages_dir', lambda v: v is not None),
            ('settings.working_dir', lambda v: v is not None),
            ('settings.log_level', lambda v: v in ['DEBUG', 'INFO', 'WARNING', 'ERROR']),
            ('settings.heartbeat_interval', lambda v: isinstance(v, int) and v > 0),
            ('settings.job_poll_interval', lambda v: isinstance(v, int) and v > 0)
        ]
        
        for key, validator in required_settings:
            value = get_nested_value(config, key)
            if value is None:
                print(f"✗ {key}: Not set")
            else:
                if validator is None or validator(value):
                    print(f"✓ {key}: {value}")
                else:
                    print(f"✗ {key}: Invalid value: {value}")
        
        return config
        
    except Exception as e:
        print(f"\nError loading config: {e}")
        return None

def get_nested_value(config, key):
    """Get nested value from config using dot notation"""
    parts = key.split('.')
    current = config
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current

def check_directories(config):
    """Check if required directories exist"""
    print("\nChecking directories...")
    print("-" * 40)
    
    if not config:
        print("No configuration available")
        return
    
    dirs_to_check = [
        ('settings.packages_dir', 'Packages directory'),
        ('settings.working_dir', 'Working directory')
    ]
    
    for key, name in dirs_to_check:
        path = get_nested_value(config, key)
        if path:
            if os.path.exists(path):
                print(f"✓ {name}: {path} (exists)")
            else:
                print(f"✗ {name}: {path} (does not exist)")
                try:
                    os.makedirs(path, exist_ok=True)
                    print(f"  Created directory: {path}")
                except Exception as e:
                    print(f"  Failed to create: {e}")
        else:
            print(f"✗ {name}: Not configured")

def check_environment():
    """Check Python environment"""
    print("\nChecking environment...")
    print("-" * 40)
    
    print(f"Python version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check for required modules
    print("\nChecking required modules:")
    modules = [
        'requests',
        'psutil',
        'cryptography',
        'schedule'
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module}: Installed")
        except ImportError:
            print(f"✗ {module}: Not installed")
    
    # Check optional modules
    print("\nChecking optional modules:")
    optional_modules = [
        ('pystray', 'System tray support'),
        ('PIL', 'Image support'),
        ('pyautogui', 'UI automation'),
        ('pywin32', 'Windows automation')
    ]
    
    for module, description in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module}: Installed ({description})")
        except ImportError:
            print(f"- {module}: Not installed ({description})")

def suggest_fixes(config):
    """Suggest fixes for common issues"""
    print("\nSuggested fixes:")
    print("-" * 40)
    
    if not config:
        print("1. Run: python windows_agent_setup.py --server <url> --tenant <id>")
        print("2. Or run: python fix_agent_config.py")
        return
    
    issues = []
    
    # Check for missing directories
    packages_dir = get_nested_value(config, 'settings.packages_dir')
    working_dir = get_nested_value(config, 'settings.working_dir')
    
    if not packages_dir or not working_dir:
        issues.append("Run: python fix_agent_config.py")
    
    # Check for missing server URL or tenant
    if not config.get('server_url') or not config.get('tenant_id'):
        issues.append("Register agent: python windows_agent_fix.py <server-url> <tenant-id>")
    
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("No issues detected. Agent should be ready to run.")
        print("\nRun agent with:")
        print(f"python run_agent.py --server {config.get('server_url')} --tenant {config.get('tenant_id')}")

if __name__ == "__main__":
    print("Agent Diagnostic Tool")
    print("=" * 40)
    
    config = check_config()
    check_directories(config)
    check_environment()
    suggest_fixes(config)
    
    print("\nDiagnostic complete.")