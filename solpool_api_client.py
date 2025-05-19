#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SolPool Insight API Client for FiLot Telegram bot
Integrates with the SolPool Insight RESTful API to fetch real-time liquidity pool data
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "https://filotanalytics.replit.app/API"
API_KEY = os.getenv("SOLPOOL_API_KEY")
API_TIMEOUT = 10  # seconds

# Cache configuration
CACHE_DURATION = 300  # 5 minutes cache
_cache = {}
_last_api_call = 0
API_RATE_LIMIT = 0.5  # seconds between API calls to avoid rate limiting

def _rate_limit():
    """Apply rate limiting to API calls"""
    global _last_api_call
    current_time = time.time()
    time_since_last_call = current_time - _last_api_call
    
    if time_since_last_call < API_RATE_LIMIT:
        time.sleep(API_RATE_LIMIT - time_since_last_call)
    
    _last_api_call = time.time()

def _get_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get data from cache if it exists and is not expired"""
    if cache_key in _cache:
        cache_time, cache_data = _cache[cache_key]
        if time.time() - cache_time < CACHE_DURATION:
            logger.debug(f"Cache hit for {cache_key}")
            return cache_data
    return None

def _save_to_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """Save data to cache with current timestamp"""
    _cache[cache_key] = (time.time(), data)
    logger.debug(f"Saved to cache: {cache_key}")

def _build_headers() -> Dict[str, str]:
    """Build request headers including API key if available"""
    headers = {
        "Accept": "application/json",
        "User-Agent": "FiLotTelegramBot/1.0"
    }
    
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    return headers

def get_pools(
    limit: int = 5,
    min_tvl: float = 1000000,
    min_apr: float = 5,
    dex: Optional[str] = "Raydium",
    token: Optional[str] = None,
    sort_by: str = "apr",
    sort_dir: str = "desc"
) -> List[Dict[str, Any]]:
    """
    Get liquidity pools from SolPool Insight API
    
    Args:
        limit: Maximum number of pools to return
        min_tvl: Minimum TVL value in USD
        min_apr: Minimum APR percentage
        dex: Optional DEX name filter (e.g., "Raydium", "Orca")
        token: Optional token symbol filter
        sort_by: Field to sort by ("apr", "tvl", "volume")
        sort_dir: Sort direction ("asc" or "desc")
        
    Returns:
        List of pool data dictionaries or empty list on error
    """
    cache_key = f"pools_{limit}_{min_tvl}_{min_apr}_{dex}_{token}_{sort_by}_{sort_dir}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        params = {
            "limit": limit,
            "min_tvl": min_tvl,
            "min_apr": min_apr,
            "sort_by": sort_by,
            "sort_dir": sort_dir
        }
        
        if dex:
            params["dex"] = dex
        
        if token:
            params["token"] = token
        
        url = f"{API_BASE_URL}/pools"
        logger.info(f"Fetching pools from SolPool API: {url} with params {params}")
        
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "data" in data:
                # Transform data to match our internal format
                pools = []
                for pool in data["data"]:
                    pool_data = {
                        "id": pool.get("id", ""),
                        "token_a_symbol": pool.get("token1_symbol", ""),
                        "token_b_symbol": pool.get("token2_symbol", ""),
                        "token_a_price": pool.get("token1_price_usd", 0),
                        "token_b_price": pool.get("token2_price_usd", 0),
                        "apr_24h": pool.get("apr", 0),
                        "apr_7d": 0,  # Not directly provided by API
                        "apr_30d": 0,  # Not directly provided by API
                        "tvl": pool.get("liquidity", 0),
                        "volume_24h": pool.get("volume_24h", 0),
                        "fee": pool.get("fee", 0),
                        "dex": pool.get("dex", ""),
                        "prediction_score": pool.get("prediction_score", 0)
                    }
                    pools.append(pool_data)
                
                _save_to_cache(cache_key, pools)
                return pools
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching pools from SolPool API: {e}")
    
    # Return empty list on error
    return []

def get_high_apr_pools(limit: int = 3) -> List[Dict[str, Any]]:
    """
    Get highest APR pools from SolPool Insight API
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of high APR pool data dictionaries or empty list on error
    """
    return get_pools(
        limit=limit,
        min_tvl=500000,  # Lower TVL threshold to find higher APR pools
        min_apr=10,
        sort_by="apr",
        sort_dir="desc"
    )

def get_pool_detail(pool_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information for a specific pool
    
    Args:
        pool_id: Unique identifier of the pool
        
    Returns:
        Pool detail dictionary or None on error
    """
    cache_key = f"pool_detail_{pool_id}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        url = f"{API_BASE_URL}/pools/{pool_id}"
        logger.info(f"Fetching pool detail from SolPool API: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "data" in data:
                pool = data["data"]
                # Transform to our internal format
                pool_data = {
                    "id": pool.get("id", ""),
                    "name": pool.get("name", ""),
                    "token_a_symbol": pool.get("token1_symbol", ""),
                    "token_b_symbol": pool.get("token2_symbol", ""),
                    "token_a_price": pool.get("token1_price_usd", 0),
                    "token_b_price": pool.get("token2_price_usd", 0),
                    "apr_24h": pool.get("apr", 0),
                    "apr_change_24h": pool.get("apr_change_24h", 0),
                    "apr_change_7d": pool.get("apr_change_7d", 0),
                    "apr_change_30d": pool.get("apr_change_30d", 0),
                    "tvl": pool.get("liquidity", 0),
                    "tvl_change_24h": pool.get("tvl_change_24h", 0),
                    "tvl_change_7d": pool.get("tvl_change_7d", 0),
                    "volume_24h": pool.get("volume_24h", 0),
                    "fee": pool.get("fee", 0),
                    "dex": pool.get("dex", ""),
                    "volatility": pool.get("volatility", 0),
                    "prediction_score": pool.get("prediction_score", 0),
                    "created_at": pool.get("created_at", ""),
                    "last_updated": pool.get("last_updated", "")
                }
                
                _save_to_cache(cache_key, pool_data)
                return pool_data
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching pool detail from SolPool API: {e}")
    
    # Return None on error
    return None

def get_pool_history(
    pool_id: str,
    days: int = 7,
    interval: str = "day"
) -> List[Dict[str, Any]]:
    """
    Get historical data for a specific pool
    
    Args:
        pool_id: Unique identifier of the pool
        days: Number of days of history to retrieve
        interval: Time interval ('hour', 'day', 'week')
        
    Returns:
        List of historical data points or empty list on error
    """
    cache_key = f"pool_history_{pool_id}_{days}_{interval}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        params = {
            "days": days,
            "interval": interval
        }
        
        url = f"{API_BASE_URL}/pools/{pool_id}/history"
        logger.info(f"Fetching pool history from SolPool API: {url} with params {params}")
        
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "data" in data:
                _save_to_cache(cache_key, data["data"])
                return data["data"]
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching pool history from SolPool API: {e}")
    
    # Return empty list on error
    return []

