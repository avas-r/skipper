"""
Asset management endpoints for the orchestrator API.

This module provides endpoints for managing assets, including credentials,
configurations, and other sensitive data.
"""

import logging
from typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from ....auth.jwt import get_current_active_user
from ....auth.permissions import PermissionChecker
from ....db.session import get_db
from ....models import User, Asset, AssetType, AssetFolder
from ....schemas.asset import (
    AssetCreate, 
    AssetUpdate, 
    AssetResponse,
    AssetValueResponse,
    AssetTypeResponse,
    AssetFolderCreate,
    AssetFolderUpdate,
    AssetFolderResponse
)
from ....services.asset_service import AssetService
from ..dependencies import get_multi_tenant_filter

router = APIRouter()
logger = logging.getLogger(__name__)

# Permission dependencies
require_asset_read = PermissionChecker(["asset:read"])
require_asset_create = PermissionChecker(["asset:create"])
require_asset_update = PermissionChecker(["asset:update"])
require_asset_delete = PermissionChecker(["asset:delete"])

@router.get("/", response_model=List[AssetResponse])
def list_assets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_read),
    skip: int = 0,
    limit: int = 100,
    folder_id: Optional[str] = None,
    asset_type_id: Optional[str] = None,
    search: Optional[str] = None
) -> Any:
    """
    List all assets with optional filtering.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        skip: Number of assets to skip
        limit: Maximum number of assets to return
        folder_id: Optional folder filter
        asset_type_id: Optional asset type filter
        search: Optional search term
        
    Returns:
        List[AssetResponse]: List of assets
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # List assets
    assets = asset_service.list_assets(
        tenant_id=str(current_user.tenant_id),
        folder_id=folder_id,
        asset_type_id=asset_type_id,
        search=search,
        skip=skip,
        limit=limit
    )
    
    return assets

@router.post("/", response_model=AssetResponse)
def create_asset(
    asset_in: AssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_create),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Create a new asset.
    
    Args:
        asset_in: Asset creation data
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        AssetResponse: Created asset
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Check if asset already exists
    existing_asset = asset_service.get_asset_by_name(
        name=asset_in.name,
        tenant_id=str(current_user.tenant_id)
    )
    
    if existing_asset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset with name {asset_in.name} already exists"
        )
    
    # Validate asset type
    asset_type = asset_service.get_asset_type(asset_in.asset_type_id)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Asset type with ID {asset_in.asset_type_id} not found"
        )
    
    # Validate folder if provided
    if asset_in.folder_id:
        folder = asset_service.get_folder(
            folder_id=asset_in.folder_id,
            tenant_id=str(current_user.tenant_id)
        )
        
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Folder with ID {asset_in.folder_id} not found"
            )
    
    # Create asset
    asset = asset_service.create_asset(
        asset_in=asset_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    # Log audit event in background
    if background_tasks:
        background_tasks.add_task(
            asset_service.log_asset_activity,
            asset_id=str(asset.asset_id),
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="create_asset",
            details={
                "name": asset.name,
                "asset_type_id": str(asset.asset_type_id),
                "folder_id": str(asset.folder_id) if asset.folder_id else None,
                "is_encrypted": asset.is_encrypted
            }
        )
    
    return asset

@router.get("/{asset_id}", response_model=AssetResponse)
def read_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_read)
) -> Any:
    """
    Get asset by ID.
    
    Args:
        asset_id: Asset ID
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        AssetResponse: Asset
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Get asset
    asset = asset_service.get_asset(
        asset_id=asset_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: str,
    asset_in: AssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_update),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Update an asset.
    
    Args:
        asset_id: Asset ID
        asset_in: Asset update data
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        AssetResponse: Updated asset
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Get asset
    asset = asset_service.get_asset(
        asset_id=asset_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Check if name is being changed to an existing one
    if asset_in.name and asset_in.name != asset.name:
        existing_asset = asset_service.get_asset_by_name(
            name=asset_in.name,
            tenant_id=str(current_user.tenant_id)
        )
        
        if existing_asset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Asset with name {asset_in.name} already exists"
            )
    
    # Validate folder if provided
    if asset_in.folder_id:
        folder = asset_service.get_folder(
            folder_id=asset_in.folder_id,
            tenant_id=str(current_user.tenant_id)
        )
        
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Folder with ID {asset_in.folder_id} not found"
            )
    
    # Update asset
    updated_asset = asset_service.update_asset(
        asset_id=asset_id,
        asset_in=asset_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    # Log audit event in background
    if background_tasks:
        update_details = {
            "name": updated_asset.name,
            "updated_fields": list(asset_in.dict(exclude_unset=True).keys())
        }
        
        background_tasks.add_task(
            asset_service.log_asset_activity,
            asset_id=asset_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="update_asset",
            details=update_details
        )
    
    return updated_asset

@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_delete),
    background_tasks: BackgroundTasks = None
) -> None:
    """
    Delete an asset.
    
    Args:
        asset_id: Asset ID
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Get asset
    asset = asset_service.get_asset(
        asset_id=asset_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Store asset name for audit log
    asset_name = asset.name
    
    # Delete asset
    asset_service.delete_asset(
        asset_id=asset_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    # Log audit event in background
    if background_tasks:
        background_tasks.add_task(
            asset_service.log_asset_activity,
            asset_id=asset_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="delete_asset",
            details={"name": asset_name}
        )

@router.get("/{asset_id}/value", response_model=AssetValueResponse)
def get_asset_value(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_read),
    background_tasks: BackgroundTasks = None
) -> Any:
    """
    Get asset value, including decryption if needed.
    
    Args:
        asset_id: Asset ID
        db: Database session
        current_user: Current user
        _: Permission check
        background_tasks: Background tasks
        
    Returns:
        AssetValueResponse: Asset value
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Get asset with decryption
    asset_with_value = asset_service.get_asset_with_value(
        asset_id=asset_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not asset_with_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )
    
    # Log access to sensitive asset in background
    if background_tasks and asset_with_value.get("is_encrypted"):
        background_tasks.add_task(
            asset_service.log_asset_activity,
            asset_id=asset_id,
            tenant_id=str(current_user.tenant_id),
            user_id=str(current_user.user_id),
            action="access_asset_value",
            details={"name": asset_with_value.get("name")}
        )
    
    return asset_with_value

