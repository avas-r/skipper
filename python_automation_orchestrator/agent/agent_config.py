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
import pystray
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from threading import Thread, Lock
from pathlib import Path
import urllib3

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

class AgentConfig:
    """Configuration manager for the agent"""
    
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), 
            ".orchestrator", 
            "agent_config.json"
        )
        self.config = self._load_config()
        

    def _get_machine_id(self):
        """Generate a unique machine ID"""
        try:
            if platform.system() == "Windows":
                # Get Windows machine GUID
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                key = winreg.OpenKey(registry, r"SOFTWARE\Microsoft\Cryptography")
                value, _ = winreg.QueryValueEx(key, "MachineGuid")
                return value
            elif platform.system() == "Linux":
                # Try to get machine-id
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            elif platform.system() == "Darwin":
                # Get macOS hardware UUID
                output = subprocess.check_output(["system_profiler", "SPHardwareDataType"])
                for line in output.decode().split('\n'):
                    if "Hardware UUID" in line:
                        return line.split(":")[1].strip()
        except Exception as e:
            logger.warning(f"Could not determine machine ID: {e}")
        
        # Fallback: Generate a UUID based on hostname and MAC address
        mac = uuid.getnode()
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{socket.gethostname()}-{mac}"))
    
    def _get_default_capabilities(self):
        """Determine agent capabilities based on installed packages"""
        capabilities = ["python"]
        
        # Check for common installed packages
        try:
            import pyautogui
            capabilities.append("ui_automation")
        except ImportError:
            pass
            
        try:
            import selenium
            capabilities.append("web_automation")
        except ImportError:
            pass
            
        try:
            import pandas
            capabilities.append("data_processing")
        except ImportError:
            pass
            
        try:
            import openpyxl
            capabilities.append("excel_automation")
        except ImportError:
            pass
            
        try:
            import pytesseract
            capabilities.append("ocr")
        except ImportError:
            pass
            
        try:
            import cv2
            capabilities.append("computer_vision")
        except ImportError:
            pass
            
        # Add system capabilities
        sys_info = {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cores": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            # Add session information
            "session_type": "standard",
            "display_available": True,
            "auto_login": {
                "enabled": False,
                "configured": False
            }
        }
        
        capabilities.append(f"system_{platform.system().lower()}")
        
        return {
            "packages": capabilities,
            "system": sys_info
        }
        
    def save(self):
        """Save current configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
            
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        self.save()
        
    def update(self, new_config):
        """Update multiple configuration values"""
        self.config.update(new_config)
        self.save()
        
    def update_for_auto_login(self):
        """Update configuration to enable auto-login mode"""
        # Update capabilities to include auto-login information
        auto_login_settings = {
            "session_type": "auto_login_service_account",
            "display_available": True,
            "auto_login": {
                "enabled": True,
                "configured": False,
                "session_persistence": {
                    "disable_screensaver": True,
                    "disable_sleep": True,
                    "keep_session_active": True
                },
                "recovery": {
                    "restart_on_crash": True,
                    "auto_restart_agent": True,
                    "max_restart_attempts": 3
                }
            }
        }
        
        # Update capabilities
        if "capabilities" in self.config:
            if "system" in self.config["capabilities"]:
                self.config["capabilities"]["system"].update(auto_login_settings)
            else:
                self.config["capabilities"]["system"] = auto_login_settings
        else:
            self.config["capabilities"] = {
                "system": auto_login_settings
            }
        
        # Update tags
        if "tags" in self.config:
            if "auto_login" not in self.config["tags"]:
                self.config["tags"].append("auto_login")
        else:
            self.config["tags"] = ["auto_login"]
        
        # Set auto-login setup flag
        self.config["setup_auto_login"] = True
        self.save()
        
        return True

    def get_encryption_key(self):
        """Get the encryption key for secure storage
        
        Returns:
            Fernet: The cryptography.fernet.Fernet object for encryption
        """
        key = self.get("encryption_key")
        if not key:
            key = Fernet.generate_key().decode()
            self.set("encryption_key", key)
        return Fernet(key.encode())