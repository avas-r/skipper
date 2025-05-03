"""
Database base module with shared model definitions.

This module imports all SQLAlchemy models to ensure they are registered
with the Base class before creating tables.
"""

# Import Base
from .session import Base

# Import all models to ensure they are registered with Base
from ..models.tenant import Tenant
from ..models.user import User, Role, Permission, RolePermission, UserRole
from ..models.agent import Agent, AgentLog
from ..models.asset import Asset, AssetType, AssetFolder, AssetPermission
from ..models.queue import Queue, QueueItem
from ..models.package import Package, PackagePermission
from ..models.schedule import Schedule
from ..models.job import Job, JobExecution, JobDependency
from ..models.notification import (
    NotificationType, 
    NotificationChannel,
    NotificationRule,
    Notification
)
from ..models.audit import AuditLog

# Base model class for all models
class BaseModel:
    """Base model with common functionality for all models"""
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}