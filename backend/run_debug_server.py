#!/usr/bin/env python3
import os
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Debug API Server")

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class OrganizationRegistration(BaseModel):
    organization_name: str
    full_name: str
    email: str
    password: str
    subscription_tier: str = "free"

# Routes
@app.get("/api/v1/healthcheck")
async def healthcheck():
    logger.info("Healthcheck request received")
    return {"status": "ok"}

@app.get("/api/v1/subscriptions/tiers/public")
async def get_public_tiers():
    logger.info("Public tiers request received")
    return [
        {
            "tier_id": "00000000-0000-0000-0000-000000000001",
            "name": "free",
            "display_name": "Free",
            "description": "Limited resources for evaluation purposes",
            "price_monthly": 0.0,
            "price_yearly": 0.0,
            "is_public": True,
            "max_agents": 2,
            "max_concurrent_jobs": 5,
            "max_schedules": 2,
            "max_queues": 2,
            "storage_gb": 1,
            "max_api_calls_daily": 1000,
            "enable_api_access": True,
            "enable_schedules": True,
            "enable_queues": True,
            "enable_analytics": False,
            "enable_custom_branding": False,
            "enable_sla_support": False,
            "enable_audit_logs": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        },
        {
            "tier_id": "00000000-0000-0000-0000-000000000002",
            "name": "standard",
            "display_name": "Standard",
            "description": "For small businesses with moderate resource needs",
            "price_monthly": 49.99,
            "price_yearly": 499.99,
            "is_public": True,
            "max_agents": 10,
            "max_concurrent_jobs": 25,
            "max_schedules": 10,
            "max_queues": 10,
            "storage_gb": 10,
            "max_api_calls_daily": 10000,
            "enable_api_access": True,
            "enable_schedules": True,
            "enable_queues": True,
            "enable_analytics": True,
            "enable_custom_branding": False,
            "enable_sla_support": False,
            "enable_audit_logs": False,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        }
    ]

@app.post("/api/v1/subscriptions/register", status_code=201)
async def register_organization(registration: OrganizationRegistration):
    # Log the registration request
    logger.info(f"Registration request: {registration.dict()}")
    
    # Simulate successful registration
    return {
        "message": "Organization registered successfully",
        "tenant_id": "00000000-0000-0000-0000-000000000010",
        "user_id": "00000000-0000-0000-0000-000000000011"
    }

if __name__ == "__main__":
    # Run server
    logger.info("Starting debug API server")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")