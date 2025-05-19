"""
Utility functions for the Telegram cryptocurrency pool bot
"""

import math
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

def format_pool_info(pools: List[Dict[str, Any]], stable_pools: Optional[List[Dict[str, Any]]] = None, show_title: Optional[str] = None) -> str:
    """
    Format pool information for display in Telegram messages.

    Args:
        pools: List of pool dictionaries from API or response_data
        stable_pools: List of stable pool dictionaries (optional)
        show_title: Optional custom title for the displayed pools

    Returns:
        Formatted string
    """
    if not pools and not stable_pools:
        return "No pools available at the moment. Please try again later."
    
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
                try:
                    # Return the value as is for string values, convert to float for numeric values
                    val = pool[possible_key]
                    if key in ['apr_24h', 'apr_7d', 'apr_30d', 'tvl'] and isinstance(val, str):
                        return float(val)
                    return val
                except (ValueError, TypeError):
                    pass  # If conversion fails, try next key
                
        return default

    # Helper function to get token price
    def get_token_price(pool, token_symbol):
        if 'tokenPrices' in pool and token_symbol in pool['tokenPrices']:
            try:
                return float(pool['tokenPrices'][token_symbol])
            except (ValueError, TypeError):
                return 0
        return 0

    # Use provided stable_pools if given, otherwise find stable pools
    if stable_pools is None:
        # Find stable pools (SOL/USDC, SOL/RAY, etc.)
        stable_tokens = ["USDC", "USDT", "RAY"]
        stable_pools = []

        for pool in pools:
            pair_name = pool.get('pairName', '')
            if any(stable in pair_name for stable in stable_tokens):
                stable_pools.append(pool)

    # Always use the provided pools (should be 2 best performance pools):
    # 1. Highest 24h APR
    # 2. Highest TVL
    try:
        # Make sure we have exactly 2 different pools for the best performing section
        if len(pools) > 2:
            # If there are more than 2 pools, pick the 2 with highest APR
            top_pools = sorted(pools, key=lambda p: float(get_value(p, 'apr_24h')), reverse=True)[:2]
        else:
            # Otherwise use all provided pools
            top_pools = pools
    except (ValueError, IndexError):
        # Fallback if sorting fails
        top_pools = pools[:2] if len(pools) >= 2 else pools

    # Always use all provided stable pools (should be 3 stable pools)
    try:
        # Sort stable pools by APR 
        if stable_pools:
            stable_pools = sorted(stable_pools, key=lambda p: float(get_value(p, 'apr_24h')), reverse=True)
    except ValueError:
        # Fallback if sorting fails - just use the provided stable pools
        pass

    # Header with custom title if provided
    if show_title:
        result = f"📈 {show_title}:\n\n"
    else:
        result = "📈 Latest Crypto Investment Update:\n\n"

    # Best Performing Investments section (only if we have regular pools)
    if pools:
        result += "Best Performing Investments Today:\n"
    for pool in top_pools:
        try:
            token_a = get_value(pool, 'token_a_symbol')
            token_b = get_value(pool, 'token_b_symbol')
            token_pair = f"{token_a}/{token_b}"
            
            # Parse numeric values safely
            pool_id = str(get_value(pool, 'id'))
            apr_24h = float(get_value(pool, 'apr_24h'))
            apr_7d = float(get_value(pool, 'apr_7d'))
            apr_30d = float(get_value(pool, 'apr_30d'))
            tvl = float(get_value(pool, 'tvl'))
            token_a_price = float(get_token_price(pool, token_a))
            
            # Build result string with safe values
            pool_info = (
                f"• Pool ID: 📋 {pool_id}\n"
                f"  Token Pair: {token_pair}\n"
                f"  24h APR: {apr_24h:.2f}%\n"
                f"  7d APR: {apr_7d:.2f}%\n"
                f"  30d APR: {apr_30d:.2f}%\n"
                f"  TVL (USD): ${tvl:,.2f}\n"
                f"  Current Price (USD): ${token_a_price:.2f} per {token_a}\n"
            )
            result += pool_info + "\n"
        except Exception as e:
            # Skip this pool if formatting fails
            continue

    # Top Stable Investments section (only if stable pools are available)
    if stable_pools:
        if pools:  # Only add section header if we have both pool types
            result += "\n\nTop Stable Investments (e.g., SOL-USDC / SOL-USDT):\n"
        else:  # If we're only showing stable pools, this is the primary section
            if show_title:  # Title already set above
                pass
            else:
                result += "Top Stable Investments (e.g., SOL-USDC / SOL-USDT):\n"
        for pool in stable_pools:
            try:
                token_a = get_value(pool, 'token_a_symbol')
                token_b = get_value(pool, 'token_b_symbol')
                token_pair = f"{token_a}/{token_b}"
                
                # Parse numeric values safely
                pool_id = str(get_value(pool, 'id'))
                apr_24h = float(get_value(pool, 'apr_24h'))
                apr_7d = float(get_value(pool, 'apr_7d'))
                apr_30d = float(get_value(pool, 'apr_30d'))
                tvl = float(get_value(pool, 'tvl'))
                token_a_price = float(get_token_price(pool, token_a))
                
                # Build result string with safe values
                pool_info = (
                    f"• Pool ID: 📋 {pool_id}\n"
                    f"  Token Pair: {token_pair}\n"
                    f"  24h APR: {apr_24h:.2f}%\n"
                    f"  7d APR: {apr_7d:.2f}%\n"
                    f"  30d APR: {apr_30d:.2f}%\n"
                    f"  TVL (USD): ${tvl:,.2f}\n"
                    f"  Current Price (USD): ${token_a_price:.2f} per {token_a}\n"
                )
                result += pool_info + "\n"
            except Exception as e:
                # Skip this pool if formatting fails
                continue
    else:
        result += "No stable pool data available at the moment.\n\n"

    # Add footer with appropriate guidance based on what was shown
    if pools:
        result += "\n\nWant to see your potential earnings? Use the '🔮 Simulate Investment' button or type /simulate [amount]."
    else:
        result += "\n\nExplore more options using the buttons below or return to the main menu."
        
    # Add a reminder about the One-Command interface
    result += "\n\nUse the persistent buttons for easy navigation through all features."

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
                try:
                    # Return the value as is for string values, convert to float for numeric values
                    val = pool[possible_key]
                    if key in ['apr_24h', 'apr_7d', 'apr_30d', 'tvl'] and isinstance(val, str):
                        return float(val)
                    return val
                except (ValueError, TypeError):
                    pass  # If conversion fails, try next key

        return default

    try:
        # Sort pools by APR (24h) for better display
        sorted_pools = sorted(pools, key=lambda p: float(get_value(p, 'apr_24h')), reverse=True)

        # Use all pools provided for simulation (should be 2 best performance pools)
        display_pools = sorted_pools
    except (ValueError, TypeError):
        # Fallback if sorting fails
        display_pools = pools

    if not display_pools:
        return "No pools available for simulation. Please try again later."

    # Header
    result = f"🚀 Simulation for an Investment of ${amount:,.2f}:\n\n"

    # Generate simulations for each pool
    for pool in display_pools:
        try:
            # Parse numeric values safely
            pool_id = str(get_value(pool, 'id'))
            apr_24h = float(get_value(pool, 'apr_24h'))
            
            # Calculate rates and earnings
            daily_rate = apr_24h / 365
            daily_earnings = amount * (daily_rate / 100)
            weekly_earnings = daily_earnings * 7
            monthly_earnings = daily_earnings * 30
            yearly_earnings = amount * (apr_24h / 100)

            # Get token information
            token_a = get_value(pool, 'token_a_symbol')
            token_b = get_value(pool, 'token_b_symbol')
            token_pair = f"{token_a}/{token_b}"

            # Format each pool's simulation results
            pool_info = (
                f"• Pool ID: 📋 {pool_id}\n"
                f"  Token Pair: {token_pair}\n"
                f"  - Daily Earnings: ${daily_earnings:.2f}\n"
                f"  - Weekly Earnings: ${weekly_earnings:.2f}\n"
                f"  - Monthly Earnings: ${monthly_earnings:.2f}\n"
                f"  - Annual Earnings: ${yearly_earnings:.2f}\n"
                f"\n"
            )
            result += pool_info
        except Exception as e:
            # Skip this pool if calculation fails
            continue

    # Add disclaimer and helpful guidance
    result += "Disclaimer: The numbers above are estimations and actual earnings may vary.\n\n"
    result += "Want to compare different amounts? Use '/simulate [amount]' with your preferred investment amount.\n\n"
    result += "Use the buttons below to explore more options or continue your investment journey."

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