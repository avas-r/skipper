"""
Package Manager for Automation Packages

This module handles automation package management:
- Downloading and caching packages
- Version management and updates
- Dependency resolution
- Package validation
- Package execution
"""

import os
import json
import time
import shutil
import hashlib
import logging
import zipfile
import tempfile
import subprocess
import sys
import importlib.util
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("orchestrator-agent")

class PackageManager:
    """Manager for automation packages"""
    
    def __init__(self, api_client, config):
        """Initialize the package manager
        
        Args:
            api_client: The API client for communicating with the orchestrator
            config: The agent configuration
        """
        self.api_client = api_client
        self.config = config
        self.packages_dir = config.get("packages_dir")
        self.active_executions = {}
        
        # Ensure packages directory exists
        os.makedirs(self.packages_dir, exist_ok=True)
        
        # Load package metadata cache
        self.metadata_cache = {}
        self._load_metadata_cache()
        
    def _load_metadata_cache(self):
        """Load package metadata cache from disk"""
        cache_path = os.path.join(self.packages_dir, "metadata_cache.json")
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    self.metadata_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load package metadata cache: {e}")
                self.metadata_cache = {}
    
    def _save_metadata_cache(self):
        """Save package metadata cache to disk"""
        cache_path = os.path.join(self.packages_dir, "metadata_cache.json")
        try:
            with open(cache_path, "w") as f:
                json.dump(self.metadata_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save package metadata cache: {e}")
    
    def get_package(self, package_id, version=None, force_download=False):
        """Get a package by ID and optionally version
        
        Args:
            package_id (str): The package ID
            version (str, optional): Specific version to retrieve. If None, gets latest.
            force_download (bool, optional): Whether to force download even if cached.
                
        Returns:
            str: Path to the package directory or None if failed
        """
        # Check if package is already cached and up to date
        package_dir = os.path.join(self.packages_dir, package_id)
        package_metadata_path = os.path.join(package_dir, "package.json")
        
        # If not forcing download and package exists
        if not force_download and os.path.exists(package_dir) and os.path.exists(package_metadata_path):
            try:
                # Check if specific version is requested
                if version:
                    with open(package_metadata_path, "r") as f:
                        metadata = json.load(f)
                    
                    if metadata.get("version") == version:
                        logger.info(f"Using cached package {package_id} version {version}")
                        return package_dir
                else:
                    # No specific version, check if we need to check for updates
                    last_check = self.metadata_cache.get(package_id, {}).get("last_check", 0)
                    cache_ttl = self.config.get("package_cache_ttl", 3600)  # 1 hour default
                    
                    # If cache is still valid
                    if time.time() - last_check < cache_ttl:
                        logger.info(f"Using cached package {package_id}")
                        return package_dir
            except Exception as e:
                logger.warning(f"Error checking package cache: {e}")
        
        # Download the package
        logger.info(f"Downloading package {package_id}" + (f" version {version}" if version else ""))
        download_path = self.api_client.get_package(package_id, version=version)
        
        if not download_path:
            logger.error(f"Failed to download package {package_id}")
            return None
            
        # Update cache metadata
        try:
            with open(os.path.join(download_path, "package.json"), "r") as f:
                metadata = json.load(f)
                
            self.metadata_cache[package_id] = {
                "last_check": time.time(),
                "version": metadata.get("version"),
                "download_time": datetime.utcnow().isoformat()
            }
            
            self._save_metadata_cache()
        except Exception as e:
            logger.warning(f"Failed to update package metadata cache: {e}")
            
        return download_path
    
    def install_dependencies(self, package_dir):
        """Install Python dependencies for a package
        
        Args:
            package_dir (str): Path to the package directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check for requirements.txt
        requirements_file = os.path.join(package_dir, "requirements.txt")
        if not os.path.exists(requirements_file):
            # No requirements file, nothing to do
            return True
            
        try:
            # Install requirements using pip
            logger.info(f"Installing dependencies from {requirements_file}")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file],
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.debug(f"Dependency installation output: {result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            logger.error(f"Pip output: {e.output}")
            return False
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return False
    
    def verify_package(self, package_dir):
        """Verify package integrity and security
        
        Args:
            package_dir (str): Path to the package directory
            
        Returns:
            tuple: (is_valid, issues) where is_valid is a boolean and issues is a list
        """
        issues = []
        
        # Check for package.json
        package_json_path = os.path.join(package_dir, "package.json")
        if not os.path.exists(package_json_path):
            issues.append("Missing package.json")
            return False, issues
            
        # Load and validate package.json
        try:
            with open(package_json_path, "r") as f:
                metadata = json.load(f)
                
            # Check required fields
            required_fields = ["name", "version", "main"]
            for field in required_fields:
                if field not in metadata:
                    issues.append(f"Missing required field '{field}' in package.json")
        except json.JSONDecodeError:
            issues.append("Invalid JSON in package.json")
            return False, issues
        except Exception as e:
            issues.append(f"Error reading package.json: {e}")
            return False, issues
            
        # Check that main script exists
        main_script = os.path.join(package_dir, metadata.get("main", "main.py"))
        if not os.path.exists(main_script):
            issues.append(f"Main script '{main_script}' not found")
            return False, issues
            
        # More security checks could be added:
        # - Validate digital signatures
        # - Check for malicious code patterns
        # - Scan with antivirus
        # - Check for network access or system calls
        
        # Return validation result
        return len(issues) == 0, issues
    
    def execute_package(self, package_id: str, parameters: Dict[str, Any] = None, execution_id: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Execute a package with the provided parameters
        
        Args:
            package_id (str): The package ID to execute
            parameters (Dict[str, Any], optional): Parameters to pass to the package
            execution_id (str, optional): An execution ID to use, or auto-generate if None
            
        Returns:
            Tuple[bool, str, Dict[str, Any]]: (success, execution_id, result)
        """
        # Generate an execution ID if not provided
        if not execution_id:
            execution_id = str(uuid.uuid4())
            
        # Get the package
        package_dir = self.get_package(package_id)
        if not package_dir:
            return False, execution_id, {"error": f"Failed to download package {package_id}"}
            
        # Verify the package
        is_valid, issues = self.verify_package(package_dir)
        if not is_valid:
            return False, execution_id, {"error": f"Invalid package: {', '.join(issues)}"}
            
        # Install dependencies
        if not self.install_dependencies(package_dir):
            return False, execution_id, {"error": "Failed to install package dependencies"}
            
        # Create execution workspace
        workspace_dir = os.path.join(self.config.get("workspace_dir", "workspaces"), execution_id)
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Find the main script
        main_script = self._find_main_script(package_dir)
        if not main_script:
            return False, execution_id, {"error": "No main script found in package"}
            
        try:
            # Set up execution context
            from .execution_context import AutomationExecutionContext
            
            # Create execution context
            context = AutomationExecutionContext(
                self.api_client,
                execution_id,
                "direct_execution",  # No specific job ID for direct package execution
                package_id,
                parameters or {}
            )
            
            # Set up workspace
            context.setup_workspace(os.path.dirname(workspace_dir))
            
            # Add to active executions
            self.active_executions[execution_id] = {
                "package_id": package_id,
                "start_time": time.time(),
                "status": "running",
                "context": context
            }
            
            # Send status update
            self.api_client.update_job_status(execution_id, "running")
            
            # Load and execute the main module
            result = self._execute_package_module(main_script, context)
            
            # Update status
            success = True
            if isinstance(result, bool):
                success = result
            elif isinstance(result, int):
                success = (result == 0)
            elif isinstance(result, dict) and "success" in result:
                success = result["success"]
                
            # Update execution status
            status = "completed" if success else "failed"
            
            # Update active executions
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = status
                self.active_executions[execution_id]["end_time"] = time.time()
                self.active_executions[execution_id]["result"] = result
                
            # Send status update
            self.api_client.update_job_status(
                execution_id, 
                status,
                error=None if success else "Package execution failed",
                results=result if isinstance(result, dict) else {"result": result}
            )
            
            return success, execution_id, result if isinstance(result, dict) else {"result": result}
            
        except Exception as e:
            logger.error(f"Error executing package {package_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Update execution status
            if execution_id in self.active_executions:
                self.active_executions[execution_id]["status"] = "failed"
                self.active_executions[execution_id]["end_time"] = time.time()
                self.active_executions[execution_id]["error"] = str(e)
                
            # Send status update
            self.api_client.update_job_status(
                execution_id, 
                "failed",
                error=str(e)
            )
            
            return False, execution_id, {"error": str(e)}
    
    def _find_main_script(self, package_dir):
        """Find the main script in a package directory
        
        Args:
            package_dir (str): Path to the package directory
            
        Returns:
            str: Path to the main script or None if not found
        """
        # Check for package.json with main field
        metadata_file = os.path.join(package_dir, "package.json")
        if os.path.isfile(metadata_file):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    
                if "main" in metadata:
                    main_file = os.path.join(package_dir, metadata["main"])
                    if os.path.isfile(main_file):
                        return main_file
            except:
                pass
        
        # Check for main.py
        main_py = os.path.join(package_dir, "main.py")
        if os.path.isfile(main_py):
            return main_py
            
        # Search for any Python file
        for root, _, files in os.walk(package_dir):
            for file in files:
                if file.endswith(".py"):
                    return os.path.join(root, file)
                    
        return None
        
    def _execute_package_module(self, script_path, context):
        """Load and execute a Python module
        
        Args:
            script_path (str): Path to the main script
            context (AutomationExecutionContext): Execution context
            
        Returns:
            Any: Result from the main function
        """
        try:
            # Generate a unique module name
            module_name = f"orchestrator_package_{Path(script_path).stem}_{int(time.time())}"
            
            # Create spec
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None:
                raise ValueError(f"Failed to create module spec for {script_path}")
                
            # Create module from spec
            module = importlib.util.module_from_spec(spec)
            
            # Add the script directory to sys.path
            script_dir = os.path.dirname(script_path)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
                
            # Execute the module
            spec.loader.exec_module(module)
            
            # Find the main function
            main_func = getattr(module, "main", None)
            if not main_func or not callable(main_func):
                raise ValueError(f"No main function found in {script_path}")
                
            # Execute the main function with context
            return main_func(context)
            
        except Exception as e:
            logger.error(f"Error executing module {script_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
            
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a package execution
        
        Args:
            execution_id (str): The execution ID
            
        Returns:
            Dict[str, Any]: Status information
        """
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            elapsed = time.time() - execution["start_time"]
            
            return {
                "execution_id": execution_id,
                "package_id": execution["package_id"],
                "status": execution["status"],
                "start_time": datetime.fromtimestamp(execution["start_time"]).isoformat(),
                "elapsed_seconds": elapsed,
                "end_time": datetime.fromtimestamp(execution["end_time"]).isoformat() if "end_time" in execution else None,
                "result": execution.get("result"),
                "error": execution.get("error")
            }
        
        # If not found in active executions, try to get from API
        execution = self.api_client.get_job_execution(execution_id)
        if execution:
            return execution
            
        return {"error": f"Execution {execution_id} not found"}
        
    def list_active_executions(self) -> List[Dict[str, Any]]:
        """List all active package executions
        
        Returns:
            List[Dict[str, Any]]: List of execution information
        """
        return [
            {
                "execution_id": execution_id,
                "package_id": info["package_id"],
                "status": info["status"],
                "start_time": datetime.fromtimestamp(info["start_time"]).isoformat(),
                "elapsed_seconds": time.time() - info["start_time"]
            }
            for execution_id, info in self.active_executions.items()
            if info["status"] == "running"
        ]
    
    def upload_package(self, package_path: str, package_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Upload a package to the orchestrator
        
        Args:
            package_path (str): Path to the package file (zip)
            package_info (Dict[str, Any]): Package information
            
        Returns:
            Optional[Dict[str, Any]]: The uploaded package information or None if failed
        """
        try:
            # Check if the file exists
            if not os.path.exists(package_path):
                logger.error(f"Package file not found: {package_path}")
                return None
                
            # Validate package file
            if not zipfile.is_zipfile(package_path):
                logger.error(f"Invalid package file (not a zip): {package_path}")
                return None
                
            # Upload to server
            result = self.api_client.upload_package(package_path, package_info)
            return result
            
        except Exception as e:
            logger.error(f"Error uploading package: {e}")
            return None
    
    def clean_packages(self, max_age_days=30):
        """Clean up old packages from the cache
        
        Args:
            max_age_days (int, optional): Maximum age in days to keep packages.
                
        Returns:
            int: Number of packages cleaned
        """
        if not os.path.exists(self.packages_dir):
            return 0
            
        count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
        
        for item in os.listdir(self.packages_dir):
            item_path = os.path.join(self.packages_dir, item)
            
            # Skip metadata cache and non-directories
            if item == "metadata_cache.json" or not os.path.isdir(item_path):
                continue
                
            # Check if package is in use or recently used
            package_id = item
            metadata = self.metadata_cache.get(package_id, {})
            last_check = metadata.get("last_check", 0)
            
            if last_check < cutoff_time:
                try:
                    shutil.rmtree(item_path)
                    count += 1
                    # Remove from metadata cache
                    if package_id in self.metadata_cache:
                        del self.metadata_cache[package_id]
                except Exception as e:
                    logger.warning(f"Failed to delete package {package_id}: {e}")
        
        # Save updated metadata cache
        if count > 0:
            self._save_metadata_cache()
            
        return count