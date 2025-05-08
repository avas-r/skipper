"""
Execution Context for Automation Jobs

This module provides a context object that automation scripts can use to:
- Access parameters and assets
- Log steps and progress
- Take screenshots
- Report results and errors
"""

import os
import sys
import json
import time
import uuid
import logging
import traceback
from datetime import datetime
from pathlib import Path

try:
    import pyautogui
    SCREENSHOTS_ENABLED = True
except ImportError:
    SCREENSHOTS_ENABLED = False

logger = logging.getLogger("orchestrator-agent")

class AutomationExecutionContext:
    """Context provided to automation scripts for interacting with the orchestrator"""
    
    def __init__(self, api_client, execution_id, job_id, package_id, parameters=None, assets=None):
        """Initialize the execution context
        
        Args:
            api_client: The API client instance for communicating with the server
            execution_id (str): The execution ID
            job_id (str): The job ID
            package_id (str): The package ID
            parameters (dict, optional): Job parameters. Defaults to None.
            assets (dict, optional): Job assets (credentials, configurations). Defaults to None.
        """
        self.api_client = api_client
        self.execution_id = execution_id
        self.job_id = job_id
        self.package_id = package_id
        self.parameters = parameters or {}
        self.assets = assets or {}
        self.working_dir = None
        self.screenshots_dir = None
        self.logs_dir = None
        self.results = {}
        self.start_time = time.time()
        
    def setup_workspace(self, working_dir):
        """Set up the execution workspace
        
        Args:
            working_dir (str): Base working directory for the execution
            
        Returns:
            str: Path to the execution working directory
        """
        # Create execution-specific directory
        self.working_dir = os.path.join(working_dir, self.execution_id)
        self.screenshots_dir = os.path.join(self.working_dir, "screenshots")
        self.logs_dir = os.path.join(self.working_dir, "logs")
        
        os.makedirs(self.working_dir, exist_ok=True)
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Save parameters to file for reference
        with open(os.path.join(self.working_dir, "parameters.json"), "w") as f:
            json.dump(self.parameters, f, indent=2)
            
        return self.working_dir
    
    def log(self, message, level="INFO", step_id=None):
        """Log a message to the execution log
        
        Args:
            message (str): The message to log
            level (str, optional): Log level. Defaults to "INFO".
            step_id (str, optional): Associated step ID. Defaults to None.
        """
        # Log to local logger
        if level.upper() == "DEBUG":
            logger.debug(message)
        elif level.upper() == "INFO":
            logger.info(message)
        elif level.upper() == "WARNING":
            logger.warning(message)
        elif level.upper() == "ERROR":
            logger.error(message)
        else:
            logger.info(message)
            
        # Write to execution log file
        if self.logs_dir:
            try:
                timestamp = datetime.now().isoformat()
                log_file = os.path.join(self.logs_dir, "execution.log")
                with open(log_file, "a") as f:
                    f.write(f"[{timestamp}] [{level}] {message}\n")
            except Exception as e:
                logger.warning(f"Failed to write to execution log file: {e}")
    
    def log_step(self, step_id, description, status="running", data=None, take_screenshot=False):
        """Log an execution step to the orchestrator
        
        Args:
            step_id (str): The step ID
            description (str): Step description
            status (str, optional): Step status. Defaults to "running".
            data (dict, optional): Additional step data. Defaults to None.
            take_screenshot (bool, optional): Whether to take a screenshot. Defaults to False.
            
        Returns:
            dict: The API response from the orchestrator
        """
        # Log locally
        level = "INFO" if status != "failed" else "ERROR"
        self.log(f"Step {step_id}: {description} - {status}", level, step_id)
        
        # Take screenshot if requested and supported
        screenshot_path = None
        if take_screenshot and SCREENSHOTS_ENABLED:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(
                    self.screenshots_dir, 
                    f"{timestamp}_{step_id}.png"
                )
                pyautogui.screenshot(screenshot_path)
            except Exception as e:
                self.log(f"Failed to take screenshot: {e}", "WARNING", step_id)
                
        # Send to orchestrator
        return self.api_client.log_step(
            self.execution_id, 
            step_id, 
            description, 
            status, 
            data,
            take_screenshot
        )
    
    def get_parameter(self, name, default=None):
        """Get a job parameter
        
        Args:
            name (str): Parameter name
            default: Default value if parameter not found
            
        Returns:
            Parameter value or default if not found
        """
        return self.parameters.get(name, default)
    
    def get_asset(self, asset_id):
        """Get an asset (credential or configuration)
        
        Args:
            asset_id (str): Asset ID
            
        Returns:
            dict: Asset data or None if not found or error
        """
        # Check if already loaded
        if asset_id in self.assets:
            return self.assets[asset_id]
            
        # Request from server
        asset = self.api_client.get_asset(asset_id)
        if asset:
            self.assets[asset_id] = asset
            
        return asset
    
    def set_result(self, results):
        """Set the execution results
        
        Args:
            results (dict): The execution results
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.results = results
        
        # Save results to file
        if self.working_dir:
            try:
                with open(os.path.join(self.working_dir, "results.json"), "w") as f:
                    json.dump(results, f, indent=2)
            except Exception as e:
                self.log(f"Failed to save results to file: {e}", "ERROR")
                
        return True
    
    def take_screenshot(self, name="screenshot"):
        """Take a screenshot and save it to the screenshots directory
        
        Args:
            name (str, optional): Screenshot name. Defaults to "screenshot".
            
        Returns:
            str: Path to the screenshot or None if failed
        """
        if not SCREENSHOTS_ENABLED:
            self.log("Screenshots are not enabled (pyautogui not installed)", "WARNING")
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(
                self.screenshots_dir, 
                f"{timestamp}_{name}.png"
            )
            pyautogui.screenshot(screenshot_path)
            return screenshot_path
        except Exception as e:
            self.log(f"Failed to take screenshot: {e}", "ERROR")
            return None
    
    def get_execution_duration(self):
        """Get the execution duration in seconds
        
        Returns:
            float: Execution duration in seconds
        """
        return time.time() - self.start_time