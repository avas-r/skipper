"""
Package management endpoints for the orchestrator API.

This module provides endpoints for managing automation packages, including
uploading, downloading, and managing versions.
"""

import logging
import os
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Package
from ....schemas.package import (
    PackageCreate, 
    PackageUpdate, 
    PackageResponse,
    PackageVersionResponse,
    PackageDeployRequest
)
from ....services.package_service import PackageService
from ..dependencies import get_multi_tenant_filter

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_package_read = PermissionChecker(["package:read"])
require_package_create = PermissionChecker(["package:create"])
require_package_update = PermissionChecker(["package:update"])
require_package_delete = PermissionChecker(["package:delete"])
require_package_deploy = PermissionChecker(["package:deploy"])

@router.get("/", response_model=List[PackageResponse])
def list_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_read),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None
) -> Any:
    """
    List all packages with optional filtering.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        skip: Number of packages to skip
        limit: Maximum number of packages to return
        status: Optional status filter
        search: Optional search term
        tag: Optional tag filter
        
    Returns:
        List[PackageResponse]: List of packages
    """
    # Create package service
    package_service = PackageService(db)
    
    # List packages
    packages = package_service.list_packages(
        tenant_id=str(current_user.tenant_id),
        status=status,
        search=search,
        tag=tag,
        skip=skip,
        limit=limit
    )
    
    return packages

@router.post("/", response_model=PackageResponse)
def create_package(
    package_in: PackageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_create),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Create a new package.
    
    Args:
        package_in: Package creation data
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        PackageResponse: Created package
    """
    # Create package service
    package_service = PackageService(db)
    
    # Check if package already exists
    existing_package = package_service.get_package_by_name_and_version(
        name=package_in.name,
        version=package_in.version,
        tenant_id=str(current_user.tenant_id)
    )
    
    if existing_package:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Package with name {package_in.name} and version {package_in.version} already exists"
        )
    
    # Create package
    package = package_service.create_package(
        package_in=package_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    # Log audit event in background
    if background_tasks:
        background_tasks.add_task(
            package_service.log_package_activity,
            package_id=str(package.package_id),
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="create_package",
            details={
                "name": package.name,
                "version": package.version,
                "status": package.status
            }
        )
    
    return package

@router.get("/{package_id}", response_model=PackageResponse)
def read_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_read)
) -> Any:
    """
    Get package by ID.
    
    Args:
        package_id: Package ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        PackageResponse: Package
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get package
    package = package_service.get_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    return package

@router.put("/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: str,
    package_in: PackageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_update),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Update a package.
    
    Args:
        package_id: Package ID
        package_in: Package update data
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        PackageResponse: Updated package
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get package
    package = package_service.get_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Prevent updating name and version
    if package_in.name and package_in.name != package.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change package name"
        )
        
    if package_in.version and package_in.version != package.version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change package version. Create a new version instead."
        )
    
    # Update package
    updated_package = package_service.update_package(
        package_id=package_id,
        package_in=package_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    # Log audit event in background
    if background_tasks:
        update_details = {
            "name": updated_package.name,
            "version": updated_package.version,
            "updated_fields": list(package_in.dict(exclude_unset=True).keys())
        }
        
        background_tasks.add_task(
            package_service.log_package_activity,
            package_id=package_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="update_package",
            details=update_details
        )
    
    return updated_package

@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_delete),
    background_tasks: BackgroundTasks = None
) -> None:
    """
    Delete a package.
    
    Args:
        package_id: Package ID
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get package
    package = package_service.get_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Check if package is in use by any jobs
    if package_service.is_package_in_use(package_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete package that is in use by one or more jobs"
        )
    
    # Store package info for audit log
    package_name = package.name
    package_version = package.version
    
    # Delete package
    package_service.delete_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    # Log audit event in background
    if background_tasks:
        background_tasks.add_task(
            package_service.log_package_activity,
            package_id=package_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="delete_package",
            details={
                "name": package_name,
                "version": package_version
            }
        )

@router.post("/upload", response_model=PackageResponse)
def upload_package(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    version: str = None,
    entry_point: str = None,
    tags: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_create),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Upload a package file.
    
    Args:
        file: Package file (ZIP)
        name: Package name (optional, will be extracted from the ZIP if not provided)
        description: Package description
        version: Package version (optional, will be extracted from the ZIP if not provided)
        entry_point: Entry point script (optional, will be detected if not provided)
        tags: Comma-separated list of tags
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        PackageResponse: Created package
    """
    # Create package service
    package_service = PackageService(db)
    
    # Check file extension
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Package file must be a ZIP file"
        )
    
    try:
        # Process the uploaded file
        package = package_service.process_uploaded_package(
            file=file,
            name=name,
            description=description,
            version=version,
            entry_point=entry_point,
            tags=[tag.strip() for tag in tags.split(",")] if tags else None,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id)
        )
        
        # Log audit event in background
        if background_tasks:
            background_tasks.add_task(
                package_service.log_package_activity,
                package_id=str(package.package_id),
                tenant_id=str(current_user.tenant_id),
                user_id=str(current_user.user_id),
                action="upload_package",
                details={
                    "name": package.name,
                    "version": package.version,
                    "file_name": file.filename,
                    "file_size": file.size
                }
            )
        
        return package
        
    except Exception as e:
        logger.error(f"Error processing uploaded package: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing uploaded package: {str(e)}"
        )

