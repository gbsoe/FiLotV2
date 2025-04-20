"""
Predefined response data for the Telegram bot with real pool data and CoinGecko prices
"""

import logging
import random
from typing import Dict, List, Any, Optional
import coingecko_utils

# Configure logging
logger = logging.getLogger(__name__)

# Real Raydium pool IDs (based on user-provided example)
REAL_POOL_IDS = [
    "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv",  # SOL/USDC
    "2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2",  # SOL/RAY
    "CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq",  # SOL/USDC (another pool)
    "Ar1owSzR5L6LXBYm7kJsEU9vHzCpexGZY6nqfuh1WjG5",  # ETH/USDC
    "HQ8oeaHofBJyM8DMhCD5YasRXjqT3cGjcCHcVNnYEGS1"   # SOL/USDT
]

# Token pair mapping for each pool
POOL_TOKEN_PAIRS = {
    "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv": ("SOL", "USDC"),
    "2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2": ("SOL", "RAY"),
    "CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq": ("SOL", "USDC"),
    "Ar1owSzR5L6LXBYm7kJsEU9vHzCpexGZY6nqfuh1WjG5": ("ETH", "USDC"),
    "HQ8oeaHofBJyM8DMhCD5YasRXjqT3cGjcCHcVNnYEGS1": ("SOL", "USDT")
}

# Realistic APR and TVL ranges for different pool types
APR_RANGES = {
    "SOL/USDC": (30.0, 150.0),
    "SOL/RAY": (40.0, 80.0),
    "SOL/USDT": (25.0, 55.0),
    "ETH/USDC": (15.0, 35.0),
    "RAY/USDC": (50.0, 100.0),
    "default": (10.0, 30.0)
}

TVL_RANGES = {
    "SOL/USDC": (5_000_000, 12_000_000),
    "SOL/RAY": (2_000_000, 5_000_000),
    "SOL/USDT": (1_500_000, 3_000_000),
    "ETH/USDC": (4_000_000, 8_000_000),
    "RAY/USDC": (1_000_000, 2_500_000),
    "default": (500_000, 1_500_000)
}

def get_pool_data():
    """
    Get predefined pool data.
    """
    try:
        # Create pool data based on real Raydium pools (updated from screenshot)
        pools_data = {
            "bestPerformance": [
                {
                    "id": "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv",
                    "pairName": "SOL/USDC",
                    "baseMint": "So11111111111111111111111111111111111111112",
                    "quoteMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "apr": "48.67",  # Updated based on screenshot
                    "aprWeekly": "47.46",  # Trade fees from screenshot
                    "aprMonthly": "45.25",
                    "liquidity": "9308852",  # Updated TVL from screenshot
                    "price": "139.75",
                    "volume24h": "30262011",  # From screenshot
                    "volume7d": "9277943.99"
                },
                {
                    "id": "2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2",
                    "pairName": "SOL/RAY",
                    "baseMint": "So11111111111111111111111111111111111111112",
                    "quoteMint": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
                    "apr": "38.50",  # Updated to realistic value
                    "aprWeekly": "37.28",
                    "aprMonthly": "36.12",
                    "liquidity": "3678901.23",
                    "price": "139.75",
                    "volume24h": "823456.78",
                    "volume7d": "3654321.09"
                }
            ],
            "topStable": [
                {
                    "id": "CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq",
                    "pairName": "USDC/USDT",
                    "baseMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                    "quoteMint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                    "apr": "8.20",  # Updated to more realistic value
                    "aprWeekly": "7.98",
                    "aprMonthly": "7.12",
                    "liquidity": "45678901.23",
                    "price": "1.00",
                    "volume24h": "12345678.00",
                    "volume7d": "76543210.99"
                }
            ],
            # Add topAPR as an alias to bestPerformance for backward compatibility
            "topAPR": []
        }
        
        # Copy bestPerformance pools to topAPR for backward compatibility
        pools_data["topAPR"] = pools_data["bestPerformance"]

        # Get token prices from CoinGecko for the tokens in our pools
        token_symbols = set()
        for pool in pools_data["bestPerformance"] + pools_data["topStable"] + pools_data["topAPR"]:
            if "/" in pool["pairName"]:
                token_a, token_b = pool["pairName"].split("/")
                token_symbols.add(token_a)
                token_symbols.add(token_b)

        # Get token prices
        token_prices = coingecko_utils.get_multiple_token_prices(list(token_symbols))
        logger.info(f"Fetched token prices: {token_prices}")

        # Update pool data with token prices for all arrays
        for pool in pools_data["bestPerformance"] + pools_data["topStable"] + pools_data["topAPR"]:
            if "/" in pool["pairName"]:
                token_a, token_b = pool["pairName"].split("/")
                pool["tokenPrices"] = {
                    token_a: token_prices.get(token_a, 0),
                    token_b: token_prices.get(token_b, 0)
                }
        return pools_data
    except Exception as e:
        logger.error(f"Error fetching pool data: {e}")
        # Return empty data structure with all necessary keys for backward compatibility
        return {
            "bestPerformance": [], 
            "topStable": [],
            "topAPR": []
        }