@router.get("/types/", response_model=List[AssetTypeResponse])
def list_asset_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_read)
) -> Any:
    """
    List all asset types.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        List[AssetTypeResponse]: List of asset types
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # List asset types
    asset_types = asset_service.list_asset_types()
    
    return asset_types

@router.get("/folders/", response_model=List[AssetFolderResponse])
def list_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_read),
    parent_folder_id: Optional[str] = None
) -> Any:
    """
    List asset folders.
    
    Args:
        db: Database session
        current_user: Current user
        _: Permission check
        parent_folder_id: Optional parent folder ID for hierarchical listing
        
    Returns:
        List[AssetFolderResponse]: List of asset folders
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # List folders
    folders = asset_service.list_folders(
        tenant_id=str(current_user.tenant_id),
        parent_folder_id=parent_folder_id
    )
    
    return folders

@router.post("/folders/", response_model=AssetFolderResponse)
def create_folder(
    folder_in: AssetFolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_create)
) -> Any:
    """
    Create a new asset folder.
    
    Args:
        folder_in: Folder creation data
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        AssetFolderResponse: Created folder
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Check if folder already exists
    existing_folder = asset_service.get_folder_by_name(
        name=folder_in.name,
        tenant_id=str(current_user.tenant_id),
        parent_folder_id=folder_in.parent_folder_id
    )
    
    if existing_folder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Folder with name {folder_in.name} already exists in this location"
        )
    
    # Validate parent folder if provided
    if folder_in.parent_folder_id:
        parent_folder = asset_service.get_folder(
            folder_id=folder_in.parent_folder_id,
            tenant_id=str(current_user.tenant_id)
        )
        
        if not parent_folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parent folder with ID {folder_in.parent_folder_id} not found"
            )
    
    # Create folder
    folder = asset_service.create_folder(
        folder_in=folder_in,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.user_id)
    )
    
    return folder

@router.put("/folders/{folder_id}", response_model=AssetFolderResponse)
def update_folder(
    folder_id: str,
    folder_in: AssetFolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_update)
) -> Any:
    """
    Update an asset folder.
    
    Args:
        folder_id: Folder ID
        folder_in: Folder update data
        db: Database session
        current_user: Current user
        _: Permission check
        
    Returns:
        AssetFolderResponse: Updated folder
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Get folder
    folder = asset_service.get_folder(
        folder_id=folder_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Check if name is being changed to an existing one
    if folder_in.name and folder_in.name != folder.name:
        existing_folder = asset_service.get_folder_by_name(
            name=folder_in.name,
            tenant_id=str(current_user.tenant_id),
            parent_folder_id=folder.parent_folder_id
        )
        
        if existing_folder:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Folder with name {folder_in.name} already exists in this location"
            )
    
    # Update folder
    updated_folder = asset_service.update_folder(
        folder_id=folder_id,
        folder_in=folder_in,
        tenant_id=str(current_user.tenant_id)
    )
    
    return updated_folder

@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    _: bool = Depends(require_asset_delete)
) -> None:
    """
    Delete an asset folder.
    
    Args:
        folder_id: Folder ID
        db: Database session
        current_user: Current user
        _: Permission check
    """
    # Create asset service
    asset_service = AssetService(db)
    
    # Get folder
    folder = asset_service.get_folder(
        folder_id=folder_id,
        tenant_id=str(current_user.tenant_id)
    )
    
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Check if folder has assets or subfolders
    has_assets = asset_service.folder_has_assets(folder_id)
    has_subfolders = asset_service.folder_has_subfolders(folder_id)
    
    if has_assets or has_subfolders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete folder that contains assets or subfolders"
        )
    
    # Delete folder
    asset_service.delete_folder(
        folder_id=folder_id,
        tenant_id=str(current_user.tenant_id)
    )