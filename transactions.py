"""
Transaction execution framework for FiLot bot.

This module provides functionality for:
1. Preparing investment transactions (liquidity provisioning)
2. Simulating transactions before execution
3. Executing transactions with user approval
4. Transaction history and status tracking
"""

import os
import time
import json
import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta

from solana_wallet_service import get_wallet_service
from raydium_client import get_client, calculate_optimal_swap_amount
from db_utils import get_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Transaction types
TRANSACTION_TYPE_SWAP = "swap"
TRANSACTION_TYPE_ADD_LIQUIDITY = "add_liquidity"
TRANSACTION_TYPE_REMOVE_LIQUIDITY = "remove_liquidity"

# Transaction statuses
TRANSACTION_STATUS_PENDING = "pending"
TRANSACTION_STATUS_SIMULATED = "simulated"
TRANSACTION_STATUS_APPROVED = "approved"
TRANSACTION_STATUS_REJECTED = "rejected"
TRANSACTION_STATUS_SUBMITTED = "submitted"
TRANSACTION_STATUS_CONFIRMED = "confirmed"
TRANSACTION_STATUS_FAILED = "failed"
TRANSACTION_STATUS_EXPIRED = "expired"

def init_transaction_tables():
    """Initialize database tables for transaction tracking."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create transactions table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(255) UNIQUE NOT NULL,
            user_id BIGINT NOT NULL,
            wallet_address VARCHAR(255) NOT NULL,
            transaction_type VARCHAR(50) NOT NULL,
            status VARCHAR(50) NOT NULL,
            amount NUMERIC(20, 8) NOT NULL,
            token_symbol VARCHAR(50) NOT NULL,
            target_symbol VARCHAR(50),
            pool_id VARCHAR(255),
            simulation_result JSONB,
            transaction_data JSONB,
            transaction_signature VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP
        )
        """)
        
        # Create transaction logs table for detailed history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_logs (
            id SERIAL PRIMARY KEY,
            transaction_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            log_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Transaction tables initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing transaction tables: {e}")
        return False

async def prepare_swap_transaction(
    user_id: int,
    wallet_address: str,
    amount: float,
    from_token: str,
    to_token: str
) -> Dict[str, Any]:
    """
    Prepare a swap transaction for execution.
    
    Args:
        user_id: Telegram user ID
        wallet_address: User's wallet address
        amount: Amount to swap
        from_token: Token to swap from
        to_token: Token to swap to
        
    Returns:
        Dict with transaction details
    """
    try:
        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Get client for Raydium API
        raydium_client = get_client()
        
        # Get the best route for the swap
        route_result = await raydium_client.get_swap_route(
            from_token=from_token,
            to_token=to_token,
            amount=amount
        )
        
        if not route_result.get("success", False):
            logger.error(f"Error getting swap route: {route_result.get('error')}")
            return {
                "success": False,
                "error": f"Could not find a route to swap {from_token} to {to_token}. {route_result.get('error')}"
            }
        
        # Create transaction data
        transaction_data = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "wallet_address": wallet_address,
            "transaction_type": TRANSACTION_TYPE_SWAP,
            "status": TRANSACTION_STATUS_PENDING,
            "amount": amount,
            "token_symbol": from_token,
            "target_symbol": to_token,
            "route": route_result.get("route"),
            "expected_output": route_result.get("expectedOutput"),
            "price_impact": route_result.get("priceImpact"),
            "minimum_received": route_result.get("minimumReceived"),
            "fee": route_result.get("fee")
        }
        
        # Store transaction in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO transactions 
        (transaction_id, user_id, wallet_address, transaction_type, status, amount, token_symbol, target_symbol, transaction_data, created_at, updated_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (
            transaction_id,
            user_id,
            wallet_address,
            TRANSACTION_TYPE_SWAP,
            TRANSACTION_STATUS_PENDING,
            amount,
            from_token,
            to_token,
            json.dumps(transaction_data),
            datetime.now(),
            datetime.now(),
            datetime.now() + timedelta(minutes=30)  # Transaction expires in 30 minutes
        ))
        
        transaction_db_id = cursor.fetchone()[0]
        
        # Log transaction creation
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            TRANSACTION_STATUS_PENDING,
            json.dumps({"message": "Transaction created", "data": transaction_data}),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "transaction_data": transaction_data
        }
    except Exception as e:
        logger.error(f"Error preparing swap transaction: {e}")
        return {
            "success": False,
            "error": f"Error preparing transaction: {str(e)}"
        }

