"""
CoinGecko API integration for fetching accurate token prices
with rate limiting and caching to avoid 429 errors
"""

import logging
import requests
import time
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import os

# Configure logging
logger = logging.getLogger(__name__)

# CoinGecko API Base URL
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

# Rate limiting parameters
MIN_REQUEST_INTERVAL = 6.0  # At least 6 seconds between requests (10 per minute max for free tier)
last_request_time = 0

# Cache parameters
CACHE_EXPIRY = 300  # 5 minutes
price_cache = {}
cache_file = "token_price_cache.json"

# Token ID mapping (symbol to CoinGecko ID)
TOKEN_ID_MAPPING = {
    "SOL": "solana",
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "RAY": "raydium",
    "USDC": "usd-coin",
    "USDT": "tether",
    "BONK": "bonk",
    "SAMO": "samoyedcoin",
    "ORCA": "orca",
    "ATLAS": "star-atlas",
    "MANGO": "mango-markets",
    "SRM": "serum"
}

# Default token prices (used when API is unavailable or rate limited)
DEFAULT_TOKEN_PRICES = {
    "SOL": 131.70,
    "BTC": 65000.00,
    "ETH": 3000.00,
    "RAY": 0.75,
    "USDC": 1.00,
    "USDT": 1.00,
    "BONK": 0.000018,
    "SAMO": 0.015,
    "ORCA": 0.85,
    "ATLAS": 0.006,
    "MANGO": 0.08,
    "SRM": 0.25
}

def _load_cache():
    """Load the price cache from a file if it exists."""
    global price_cache
    try:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
                
                # Convert string timestamps to datetime objects
                for symbol, data in cache_data.items():
                    if 'timestamp' in data:
                        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                
                price_cache = cache_data
                logger.info(f"Loaded price cache for {len(price_cache)} tokens")
    except Exception as e:
        logger.error(f"Error loading price cache: {e}")
        price_cache = {}

def _save_cache():
    """Save the price cache to a file."""
    try:
        # Convert datetime objects to strings
        cache_to_save = {}
        for symbol, data in price_cache.items():
            cache_to_save[symbol] = data.copy()
            if 'timestamp' in cache_to_save[symbol]:
                cache_to_save[symbol]['timestamp'] = cache_to_save[symbol]['timestamp'].isoformat()
        
        with open(cache_file, 'w') as f:
            json.dump(cache_to_save, f)
            logger.info(f"Saved price cache for {len(price_cache)} tokens")
    except Exception as e:
        logger.error(f"Error saving price cache: {e}")

def _apply_rate_limit():
    """Apply rate limiting to avoid 429 errors."""
    global last_request_time
    current_time = time.time()
    elapsed = current_time - last_request_time
    
    if elapsed < MIN_REQUEST_INTERVAL:
        sleep_time = MIN_REQUEST_INTERVAL - elapsed
        logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    last_request_time = time.time()