def get_token_pools(
    token_symbol: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get all pools containing a specific token
    
    Args:
        token_symbol: The token symbol (e.g., "SOL", "BONK")
        limit: Maximum number of pools to return
        
    Returns:
        List of pools containing the token or empty list on error
    """
    return get_pools(
        limit=limit,
        token=token_symbol,
        sort_by="liquidity",
        sort_dir="desc"
    )

def get_predictions(
    min_score: int = 80,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Get ML-based predictions for pools
    
    Args:
        min_score: Minimum prediction score (0-100)
        limit: Maximum number of results
        
    Returns:
        List of pool predictions or empty list on error
    """
    cache_key = f"predictions_{min_score}_{limit}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        params = {
            "min_score": min_score,
            "limit": limit
        }
        
        url = f"{API_BASE_URL}/predictions"
        logger.info(f"Fetching predictions from SolPool API: {url} with params {params}")
        
        response = requests.get(
            url,
            params=params,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "data" in data:
                predictions = []
                for pred in data["data"]:
                    prediction = {
                        "pool_id": pred.get("pool_id", ""),
                        "name": pred.get("name", ""),
                        "dex": pred.get("dex", ""),
                        "current_tvl": pred.get("current_tvl", 0),
                        "current_apr": pred.get("current_apr", 0),
                        "prediction_score": pred.get("prediction_score", 0),
                        "predicted_apr_low": pred.get("predicted_apr_range", {}).get("low", 0),
                        "predicted_apr_mid": pred.get("predicted_apr_range", {}).get("mid", 0),
                        "predicted_apr_high": pred.get("predicted_apr_range", {}).get("high", 0),
                        "predicted_tvl_change": pred.get("predicted_tvl_change", 0),
                        "key_factors": pred.get("key_factors", [])
                    }
                    predictions.append(prediction)
                
                _save_to_cache(cache_key, predictions)
                return predictions
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching predictions from SolPool API: {e}")
    
    # Return empty list on error
    return []

def api_health_check() -> bool:
    """
    Check if the SolPool API is available
    
    Returns:
        True if API is available, False otherwise
    """
    try:
        _rate_limit()
        
        url = f"{API_BASE_URL}/pools?limit=1"
        logger.info(f"Checking SolPool API health: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=5  # Shorter timeout for health check
        )
        
        return response.status_code == 200
    
    except Exception as e:
        logger.error(f"SolPool API health check failed: {e}")
        return False

# Initialize with a health check
if __name__ == "__main__":
    is_healthy = api_health_check()
    logger.info(f"SolPool API is {'available' if is_healthy else 'unavailable'}")
    
    if is_healthy:
        # Test retrieving pools
        pools = get_pools(limit=3)
        logger.info(f"Retrieved {len(pools)} pools")
        for pool in pools:
            logger.info(f"Pool: {pool['token_a_symbol']}-{pool['token_b_symbol']}, APR: {pool['apr_24h']}%, TVL: ${pool['tvl']:,.2f}")