async def prepare_add_liquidity_transaction(
    user_id: int,
    wallet_address: str,
    amount: float,
    token_a: str,
    token_b: str,
    pool_id: str
) -> Dict[str, Any]:
    """
    Prepare a transaction to add liquidity to a pool.
    
    Args:
        user_id: Telegram user ID
        wallet_address: User's wallet address
        amount: Total amount in USD to add as liquidity
        token_a: First token in the pool
        token_b: Second token in the pool
        pool_id: ID of the liquidity pool
        
    Returns:
        Dict with transaction details
    """
    try:
        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Get client for Raydium API
        raydium_client = get_client()
        
        # Get pool information
        pool_info = await raydium_client.get_pool_by_id(pool_id)
        
        if not pool_info:
            logger.error(f"Pool not found: {pool_id}")
            return {
                "success": False,
                "error": f"Pool not found with ID: {pool_id}"
            }
        
        # Calculate optimal distribution between tokens
        optimal_amounts = calculate_optimal_swap_amount(
            amount,
            token_a,
            token_b,
            pool_info.get("tokenRatio", 1.0),
            pool_info.get("tokenPrices", {})
        )
        
        # Create transaction data
        transaction_data = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "wallet_address": wallet_address,
            "transaction_type": TRANSACTION_TYPE_ADD_LIQUIDITY,
            "status": TRANSACTION_STATUS_PENDING,
            "amount": amount,
            "token_symbol": token_a,
            "target_symbol": token_b,
            "pool_id": pool_id,
            "token_a_amount": optimal_amounts.get("token_a_amount"),
            "token_b_amount": optimal_amounts.get("token_b_amount"),
            "pool_info": pool_info
        }
        
        # Store transaction in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO transactions 
        (transaction_id, user_id, wallet_address, transaction_type, status, amount, token_symbol, target_symbol, pool_id, transaction_data, created_at, updated_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (
            transaction_id,
            user_id,
            wallet_address,
            TRANSACTION_TYPE_ADD_LIQUIDITY,
            TRANSACTION_STATUS_PENDING,
            amount,
            token_a,
            token_b,
            pool_id,
            json.dumps(transaction_data),
            datetime.now(),
            datetime.now(),
            datetime.now() + timedelta(minutes=30)  # Transaction expires in 30 minutes
        ))
        
        transaction_db_id = cursor.fetchone()[0]
        
        # Log transaction creation
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            TRANSACTION_STATUS_PENDING,
            json.dumps({"message": "Transaction created", "data": transaction_data}),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "transaction_data": transaction_data
        }
    except Exception as e:
        logger.error(f"Error preparing add liquidity transaction: {e}")
        return {
            "success": False,
            "error": f"Error preparing transaction: {str(e)}"
        }

