import subprocess
import os
import sys
import logging
import platform
import time
from pathlib import Path

# Platform-specific imports
if platform.system() == "Windows":
    import winreg
    import ctypes
else:
    # Mock these modules for non-Windows platforms
    class WinregMock:
        def __getattr__(self, name):
            raise NotImplementedError("winreg is only available on Windows")
    
    class CtypesMock:
        class windll:
            class User32:
                def __getattr__(self, name):
                    raise NotImplementedError("ctypes.windll is only available on Windows")
    
    winreg = WinregMock()
    ctypes = CtypesMock()

logger = logging.getLogger("auto-login-manager")

def configure_windows_auto_login(username, password, domain=None):
    """Configure Windows auto-login for a service account"""
    try:
        # Set registry keys for auto-login
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, 
                          winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "AutoAdminLogon", 0, winreg.REG_SZ, "1")
            winreg.SetValueEx(key, "DefaultUserName", 0, winreg.REG_SZ, username)
            winreg.SetValueEx(key, "DefaultPassword", 0, winreg.REG_SZ, password)
            
            if domain:
                winreg.SetValueEx(key, "DefaultDomainName", 0, winreg.REG_SZ, domain)
        
        logger.info(f"Auto-login configured for user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error configuring auto-login: {e}")
        return False

def configure_session_persistence():
    """Configure session persistence settings to prevent locking and sleep"""
    try:
        # Disable screen saver
        reg_path = r"Control Panel\Desktop"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, 
                          winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, "ScreenSaveActive", 0, winreg.REG_SZ, "0")
            winreg.SetValueEx(key, "ScreenSaverIsSecure", 0, winreg.REG_SZ, "0")
        
        # Disable sleep/hibernate using powercfg
        try:
            subprocess.run(["powercfg", "/change", "standby-timeout-ac", "0"], 
                           check=True)
            subprocess.run(["powercfg", "/change", "hibernate-timeout-ac", "0"], 
                           check=True)
            subprocess.run(["powercfg", "/change", "monitor-timeout-ac", "0"], 
                           check=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Error configuring power settings: {e}")
        
        # Disable lock screen
        try:
            reg_path = r"SOFTWARE\Policies\Microsoft\Windows\Personalization"
            # Create key if it doesn't exist
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                winreg.CloseKey(key)
            except:
                pass
                
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, 
                              winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "NoLockScreen", 0, winreg.REG_DWORD, 1)
        except Exception as e:
            logger.warning(f"Error disabling lock screen: {e}")
        
        logger.info("Session persistence configured successfully")
        return True
    except Exception as e:
        logger.error(f"Error configuring session persistence: {e}")
        return False

def setup_agent_autostart():
    """Set agent to start automatically when user logs in"""
    try:
        # Create autostart entry in the current user's startup folder
        startup_folder = Path(os.path.expandvars("%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"))
        startup_folder.mkdir(parents=True, exist_ok=True)
        
        # Create a shortcut or batch file
        agent_path = os.path.abspath(sys.argv[0])
        startup_script = startup_folder / "automation_agent.bat"
        
        with open(startup_script, "w") as f:
            f.write(f'@echo off\n')
            f.write(f'cd "{os.path.dirname(agent_path)}"\n')
            f.write(f'"{sys.executable}" "{agent_path}"\n')
        
        logger.info(f"Agent autostart configured at: {startup_script}")
        return True
    except Exception as e:
        logger.error(f"Error setting up agent autostart: {e}")
        return False

class AutoLoginAgentManager:
    """Manager for agents with auto-login capabilities"""
    
    def __init__(self, config, api_client):
        self.config = config
        self.api_client = api_client
        self.logger = logging.getLogger("auto-login-manager")
    
    def setup_auto_login(self):
        """Set up auto-login for the agent if enabled"""
        try:
            # Check if auto-login is enabled in capabilities
            capabilities = self.config.get("capabilities", {}).get("system", {})
            if not capabilities.get("auto_login", {}).get("enabled", False):
                self.logger.info("Auto-login not enabled for this agent")
                return False
            
            # Get agent credentials from orchestrator
            credentials = self.api_client.get_agent_credentials()
            
            if not credentials:
                self.logger.error("No credentials available for auto-login")
                return False
            
            # Configure auto-login based on the platform
            if platform.system() == "Windows":
                # Setup Windows auto-login
                success = configure_windows_auto_login(
                    credentials["username"],
                    credentials["password"],
                    credentials.get("domain")
                )
                
                if success:
                    # Configure session persistence
                    configure_session_persistence()
                    
                    # Set up agent to start automatically
                    setup_agent_autostart()
                
                return success
            
            elif platform.system() == "Linux":
                # Linux auto-login would be implemented here
                self.logger.warning("Linux auto-login not yet implemented")
                return False
            
            elif platform.system() == "Darwin":
                # macOS auto-login would be implemented here
                self.logger.warning("macOS auto-login not yet implemented")
                return False
            
            else:
                self.logger.error(f"Unsupported platform for auto-login: {platform.system()}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error setting up auto-login: {e}")
            return False
    
    def update_session_status(self, status):
        """Update the agent's session status with the orchestrator"""
        try:
            # Send session status update to orchestrator
            self.api_client.update_session_status(status)
            return True
        except Exception as e:
            self.logger.error(f"Error updating session status: {e}")
            return False
    
    def check_session_status(self):
        """Check if the current session is still active"""
        try:
            # For Windows, check if screen is locked
            if platform.system() == "Windows":
                # Check if workstation is locked
                # Using Windows API calls
                try:
                    # This is a simplified check - a more reliable method would use the 
                    # Windows Session API, but this requires more complex code
                    user32 = ctypes.windll.User32
                    foreground_window = user32.GetForegroundWindow()
                    if foreground_window == 0:
                        # No foreground window - might be locked or at login screen
                        return "possibly_locked"
                    
                    # Additional check - try to get the title of the foreground window
                    title_len = user32.GetWindowTextLengthW(foreground_window) + 1
                    title = ctypes.create_unicode_buffer(title_len)
                    user32.GetWindowTextW(foreground_window, title, title_len)
                    
                    # If the foreground window is the lock screen
                    if "lock" in title.value.lower() or "logon" in title.value.lower():
                        return "locked"
                    
                    # Check for user activity
                    last_input_info = ctypes.wintypes.LASTINPUTINFO()
                    last_input_info.cbSize = ctypes.sizeof(last_input_info)
                    user32.GetLastInputInfo(ctypes.byref(last_input_info))
                    
                    # Get time since last input in milliseconds
                    millis_since_input = user32.GetTickCount() - last_input_info.dwTime
                    
                    # If no input for more than 5 minutes, consider it idle
                    if millis_since_input > 300000:  # 5 minutes in milliseconds
                        return "idle"
                    
                    return "active"
                except Exception as e:
                    self.logger.error(f"Error checking Windows session status: {e}")
                    return "unknown"
            
            elif platform.system() == "Linux":
                # Linux session status check
                # Would check for X session lock status or similar
                return "unknown"
            
            elif platform.system() == "Darwin":
                # macOS session status check
                return "unknown"
                
            return "unknown"
        except Exception as e:
            self.logger.error(f"Error checking session status: {e}")
            return "error"

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