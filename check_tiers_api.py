#!/usr/bin/env python3
import sys
import requests
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Backend URL 
    backend_url = "http://localhost:8000/api/v1/subscriptions/tiers/public"
    
    logger.info(f"Fetching subscription tiers from: {backend_url}")
    
    # Send GET request to the API
    try:
        response = requests.get(
            backend_url, 
            headers={
                "Accept": "application/json"
            }
        )
        
        # Log response details
        logger.info(f"Status code: {response.status_code}")
        
        try:
            if response.status_code == 200:
                tiers = response.json()
                logger.info(f"Found {len(tiers)} subscription tiers:")
                for tier in tiers:
                    logger.info(f"  - {tier['name']} ({tier['display_name']}): ${tier['price_monthly']}/month")
                
                # Also print the full JSON for inspection
                logger.info(f"Full response: {json.dumps(response.json(), indent=2)}")
            else:
                logger.error(f"Failed to fetch tiers: {response.text}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
    
    except Exception as e:
        logger.error(f"Error sending request: {str(e)}")
        
if __name__ == "__main__":
    main()