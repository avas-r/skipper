"""
API router for the orchestrator application.

This module configures the API router and includes all endpoint modules.
"""

from fastapi import APIRouter

from .endpoints import (
    agents_endpoint,
    assets_endpoint,
    auth_endpoint,
    executions_endpoint,
    jobs_endpoint,
    notifications_endpoint,
    packages_endpoint,
    queues_endpoint,
    schedules_endpoint,
    service_account_endpoint,
    subscriptions_endpoint,
    tenants_endpoint,
    analytics,
    agent_packages,
    users_endpoint
)

# Create API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_endpoint.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users_endpoint.router, prefix="/users", tags=["Users"])
api_router.include_router(tenants_endpoint.router, prefix="/tenants", tags=["Tenants"])
api_router.include_router(agents_endpoint.router, prefix="/agents", tags=["Agents"])
api_router.include_router(assets_endpoint.router, prefix="/assets", tags=["Assets"])
api_router.include_router(packages_endpoint.router, prefix="/packages", tags=["Packages"])
api_router.include_router(queues_endpoint.router, prefix="/queues", tags=["Queues"])
api_router.include_router(schedules_endpoint.router, prefix="/schedules", tags=["Schedules"])
api_router.include_router(jobs_endpoint.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(executions_endpoint.router, prefix="/job-executions", tags=["Job Executions"])
api_router.include_router(notifications_endpoint.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(subscriptions_endpoint.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(service_account_endpoint.router, prefix="/service-accounts", tags=["Service Accounts"])
api_router.include_router(agent_packages.router, prefix="/agent-packages", tags=["Agent Packages"])