def get_predefined_responses():
    """
    Return a dictionary of detailed predefined responses with canonical keys.
    The text has been updated to fix encoding issues.
    """
    # Import our fixed responses
    from fixed_responses import get_fixed_responses
    return get_fixed_responses()

# Legacy dictionary - no longer used
def get_legacy_responses():
    """Legacy responses - kept for reference but not used anymore"""
    return {
        # --- Detailed Product Information ---
        "what is filot": (
            "*FiLot* is a next-generation, AI-powered investment assistant that revolutionizes crypto investing. "
            "It provides real-time liquidity pool data, personalized investment strategies, and risk analysis for "
            "DeFi platforms, with a primary focus on Raydium's liquidity pools on the Solana blockchain."
        ),

        "what is la token": (
            "*LA Token* is the native governance and utility token of the FiLot ecosystem. LA Token holders can "
            "participate in governance decisions, access premium features, and receive fee discounts. The token "
            "maintains a deflationary model with regular burns from fees collected across the platform."
        ),

        "what is the roadmap": (
            "*FiLot Roadmap:*\n"
            "Q2 2025: Launch beta version with basic pool tracking\n"
            "Q3 2025: Full release with AI-powered investment recommendations\n"
            "Q4 2025: Advanced risk analysis and portfolio management\n"
            "Q1 2026: Cross-chain integration and expanded DeFi coverage\n"
            "Q2 2026: Mobile app launch and premium subscription features"
        ),

        # --- How-to Guides ---
        "how to use filot": (
            "To use FiLot:\n"
            "1. Start with /start command\n"
            "2. Use /info to view top-performing pools\n"
            "3. Try /simulate 1000 to see potential returns for $1000\n"
            "4. Connect your wallet with /wallet or /walletconnect\n"
            "5. Set your risk profile with /profile\n"
            "6. Ask me anything about crypto investments!"
        ),

        "what can i ask": (
            "You can ask me about:\n"
            "• Current liquidity pool performance and APRs\n"
            "• Investment recommendations based on your risk profile\n"
            "• Explanations of DeFi concepts like impermanent loss\n"
            "• Token price predictions and market analysis\n"
            "• Risk assessment for specific investments\n"
            "• How to optimize your DeFi strategy"
        ),

        # --- Educational Content ---
        "what is liquidity pool": (
            "A *liquidity pool* is a collection of cryptocurrency tokens locked in a smart contract that facilitates "
            "trading, lending, and other DeFi activities. Liquidity providers (LPs) deposit equal values of two tokens "
            "to create trading pairs (like SOL/USDC). In return, LPs earn fees from trades executed against that pool "
            "and often additional rewards in the form of APR/APY."
        ),

        "what is apr": (
            "*APR* (Annual Percentage Rate) represents the yearly interest generated by an investment, not accounting "
            "for compounding. In DeFi, APR typically comes from trading fees and token rewards. For example, a 100% APR "
            "means your investment would theoretically double in a year if rates remained stable. However, DeFi APRs "
            "fluctuate based on trading volume, token prices, and market conditions."
        ),

        "impermanent loss": (
            "*Impermanent loss* occurs when the price ratio of tokens in a liquidity pool changes compared to when you "
            "deposited them. If you had simply held the tokens instead of providing liquidity, you might have more value. "
            "The loss is 'impermanent' because it can decrease or disappear if token prices return to the original ratio. "
            "Higher volatility between token pairs leads to greater impermanent loss risk."
        ),

        "risk assessment": (
            "FiLot assesses investment risk through multiple factors:\n"
            "• Volatility: How much token prices fluctuate\n"
            "• Pool TVL: Higher liquidity generally means lower risk\n"
            "• Smart contract security: Based on audit status and history\n"
            "• Impermanent loss potential: Higher in volatile token pairs\n"
            "• Protocol reputation: Established protocols typically present lower risk\n"
            "Risk is categorized as Low, Medium, or High for each investment opportunity."
        ),

        # --- User Features ---
        "wallet integration": (
            "FiLot offers two ways to connect your crypto wallet:\n"
            "1. Direct connection: Use /wallet to register your address\n"
            "2. WalletConnect: Use /walletconnect for QR code connection\n"
            "Connected wallets allow for real-time portfolio tracking, one-click investments, and personalized analytics "
            "based on your actual holdings. All connections use secure, read-only access by default."
        ),

        "risk profiles": (
            "FiLot offers three risk profiles:\n"
            "• Conservative: Focuses on stable pairs (USDC/USDT, major assets) with lower but consistent returns\n"
            "• Moderate: Balanced approach with established tokens and medium volatility\n"
            "• Aggressive: Higher-risk pools with emerging tokens and potentially higher rewards\n"
            "Set your preferred risk profile with /profile to get personalized recommendations."
        )
    }

