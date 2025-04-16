#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Raydium SDK integration for fetching cryptocurrency pool data
"""

import logging
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class RaydiumClient:
    """Client for interacting with Raydium API to fetch pool data."""
    
    def __init__(self, pool_ids: List[str]):
        """
        Initialize the Raydium client.
        
        Args:
            pool_ids: List of pool IDs to track
        """
        self.pool_ids = pool_ids
        self.base_url = "https://api.raydium.io/v2"
        self.session = None
        self.last_request_time = 0
        
    async def _ensure_session(self):
        """Ensure that the aiohttp session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def check_status(self) -> bool:
        """
        Check if the Raydium API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/info") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error checking Raydium API status: {e}")
            return False
            
    async def fetch_pool_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data for the tracked pools.
        
        Returns:
            List of dictionaries containing pool data
        """
        pools_data = []
        
        try:
            await self._ensure_session()
            
            # Fetch general liquidity pools data
            async with self.session.get(f"{self.base_url}/liquidity/mainnet") as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch liquidity data: {response.status}")
                    return []
                
                pools = await response.json()
                
                # Filter for the pools we're interested in
                for pool in pools:
                    if pool.get("id") in self.pool_ids:
                        # Fetch additional data for this pool
                        pool_detail = await self._fetch_pool_detail(pool["id"])
                        if pool_detail:
                            pool_data = {**pool, **pool_detail}
                            pools_data.append(pool_data)
            
            # Fetch additional high APR pools (top 5)
            high_apr_pools = await self._fetch_high_apr_pools(5)
            pools_data.extend(high_apr_pools)
            
            # Fetch stable pools (USDC/USDT pairs) if not already included
            stable_pools = await self._fetch_stable_pools()
            
            # Add stable pools that aren't already in pools_data
            existing_ids = {pool["id"] for pool in pools_data}
            for pool in stable_pools:
                if pool["id"] not in existing_ids:
                    pools_data.append(pool)
            
            return pools_data
            
        except Exception as e:
            logger.error(f"Error fetching pool data: {e}")
            return []
            
    async def _fetch_pool_detail(self, pool_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed data for a specific pool.
        
        Args:
            pool_id: ID of the pool to fetch data for
            
        Returns:
            Dictionary with pool details or None if failed
        """
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/pool/{pool_id}") as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch pool detail: {response.status}")
                    return None
                
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching pool detail: {e}")
            return None
            
    async def _fetch_high_apr_pools(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch pools with the highest APR.
        
        Args:
            limit: Number of high APR pools to fetch
            
        Returns:
            List of dictionaries containing high APR pool data
        """
        try:
            await self._ensure_session()
            
            # Fetch all liquidity pools
            async with self.session.get(f"{self.base_url}/liquidity/mainnet") as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch liquidity data: {response.status}")
                    return []
                
                pools = await response.json()
                
                # Sort by APR (descending)
                sorted_pools = sorted(pools, key=lambda x: float(x.get("apr", 0)), reverse=True)
                
                # Get the top pools
                high_apr_pools = sorted_pools[:limit]
                
                # Fetch additional data for these pools
                result = []
                for pool in high_apr_pools:
                    pool_detail = await self._fetch_pool_detail(pool["id"])
                    if pool_detail:
                        pool_data = {**pool, **pool_detail}
                        result.append(pool_data)
                
                return result
                
        except Exception as e:
            logger.error(f"Error fetching high APR pools: {e}")
            return []
            
    async def _fetch_stable_pools(self) -> List[Dict[str, Any]]:
        """
        Fetch stable pools (USDC/USDT pairs with SOL).
        
        Returns:
            List of dictionaries containing stable pool data
        """
        try:
            await self._ensure_session()
            
            # Fetch all liquidity pools
            async with self.session.get(f"{self.base_url}/liquidity/mainnet") as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch liquidity data: {response.status}")
                    return []
                
                pools = await response.json()
                
                # Filter for stable pools (SOL-USDC, SOL-USDT)
                stable_pools = []
                for pool in pools:
                    token_a = pool.get("token_a", {}).get("symbol", "").upper()
                    token_b = pool.get("token_b", {}).get("symbol", "").upper()
                    
                    if (token_a == "SOL" and token_b in ["USDC", "USDT"]) or \
                       (token_b == "SOL" and token_a in ["USDC", "USDT"]):
                        pool_detail = await self._fetch_pool_detail(pool["id"])
                        if pool_detail:
                            pool_data = {**pool, **pool_detail}
                            stable_pools.append(pool_data)
                
                return stable_pools
                
        except Exception as e:
            logger.error(f"Error fetching stable pools: {e}")
            return []