async def prepare_remove_liquidity_transaction(
    user_id: int,
    wallet_address: str,
    pool_id: str,
    percentage: float  # Percentage of LP tokens to withdraw (0-100)
) -> Dict[str, Any]:
    """
    Prepare a transaction to remove liquidity from a pool.
    
    Args:
        user_id: Telegram user ID
        wallet_address: User's wallet address
        pool_id: ID of the liquidity pool
        percentage: Percentage of liquidity to remove (0-100)
        
    Returns:
        Dict with transaction details
    """
    try:
        # Generate a unique transaction ID
        transaction_id = str(uuid.uuid4())
        
        # Get client for Raydium API
        raydium_client = get_client()
        
        # Get pool information
        pool_info = await raydium_client.get_pool_by_id(pool_id)
        
        if not pool_info:
            logger.error(f"Pool not found: {pool_id}")
            return {
                "success": False,
                "error": f"Pool not found with ID: {pool_id}"
            }
        
        # Get user's LP token balance for this pool
        wallet_service = get_wallet_service()
        token_balances = await wallet_service.get_token_balances(wallet_address)
        
        # In a real implementation, we would find the LP token balance for this specific pool
        # For now, we'll use a placeholder
        lp_token_balance = 1.0  # Placeholder value
        
        # Calculate amount to withdraw
        amount_to_withdraw = (percentage / 100.0) * lp_token_balance
        
        # Extract token information from pool
        token_a = pool_info.get("tokenA", {}).get("symbol", "Unknown")
        token_b = pool_info.get("tokenB", {}).get("symbol", "Unknown")
        
        # Create transaction data
        transaction_data = {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "wallet_address": wallet_address,
            "transaction_type": TRANSACTION_TYPE_REMOVE_LIQUIDITY,
            "status": TRANSACTION_STATUS_PENDING,
            "amount": amount_to_withdraw,
            "token_symbol": f"{token_a}-{token_b}-LP",  # LP token symbol
            "target_symbol": None,  # We're not targeting a specific token
            "pool_id": pool_id,
            "percentage": percentage,
            "pool_info": pool_info
        }
        
        # Store transaction in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO transactions 
        (transaction_id, user_id, wallet_address, transaction_type, status, amount, token_symbol, target_symbol, pool_id, transaction_data, created_at, updated_at, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """, (
            transaction_id,
            user_id,
            wallet_address,
            TRANSACTION_TYPE_REMOVE_LIQUIDITY,
            TRANSACTION_STATUS_PENDING,
            amount_to_withdraw,
            f"{token_a}-{token_b}-LP",
            None,
            pool_id,
            json.dumps(transaction_data),
            datetime.now(),
            datetime.now(),
            datetime.now() + timedelta(minutes=30)  # Transaction expires in 30 minutes
        ))
        
        transaction_db_id = cursor.fetchone()[0]
        
        # Log transaction creation
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            TRANSACTION_STATUS_PENDING,
            json.dumps({"message": "Transaction created", "data": transaction_data}),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "transaction_data": transaction_data
        }
    except Exception as e:
        logger.error(f"Error preparing remove liquidity transaction: {e}")
        return {
            "success": False,
            "error": f"Error preparing transaction: {str(e)}"
        }

async def simulate_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Simulate a transaction before execution to check if it will succeed.
    
    Args:
        transaction_id: ID of the transaction to simulate
        
    Returns:
        Dict with simulation results
    """
    try:
        # Get transaction data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT transaction_data, wallet_address, transaction_type, amount, token_symbol, target_symbol
        FROM transactions 
        WHERE transaction_id = %s
        """, (transaction_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction not found with ID: {transaction_id}"
            }
            
        transaction_data_str, wallet_address, transaction_type, amount, token_symbol, target_symbol = result
        transaction_data = json.loads(transaction_data_str)
        
        # Get wallet service
        wallet_service = get_wallet_service()
        
        # Simulate transaction based on transaction type
        simulation_result = None
        error = None
        
        try:
            if transaction_type == TRANSACTION_TYPE_SWAP:
                # Simulate swap transaction
                simulation_result = await wallet_service.simulate_transaction({
                    "type": "swap",
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "from_token": token_symbol,
                    "to_token": target_symbol,
                    "transaction_data": transaction_data
                })
            elif transaction_type == TRANSACTION_TYPE_ADD_LIQUIDITY:
                # Simulate add liquidity transaction
                simulation_result = await wallet_service.simulate_transaction({
                    "type": "add_liquidity",
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "token_a": token_symbol,
                    "token_b": target_symbol,
                    "pool_id": transaction_data.get("pool_id"),
                    "transaction_data": transaction_data
                })
            elif transaction_type == TRANSACTION_TYPE_REMOVE_LIQUIDITY:
                # Simulate remove liquidity transaction
                simulation_result = await wallet_service.simulate_transaction({
                    "type": "remove_liquidity",
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "pool_id": transaction_data.get("pool_id"),
                    "percentage": transaction_data.get("percentage", 100),
                    "transaction_data": transaction_data
                })
            else:
                error = f"Unknown transaction type: {transaction_type}"
                simulation_result = {"success": False, "error": error}
        except Exception as sim_error:
            error = f"Error simulating transaction: {str(sim_error)}"
            simulation_result = {"success": False, "error": error}
        
        # Update transaction status based on simulation result
        if simulation_result.get("success", False):
            new_status = TRANSACTION_STATUS_SIMULATED
        else:
            new_status = TRANSACTION_STATUS_FAILED
            
        # Update transaction in database
        cursor.execute("""
        UPDATE transactions 
        SET status = %s, simulation_result = %s, updated_at = %s
        WHERE transaction_id = %s
        """, (
            new_status,
            json.dumps(simulation_result),
            datetime.now(),
            transaction_id
        ))
        
        # Log transaction simulation
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            new_status,
            json.dumps({
                "message": "Transaction simulated", 
                "simulation_result": simulation_result
            }),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": simulation_result.get("success", False),
            "transaction_id": transaction_id,
            "status": new_status,
            "simulation_result": simulation_result,
            "error": error
        }
    except Exception as e:
        logger.error(f"Error simulating transaction: {e}")
        return {
            "success": False,
            "error": f"Error simulating transaction: {str(e)}"
        }

async def approve_transaction(transaction_id: str, user_id: int) -> Dict[str, Any]:
    """
    Approve a transaction for execution.
    
    Args:
        transaction_id: ID of the transaction to approve
        user_id: Telegram user ID approving the transaction
        
    Returns:
        Dict with approval result
    """
    try:
        # Get transaction data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT transaction_data, wallet_address, status, user_id
        FROM transactions 
        WHERE transaction_id = %s
        """, (transaction_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction not found with ID: {transaction_id}"
            }
            
        transaction_data_str, wallet_address, status, tx_user_id = result
        
        # Verify user is the transaction owner
        if int(tx_user_id) != int(user_id):
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": "You are not authorized to approve this transaction"
            }
        
        # Verify transaction is in a valid state to be approved
        if status not in [TRANSACTION_STATUS_PENDING, TRANSACTION_STATUS_SIMULATED]:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction cannot be approved in its current state: {status}"
            }
        
        # Update transaction status to approved
        cursor.execute("""
        UPDATE transactions 
        SET status = %s, updated_at = %s
        WHERE transaction_id = %s
        """, (
            TRANSACTION_STATUS_APPROVED,
            datetime.now(),
            transaction_id
        ))
        
        # Log transaction approval
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            TRANSACTION_STATUS_APPROVED,
            json.dumps({"message": "Transaction approved by user", "user_id": user_id}),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": TRANSACTION_STATUS_APPROVED,
            "message": "Transaction approved successfully"
        }
    except Exception as e:
        logger.error(f"Error approving transaction: {e}")
        return {
            "success": False,
            "error": f"Error approving transaction: {str(e)}"
        }