@router.get("/{package_id}/download")
def download_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_read),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Download a package file.
    
    Args:
        package_id: Package ID
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        FileResponse: Package ZIP file
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get package
    package = package_service.get_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Get package file path
    file_path = package.storage_path
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package file not found"
        )
    
    # Log download in background
    if background_tasks:
        background_tasks.add_task(
            package_service.log_package_activity,
            package_id=package_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="download_package",
            details={
                "name": package.name,
                "version": package.version
            }
        )
    
    # Return file response
    return FileResponse(
        path=file_path,
        filename=f"{package.name}-{package.version}.zip",
        media_type="application/zip"
    )

@router.get("/name/{name}/versions", response_model=List[PackageVersionResponse])
def list_package_versions(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_read)
) -> Any:
    """
    List all versions of a package by name.
    
    Args:
        name: Package name
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        List[PackageVersionResponse]: List of package versions
    """
    # Create package service
    package_service = PackageService(db)
    
    # List package versions
    versions = package_service.list_package_versions(
        name=name,
        tenant_id=str(current_user.tenant_id)
    )
    
    return versions

@router.get("/name/{name}/latest", response_model=PackageResponse)
def get_latest_package_version(
    name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_read)
) -> Any:
    """
    Get the latest version of a package by name.
    
    Args:
        name: Package name
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        PackageResponse: Latest package version
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get latest package version
    package = package_service.get_latest_package_version(
        name=name,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Package with name {name} not found"
        )
    
    return package

@router.post("/{package_id}/deploy", response_model=PackageResponse)
def deploy_package(
    package_id: str,
    deploy_request: PackageDeployRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_deploy),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Deploy a package to production.
    
    Args:
        package_id: Package ID
        deploy_request: Deploy request data
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        PackageResponse: Deployed package
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get package
    package = package_service.get_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Check if package is already deployed
    if package.status == "production":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Package is already deployed to production"
        )
    
    # Deploy package
    package = package_service.deploy_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id),
        notes=deploy_request.deployment_notes
    )
    
    # Log deployment in background
    if background_tasks:
        background_tasks.add_task(
            package_service.log_package_activity,
            package_id=package_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="deploy_package",
            details={
                "name": package.name,
                "version": package.version,
                "notes": deploy_request.deployment_notes
            }
        )
    
    return package

@router.post("/{package_id}/validate", status_code=status.HTTP_200_OK)
def validate_package(
    package_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_package_read)
) -> Any:
    """
    Validate a package for errors.
    
    Args:
        package_id: Package ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        JSON response with validation results
    """
    # Create package service
    package_service = PackageService(db)
    
    # Get package
    package = package_service.get_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    
    # Validate package
    valid, issues = package_service.validate_package(
        package_id=package_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    return {
        "valid": valid,
        "issues": issues,
        "name": package.name,
        "version": package.version
    }