"""
Utility functions for the Telegram cryptocurrency pool bot
"""

import math
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

def format_pool_info(pools: List[Dict[str, Any]]) -> str:
    """
    Format pool information for display in Telegram messages.
    
    Args:
        pools: List of pool dictionaries from API or response_data
        
    Returns:
        Formatted string
    """
    if not pools:
        return "No pools available at the moment. Please try again later."
        
    result = "📈 Latest Crypto Investment Update:\n\n"
    result += "Best Performing Investments Today:\n"
    
    for pool in pools:
        result += f"• Pool ID: 📋 {pool.get('id', 'Unknown')}\n"
        result += f"  Token Pair: {pool.get('pairName', 'Unknown')}\n"
        result += f"  24h APR: {pool.get('apr', '0.00')}%\n"
        result += f"  7d APR: {pool.get('aprWeekly', '0.00')}%\n"
        result += f"  30d APR: {pool.get('aprMonthly', '0.00')}%\n"
        result += f"  TVL (USD): ${float(pool.get('liquidity', 0)):,.2f}\n"
        
        # Get base token from pair name
        base_token = pool.get('pairName', '/').split('/')[0] if '/' in pool.get('pairName', '') else ''
        result += f"  Current Price (USD): ${float(pool.get('price', 0)):,.2f} per {base_token}\n\n"
    
    result += "Top Stable Investments (e.g., SOL-USDC / SOL-USDT):\n\n"
    result += "Want to see your potential earnings? Try /simulate amount (default is $1000)."
    
    return result
    
    # Helper function to safely get dictionary values
    def get_value(pool, key, default=0):
        # Handle the different key names in our response_data vs. API
        value_map = {
            'apr_24h': ['apr', 'apr_24h'],
            'apr_7d': ['aprWeekly', 'apr_7d'],
            'apr_30d': ['aprMonthly', 'apr_30d'],
            'tvl': ['liquidity', 'tvl'],
            'id': ['id'],
            'token_a_symbol': [],
            'token_b_symbol': []
        }
        
        # For token symbols, extract from pairName if available
        if key in ['token_a_symbol', 'token_b_symbol']:
            pair_name = pool.get('pairName', '')
            if '/' in pair_name:
                token_a, token_b = pair_name.split('/')
                return token_a if key == 'token_a_symbol' else token_b
            return ''
            
        # Try all possible keys
        for possible_key in value_map.get(key, [key]):
            if possible_key in pool:
                return pool[possible_key]
                
        return default
        
    # Helper function to get token price
    def get_token_price(pool, token_symbol):
        if 'tokenPrices' in pool and token_symbol in pool['tokenPrices']:
            return pool['tokenPrices'][token_symbol]
        return 0
    
    # Exactly 2 pools for Best Performing Investments Today:
    # 1. Highest 24h APR
    # 2. Highest TVL
    pools_by_apr = sorted(pools, key=lambda p: get_value(p, 'apr_24h'), reverse=True)
    pools_by_tvl = sorted(pools, key=lambda p: get_value(p, 'tvl'), reverse=True)
    
    top_apr_pool = pools_by_apr[0] if pools_by_apr else None
    top_tvl_pool = pools_by_tvl[0] if pools_by_tvl else None
    
    # Make sure we have 2 different pools (if possible)
    top_pools = []
    if top_apr_pool:
        top_pools.append(top_apr_pool)
    if top_tvl_pool and get_value(top_tvl_pool, 'id') != get_value(top_apr_pool, 'id', None):
        top_pools.append(top_tvl_pool)
    elif len(pools_by_apr) > 1:
        # If top APR and TVL are the same pool, get the second highest APR
        top_pools.append(pools_by_apr[1])
    
    # Find stable pools (SOL/USDC, SOL/RAY, etc.)
    stable_tokens = ["USDC", "USDT", "RAY"]
    stable_pools = []
    
    for pool in pools:
        pair_name = pool.get('pairName', '')
        if any(stable in pair_name for stable in stable_tokens):
            stable_pools.append(pool)
    
    # Sort stable pools by APR and take top 3
    stable_pools = sorted(stable_pools, key=lambda p: get_value(p, 'apr_24h'), reverse=True)[:3]
    
    # Header
    result = "📈 Latest Crypto Investment Update:\n\n"
    
    # Best Performing Investments Today section
    result += "Best Performing Investments Today:\n"
    for pool in top_pools:
        token_a = get_value(pool, 'token_a_symbol')
        token_b = get_value(pool, 'token_b_symbol')
        token_pair = f"{token_a}/{token_b}"
        token_a_price = get_token_price(pool, token_a)
        
        result += (
            f"• Pool ID: 📋 {get_value(pool, 'id')}\n"
            f"  Token Pair: {token_pair}\n"
            f"  24h APR: {get_value(pool, 'apr_24h'):.2f}%\n"
            f"  7d APR: {get_value(pool, 'apr_7d'):.2f}%\n"
            f"  30d APR: {get_value(pool, 'apr_30d'):.2f}%\n"
            f"  TVL (USD): ${get_value(pool, 'tvl'):,.2f}\n"
            f"  Current Price (USD): ${token_a_price} per {token_a}\n"
        )
        result += "\n"
    
    # Top Stable Investments section
    result += "Top Stable Investments (e.g., SOL-USDC / SOL-USDT):\n"
    for pool in stable_pools:
        token_a = get_value(pool, 'token_a_symbol')
        token_b = get_value(pool, 'token_b_symbol')
        token_pair = f"{token_a}/{token_b}"
        token_a_price = get_token_price(pool, token_a)
        
        result += (
            f"• Pool ID: 📋 {get_value(pool, 'id')}\n"
            f"  Token Pair: {token_pair}\n"
            f"  24h APR: {get_value(pool, 'apr_24h'):.2f}%\n"
            f"  7d APR: {get_value(pool, 'apr_7d'):.2f}%\n"
            f"  30d APR: {get_value(pool, 'apr_30d'):.2f}%\n"
            f"  TVL (USD): ${get_value(pool, 'tvl'):,.2f}\n"
            f"  Current Price (USD): ${token_a_price} per {token_a}\n"
        )
        result += "\n"
    
    result += "\nWant to see your potential earnings? Try /simulate amount (default is $1000)."
    
    return result

