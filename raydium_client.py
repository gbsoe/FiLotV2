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
from urllib3.util.retry import Retry

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
        self.base_url = os.environ.get("RAYDIUM_API_URL", "https://raydium-trader-filot.replit.app")
        self.api_key = os.environ.get("RAYDIUM_API_KEY", "")

        if not self.api_key:
            raise ValueError("RAYDIUM_API_KEY environment variable is required")

        # Headers for all requests
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Create a session with retry strategy
        self.session = requests.Session()
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
                        headers=self.headers,
                        params=params,
                        timeout=10
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
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

    def get_pools(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get all categorized liquidity pools."""
        logger.info("Fetching pools data")
        try:
            params = {"limit": limit} if limit else None
            response = self.make_request_with_retry("/pools", params=params)
            return response.get('pools', {})
        except Exception as e:
            logger.error(f"Error fetching pools: {e}")
            raise

    def filter_pools(
        self,
        token_symbol: Optional[str] = None,
        token_address: Optional[str] = None,
        min_apr: Optional[float] = None,
        max_apr: Optional[float] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Filter pools based on criteria."""
        logger.info(f"Filtering pools: token={token_symbol}, min_apr={min_apr}, max_apr={max_apr}")
        try:
            params = {
                "tokenSymbol": token_symbol,
                "tokenAddress": token_address,
                "minApr": min_apr,
                "maxApr": max_apr,
                "limit": limit
            }
            params = {k: v for k, v in params.items() if v is not None}
            return self.make_request_with_retry("/pools/filter", params=params)
        except Exception as e:
            logger.error(f"Error filtering pools: {e}")
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