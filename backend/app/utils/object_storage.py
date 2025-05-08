"""
Object storage utility module.

This module provides utilities for interacting with object storage (MinIO)
for storing logs, screenshots, packages, and other binary assets.
"""

import io
import logging
from typing import Optional, Union, List, Dict, Any

import minio
from minio.error import S3Error

from ..config import settings

logger = logging.getLogger(__name__)

# Global MinIO client instance
_minio_client = None

def get_minio_client():
    """
    Get the MinIO client instance.
    
    Returns:
        minio.Minio: MinIO client instance
    """
    global _minio_client
    if _minio_client is None:
        _minio_client = minio.Minio(
            f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        
        # Create bucket if it doesn't exist
        try:
            if not _minio_client.bucket_exists(settings.MINIO_BUCKET):
                _minio_client.make_bucket(settings.MINIO_BUCKET)
                logger.info(f"Created MinIO bucket: {settings.MINIO_BUCKET}")
        except S3Error as e:
            logger.error(f"Error checking/creating MinIO bucket: {e}")
            
    return _minio_client

class ObjectStorage:
    """
    Object storage utility for interacting with MinIO.
    
    Provides methods for uploading, downloading, listing, and deleting objects
    in MinIO object storage.
    """
    
    def __init__(self, bucket: Optional[str] = None):
        """
        Initialize the object storage utility.
        
        Args:
            bucket: Optional bucket name (defaults to settings.MINIO_BUCKET)
        """
        self.client = get_minio_client()
        self.bucket = bucket or settings.MINIO_BUCKET
        
    def upload_bytes(
        self, 
        data: Union[bytes, io.BytesIO], 
        object_name: str, 
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload bytes data to object storage.
        
        Args:
            data: Bytes data to upload
            object_name: Object name/path in storage
            content_type: Optional content type
            metadata: Optional object metadata
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            # Convert bytes to BytesIO if needed
            if isinstance(data, bytes):
                data = io.BytesIO(data)
                
            # Get data length
            data.seek(0, io.SEEK_END)
            length = data.tell()
            data.seek(0)
            
            # Upload object
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=object_name,
                data=data,
                length=length,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.debug(f"Uploaded object: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error uploading object {object_name}: {e}")
            return False
            
    def upload_file(
        self, 
        file_path: str, 
        object_name: Optional[str] = None,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload a file to object storage.
        
        Args:
            file_path: Path to file to upload
            object_name: Optional object name/path in storage (defaults to file name)
            content_type: Optional content type
            metadata: Optional object metadata
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            # Use file name if object_name not provided
            if not object_name:
                import os
                object_name = os.path.basename(file_path)
                
            # Upload file
            self.client.fput_object(
                bucket_name=self.bucket,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.debug(f"Uploaded file {file_path} to {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error uploading file {file_path} to {object_name}: {e}")
            return False
    
    def download_bytes(self, object_name: str) -> Optional[bytes]:
        """
        Download object as bytes.
        
        Args:
            object_name: Object name/path in storage
            
        Returns:
            Optional[bytes]: Object data as bytes or None if download fails
        """
        try:
            # Get object
            response = self.client.get_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            # Read data
            data = response.read()
            
            # Close response
            response.close()
            response.release_conn()
            
            logger.debug(f"Downloaded object: {object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"Error downloading object {object_name}: {e}")
            return None
            
    def download_file(self, object_name: str, file_path: str) -> bool:
        """
        Download object to a file.
        
        Args:
            object_name: Object name/path in storage
            file_path: Path to save the file
            
        Returns:
            bool: True if download successful, False otherwise
        """
        try:
            # Download object
            self.client.fget_object(
                bucket_name=self.bucket,
                object_name=object_name,
                file_path=file_path
            )
            
            logger.debug(f"Downloaded object {object_name} to {file_path}")
            return True
            
        except S3Error as e:
            logger.error(f"Error downloading object {object_name} to {file_path}: {e}")
            return False
            
    def list_objects(self, prefix: str, recursive: bool = True) -> List[Dict[str, Any]]:
        """
        List objects with a given prefix.
        
        Args:
            prefix: Prefix to filter objects
            recursive: Whether to list objects recursively
            
        Returns:
            List[Dict[str, Any]]: List of object information dictionaries
        """
        try:
            # List objects
            objects = self.client.list_objects(
                bucket_name=self.bucket,
                prefix=prefix,
                recursive=recursive
            )
            
            # Convert to list of dictionaries
            result = []
            for obj in objects:
                result.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified,
                    "etag": obj.etag
                })
                
            return result
            
        except S3Error as e:
            logger.error(f"Error listing objects with prefix {prefix}: {e}")
            return []
            
    def delete_object(self, object_name: str) -> bool:
        """
        Delete an object.
        
        Args:
            object_name: Object name/path in storage
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            # Delete object
            self.client.remove_object(
                bucket_name=self.bucket,
                object_name=object_name
            )
            
            logger.debug(f"Deleted object: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"Error deleting object {object_name}: {e}")
            return False
            
    def delete_objects(self, object_names: List[str]) -> bool:
        """
        Delete multiple objects.
        
        Args:
            object_names: List of object names/paths in storage
            
        Returns:
            bool: True if all deletions successful, False otherwise
        """
        try:
            # Convert list of object names to object deletion format
            delete_objects = [minio.DeleteObject(name) for name in object_names]
            
            # Delete objects
            errors = self.client.remove_objects(
                bucket_name=self.bucket,
                delete_object_list=delete_objects
            )
            
            # Check for errors
            error_count = 0
            for error in errors:
                logger.error(f"Error deleting object {error.object_name}: {error.error_message}")
                error_count += 1
                
            if error_count == 0:
                logger.debug(f"Deleted {len(object_names)} objects")
                return True
            else:
                logger.warning(f"Deleted {len(object_names) - error_count} objects, {error_count} errors")
                return False
                
        except S3Error as e:
            logger.error(f"Error deleting objects: {e}")
            return False
            
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        Get a presigned URL for an object.
        
        Args:
            object_name: Object name/path in storage
            expires: URL expiration time in seconds
            
        Returns:
            Optional[str]: Presigned URL or None if generation fails
        """
        try:
            # Generate URL
            url = self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=object_name,
                expires=expires
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            return None