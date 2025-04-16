#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Predefined responses for commonly asked questions
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Union, Any

logger = logging.getLogger(__name__)

# Mapping of keywords to predefined responses
PREDEFINED_RESPONSES = {
    # General bot information
    "what can you do": (
        "I'm a cryptocurrency pool tracking bot specializing in Raydium pools. I can:\n\n"
        "• Show you the highest APR pools with /info\n"
        "• Simulate investment returns with /simulate\n"
        "• Subscribe you to daily updates with /subscribe\n"
        "• Answer questions about cryptocurrency pools and investments"
    ),
    
    "help": (
        "Here are the commands I understand:\n\n"
        "• /start - Start the bot\n"
        "• /help - Show this help message\n"
        "• /info - Get information about the best cryptocurrency pools\n"
        "• /simulate <amount> - Simulate investment returns with a specific amount\n"
        "• /subscribe - Subscribe to daily pool updates\n"
        "• /unsubscribe - Unsubscribe from daily updates\n"
        "• /status - Check bot status\n"
        "• /verify - Verify your account\n\n"
        "You can also ask me questions about cryptocurrency pools and investments!"
    ),
    
    # Investment and pools related
    "what is apr": (
        "APR (Annual Percentage Rate) is the yearly interest rate earned on an investment, expressed as a percentage.\n\n"
        "In cryptocurrency liquidity pools:\n"
        "• APR represents the expected yearly return from providing liquidity\n"
        "• It's calculated based on trading fees collected from the pool\n"
        "• Higher APR generally means higher returns, but often comes with higher risk\n"
        "• APR can fluctuate based on trading volume and market conditions\n\n"
        "Use /info to see current pool APRs and /simulate to estimate potential returns."
    ),
    
    "what is tvl": (
        "TVL (Total Value Locked) is the total value of all assets deposited in a protocol or pool, expressed in USD.\n\n"
        "Key TVL insights:\n"
        "• Higher TVL indicates more liquidity and often greater stability\n"
        "• Pools with higher TVL tend to have lower slippage for large trades\n"
        "• Lower TVL pools might offer higher APRs but with greater volatility\n"
        "• TVL is a key metric for assessing a pool's size and popularity\n\n"
        "You can see TVL for Raydium pools using the /info command."
    ),
    
    "what is impermanent loss": (
        "Impermanent Loss (IL) is a temporary loss of funds that liquidity providers experience when providing assets to a pool, compared to simply holding those assets.\n\n"
        "Key facts about impermanent loss:\n"
        "• It occurs when the price ratio of paired assets changes after you deposit them\n"
        "• The greater the price change, the larger the impermanent loss\n"
        "• It's called 'impermanent' because it only becomes permanent when you withdraw liquidity\n"
        "• Trading fees earned can offset impermanent loss\n"
        "• Stablecoin pairs have minimal impermanent loss risk\n\n"
        "Use /simulate to estimate potential returns including impermanent loss considerations."
    ),
    
    "what is raydium": (
        "Raydium is a decentralized exchange (DEX) and automated market maker (AMM) built on the Solana blockchain.\n\n"
        "Key features of Raydium:\n"
        "• Enables fast and low-cost trades with minimal slippage\n"
        "• Provides liquidity to Serum's order book while operating like traditional AMMs\n"
        "• Allows users to earn rewards by providing liquidity to pools\n"
        "• Offers yield farming opportunities through liquidity mining programs\n"
        "• Features lower fees compared to Ethereum-based exchanges\n\n"
        "Use /info to see current Raydium pool information."
    ),
    
    # How to invest/provide liquidity
    "how to provide liquidity": (
        "To provide liquidity on Raydium:\n\n"
        "1. Visit Raydium.io and connect your Solana wallet (like Phantom)\n"
        "2. Navigate to the 'Liquidity' section\n"
        "3. Select the token pair you want to provide liquidity for\n"
        "4. Enter the amount of tokens you want to deposit\n"
        "5. Approve the transaction in your wallet\n"
        "6. You'll receive LP tokens representing your share of the pool\n\n"
        "Tips:\n"
        "• Ensure you understand impermanent loss before investing\n"
        "• Consider starting with stablecoin pairs for lower risk\n"
        "• Check APRs and TVL using our /info command before investing"
    ),
    
    "best pools": (
        "The best pools to invest in depend on your risk tolerance and investment goals.\n\n"
        "Some factors to consider:\n"
        "• High APR pools offer better returns but may have higher risk\n"
        "• Higher TVL indicates more liquidity and often greater stability\n"
        "• Stablecoin pairs generally have lower impermanent loss risk\n"
        "• Volatile token pairs have higher impermanent loss risk\n\n"
        "To see current pools with the highest APR, use the /info command. To simulate potential returns, use /simulate <amount>."
    ),
    
    # Errors and troubleshooting
    "not working": (
        "I'm sorry you're experiencing issues. Here are some troubleshooting steps:\n\n"
        "1. Ensure you're using the correct command format (e.g., /simulate 1000)\n"
        "2. Try restarting the bot with /start\n"
        "3. Check your internet connection\n"
        "4. If you're still having issues, please try again later\n\n"
        "You can also use /status to check if there are any system issues."
    ),
    
    # Subscription related
    "subscription": (
        "My subscription service provides daily updates on the best performing cryptocurrency pools.\n\n"
        "Benefits:\n"
        "• Daily notification of top pools by APR\n"
        "• Updates on significant APR changes\n"
        "• Alerts for new high-performing pools\n\n"
        "Commands:\n"
        "• /subscribe - Start receiving daily updates\n"
        "• /unsubscribe - Stop receiving updates\n\n"
        "The subscription is completely free!"
    ),
}

