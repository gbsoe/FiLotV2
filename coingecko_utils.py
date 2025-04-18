"""
CoinGecko API integration for fetching accurate token prices
"""

import logging
import requests
from typing import Dict, Any, Optional, List, Union

# Configure logging
logger = logging.getLogger(__name__)

# CoinGecko API Base URL
COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

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

def get_token_price(token_symbol: str) -> Optional[float]:
    """
    Get the current price of a token from CoinGecko API.
    
    Args:
        token_symbol: The token symbol (e.g., "SOL", "BTC")
        
    Returns:
        The token price in USD, or None if the price couldn't be fetched
    """
    token_id = TOKEN_ID_MAPPING.get(token_symbol.upper())
    if not token_id:
        logger.warning(f"No CoinGecko ID mapping for token symbol: {token_symbol}")
        return None
        
    try:
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
            logger.info(f"Fetched price for {token_symbol}: ${price}")
            return float(price)
        else:
            logger.warning(f"Could not find price for {token_symbol} in CoinGecko response")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching {token_symbol} price from CoinGecko: {e}")
        return None
        
def get_multiple_token_prices(token_symbols: List[str]) -> Dict[str, float]:
    """
    Get prices for multiple tokens from CoinGecko API in a single request.
    
    Args:
        token_symbols: List of token symbols (e.g., ["SOL", "BTC"])
        
    Returns:
        Dictionary mapping token symbols to their USD prices
    """
    token_ids = []
    symbol_to_id = {}
    
    # Get CoinGecko IDs for all tokens
    for symbol in token_symbols:
        token_id = TOKEN_ID_MAPPING.get(symbol.upper())
        if token_id:
            token_ids.append(token_id)
            symbol_to_id[token_id] = symbol.upper()
    
    if not token_ids:
        logger.warning("No valid token symbols provided")
        return {}
        
    try:
        url = f"{COINGECKO_API_BASE}/simple/price"
        params = {
            "ids": ",".join(token_ids),
            "vs_currencies": "usd"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Map results back to token symbols
        result = {}
        for token_id, token_data in data.items():
            symbol = symbol_to_id.get(token_id)
            if symbol and "usd" in token_data:
                result[symbol] = float(token_data["usd"])
                
        logger.info(f"Fetched prices for {len(result)} tokens from CoinGecko")
        return result
            
    except Exception as e:
        logger.error(f"Error fetching token prices from CoinGecko: {e}")
        return {}

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

# Verify API access on module import
try:
    logger.info("Testing CoinGecko API connection...")
    test_price = get_token_price("SOL")
    if test_price is not None:
        logger.info(f"CoinGecko API is accessible, SOL price: ${test_price}")
    else:
        logger.warning("Could not fetch SOL price from CoinGecko API")
except Exception as e:
    logger.error(f"Error testing CoinGecko API: {e}")