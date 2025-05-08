"""
API router for the orchestrator application.

This module configures the API router and includes all endpoint modules.
"""

from fastapi import APIRouter

from .endpoints import (
    auth,
    users,
    tenants,
    agents,
    assets,
    packages,
    queues,
    schedules,
    jobs,
    executions,
    notifications,
    analytics,
    subscriptions,
    service_account
)

# Create API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(packages.router, prefix="/packages", tags=["Packages"])
api_router.include_router(queues.router, prefix="/queues", tags=["Queues"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(executions.router, prefix="/job-executions", tags=["Job Executions"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(service_account.router, prefix="/service-accounts", tags=["Service Accounts"])
