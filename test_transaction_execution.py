"""
Test script to verify transaction execution functionality.
"""

import asyncio
import json
import logging
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
from transactions import (
    prepare_swap_transaction,
    prepare_add_liquidity_transaction,
    prepare_remove_liquidity_transaction,
    simulate_transaction,
    approve_transaction,
    execute_transaction,
    get_transaction_status
)

async def test_transaction_execution():
    """Test the entire transaction execution flow from preparation to execution."""
    
    # Test wallet address (for demonstration only)
    test_user_id = 123456
    test_wallet_address = "5r1RVMHxP2iyTZxYJEGq9U1HWyX7YEGqhzAY98NSNSp3"
    
    logger.info("======================================================")
    logger.info("TESTING SWAP TRANSACTION")
    logger.info("======================================================")
    
    # 1. Prepare a swap transaction
    logger.info("1. Preparing swap transaction...")
    swap_result = await prepare_swap_transaction(
        user_id=test_user_id,
        wallet_address=test_wallet_address,
        amount=1.0,  # 1 SOL
        from_token="SOL",
        to_token="USDC"
    )
    
    if not swap_result["success"]:
        logger.error(f"Failed to prepare swap transaction: {swap_result['error']}")
        return
    
    swap_tx_id = swap_result["transaction_id"]
    logger.info(f"Swap transaction prepared: {swap_tx_id}")
    
    # 2. Simulate the transaction
    logger.info("2. Simulating swap transaction...")
    sim_result = await simulate_transaction(swap_tx_id)
    
    if not sim_result["success"]:
        logger.error(f"Simulation failed: {sim_result['error']}")
        return
    
    logger.info(f"Simulation successful: {json.dumps(sim_result, indent=2)}")
    
    # 3. Approve the transaction
    logger.info("3. Approving swap transaction...")
    approval_result = await approve_transaction(swap_tx_id, test_user_id)
    
    if not approval_result["success"]:
        logger.error(f"Approval failed: {approval_result['error']}")
        return
    
    logger.info(f"Transaction approved: {json.dumps(approval_result, indent=2)}")
    
    # 4. Execute the transaction
    logger.info("4. Executing swap transaction...")
    execution_result = await execute_transaction(swap_tx_id)
    
    if not execution_result["success"]:
        logger.error(f"Execution failed: {execution_result['error']}")
    else:
        logger.info(f"Execution successful: {json.dumps(execution_result, indent=2)}")
    
    # 5. Check transaction status
    logger.info("5. Checking transaction status...")
    status_result = await get_transaction_status(swap_tx_id)
    logger.info(f"Final transaction status: {json.dumps(status_result, indent=2)}")
    
    logger.info("======================================================")
    logger.info("TESTING ADD LIQUIDITY TRANSACTION")
    logger.info("======================================================")
    
    # 1. Prepare an add liquidity transaction
    logger.info("1. Preparing add liquidity transaction...")
    liquidity_result = await prepare_add_liquidity_transaction(
        user_id=test_user_id,
        wallet_address=test_wallet_address,
        amount=100.0,  # $100
        token_a="SOL",
        token_b="USDC",
        pool_id="sol_usdc_pool_1"
    )
    
    if not liquidity_result["success"]:
        logger.error(f"Failed to prepare add liquidity transaction: {liquidity_result['error']}")
        return
    
    liquidity_tx_id = liquidity_result["transaction_id"]
    logger.info(f"Add liquidity transaction prepared: {liquidity_tx_id}")
    
    # 2. Simulate the transaction
    logger.info("2. Simulating add liquidity transaction...")
    sim_result = await simulate_transaction(liquidity_tx_id)
    
    if not sim_result["success"]:
        logger.error(f"Simulation failed: {sim_result['error']}")
        return
    
    logger.info(f"Simulation successful: {json.dumps(sim_result, indent=2)}")
    
    # 3. Approve the transaction
    logger.info("3. Approving add liquidity transaction...")
    approval_result = await approve_transaction(liquidity_tx_id, test_user_id)
    
    if not approval_result["success"]:
        logger.error(f"Approval failed: {approval_result['error']}")
        return
    
    logger.info(f"Transaction approved: {json.dumps(approval_result, indent=2)}")
    
    # 4. Execute the transaction
    logger.info("4. Executing add liquidity transaction...")
    execution_result = await execute_transaction(liquidity_tx_id)
    
    if not execution_result["success"]:
        logger.error(f"Execution failed: {execution_result['error']}")
    else:
        logger.info(f"Execution successful: {json.dumps(execution_result, indent=2)}")
    
    # 5. Check transaction status
    logger.info("5. Checking transaction status...")
    status_result = await get_transaction_status(liquidity_tx_id)
    logger.info(f"Final transaction status: {json.dumps(status_result, indent=2)}")
    
    # Close client
    await close_client()
    logger.info("Test complete")

if __name__ == "__main__":
    # Run test if module is executed directly
    asyncio.run(test_transaction_execution())