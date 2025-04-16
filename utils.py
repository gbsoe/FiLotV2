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
    
    # Header
    result = "🏊‍♂️ *Top Liquidity Pools Today* 🏊‍♂️\n\n"
    
    # Add pool information
    for i, pool in enumerate(pools):
        token_pair = f"{pool.token_a_symbol}/{pool.token_b_symbol}"
        
        # Format APR with emoji indicators
        apr_24h = pool.apr_24h
        apr_emoji = "🔥" if apr_24h > 50 else "💰" if apr_24h > 20 else "💸"
        
        # Format TVL with appropriate prefix
        tvl = pool.tvl
        if tvl >= 1_000_000:
            tvl_formatted = f"${tvl/1_000_000:.1f}M"
        else:
            tvl_formatted = f"${tvl/1_000:.1f}K"
        
        # Add entry
        result += (
            f"{i+1}. *{token_pair}* {apr_emoji}\n"
            f"   • APR: *{apr_24h:.2f}%* (24h)\n"
            f"   • TVL: *{tvl_formatted}*\n"
            f"   • Fee: {pool.fee*100:.2f}%\n\n"
        )
    
    # Add footer with explanation and call-to-action
    result += (
        "ℹ️ APR = Annual Percentage Rate, the yearly return on investment.\n"
        "ℹ️ TVL = Total Value Locked, the total amount of assets in the pool.\n\n"
        "💡 To simulate potential earnings, use /simulate [amount]"
    )
    
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
    
    # Header
    result = f"💰 *Investment Simulation: ${amount:,.2f}* 💰\n\n"
    
    # Add pool simulation information
    for i, pool in enumerate(pools):
        token_pair = f"{pool.token_a_symbol}/{pool.token_b_symbol}"
        
        # Calculate potential earnings
        apr_24h = pool.apr_24h
        daily_rate = apr_24h / 365
        
        # Calculate earnings for different time periods
        daily_earnings = amount * (daily_rate / 100)
        weekly_earnings = daily_earnings * 7
        monthly_earnings = daily_earnings * 30
        yearly_earnings = amount * (apr_24h / 100)
        
        # Add entry
        result += (
            f"{i+1}. *{token_pair}* (APR: {apr_24h:.2f}%)\n"
            f"   • Daily: *${daily_earnings:.2f}*\n"
            f"   • Weekly: *${weekly_earnings:.2f}*\n"
            f"   • Monthly: *${monthly_earnings:.2f}*\n"
            f"   • Yearly: *${yearly_earnings:.2f}*\n\n"
        )
    
    # Compare with traditional bank
    bank_apr = 0.01  # 1% annual interest rate
    bank_yearly = amount * bank_apr
    bank_monthly = bank_yearly / 12
    top_pool = pools[0]
    top_monthly = amount * (top_pool.apr_24h / 100) / 12
    
    diff_multiplier = top_monthly / max(bank_monthly, 0.01)  # Avoid division by zero
    
    result += (
        "💼 *Comparison with Traditional Bank*\n"
        f"Traditional bank (1% APY): *${bank_monthly:.2f}/month*\n"
        f"Top liquidity pool: *${top_monthly:.2f}/month*\n"
        f"That's *{diff_multiplier:.1f}x more* with FiLot! 🚀\n\n"
        "ℹ️ Note: Higher returns come with higher risks. The APR is variable and based on current market conditions.\n\n"
        "💡 View available pools with /info"
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