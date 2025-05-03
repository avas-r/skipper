"""
Configuration module for the orchestrator application.

This module handles loading configuration from environment variables,
configuration files, and provides default values. pydantic-settings
"""

import os
import json
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import PostgresDsn, field_validator, FieldValidationInfo
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings"""
    
    # Application name and metadata
    APP_NAME: str = "Python Automation Orchestrator"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Enterprise-grade orchestrator for Python automation scripts"
    
    # Environment - "development", "testing", "production"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_URL: Optional[str] = "/docs"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    
    # Security
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: List[str] = ["*"]
    
    # PostgreSQL connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "admin"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "skipper_db"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None
    

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    def assemble_db_uri(cls, v: Optional[str], info: field_validator) -> str:
        # if they passed in a full URI, just return it
        if isinstance(v, str) and v:
            return v

        data = info.data  # this is your dict of other field values
        return PostgresDsn.build(
            scheme="postgresql",
            username=data["POSTGRES_USER"],
            password=data["POSTGRES_PASSWORD"],
            host=data["POSTGRES_SERVER"],
            port=int(data["POSTGRES_PORT"]),
            path=f"/{data['POSTGRES_DB'] or ''}",
        )
    
    # Redis connection
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URI: Optional[str] = None
    
    @field_validator("REDIS_URI", mode="before")
    def assemble_redis_uri(cls, v: Optional[str], info: field_validator) -> str:
        # If user passed a URI already, just use it.
        if isinstance(v, str) and v:
            return v
        data = info.data
        pwd = data.get("REDIS_PASSWORD")
        password_str = f":{pwd}@" if pwd else ""
        return f"redis://{password_str}{data['REDIS_HOST']}:{data['REDIS_PORT']}/{data['REDIS_DB']}"  
    
    
    # RabbitMQ connection
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_VHOST: str = "/"
    RABBITMQ_URI: Optional[str] = None
    
    @field_validator("RABBITMQ_URI", mode="before")
    def assemble_rabbitmq_uri(cls, v: Optional[str], info: field_validator) -> str:
        if isinstance(v, str):
            return v
        data = info.data
        # Note: you may need to URL-encode the vhost if it contains "/" etc.
        return (
            f"amqp://{data['RABBITMQ_USER']}:"
            f"{data['RABBITMQ_PASSWORD']}@"
            f"{data['RABBITMQ_HOST']}:"
            f"{data['RABBITMQ_PORT']}/"
            f"{data['RABBITMQ_VHOST']}"
        )
    
    # MinIO (Object Storage) connection
    MINIO_HOST: str = "localhost"
    MINIO_PORT: int = 9000
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET: str = "orchestrator"
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = "orchestrator.log"
    
    # Agent settings
    AGENT_HEARTBEAT_TIMEOUT: int = 300  # seconds
    
    # Job settings
    DEFAULT_JOB_TIMEOUT: int = 3600  # seconds
    MAX_CONCURRENT_JOBS_PER_TENANT: int = 50
    
    # Cache settings
    CACHE_TTL: int = 60  # seconds
    
    # Multi-tenancy settings
    MULTI_TENANCY_ENABLED: bool = True
    DEFAULT_TENANT_ID: Optional[str] = None
    
    # File storage
    UPLOADS_FOLDER: str = "uploads"
    PACKAGES_FOLDER: str = "packages"
    
    class Config:
        """Pydantic Config"""
        env_file = ".venv"
        case_sensitive = True

# Generate a random secret key if not provided
def generate_secret_key() -> str:
    """Generate a random secret key"""
    return secrets.token_hex(32)

# Initialize settings
settings = Settings()

# Set a random secret key if not already set
if not settings.SECRET_KEY:
    settings.SECRET_KEY = generate_secret_key()

# Ensure required directories exist
def create_required_directories():
    """Create required directories if they don't exist"""
    Path(settings.UPLOADS_FOLDER).mkdir(exist_ok=True)
    Path(settings.PACKAGES_FOLDER).mkdir(exist_ok=True)

# Create directories
create_required_directories()