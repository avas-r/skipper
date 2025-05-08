#!/usr/bin/env python
"""
Agent Runner Script

This script runs the automation agent in a clean way, suppressing warnings from
optional dependencies that might not be installed.
"""

import os
import sys
import warnings
import argparse
import urllib.parse

# Suppress warnings from missing optional dependencies
warnings.filterwarnings("ignore", ".*")

def parse_args():
    """Parse command line arguments and validate them"""
    parser = argparse.ArgumentParser(description='Run the automation agent')
    parser.add_argument('--server', required=True, help='Orchestrator server URL')
    parser.add_argument('--tenant', required=True, help='Tenant ID')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Validate server URL
    if args.server == 'https://your-orchestrator-server':
        print("ERROR: Please provide a real server URL, not the placeholder.")
        print("Example: python run_agent.py --server https://orchestrator.example.com --tenant your-tenant-id")
        sys.exit(1)
    
    # Validate tenant ID
    if args.tenant == 'your-tenant-id':
        print("ERROR: Please provide a real tenant ID, not the placeholder.")
        print("Example: python run_agent.py --server https://orchestrator.example.com --tenant abc123")
        sys.exit(1)
        
    # Try to parse the URL to validate it
    try:
        result = urllib.parse.urlparse(args.server)
        if not all([result.scheme, result.netloc]):
            raise ValueError("Invalid URL")
    except Exception:
        print(f"ERROR: '{args.server}' is not a valid URL. Please provide a valid server URL.")
        print("Example: python run_agent.py --server https://orchestrator.example.com --tenant your-tenant-id")
        sys.exit(1)
    
    return args

if __name__ == "__main__":
    # Parse and validate arguments
    args = parse_args()
    
    # Set an environment variable to indicate headless mode if needed
    if args.headless:
        os.environ["AGENT_HEADLESS"] = "1"
    
    # Import and run the agent
    from agent.agent_main import main
    
    # Pass command-line arguments to the agent
    exit_code = main()
    sys.exit(exit_code)