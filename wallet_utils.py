"""
Wallet integration utilities for the Telegram cryptocurrency pool bot
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, Union, Tuple
import json
import base64
import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Define token mints (SOL is native, others are SPL tokens)
TOKEN_MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R"
}

# RPC endpoint
RPC_ENDPOINT = os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# For our simulation, define:
# - Optimal ratio for a SOL-USDC pool: 1 SOL should be paired with 120 USDC.
# - A simulated conversion rate: 1 SOL = 133 USDC.
OPTIMAL_USDC_PER_SOL = 120.0
SIMULATED_CONVERSION_RATE = 133.0  # USDC received per SOL swapped (after fees, slippage, etc.)

#########################
# Wallet Address Validation
#########################

def validate_wallet_address(wallet_address: str) -> bool:
    """
    Validate that the provided string is a valid Solana wallet address.
    
    Args:
        wallet_address: The wallet address to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Simple validation: Solana addresses are 44 characters, base58 encoded
        if not wallet_address or len(wallet_address) != 44:
            return False
            
        # Attempt to decode as base58 (this is a simple check, not full validation)
        # In production, use a proper Solana library
        allowed_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        return all(c in allowed_chars for c in wallet_address)
    except Exception as e:
        logger.error(f"Error validating wallet address {wallet_address}: {e}")
        return False

def connect_wallet(wallet_address: str) -> str:
    """
    "Connect" the wallet by verifying the address.
    (In production, signing and secure connection would be handled externally.)
    
    Args:
        wallet_address: The wallet address to connect
        
    Returns:
        The wallet address if valid
        
    Raises:
        ValueError: If wallet address is invalid
    """
    if validate_wallet_address(wallet_address):
        logger.info(f"Wallet {wallet_address} validated and connected")
        return wallet_address
    else:
        raise ValueError("Invalid wallet address")

#########################
# Balance Checking
#########################

