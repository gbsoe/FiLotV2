#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FilotSense API Client
Connects to FilotSense Public API for market sentiment and token analysis
"""

import os
import time
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FilotSense API configuration
FILOTSENSE_API_URL = os.getenv("FILOTSENSE_API_URL", "https://api.filotsense.io/v1")
FILOTSENSE_API_KEY = os.getenv("FILOTSENSE_API_KEY")

# Cache configuration
CACHE_EXPIRY = 300  # 5 minutes cache for sentiment data
RATE_LIMIT_PERIOD = 120  # 2 minutes between API calls to avoid rate limiting

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
    Check if the FilotSense API is accessible
    
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
        url = f"{FILOTSENSE_API_URL}/health"
        
        # Use API key if available
        headers = {}
        if FILOTSENSE_API_KEY:
            headers["X-API-Key"] = FILOTSENSE_API_KEY
            
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

def get_sentiment_data(token: str = None) -> Dict[str, Any]:
    """
    Get sentiment data for a specific token or all major tokens
    
    Args:
        token: Optional token symbol to get sentiment for (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with sentiment data
    """
    try:
        # Generate cache key
        cache_key = f"sentiment_{token.upper() if token else 'all'}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("sentiment"):
            # Rate limited, return cached data if available or error
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return {
                    "status": "error",
                    "message": "Rate limited and no cached data available",
                    "sentiment": {}
                }
        
        # Make API call
        url = f"{FILOTSENSE_API_URL}/sentiment"
        params = {}
        
        if token:
            params["token"] = token.upper()
            
        # Use API key if available
        headers = {}
        if FILOTSENSE_API_KEY:
            headers["X-API-Key"] = FILOTSENSE_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("sentiment")
        
        if response.status_code == 200:
            result = response.json()
            _save_to_cache(cache_key, result)
            return result
            
        # Return fallback data on error
        fallback_data = _generate_fallback_sentiment(token)
        _save_to_cache(cache_key, fallback_data)
        return fallback_data
        
    except Exception as e:
        logger.error(f"Error getting sentiment data: {e}")
        # Return fallback data on error
        fallback_data = _generate_fallback_sentiment(token)
        _save_to_cache(cache_key, fallback_data)
        return fallback_data

def get_price_data(token: str = None) -> Dict[str, Any]:
    """
    Get price data for a specific token or all major tokens
    
    Args:
        token: Optional token symbol to get price for (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with price data
    """
    try:
        # Generate cache key
        cache_key = f"price_{token.upper() if token else 'all'}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("price"):
            # Rate limited, return cached data if available or error
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return {
                    "status": "error",
                    "message": "Rate limited and no cached data available",
                    "prices": {}
                }
        
        # Make API call
        url = f"{FILOTSENSE_API_URL}/prices"
        params = {}
        
        if token:
            params["token"] = token.upper()
            
        # Use API key if available
        headers = {}
        if FILOTSENSE_API_KEY:
            headers["X-API-Key"] = FILOTSENSE_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("price")
        
        if response.status_code == 200:
            result = response.json()
            _save_to_cache(cache_key, result)
            return result
            
        # Return fallback data on error
        fallback_data = _generate_fallback_prices(token)
        _save_to_cache(cache_key, fallback_data)
        return fallback_data
        
    except Exception as e:
        logger.error(f"Error getting price data: {e}")
        # Return fallback data on error
        fallback_data = _generate_fallback_prices(token)
        _save_to_cache(cache_key, fallback_data)
        return fallback_data

def get_token_trends(token: str) -> Dict[str, Any]:
    """
    Get trend data for a specific token
    
    Args:
        token: Token symbol to get trends for (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with trend data
    """
    try:
        # Generate cache key
        cache_key = f"trends_{token.upper()}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("trends"):
            # Rate limited, return cached data if available or error
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return {
                    "status": "error",
                    "message": "Rate limited and no cached data available",
                    "trends": {}
                }
        
        # Make API call
        url = f"{FILOTSENSE_API_URL}/trends"
        params = {"token": token.upper()}
        
        # Use API key if available
        headers = {}
        if FILOTSENSE_API_KEY:
            headers["X-API-Key"] = FILOTSENSE_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("trends")
        
        if response.status_code == 200:
            result = response.json()
            _save_to_cache(cache_key, result)
            return result
            
        # Return fallback data on error
        fallback_data = {
            "status": "fallback",
            "message": f"Unable to retrieve trend data for {token}",
            "trends": {}
        }
        _save_to_cache(cache_key, fallback_data)
        return fallback_data
        
    except Exception as e:
        logger.error(f"Error getting trend data: {e}")
        # Return fallback data on error
        fallback_data = {
            "status": "error",
            "message": f"Error: {str(e)}",
            "trends": {}
        }
        _save_to_cache(cache_key, fallback_data)
        return fallback_data

def get_topic_sentiment(token: str) -> Dict[str, Any]:
    """
    Get topic-based sentiment for a specific token
    
    Args:
        token: Token symbol to get topic sentiment for (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with topic sentiment data
    """
    try:
        # Generate cache key
        cache_key = f"topic_sentiment_{token.upper()}"
        
        if _is_cache_valid(cache_key):
            # Return cached data
            return _cache[cache_key]["data"]
        
        if not _can_make_api_call("topic_sentiment"):
            # Rate limited, return cached data if available or error
            if cache_key in _cache:
                return _cache[cache_key]["data"]
            else:
                return {
                    "status": "error",
                    "message": "Rate limited and no cached data available",
                    "data": {}
                }
        
        # Make API call
        url = f"{FILOTSENSE_API_URL}/topic-sentiment"
        params = {"token": token.upper()}
        
        # Use API key if available
        headers = {}
        if FILOTSENSE_API_KEY:
            headers["X-API-Key"] = FILOTSENSE_API_KEY
            
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        # Update call timestamp
        _update_api_call_timestamp("topic_sentiment")
        
        if response.status_code == 200:
            result = response.json()
            _save_to_cache(cache_key, result)
            return result
            
        # Return fallback data on error
        fallback_data = _generate_fallback_topic_sentiment(token)
        _save_to_cache(cache_key, fallback_data)
        return fallback_data
        
    except Exception as e:
        logger.error(f"Error getting topic sentiment: {e}")
        # Return fallback data on error
        fallback_data = _generate_fallback_topic_sentiment(token)
        _save_to_cache(cache_key, fallback_data)
        return fallback_data

def _generate_fallback_sentiment(token: str = None) -> Dict[str, Any]:
    """
    Generate fallback sentiment data for testing/development
    
    Args:
        token: Optional token to generate sentiment for
        
    Returns:
        Dictionary with fallback sentiment data
    """
    # Create sentiment data for common tokens
    sentiment_data = {
        "SOL": {"score": 0.35, "timestamp": datetime.now().isoformat()},
        "BTC": {"score": 0.28, "timestamp": datetime.now().isoformat()},
        "ETH": {"score": 0.21, "timestamp": datetime.now().isoformat()},
        "USDC": {"score": 0.1, "timestamp": datetime.now().isoformat()},
        "BONK": {"score": 0.42, "timestamp": datetime.now().isoformat()},
        "JTO": {"score": 0.18, "timestamp": datetime.now().isoformat()},
        "USDT": {"score": 0.05, "timestamp": datetime.now().isoformat()},
        "RAY": {"score": 0.15, "timestamp": datetime.now().isoformat()},
        "PYTH": {"score": 0.22, "timestamp": datetime.now().isoformat()}
    }
    
    result = {
        "status": "fallback",
        "message": "Using fallback sentiment data",
        "sentiment": sentiment_data
    }
    
    # If token specified, filter to just that token
    if token:
        token = token.upper()
        # If token exists in our fallback data
        if token in sentiment_data:
            result["sentiment"] = {token: sentiment_data[token]}
        else:
            # Generate random sentiment for unknown token
            import random
            result["sentiment"] = {
                token: {
                    "score": round(random.uniform(-0.5, 0.5), 2),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    return result

def _generate_fallback_prices(token: str = None) -> Dict[str, Any]:
    """
    Generate fallback price data for testing/development
    
    Args:
        token: Optional token to generate price for
        
    Returns:
        Dictionary with fallback price data
    """
    # Create price data for common tokens
    price_data = {
        "SOL": {
            "price_usd": 146.28,
            "percent_change_24h": 3.5,
            "volume_24h": 1523487254,
            "timestamp": datetime.now().isoformat()
        },
        "BTC": {
            "price_usd": 64832.12,
            "percent_change_24h": 1.2,
            "volume_24h": 29876543210,
            "timestamp": datetime.now().isoformat()
        },
        "ETH": {
            "price_usd": 3456.78,
            "percent_change_24h": 2.3,
            "volume_24h": 12345678901,
            "timestamp": datetime.now().isoformat()
        },
        "USDC": {
            "price_usd": 1.0,
            "percent_change_24h": 0.01,
            "volume_24h": 9876543210,
            "timestamp": datetime.now().isoformat()
        },
        "BONK": {
            "price_usd": 0.000025,
            "percent_change_24h": 8.4,
            "volume_24h": 456789012,
            "timestamp": datetime.now().isoformat()
        },
        "JTO": {
            "price_usd": 2.37,
            "percent_change_24h": 5.1,
            "volume_24h": 98765432,
            "timestamp": datetime.now().isoformat()
        },
        "USDT": {
            "price_usd": 1.0,
            "percent_change_24h": 0.02,
            "volume_24h": 8765432109,
            "timestamp": datetime.now().isoformat()
        },
        "RAY": {
            "price_usd": 1.84,
            "percent_change_24h": 4.7,
            "volume_24h": 87654321,
            "timestamp": datetime.now().isoformat()
        },
        "PYTH": {
            "price_usd": 0.56,
            "percent_change_24h": 2.8,
            "volume_24h": 43210987,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    result = {
        "status": "fallback",
        "message": "Using fallback price data",
        "prices": price_data
    }
    
    # If token specified, filter to just that token
    if token:
        token = token.upper()
        # If token exists in our fallback data
        if token in price_data:
            result["prices"] = {token: price_data[token]}
        else:
            # Generate random price for unknown token
            import random
            result["prices"] = {
                token: {
                    "price_usd": round(random.uniform(0.1, 100.0), 6),
                    "percent_change_24h": round(random.uniform(-10.0, 10.0), 2),
                    "volume_24h": round(random.uniform(1000000, 100000000), 0),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    return result

def _generate_fallback_topic_sentiment(token: str) -> Dict[str, Any]:
    """
    Generate fallback topic sentiment data for testing/development
    
    Args:
        token: Token to generate topic sentiment for
        
    Returns:
        Dictionary with fallback topic sentiment data
    """
    token = token.upper()
    
    # Create topic sentiment data for SOL
    if token == "SOL":
        topic_data = {
            "SOL": {
                "topics": {
                    "development": 0.45,
                    "adoption": 0.38,
                    "security": 0.12,
                    "ecosystem": 0.35,
                    "performance": 0.29
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    # Create topic sentiment data for BTC
    elif token == "BTC":
        topic_data = {
            "BTC": {
                "topics": {
                    "adoption": 0.42,
                    "regulation": -0.15,
                    "security": 0.38,
                    "mining": 0.05,
                    "energy": -0.22
                },
                "timestamp": datetime.now().isoformat()
            }
        }
    # Create topic sentiment data for other tokens
    else:
        # Generate random topic sentiment
        import random
        
        topics = ["adoption", "development", "security", "competition", "innovation"]
        topic_sentiment = {}
        
        for topic in topics:
            topic_sentiment[topic] = round(random.uniform(-0.5, 0.5), 2)
            
        topic_data = {
            token: {
                "topics": topic_sentiment,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    return {
        "status": "fallback",
        "message": "Using fallback topic sentiment data",
        "data": topic_data
    }

# Test the module
if __name__ == "__main__":
    print("Testing FilotSense API Client")
    
    # Check API health
    print(f"API Health Check: {api_health_check()}")
    
    # Get sentiment data for SOL
    sol_sentiment = get_sentiment_data("SOL")
    print(f"\nSOL Sentiment: {sol_sentiment}")
    
    # Get price data for SOL
    sol_price = get_price_data("SOL")
    print(f"\nSOL Price: {sol_price}")
    
    # Get topic sentiment for SOL
    sol_topics = get_topic_sentiment("SOL")
    print(f"\nSOL Topic Sentiment: {sol_topics}")
    
    # Get sentiment for all tokens
    all_sentiment = get_sentiment_data()
    print(f"\nAll Sentiment: {all_sentiment}")