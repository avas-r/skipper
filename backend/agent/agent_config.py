# agent/agent_config.py
import os
import sys
import json
import uuid
import logging
import platform
import socket
import psutil
from datetime import datetime
from cryptography.fernet import Fernet
from pathlib import Path

logger = logging.getLogger("orchestrator-agent")

class AgentConfig:
    """Configuration manager for the agent"""
    
    def __init__(self, config_path=None):
        # Parse command line arguments
        self.args = self._parse_args()
        
        self.config_path = config_path or os.path.join(
            os.path.expanduser("~"), 
            ".orchestrator", 
            "agent_config.json"
        )
        self.config = self._load_config()
        
        # Apply command line arguments to config
        if self.args:
            self._apply_args_to_config()
            
    def _parse_args(self):
        """Parse command line arguments"""
        args = {}
        i = 1
        while i < len(sys.argv):
            if sys.argv[i].startswith('--'):
                key = sys.argv[i][2:]
                if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith('--'):
                    args[key] = sys.argv[i + 1]
                    i += 2
                else:
                    args[key] = True
                    i += 1
            else:
                i += 1
        
        # Check for headless mode
        if 'headless' in args or '--headless' in sys.argv:
            args['headless'] = True
            
        return args
        
    def _apply_args_to_config(self):
        """Apply command line arguments to configuration"""
        if 'server' in self.args:
            self.config['server_url'] = self.args['server']
        if 'tenant' in self.args:
            self.config['tenant_id'] = self.args['tenant']
        if 'headless' in self.args and self.args['headless']:
            self.config['settings']['headless'] = True
                
    def _load_config(self):
        """Load configuration from file or create a default one"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading configuration: {e}")
        
        # Create default configuration
        default_config = {
            "agent_id": str(uuid.uuid4()),
            "server_url": "https://localhost:8000",
            "tenant_id": "",
            "name": f"Agent-{socket.gethostname()}",
            "machine_id": self._get_machine_id(),
            "capabilities": self._get_default_capabilities(),
            "tags": ["default"],
            "settings": {
                "log_level": "INFO",
                "heartbeat_interval": 30,
                "job_poll_interval": 15,
                "update_check_interval": 3600,
                "headless": True,
                "packages_dir": os.path.join(os.path.expanduser("~"), ".orchestrator", "packages"),
                "working_dir": os.path.join(os.path.expanduser("~"), ".orchestrator", "workspaces"),
                "workspace_dir": os.path.join(os.path.expanduser("~"), ".orchestrator", "workspaces")
            }
        }
        
        return default_config

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
        if "." in key:
            parts = key.split(".")
            current = self.config
            for part in parts:
                if part in current:
                    current = current[part]
                else:
                    return default
            return current
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set configuration value"""
        if "." in key:
            parts = key.split(".")
            current = self.config
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
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