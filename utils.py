"""
Utility functions for the Telegram cryptocurrency pool bot
"""

import math
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

def format_pool_info(pools: List) -> str:
    """
    Format pool information for display in Telegram messages.
    
    Args:
        pools: List of Pool objects
        
    Returns:
        Formatted string
    """
    if not pools:
        return "No pools available at the moment. Please try again later."
    
    # Sort pools by APR (24h) and TVL
    pools_by_apr = sorted(pools, key=lambda p: p.apr_24h or 0, reverse=True)
    pools_by_tvl = sorted(pools, key=lambda p: p.tvl or 0, reverse=True)
    
    # Get unique top pools (by APR and TVL) for "Best Performing" section (limit to 2)
    top_pools = []
    if pools_by_apr:
        top_pools.append(pools_by_apr[0])  # Top by APR
    if pools_by_tvl and pools_by_tvl[0] not in top_pools:
        top_pools.append(pools_by_tvl[0])  # Top by TVL
    
    top_pools = top_pools[:2]  # Limit to 2 pools
    
    # Find stable pools (containing USDC, USDT, or similar)
    stable_tokens = ["USDC", "USDT", "RAY"]
    stable_pools = []
    
    for pool in pools:
        token_a = pool.token_a_symbol or ""
        token_b = pool.token_b_symbol or ""
        
        if any(stable in token_a or stable in token_b for stable in stable_tokens):
            stable_pools.append(pool)
    
    # Sort stable pools by APR and take top 3
    stable_pools = sorted(stable_pools, key=lambda p: p.apr_24h or 0, reverse=True)[:3]
    
    # Header
    result = "📈 *Latest Crypto Investment Update:*\n\n"
    
    # Best Performing Investments Today section
    result += "*Best Performing Investments Today:*\n"
    for pool in top_pools:
        token_pair = f"{pool.token_a_symbol}/{pool.token_b_symbol}"
        token_a_price = pool.token_a_price or 0
        
        result += (
            f"• Pool ID: 📋 {pool.id}\n"
            f"  Token Pair: {token_pair}\n"
            f"  24h APR: {pool.apr_24h:.2f}%\n"
            f"  7d APR: {pool.apr_7d:.2f}%\n"
            f"  30d APR: {pool.apr_30d:.2f}%\n"
            f"  TVL (USD): ${pool.tvl:,.2f}\n"
            f"  Current Price (USD): ${token_a_price:.1f} per {pool.token_a_symbol}\n\n"
        )
    
    # Top Stable Investments section
    result += "*Top Stable Investments (e.g., SOL-USDC / SOL-USDT):*\n"
    for pool in stable_pools:
        token_pair = f"{pool.token_a_symbol}/{pool.token_b_symbol}"
        token_a_price = pool.token_a_price or 0
        
        result += (
            f"• Pool ID: 📋 {pool.id}\n"
            f"  Token Pair: {token_pair}\n"
            f"  24h APR: {pool.apr_24h:.2f}%\n"
            f"  7d APR: {pool.apr_7d:.2f}%\n"
            f"  30d APR: {pool.apr_30d:.2f}%\n"
            f"  TVL (USD): ${pool.tvl:,.2f}\n"
            f"  Current Price (USD): ${token_a_price:.1f} per {pool.token_a_symbol}\n\n"
        )
    
    # Footer
    result += "\nWant to see your potential earnings? Try /simulate amount (default is $1000)."
    
    return result

def format_simulation_results(pools: List, amount: float) -> str:
    """
    Format investment simulation results for display in Telegram messages.
    
    Args:
        pools: List of Pool objects
        amount: Investment amount in USD
        
    Returns:
        Formatted string
    """
    if not pools:
        return "No pools available for simulation. Please try again later."
    
    # Sort pools by APR (24h) to get top pool for simulation
    top_pool = sorted(pools, key=lambda p: p.apr_24h or 0, reverse=True)[0] if pools else None
    
    if not top_pool:
        return "No pools available for simulation. Please try again later."
    
    # Header
    result = f"🚀 *Simulation for an Investment of ${amount:,.2f}:*\n\n"
    
    # Calculate potential earnings
    apr_24h = top_pool.apr_24h
    daily_rate = apr_24h / 365
    
    # Calculate earnings for different time periods
    daily_earnings = amount * (daily_rate / 100)
    weekly_earnings = daily_earnings * 7
    monthly_earnings = daily_earnings * 30
    yearly_earnings = amount * (apr_24h / 100)
    
    # Token pair and pool ID
    token_pair = f"{top_pool.token_a_symbol}/{top_pool.token_b_symbol}"
    
    # Format the simulation result
    result += (
        f"• Pool ID: 📋 {top_pool.id} - {token_pair}\n"
        f"  - Daily Earnings: ${daily_earnings:.2f}\n"
        f"  - Weekly Earnings: ${weekly_earnings:.2f}\n"
        f"  - Monthly Earnings: ${monthly_earnings:.2f}\n"
        f"  - Annual Earnings: ${yearly_earnings:.2f}\n"
    )
    
    return result

def format_daily_update(pools: List) -> str:
    """
    Format daily update message for subscribed users.
    
    Args:
        pools: List of Pool objects
        
    Returns:
        Formatted string
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Header
    result = f"📊 *Daily Pool Update - {today}* 📊\n\n"
    
    # Add pool information
    result += format_pool_info(pools)
    
    # Add footer
    result += (
        "\n\n📱 Stay updated with FiLot!\n"
        "Use /subscribe to receive daily updates.\n"
        "Use /unsubscribe to stop receiving updates."
    )
    
    return result

def format_number(value: float, decimals: int = 2) -> str:
    """Format a number with thousands separator."""
    return f"{value:,.{decimals}f}"

def format_currency(value: float, decimals: int = 2) -> str:
    """Format a currency value."""
    return f"${format_number(value, decimals)}"