def format_simulation_results(pools: List[Dict[str, Any]], amount: float) -> str:
    """
    Format investment simulation results for display in Telegram messages.
    
    Args:
        pools: List of pool dictionaries
        amount: Investment amount in USD
        
    Returns:
        Formatted string showing potential earnings for top pools
    """
    if not pools:
        return "No pools available for simulation. Please try again later."
    
    # Helper function to safely get dictionary values
    def get_value(pool, key, default=0):
        # Handle the different key names in our response_data vs. API
        value_map = {
            'apr_24h': ['apr', 'apr_24h'],
            'apr_7d': ['aprWeekly', 'apr_7d'],
            'apr_30d': ['aprMonthly', 'apr_30d'],
            'tvl': ['liquidity', 'tvl'],
            'id': ['id'],
            'token_a_symbol': [],
            'token_b_symbol': []
        }
        
        # For token symbols, extract from pairName if available
        if key in ['token_a_symbol', 'token_b_symbol']:
            pair_name = pool.get('pairName', '')
            if '/' in pair_name:
                token_a, token_b = pair_name.split('/')
                return token_a if key == 'token_a_symbol' else token_b
            return ''
            
        # Try all possible keys
        for possible_key in value_map.get(key, [key]):
            if possible_key in pool:
                return pool[possible_key]
                
        return default
    
    # Sort pools by APR (24h) for better display
    sorted_pools = sorted(pools, key=lambda p: get_value(p, 'apr_24h'), reverse=True)
    
    # Limit to top 3 pools to avoid overly long messages
    display_pools = sorted_pools[:3]
    
    if not display_pools:
        return "No pools available for simulation. Please try again later."
    
    # Header
    result = f"🚀 Simulation for an Investment of ${amount:,.2f}:\n\n"
    
    # Generate simulations for each pool
    for pool in display_pools:
        # Calculate potential earnings
        apr_24h = get_value(pool, 'apr_24h')
        daily_rate = apr_24h / 365
        
        # Calculate earnings for different time periods
        daily_earnings = amount * (daily_rate / 100)
        weekly_earnings = daily_earnings * 7
        monthly_earnings = daily_earnings * 30
        yearly_earnings = amount * (apr_24h / 100)
        
        # Token pair and pool ID
        token_a = get_value(pool, 'token_a_symbol')
        token_b = get_value(pool, 'token_b_symbol')
        token_pair = f"{token_a}/{token_b}"
        
        # Format each pool's simulation results
        result += (
            f"• Pool ID: 📋 {get_value(pool, 'id')}\n"
            f"  Token Pair: {token_pair}\n"
            f"  - Daily Earnings: ${daily_earnings:.2f}\n"
            f"  - Weekly Earnings: ${weekly_earnings:.2f}\n"
            f"  - Monthly Earnings: ${monthly_earnings:.2f}\n"
            f"  - Annual Earnings: ${yearly_earnings:.2f}\n"
            f"\n"
        )
    
    # Add disclaimer
    result += "Disclaimer: The numbers above are estimations and actual earnings may vary."
    
    return result

def format_daily_update(pools: List[Dict[str, Any]]) -> str:
    """
    Format daily update message for subscribed users.
    
    Args:
        pools: List of pool dictionaries
        
    Returns:
        Formatted string
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Header
    result = f"📊 Daily Pool Update - {today} 📊\n\n"
    
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