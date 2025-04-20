#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Client for interacting with the Raydium API Service.
"""

import os
import logging
import requests
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
        self.base_url = os.environ.get("NODE_SERVICE_URL", "https://raydium-trader-filot.replit.app") #Use environment variable if available, otherwise default
        self.api_key = os.environ.get("RAYDIUM_API_KEY", "")

        if not self.api_key:
            raise ValueError("RAYDIUM_API_KEY environment variable is required")

        # Headers for all requests
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        # Create a session with retry strategy for connection pooling
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def check_health(self) -> Dict[str, Any]:
        """Check if the API service is healthy."""
        logger.info("Checking API health")
        try:
            response = self.session.get(f"{self.base_url}/health", headers=self.headers)
            response.raise_for_status()
            logger.info("API health check successful")
            return response.json()
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            raise

    def get_service_metadata(self) -> Dict[str, Any]:
        """Get detailed metadata about the API service."""
        logger.info("Fetching API service metadata")
        try:
            response = self.session.get(f"{self.base_url}/metadata", headers=self.headers)
            response.raise_for_status()
            logger.info("Successfully retrieved API metadata")
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching API metadata: {e}")
            raise

    def get_pools(self, limit: int = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get all categorized liquidity pools."""
        logger.info("Fetching all pools data")
        try:
            params = {}
            if limit is not None:
                params["limit"] = limit
            response = self.session.get(f"{self.base_url}/pools", headers=self.headers, params=params)
            response.raise_for_status()
            pools_data = response.json()
            return pools_data.get('pools', []) #Handle case where 'pools' key might be missing
        except Exception as e:
            logger.error(f"Error fetching pools data: {e}")
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
        logger.info(f"Filtering pools: token_symbol={token_symbol}, min_apr={min_apr}, max_apr={max_apr}, limit={limit}")
        try:
            params = {
                "tokenSymbol": token_symbol,
                "tokenAddress": token_address,
                "minApr": min_apr,
                "maxApr": max_apr,
                "limit": limit
            }
            params = {k: v for k, v in params.items() if v is not None}

            response = self.session.get(
                f"{self.base_url}/pools/filter",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error filtering pools: {e}")
            raise

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        logger.info("Fetching cache statistics")
        try:
            response = self.session.get(f"{self.base_url}/cache/stats", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching cache statistics: {e}")
            raise

    def clear_cache(self) -> Dict[str, Any]:
        """Clear the API service cache."""
        logger.info("Clearing API cache")
        try:
            response = self.session.post(f"{self.base_url}/cache/clear", headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error clearing API cache: {e}")
            raise

    def get_token_prices(self, symbols: List[str] = None) -> Dict[str, float]:
        """
        Get current prices for specified tokens.

        Args:
            symbols: List of token symbols to get prices for (e.g., ["SOL", "USDC"])
                    If None, fetches prices for all available tokens

        Returns:
            Dictionary mapping token symbols to their current prices in USD
        """
        logger.info(f"Fetching token prices for {symbols if symbols else 'all tokens'}")
        try:
            params = {}
            if symbols:
                params["symbols"] = ",".join(symbols)

            response = self.session.get(
                f"{self.base_url}/tokens/prices",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            price_data = response.json()
            logger.info(f"Successfully retrieved prices for {len(price_data)} tokens")
            return price_data
        except Exception as e:
            logger.error(f"Error fetching token prices: {e}")
            raise

# Singleton instance for use throughout the application
_instance = None

def get_client():
    """Get the singleton RaydiumClient instance."""
    global _instance
    if _instance is None:
        try:
            _instance = RaydiumClient()
        except Exception as e:
            logger.error(f"Failed to initialize RaydiumClient: {e}")
            raise
    return _instance