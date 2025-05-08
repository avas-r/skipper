"""
Models package for the orchestrator application.

This package contains SQLAlchemy models that define the database schema
for the orchestration system.
"""

# Import all models to make them available from the package
from .tenant import Tenant
from .user import User, Role, Permission, RolePermission, UserRole
from .agent import Agent, AgentLog, ServiceAccount, AgentSession
from .asset import Asset, AssetType, AssetFolder, AssetPermission
from .queue import Queue, QueueItem
from .package import Package, PackagePermission
from .schedule import Schedule
from .job import Job, JobExecution, JobDependency
from .notification import NotificationType, NotificationChannel, NotificationRule, Notification
from .audit import AuditLog
from .subscription_tier import SubscriptionTier
from .tenant_subscription import TenantSubscription

# Define all models for easy access
__all__ = [
    "Tenant",
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "Agent",
    "AgentLog",
    "ServiceAccount",
    "AgentSession",
    "Asset",
    "AssetType",
    "AssetFolder",
    "AssetPermission",
    "Queue",
    "QueueItem",
    "Package",
    "PackagePermission",
    "Schedule",
    "Job",
    "JobExecution",
    "JobDependency",
    "NotificationType",
    "NotificationChannel",
    "NotificationRule",
    "Notification",
    "AuditLog",
    "SubscriptionTier",
    "TenantSubscription",
]