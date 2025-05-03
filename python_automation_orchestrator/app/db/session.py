"""
Database session management module.

This module provides the SQLAlchemy engine and session factory
for database operations.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, Request

from ..config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    str(settings.SQLALCHEMY_DATABASE_URI),
    pool_pre_ping=True,  # Check connection before using from pool
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=20,        # Connection pool size
    max_overflow=10,     # Allow up to 10 additional connections
    echo=settings.DEBUG, # Log SQL if in debug mode
)

# Create sessionmaker for creating database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for declarative models
Base = declarative_base()

def get_db() -> Session:
    """
    Get a database session from the request state or create a new one.
    
    This function is used as a FastAPI dependency to provide database
    sessions to API endpoints.
    
    Returns:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_from_request(request: Request) -> Session:
    """
    Get the database session from the request state.
    
    Args:
        request (Request): The FastAPI request object
        
    Returns:
        Session: SQLAlchemy database session
    """
    return request.state.db