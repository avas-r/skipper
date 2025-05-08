"""
Package service for managing automation packages.

This module provides services for managing automation packages,
including uploading, versioning, and deployment.
"""

import os
import uuid
import hashlib
import logging
import shutil
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Any, BinaryIO

from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc

from ..models import Package, PackagePermission, Role, User, Agent, Job, AuditLog
from ..schemas.package import PackageCreate, PackageUpdate, PackageUpload, PackageDeployRequest
from ..utils.object_storage import ObjectStorage
from ..config import settings

logger = logging.getLogger(__name__)

class PackageService:
    """Service for managing automation packages"""
    
    def __init__(self, db: Session, storage: Optional[ObjectStorage] = None):
        """
        Initialize the package service.
        
        Args:
            db: Database session
            storage: Optional object storage service (MinIO)
        """
        self.db = db
        self.storage = storage or ObjectStorage()
        self.packages_dir = settings.PACKAGES_FOLDER
        os.makedirs(self.packages_dir, exist_ok=True)
        
    def create_package(self, package_in: PackageCreate, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Package:
        """
        Create a new package.
        
        Args:
            package_in: Package data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Package: Created package
            
        Raises:
            ValueError: If package with same name and version exists
        """
        # Check if package with same name and version exists
        existing = self.db.query(Package).filter(
            Package.tenant_id == tenant_id,
            Package.name == package_in.name,
            Package.version == package_in.version
        ).first()
        
        if existing:
            raise ValueError(f"Package with name '{package_in.name}' and version '{package_in.version}' already exists")
        
        # Create storage path
        storage_path = f"tenants/{tenant_id}/packages/{package_in.name}/{package_in.version}"
        
        # Create package
        db_package = Package(
            package_id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=package_in.name,
            description=package_in.description,
            version=package_in.version,
            main_file_path=package_in.main_file_path,
            storage_path=storage_path,
            entry_point=package_in.entry_point,
            status=package_in.status or "development",
            dependencies=package_in.dependencies,
            tags=package_in.tags,
            created_by=user_id,
            updated_by=user_id
        )
        
        self.db.add(db_package)
        self.db.commit()
        self.db.refresh(db_package)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="create_package",
            entity_type="package",
            entity_id=db_package.package_id,
            details={
                "name": db_package.name,
                "version": db_package.version
            }
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return db_package
    
    def update_package(self, package_id: uuid.UUID, package_in: PackageUpdate, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Optional[Package]:
        """
        Update a package.
        
        Args:
            package_id: Package ID
            package_in: Package update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Optional[Package]: Updated package or None if not found
            
        Raises:
            ValueError: If package not found or invalid status
        """
        # Get package
        package = self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        # Check status transition
        if package_in.status and package_in.status != package.status:
            # Validate status
            valid_statuses = ["development", "testing", "production", "deprecated", "archived"]
            if package_in.status not in valid_statuses:
                raise ValueError(f"Invalid status: {package_in.status}")
            
            # Validate status transition
            # For example, can't go from archived back to production
            if package.status == "archived" and package_in.status != "archived":
                raise ValueError(f"Cannot change status from 'archived' to '{package_in.status}'")
        
        # Update fields
        update_data = package_in.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(package, key, value)
            
        # Update audit fields
        package.updated_at = datetime.utcnow()
        package.updated_by = user_id
        
        self.db.commit()
        self.db.refresh(package)
        
        # Create audit log
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="update_package",
            entity_type="package",
            entity_id=package.package_id,
            details=update_data
        )
        self.db.add(audit_log)
        self.db.commit()
        
        return package
    
    def delete_package(self, package_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Delete a package.
        
        Args:
            package_id: Package ID
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            ValueError: If package not found or has jobs
        """
        # Get package
        package = self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        # Check if package has jobs
        job_count = self.db.query(Job).filter(
            Job.package_id == package_id
        ).count()
        
        if job_count > 0:
            raise ValueError(f"Cannot delete package that is used by {job_count} jobs")
        
        # Delete package files
        try:
            # Delete from object storage
            if package.storage_path:
                self.storage.delete_objects(self.storage.list_objects(package.storage_path))
                
            # Delete from local storage if exists
            local_path = os.path.join(self.packages_dir, str(package.package_id))
            if os.path.exists(local_path):
                shutil.rmtree(local_path)
        except Exception as e:
            logger.warning(f"Error deleting package files: {e}")
        
        # Create audit log before deletion
        audit_log = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            action="delete_package",
            entity_type="package",
            entity_id=package.package_id,
            details={
                "name": package.name,
                "version": package.version
            }
        )
        self.db.add(audit_log)
        
        # Delete package permissions
        self.db.query(PackagePermission).filter(
            PackagePermission.package_id == package_id
        ).delete()
        
        # Delete package
        self.db.delete(package)
        self.db.commit()
        
        return True
    
    def get_package(self, package_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[Package]:
        """
        Get a package by ID.
        
        Args:
            package_id: Package ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Package]: Package or None if not found
        """
        return self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
    
    def list_packages(
        self,
        tenant_id: uuid.UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List packages with filtering.
        
        Args:
            tenant_id: Tenant ID
            status: Optional status filter
            search: Optional search term
            tags: Optional tags filter
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dict[str, Any]: Dictionary with total count and list of packages
        """
        # Build base query
        query = self.db.query(Package).filter(Package.tenant_id == tenant_id)
        
        # Apply filters
        if status:
            query = query.filter(Package.status == status)
            
        if search:
            query = query.filter(
                or_(
                    Package.name.ilike(f"%{search}%"),
                    Package.description.ilike(f"%{search}%")
                )
            )
            
        if tags:
            # Use any() to find packages with any of the specified tags
            for tag in tags:
                query = query.filter(Package.tags.contains([tag]))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get latest version first
        packages = query.order_by(
            Package.name,
            desc(Package.version)
        ).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": packages
        }
    
    def list_package_versions(
        self,
        tenant_id: uuid.UUID,
        name: str,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List all versions of a package.
        
        Args:
            tenant_id: Tenant ID
            name: Package name
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dict[str, Any]: Dictionary with total count and list of package versions
        """
        # Build query
        query = self.db.query(Package).filter(
            Package.tenant_id == tenant_id,
            Package.name == name
        )
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get latest version first
        versions = query.order_by(desc(Package.version)).offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": versions
        }
    
    def upload_package(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        file: BinaryIO,
        info: PackageUpload
    ) -> Package:
        """
        Upload a package.
        
        Args:
            tenant_id: Tenant ID
            user_id: User ID
            file: Uploaded file
            info: Package upload information
            
        Returns:
            Package: Created or updated package
            
        Raises:
            ValueError: If package is invalid or upload fails
        """
        # Check if package exists
        existing = self.db.query(Package).filter(
            Package.tenant_id == tenant_id,
            Package.name == info.name,
            Package.version == info.version
        ).first()
        
        if existing and not info.overwrite:
            raise ValueError(f"Package with name '{info.name}' and version '{info.version}' already exists")
        
        # Create temporary directory
        temp_dir = os.path.join(self.packages_dir, "temp", str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Save file to temp directory
            zip_path = os.path.join(temp_dir, "package.zip")
            with open(zip_path, "wb") as f:
                f.write(file.read())
            
            # Validate zip file
            if not zipfile.is_zipfile(zip_path):
                raise ValueError("Invalid zip file")
            
            # Extract zip file
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Validate entry point
            entry_point_path = os.path.join(extract_dir, info.entry_point)
            if not os.path.exists(entry_point_path):
                raise ValueError(f"Entry point not found: {info.entry_point}")
            
            # Calculate MD5 hash
            md5_hash = self._calculate_file_md5(zip_path)
            
            # Create or update package
            if existing:
                # Update existing package
                existing.description = info.description or existing.description
                existing.entry_point = info.entry_point
                existing.md5_hash = md5_hash
                existing.updated_at = datetime.utcnow()
                existing.updated_by = user_id
                
                package = existing
                
                # Create audit log
                audit_log = AuditLog(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="update_package",
                    entity_type="package",
                    entity_id=package.package_id,
                    details={
                        "name": package.name,
                        "version": package.version,
                        "md5_hash": md5_hash
                    }
                )
                self.db.add(audit_log)
                
            else:
                # Create new package
                storage_path = f"tenants/{tenant_id}/packages/{info.name}/{info.version}"
                
                package = Package(
                    package_id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=info.name,
                    description=info.description,
                    version=info.version,
                    main_file_path=info.entry_point,
                    storage_path=storage_path,
                    entry_point=info.entry_point,
                    md5_hash=md5_hash,
                    status="development",
                    created_by=user_id,
                    updated_by=user_id
                )
                
                self.db.add(package)
                
                # Create audit log
                audit_log = AuditLog(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="create_package",
                    entity_type="package",
                    entity_id=package.package_id,
                    details={
                        "name": package.name,
                        "version": package.version,
                        "md5_hash": md5_hash
                    }
                )
                self.db.add(audit_log)
            
            self.db.commit()
            self.db.refresh(package)
            
            # Upload to object storage
            object_name = f"{package.storage_path}/package.zip"
            
            with open(zip_path, "rb") as f:
                self.storage.upload_bytes(
                    f.read(),
                    object_name,
                    content_type="application/zip",
                    metadata={
                        "tenant_id": str(tenant_id),
                        "package_id": str(package.package_id),
                        "name": package.name,
                        "version": package.version,
                        "md5_hash": md5_hash
                    }
                )
            
            return package
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {e}")
    
    def deploy_package(
        self,
        package_id: uuid.UUID,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        deploy_request: PackageDeployRequest
    ) -> Dict[str, Any]:
        """
        Deploy a package to agents.
        
        Args:
            package_id: Package ID
            tenant_id: Tenant ID
            user_id: User ID
            deploy_request: Deployment request
            
        Returns:
            Dict[str, Any]: Deployment result
            
        Raises:
            ValueError: If package not found or deployment fails
        """
        # Get package
        package = self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        # Update package status if needed
        if package.status != deploy_request.target_environment:
            package.status = deploy_request.target_environment
            package.updated_at = datetime.utcnow()
            package.updated_by = user_id
            
            self.db.commit()
            self.db.refresh(package)
        
        # Get target agents
        if deploy_request.agent_ids:
            # Deploy to specific agents
            agents = self.db.query(Agent).filter(
                Agent.tenant_id == tenant_id,
                Agent.agent_id.in_(deploy_request.agent_ids)
            ).all()
            
        elif deploy_request.deploy_to_all_agents:
            # Deploy to all online agents
            agents = self.db.query(Agent).filter(
                Agent.tenant_id == tenant_id,
                Agent.status == "online"
            ).all()
            
        else:
            # No agents specified
            return {
                "success": False,
                "message": "No agents specified for deployment",
                "deployed_count": 0,
                "failed_count": 0
            }
        
        if not agents:
            return {
                "success": False,
                "message": "No agents found for deployment",
                "deployed_count": 0,
                "failed_count": 0
            }
        
        # Deploy to agents
        deployed_count = 0
        failed_count = 0
        
        for agent in agents:
            try:
                # In a real implementation, this would send a command to the agent
                # to download and install the package. For now, we just log it.
                logger.info(
                    f"Deploying package {package.name} v{package.version} to agent {agent.name} ({agent.agent_id})"
                )
                
                # Create audit log
                audit_log = AuditLog(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    action="deploy_package",
                    entity_type="package",
                    entity_id=package.package_id,
                    details={
                        "package_name": package.name,
                        "package_version": package.version,
                        "agent_id": str(agent.agent_id),
                        "agent_name": agent.name,
                        "environment": deploy_request.target_environment
                    }
                )
                self.db.add(audit_log)
                
                deployed_count += 1
                
            except Exception as e:
                logger.error(f"Error deploying package to agent {agent.agent_id}: {e}")
                failed_count += 1
        
        self.db.commit()
        
        return {
            "success": deployed_count > 0,
            "message": f"Deployed to {deployed_count} agents, {failed_count} failed",
            "deployed_count": deployed_count,
            "failed_count": failed_count
        }
    
    def download_package(self, package_id: uuid.UUID, tenant_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Optional[bytes]:
        """
        Download a package.
        
        Args:
            package_id: Package ID
            tenant_id: Tenant ID
            user_id: Optional user ID for audit logging
            
        Returns:
            Optional[bytes]: Package data or None if not found
        """
        # Get package
        package = self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            return None
        
        # Download from object storage
        object_name = f"{package.storage_path}/package.zip"
        data = self.storage.download_bytes(object_name)
        
        if not data:
            return None
        
        # Log download if user ID provided
        if user_id:
            # Create audit log
            audit_log = AuditLog(
                tenant_id=tenant_id,
                user_id=user_id,
                action="download_package",
                entity_type="package",
                entity_id=package.package_id,
                details={
                    "name": package.name,
                    "version": package.version
                }
            )
            self.db.add(audit_log)
            self.db.commit()
        
        return data
    
    def get_package_permissions(self, package_id: uuid.UUID, tenant_id: uuid.UUID, user_id: uuid.UUID) -> Dict[str, bool]:
        """
        Get package permissions for a user.
        
        Args:
            package_id: Package ID
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Dict[str, bool]: Dictionary of permissions
        """
        # Get user roles
        user = self.db.query(User).filter(
            User.user_id == user_id,
            User.tenant_id == tenant_id
        ).first()
        
        if not user:
            return {}
        
        # Check if user has superuser role
        for user_role in user.roles:
            if user_role.role.name == "superuser":
                # Superuser has all permissions
                return {
                    "can_view": True,
                    "can_execute": True,
                    "can_edit": True,
                    "can_delete": True
                }
        
        # Get role IDs
        role_ids = [role.role.role_id for role in user.roles]
        
        if not role_ids:
            return {}
        
        # Get package permissions for user roles
        permissions = self.db.query(PackagePermission).filter(
            PackagePermission.package_id == package_id,
            PackagePermission.role_id.in_(role_ids)
        ).all()
        
        # Combine permissions (if any role has permission, user has permission)
        result = {
            "can_view": False,
            "can_execute": False,
            "can_edit": False,
            "can_delete": False
        }
        
        for perm in permissions:
            result["can_view"] = result["can_view"] or perm.can_view
            result["can_execute"] = result["can_execute"] or perm.can_execute
            result["can_edit"] = result["can_edit"] or perm.can_edit
            result["can_delete"] = result["can_delete"] or perm.can_delete
        
        return result
    
    def set_package_permissions(
        self,
        package_id: uuid.UUID,
        tenant_id: uuid.UUID,
        role_id: uuid.UUID,
        permissions: Dict[str, bool]
    ) -> bool:
        """
        Set package permissions for a role.
        
        Args:
            package_id: Package ID
            tenant_id: Tenant ID
            role_id: Role ID
            permissions: Dictionary of permissions
            
        Returns:
            bool: True if permissions set successfully
        """
        # Get package
        package = self.db.query(Package).filter(
            Package.package_id == package_id,
            Package.tenant_id == tenant_id
        ).first()
        
        if not package:
            return False
        
        # Get role
        role = self.db.query(Role).filter(
            Role.role_id == role_id,
            Role.tenant_id == tenant_id
        ).first()
        
        if not role:
            return False
        
        # Get existing permission
        permission = self.db.query(PackagePermission).filter(
            PackagePermission.package_id == package_id,
            PackagePermission.role_id == role_id
        ).first()
        
        if permission:
            # Update existing permission
            permission.can_view = permissions.get("can_view", permission.can_view)
            permission.can_execute = permissions.get("can_execute", permission.can_execute)
            permission.can_edit = permissions.get("can_edit", permission.can_edit)
            permission.can_delete = permissions.get("can_delete", permission.can_delete)
        else:
            # Create new permission
            permission = PackagePermission(
                package_id=package_id,
                role_id=role_id,
                can_view=permissions.get("can_view", False),
                can_execute=permissions.get("can_execute", False),
                can_edit=permissions.get("can_edit", False),
                can_delete=permissions.get("can_delete", False)
            )
            self.db.add(permission)
        
        self.db.commit()
        return True
    
    def _calculate_file_md5(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            str: MD5 hash as hexadecimal string
        """
        md5 = hashlib.md5()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
                
        return md5.hexdigest()
        
    def list_packages_for_agent(self, agent_id: uuid.UUID, tenant_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        List packages available for an agent.
        
        Args:
            agent_id: Agent ID
            tenant_id: Tenant ID
            
        Returns:
            List[Dict[str, Any]]: List of packages
        """
        # Get agent
        agent = self.db.query(Agent).filter(
            Agent.agent_id == agent_id,
            Agent.tenant_id == tenant_id
        ).first()
        
        if not agent:
            return []
            
        # Get packages for tenant
        packages = self.db.query(Package).filter(
            Package.tenant_id == tenant_id,
            Package.status.in_(["production", "testing"])
        ).all()
        
        # Format for agent consumption
        return [
            {
                "package_id": str(pkg.package_id),
                "name": pkg.name,
                "version": pkg.version,
                "description": pkg.description,
                "entry_point": pkg.entry_point,
                "status": pkg.status,
                "md5_hash": pkg.md5_hash
            }
            for pkg in packages
        ]
        
    def process_agent_package_upload(
        self,
        file: UploadFile,
        name: str,
        version: str,
        description: Optional[str],
        entry_point: Optional[str],
        tenant_id: uuid.UUID,
        agent_id: uuid.UUID
    ) -> Package:
        """
        Process and save a package uploaded by an agent.
        
        Args:
            file: Uploaded package file
            name: Package name
            version: Package version
            description: Package description
            entry_point: Package entry point
            tenant_id: Tenant ID
            agent_id: Agent ID
            
        Returns:
            Package: Created or updated package
            
        Raises:
            ValueError: If package is invalid or upload fails
        """
        # Ensure temp directory exists
        temp_dir = os.path.join(settings.TEMP_FOLDER, str(uuid.uuid4()))
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Save file to temp directory
            zip_path = os.path.join(temp_dir, "package.zip")
            with open(zip_path, "wb") as f:
                f.write(file.file.read())
                
            # Validate zip file
            if not zipfile.is_zipfile(zip_path):
                raise ValueError("Invalid zip file")
                
            # Extract zip file
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
                
            # Validate entry point if provided
            if entry_point:
                entry_point_path = os.path.join(extract_dir, entry_point)
                if not os.path.exists(entry_point_path):
                    raise ValueError(f"Entry point not found: {entry_point}")
            else:
                # Try to find main.py
                if os.path.exists(os.path.join(extract_dir, "main.py")):
                    entry_point = "main.py"
                else:
                    # Find first Python file
                    for root, _, files in os.walk(extract_dir):
                        for file in files:
                            if file.endswith(".py"):
                                rel_path = os.path.relpath(os.path.join(root, file), extract_dir)
                                entry_point = rel_path
                                break
                        if entry_point:
                            break
                            
                    if not entry_point:
                        raise ValueError("No Python files found in package")
                        
            # Calculate MD5 hash
            md5_hash = self._calculate_file_md5(zip_path)
            
            # Check if package exists
            existing = self.db.query(Package).filter(
                Package.tenant_id == tenant_id,
                Package.name == name,
                Package.version == version
            ).first()
            
            # Create storage path
            storage_path = f"tenants/{tenant_id}/packages/{name}/{version}"
            
            if existing:
                # Update existing package
                existing.description = description or existing.description
                existing.entry_point = entry_point
                existing.md5_hash = md5_hash
                existing.updated_at = datetime.utcnow()
                
                package = existing
                
                # Create audit log
                audit_log = AuditLog(
                    tenant_id=tenant_id,
                    action="update_package",
                    entity_type="package",
                    entity_id=package.package_id,
                    details={
                        "name": package.name,
                        "version": package.version,
                        "md5_hash": md5_hash,
                        "agent_id": str(agent_id)
                    }
                )
                self.db.add(audit_log)
            else:
                # Create new package
                package = Package(
                    package_id=uuid.uuid4(),
                    tenant_id=tenant_id,
                    name=name,
                    description=description,
                    version=version,
                    main_file_path=entry_point,
                    storage_path=storage_path,
                    entry_point=entry_point,
                    md5_hash=md5_hash,
                    status="development"
                )
                
                self.db.add(package)
                
                # Create audit log
                audit_log = AuditLog(
                    tenant_id=tenant_id,
                    action="create_package",
                    entity_type="package",
                    entity_id=package.package_id,
                    details={
                        "name": package.name,
                        "version": package.version,
                        "md5_hash": md5_hash,
                        "agent_id": str(agent_id)
                    }
                )
                self.db.add(audit_log)
                
            self.db.commit()
            self.db.refresh(package)
            
            # Upload to object storage
            object_name = f"{package.storage_path}/package.zip"
            
            with open(zip_path, "rb") as f:
                self.storage.upload_bytes(
                    f.read(),
                    object_name,
                    content_type="application/zip",
                    metadata={
                        "tenant_id": str(tenant_id),
                        "package_id": str(package.package_id),
                        "name": package.name,
                        "version": package.version,
                        "md5_hash": md5_hash,
                        "uploaded_by_agent": str(agent_id)
                    }
                )
                
            return package
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {e}")