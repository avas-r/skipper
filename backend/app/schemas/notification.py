"""
Notification schemas for the orchestrator API.

This module defines Pydantic models for notification-related API requests and responses.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

class NotificationChannelBase(BaseModel):
    """Base schema for notification channel data"""
    name: str
    type: str = Field(..., description="Channel type (email, slack, webhook, etc.)")
    configuration: Dict[str, Any] = Field(..., description="Channel-specific configuration")

class NotificationChannelCreate(NotificationChannelBase):
    """Schema for creating a new notification channel"""
    
    @validator("type")
    def validate_type(cls, v):
        """Validate notification channel type"""
        valid_types = ["email", "slack", "webhook", "teams", "sms"]
        if v not in valid_types:
            raise ValueError(f"Invalid channel type. Must be one of: {', '.join(valid_types)}")
        return v
    
    @validator("configuration")
    def validate_configuration(cls, v, values):
        """Validate configuration based on channel type"""
        if "type" not in values:
            return v
            
        channel_type = values["type"]
        
        if channel_type == "email":
            required = ["recipient_email"]
        elif channel_type == "slack":
            required = ["webhook_url"]
        elif channel_type == "webhook":
            required = ["url", "method"]
        elif channel_type == "teams":
            required = ["webhook_url"]
        elif channel_type == "sms":
            required = ["phone_number"]
        else:
            return v
            
        missing = [field for field in required if field not in v]
        if missing:
            raise ValueError(f"Missing required configuration fields for {channel_type}: {', '.join(missing)}")
            
        return v

class NotificationChannelUpdate(BaseModel):
    """Schema for updating a notification channel"""
    name: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class NotificationChannelInDB(NotificationChannelBase):
    """Base schema for notification channel in database"""
    channel_id: UUID
    tenant_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class NotificationChannelResponse(NotificationChannelInDB):
    """Schema for notification channel response"""
    pass

class NotificationTypeBase(BaseModel):
    """Base schema for notification type data"""
    name: str
    description: Optional[str] = None

class NotificationTypeResponse(NotificationTypeBase):
    """Schema for notification type response"""
    type_id: UUID
    created_at: datetime
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class NotificationRuleBase(BaseModel):
    """Base schema for notification rule data"""
    name: str
    notification_type_id: UUID
    channel_id: UUID
    conditions: Dict[str, Any] = Field(..., description="Conditions for triggering notification")

class NotificationRuleCreate(NotificationRuleBase):
    """Schema for creating a new notification rule"""
    pass

class NotificationRuleUpdate(BaseModel):
    """Schema for updating a notification rule"""
    name: Optional[str] = None
    notification_type_id: Optional[UUID] = None
    channel_id: Optional[UUID] = None
    conditions: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

class NotificationRuleInDB(NotificationRuleBase):
    """Base schema for notification rule in database"""
    rule_id: UUID
    tenant_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class NotificationRuleResponse(NotificationRuleInDB):
    """Schema for notification rule response"""
    notification_type: NotificationTypeResponse
    channel: NotificationChannelResponse

class NotificationBase(BaseModel):
    """Base schema for notification data"""
    subject: str
    message: str
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    info: Optional[Dict[str, Any]] = None

class NotificationCreate(NotificationBase):
    """Schema for creating a new notification"""
    rule_id: UUID

class NotificationInDB(NotificationBase):
    """Base schema for notification in database"""
    notification_id: UUID
    tenant_id: UUID
    rule_id: UUID
    status: str
    created_at: datetime
    sent_at: Optional[datetime] = None
    
    class Config:
        """Configuration for Pydantic model"""
        from_attributes = True

class NotificationResponse(NotificationInDB):
    """Schema for notification response"""
    rule: NotificationRuleResponse

class NotificationCountResponse(BaseModel):
    """Schema for notification count response"""
    total: int
    pending: int
    sent: int
    failed: int

class NotificationTestRequest(BaseModel):
    """Schema for testing a notification channel"""
    channel_id: UUID
    subject: str = "Test Notification"
    message: str = "This is a test notification sent from the Orchestrator system."