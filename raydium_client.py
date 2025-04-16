"""
Client for fetching pool data from Raydium API and token prices from CoinGecko
"""

import os
import json
import asyncio
import logging
import aiohttp
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load config
CONFIG_PATH = "config.json"
config = {}
try:
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
except Exception as e:
    logger.error(f"Error loading config.json: {e}")
    config = {"poolIds": []}

# Default pool IDs if not in config
DEFAULT_POOL_IDS = [
    "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2",
    "7XawhbbxtsRcQA8KTkHT9f9nc6d69UwqCDh6U5EEbEmX",
    "6UmmUiYoBjSrhakAobJw8BvkmJtDVxaeBtbt7rxWo1mg"
]
POOL_IDS = config.get("poolIds", DEFAULT_POOL_IDS)

# Relevant token symbols to track
TOKEN_SYMBOLS = ["SOL", "USDC", "USDT", "RAY"]

async def _fetch_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch JSON data from a URL with timeout."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    logger.error(f"Error fetching from {url}: Status {response.status}")
                    return {}
                return await response.json()
        except asyncio.TimeoutError:
            logger.error(f"Timeout when fetching from {url}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching from {url}: {e}")
            return {}

async def fetch_token_prices() -> Dict[str, float]:
    """
    Fetch token prices from CoinGecko API.
    Returns a dictionary of token symbols to USD prices.
    """
    logger.info("Fetching token prices from CoinGecko")
    coingecko_url = "https://api.coingecko.com/api/v3/simple/price?ids=solana%2Ctether%2Cusd-coin%2Craydium&vs_currencies=usd"
    
    try:
        data = await _fetch_json(coingecko_url, timeout=10)
        if not data:
            logger.warning("No data received from CoinGecko")
            return _get_fallback_prices()
            
        prices = {
            "SOL": data.get("solana", {}).get("usd", 0),
            "USDT": data.get("tether", {}).get("usd", 1),  # Default to 1 for stablecoins
            "USDC": data.get("usd-coin", {}).get("usd", 1),  # Default to 1 for stablecoins
            "RAY": data.get("raydium", {}).get("usd", 0)
        }
        
        # Validate prices
        for symbol, price in prices.items():
            if price is None or price <= 0:
                if symbol in ["USDT", "USDC"]:
                    prices[symbol] = 1.0  # Default stablecoins to 1.0
                else:
                    prices[symbol] = 0.0
                    
        logger.info(f"Fetched token prices: {prices}")
        return prices
    except Exception as e:
        logger.error(f"Error fetching token prices: {e}")
        return _get_fallback_prices()

def _get_fallback_prices() -> Dict[str, float]:
    """Get fallback token prices if API fails."""
    return {
        "SOL": 0.0,
        "USDT": 1.0,
        "USDC": 1.0,
        "RAY": 0.0
    }

