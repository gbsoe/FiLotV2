#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to fetch and display all available pool data from the Raydium API.
This helps verify what data is actually available from the API server.
"""

import os
import logging
import json
from raydium_client import get_client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('api_test')

# Load environment variables
load_dotenv()

def fetch_and_print_pools():
    """Fetch and print all available pools from the Raydium API."""
    try:
        # Get the Raydium client
        client = get_client()
        
        # Verify API connectivity
        logger.info("Testing API connectivity...")
        try:
            health = client.check_health()
            logger.info(f"API health check: {health}")
        except Exception as e:
            logger.error(f"API health check failed: {e}")
        
        # Test basic pool fetching
        logger.info("Fetching pools from main endpoint...")
        pools = client.get_pools()
        best_performance = pools.get('bestPerformance', [])
        top_stable = pools.get('topStable', [])
        
        logger.info(f"Found {len(best_performance)} best performance pools and {len(top_stable)} stable pools")
        
        # Print pool details (first up to 5 of each type)
        logger.info("\n--- BEST PERFORMANCE POOLS ---")
        for i, pool in enumerate(best_performance[:5]):
            logger.info(f"Pool {i+1}:")
            logger.info(f"  ID: {pool.get('id', 'N/A')}")
            logger.info(f"  Pair: {pool.get('tokenPair', 'N/A')}")
            logger.info(f"  APR (24h): {pool.get('apr24h', pool.get('apr', 'N/A'))}")
            logger.info(f"  APR (7d): {pool.get('apr7d', pool.get('aprWeekly', 'N/A'))}")
            logger.info(f"  APR (30d): {pool.get('apr30d', pool.get('aprMonthly', 'N/A'))}")
            logger.info(f"  Liquidity: {pool.get('liquidityUsd', pool.get('liquidity', 'N/A'))}")
        
        logger.info("\n--- TOP STABLE POOLS ---")
        for i, pool in enumerate(top_stable[:5]):
            logger.info(f"Pool {i+1}:")
            logger.info(f"  ID: {pool.get('id', 'N/A')}")
            logger.info(f"  Pair: {pool.get('tokenPair', 'N/A')}")
            logger.info(f"  APR (24h): {pool.get('apr24h', pool.get('apr', 'N/A'))}")
            logger.info(f"  APR (7d): {pool.get('apr7d', pool.get('aprWeekly', 'N/A'))}")
            logger.info(f"  APR (30d): {pool.get('apr30d', pool.get('aprMonthly', 'N/A'))}")
            logger.info(f"  Liquidity: {pool.get('liquidityUsd', pool.get('liquidity', 'N/A'))}")
        
        # Try to get specific pools to test individual pool endpoint
        logger.info("\n--- TESTING INDIVIDUAL POOL FETCHING ---")
        # Try to fetch the pool with ID 3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv
        test_pool_id = "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv"
        logger.info(f"Fetching pool with ID {test_pool_id}...")
        pool_data = client.get_pool_by_id(test_pool_id)
        if pool_data:
            logger.info(f"Successfully fetched pool: {json.dumps(pool_data, indent=2)}")
        else:
            logger.warning(f"Could not fetch pool with ID {test_pool_id}")
        
        # Try to fetch some of the problematic pool IDs we had before
        problem_pool_ids = [
            "HQ8oeaHofBJyM8DMhCD5YasRXjqT3cGjcCHcVNnYEGS1",  # Previously used but may not exist
            "Ar1owSzR5L6LXBYm7kJsEU9vHzCpexGZY6nqfuh1WjG5",  # Previously used but may not exist
            "CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq",  # Previously mislabeled
            "6fTRDD7sYxCDSWMW1zQW2HaPM3SubmER9TP5qcZ3qP9F",  # Added as a replacement
            "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"   # Added as a replacement
        ]
        
        logger.info("\n--- TESTING PROBLEMATIC POOL IDs ---")
        for pid in problem_pool_ids:
            try:
                logger.info(f"Checking if pool {pid} exists...")
                pool_data = client.get_pool_by_id(pid)
                if pool_data:
                    logger.info(f"Pool {pid} exists with data: {json.dumps(pool_data, indent=2)}")
                else:
                    logger.warning(f"Pool {pid} does not exist or returned no data")
            except Exception as e:
                logger.error(f"Error fetching pool {pid}: {e}")
        
        # Test token price fetching
        logger.info("\n--- TESTING TOKEN PRICE FETCHING ---")
        test_tokens = ["SOL", "USDC", "USDT", "RAY", "mSOL"]
        try:
            token_prices = client.get_token_prices(test_tokens)
            logger.info(f"Token prices: {json.dumps(token_prices, indent=2)}")
        except Exception as e:
            logger.error(f"Error fetching token prices: {e}")
            
        # Summarize results
        logger.info("\n--- TEST SUMMARY ---")
        logger.info(f"Total best performance pools available: {len(best_performance)}")
        logger.info(f"Total stable pools available: {len(top_stable)}")
        logger.info("End of API test")
        
    except Exception as e:
        logger.error(f"Error in API test: {e}")

if __name__ == "__main__":
    fetch_and_print_pools()