#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client for interacting with the Raydium API Service.
"""

import os
import logging
import requests
import time
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter

try:
    from urllib3.util.retry import Retry
except ImportError:
    # Define a minimal Retry implementation if urllib3 is not available
    class Retry:
        def __init__(self, total=3, backoff_factor=1, status_forcelist=None):
            self.total = total
            self.backoff_factor = backoff_factor
            self.status_forcelist = status_forcelist or []

try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
except ImportError:
    # Ignore if dotenv is not installed
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('raydium_client')

class RaydiumClient:
    """Client for interacting with the Raydium API Service."""

    def __init__(self):
        """Initialize the client with configuration from environment variables."""
        # Use the correct API URL, ensuring it doesn't end with a slash
        base_url = os.environ.get("RAYDIUM_API_URL", "https://raydium-trader-filot.replit.app")
        # Remove trailing slash if it exists to avoid double slash issues
        self.base_url = base_url.rstrip('/')
        self.api_key = os.environ.get("RAYDIUM_API_KEY", "raydium_filot_api_key_125fje90")

        # Create a session for better performance
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        })
        
        logger.info(f"Initialized Raydium client with API URL: {self.base_url}")
        
        # Verify the configured connection is valid
        try:
            self.check_health()
            logger.info("Raydium API connection successfully verified")
        except Exception as e:
            logger.warning(f"Raydium API initial connection could not be verified: {e}")
            # We don't raise an error here to allow the application to start
            # even if the API is temporarily unavailable

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def make_request_with_retry(self, endpoint: str, method: str = 'get', params: dict = None, max_retries: int = 3) -> Dict[str, Any]:
        """Make API request with retry logic."""
        retries = 0
        while retries < max_retries:
            try:
                if method.lower() == 'get':
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        params=params,
                        timeout=10
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json=params,
                        timeout=10
                    )

                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if (hasattr(e, 'response') and 
                    e.response is not None and
                    (e.response.status_code == 429 or e.response.status_code >= 500) and
                    retries < max_retries - 1):
                    retries += 1
                    delay = 2 ** retries
                    logger.warning(f"Retry attempt {retries} for {endpoint} after {delay}s delay")
                    time.sleep(delay)
                else:
                    logger.error(f"Request failed: {str(e)}")
                    raise

    def get_pools(self) -> Dict[str, Any]:
        """
        Get all categorized liquidity pools from the Raydium API.
        Returns only verified pools that actually exist in the Raydium system.
        If API fails, returns empty lists rather than using hardcoded fallback data.
        """
        logger.info("Fetching pools data from Raydium API")
        try:
            # First try to get pools from the main API endpoint
            response = self.make_request_with_retry("/api/pools")
            
            # Extract the pools from the response
            best_performance = response.get('pools', {}).get('bestPerformance', [])
            top_stable = response.get('pools', {}).get('topStable', [])
            
            logger.info(f"Successfully fetched {len(best_performance)} best performance pools and {len(top_stable)} stable pools")
            
            # If we got empty results, try to fetch individual pool types
            if not best_performance:
                try:
                    # Try to fetch best performance pools separately
                    best_response = self.make_request_with_retry("/api/pools/best")
                    best_performance = best_response.get('pools', [])
                    logger.info(f"Fetched {len(best_performance)} best performance pools separately")
                except Exception as e:
                    logger.error(f"Failed to fetch best performance pools separately: {e}")
            
            if not top_stable:
                try:
                    # Try to fetch stable pools separately
                    stable_response = self.make_request_with_retry("/api/pools/stable")
                    top_stable = stable_response.get('pools', [])
                    logger.info(f"Fetched {len(top_stable)} stable pools separately")
                except Exception as e:
                    logger.error(f"Failed to fetch stable pools separately: {e}")
            
            # Return whatever we were able to fetch
            return {
                'bestPerformance': best_performance,
                'topStable': top_stable
            }
        except Exception as e:
            logger.error(f"Critical error fetching pools from Raydium API: {e}")
            
            # Return empty lists instead of hardcoded data
            # This ensures we never show non-existent pools to users
            return {'bestPerformance': [], 'topStable': []}

    def filter_pools(
        self,
        token_symbol: Optional[str] = None,
        min_apr: Optional[float] = None,
        max_apr: Optional[float] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Filter pools based on criteria."""
        logger.info(f"Filtering pools: token={token_symbol}, min_apr={min_apr}, max_apr={max_apr}")
        try:
            params = {
                "tokenSymbol": token_symbol,
                "minApr": min_apr,
                "maxApr": max_apr,
                "limit": limit
            }
            params = {k: v for k, v in params.items() if v is not None}
            return self.make_request_with_retry("/api/filter", params=params)
        except Exception as e:
            logger.error(f"Error filtering pools: {e}")
            return {"count": 0, "pools": []}

    def get_pool_by_id(self, pool_id: str) -> Dict[str, Any]:
        """Get specific pool by ID."""
        try:
            return self.make_request_with_retry(f"/api/pool/{pool_id}")
        except Exception as e:
            logger.error(f"Error fetching pool {pool_id}: {e}")
            return None

    def check_health(self) -> Dict[str, Any]:
        """Check if the API service is healthy."""
        logger.info("Checking API health")
        try:
            return self.make_request_with_retry("/health")
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            raise

    def get_service_metadata(self) -> Dict[str, Any]:
        """Get detailed metadata about the API service."""
        logger.info("Fetching API service metadata")
        try:
            return self.make_request_with_retry("/metadata")
        except Exception as e:
            logger.error(f"Error fetching API metadata: {e}")
            raise

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.make_request_with_retry("/cache/stats")

    def clear_cache(self) -> Dict[str, Any]:
        """Clear the API service cache."""
        return self.make_request_with_retry("/cache/clear", method='post')

    def get_token_prices(self, symbols: Optional[List[str]] = None) -> Dict[str, float]:
        """Get current prices for specified tokens."""
        try:
            params = {"symbols": ",".join(symbols)} if symbols else None
            return self.make_request_with_retry("/tokens/prices", params=params)
        except Exception as e:
            logger.error(f"Error fetching token prices: {e}")
            raise
            
    def get_swap_route(self, from_token: str, to_token: str, amount: float) -> Dict[str, Any]:
        """
        Get the best route for swapping tokens.
        
        Args:
            from_token: Token to swap from
            to_token: Token to swap to
            amount: Amount to swap
            
        Returns:
            Dict with route details
        """
        logger.info(f"Getting swap route: {from_token} -> {to_token}, amount: {amount}")
        try:
            params = {
                "fromToken": from_token,
                "toToken": to_token,
                "amount": amount
            }
            return self.make_request_with_retry("/api/swap/route", method='post', params=params)
        except Exception as e:
            logger.error(f"Error getting swap route: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def simulate_swap(self, from_token: str, to_token: str, amount: float) -> Dict[str, Any]:
        """
        Simulate a token swap to get expected output without executing it.
        
        Args:
            from_token: Token to swap from
            to_token: Token to swap to
            amount: Amount to swap
            
        Returns:
            Dict with simulation results
        """
        logger.info(f"Simulating swap: {from_token} -> {to_token}, amount: {amount}")
        try:
            params = {
                "fromToken": from_token,
                "toToken": to_token,
                "amount": amount
            }
            return self.make_request_with_retry("/api/swap/simulate", method='post', params=params)
        except Exception as e:
            logger.error(f"Error simulating swap: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def get_liquidity_info(self, pool_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a liquidity pool.
        
        Args:
            pool_id: ID of the liquidity pool
            
        Returns:
            Dict with pool liquidity details
        """
        logger.info(f"Getting liquidity info for pool: {pool_id}")
        try:
            return self.make_request_with_retry(f"/api/liquidity/{pool_id}")
        except Exception as e:
            logger.error(f"Error getting liquidity info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Utility function to calculate optimal swap amounts
def calculate_optimal_swap_amount(
    total_amount: float,
    token_a: str,
    token_b: str,
    token_ratio: float = 1.0,
    token_prices: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Calculate the optimal distribution of tokens for adding liquidity.
    
    Args:
        total_amount: Total amount in USD to add as liquidity
        token_a: First token in the pool
        token_b: Second token in the pool
        token_ratio: Ratio of token_a to token_b in the pool
        token_prices: Dictionary of token prices (optional)
        
    Returns:
        Dict with token amounts
    """
    try:
        logger.info(f"Calculating optimal swap amounts: {total_amount} USD for {token_a}/{token_b}")
        
        # Get token prices if not provided
        if not token_prices:
            client = get_client()
            prices_response = client.get_token_prices([token_a, token_b])
            token_prices = prices_response.get('prices', {})
            
        # Get token prices
        price_a = token_prices.get(token_a, 1.0)
        price_b = token_prices.get(token_b, 1.0)
        
        if price_a <= 0 or price_b <= 0:
            logger.warning(f"Invalid token prices: {token_a}=${price_a}, {token_b}=${price_b}")
            price_a = price_a or 1.0
            price_b = price_b or 1.0
        
        # Calculate amounts in USD
        amount_a_usd = total_amount / 2
        amount_b_usd = total_amount / 2
        
        # Adjust based on token ratio
        if token_ratio != 1.0:
            adjustment_factor = (token_ratio * price_b) / price_a
            total_parts = 1 + adjustment_factor
            amount_a_usd = total_amount / total_parts
            amount_b_usd = total_amount - amount_a_usd
            
        # Convert USD amounts to token amounts
        token_a_amount = amount_a_usd / price_a
        token_b_amount = amount_b_usd / price_b
        
        logger.info(f"Optimal amounts: {token_a_amount} {token_a} (${amount_a_usd}), {token_b_amount} {token_b} (${amount_b_usd})")
        
        return {
            "success": True,
            "total_amount_usd": total_amount,
            "token_a": token_a,
            "token_b": token_b,
            "token_a_amount": token_a_amount,
            "token_b_amount": token_b_amount,
            "token_a_amount_usd": amount_a_usd,
            "token_b_amount_usd": amount_b_usd,
            "token_a_price": price_a,
            "token_b_price": price_b,
            "token_ratio": token_ratio
        }
    except Exception as e:
        logger.error(f"Error calculating optimal swap amounts: {e}")
        return {
            "success": False,
            "error": str(e),
            "token_a": token_a,
            "token_b": token_b,
            "total_amount_usd": total_amount
        }

# Singleton instance
_instance = None

def get_client() -> RaydiumClient:
    """Get the singleton RaydiumClient instance."""
    global _instance
    if _instance is None:
        try:
            _instance = RaydiumClient()
        except Exception as e:
            logger.error(f"Failed to initialize RaydiumClient: {e}")
            raise
    return _instance