async def reject_transaction(transaction_id: str, user_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
    """
    Reject a transaction.
    
    Args:
        transaction_id: ID of the transaction to reject
        user_id: Telegram user ID rejecting the transaction
        reason: Optional reason for rejection
        
    Returns:
        Dict with rejection result
    """
    try:
        # Get transaction data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT transaction_data, wallet_address, status, user_id
        FROM transactions 
        WHERE transaction_id = %s
        """, (transaction_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction not found with ID: {transaction_id}"
            }
            
        transaction_data_str, wallet_address, status, tx_user_id = result
        
        # Verify user is the transaction owner
        if int(tx_user_id) != int(user_id):
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": "You are not authorized to reject this transaction"
            }
        
        # Verify transaction is in a valid state to be rejected
        if status not in [TRANSACTION_STATUS_PENDING, TRANSACTION_STATUS_SIMULATED]:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction cannot be rejected in its current state: {status}"
            }
        
        # Update transaction status to rejected
        cursor.execute("""
        UPDATE transactions 
        SET status = %s, updated_at = %s
        WHERE transaction_id = %s
        """, (
            TRANSACTION_STATUS_REJECTED,
            datetime.now(),
            transaction_id
        ))
        
        # Log transaction rejection
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            TRANSACTION_STATUS_REJECTED,
            json.dumps({
                "message": "Transaction rejected by user", 
                "user_id": user_id,
                "reason": reason
            }),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": TRANSACTION_STATUS_REJECTED,
            "message": "Transaction rejected successfully"
        }
    except Exception as e:
        logger.error(f"Error rejecting transaction: {e}")
        return {
            "success": False,
            "error": f"Error rejecting transaction: {str(e)}"
        }

async def execute_transaction(transaction_id: str) -> Dict[str, Any]:
    """
    Execute an approved transaction.
    
    Args:
        transaction_id: ID of the transaction to execute
        
    Returns:
        Dict with execution result
    """
    try:
        # Get transaction data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT transaction_data, wallet_address, status, transaction_type, amount, token_symbol, target_symbol
        FROM transactions 
        WHERE transaction_id = %s
        """, (transaction_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction not found with ID: {transaction_id}"
            }
            
        transaction_data_str, wallet_address, status, transaction_type, amount, token_symbol, target_symbol = result
        transaction_data = json.loads(transaction_data_str)
        
        # Verify transaction is approved
        if status != TRANSACTION_STATUS_APPROVED:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction must be approved before execution. Current status: {status}"
            }
        
        # Update transaction status to submitted
        cursor.execute("""
        UPDATE transactions 
        SET status = %s, updated_at = %s
        WHERE transaction_id = %s
        """, (
            TRANSACTION_STATUS_SUBMITTED,
            datetime.now(),
            transaction_id
        ))
        
        # Log transaction submission
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            TRANSACTION_STATUS_SUBMITTED,
            json.dumps({"message": "Transaction submitted for execution"}),
            datetime.now()
        ))
        
        conn.commit()
        
        # Get wallet service
        wallet_service = get_wallet_service()
        
        # Execute transaction based on transaction type
        execution_result = None
        signature = None
        error = None
        
        try:
            if transaction_type == TRANSACTION_TYPE_SWAP:
                # Execute swap transaction
                execution_result = await wallet_service.execute_transaction({
                    "type": "swap",
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "from_token": token_symbol,
                    "to_token": target_symbol,
                    "transaction_data": transaction_data
                })
            elif transaction_type == TRANSACTION_TYPE_ADD_LIQUIDITY:
                # Execute add liquidity transaction
                execution_result = await wallet_service.execute_transaction({
                    "type": "add_liquidity",
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "token_a": token_symbol,
                    "token_b": target_symbol,
                    "pool_id": transaction_data.get("pool_id"),
                    "transaction_data": transaction_data
                })
            elif transaction_type == TRANSACTION_TYPE_REMOVE_LIQUIDITY:
                # Execute remove liquidity transaction
                execution_result = await wallet_service.execute_transaction({
                    "type": "remove_liquidity",
                    "wallet_address": wallet_address,
                    "amount": amount,
                    "pool_id": transaction_data.get("pool_id"),
                    "percentage": transaction_data.get("percentage", 100),
                    "transaction_data": transaction_data
                })
            else:
                error = f"Unknown transaction type: {transaction_type}"
                execution_result = {"success": False, "error": error}
                
            if execution_result.get("success", False):
                signature = execution_result.get("signature")
        except Exception as exec_error:
            error = f"Error executing transaction: {str(exec_error)}"
            execution_result = {"success": False, "error": error}
        
        # Update transaction status based on execution result
        if execution_result.get("success", False):
            new_status = TRANSACTION_STATUS_CONFIRMED
        else:
            new_status = TRANSACTION_STATUS_FAILED
            
        # Update transaction in database
        cursor.execute("""
        UPDATE transactions 
        SET status = %s, transaction_signature = %s, updated_at = %s
        WHERE transaction_id = %s
        """, (
            new_status,
            signature,
            datetime.now(),
            transaction_id
        ))
        
        # Log transaction execution
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            new_status,
            json.dumps({
                "message": "Transaction execution completed", 
                "execution_result": execution_result,
                "signature": signature
            }),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": execution_result.get("success", False),
            "transaction_id": transaction_id,
            "status": new_status,
            "signature": signature,
            "execution_result": execution_result,
            "error": error
        }
    except Exception as e:
        logger.error(f"Error executing transaction: {e}")
        return {
            "success": False,
            "error": f"Error executing transaction: {str(e)}"
        }

