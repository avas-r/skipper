#!/usr/bin/env python
"""
Windows Agent Setup Script

This script helps set up a Windows machine to run as an automation agent.
It handles configuration, registration, and initial setup.
"""

import os
import sys
import json
import socket
import uuid
import platform
import subprocess
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent-setup")

def get_machine_id():
    """Generate a unique machine ID for Windows"""
    try:
        # Try to get Windows machine GUID from registry
        import winreg
        registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key = winreg.OpenKey(registry, r"SOFTWARE\\Microsoft\\Cryptography")
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        return value
    except:
        # Fallback to MAC address-based UUID
        mac = uuid.getnode()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{socket.gethostname()}-{mac}"))

def get_system_info():
    """Get system information for the Windows machine"""
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "machine": platform.machine(),
        "display_available": True  # Windows typically has display
    }
    
    # Check if running in RDP session
    try:
        session_name = os.environ.get('SESSIONNAME', '')
        info['session_type'] = 'rdp' if 'RDP' in session_name else 'console'
    except:
        info['session_type'] = 'unknown'
    
    return info

def get_capabilities():
    """Determine agent capabilities based on installed packages"""
    capabilities = {
        "packages": ["python"],
        "system": {
            "platform": "windows",
            "display_available": True,
            "auto_login": {
                "enabled": False,
                "type": "windows"
            }
        }
    }
    
    # Check for PyAutoGUI
    try:
        import pyautogui
        capabilities["packages"].append("pyautogui")
        capabilities["system"]["automation_ui"] = True
    except ImportError:
        capabilities["system"]["automation_ui"] = False
    
    # Check for Selenium
    try:
        import selenium
        capabilities["packages"].append("selenium")
        capabilities["system"]["web_automation"] = True
    except ImportError:
        capabilities["system"]["web_automation"] = False
    
    # Check for Office automation
    try:
        import win32com.client
        capabilities["packages"].append("pywin32")
        capabilities["system"]["office_automation"] = True
    except ImportError:
        capabilities["system"]["office_automation"] = False
    
    return capabilities

def create_agent_config(server_url, tenant_id, config_dir=None):
    """Create agent configuration file"""
    if config_dir is None:
        config_dir = os.path.join(Path.home(), ".orchestrator")
    
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "agent_config.json")
    
    machine_id = get_machine_id()
    system_info = get_system_info()
    capabilities = get_capabilities()
    
    config = {
        "server_url": server_url,
        "tenant_id": tenant_id,
        "machine_id": machine_id,
        "name": f"Windows-{system_info['hostname']}",
        "version": "1.0.0",
        "capabilities": capabilities,
        "tags": ["windows", system_info['processor'], f"python-{system_info['python_version']}"],
        "settings": {
            "log_level": "INFO",
            "heartbeat_interval": 30,
            "job_poll_interval": 15,
            "headless": False,
            "packages_dir": os.path.join(config_dir, "packages"),
            "working_dir": os.path.join(config_dir, "work"),
            "verify_ssl": True
        }
    }
    
    # Save configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Configuration saved to: {config_path}")
    return config_path

def install_dependencies():
    """Install required Python packages"""
    required_packages = [
        "requests",
        "psutil",
        "cryptography",
        "pystray",  # For system tray
        "pillow",   # For icon generation
        "pyautogui",  # For UI automation
        "schedule"  # For scheduling
    ]
    
    logger.info("Installing required packages...")
    
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            logger.info(f"✓ Installed {package}")
        except subprocess.CalledProcessError:
            logger.warning(f"✗ Failed to install {package}")

def create_startup_batch():
    """Create a batch file for easy agent startup"""
    batch_content = """@echo off
REM Windows Agent Startup Script
REM This script starts the automation agent

echo Starting Automation Agent...
cd /d "%~dp0"
python run_agent.py
pause
"""
    
    batch_path = "start_agent.bat"
    with open(batch_path, 'w') as f:
        f.write(batch_content)
    
    logger.info(f"Startup script created: {batch_path}")
    return batch_path

def setup_windows_service():
    """Create Windows service for agent (requires admin privileges)"""
    service_script = """import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

class AgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SkipperAgent"
    _svc_display_name_ = "Skipper Automation Agent"
    _svc_description_ = "Runs the Skipper automation agent as a Windows service"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        
    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        self.main()
        
    def main(self):
        # Import and run the agent
        from agent.agent_main import main
        main()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AgentService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AgentService)
"""
    
    service_path = "agent_service.py"
    with open(service_path, 'w') as f:
        f.write(service_script)
    
    logger.info(f"Windows service script created: {service_path}")
    logger.info("To install as service (requires admin): python agent_service.py install")
    logger.info("To start service: python agent_service.py start")
    
    return service_path

def main():
    parser = argparse.ArgumentParser(description='Set up Windows automation agent')
    parser.add_argument('--server', required=True, help='Orchestrator server URL')
    parser.add_argument('--tenant', required=True, help='Tenant ID')
    parser.add_argument('--install-deps', action='store_true', help='Install Python dependencies')
    parser.add_argument('--create-service', action='store_true', help='Create Windows service script')
    parser.add_argument('--config-dir', help='Configuration directory (default: ~/.orchestrator)')
    
    args = parser.parse_args()
    
    print("Windows Agent Setup")
    print("==================")
    print()
    
    # Install dependencies if requested
    if args.install_deps:
        install_dependencies()
        print()
    
    # Create configuration
    config_path = create_agent_config(args.server, args.tenant, args.config_dir)
    print()
    
    # Create startup batch file
    batch_path = create_startup_batch()
    print()
    
    # Create service script if requested
    if args.create_service:
        service_path = setup_windows_service()
        print()
    
    # Display system information
    print("System Information:")
    print("------------------")
    info = get_system_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    print()
    
    # Display capabilities
    print("Agent Capabilities:")
    print("------------------")
    capabilities = get_capabilities()
    print(json.dumps(capabilities, indent=2))
    print()
    
    print("Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Register the agent:")
    print(f"   python windows_agent_fix.py {args.server} {args.tenant}")
    print()
    print("2. Run the agent:")
    print("   python run_agent.py")
    print("   OR")
    print(f"   {batch_path}")
    print()
    
    if args.create_service:
        print("3. Optional - Install as Windows service (requires admin):")
        print("   python agent_service.py install")
        print("   python agent_service.py start")

if __name__ == "__main__":
    main()