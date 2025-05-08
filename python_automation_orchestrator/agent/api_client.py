"""
API Client for Orchestrator Server Communication

This module handles all communication between the agent and the orchestration server,
including:
- Agent registration and authentication
- Heartbeat signals
- Job retrieval and status updates
- Package downloads
- Credential and configuration retrieval
"""

import os
import json
import logging
import requests
import urllib3
import platform
import socket
import uuid
from datetime import datetime
import psutil
import time
import zipfile
import tempfile
from pathlib import Path
from io import BytesIO

logger = logging.getLogger("orchestrator-agent")

class ApiClient:
    """Client for communicating with the orchestrator API"""
    
    def __init__(self, config):
        """Initialize the API client
        
        Args:
            config: The agent configuration object (AgentConfig instance)
        """
        self.config = config
        self.base_url = config.get("server_url")
        self.api_key = config.get("api_key")
        self.tenant_id = config.get("tenant_id")
        self.agent_id = config.get("agent_id")
        self.session = requests.Session()
        
        # Configure session
        if config.get("verify_ssl", True):
            if config.get("certificate_path"):
                self.session.verify = config.get("certificate_path")
            else:
                self.session.verify = True
        else:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.session.verify = False
            
        # Add default headers
        self.session.headers.update({
            "User-Agent": f"OrchestratorAgent/{self._get_version()}",
            "X-Agent-ID": self.agent_id,
            "X-Tenant-ID": self.tenant_id,
            "X-Machine-ID": config.get("machine_id"),
            "Content-Type": "application/json"
        })
        
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
    
    def _get_version(self):
        """Get agent version
        
        Returns:
            str: The agent version
        """
        return "1.0.0"  # Would be pulled from package version in real implementation
    
    def _get_ip_address(self):
        """Get the agent's IP address
        
        Returns:
            str: The agent's IP address
        """
        try:
            # Create a socket to determine which interface would be used to connect to the internet
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # This doesn't actually establish a connection
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logger.warning(f"Unable to determine IP address: {e}")
            return socket.gethostbyname(socket.gethostname())
    
    def register_agent(self):
        """Register agent with orchestrator
        
        Returns:
            dict: The registration response or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/agents/register"
            
            data = {
                "machine_id": self.config.get("machine_id"),
                "name": self.config.get("name"),
                "ip_address": self._get_ip_address(),
                "version": self._get_version(),
                "capabilities": self.config.get("capabilities"),
                "tags": self.config.get("tags", []),
                "service_account_id": self.config.get("service_account_id"),
                "session_type": self.config.get("capabilities", {}).get("system", {}).get("session_type", "standard"),
                "auto_login_enabled": self.config.get("capabilities", {}).get("system", {}).get("auto_login", {}).get("enabled", False),
                "tenant_id": self.tenant_id
            }
            
            response = self.session.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Update agent_id if provided
                if "agent_id" in result:
                    self.agent_id = result["agent_id"]
                    self.config.set("agent_id", result["agent_id"])
                    self.session.headers.update({"X-Agent-ID": result["agent_id"]})
                
                # Update API key if provided
                if "api_key" in result:
                    self.api_key = result["api_key"]
                    self.config.set("api_key", result["api_key"])
                    self.session.headers.update({"Authorization": f"Bearer {result['api_key']}"})
                    
                return result
            else:
                logger.error(f"Agent registration failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error during agent registration: {e}")
            return None
            
    def send_heartbeat(self, metrics=None):
        """Send heartbeat to orchestrator
        
        Args:
            metrics (dict, optional): Custom metrics to include in the heartbeat.
                Defaults to None (auto-generated metrics).
                
        Returns:
            dict: The heartbeat response or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/agents/{self.agent_id}/heartbeat"
            
            # Collect basic system metrics
            if metrics is None:
                metrics = {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_percent": psutil.disk_usage("/").percent,
                    "active_jobs": 0,  # Would be set by agent manager
                    "timestamp": datetime.utcnow().isoformat(),
                    "session_status": self.config.get("session_status", "unknown"),
                    "tenant_id": self.tenant_id  # Add tenant_id to help the server
                }
                
            # Always include tenant_id in heartbeat data
            if "tenant_id" not in metrics:
                metrics["tenant_id"] = self.tenant_id
                
            response = self.session.post(url, json=metrics)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Heartbeat failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return None
            
    def get_pending_jobs(self):
        """Get pending jobs from orchestrator
        
        Returns:
            list: List of pending jobs or empty list if failed
        """
        try:
            url = f"{self.base_url}/api/v1/agents/{self.agent_id}/jobs"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get pending jobs: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting pending jobs: {e}")
            return []
            
    def update_job_status(self, execution_id, status, error=None, results=None):
        """Update job execution status
        
        Args:
            execution_id (str): The job execution ID
            status (str): The new status ('running', 'completed', 'failed', etc.)
            error (str, optional): Error message in case of failure. Defaults to None.
            results (dict, optional): Job results in case of success. Defaults to None.
            
        Returns:
            dict: The status update response or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/job-executions/{execution_id}/status"
            
            data = {
                "status": status,
                "timestamp": datetime.now(datetime.UTC).isoformat()
            }
            
            if error:
                data["error_message"] = error
                
            if results:
                data["results"] = results
                
            response = self.session.put(url, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to update job status: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating job status: {e}")
            return None
            
    def get_package(self, package_id, target_dir=None):
        """Download automation package
        
        Args:
            package_id (str): The package ID to download
            target_dir (str, optional): Directory to save the package.
                Defaults to the configured packages_dir.
                
        Returns:
            str: Path to the downloaded package or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/packages/{package_id}/download"
            
            target_dir = target_dir or self.config.get("packages_dir")
            package_path = os.path.join(target_dir, f"{package_id}")
            
            response = self.session.get(url, stream=True)
            
            if response.status_code == 200:
                # Create package directory
                os.makedirs(package_path, exist_ok=True)
                
                # Extract the package (assuming it's a zip)
                with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
                    zip_ref.extractall(package_path)
                    
                return package_path
            else:
                logger.warning(f"Failed to download package: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading package: {e}")
            return None
            
    def get_asset(self, asset_id):
        """Get an asset (credential or configuration)
        
        Args:
            asset_id (str): The asset ID to retrieve
            
        Returns:
            dict: The asset data or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/assets/{asset_id}/value"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get asset: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting asset: {e}")
            return None
            
    def upload_package(self, package_path, package_info):
        """Upload automation package
        
        Args:
            package_path (str): Path to the package zip file
            package_info (dict): Package metadata
                
        Returns:
            dict: The uploaded package information or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/packages/upload"
            
            # Prepare the form data
            files = {
                'file': ('package.zip', open(package_path, 'rb'), 'application/zip')
            }
            
            # Add metadata fields
            data = {}
            if 'name' in package_info:
                data['name'] = package_info['name']
            if 'description' in package_info:
                data['description'] = package_info['description']
            if 'version' in package_info:
                data['version'] = package_info['version']
            if 'entry_point' in package_info:
                data['entry_point'] = package_info['entry_point']
            if 'tags' in package_info:
                data['tags'] = ','.join(package_info['tags']) if isinstance(package_info['tags'], list) else package_info['tags']
                
            # Upload the package
            response = self.session.post(url, files=files, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to upload package: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading package: {e}")
            return None
            
    def get_job_execution(self, execution_id):
        """Get information about a job execution
        
        Args:
            execution_id (str): The execution ID
                
        Returns:
            dict: The execution information or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/job-executions/{execution_id}"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get execution: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting execution: {e}")
            return None
            
    def log_step(self, execution_id, step_id, description, status, data=None, take_screenshot=False):
        """Log a job execution step
        
        Args:
            execution_id (str): The job execution ID
            step_id (str): The step ID
            description (str): Step description
            status (str): Step status ('running', 'completed', 'failed')
            data (dict, optional): Additional step data. Defaults to None.
            take_screenshot (bool, optional): Whether to take and upload a screenshot.
                Defaults to False.
                
        Returns:
            dict: The log response or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/job-executions/{execution_id}/steps"
            
            step_data = {
                "step_id": step_id,
                "description": description,
                "status": status,
                "timestamp": datetime.now(datetime.UTC).isoformat()
            }
            
            if data:
                step_data["data"] = data
                
            # Capture screenshot if requested and we're not in headless mode
            screenshot_data = None
            if take_screenshot and not self.config.get("settings", {}).get("headless", False):
                try:
                    # Import only when needed and check if import is successful
                    try:
                        import pyautogui
                        import base64
                        from io import BytesIO
                        from PIL import Image
                        
                        screenshot = pyautogui.screenshot()
                        buffered = BytesIO()
                        screenshot.save(buffered, format="PNG")
                        screenshot_data = base64.b64encode(buffered.getvalue()).decode('utf-8')
                        step_data["screenshot"] = screenshot_data
                    except ImportError as import_err:
                        logger.warning(f"Screenshot module not available: {import_err}")
                except Exception as screenshot_error:
                    logger.warning(f"Failed to capture screenshot: {screenshot_error}")
                
            response = self.session.post(url, json=step_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to log step: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error logging step: {e}")
            return None

    def get_agent_credentials(self):
        """Get credentials for the agent's service account"""
        try:
            url = f"{self.base_url}/api/v1/agents/{self.agent_id}/credentials"
            
            response = self.session.get(url)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get agent credentials: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting agent credentials: {e}")
            return None
    
    def update_session_status(self, status):
        """Update the agent's session status"""
        try:
            url = f"{self.base_url}/api/v1/agents/{self.agent_id}/session-status"
            
            data = {
                "status": status,
                "timestamp": datetime.now(datetime.UTC).isoformat()
            }
            
            response = self.session.put(url, json=data)
            
            if response.status_code == 200:
                # Update local config
                self.config.set("session_status", status)
                return response.json()
            else:
                logger.warning(f"Failed to update session status: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating session status: {e}")
            return None        

