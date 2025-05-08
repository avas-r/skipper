import os
import sys
import json
import uuid
import time
import logging
import platform
import requests
import subprocess
import threading
import tempfile
import ssl
import socket
import base64
import certifi
import psutil
import zipfile
import schedule
from io import BytesIO
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from threading import Thread, Lock
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib3

# Try to import optional UI dependencies
try:
    import pystray
    from PIL import Image
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False

# Try to import PyAutoGUI only if we need it
PYAUTOGUI_AVAILABLE = False
try:
    # Only attempt to import if not headless
    headless = '--headless' in sys.argv or os.environ.get('AGENT_HEADLESS') == '1'
    if not headless:
        import pyautogui
        PYAUTOGUI_AVAILABLE = True
except ImportError:
    pass  # PyAutoGUI not available

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("orchestrator-agent")

# Import local modules
from agent.agent_config import AgentConfig
from agent.api_client import ApiClient
from agent.auto_login_manager import AutoLoginAgentManager, configure_windows_auto_login, configure_session_persistence, setup_agent_autostart
from agent.package_manager import PackageManager
from agent.job_executor import JobExecutor

def send_heartbeat_periodically(api_client, interval_seconds):
    """Send heartbeat to orchestrator periodically"""
    while True:
        try:
            # Get metrics
            metrics = {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage("/").percent,
                "active_jobs": 0,  # Would be set by job manager
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send heartbeat
            api_client.send_heartbeat(metrics)
            
            # Sleep until next interval
            time.sleep(interval_seconds)
        except Exception as e:
            logger.error(f"Error in heartbeat thread: {e}")
            time.sleep(interval_seconds * 2)  # Wait longer on error

def poll_for_jobs(api_client, config, package_manager=None, job_executor=None):
    """Poll for pending jobs from orchestrator"""
    try:
        # Get pending jobs
        pending_jobs = api_client.get_pending_jobs()
        
        if not pending_jobs:
            return
            
        logger.info(f"Received {len(pending_jobs)} pending jobs")
        
        # Process each job
        for job in pending_jobs:
            job_type = job.get("job_type", "standard")
            
            if job_type == "package_execution":
                # Handle package execution
                if package_manager:
                    package_id = job.get("package_id")
                    parameters = job.get("parameters", {})
                    execution_id = job.get("execution_id")
                    
                    if not package_id:
                        logger.error(f"Missing package_id in job: {job}")
                        continue
                        
                    logger.info(f"Executing package {package_id} with execution ID {execution_id}")
                    
                    # Execute in a separate thread to not block the polling
                    thread = Thread(
                        target=package_manager.execute_package,
                        args=(package_id, parameters, execution_id),
                        daemon=True
                    )
                    thread.start()
                else:
                    logger.warning("Package execution requested but package manager not available")
            else:
                # Handle standard job execution
                if job_executor:
                    logger.info(f"Executing job: {job.get('job_id')}")
                    job_executor.execute_job(job)
                else:
                    logger.warning("Job execution requested but job executor not available")
    except Exception as e:
        logger.error(f"Error polling for jobs: {e}")
        import traceback
        logger.error(traceback.format_exc())

def setup_system_tray(config):
    """Set up system tray icon for agent"""
    if not PYSTRAY_AVAILABLE:
        logger.warning("Pystray not available. System tray icon will not be shown.")
        return None
        
    try:
        # Create a simple icon - in real implementation, would use a proper icon
        icon_image = Image.new('RGB', (64, 64), color = 'blue')
        
        # Define menu items
        def on_quit(icon, item):
            icon.stop()
            os._exit(0)
            
        def on_status(icon, item):
            # Show a temporary notification with agent status
            icon.notify(f"Agent ID: {config.get('agent_id')}\nStatus: Running", "Agent Status")
            
        def on_sync(icon, item):
            # Manual sync with orchestrator
            icon.notify("Synchronizing with orchestrator...", "Agent")
            
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Status", on_status),
            pystray.MenuItem("Synchronize Now", on_sync),
            pystray.MenuItem("Quit", on_quit)
        )
        
        # Create icon
        icon = pystray.Icon("orchestrator-agent", icon_image, "Orchestrator Agent", menu)
        
        # Run icon in a separate thread
        icon_thread = Thread(target=icon.run, daemon=True)
        icon_thread.start()
        
        return icon
    except Exception as e:
        logger.error(f"Error setting up system tray: {e}")
        return None

def monitor_session_status(auto_login_manager):
    """Monitor and report session status"""
    while True:
        try:
            # Check current session status
            status = auto_login_manager.check_session_status()
            
            # Update status with orchestrator
            auto_login_manager.update_session_status(status)
            
            # Sleep for a while before checking again
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Error in session monitoring: {e}")
            time.sleep(300)  # Wait 5 minutes on error

def main():
    """Main entry point for agent with auto-login support"""
    try:
        # Initialize configuration
        config = AgentConfig()
        
        # Set up logging based on configuration
        logger.setLevel(config.get("log_level", "INFO"))
        
        # Create API client
        api_client = ApiClient(config)
        
        # Create auto-login manager
        auto_login_manager = AutoLoginAgentManager(config, api_client)
        
        # Check if we need to set up auto-login
        if config.get("setup_auto_login", False):
            logger.info("Setting up auto-login...")
            if auto_login_manager.setup_auto_login():
                logger.info("Auto-login setup completed successfully")
                # Update config to indicate auto-login is set up
                config.set("setup_auto_login", False)
                config.set("auto_login_configured", True)
            else:
                logger.error("Failed to set up auto-login")
        
        # Register agent with orchestrator
        try:
            registration_result = api_client.register_agent()
            
            if not registration_result:
                logger.error("Failed to register agent with orchestrator")
                return 1
                
            logger.info(f"Agent registered successfully with ID: {config.get('agent_id')}")
        except Exception as e:
            logger.error(f"Error registering agent: {e}")
            return 1
        
        # Start heartbeat thread
        heartbeat_thread = Thread(
            target=send_heartbeat_periodically, 
            args=(api_client, config.get("heartbeat_interval", 30)),
            daemon=True
        )
        heartbeat_thread.start()
        
        # Create package manager
        package_manager = PackageManager(api_client, config)
        
        # Create job executor
        job_executor = JobExecutor(api_client, config)
        
        # Start job polling thread
        job_thread = Thread(
            target=poll_for_jobs,
            args=(api_client, config, package_manager, job_executor),
            daemon=True
        )
        job_thread.start()
        
        # If auto-login is configured, start session monitor
        if config.get("auto_login_configured", False):
            session_thread = Thread(
                target=monitor_session_status,
                args=(auto_login_manager,),
                daemon=True
            )
            session_thread.start()
        
        # Create system tray icon if in attended mode
        if not config.get("headless", False):
            setup_system_tray(config)
            
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        return 1

if __name__ == "__main__":
    # Check if auto-login configuration is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--configure-auto-login":
        # If running with this flag, update the configuration for auto-login
        config = AgentConfig()
        config.update_for_auto_login()
        logger.info("Agent configured for auto-login. Run the agent normally to set up auto-login.")
        sys.exit(0)
        
    # Regular execution
    sys.exit(main())