"""
Job Executor for Automation Tasks

This module is responsible for:
- Managing job execution lifecycle
- Loading and running automation scripts
- Capturing results and errors
- Reporting job status to the orchestrator
"""

import os
import sys
import json
import time
import logging
import traceback
import importlib.util
import inspect
import threading
import signal
from pathlib import Path
from datetime import datetime

from .execution_context import AutomationExecutionContext

logger = logging.getLogger("orchestrator-agent")

class JobExecutor:
    """Responsible for executing automation jobs"""
    
    def __init__(self, api_client, config):
        """Initialize the job executor
        
        Args:
            api_client: The API client for communicating with the orchestrator
            config: The agent configuration
        """
        self.api_client = api_client
        self.config = config
        self.running_jobs = {}  # Dictionary of running jobs by execution_id
        self.job_threads = {}   # Dictionary of job threads by execution_id
        self.stop_event = threading.Event()
        
    def execute_job(self, job_data):
        """Execute an automation job
        
        Args:
            job_data (dict): The job data from the orchestrator
            
        Returns:
            bool: True if job started successfully, False otherwise
        """
        try:
            # Extract job information
            execution_id = job_data.get("execution_id")
            job_id = job_data.get("job_id")
            package_id = job_data.get("package_id")
            parameters = job_data.get("parameters", {})
            asset_ids = job_data.get("asset_ids", [])
            
            if not execution_id or not job_id or not package_id:
                logger.error(f"Missing required job information: {job_data}")
                return False
                
            # Check if job is already running
            if execution_id in self.running_jobs:
                logger.warning(f"Job {execution_id} is already running")
                return False
                
            # Update job status to running
            self.api_client.update_job_status(execution_id, "running")
            
            # Create execution context
            context = AutomationExecutionContext(
                self.api_client,
                execution_id,
                job_id,
                package_id,
                parameters
            )
            
            # Set up workspace
            working_dir = context.setup_workspace(self.config.get("working_dir"))
            context.log(f"Setting up workspace at {working_dir}")
            
            # Download package if not already available
            package_dir = os.path.join(self.config.get("packages_dir"), package_id)
            if not os.path.exists(package_dir):
                context.log(f"Downloading package {package_id}")
                package_dir = self.api_client.get_package(package_id)
                if not package_dir:
                    raise Exception(f"Failed to download package {package_id}")
            
            # Load assets
            for asset_id in asset_ids:
                context.log(f"Loading asset {asset_id}")
                asset = self.api_client.get_asset(asset_id)
                if asset:
                    context.assets[asset_id] = asset
                else:
                    context.log(f"Warning: Failed to load asset {asset_id}", "WARNING")
            
            # Store job in running jobs
            self.running_jobs[execution_id] = {
                "context": context,
                "start_time": time.time(),
                "package_dir": package_dir,
                "status": "running"
            }
            
            # Start job in a separate thread
            job_thread = threading.Thread(
                target=self._run_job_thread,
                args=(execution_id, package_dir, context),
                daemon=True
            )
            self.job_threads[execution_id] = job_thread
            job_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting job: {e}")
            logger.error(traceback.format_exc())
            
            # Update job status to failed
            if execution_id:
                self.api_client.update_job_status(
                    execution_id, 
                    "failed",
                    error=str(e)
                )
                
            return False
    
    def _run_job_thread(self, execution_id, package_dir, context):
        """Run a job in a separate thread
        
        Args:
            execution_id (str): The execution ID
            package_dir (str): Path to the package directory
            context (AutomationExecutionContext): The execution context
        """
        job_success = False
        error_message = None
        
        try:
            # Find main script in package
            context.log_step("setup", "Finding main script")
            main_script = self._find_main_script(package_dir)
            if not main_script:
                raise Exception(f"No main script found in package directory: {package_dir}")
                
            context.log_step("setup", f"Found main script: {main_script}")
            
            # Load the main module
            context.log_step("load", "Loading automation module")
            module = self._load_module(main_script)
            if not module:
                raise Exception(f"Failed to load module from {main_script}")
                
            # Find the main function
            main_func = getattr(module, "main", None)
            if not main_func or not callable(main_func):
                raise Exception(f"No main function found in {main_script}")
                
            # Set timeout handler if specified
            timeout_seconds = context.get_parameter("timeout_seconds", 
                                                  self.config.get("default_timeout", 3600))
            timer = None
            
            if timeout_seconds > 0:
                def timeout_handler():
                    context.log(f"Job execution timed out after {timeout_seconds} seconds", "ERROR")
                    # In a real implementation, we would need to forcefully terminate
                    # the job process here, as a thread can't be easily terminated in Python
                
                timer = threading.Timer(timeout_seconds, timeout_handler)
                timer.daemon = True
                timer.start()
            
            # Execute the main function
            context.log_step("execute", "Starting automation execution")
            result = main_func(context)
            
            # If we get here, job was successful
            job_success = True
            
            # Record job results
            if isinstance(result, int):
                # Assume exit code
                job_success = (result == 0)
                context.set_result({"exit_code": result})
            elif isinstance(result, dict):
                # Assume result dictionary
                context.set_result(result)
            else:
                # Convert to bool
                job_success = bool(result)
                context.set_result({"success": job_success})
                
        except Exception as e:
            logger.error(f"Error executing job {execution_id}: {e}")
            logger.error(traceback.format_exc())
            job_success = False
            error_message = f"{type(e).__name__}: {str(e)}"
            
            # Log the error in the context
            try:
                context.log(f"Error: {error_message}", "ERROR")
                context.log_step("error", f"Execution failed: {error_message}", "failed")
            except:
                pass
                
        finally:
            # Cancel timeout timer if it exists
            if 'timer' in locals() and timer:
                timer.cancel()
                
            # Update job status
            try:
                status = "completed" if job_success else "failed"
                self.api_client.update_job_status(
                    execution_id,
                    status,
                    error=error_message,
                    results=context.results
                )
                
                # Clean up job references
                if execution_id in self.running_jobs:
                    self.running_jobs[execution_id]["status"] = status
                    
                if execution_id in self.job_threads:
                    del self.job_threads[execution_id]
                    
            except Exception as cleanup_error:
                logger.error(f"Error during job cleanup: {cleanup_error}")
    
    def _find_main_script(self, package_dir):
        """Find the main script in a package directory
        
        Args:
            package_dir (str): Path to the package directory
            
        Returns:
            str: Path to the main script or None if not found
        """
        # Check for main.py
        main_py = os.path.join(package_dir, "main.py")
        if os.path.isfile(main_py):
            return main_py
            
        # Check for package metadata
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
                
        # Search for any Python file
        for root, _, files in os.walk(package_dir):
            for file in files:
                if file.endswith(".py"):
                    return os.path.join(root, file)
                    
        return None
    
    def _load_module(self, script_path):
        """Load a Python module from file
        
        Args:
            script_path (str): Path to the Python script
            
        Returns:
            module: The loaded module or None if failed
        """
        try:
            # Generate a unique module name
            module_name = f"orchestrator_job_{Path(script_path).stem}_{int(time.time())}"
            
            # Create spec
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            if spec is None:
                return None
                
            # Create module from spec
            module = importlib.util.module_from_spec(spec)
            
            # Set up sys.path to include the script directory
            script_dir = os.path.dirname(script_path)
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
                
            # Execute the module
            spec.loader.exec_module(module)
            
            return module
        except Exception as e:
            logger.error(f"Error loading module from {script_path}: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def get_running_jobs(self):
        """Get information about running jobs
        
        Returns:
            dict: Dictionary of running jobs
        """
        return {k: {
            "start_time": v["start_time"],
            "elapsed_seconds": time.time() - v["start_time"],
            "status": v["status"]
        } for k, v in self.running_jobs.items()}
    
    def stop_job(self, execution_id):
        """Stop a running job
        
        Args:
            execution_id (str): The execution ID to stop
            
        Returns:
            bool: True if job was stopped, False otherwise
        """
        if execution_id not in self.running_jobs:
            logger.warning(f"Job {execution_id} is not running")
            return False
            
        # In a real implementation, we would need a way to forcefully terminate
        # the job process, as a thread can't be easily terminated in Python
        # This would likely involve running jobs in separate processes
        
        # For now, just mark the job as cancelled
        self.running_jobs[execution_id]["status"] = "cancelled"
        
        # Update status in orchestrator
        self.api_client.update_job_status(
            execution_id,
            "cancelled",
            error="Job was cancelled by user or system"
        )
        
        return True
    
    def stop_all_jobs(self):
        """Stop all running jobs
        
        Returns:
            int: Number of jobs stopped
        """
        count = 0
        for execution_id in list(self.running_jobs.keys()):
            if self.stop_job(execution_id):
                count += 1
                
        return count