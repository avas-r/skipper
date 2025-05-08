"""
Asset service for managing asset operations.

This module provides services for managing assets, including credential storage,
configuration management, and secure value handling.
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from ..models import Asset, AssetType, AssetFolder, AuditLog
from ..schemas.asset import AssetCreate, AssetUpdate, AssetFolderCreate, AssetFolderUpdate
from ..utils.security import encrypt_value, decrypt_value

logger = logging.getLogger(__name__)

class AssetService:
    """Service for managing assets"""
    
    def __init__(self, db: Session):
        """
        Initialize the asset service.
        
        Args:
            db: Database session
        """
        self.db = db
        
    def create_asset(self, asset_in: AssetCreate, tenant_id: str, user_id: str) -> Asset:
        """
        Create a new asset.
        
        Args:
            asset_in: Asset creation data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Asset: Created asset
        """
        # Handle value encryption if needed
        value = asset_in.value
        if asset_in.is_encrypted and value:
            value = encrypt_value(value)
        
        # Create asset
        db_asset = Asset(
            asset_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            asset_type_id=asset_in.asset_type_id,
            folder_id=asset_in.folder_id,
            name=asset_in.name,
            description=asset_in.description,
            is_encrypted=asset_in.is_encrypted,
            value=value,
            created_by=uuid.UUID(user_id),
            updated_by=uuid.UUID(user_id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
        
        self.db.add(db_asset)
        self.db.commit()
        self.db.refresh(db_asset)
        
        return db_asset
    
    def get_asset(self, asset_id: str, tenant_id: str) -> Optional[Asset]:
        """
        Get an asset by ID.
        
        Args:
            asset_id: Asset ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Asset]: Asset or None if not found
        """
        return self.db.query(Asset).filter(
            Asset.asset_id == asset_id,
            Asset.tenant_id == tenant_id
        ).first()
    
    def get_asset_by_name(self, name: str, tenant_id: str) -> Optional[Asset]:
        """
        Get an asset by name.
        
        Args:
            name: Asset name
            tenant_id: Tenant ID
            
        Returns:
            Optional[Asset]: Asset or None if not found
        """
        return self.db.query(Asset).filter(
            Asset.name == name,
            Asset.tenant_id == tenant_id
        ).first()
    
    def list_assets(
        self,
        tenant_id: str,
        folder_id: Optional[str] = None,
        asset_type_id: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Asset]:
        """
        List assets with filtering.
        
        Args:
            tenant_id: Tenant ID
            folder_id: Optional folder filter
            asset_type_id: Optional asset type filter
            search: Optional search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Asset]: List of assets
        """
        query = self.db.query(Asset).filter(Asset.tenant_id == tenant_id)
        
        # Apply folder filter
        if folder_id:
            query = query.filter(Asset.folder_id == folder_id)
            
        # Apply asset type filter
        if asset_type_id:
            query = query.filter(Asset.asset_type_id == asset_type_id)
            
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Asset.name.ilike(f"%{search}%"),
                    Asset.description.ilike(f"%{search}%")
                )
            )
        
        # Apply pagination
        total = query.count()
        assets = query.order_by(Asset.name).offset(skip).limit(limit).all()
        
        # Remove sensitive values from responses
        for asset in assets:
            asset.value = None
        
        return assets
    
    def update_asset(self, asset_id: str, asset_in: AssetUpdate, tenant_id: str, user_id: str) -> Optional[Asset]:
        """
        Update an asset.
        
        Args:
            asset_id: Asset ID
            asset_in: Asset update data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            Optional[Asset]: Updated asset or None if not found
        """
        # Get asset
        asset = self.db.query(Asset).filter(
            Asset.asset_id == asset_id,
            Asset.tenant_id == tenant_id
        ).first()
        
        if not asset:
            return None
        
        # Prepare update data
        update_data = asset_in.dict(exclude_unset=True)
        
        # Handle value encryption if needed
        if "value" in update_data and update_data["value"] is not None:
            if update_data.get("is_encrypted", asset.is_encrypted):
                update_data["value"] = encrypt_value(update_data["value"])
        
        # Update asset attributes
        for key, value in update_data.items():
            setattr(asset, key, value)
            
        # Update metadata
        asset.updated_at = datetime.utcnow()
        asset.updated_by = uuid.UUID(user_id)
        asset.version += 1
        
        self.db.commit()
        self.db.refresh(asset)
        
        # Remove sensitive value from response
        asset.value = None
        
        return asset
    
    def delete_asset(self, asset_id: str, tenant_id: str) -> bool:
        """
        Delete an asset.
        
        Args:
            asset_id: Asset ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get asset
        asset = self.db.query(Asset).filter(
            Asset.asset_id == asset_id,
            Asset.tenant_id == tenant_id
        ).first()
        
        if not asset:
            return False
        
        # Delete asset
        self.db.delete(asset)
        self.db.commit()
        
        return True
    
    def get_asset_with_value(self, asset_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an asset with its actual value, decrypting if needed.
        
        Args:
            asset_id: Asset ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[Dict[str, Any]]: Asset with value or None if not found
        """
        # Get asset
        asset = self.db.query(Asset).filter(
            Asset.asset_id == asset_id,
            Asset.tenant_id == tenant_id
        ).first()
        
        if not asset:
            return None
        
        # Create a copy to avoid modifying the database entity
        result = {
            "asset_id": asset.asset_id,
            "name": asset.name,
            "description": asset.description,
            "asset_type_id": asset.asset_type_id,
            "is_encrypted": asset.is_encrypted,
            "value": asset.value,
            "version": asset.version
        }
        
        # Decrypt value if encrypted
        if asset.is_encrypted and asset.value:
            try:
                result["value"] = decrypt_value(asset.value)
            except Exception as e:
                logger.error(f"Error decrypting asset value: {e}")
                result["value"] = None
                
        return result
    
    def get_asset_type(self, asset_type_id: str) -> Optional[AssetType]:
        """
        Get an asset type by ID.
        
        Args:
            asset_type_id: Asset type ID
            
        Returns:
            Optional[AssetType]: Asset type or None if not found
        """
        return self.db.query(AssetType).filter(AssetType.asset_type_id == asset_type_id).first()
    
    def list_asset_types(self) -> List[AssetType]:
        """
        List all asset types.
        
        Returns:
            List[AssetType]: List of asset types
        """
        return self.db.query(AssetType).order_by(AssetType.name).all()
    
    def create_asset_type(self, name: str, description: Optional[str] = None) -> AssetType:
        """
        Create a new asset type.
        
        Args:
            name: Asset type name
            description: Optional description
            
        Returns:
            AssetType: Created asset type
        """
        # Create asset type
        db_asset_type = AssetType(
            asset_type_id=uuid.uuid4(),
            name=name,
            description=description,
            created_at=datetime.utcnow()
        )
        
        self.db.add(db_asset_type)
        self.db.commit()
        self.db.refresh(db_asset_type)
        
        return db_asset_type
    
    def get_folder(self, folder_id: str, tenant_id: str) -> Optional[AssetFolder]:
        """
        Get an asset folder by ID.
        
        Args:
            folder_id: Folder ID
            tenant_id: Tenant ID
            
        Returns:
            Optional[AssetFolder]: Folder or None if not found
        """
        return self.db.query(AssetFolder).filter(
            AssetFolder.folder_id == folder_id,
            AssetFolder.tenant_id == tenant_id
        ).first()
    
    def get_folder_by_name(
        self,
        name: str,
        tenant_id: str,
        parent_folder_id: Optional[str] = None
    ) -> Optional[AssetFolder]:
        """
        Get an asset folder by name and optional parent folder.
        
        Args:
            name: Folder name
            tenant_id: Tenant ID
            parent_folder_id: Optional parent folder ID
            
        Returns:
            Optional[AssetFolder]: Folder or None if not found
        """
        query = self.db.query(AssetFolder).filter(
            AssetFolder.name == name,
            AssetFolder.tenant_id == tenant_id
        )
        
        if parent_folder_id:
            query = query.filter(AssetFolder.parent_folder_id == parent_folder_id)
        else:
            query = query.filter(AssetFolder.parent_folder_id.is_(None))
            
        return query.first()
    
    def list_folders(
        self,
        tenant_id: str,
        parent_folder_id: Optional[str] = None
    ) -> List[AssetFolder]:
        """
        List asset folders.
        
        Args:
            tenant_id: Tenant ID
            parent_folder_id: Optional parent folder ID for hierarchical listing
            
        Returns:
            List[AssetFolder]: List of folders
        """
        query = self.db.query(AssetFolder).filter(AssetFolder.tenant_id == tenant_id)
        
        if parent_folder_id:
            query = query.filter(AssetFolder.parent_folder_id == parent_folder_id)
        else:
            query = query.filter(AssetFolder.parent_folder_id.is_(None))
            
        return query.order_by(AssetFolder.name).all()
    
    def create_folder(
        self,
        folder_in: AssetFolderCreate,
        tenant_id: str,
        user_id: str
    ) -> AssetFolder:
        """
        Create a new asset folder.
        
        Args:
            folder_in: Folder creation data
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            AssetFolder: Created folder
        """
        # Create folder
        db_folder = AssetFolder(
            folder_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            name=folder_in.name,
            parent_folder_id=folder_in.parent_folder_id,
            created_by=uuid.UUID(user_id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(db_folder)
        self.db.commit()
        self.db.refresh(db_folder)
        
        return db_folder
    
    def update_folder(
        self,
        folder_id: str,
        folder_in: AssetFolderUpdate,
        tenant_id: str
    ) -> Optional[AssetFolder]:
        """
        Update an asset folder.
        
        Args:
            folder_id: Folder ID
            folder_in: Folder update data
            tenant_id: Tenant ID
            
        Returns:
            Optional[AssetFolder]: Updated folder or None if not found
        """
        # Get folder
        folder = self.db.query(AssetFolder).filter(
            AssetFolder.folder_id == folder_id,
            AssetFolder.tenant_id == tenant_id
        ).first()
        
        if not folder:
            return None
        
        # Update folder attributes
        for key, value in folder_in.dict(exclude_unset=True).items():
            setattr(folder, key, value)
            
        # Update timestamp
        folder.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(folder)
        
        return folder
    
    def delete_folder(self, folder_id: str, tenant_id: str) -> bool:
        """
        Delete an asset folder.
        
        Args:
            folder_id: Folder ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if deletion successful
        """
        # Get folder
        folder = self.db.query(AssetFolder).filter(
            AssetFolder.folder_id == folder_id,
            AssetFolder.tenant_id == tenant_id
        ).first()
        
        if not folder:
            return False
        
        # Delete folder
        self.db.delete(folder)
        self.db.commit()
        
        return True
    
    def folder_has_assets(self, folder_id: str) -> bool:
        """
        Check if a folder contains any assets.
        
        Args:
            folder_id: Folder ID
            
        Returns:
            bool: True if folder has assets
        """
        count = self.db.query(func.count(Asset.asset_id)).filter(
            Asset.folder_id == folder_id
        ).scalar()
        
        return count > 0
    
    def folder_has_subfolders(self, folder_id: str) -> bool:
        """
        Check if a folder contains any subfolders.
        
        Args:
            folder_id: Folder ID
            
        Returns:
            bool: True if folder has subfolders
        """
        count = self.db.query(func.count(AssetFolder.folder_id)).filter(
            AssetFolder.parent_folder_id == folder_id
        ).scalar()
        
        return count > 0
    
    def log_asset_activity(
        self,
        asset_id: str,
        tenant_id: str,
        user_id: str,
        action: str,
        details: Dict[str, Any]
    ) -> AuditLog:
        """
        Log asset activity for audit purposes.
        
        Args:
            asset_id: Asset ID
            tenant_id: Tenant ID
            user_id: User ID
            action: Action performed
            details: Additional details
            
        Returns:
            AuditLog: Created audit log entry
        """
        # Create audit log
        audit_log = AuditLog(
            log_id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            user_id=uuid.UUID(user_id),
            action=action,
            entity_type="asset",
            entity_id=uuid.UUID(asset_id),
            created_at=datetime.utcnow(),
            details=details
        )
        
        self.db.add(audit_log)
        self.db.commit()
        
        return audit_log
    
    def get_asset_tree(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get hierarchical tree of folders and assets.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            List[Dict[str, Any]]: Tree structure
        """
        # Get all folders
        folders = self.db.query(AssetFolder).filter(
            AssetFolder.tenant_id == tenant_id
        ).all()
        
        # Get all assets
        assets = self.db.query(Asset).filter(
            Asset.tenant_id == tenant_id
        ).all()
        
        # Build folder tree
        folder_map = {}
        root_folders = []
        
        for folder in folders:
            folder_item = {
                "id": str(folder.folder_id),
                "name": folder.name,
                "type": "folder",
                "parent_id": str(folder.parent_folder_id) if folder.parent_folder_id else None,
                "children": []
            }
            
            folder_map[str(folder.folder_id)] = folder_item
            
            if folder.parent_folder_id is None:
                root_folders.append(folder_item)
                
        # Add child folders
        for folder in folders:
            if folder.parent_folder_id:
                parent_id = str(folder.parent_folder_id)
                if parent_id in folder_map:
                    folder_map[parent_id]["children"].append(folder_map[str(folder.folder_id)])
        
        # Add assets to folders
        for asset in assets:
            asset_item = {
                "id": str(asset.asset_id),
                "name": asset.name,
                "type": "asset",
                "parent_id": str(asset.folder_id) if asset.folder_id else None,
                "asset_type_id": asset.asset_type_id,
                "is_encrypted": asset.is_encrypted
            }
            
            if asset.folder_id:
                folder_id = str(asset.folder_id)
                if folder_id in folder_map:
                    if "children" not in folder_map[folder_id]:
                        folder_map[folder_id]["children"] = []
                    folder_map[folder_id]["children"].append(asset_item)
            else:
                root_folders.append(asset_item)
                
        return root_folders