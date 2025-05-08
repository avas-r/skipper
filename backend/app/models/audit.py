"""
Audit model for audit logging.

This module defines the AuditLog model for tracking actions
and changes in the system for security and compliance.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, INET

from ..db.session import Base

class AuditLog(Base):
    """
    Audit log model for tracking actions and changes in the system.
    
    Audit logs record user actions for security and compliance purposes.
    """
    
    __tablename__ = "audit_logs"
    
    # Primary key
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Tenant foreign key
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.tenant_id"), nullable=False)
    tenant = relationship("Tenant")
    
    # User foreign key (optional - for system actions)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True)
    user = relationship("User")
    
    # Action information
    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Additional details
    details = Column(JSON, nullable=True)
    ip_address = Column(INET, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    def __repr__(self):
        """String representation of the audit log"""
        return f"<AuditLog {self.log_id} - {self.action} on {self.entity_type}>"