def get_token_price(token_symbol: str) -> float:
    """
    Get the current price of a token from CoinGecko API with caching and rate limiting.
    
    Args:
        token_symbol: The token symbol (e.g., "SOL", "BTC")
        
    Returns:
        The token price in USD, using cached/default value if API is unavailable
    """
    token_symbol = token_symbol.upper()
    
    # Check cache first
    if token_symbol in price_cache:
        cache_entry = price_cache[token_symbol]
        cache_time = cache_entry.get('timestamp')
        now = datetime.now()
        
        if cache_time and (now - cache_time) < timedelta(seconds=CACHE_EXPIRY):
            logger.info(f"Using cached price for {token_symbol}: ${cache_entry['price']}")
            return cache_entry['price']
    
    # If not in cache or expired, try to fetch from API
    token_id = TOKEN_ID_MAPPING.get(token_symbol)
    if not token_id:
        logger.warning(f"No CoinGecko ID mapping for token symbol: {token_symbol}")
        return DEFAULT_TOKEN_PRICES.get(token_symbol, 0)
    
    try:
        _apply_rate_limit()  # Apply rate limiting
        
        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {
            "ids": token_id,
            "vs_currencies": "usd"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        price = data.get(token_id, {}).get("usd")
        if price is not None:
            # Update cache
            price_cache[token_symbol] = {
                'price': float(price),
                'timestamp': datetime.now()
            }
            _save_cache()
            logger.info(f"Fetched price for {token_symbol}: ${price}")
            return float(price)
        else:
            logger.warning(f"Could not find price for {token_symbol} in CoinGecko response")
            return DEFAULT_TOKEN_PRICES.get(token_symbol, 0)
            
    except Exception as e:
        logger.error(f"Error fetching {token_symbol} price from CoinGecko: {e}")
        return DEFAULT_TOKEN_PRICES.get(token_symbol, 0)
        
def get_multiple_token_prices(token_symbols: List[str]) -> Dict[str, float]:
    """
    Get prices for multiple tokens with caching and rate limiting.
    
    Args:
        token_symbols: List of token symbols (e.g., ["SOL", "BTC"])
        
    Returns:
        Dictionary mapping token symbols to their USD prices
    """
    result = {}
    uncached_symbols = []
    uncached_ids = []
    symbol_to_id = {}
    
    # First check which tokens we need from the cache
    for symbol in token_symbols:
        symbol = symbol.upper()
        
        # Check if in cache and not expired
        if symbol in price_cache:
            cache_entry = price_cache[symbol]
            cache_time = cache_entry.get('timestamp')
            now = datetime.now()
            
            if cache_time and (now - cache_time) < timedelta(seconds=CACHE_EXPIRY):
                result[symbol] = cache_entry['price']
                continue
        
        # If not cached or expired, add to uncached list
        token_id = TOKEN_ID_MAPPING.get(symbol)
        if token_id:
            uncached_symbols.append(symbol)
            uncached_ids.append(token_id)
            symbol_to_id[token_id] = symbol
    
    # If no uncached tokens, return result
    if not uncached_ids:
        logger.info(f"Using cached prices for all {len(result)} tokens")
        return result
    
    # Otherwise, try to fetch uncached tokens
    try:
        _apply_rate_limit()  # Apply rate limiting
        
        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {
            "ids": ",".join(uncached_ids),
            "vs_currencies": "usd"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Update cache and result with new data
        now = datetime.now()
        for token_id, token_data in data.items():
            symbol = symbol_to_id.get(token_id)
            if symbol and "usd" in token_data:
                price = float(token_data["usd"])
                result[symbol] = price
                
                # Update cache
                price_cache[symbol] = {
                    'price': price,
                    'timestamp': now
                }
        
        _save_cache()
        logger.info(f"Fetched prices for {len(uncached_symbols)} tokens from CoinGecko")
            
    except Exception as e:
        logger.error(f"Error fetching token prices from CoinGecko: {e}")
        # Fall back to default prices for uncached tokens
        for symbol in uncached_symbols:
            result[symbol] = DEFAULT_TOKEN_PRICES.get(symbol, 0)
    
    # Fill in any missing tokens with default prices
    for symbol in token_symbols:
        symbol = symbol.upper()
        if symbol not in result:
            result[symbol] = DEFAULT_TOKEN_PRICES.get(symbol, 0)
    
    return result

def get_token_data(token_symbol: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed data for a token from CoinGecko API.
    
    Args:
        token_symbol: The token symbol (e.g., "SOL", "BTC")
        
    Returns:
        Dictionary with token data, or None if the data couldn't be fetched
    """
    token_id = TOKEN_ID_MAPPING.get(token_symbol.upper())
    if not token_id:
        logger.warning(f"No CoinGecko ID mapping for token symbol: {token_symbol}")
        return None
    
    try:
        _apply_rate_limit()  # Apply rate limiting
        
        url = f"{COINGECKO_API_BASE}/coins/{token_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data
            
    except Exception as e:
        logger.error(f"Error fetching {token_symbol} data from CoinGecko: {e}")
        return None

# Load cache on module import
_load_cache()

# Test API connection on module import, but use cached data if available
try:
    logger.info("Testing CoinGecko API connection...")
    test_price = get_token_price("SOL")
    logger.info(f"CoinGecko API is accessible, SOL price: ${test_price}")
except Exception as e:
    logger.error(f"Error testing CoinGecko API: {e}")