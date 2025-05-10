"""
JWT authentication module.

This module provides JWT token generation, validation, and handling
for user authentication.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..config import settings
from ..db.session import get_db
from ..models.user import User
from ..models.agent import Agent
from ..schemas.token import TokenPayload

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Token subject (typically user ID)
        expires_delta: Optional expiration delta (overrides default)
        
    Returns:
        str: Encoded JWT token
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Convert to timestamp for consistent handling
    exp_timestamp = int(expire.timestamp())
    now_timestamp = int(datetime.utcnow().timestamp())
    
    logger.info(f"Creating token: Expires at {expire} ({exp_timestamp}), current time: {datetime.utcnow()} ({now_timestamp})")
    logger.info(f"Token will be valid for {(exp_timestamp - now_timestamp) // 60} minutes")
    
    to_encode = {"exp": exp_timestamp, "sub": str(subject), "type": "access", "iat": now_timestamp}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        subject: Token subject (typically user ID)
        expires_delta: Optional expiration delta (overrides default)
        
    Returns:
        str: Encoded JWT token
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    # Convert to timestamp for consistent handling
    exp_timestamp = int(expire.timestamp())
    now_timestamp = int(datetime.utcnow().timestamp()) 
    
    logger.info(f"Creating refresh token: Expires at {expire} ({exp_timestamp}), current time: {datetime.utcnow()} ({now_timestamp})")
    logger.info(f"Refresh token will be valid for {(exp_timestamp - now_timestamp) // (60*24)} days")
    
    to_encode = {"exp": exp_timestamp, "sub": str(subject), "type": "refresh", "iat": now_timestamp}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        TokenPayload: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Verifying token: {token[:10]}...")
    
    try:
        # Don't verify expiration here - we'll check it manually
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False}
        )
        logger.info(f"Token payload: {payload}")
        
        token_data = TokenPayload(**payload)
        
        # Check if token is expired - with logging
        now_timestamp = int(datetime.utcnow().timestamp())
        exp_timestamp = token_data.exp
        
        # Add a 60-second buffer to account for clock skew
        buffer_timestamp = now_timestamp - 60
        
        # For logging - convert to datetime
        now = datetime.utcnow()
        exp_time = datetime.fromtimestamp(exp_timestamp)
        buffer_time = datetime.fromtimestamp(buffer_timestamp)
        
        logger.info(f"Token expiration: {exp_time} ({exp_timestamp}), current time: {now} ({now_timestamp})")
        logger.info(f"Time left until expiration: {exp_timestamp - now_timestamp} seconds")
        
        if exp_timestamp < buffer_timestamp:
            logger.warning(f"Token expired by {buffer_timestamp - exp_timestamp} seconds")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token has expired at {exp_time} ({exp_timestamp}). Current time is {now} ({now_timestamp})",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return token_data
        
    except jwt.exceptions.ExpiredSignatureError as e:
        logger.error(f"JWT expired signature error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired (signature check)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.exceptions.InvalidTokenError as e:
        logger.error(f"JWT invalid token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError as e:
        logger.error(f"Validation error for token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get the current authenticated user from a JWT token.
    
    This function is used as a dependency to authenticate API requests.
    
    Args:
        db: Database session
        token: JWT token from Authorization header
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_data = verify_token(token)
    
    # Verify token type is access token
    if token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.user_id == token_data.sub).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
        )
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current active superuser.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    # Check if user has superuser role
    for user_role in current_user.roles:
        if user_role.role.name == "superuser":
            return current_user
            
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="The user doesn't have enough privileges",
    )
    
# API key scheme for agent authentication
# We're using the same OAuth2 scheme for consistency
agent_auth_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False
)

async def get_current_agent(
    db: Session = Depends(get_db), token: str = Depends(agent_auth_scheme)
) -> Agent:
    """
    Get the current authenticated agent from API key or token.
    
    This function is used as a dependency to authenticate agent API requests.
    It supports both agent API keys and JWT tokens with agent claims.
    
    Args:
        db: Database session
        token: API key from Authorization header
        
    Returns:
        Agent: Current authenticated agent
        
    Raises:
        HTTPException: If token is invalid or agent not found
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # First, try to validate as JWT token
    try:
        token_data = verify_token(token)
        
        # Check if it has agent_id claim
        if hasattr(token_data, 'agent_id'):
            agent_id = token_data.agent_id
            agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
            if agent:
                return agent
    except (HTTPException, Exception):
        # If token is not a valid JWT, try as an API key
        pass
    
    # Try as API key - tokens stored in agent table
    agent = db.query(Agent).filter(Agent.api_key == token).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if agent is active
    if agent.status != "online" and agent.status != "idle":
        # We don't want to be too strict, since agents may be reconnecting
        # Just log, don't prevent authentication
        pass
        
    return agent