#!/usr/bin/env python3
import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registration data
registration_data = {
    "organization_name": "Test Organization",
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "password123",
    "subscription_tier": "free"
}

# First, check if server is reachable
try:
    logger.info("Checking if server is running...")
    ping_response = requests.get("http://localhost:8000/api/v1/healthcheck")
    logger.info(f"Server ping status: {ping_response.status_code}")
except Exception as e:
    logger.error(f"Server ping failed: {str(e)}")

# Try all common API paths to see what's available
api_paths = [
    "/api/v1/healthcheck",
    "/api/v1/subscriptions/register",
    "/api/v1/subscriptions/tiers/public", 
    "/api"
]
    
for path in api_paths:
    try:
        logger.info(f"Checking API path: {path}")
        response = requests.get(f"http://localhost:8000{path}")
        logger.info(f"  Status: {response.status_code}")
    except Exception as e:
        logger.error(f"  Error: {str(e)}")

# Make request to registration endpoint
try:
    logger.info("Sending registration request...")
    response = requests.post(
        "http://localhost:8000/api/v1/subscriptions/register",
        json=registration_data
    )

    # Print response
    logger.info(f"Status code: {response.status_code}")
    logger.info(f"Response headers: {response.headers}")
    try:
        logger.info(f"Response body: {json.dumps(response.json(), indent=2)}")
    except:
        logger.info(f"Response body: {response.text}")
except Exception as e:
    logger.error(f"Registration request failed: {str(e)}")