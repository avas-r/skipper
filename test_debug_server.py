#!/usr/bin/env python3
import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    logger.info("Testing healthcheck endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/healthcheck")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def test_public_tiers():
    logger.info("Testing public tiers endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/subscriptions/tiers/public")
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

def test_registration():
    logger.info("Testing registration endpoint...")
    try:
        registration_data = {
            "organization_name": "Test Organization",
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "password123",
            "subscription_tier": "free"
        }
        response = requests.post(
            f"{API_BASE_URL}/subscriptions/register", 
            json=registration_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response: {response.json()}")
        return response.status_code == 201
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Run tests
    health_ok = test_health_check()
    tiers_ok = test_public_tiers()
    registration_ok = test_registration()
    
    # Print summary
    logger.info("\nTest Results:")
    logger.info(f"Healthcheck:   {'✅ PASS' if health_ok else '❌ FAIL'}")
    logger.info(f"Public Tiers:  {'✅ PASS' if tiers_ok else '❌ FAIL'}")
    logger.info(f"Registration:  {'✅ PASS' if registration_ok else '❌ FAIL'}")
    
    if health_ok and tiers_ok and registration_ok:
        logger.info("\n✅ All tests passed!")
    else:
        logger.info("\n❌ Some tests failed!")