async def _fetch_json_rpc(method: str, params: list) -> Dict[str, Any]:
    """
    Make a JSON-RPC request to the Solana RPC endpoint.
    
    Args:
        method: RPC method name
        params: List of parameters for the method
        
    Returns:
        JSON response from the RPC endpoint
    """
    async with aiohttp.ClientSession() as session:
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params
            }
            
            headers = {"Content-Type": "application/json"}
            
            async with session.post(RPC_ENDPOINT, json=payload, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Error from RPC endpoint: {response.status}")
                    return {}
                    
                resp_data = await response.json()
                if "error" in resp_data:
                    logger.error(f"RPC error: {resp_data['error']}")
                    return {}
                
                return resp_data.get("result", {})
        except Exception as e:
            logger.error(f"Error making RPC request: {e}")
            return {}

async def get_sol_balance(wallet_address: str) -> float:
    """
    Fetch the SOL balance (in SOL) for the given wallet address.
    
    Args:
        wallet_address: The wallet address to check
        
    Returns:
        SOL balance as a float
    """
    try:
        resp = await _fetch_json_rpc("getBalance", [wallet_address])
        if resp and "value" in resp:
            # Convert lamports to SOL (1 SOL = 10^9 lamports)
            sol_balance = resp["value"] / 1_000_000_000
            logger.info(f"Wallet {wallet_address} SOL balance: {sol_balance}")
            return sol_balance
        return 0.0
    except Exception as e:
        logger.error(f"Error fetching SOL balance: {e}")
        return 0.0

async def get_token_balance(wallet_address: str, token_mint: str) -> float:
    """
    Fetch the SPL token balance for a given token mint.
    
    Args:
        wallet_address: The wallet address to check
        token_mint: The token mint address
        
    Returns:
        Token balance as a float
    """
    try:
        # Proper implementation would use Solana's RPC to get actual token balances
        # For testing purposes, we will return 0 as the actual balance
        # In production, you would use getTokenAccountsByOwner RPC method
        
        # Uncomment for testing with real balance lookup:
        # method = "getTokenAccountsByOwner"
        # params = [
        #     wallet_address,
        #     {"mint": token_mint},
        #     {"encoding": "jsonParsed"}
        # ]
        # resp = await _fetch_json_rpc(method, params)
        
        balance = 0.0  # Return actual zero balance instead of a random value
        logger.info(f"Token balance for {wallet_address}, token {token_mint}: {balance}")
        return balance
    except Exception as e:
        logger.error(f"Error fetching token balance: {e}")
        return 0.0

async def check_wallet_balance(wallet_address: str) -> Dict[str, Any]:
    """
    Check and return the wallet's balance for SOL and key tokens.
    
    Args:
        wallet_address: The wallet address to check
        
    Returns:
        Dictionary of token symbols to balances or error message
    """
    if not validate_wallet_address(wallet_address):
        logger.error(f"Invalid wallet address: {wallet_address}")
        return {"error": "Invalid wallet address"}
        
    balances = {"SOL": await get_sol_balance(wallet_address)}
    
    # Get token balances
    for token, mint in TOKEN_MINTS.items():
        if token != "SOL":
            balances[token] = await get_token_balance(wallet_address, mint)
            
    return balances

#########################
# Swap & Deposit Calculation
#########################

def simulate_swap(sol_amount: float) -> float:
    """
    Simulate swapping a given SOL amount for USDC using a fixed conversion rate.
    
    Args:
        sol_amount: Amount of SOL to swap
        
    Returns:
        USDC received
    """
    usdc_received = sol_amount * SIMULATED_CONVERSION_RATE
    logger.info(f"Simulated swap: {sol_amount} SOL -> {usdc_received} USDC")
    return usdc_received

async def calculate_deposit_strategy(
    wallet_address: str, 
    optimal_ratio: float = OPTIMAL_USDC_PER_SOL, 
    conversion_rate: float = SIMULATED_CONVERSION_RATE
) -> Dict[str, Any]:
    """
    Calculate two deposit strategies for a SOL-USDC pool.
    
    Args:
        wallet_address: The wallet address to use
        optimal_ratio: Optimal USDC:SOL ratio (default: OPTIMAL_USDC_PER_SOL)
        conversion_rate: SOL to USDC conversion rate (default: SIMULATED_CONVERSION_RATE)
        
    Returns:
        Dictionary with auto_swap and partial_deposit strategies
    """
    balances = await check_wallet_balance(wallet_address)
    
    if "error" in balances:
        return {"error": balances["error"]}
        
    sol_balance = balances.get("SOL", 0.0)
    usdc_balance = balances.get("USDC", 0.0)
    
    # Optimal USDC required if all SOL is to be deposited
    optimal_required_usdc = sol_balance * optimal_ratio
    strategy = {}
    
    if usdc_balance >= optimal_required_usdc:
        # The user already has sufficient USDC for their entire SOL balance
        strategy["auto_swap"] = {
            "swap_sol": 0.0,
            "post_swap_sol": sol_balance,
            "post_swap_usdc": usdc_balance
        }
        strategy["partial_deposit"] = {
            "deposit_sol": sol_balance,
            "deposit_usdc": optimal_required_usdc
        }
    else:
        # Calculate shortfall in USDC
        usdc_shortfall = optimal_required_usdc - usdc_balance
        # Amount of SOL required to swap to cover the shortfall
        swap_sol = usdc_shortfall / conversion_rate
        # Ensure we don't swap more than available SOL
        swap_sol = min(swap_sol, sol_balance)
        
        strategy["auto_swap"] = {
            "swap_sol": swap_sol,
            "post_swap_sol": sol_balance - swap_sol,
            "post_swap_usdc": usdc_balance + simulate_swap(swap_sol)
        }
        
        # For partial deposit: reduce SOL deposit so that existing USDC fully pairs
        deposit_sol = usdc_balance / optimal_ratio
        strategy["partial_deposit"] = {
            "deposit_sol": deposit_sol,
            "deposit_usdc": usdc_balance
        }
    
    logger.info(f"Calculated deposit strategy for {wallet_address}: {strategy}")
    return strategy

#########################
# Transaction Simulation
#########################

def join_pool_transaction(
    wallet_address: str,
    pool_id: str,
    token_a: str,
    token_b: str,
    deposit_sol: float,
    deposit_usdc: float
) -> bool:
    """
    Simulate joining a liquidity pool.
    
    Args:
        wallet_address: The wallet address to use
        pool_id: ID of the pool to join
        token_a: First token symbol
        token_b: Second token symbol
        deposit_sol: Amount of SOL to deposit
        deposit_usdc: Amount of USDC to deposit
        
    Returns:
        True if successful (simulated)
    """
    try:
        logger.info(f"Simulating join pool transaction for wallet {wallet_address} on pool {pool_id}")
        logger.info(f"Depositing {deposit_sol} {token_a} and {deposit_usdc} {token_b}")
        # In a real implementation, this would build and send a transaction
        return True
    except Exception as e:
        logger.error(f"Error simulating join pool transaction: {e}")
        return False

def stop_pool_transaction(wallet_address: str, pool_id: str) -> bool:
    """
    Simulate exiting a liquidity pool.
    
    Args:
        wallet_address: The wallet address to use
        pool_id: ID of the pool to exit
        
    Returns:
        True if successful (simulated)
    """
    try:
        logger.info(f"Simulating stop pool transaction for wallet {wallet_address} on pool {pool_id}")
        # In a real implementation, this would build and send a transaction
        return True
    except Exception as e:
        logger.error(f"Error simulating stop pool transaction: {e}")
        return False

# This function can be used to format wallet balance information for the Telegram bot
def format_wallet_info(balances: Dict[str, Any]) -> str:
    """
    Format wallet balance information for display in Telegram messages.
    
    Args:
        balances: Dictionary of token symbols to balances or error message
        
    Returns:
        Formatted string
    """
    if "error" in balances:
        return f"❌ Error: {balances['error']}"
        
    # Header
    result = "💼 *Wallet Balance* 💼\n\n"
    
    # Format balances
    for token, balance in balances.items():
        if token == "SOL":
            result += f"• SOL: *{balance:.4f}* (≈${balance * 133:.2f})\n"
        elif token == "USDC" or token == "USDT":
            result += f"• {token}: *{balance:.2f}*\n"
        else:
            result += f"• {token}: *{balance:.4f}*\n"
    
    # Add footer with information on how to use the balance
    result += "\n💡 Use /simulate to see potential earnings with these tokens in liquidity pools."
    
    return result