#!/usr/bin/env python3
import sys
import os
import requests
import json
import logging
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Backend URL 
    backend_url = "http://localhost:8000/api/v1/subscriptions/register"
    
    # Generate unique test data
    test_id = str(uuid.uuid4())[:8]
    test_org = f"Test Org {test_id}"
    test_email = f"test_{test_id}@example.com"
    
    # Registration data
    registration_data = {
        "organization_name": test_org,
        "full_name": "Test User",
        "email": test_email,
        "password": "password123",
        "subscription_tier": "free"
    }
    
    logger.info(f"Sending registration data: {json.dumps(registration_data, indent=2)}")
    
    # Send registration request to the API
    try:
        # Set up session with detailed logging
        session = requests.Session()
        
        response = session.post(
            backend_url, 
            json=registration_data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        # Log response details
        logger.info(f"Status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        try:
            logger.info(f"Response body: {json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            logger.info(f"Response body (raw): {response.text}")
        
        # Check if registration was successful
        if response.status_code == 201:
            logger.info("Registration successful!")
        else:
            logger.error(f"Registration failed with status code: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Error sending registration request: {str(e)}")
        
if __name__ == "__main__":
    main()