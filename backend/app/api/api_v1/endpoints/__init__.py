"""
API endpoints package for the orchestrator application.

This package contains all the FastAPI endpoint modules.
"""

# Make all endpoint modules available
from ...api_v1.endpoints import (
    agents_endpoint,
    analytics,
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
    users_endpoint
)