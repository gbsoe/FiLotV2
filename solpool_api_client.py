#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SolPool Insight API Client
Connects to SolPool Insight API for real-time liquidity pool data
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# SolPool API configuration
SOLPOOL_API_URL = os.getenv("SOLPOOL_API_URL", "https://api.solpool.io/v1")
SOLPOOL_API_KEY = os.getenv("SOLPOOL_API_KEY")

# Cache configuration
CACHE_EXPIRY = 60  # 1 minute cache for pool data
RATE_LIMIT_PERIOD = 10  # 10 seconds between API calls

# Cache storage
_cache = {}
_last_call_timestamp = {}

def _is_cache_valid(cache_key: str) -> bool:
    """
    Check if cached data is still valid
    
    Args:
        cache_key: Cache key to check
        
    Returns:
        True if cache is valid, False otherwise
    """
    if cache_key not in _cache:
        return False
        
    cache_entry = _cache[cache_key]
    
    # Check if cache has expired
    if "timestamp" not in cache_entry:
        return False
        
    current_time = time.time()
    return current_time - cache_entry["timestamp"] < CACHE_EXPIRY

def _can_make_api_call(endpoint: str) -> bool:
    """
    Check if we can make an API call based on rate limiting
    
    Args:
        endpoint: API endpoint to check
        
    Returns:
        True if API call allowed, False otherwise
    """
    if endpoint not in _last_call_timestamp:
        return True
        
    current_time = time.time()
    return current_time - _last_call_timestamp[endpoint] >= RATE_LIMIT_PERIOD

def _save_to_cache(cache_key: str, data: Dict[str, Any]) -> None:
    """
    Save data to cache
    
    Args:
        cache_key: Cache key to use
        data: Data to cache
    """
    _cache[cache_key] = {
        "data": data,
        "timestamp": time.time()
    }

def _update_api_call_timestamp(endpoint: str) -> None:
    """
    Update timestamp of last API call
    
    Args:
        endpoint: API endpoint that was called
    """
    _last_call_timestamp[endpoint] = time.time()

def api_health_check() -> bool:
    """
    Check if the SolPool API is accessible
    
    Returns:
        True if API is accessible, False otherwise
    """
    try:
        # Try to get the API health endpoint
        cache_key = "health_check"
        
        if _is_cache_valid(cache_key):
            # Return cached health status
            return _cache[cache_key]["data"].get("status") == "success"
        
        if not _can_make_api_call("health"):
            # Rate limited, assume API is healthy if we've successfully connected before
            return cache_key in _cache and _cache[cache_key]["data"].get("status") == "success"
            
        # Make API call
        url = f"{SOLPOOL_API_URL}/health"
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, headers=headers, timeout=5)
        
        # Update call timestamp
        _update_api_call_timestamp("health")
        
        if response.status_code == 200:
            result = response.json()
            _save_to_cache(cache_key, result)
            return result.get("status") == "success"
            
        return False
    except Exception as e:
        logger.error(f"Error checking API health: {e}")
        return False

