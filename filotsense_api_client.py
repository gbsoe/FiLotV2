#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FilotSense API Client for FiLot Telegram bot
Integrates with the FilotSense API to fetch real-time cryptocurrency sentiment data
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
API_BASE_URL = "https://filotsense.replit.app/api"
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
    """Build request headers"""
    headers = {
        "Accept": "application/json",
        "User-Agent": "FiLotTelegramBot/1.0"
    }
    return headers

def get_sentiment_data(token_symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Get sentiment data for cryptocurrencies
    
    Args:
        token_symbol: Optional token symbol to filter results (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with sentiment data or empty dict on error
    """
    cache_key = f"sentiment_simple_{token_symbol or 'all'}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        url = f"{API_BASE_URL}/sentiment/simple"
        logger.info(f"Fetching sentiment data from FilotSense API: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "sentiment" in data:
                result = {"status": "success", "timestamp": data.get("timestamp", "")}
                
                # If token symbol is provided, filter for just that token
                if token_symbol:
                    token_upper = token_symbol.upper()
                    if token_upper in data["sentiment"]:
                        result["sentiment"] = {token_upper: data["sentiment"][token_upper]}
                    else:
                        result["sentiment"] = {}
                        result["message"] = f"No sentiment data available for {token_symbol}"
                else:
                    result["sentiment"] = data["sentiment"]
                
                _save_to_cache(cache_key, result)
                return result
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching sentiment data from FilotSense API: {e}")
    
    # Return empty dict on error
    return {"status": "error", "sentiment": {}, "message": "Failed to retrieve sentiment data"}

def get_price_data(token_symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Get price data for cryptocurrencies
    
    Args:
        token_symbol: Optional token symbol to filter results (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with price data or empty dict on error
    """
    cache_key = f"prices_latest_{token_symbol or 'all'}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        url = f"{API_BASE_URL}/prices/latest"
        logger.info(f"Fetching price data from FilotSense API: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "prices" in data:
                result = {
                    "status": "success", 
                    "timestamp": data.get("timestamp", ""),
                    "data_attribution": data.get("data_attribution", "")
                }
                
                # If token symbol is provided, filter for just that token
                if token_symbol:
                    token_upper = token_symbol.upper()
                    if token_upper in data["prices"]:
                        result["prices"] = {token_upper: data["prices"][token_upper]}
                    else:
                        result["prices"] = {}
                        result["message"] = f"No price data available for {token_symbol}"
                else:
                    result["prices"] = data["prices"]
                
                _save_to_cache(cache_key, result)
                return result
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching price data from FilotSense API: {e}")
    
    # Return empty dict on error
    return {"status": "error", "prices": {}, "message": "Failed to retrieve price data"}

def get_token_sources(token_symbol: str) -> Dict[str, Any]:
    """
    Get news and social media sources for a specific cryptocurrency
    
    Args:
        token_symbol: Token symbol (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with source data or empty dict on error
    """
    cache_key = f"sources_{token_symbol}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        token_upper = token_symbol.upper()
        url = f"{API_BASE_URL}/crypto/sources/{token_upper}"
        logger.info(f"Fetching sources for {token_upper} from FilotSense API: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success":
                _save_to_cache(cache_key, data)
                return data
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching sources from FilotSense API: {e}")
    
    # Return empty dict on error
    return {"status": "error", "sources": [], "message": f"Failed to retrieve sources for {token_symbol}"}

def get_comprehensive_data(token_symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Get comprehensive data including prices, sentiment, and market correlations
    
    Args:
        token_symbol: Optional token symbol to filter results (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with comprehensive data or empty dict on error
    """
    cache_key = f"realdata_{token_symbol or 'all'}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        # Build URL with optional token filter
        url = f"{API_BASE_URL}/realdata"
        if token_symbol:
            url += f"?symbol={token_symbol.upper()}"
            
        logger.info(f"Fetching comprehensive data from FilotSense API: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success":
                _save_to_cache(cache_key, data)
                return data
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching comprehensive data from FilotSense API: {e}")
    
    # Return empty dict on error
    return {"status": "error", "data": {}, "message": "Failed to retrieve comprehensive data"}

def get_topic_sentiment(token_symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Get sentiment data segmented by topic for cryptocurrencies
    
    Args:
        token_symbol: Optional token symbol to filter results (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with topic sentiment data or empty dict on error
    """
    cache_key = f"sentiment_topics_{token_symbol or 'all'}"
    cached_data = _get_from_cache(cache_key)
    
    if cached_data:
        return cached_data
    
    try:
        _rate_limit()
        
        url = f"{API_BASE_URL}/sentiment/topics"
        logger.info(f"Fetching topic sentiment from FilotSense API: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data["status"] == "success" and "data" in data:
                result = {"status": "success", "timestamp": data.get("timestamp", "")}
                
                # If token symbol is provided, filter for just that token
                if token_symbol:
                    token_upper = token_symbol.upper()
                    if token_upper in data["data"]:
                        result["data"] = {token_upper: data["data"][token_upper]}
                    else:
                        result["data"] = {}
                        result["message"] = f"No topic sentiment data available for {token_symbol}"
                else:
                    result["data"] = data["data"]
                
                _save_to_cache(cache_key, result)
                return result
            
            logger.warning(f"API returned unexpected data format: {data}")
        else:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
    
    except Exception as e:
        logger.error(f"Error fetching topic sentiment from FilotSense API: {e}")
    
    # Return empty dict on error
    return {"status": "error", "data": {}, "message": "Failed to retrieve topic sentiment data"}

def api_health_check() -> bool:
    """
    Check if the FilotSense API is available
    
    Returns:
        True if API is available, False otherwise
    """
    try:
        _rate_limit()
        
        url = f"{API_BASE_URL}/prices/latest"
        logger.info(f"Checking FilotSense API health: {url}")
        
        response = requests.get(
            url,
            headers=_build_headers(),
            timeout=5  # Shorter timeout for health check
        )
        
        return response.status_code == 200
    
    except Exception as e:
        logger.error(f"FilotSense API health check failed: {e}")
        return False

# Initialize with a health check
if __name__ == "__main__":
    is_healthy = api_health_check()
    logger.info(f"FilotSense API is {'available' if is_healthy else 'unavailable'}")
    
    if is_healthy:
        # Test retrieving sentiment data
        sentiment_data = get_sentiment_data()
        if sentiment_data.get("status") == "success":
            logger.info(f"Retrieved sentiment data for {len(sentiment_data.get('sentiment', {}))} tokens")
        
        # Test retrieving price data
        price_data = get_price_data()
        if price_data.get("status") == "success":
            logger.info(f"Retrieved price data for {len(price_data.get('prices', {}))} tokens")