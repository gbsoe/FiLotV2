#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Predefined responses for the Telegram cryptocurrency pool bot
"""

import re
from typing import Optional, Dict, List, Pattern

# Dictionary of predefined responses
PREDEFINED_RESPONSES: Dict[str, str] = {
    "hello": "👋 Hello! How can I help you with cryptocurrency pools today?",
    "hi": "👋 Hi there! Looking for crypto pool information?",
    "help": "Need help? Use /help to see all available commands.",
    "thanks": "You're welcome! Let me know if you need anything else.",
    "thank you": "You're welcome! Happy to help with your crypto questions.",
    "bye": "Goodbye! Come back anytime for more crypto pool information.",
    
    # Crypto-specific queries
    "what is apr": "APR (Annual Percentage Rate) represents the yearly interest rate earned on an investment, excluding the effects of compounding.",
    "what is apy": "APY (Annual Percentage Yield) represents the yearly interest rate earned on an investment, including the effects of compounding.",
    "what is impermanent loss": "Impermanent loss occurs when the price ratio of tokens in a liquidity pool changes compared to when you deposited them. The more prices diverge, the more impermanent loss you experience.",
    "what is tvl": "TVL (Total Value Locked) is the total value of cryptocurrency assets deposited in a DeFi protocol or platform.",
    "what is raydium": "Raydium is a decentralized exchange (DEX) built on the Solana blockchain that provides automated market making (AMM) services and liquidity pools.",
    
    # Pool-related queries
    "best pools": "To see the current best performing pools, use the /info command. This will show you pools with the highest APR.",
    "stable pools": "Stable pools typically involve stablecoin pairs like USDC-USDT or stablecoin-SOL pairs. These usually have lower APR but also lower risk.",
    "high apr pools": "High APR pools can offer greater returns but often come with higher risk. Use /info to see current high APR pools.",
    
    # Investment-related queries
    "investment strategy": "A common strategy is to balance high-APR pools with stable pools to manage risk. Use /simulate to calculate potential returns.",
    "how to invest": "To invest in Raydium pools, you need a Solana wallet with SOL and the tokens you want to provide. Connect your wallet to Raydium's website to deposit liquidity.",
    "risk management": "Manage risk by diversifying across different pools, monitoring price action, and understanding impermanent loss potential for each pool.",
}

# Regex patterns for more flexible matching
REGEX_PATTERNS: List[tuple[Pattern, str]] = [
    (re.compile(r'\b(hi|hello|hey)\b', re.IGNORECASE), "👋 Hello! How can I help you with cryptocurrency pools today?"),
    (re.compile(r'\b(thanks|thank you|thx)\b', re.IGNORECASE), "You're welcome! Let me know if you need anything else."),
    (re.compile(r'\b(bye|goodbye|see you)\b', re.IGNORECASE), "Goodbye! Come back anytime for more crypto pool information."),
    
    # APR/APY questions
    (re.compile(r'\b(what is|explain|tell me about)\s+(apr)\b', re.IGNORECASE), 
     "APR (Annual Percentage Rate) represents the yearly interest rate earned on an investment, excluding the effects of compounding."),
    (re.compile(r'\b(what is|explain|tell me about)\s+(apy)\b', re.IGNORECASE), 
     "APY (Annual Percentage Yield) represents the yearly interest rate earned on an investment, including the effects of compounding."),
    
    # Pool questions
    (re.compile(r'\b(best|top|highest)\s+(pools|pool|apr|yield)\b', re.IGNORECASE), 
     "To see the current best performing pools, use the /info command. This will show you pools with the highest APR."),
    (re.compile(r'\b(stable|safe|low risk)\s+(pools|pool)\b', re.IGNORECASE), 
     "Stable pools typically involve stablecoin pairs like USDC-USDT or stablecoin-SOL pairs. These usually have lower APR but also lower risk."),
    
    # Impermanent loss
    (re.compile(r'\b(impermanent loss|IL)\b', re.IGNORECASE), 
     "Impermanent loss occurs when the price ratio of tokens in a liquidity pool changes compared to when you deposited them. The more prices diverge, the more impermanent loss you experience."),
    
    # Investment questions
    (re.compile(r'\b(how to|how do I)\s+(invest|start|begin)\b', re.IGNORECASE), 
     "To invest in Raydium pools, you need a Solana wallet with SOL and the tokens you want to provide. Connect your wallet to Raydium's website to deposit liquidity."),
    (re.compile(r'\b(risk|risks|risky)\b', re.IGNORECASE), 
     "The main risks in liquidity pools include impermanent loss, smart contract vulnerabilities, and token price volatility. To manage risk, diversify your investments and monitor market conditions."),
]

def get_predefined_response(message: str) -> Optional[str]:
    """
    Check if there's a predefined response for the given message.
    
    Args:
        message: User's message text
        
    Returns:
        Predefined response if found, None otherwise
    """
    # First try exact matches
    message_lower = message.lower()
    if message_lower in PREDEFINED_RESPONSES:
        return PREDEFINED_RESPONSES[message_lower]
    
    # Then try regex patterns
    for pattern, response in REGEX_PATTERNS:
        if pattern.search(message):
            return response
    
    # No match found
    return None
