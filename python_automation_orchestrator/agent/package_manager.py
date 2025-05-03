"""
Package Manager for Automation Packages

This module handles automation package management:
- Downloading and caching packages
- Version management and updates
- Dependency resolution
- Package validation
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
from pathlib import Path
from datetime import datetime

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