def get_pool_list(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get list of all pools
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of pool data dictionaries
    """
    try:
        # Generate cache key
        cache_key = f"pool_list_{limit}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("pools"):
            # Rate limited, return cached data if available or empty list
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return []
        
        # Make API call
        url = f"{SOLPOOL_API_URL}/pools"
        params = {"limit": limit}
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("pools")
        
        if response.status_code == 200:
            result = response.json()
            if "pools" in result and isinstance(result["pools"], list):
                _save_to_cache(cache_key, result["pools"])
                return result["pools"]
        
        # Return empty list on error
        return []
    except Exception as e:
        logger.error(f"Error getting pool list: {e}")
        # Always return a list, even on error
        return []

def get_pool_detail(pool_id: str) -> Dict[str, Any]:
    """
    Get detailed data for a specific pool
    
    Args:
        pool_id: Pool ID to get details for
        
    Returns:
        Dictionary with pool details
    """
    try:
        # Generate cache key
        cache_key = f"pool_detail_{pool_id}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("pool_detail"):
            # Rate limited, return cached data if available or empty dict
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return {}
        
        # Make API call
        url = f"{SOLPOOL_API_URL}/pools/{pool_id}"
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("pool_detail")
        
        if response.status_code == 200:
            result = response.json()
            if "pool" in result and isinstance(result["pool"], dict):
                _save_to_cache(cache_key, result["pool"])
                return result["pool"]
        
        # Return empty dict on error
        return {}
    except Exception as e:
        logger.error(f"Error getting pool detail: {e}")
        # Always return a dict, even on error
        return {}

def get_high_apr_pools(min_apr: float = 10.0, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get pools with high APR
    
    Args:
        min_apr: Minimum APR threshold
        limit: Maximum number of pools to return
        
    Returns:
        List of high APR pool data dictionaries
    """
    try:
        # Generate cache key
        cache_key = f"high_apr_pools_{min_apr}_{limit}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("high_apr"):
            # Rate limited, return cached data if available or empty list
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return []
        
        # Make API call
        url = f"{SOLPOOL_API_URL}/pools/high-apr"
        params = {"min_apr": min_apr, "limit": limit}
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("high_apr")
        
        if response.status_code == 200:
            result = response.json()
            if "pools" in result and isinstance(result["pools"], list):
                _save_to_cache(cache_key, result["pools"])
                return result["pools"]
        
        # Return empty list on error
        return []
    except Exception as e:
        logger.error(f"Error getting high APR pools: {e}")
        # Always return a list, even on error
        return []

def get_token_pools(token: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get pools containing a specific token
    
    Args:
        token: Token symbol to search for
        limit: Maximum number of pools to return
        
    Returns:
        List of pool data dictionaries containing the token
    """
    try:
        # Generate cache key
        cache_key = f"token_pools_{token}_{limit}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("token_pools"):
            # Rate limited, return cached data if available or empty list
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return []
        
        # Make API call
        url = f"{SOLPOOL_API_URL}/pools/by-token"
        params = {"token": token, "limit": limit}
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("token_pools")
        
        if response.status_code == 200:
            result = response.json()
            if "pools" in result and isinstance(result["pools"], list):
                _save_to_cache(cache_key, result["pools"])
                return result["pools"]
        
        # Return empty list on error
        return []
    except Exception as e:
        logger.error(f"Error getting token pools: {e}")
        # Always return a list, even on error
        return []

def get_predictions(min_score: float = 50.0, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get pools with AI predictions
    
    Args:
        min_score: Minimum prediction score threshold
        limit: Maximum number of predictions to return
        
    Returns:
        List of predicted pool data dictionaries
    """
    try:
        # Generate cache key
        cache_key = f"predictions_{min_score}_{limit}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("predictions"):
            # Rate limited, return cached data if available or empty list
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return []
        
        # Make API call
        url = f"{SOLPOOL_API_URL}/predictions"
        params = {"min_score": min_score, "limit": limit}
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("predictions")
        
        if response.status_code == 200:
            result = response.json()
            if "predictions" in result and isinstance(result["predictions"], list):
                _save_to_cache(cache_key, result["predictions"])
                return result["predictions"]
        
        # Return empty list on error
        return []
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        # Always return a list, even on error
        return []

def simulate_investment(
    pool_id: str,
    amount: float,
    days: int = 30
) -> Dict[str, Any]:
    """
    Simulate investment in a specific pool
    
    Args:
        pool_id: Pool ID to simulate investment in
        amount: Amount to invest (in USD)
        days: Number of days to simulate
        
    Returns:
        Dictionary with simulation results
    """
    try:
        # Generate cache key
        cache_key = f"simulation_{pool_id}_{amount}_{days}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("simulate"):
            # Rate limited, return cached data if available or fallback
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                # Generate fallback simulation data
                return _generate_fallback_simulation(pool_id, amount, days)
        
        # Make API call
        url = f"{SOLPOOL_API_URL}/simulate"
        params = {
            "pool_id": pool_id,
            "amount": amount,
            "days": days
        }
        
        # Use API key if available
        headers = {}
        if SOLPOOL_API_KEY:
            headers["X-API-Key"] = SOLPOOL_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("simulate")
        
        if response.status_code == 200:
            result = response.json()
            if "simulation" in result and isinstance(result["simulation"], dict):
                _save_to_cache(cache_key, result["simulation"])
                return result["simulation"]
        
        # Return fallback simulation data on error
        fallback_simulation = _generate_fallback_simulation(pool_id, amount, days)
        _save_to_cache(cache_key, fallback_simulation)
        return fallback_simulation
    except Exception as e:
        logger.error(f"Error simulating investment: {e}")
        # Return fallback simulation data on error
        fallback_simulation = _generate_fallback_simulation(pool_id, amount, days)
        _save_to_cache(cache_key, fallback_simulation)
        return fallback_simulation

def _generate_fallback_simulation(pool_id: str, amount: float, days: int) -> Dict[str, Any]:
    """
    Generate fallback simulation data
    
    Args:
        pool_id: Pool ID to simulate
        amount: Amount to invest
        days: Number of days to simulate
        
    Returns:
        Dictionary with fallback simulation data
    """
    # Try to get pool details
    pool_detail = None
    
    try:
        # Cache key for pool detail
        cache_key = f"pool_detail_{pool_id}"
        
        if cache_key in _cache:
            pool_detail = _cache[cache_key]["data"]
    except:
        pass
    
    # If pool detail available, use its APR
    apr = 12.5  # Default APR if pool details not available
    
    if pool_detail and "apr_24h" in pool_detail:
        apr = pool_detail["apr_24h"]
    
    # Calculate daily rate
    daily_rate = apr / 365 / 100
    
    # Calculate final amount after specified days
    final_amount = amount * (1 + daily_rate) ** days
    profit = final_amount - amount
    
    # Generate fallback simulation
    return {
        "status": "fallback",
        "pool_id": pool_id,
        "initial_amount": amount,
        "days": days,
        "apr_used": apr,
        "final_amount": final_amount,
        "profit": profit,
        "roi_percent": (profit / amount) * 100,
        "note": "This is a fallback simulation based on simple calculations"
    }

# Test the module
if __name__ == "__main__":
    print("Testing SolPool API Client")
    
    # Check API health
    print(f"API Health Check: {api_health_check()}")
    
    # Get pool list
    pools = get_pool_list(limit=3)
    print(f"\nPool List (3): {pools}")
    
    # Get high APR pools
    high_apr_pools = get_high_apr_pools(min_apr=15.0, limit=3)
    print(f"\nHigh APR Pools: {high_apr_pools}")
    
    # Simulate investment in first pool
    if pools:
        pool_id = pools[0].get("id", "")
        if pool_id:
            simulation = simulate_investment(pool_id, 1000.0, 30)
            print(f"\nSimulation Results: {simulation}")
    
    # Get predictions
    predictions = get_predictions(min_score=60.0, limit=3)
    print(f"\nPredictions: {predictions}")