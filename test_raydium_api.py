#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the Raydium API integration
"""

import os
import json
import logging
from raydium_client import RaydiumClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Pretty print helper
def print_json(data):
    print(json.dumps(data, indent=2))

# Testing the Raydium API
def main():
    try:
        # Initialize client
        logger.info("Initializing Raydium client")
        client = RaydiumClient()
        
        # Test health check
        print("\n" + "=" * 40)
        print("API HEALTH CHECK")
        print("=" * 40)
        health = client.check_health()
        print(f"API Status: {health.get('status', 'Unknown')}")
        print(f"API Message: {health.get('message', 'Unknown')}")
        print(f"API Service: {health.get('service', 'Unknown')}")
        
        # Get top APR pools
        print("\n" + "=" * 40)
        print("TOP APR POOLS")
        print("=" * 40)
        pools = client.get_pools()
        print(f"Top APR Pools: {len(pools.get('topAPR', []))}")
        print(f"Mandatory Pools: {len(pools.get('mandatory', []))}")
        
        # Print first pool details
        if pools.get('topAPR', []):
            first_pool = pools['topAPR'][0]
            print("\nHighest APR Pool:")
            print(f"  Pair: {first_pool.get('pairName', 'Unknown')}")
            print(f"  APR: {first_pool.get('apr', 'Unknown')}%")
            print(f"  Liquidity: {first_pool.get('liquidity', 'Unknown')}")
        
        # Filter pools for SOL
        print("\n" + "=" * 40)
        print("SOL POOLS (FILTERED)")
        print("=" * 40)
        sol_pools = client.filter_pools(token_symbol="SOL", limit=3)
        print(f"Found {sol_pools.get('count', 0)} SOL pools")
        for pool in sol_pools.get('pools', []):
            print(f"  {pool.get('pairName', 'Unknown')} - APR: {pool.get('apr', 'Unknown')}%")
        
        # Get token prices
        print("\n" + "=" * 40)
        print("TOKEN PRICES")
        print("=" * 40)
        tokens = ["SOL", "BTC", "ETH", "USDC"]
        prices = client.get_token_prices(symbols=tokens)
        for token, price in prices.items():
            print(f"  {token}: ${price:.4f}")
        
        print("\n" + "=" * 40)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 40)
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()