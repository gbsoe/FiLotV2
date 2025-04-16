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

# CoinGecko API endpoints
COINGECKO_API_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PRICE_ENDPOINT = f"{COINGECKO_API_BASE_URL}/simple/price"

# Common token IDs mapping (symbol -> CoinGecko ID)
TOKEN_ID_MAPPING = {
    "SOL": "solana",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDC": "usd-coin",
    "USDT": "tether",
    "RAY": "raydium",
    "ORCA": "orca",
    "MNGO": "mango-markets",
    "SRM": "serum",
    "FTT": "ftx-token",
    "FIDA": "bonfida",
    "STEP": "step-finance",
    "ATLAS": "star-atlas",
    "POLIS": "star-atlas-polis",
    "SAMO": "samoyedcoin",
    "BONK": "bonk",
    "GENE": "genopets"
}

async def get_token_prices(symbols: List[str]) -> Dict[str, float]:
    """
    Get token prices from CoinGecko API.
    
    Args:
        symbols: List of token symbols to get prices for
        
    Returns:
        Dictionary mapping symbols to prices in USD
    """
    try:
        # Get CoinGecko IDs for the provided symbols
        token_ids = []
        symbol_to_id = {}
        
        for symbol in symbols:
            if symbol in TOKEN_ID_MAPPING:
                token_id = TOKEN_ID_MAPPING[symbol]
                token_ids.append(token_id)
                symbol_to_id[token_id] = symbol
        
        if not token_ids:
            logger.warning(f"No mappable token IDs for symbols: {symbols}")
            return {}
        
        # Build query parameters
        params = {
            "ids": ",".join(token_ids),
            "vs_currencies": "usd"
        }
        
        # Create an async HTTP session
        async with aiohttp.ClientSession() as session:
            # Make a request to the CoinGecko price endpoint
            async with session.get(COINGECKO_PRICE_ENDPOINT, params=params) as response:
                if response.status != 200:
                    logger.error(f"Error fetching token prices: HTTP {response.status}")
                    return {}
                
                # Parse the response JSON
                data = await response.json()
                
                if not data:
                    logger.error(f"Invalid data returned from CoinGecko API")
                    return {}
                
                # Process the price data
                prices = {}
                for token_id, price_data in data.items():
                    if "usd" in price_data and token_id in symbol_to_id:
                        symbol = symbol_to_id[token_id]
                        prices[symbol] = price_data["usd"]
                
                return prices
    except Exception as e:
        logger.error(f"Error fetching token prices: {e}")
        return {}

async def get_pools(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Get pool data from the Raydium API.
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of pool data dictionaries
    """
    try:
        # Create an async HTTP session
        async with aiohttp.ClientSession() as session:
            # Make a request to the Raydium pools endpoint
            async with session.get(POOLS_ENDPOINT) as response:
                if response.status != 200:
                    logger.error(f"Error fetching pool data: HTTP {response.status}")
                    # Return generated data as backup
                    return generate_sample_pool_data(limit)
                
                # Parse the response JSON
                data = await response.json()
                
                if not data or not isinstance(data, list):
                    logger.error(f"Invalid data returned from Raydium API")
                    # Return generated data as backup
                    return generate_sample_pool_data(limit)
                
                # Process and format pool data
                processed_pools = []
                for pool in data[:limit]:
                    try:
                        pool_id = pool.get('id', f"unknown_{len(processed_pools)}")
                        token_a_symbol = pool.get('tokenA', {}).get('symbol', 'UNK')
                        token_b_symbol = pool.get('tokenB', {}).get('symbol', 'UNK')
                        
                        # Extract APR data
                        apr_24h = float(pool.get('apr24h', 0) or 0)
                        apr_7d = float(pool.get('apr7d', 0) or 0)
                        apr_30d = float(pool.get('apr30d', 0) or 0)
                        
                        # Extract TVL
                        tvl = float(pool.get('tvl', 0) or 0)
                        
                        # Extract token prices (we'll update with CoinGecko data later)
                        token_a_price = float(pool.get('tokenA', {}).get('price', 0) or 0)
                        token_b_price = float(pool.get('tokenB', {}).get('price', 0) or 0)
                        
                        # Extract fee
                        fee = float(pool.get('fee', 0.003) or 0.003)
                        
                        # Extract volume data
                        volume_24h = float(pool.get('volume24h', 0) or 0)
                        
                        # Extract transaction count 
                        tx_count_24h = int(pool.get('txCount24h', 0) or 0)
                        
                        # Create standardized pool data
                        processed_pool = {
                            "id": pool_id,
                            "token_a": {
                                "symbol": token_a_symbol,
                                "price": token_a_price
                            },
                            "token_b": {
                                "symbol": token_b_symbol,
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
                        
                        processed_pools.append(processed_pool)
                    except Exception as e:
                        logger.error(f"Error processing pool data: {str(e)}")
                        continue
                
                # Collect token symbols for price lookups
                token_symbols = set()
                for pool in processed_pools:
                    token_symbols.add(pool["token_a"]["symbol"])
                    token_symbols.add(pool["token_b"]["symbol"])
                
                # Fetch token prices from CoinGecko
                token_prices = await get_token_prices(list(token_symbols))
                
                # Update pool data with CoinGecko prices when available
                for pool in processed_pools:
                    token_a_symbol = pool["token_a"]["symbol"]
                    token_b_symbol = pool["token_b"]["symbol"]
                    
                    if token_a_symbol in token_prices:
                        pool["token_a"]["price"] = token_prices[token_a_symbol]
                    
                    if token_b_symbol in token_prices:
                        pool["token_b"]["price"] = token_prices[token_b_symbol]
                
                # Sort pools by APR (descending)
                processed_pools.sort(key=lambda p: p["apr_24h"], reverse=True)
                
                return processed_pools
                
    except Exception as e:
        logger.error(f"Error fetching pool data: {e}")
        # Return generated data as backup
        return generate_sample_pool_data(limit)

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