"""
Token schemas for the orchestrator API.

This module defines Pydantic models for authentication tokens.
"""

from typing import Optional

from pydantic import BaseModel

class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str

class TokenPayload(BaseModel):
    """Schema for token payload"""
    sub: Optional[str] = None
    exp: int
    type: str = "access"  # "access" or "refresh"
    agent_id: Optional[str] = None  # Set for agent tokens