async def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
    """
    Get the current status of a transaction.
    
    Args:
        transaction_id: ID of the transaction to check
        
    Returns:
        Dict with transaction status and details
    """
    try:
        # Get transaction data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT id, transaction_id, user_id, wallet_address, transaction_type, status, 
               amount, token_symbol, target_symbol, pool_id, transaction_data, simulation_result,
               transaction_signature, created_at, updated_at, expires_at
        FROM transactions 
        WHERE transaction_id = %s
        """, (transaction_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction not found with ID: {transaction_id}"
            }
            
        (db_id, tx_id, user_id, wallet_address, tx_type, status, 
         amount, token_symbol, target_symbol, pool_id, tx_data_str, 
         simulation_result_str, signature, created_at, updated_at, expires_at) = result
         
        tx_data = json.loads(tx_data_str) if tx_data_str else {}
        simulation_result = json.loads(simulation_result_str) if simulation_result_str else {}
        
        # Get transaction logs
        cursor.execute("""
        SELECT status, log_data, created_at
        FROM transaction_logs 
        WHERE transaction_id = %s
        ORDER BY created_at ASC
        """, (transaction_id,))
        
        logs = []
        for log_status, log_data_str, log_created_at in cursor.fetchall():
            log_data = json.loads(log_data_str) if log_data_str else {}
            logs.append({
                "status": log_status,
                "data": log_data,
                "timestamp": log_created_at.isoformat() if log_created_at else None
            })
            
        cursor.close()
        conn.close()
        
        # Check if transaction is expired
        is_expired = expires_at and datetime.now() > expires_at
        current_status = TRANSACTION_STATUS_EXPIRED if is_expired and status in [TRANSACTION_STATUS_PENDING, TRANSACTION_STATUS_SIMULATED] else status
        
        # If status has changed due to expiration, update it
        if current_status != status:
            await update_transaction_status(transaction_id, current_status, {"message": "Transaction expired"})
        
        return {
            "success": True,
            "transaction_id": tx_id,
            "user_id": user_id,
            "wallet_address": wallet_address,
            "transaction_type": tx_type,
            "status": current_status,
            "amount": float(amount) if amount else 0,
            "token_symbol": token_symbol,
            "target_symbol": target_symbol,
            "pool_id": pool_id,
            "transaction_data": tx_data,
            "simulation_result": simulation_result,
            "signature": signature,
            "created_at": created_at.isoformat() if created_at else None,
            "updated_at": updated_at.isoformat() if updated_at else None,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "is_expired": is_expired,
            "logs": logs
        }
    except Exception as e:
        logger.error(f"Error getting transaction status: {e}")
        return {
            "success": False,
            "error": f"Error getting transaction status: {str(e)}"
        }

async def get_user_transactions(user_id: int, limit: int = 10, status: Optional[str] = None) -> Dict[str, Any]:
    """
    Get transactions for a specific user.
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of transactions to return
        status: Optional status filter
        
    Returns:
        Dict with list of transactions
    """
    try:
        # Get transaction data from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on parameters
        query = """
        SELECT id, transaction_id, user_id, wallet_address, transaction_type, status, 
               amount, token_symbol, target_symbol, pool_id, created_at, updated_at
        FROM transactions 
        WHERE user_id = %s
        """
        params = [user_id]
        
        if status:
            query += " AND status = %s"
            params.append(status)
            
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cursor.execute(query, params)
        
        transactions = []
        for (db_id, tx_id, tx_user_id, wallet_address, tx_type, tx_status, 
             amount, token_symbol, target_symbol, pool_id, created_at, updated_at) in cursor.fetchall():
            
            transactions.append({
                "transaction_id": tx_id,
                "user_id": tx_user_id,
                "wallet_address": wallet_address,
                "transaction_type": tx_type,
                "status": tx_status,
                "amount": float(amount) if amount else 0,
                "token_symbol": token_symbol,
                "target_symbol": target_symbol,
                "pool_id": pool_id,
                "created_at": created_at.isoformat() if created_at else None,
                "updated_at": updated_at.isoformat() if updated_at else None
            })
            
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "user_id": user_id,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting user transactions: {e}")
        return {
            "success": False,
            "error": f"Error getting user transactions: {str(e)}"
        }

async def update_transaction_status(transaction_id: str, status: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the status of a transaction.
    
    Args:
        transaction_id: ID of the transaction to update
        status: New status
        log_data: Data to log with the status update
        
    Returns:
        Dict with update result
    """
    try:
        # Update transaction in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE transactions 
        SET status = %s, updated_at = %s
        WHERE transaction_id = %s
        RETURNING id
        """, (
            status,
            datetime.now(),
            transaction_id
        ))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error": f"Transaction not found with ID: {transaction_id}"
            }
        
        # Log transaction status update
        cursor.execute("""
        INSERT INTO transaction_logs 
        (transaction_id, status, log_data, created_at)
        VALUES (%s, %s, %s, %s)
        """, (
            transaction_id,
            status,
            json.dumps(log_data),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": status,
            "message": "Transaction status updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating transaction status: {e}")
        return {
            "success": False,
            "error": f"Error updating transaction status: {str(e)}"
        }

# Initialize transaction tables when module is imported
init_transaction_tables()