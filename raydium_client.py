#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client for interacting with the Raydium API
"""

import aiohttp
import logging
import json
import random
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# API endpoints
API_BASE_URL = "https://api.raydium.io/v2"
POOLS_ENDPOINT = f"{API_BASE_URL}/pools"

async def get_pools(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get pool data from the Raydium API.
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of pool data dictionaries
    """
    try:
        # For demonstration purposes, we'll generate mock data
        # In a real implementation, we would call the Raydium API
        pool_data = generate_sample_pool_data(limit)
        return pool_data
    except Exception as e:
        logger.error(f"Error fetching pool data: {e}")
        raise

async def get_pool_by_id(pool_id: str) -> Optional[Dict[str, Any]]:
    """
    Get data for a specific pool by ID.
    
    Args:
        pool_id: Raydium pool ID
        
    Returns:
        Pool data dictionary or None if not found
    """
    try:
        # For demonstration purposes, we'll generate mock data
        # In a real implementation, we would call the Raydium API
        pools = generate_sample_pool_data(20)
        for pool in pools:
            if pool["id"] == pool_id:
                return pool
        return None
    except Exception as e:
        logger.error(f"Error fetching pool data: {e}")
        return None

def generate_sample_pool_data(count: int) -> List[Dict[str, Any]]:
    """
    Generate sample pool data for demonstration purposes.
    
    Args:
        count: Number of pools to generate
        
    Returns:
        List of pool data dictionaries
    """
    # Token symbols for sample data
    token_symbols = [
        "SOL", "USDC", "USDT", "ETH", "BTC", "RAY", "ORCA", "MNGO", "SRM",
        "FTT", "FIDA", "STEP", "ATLAS", "POLIS", "SAMO", "BONK", "GENE"
    ]
    
    pools = []
    
    for i in range(count):
        # Pick two different tokens for the pair
        token_a, token_b = random.sample(token_symbols, 2)
        
        # Generate random pool ID
        pool_id = f"pool_{i}_{token_a}_{token_b}"
        
        # Generate random APR values
        apr_24h = random.uniform(5.0, 150.0)
        apr_7d = apr_24h * random.uniform(0.8, 1.2)
        apr_30d = apr_7d * random.uniform(0.8, 1.2)
        
        # Generate random TVL
        tvl = random.uniform(10000.0, 10000000.0)
        
        # Generate random token prices
        token_a_price = random.uniform(0.1, 1000.0)
        token_b_price = random.uniform(0.1, 1000.0)
        
        # Generate random fee
        fee = random.choice([0.0025, 0.003, 0.005])
        
        # Generate random 24h volume
        volume_24h = tvl * random.uniform(0.05, 0.5)
        
        # Generate random 24h transaction count
        tx_count_24h = int(volume_24h / random.uniform(100.0, 1000.0))
        
        # Create pool data dictionary
        pool = {
            "id": pool_id,
            "token_a": {
                "symbol": token_a,
                "price": token_a_price
            },
            "token_b": {
                "symbol": token_b,
                "price": token_b_price
            },
            "apr_24h": apr_24h,
            "apr_7d": apr_7d,
            "apr_30d": apr_30d,
            "tvl": tvl,
            "fee": fee,
            "volume_24h": volume_24h,
            "tx_count_24h": tx_count_24h
        }
        
        pools.append(pool)
    
    # Sort pools by APR (descending)
    pools.sort(key=lambda p: p["apr_24h"], reverse=True)
    
    return pools