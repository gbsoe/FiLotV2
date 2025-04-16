#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for the Telegram cryptocurrency pool bot
"""

import time
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache: Dict[str, Dict[str, Any]] = {}

def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """
    Set a value in the cache with a TTL (Time To Live).
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live in seconds (default: 300)
    """
    _cache[key] = {
        'value': value,
        'expires': time.time() + ttl
    }
    
def get_cache(key: str) -> Optional[Any]:
    """
    Get a value from the cache if it exists and hasn't expired.
    
    Args:
        key: Cache key
        
    Returns:
        Cached value if found and not expired, None otherwise
    """
    if key not in _cache:
        return None
        
    cache_entry = _cache[key]
    
    # Check if the cache entry has expired
    if time.time() > cache_entry['expires']:
        del _cache[key]
        return None
        
    return cache_entry['value']
    
def clear_cache(key: Optional[str] = None) -> None:
    """
    Clear the cache or a specific cache entry.
    
    Args:
        key: Cache key to clear (if None, clear all cache)
    """
    if key:
        if key in _cache:
            del _cache[key]
    else:
        _cache.clear()

def format_pool_data(pool_data: List[Dict[str, Any]]) -> str:
    """
    Format pool data into a readable markdown message.
    
    Args:
        pool_data: List of pool data dictionaries
        
    Returns:
        Formatted markdown string
    """
    if not pool_data:
        return "No pool data available."
        
    # Sort pools by APR (descending)
    sorted_pools = sorted(pool_data, key=lambda x: float(x.get("apr", 0)), reverse=True)
    
    # Prepare message
    message = "🏊‍♂️ *Cryptocurrency Pool Data* 🏊‍♂️\n\n"
    
    # Add high APR pools section
    message += "📈 *High APR Pools*\n\n"
    
    for i, pool in enumerate(sorted_pools[:5], 1):
        # Extract token symbols
        token_a = pool.get("token_a", {}).get("symbol", "Unknown")
        token_b = pool.get("token_b", {}).get("symbol", "Unknown")
        
        # Extract APR, TVL, and prices
        apr = float(pool.get("apr", 0)) * 100  # Convert to percentage
        tvl = float(pool.get("tvl", 0))
        price_a = float(pool.get("token_a", {}).get("price", 0))
        price_b = float(pool.get("token_b", {}).get("price", 0))
        
        # Format the pool data
        message += (
            f"{i}. *{token_a}-{token_b}*\n"
            f"   • APR: *{apr:.2f}%*\n"
            f"   • TVL: ${tvl:,.2f}\n"
            f"   • Prices: {token_a} = ${price_a:.4f}, {token_b} = ${price_b:.4f}\n"
            f"   • Pool ID: `{pool.get('id', 'Unknown')}`\n\n"
        )
    
    # Add stable pools section
    message += "🔒 *Stable Pools*\n\n"
    
    stable_pools = [
        p for p in pool_data 
        if any(s in p.get("token_a", {}).get("symbol", "").upper() for s in ["USDC", "USDT"]) or 
           any(s in p.get("token_b", {}).get("symbol", "").upper() for s in ["USDC", "USDT"])
    ]
    
    for i, pool in enumerate(stable_pools[:3], 1):
        # Extract token symbols
        token_a = pool.get("token_a", {}).get("symbol", "Unknown")
        token_b = pool.get("token_b", {}).get("symbol", "Unknown")
        
        # Extract APR, TVL, and prices
        apr = float(pool.get("apr", 0)) * 100  # Convert to percentage
        tvl = float(pool.get("tvl", 0))
        price_a = float(pool.get("token_a", {}).get("price", 0))
        price_b = float(pool.get("token_b", {}).get("price", 0))
        
        # Format the pool data
        message += (
            f"{i}. *{token_a}-{token_b}*\n"
            f"   • APR: *{apr:.2f}%*\n"
            f"   • TVL: ${tvl:,.2f}\n"
            f"   • Prices: {token_a} = ${price_a:.4f}, {token_b} = ${price_b:.4f}\n"
            f"   • Pool ID: `{pool.get('id', 'Unknown')}`\n\n"
        )
    
    message += (
        "Use /simulate <amount> to calculate potential returns.\n"
        "Subscribe for daily updates with /subscribe."
    )
    
    return message

def format_simulation_results(results: Dict[str, Any], il_risk: Dict[str, Any], amount: float) -> str:
    """
    Format simulation results into a readable markdown message.
    
    Args:
        results: Dictionary of simulation results
        il_risk: Dictionary of impermanent loss risk data
        amount: Investment amount
        
    Returns:
        Formatted markdown string
    """
    message = f"💰 *Investment Simulation: ${amount:,.2f}* 💰\n\n"
    
    # Add pool information
    pool = results.get("pool", {})
    token_a = pool.get("token_a", {}).get("symbol", "Unknown")
    token_b = pool.get("token_b", {}).get("symbol", "Unknown")
    
    message += (
        f"📊 *Pool: {token_a}-{token_b}*\n"
        f"• APR: *{float(pool.get('apr', 0)) * 100:.2f}%*\n"
        f"• TVL: ${float(pool.get('tvl', 0)):,.2f}\n"
        f"• Fees: {float(pool.get('fee', 0)) * 100:.2f}%\n\n"
    )
    
    # Add projected returns
    daily_return = results.get("daily_return", 0)
    weekly_return = results.get("weekly_return", 0)
    monthly_return = results.get("monthly_return", 0)
    yearly_return = results.get("yearly_return", 0)
    
    message += (
        f"📈 *Projected Returns*\n"
        f"• Daily: ${daily_return:.2f}\n"
        f"• Weekly: ${weekly_return:.2f}\n"
        f"• Monthly: ${monthly_return:.2f}\n"
        f"• Yearly: ${yearly_return:.2f}\n\n"
    )
    
    # Add impermanent loss risk
    il_low = il_risk.get("low", 0) * 100
    il_medium = il_risk.get("medium", 0) * 100
    il_high = il_risk.get("high", 0) * 100
    
    message += (
        f"⚠️ *Impermanent Loss Risk*\n"
        f"• Low volatility (±5%): *{il_low:.2f}%*\n"
        f"• Medium volatility (±15%): *{il_medium:.2f}%*\n"
        f"• High volatility (±30%): *{il_high:.2f}%*\n\n"
    )
    
    # Add explanation and disclaimer
    message += (
        "💡 *Note:* These projections are based on current APR and assume constant rates, which may change.\n\n"
        "*Disclaimer:* This is a simulation only and not financial advice. "
        "Actual returns may vary due to market conditions, impermanent loss, and other factors."
    )
    
    return message

def calculate_returns(pool_data: List[Dict[str, Any]], amount: float) -> Dict[str, Any]:
    """
    Calculate expected returns based on investment amount and pool data.
    
    Args:
        pool_data: List of pool data dictionaries
        amount: Investment amount
        
    Returns:
        Dictionary with calculated returns
    """
    # Use the highest APR pool if available
    if not pool_data:
        return {
            "pool": {},
            "daily_return": 0,
            "weekly_return": 0,
            "monthly_return": 0,
            "yearly_return": 0
        }
    
    # Sort by APR (descending) and take the highest
    sorted_pools = sorted(pool_data, key=lambda x: float(x.get("apr", 0)), reverse=True)
    pool = sorted_pools[0]
    
    # Calculate returns
    apr = float(pool.get("apr", 0))
    fee = float(pool.get("fee", 0.003))  # Default to 0.3% if not specified
    
    # Yearly return (APR * amount)
    yearly_return = amount * apr
    
    # Monthly return (yearly / 12)
    monthly_return = yearly_return / 12
    
    # Weekly return (yearly / 52)
    weekly_return = yearly_return / 52
    
    # Daily return (yearly / 365)
    daily_return = yearly_return / 365
    
    return {
        "pool": pool,
        "daily_return": daily_return,
        "weekly_return": weekly_return,
        "monthly_return": monthly_return,
        "yearly_return": yearly_return
    }

def calculate_impermanent_loss(pool_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate impermanent loss risk for different volatility scenarios.
    
    Args:
        pool_data: List of pool data dictionaries
        
    Returns:
        Dictionary with impermanent loss percentages for different scenarios
    """
    # Use the same pool as in calculate_returns for consistency
    if not pool_data:
        return {
            "low": 0,
            "medium": 0,
            "high": 0
        }
    
    # Sort by APR (descending) and take the highest
    sorted_pools = sorted(pool_data, key=lambda x: float(x.get("apr", 0)), reverse=True)
    pool = sorted_pools[0]
    
    # Calculate impermanent loss for different price ratio changes
    # Formula: IL = 2 * sqrt(price_ratio) / (1 + price_ratio) - 1
    
    # Low volatility scenario (±5% price change)
    il_low = 2 * (1.05**0.5) / (1 + 1.05) - 1
    
    # Medium volatility scenario (±15% price change)
    il_medium = 2 * (1.15**0.5) / (1 + 1.15) - 1
    
    # High volatility scenario (±30% price change)
    il_high = 2 * (1.3**0.5) / (1 + 1.3) - 1
    
    return {
        "low": abs(il_low),
        "medium": abs(il_medium),
        "high": abs(il_high)
    }
