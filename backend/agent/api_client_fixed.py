# agent/api_client_fixed.py
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
        
        # Initialize headers
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with latest configuration"""
        # Add default headers
        self.session.headers.update({
            "User-Agent": f"OrchestratorAgent/{self._get_version()}",
            "X-Tenant-ID": self.tenant_id,
            "X-Machine-ID": self.config.get("machine_id"),
            "Content-Type": "application/json"
        })
        
        # Add agent ID header if available
        if self.agent_id:
            self.session.headers.update({"X-Agent-ID": self.agent_id})
        
        # Add authorization header if API key is available
        if self.api_key:
            logger.debug(f"Setting Authorization header with API key: Bearer {'*' * 20}")
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}"
            })
        else:
            logger.warning("No API key available for authentication")
    
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
                "hostname": socket.gethostname(),
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
                
                # Update API key if provided
                if "api_key" in result:
                    logger.info("Received API key from registration")
                    self.api_key = result["api_key"]
                    self.config.set("api_key", result["api_key"])
                    
                    # Save the configuration to persist the API key
                    self.config.save()
                    
                    # Update headers with new API key
                    self._update_headers()
                    logger.info("Updated authorization headers with new API key")
                else:
                    logger.warning("No API key received in registration response")
                    
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
                    "active_jobs": 0,  # Would be set by job manager
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Ensure proper request format
            data = {
                "status": "online",
                "metrics": metrics,
                "jobs": {}
            }
            
            logger.debug(f"Sending heartbeat to {url}")
            logger.debug(f"Headers: {dict(self.session.headers)}")
            
            response = self.session.post(url, json=data)
            
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
                "timestamp": datetime.utcnow().isoformat()
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
            
    def get_package(self, package_id, version=None, target_dir=None):
        """Download automation package
        
        Args:
            package_id (str): The package ID to download
            version (str, optional): The specific version to download
            target_dir (str, optional): Directory to save the package.
                Defaults to the configured packages_dir.
                
        Returns:
            str: Path to the downloaded package or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/packages/{package_id}/download"
            if version:
                url += f"?version={version}"
            
            target_dir = target_dir or self.config.get("settings.packages_dir") or "packages"
            os.makedirs(target_dir, exist_ok=True)
            
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
            
    def upload_job_log(self, execution_id, log_type, content):
        """Upload job execution log
        
        Args:
            execution_id (str): The job execution ID
            log_type (str): Type of log ('step', 'error', 'info', etc.)
            content (str): Log content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/v1/job-executions/{execution_id}/logs"
            
            data = {
                "log_type": log_type,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            response = self.session.post(url, json=data)
            
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Failed to upload log: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading log: {e}")
            return False
            
    def upload_screenshot(self, execution_id, screenshot_data, filename=None):
        """Upload job execution screenshot
        
        Args:
            execution_id (str): The job execution ID
            screenshot_data: Screenshot image data
            filename (str, optional): Filename for the screenshot
            
        Returns:
            str: URL of uploaded screenshot or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/job-executions/{execution_id}/screenshots"
            
            if filename is None:
                filename = f"screenshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.png"
            
            files = {
                'file': (filename, screenshot_data, 'image/png')
            }
            
            # Temporarily remove Content-Type header for multipart
            headers = dict(self.session.headers)
            headers.pop('Content-Type', None)
            
            response = self.session.post(url, files=files, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('url')
            else:
                logger.warning(f"Failed to upload screenshot: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error uploading screenshot: {e}")
            return None