def get_predefined_response(query: str) -> Optional[str]:
    """
    Get a predefined response for a query.

    Args:
        query: User's query text

    Returns:
        Predefined response or None if no match is found
    """
    if not query:
        return None

    query_lower = query.lower().strip()

    # Log the query for debugging
    import logging
    logger = logging.getLogger("question_detector")
    logger.info(f"Processing potential question: '{query_lower}'")

    # Get all responses
    responses = get_predefined_responses()

    # Define variations for each canonical query (extended with more variations)
    variations = {
        "what is filot": [
            "what is filot", "tell me about filot", "who is filot", "filot info", "explain filot", 
            "what's filot", "what filot is", "filot description", "describe filot"
        ],
        "what is la token": [
            "la token", "tell me about la", "la info", "what's la", "la token info", 
            "what is la", "what is the la token", "tell me about the la token", "la"
        ],
        "what is the roadmap": [
            "roadmap", "future plans", "development timeline", "upcoming features",
            "what is the roadmap", "project timeline", "milestones", "roadmap info"
        ],
        "how to use filot": [
            "how to use", "how to start", "getting started", "begin with filot", "tutorial",
            "how do i use filot", "user guide", "instructions", "how filot works"
        ],
        "what can i ask": [
            "what can you do", "what questions", "capabilities", "features", "what can i do",
            "what can filot do", "what filot can do", "what to ask", "functions", "skills", "abilities"
        ],
        "what is liquidity pool": [
            "liquidity pool", "what are pools", "explain pools", "lp", "what is lp",
            "defi pools", "liquidity", "pool explanation", "pools work"
        ],
        "what is apr": [
            "apr", "annual percentage rate", "interest rate", "returns", "yield",
            "what does apr mean", "explain apr", "how apr works", "apr calculation"
        ],
        "impermanent loss": [
            "il", "explain impermanent loss", "what is impermanent loss", 
            "tell me about impermanent loss", "il explanation", "impermanent"
        ],
        "risk assessment": [
            "risk analysis", "how do you assess risk", "risk evaluation", "risk metrics",
            "how risks are calculated", "risk factors", "risk measurement"
        ],
        "wallet integration": [
            "connect wallet", "wallet", "how to connect wallet", "walletconnect",
            "wallet connection", "linking wallet", "wallet setup", "wallet support"
        ],
        "risk profiles": [
            "investment profiles", "risk levels", "risk types", "risk preferences",
            "investor profiles", "risk tolerance", "risk settings"
        ]
    }

    # Check for single-word queries using key terms (extended)
    key_terms = {
        'la': 'what is la token',
        'filot': 'what is filot',
        'token': 'what is la token',
        'roadmap': 'what is the roadmap',
        'apr': 'what is apr',
        'pools': 'what is liquidity pool',
        'pool': 'what is liquidity pool',
        'wallet': 'wallet integration',
        'impermanent': 'impermanent loss',
        'risk': 'risk assessment',
        'features': 'what can i ask',
    }
    if query_lower in key_terms:
        logger.info(f"Matched single keyword: {query_lower} → {key_terms[query_lower]}")
        return responses.get(key_terms[query_lower])

    # Check for exact matches
    if query_lower in responses:
        logger.info(f"Matched exact response key: {query_lower}")
        return responses[query_lower]

    # Check in variations (exact match)
    for canonical, variant_list in variations.items():
        if query_lower in variant_list:
            logger.info(f"Matched exact variation: {query_lower} → {canonical}")
            return responses.get(canonical)

    # Check for substring matches in variations
    for canonical, variant_list in variations.items():
        for variant in variant_list:
            if variant in query_lower:
                logger.info(f"Matched variation as substring: {variant} in '{query_lower}' → {canonical}")
                return responses.get(canonical)
            elif query_lower in variant:
                logger.info(f"Matched query as substring of variation: '{query_lower}' in {variant} → {canonical}")
                return responses.get(canonical)

    # Check for keyword combinations (extended)
    keyword_combinations = {
        ('how', 'start'): 'how to use filot',
        ('how', 'use'): 'how to use filot',
        ('what', 'pool'): 'what is liquidity pool',
        ('what', 'apr'): 'what is apr',
        ('what', 'yield'): 'what is apr',
        ('what', 'return'): 'what is apr',
        ('impermanent', 'loss'): 'impermanent loss',
        ('who', 'you'): 'what is filot',
        ('what', 'ask'): 'what can i ask',
        ('what', 'questions'): 'what can i ask',
        ('what', 'do'): 'what can i ask',
        ('connect', 'wallet'): 'wallet integration',
        ('risk', 'profile'): 'risk profiles',
        ('risk', 'assess'): 'risk assessment',
        ('road', 'map'): 'what is the roadmap',
        ('token', 'la'): 'what is la token',
    }
    for keywords, response_key in keyword_combinations.items():
        if all(keyword in query_lower for keyword in keywords):
            logger.info(f"Matched keyword combination: {keywords} → {response_key}")
            return responses.get(response_key)

    # Word similarity check (for typos and slight variations)
    import difflib

    # Create a flat list of all variations
    all_variations = []
    for canonical, variants in variations.items():
        for variant in variants:
            all_variations.append((variant, canonical))

    # Find closest matching variation using sequence matcher
    best_match = None
    best_ratio = 0.8  # Minimum threshold for a match

    for variant, canonical in all_variations:
        ratio = difflib.SequenceMatcher(None, query_lower, variant).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = canonical

    if best_match:
        logger.info(f"Matched by similarity ({best_ratio:.2f}): '{query_lower}' → {best_match}")
        return responses.get(best_match)

    # Fallback: return None if no match is found
    logger.info(f"No match found for: '{query_lower}'")
    return None

# Example usage (for testing purposes)
if __name__ == "__main__":
    sample_queries = [
        "What is FiLot?",
        "Tell me about LA!",
        "How do I start investing?",
        "Explain impermanent loss"
    ]
    for q in sample_queries:
        print("Query:", q)
        print("Response:", get_predefined_response(q))
        print("-" * 50)