async def fetch_pools(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch pool data from Raydium API.
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of pool data dictionaries
    """
    logger.info(f"Fetching pool data for {len(POOL_IDS)} pool IDs")
    
    # Mock data structure to simulate fetching from Raydium SDK
    # This would be replaced with actual API calls in production
    pools = []
    token_prices = await fetch_token_prices()
    
    try:
        # Make API request to Raydium
        raydium_url = f"https://api.raydium.io/v2/ammPools"
        raydium_data = await _fetch_json(raydium_url)
        
        if not raydium_data or not isinstance(raydium_data, dict) or "data" not in raydium_data:
            logger.warning("Invalid response from Raydium API")
            return generate_mock_pools(token_prices, limit)
            
        all_pools = raydium_data.get("data", [])
        if not all_pools:
            logger.warning("No pools found in Raydium API response")
            return generate_mock_pools(token_prices, limit)
            
        # Filter pools by IDs from config
        for pool_info in all_pools:
            pool_id = pool_info.get("id")
            if pool_id in POOL_IDS:
                # Extract token pair
                token_a_symbol = pool_info.get("baseMint", {}).get("symbol", "Unknown")
                token_b_symbol = pool_info.get("quoteMint", {}).get("symbol", "Unknown")
                
                # Extract APR data
                apr_24h = _extract_apr(pool_info, "day") 
                apr_7d = _extract_apr(pool_info, "week")
                apr_30d = _extract_apr(pool_info, "month")
                
                # Extract TVL and volume
                tvl = _extract_numeric(pool_info, "liquidity", "usd")
                volume_24h = _extract_numeric(pool_info, "volume", "day", "usd")
                
                # Determine token prices
                token_a_price = token_prices.get(token_a_symbol, 0)
                token_b_price = token_prices.get(token_b_symbol, 0)
                
                # Create standardized pool object
                pool = {
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
                    "fee": pool_info.get("fee", 0) / 10000,  # Convert basis points to percentage
                    "volume_24h": volume_24h,
                    "tx_count_24h": pool_info.get("txCount", {}).get("day", 0)
                }
                
                pools.append(pool)
        
        # Sort by APR and limit
        pools.sort(key=lambda p: p.get("apr_24h", 0), reverse=True)
        pools = pools[:limit]
        
        if not pools:
            logger.warning(f"No pools found with configured IDs: {POOL_IDS}")
            return generate_mock_pools(token_prices, limit)
            
        logger.info(f"Successfully fetched {len(pools)} pools")
        return pools
    except Exception as e:
        logger.error(f"Error fetching pools: {e}")
        return generate_mock_pools(token_prices, limit)

def _extract_apr(pool_info: Dict[str, Any], time_period: str) -> float:
    """Extract APR value from pool info."""
    try:
        apr = pool_info.get(time_period, {}).get("apr", 0)
        return _format_apr(apr)
    except (TypeError, KeyError):
        return 0.0

def _extract_numeric(pool_info: Dict[str, Any], field: str, *keys: str) -> float:
    """Extract numeric value from nested dict."""
    try:
        value = pool_info
        for k in [field] + list(keys):
            value = value.get(k, {})
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0
    except (TypeError, KeyError):
        return 0.0

def _format_apr(apr: float) -> float:
    """Format APR value."""
    if apr is None or not isinstance(apr, (int, float)) or apr < 0:
        return 0.0
    return round(apr, 2)

def generate_mock_pools(token_prices: Dict[str, float], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Generate mock pool data for testing when API fails.
    
    Args:
        token_prices: Dictionary of token symbols to USD prices
        limit: Maximum number of mock pools to generate
        
    Returns:
        List of mock pool data dictionaries
    """
    # Some predefined pairs
    pairs = [
        ("SOL", "USDC"),
        ("SOL", "USDT"),
        ("RAY", "SOL"),
        ("RAY", "USDC"),
        ("USDC", "USDT")
    ]
    
    pools = []
    for i, (token_a, token_b) in enumerate(pairs[:limit]):
        apr_base = max(5.0 + i * 3.5, 0)  # Generate different APRs
        pool = {
            "id": f"mock_pool_{i}",
            "token_a": {
                "symbol": token_a,
                "price": token_prices.get(token_a, 0)
            },
            "token_b": {
                "symbol": token_b,
                "price": token_prices.get(token_b, 0)
            },
            "apr_24h": apr_base + 2.0,
            "apr_7d": apr_base,
            "apr_30d": max(apr_base - 1.0, 0),
            "tvl": 1000000.0 / (i + 1),  # Decreasing TVL
            "fee": 0.0025,  # 0.25%
            "volume_24h": 500000.0 / (i + 1),  # Decreasing volume
            "tx_count_24h": 1000 - (i * 100)  # Decreasing tx count
        }
        pools.append(pool)
    
    return pools

# Directly usable functions for the bot
async def get_pools(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get pool data for use in the bot.
    This is the main function to be called from the bot.
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of pool data dictionaries
    """
    return await fetch_pools(limit)

async def get_token_prices() -> Dict[str, float]:
    """
    Get token prices for use in the bot.
    
    Returns:
        Dictionary of token symbols to USD prices
    """
    return await fetch_token_prices()

# For testing
if __name__ == "__main__":
    async def test():
        print("Testing token prices...")
        prices = await fetch_token_prices()
        print(f"Token prices: {prices}")
        
        print("\nTesting pool data...")
        pools = await fetch_pools(limit=3)
        for pool in pools:
            print(f"\nPool: {pool['token_a']['symbol']}/{pool['token_b']['symbol']}")
            print(f"APR 24h: {pool['apr_24h']}%")
            print(f"TVL: ${pool['tvl']:.2f}")
            print(f"Volume 24h: ${pool['volume_24h']:.2f}")
    
    asyncio.run(test())