# Define patterns for detecting question types
QUESTION_PATTERNS = {
    "apr_question": r"\b(what|how|explain|tell).+(apr|annual percentage|yearly.+rate)\b",
    "tvl_question": r"\b(what|how|explain|tell).+(tvl|total value locked|liquidity amount)\b",
    "impermanent_loss_question": r"\b(what|how|explain|tell).+(impermanent loss|IL)\b",
    "raydium_question": r"\b(what|who|explain|tell).+(raydium|ray)\b",
    "provide_liquidity_question": r"\b(how|guide|steps).+(provide|add|supply|deposit).+(liquidity)\b",
    "best_pools_question": r"\b(what|which|list|show).+(best|top|highest|profitable).+(pool|pair|liquidity)\b",
    "not_working_question": r"\b(not working|broken|error|issue|problem|bug|failed)\b",
    "subscription_question": r"\b(what|how|about).+(subscri|daily|update|alert|notification)\b",
    "help_question": r"\b(help|command|instruction|guide)\b",
    "bot_capabilities_question": r"\b(what.+(do|function)|function|capability|able to do)\b"
}

def get_response_for_question(question: str) -> Optional[str]:
    """
    Returns a predefined response for a question if available.
    
    Args:
        question: The user's question
        
    Returns:
        A predefined response if available, None otherwise
    """
    # Normalize the question
    normalized_question = question.lower().strip()
    
    # Direct keyword matching
    for keyword, response in PREDEFINED_RESPONSES.items():
        if keyword in normalized_question:
            logger.info(f"Found direct keyword match for: {keyword}")
            return response
    
    # Pattern matching
    for question_type, pattern in QUESTION_PATTERNS.items():
        if re.search(pattern, normalized_question, re.IGNORECASE):
            logger.info(f"Found pattern match for: {question_type}")
            
            # Map question types to response keywords
            response_mapping = {
                "apr_question": "what is apr",
                "tvl_question": "what is tvl",
                "impermanent_loss_question": "what is impermanent loss",
                "raydium_question": "what is raydium",
                "provide_liquidity_question": "how to provide liquidity",
                "best_pools_question": "best pools",
                "not_working_question": "not working",
                "subscription_question": "subscription",
                "help_question": "help",
                "bot_capabilities_question": "what can you do"
            }
            
            if question_type in response_mapping:
                return PREDEFINED_RESPONSES[response_mapping[question_type]]
    
    # No match found
    return None

# Additional specialized responses

def format_about_response() -> str:
    """Return formatted about information for the bot."""
    return (
        "🤖 *Crypto Pool Tracker Bot*\n\n"
        "I'm a specialized bot for tracking and providing information about cryptocurrency pools on Raydium.\n\n"
        "*Features:*\n"
        "• Real-time pool tracking with APR and TVL data\n"
        "• Investment simulation\n"
        "• Daily updates on the best performing pools\n"
        "• Security features including rate limiting and spam protection\n"
        "• AI-powered responses to your questions\n\n"
        "*Version:* 1.0.0\n"
        "*Created by:* Your team\n\n"
        "Use /help to see available commands."
    )

def format_start_response(is_new_user: bool = True) -> str:
    """Return formatted start message for the bot."""
    if is_new_user:
        return (
            "👋 *Welcome to the Crypto Pool Tracker Bot!*\n\n"
            "I can help you track cryptocurrency pools on Raydium and simulate investment returns.\n\n"
            "*Key commands:*\n"
            "/info - Get information about the best pools\n"
            "/simulate <amount> - Simulate investment returns\n"
            "/subscribe - Get daily updates on the best pools\n"
            "/help - Show all available commands\n\n"
            "You can also ask me questions about cryptocurrency pools and investments!"
        )
    else:
        return (
            "👋 *Welcome back to the Crypto Pool Tracker Bot!*\n\n"
            "Great to see you again! Here are some commands to get started:\n\n"
            "/info - See the latest pool information\n"
            "/simulate <amount> - Run a new investment simulation\n"
            "/help - View all available commands\n\n"
            "Is there anything specific you'd like to know today?"
        )

def format_no_match_response() -> str:
    """Return response for when no predefined answer is available."""
    return (
        "I don't have a predefined answer for that question. Let me help you with some related information:\n\n"
        "• For pool information, use /info\n"
        "• To simulate investment returns, use /simulate <amount>\n"
        "• For general help, use /help\n\n"
        "You can also try asking in a different way or using different keywords."
    )