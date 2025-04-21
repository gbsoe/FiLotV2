"""
Test script to verify the API integration and pool data fetching logic.
This script helps diagnose issues with the Raydium API connection
and the pool data retrieval after the URL fixes.
"""

import logging
import json
import os
from dotenv import load_dotenv
from raydium_client import get_client
import response_data

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("test_api_integration")

# Load environment variables
load_dotenv()

def test_api_connection():
    """Test basic API connectivity."""
    logger.info("Testing API connection...")
    client = get_client()
    
    # Log the API URL being used
    logger.info(f"Using API URL: {client.base_url}")
    
    try:
        # Test health endpoint
        health = client.check_health()
        logger.info(f"API health check result: {health}")
        return True
    except Exception as e:
        logger.error(f"API connection test failed: {e}")
        return False

def test_pool_retrieval():
    """Test retrieving specific pools by ID."""
    logger.info("Testing pool retrieval by ID...")
    client = get_client()
    
    # Known pool IDs to test
    known_pool_ids = [
        "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv",  # SOL/USDC
        "CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq",  # SOL/USDC (another pool)
        "2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2",  # SOL/RAY
    ]
    
    success_count = 0
    for pool_id in known_pool_ids:
        try:
            logger.info(f"Attempting to fetch pool {pool_id}...")
            pool_data = client.get_pool_by_id(pool_id)
            if pool_data and 'pool' in pool_data:
                logger.info(f"Successfully retrieved pool {pool_id}")
                success_count += 1
                
                # Show limited pool data for verification
                pool = pool_data['pool']
                logger.info(f"Pool info: ID={pool.get('id', 'N/A')}, "
                           f"Token Pair={pool.get('tokenPair', 'N/A')}, "
                           f"APR={pool.get('apr', 'N/A')}, "
                           f"TVL=${pool.get('liquidity', 'N/A')}")
            else:
                logger.warning(f"Pool {pool_id} request succeeded but returned no valid pool data")
        except Exception as e:
            logger.error(f"Error fetching pool {pool_id}: {e}")
    
    logger.info(f"Successfully retrieved {success_count} out of {len(known_pool_ids)} pools")
    return success_count > 0

def test_get_pools_endpoint():
    """Test the /api/pools endpoint."""
    logger.info("Testing /api/pools endpoint...")
    client = get_client()
    
    try:
        # Get all pools
        pools_data = client.get_pools()
        
        # Count the pools in each category
        best_performance_count = len(pools_data.get('bestPerformance', []))
        top_stable_count = len(pools_data.get('topStable', []))
        
        logger.info(f"API returned {best_performance_count} best performance pools and {top_stable_count} stable pools")
        
        # If we got any pools, show the first one as an example
        if best_performance_count > 0:
            example_pool = pools_data['bestPerformance'][0]
            logger.info(f"Example best performance pool: ID={example_pool.get('id', 'N/A')}, "
                       f"Token Pair={example_pool.get('tokenPair', 'N/A')}")
            
        if top_stable_count > 0:
            example_pool = pools_data['topStable'][0]
            logger.info(f"Example stable pool: ID={example_pool.get('id', 'N/A')}, "
                       f"Token Pair={example_pool.get('tokenPair', 'N/A')}")
            
        return True
    except Exception as e:
        logger.error(f"Error testing /api/pools endpoint: {e}")
        return False

def test_response_data_integration():
    """Test the integration with response_data.py."""
    logger.info("Testing response_data.py integration...")
    try:
        # Get pool data using the function
        pools_data = response_data.get_pool_data()
        
        # Count the pools in each category
        best_performance_count = len(pools_data.get('bestPerformance', []))
        top_stable_count = len(pools_data.get('topStable', []))
        top_apr_count = len(pools_data.get('topAPR', []))
        
        logger.info(f"response_data.py returned {best_performance_count} best performance pools, "
                  f"{top_stable_count} stable pools, and {top_apr_count} top APR pools")
        
        # Print best performance pools
        if best_performance_count > 0:
            logger.info("Best performance pools:")
            for i, pool in enumerate(pools_data['bestPerformance']):
                logger.info(f"  {i+1}. ID={pool.get('id', 'N/A')}, "
                           f"Pair={pool.get('pairName', pool.get('tokenPair', 'N/A'))}, "
                           f"APR={pool.get('apr', 'N/A')}%, "
                           f"TVL=${pool.get('liquidity', 'N/A')}")
        
        # Print stable pools
        if top_stable_count > 0:
            logger.info("Top stable pools:")
            for i, pool in enumerate(pools_data['topStable']):
                logger.info(f"  {i+1}. ID={pool.get('id', 'N/A')}, "
                           f"Pair={pool.get('pairName', pool.get('tokenPair', 'N/A'))}, "
                           f"APR={pool.get('apr', 'N/A')}%, "
                           f"TVL=${pool.get('liquidity', 'N/A')}")
        
        # Save the full pool data to a file for inspection
        with open('pool_data_test_results.json', 'w') as f:
            # Convert to a serializable format (handling sets, etc.)
            serializable_data = json.dumps(pools_data, default=lambda o: str(o) if isinstance(o, (set, complex)) else o.__dict__ if hasattr(o, '__dict__') else None, indent=2)
            f.write(serializable_data)
            
        logger.info("Full pool data saved to pool_data_test_results.json")
        
        return best_performance_count > 0 and top_stable_count > 0
    except Exception as e:
        logger.error(f"Error testing response_data.py integration: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting API integration tests...")
    
    # Run all tests
    api_connection = test_api_connection()
    pool_retrieval = test_pool_retrieval()
    pools_endpoint = test_get_pools_endpoint()
    response_data_integration = test_response_data_integration()
    
    # Summary
    logger.info("=== Test Summary ===")
    logger.info(f"API connection: {'SUCCESS' if api_connection else 'FAILED'}")
    logger.info(f"Pool retrieval by ID: {'SUCCESS' if pool_retrieval else 'FAILED'}")
    logger.info(f"Get pools endpoint: {'SUCCESS' if pools_endpoint else 'FAILED'}")
    logger.info(f"response_data.py integration: {'SUCCESS' if response_data_integration else 'FAILED'}")
    
    if api_connection and pool_retrieval and pools_endpoint and response_data_integration:
        logger.info("All tests PASSED!")
    else:
        logger.warning("Some tests FAILED. Check the logs for details.")