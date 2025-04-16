#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for the Telegram cryptocurrency pool bot
"""

from typing import List, Dict, Any, Optional
import datetime
from models import Pool

def format_pool_info(pools: List[Pool]) -> str:
    """
    Format pool information for display.
    
    Args:
        pools: List of Pool objects
        
    Returns:
        Formatted string for display
    """
    if not pools:
        return "No pool data available."
    
    message = "🔥 *Top Cryptocurrency Pools by APR*\n\n"
    
    for i, pool in enumerate(pools, 1):
        message += (
            f"*{i}. {pool.token_a_symbol}/{pool.token_b_symbol}*\n"
            f"   • APR: *{pool.apr_24h:.2f}%* (24h) / {pool.apr_7d:.2f}% (7d) / {pool.apr_30d:.2f}% (30d)\n"
            f"   • TVL: *${pool.tvl:,.2f}*\n"
            f"   • Prices: {pool.token_a_symbol}: ${pool.token_a_price:.4f}, {pool.token_b_symbol}: ${pool.token_b_price:.4f}\n"
            f"   • Fee: {pool.fee * 100:.2f}%\n\n"
        )
    
    message += "Use /simulate <amount> to see potential earnings for these pools."
    
    return message

def format_simulation_results(pools: List[Pool], amount: float) -> str:
    """
    Format investment simulation results.
    
    Args:
        pools: List of Pool objects
        amount: Investment amount
        
    Returns:
        Formatted simulation results
    """
    if not pools:
        return "No pool data available for simulation."
    
    message = f"💰 *Investment Simulation: ${amount:,.2f}*\n\n"
    
    for i, pool in enumerate(pools, 1):
        # Calculate daily, weekly, monthly, and yearly earnings
        daily_earnings = amount * (pool.apr_24h / 100 / 365)
        weekly_earnings = daily_earnings * 7
        monthly_earnings = daily_earnings * 30
        yearly_earnings = amount * (pool.apr_24h / 100)
        
        message += (
            f"*{i}. {pool.token_a_symbol}/{pool.token_b_symbol}* (APR: {pool.apr_24h:.2f}%)\n"
            f"   • Daily: *${daily_earnings:.2f}*\n"
            f"   • Weekly: *${weekly_earnings:.2f}*\n"
            f"   • Monthly: *${monthly_earnings:.2f}*\n"
            f"   • Yearly: *${yearly_earnings:.2f}*\n\n"
        )
    
    message += (
        "⚠️ *Disclaimer*: These are estimates based on current APR rates. "
        "Actual returns may vary due to market conditions, impermanent loss, and other factors."
    )
    
    return message

def format_timestamp(timestamp: datetime.datetime) -> str:
    """
    Format a timestamp for display.
    
    Args:
        timestamp: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    now = datetime.datetime.utcnow()
    diff = now - timestamp
    
    if diff.days == 0:
        # Today
        if diff.seconds < 60:
            return "just now"
        elif diff.seconds < 3600:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.days == 1:
        # Yesterday
        return "yesterday"
    elif diff.days < 7:
        # This week
        return f"{diff.days} days ago"
    else:
        # Older
        return timestamp.strftime("%Y-%m-%d")

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

def escape_markdown(text: str) -> str:
    """
    Escape Markdown special characters.
    
    Args:
        text: Text to escape
        
    Returns:
        Escaped text
    """
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)