#!/usr/bin/env python3
"""
Test script to verify the pool data handling with a specific pool ID
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add current directory to sys.path to allow imports
sys.path.append(os.getcwd())

# Import the necessary modules
from response_data import get_pool_data
from utils import format_pool_info

def test_specific_pool_id(pool_id="3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv"):
    """Test fetching and formatting data for a specific pool ID."""
    logger.info(f"Testing pool ID: {pool_id}")
    
    # Get pool data
    pool_data = get_pool_data()
    logger.info(f"Got {len(pool_data.get('topAPR', []))} pools in topAPR category")
    
    # Find the specific pool
    found_pool = None
    for pool in pool_data.get('topAPR', []):
        if pool.get('id') == pool_id:
            found_pool = pool
            break
            
    if found_pool:
        logger.info(f"Found pool with ID: {pool_id}")
        logger.info(f"Pool pair: {found_pool.get('pairName')}")
        logger.info(f"Pool APR: {found_pool.get('apr')}%")
        logger.info(f"Pool liquidity: ${found_pool.get('liquidity'):,.2f}")
        
        # Check token prices from CoinGecko
        token_prices = found_pool.get('tokenPrices', {})
        for token, price in token_prices.items():
            logger.info(f"Token {token} price: ${price}")
            
        # Test formatting the pool data for display
        logger.info("Testing pool data formatting:")
        formatted_info = format_pool_info([found_pool])
        print("\n" + "="*50)
        print("FORMATTED POOL INFO:")
        print(formatted_info)
        print("="*50)
        
        return found_pool
    else:
        logger.warning(f"Pool with ID {pool_id} not found!")
        return None

if __name__ == "__main__":
    # Test with the specific pool ID
    target_pool_id = "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv"
    result = test_specific_pool_id(target_pool_id)
    
    if not result:
        # If not found, print all available pool IDs
        logger.info("Listing all available pool IDs:")
        pool_data = get_pool_data()
        for pool in pool_data.get('topAPR', []):
            logger.info(f"Available pool: {pool.get('id')} - {pool.get('pairName')}")