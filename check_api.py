#!/usr/bin/env python
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def check_raydium_api():
    """Check if the Raydium API is accessible"""
    api_url = "https://raydium-trader-filot.replit.app/api/pools"
    
    try:
        logger.info(f"Attempting to connect to {api_url}")
        response = requests.get(api_url, timeout=10)
        
        logger.info(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully retrieved data: {len(data.get('topAPR', []))} top APR pools")
            return True
        else:
            logger.error(f"API returned error status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error connecting to API: {e}")
        return False

if __name__ == "__main__":
    check_raydium_api()