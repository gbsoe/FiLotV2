"""
Test script to verify the wallet transaction execution functionality specifically.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import necessary modules
from solana_wallet_service import get_wallet_service, close_client

async def test_wallet_transaction_execution():
    """Test the wallet transaction execution functionality."""
    
    # Test wallet address (for demonstration only)
    wallet_address = "5r1RVMHxP2iyTZxYJEGq9U1HWyX7YEGqhzAY98NSNSp3"
    
    logger.info("======================================================")
    logger.info("TESTING WALLET TRANSACTION EXECUTION")
    logger.info("======================================================")
    
    # Get wallet service
    wallet_service = get_wallet_service()
    
    # Test swap transaction
    logger.info("1. Testing swap transaction execution...")
    swap_result = await wallet_service.execute_transaction({
        "type": "swap",
        "wallet_address": wallet_address,
        "amount": 1.0,
        "from_token": "SOL",
        "to_token": "USDC"
    })
    
    logger.info(f"Swap transaction result: {json.dumps(swap_result, indent=2)}")
    
    # Test add liquidity transaction
    logger.info("2. Testing add liquidity transaction execution...")
    add_liquidity_result = await wallet_service.execute_transaction({
        "type": "add_liquidity",
        "wallet_address": wallet_address,
        "amount": 100.0,
        "token_a": "SOL",
        "token_b": "USDC",
        "pool_id": "sol_usdc_pool_1"
    })
    
    logger.info(f"Add liquidity transaction result: {json.dumps(add_liquidity_result, indent=2)}")
    
    # Test remove liquidity transaction
    logger.info("3. Testing remove liquidity transaction execution...")
    remove_liquidity_result = await wallet_service.execute_transaction({
        "type": "remove_liquidity",
        "wallet_address": wallet_address,
        "pool_id": "sol_usdc_pool_1",
        "percentage": 50.0
    })
    
    logger.info(f"Remove liquidity transaction result: {json.dumps(remove_liquidity_result, indent=2)}")
    
    # Close client
    await close_client()
    logger.info("Test complete")

if __name__ == "__main__":
    # Run test
    asyncio.run(test_wallet_transaction_execution())