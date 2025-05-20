#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wallet execution logic for FiLot Telegram bot
Handles wallet connection, transaction signing, and investment execution
"""

import logging
import base64
import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from models import User, InvestmentLog, db
from walletconnect_manager import wallet_connect_manager

# Configure logging
logger = logging.getLogger(__name__)

class WalletConnectionStatus:
    """Enumeration of wallet connection statuses"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


def get_wallet_status(user_id: int) -> Tuple[str, Optional[str]]:
    """
    Get the current wallet connection status for a user
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Tuple of (status, wallet_address)
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return WalletConnectionStatus.DISCONNECTED, None
            
        # Return wallet status from user model
        if hasattr(user, 'wallet_address') and user.wallet_address:
            return WalletConnectionStatus.CONNECTED, user.wallet_address
        elif hasattr(user, 'connection_status') and user.connection_status == WalletConnectionStatus.CONNECTING:
            return WalletConnectionStatus.CONNECTING, None
        else:
            return WalletConnectionStatus.DISCONNECTED, None
            
    except Exception as e:
        logger.error(f"Error getting wallet status for user {user_id}: {e}")
        return WalletConnectionStatus.FAILED, None


def connect_wallet(user_id: int, wallet_address: str) -> bool:
    """
    Connect a wallet to the user's account
    
    Args:
        user_id: Telegram user ID
        wallet_address: Solana wallet address
        
    Returns:
        bool: Success or failure
    """
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"Cannot connect wallet for non-existent user {user_id}")
            return False
            
        # Validate wallet address format
        if not wallet_address.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
            logger.error(f"Invalid wallet address format: {wallet_address}")
            return False
            
        # Update user wallet information
        user.wallet_address = wallet_address
        user.connection_status = WalletConnectionStatus.CONNECTED
        db.session.commit()
        
        logger.info(f"Wallet {wallet_address[:8]}... successfully connected for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error connecting wallet for user {user_id}: {e}")
        return False


def disconnect_wallet(user_id: int) -> bool:
    """
    Disconnect a user's wallet
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        bool: Success or failure
    """
    try:
        user = User.query.get(user_id)
        if not user:
            logger.error(f"Cannot disconnect wallet for non-existent user {user_id}")
            return False
            
        # Clear wallet information
        user.wallet_address = None
        user.connection_status = WalletConnectionStatus.DISCONNECTED
        db.session.commit()
        
        logger.info(f"Wallet successfully disconnected for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error disconnecting wallet for user {user_id}: {e}")
        return False


async def initiate_wallet_connection(user_id: int) -> Dict[str, Any]:
    """
    Initiate a new wallet connection process
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Dict with session_id and qr_code_data for WalletConnect
    """
    try:
        # Create or get the user
        user = User.query.get(user_id)
        if not user:
            logger.error(f"Cannot initiate wallet connection for non-existent user {user_id}")
            return {"success": False, "error": "User not found"}
            
        # Update user connection status
        user.connection_status = WalletConnectionStatus.CONNECTING
        db.session.commit()
        
        # Use the WalletConnect manager to create a session
        result = await wallet_connect_manager.create_connection_session(user_id)
        
        if not result.get("success", False):
            logger.error(f"Failed to create WalletConnect session for user {user_id}: {result.get('error')}")
            return result
        
        # Return the session information
        return {
            "success": True,
            "session_id": result.get("session_id"),
            "qr_code_data": result.get("qr_code_data"),
            "qr_code_image": result.get("qr_code_image"),
            "expires_at": result.get("expires_at"),
            "deep_link": result.get("deep_link")
        }
        
    except Exception as e:
        logger.error(f"Error initiating wallet connection for user {user_id}: {e}")
        return {"success": False, "error": str(e)}


async def check_connection_status(user_id: int, session_id: str) -> Dict[str, Any]:
    """
    Check the status of a wallet connection in progress
    
    Args:
        user_id: Telegram user ID
        session_id: Connection session ID
        
    Returns:
        Dict with status information
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return {"success": False, "status": WalletConnectionStatus.FAILED, "error": "User not found"}
            
        # Check if session IDs match
        if user.wallet_session_id != session_id:
            return {"success": False, "status": WalletConnectionStatus.FAILED, "error": "Invalid session"}
        
        # Use the WalletConnect manager to check session status
        result = await wallet_connect_manager.check_session_status(session_id)
        
        if not result.get("success", False):
            logger.error(f"Failed to check WalletConnect session for user {user_id}: {result.get('error')}")
            if result.get("status") == "expired":
                # Update user status if session expired
                user.connection_status = WalletConnectionStatus.DISCONNECTED
                user.wallet_session_id = None
                db.session.commit()
            return {"success": False, "status": result.get("status", WalletConnectionStatus.FAILED), "error": result.get("error")}
        
        # Update user information based on session status
        if result.get("status") == "connected" and user.connection_status != WalletConnectionStatus.CONNECTED:
            wallet_address = result.get("wallet_address")
            if wallet_address:
                user.wallet_address = wallet_address
                user.connection_status = WalletConnectionStatus.CONNECTED
                user.wallet_connected_at = datetime.utcnow()
                db.session.commit()
        
        # Return status information
        return {
            "success": True,
            "status": user.connection_status,
            "wallet_address": user.wallet_address,
            "expires_at": result.get("expires_at")
        }
        
    except Exception as e:
        logger.error(f"Error checking connection status for user {user_id}: {e}")
        return {"success": False, "status": WalletConnectionStatus.FAILED, "error": str(e)}


async def execute_investment(wallet_address: str, pool_id: str, amount: float) -> Dict[str, Any]:
    """
    Execute an investment in a Raydium liquidity pool
    
    Args:
        wallet_address: User's Solana wallet address
        pool_id: Raydium pool ID
        amount: Investment amount in USD
        
    Returns:
        Dict with transaction information
    """
    try:
        logger.info(f"Starting investment execution for wallet {wallet_address[:8]}... in pool {pool_id}, amount ${amount}")
        
        # 1. Fetch pool metadata from SolPool API
        pool_data = await fetch_pool_metadata(pool_id)
        if not pool_data:
            return {
                "success": False,
                "error": "Failed to fetch pool data",
                "message": "Could not retrieve pool information. Please try again later."
            }
        
        token_a_mint = pool_data.get('token_a_mint')
        token_b_mint = pool_data.get('token_b_mint')
        token_a_symbol = pool_data.get('token_a_symbol', 'Unknown')
        token_b_symbol = pool_data.get('token_b_symbol', 'Unknown')
        
        logger.info(f"Pool {pool_id} metadata fetched: {token_a_symbol}/{token_b_symbol}")
        
        # 2. Calculate token amounts based on current prices
        token_amounts = await calculate_token_amounts(pool_id, amount)
        if not token_amounts or 'error' in token_amounts:
            return {
                "success": False,
                "error": token_amounts.get('error', "Failed to calculate token amounts"),
                "message": "Could not determine token ratios for investment. Please try again later."
            }
        
        token_a_amount = token_amounts.get('token_a_amount')
        token_b_amount = token_amounts.get('token_b_amount')
        
        logger.info(f"Calculated token amounts: {token_a_amount} {token_a_symbol}, {token_b_amount} {token_b_symbol}")
        
        # 3. Build a Solana transaction for Raydium liquidity pool investment
        transaction_data = await build_raydium_lp_transaction(
            wallet_address=wallet_address,
            pool_id=pool_id,
            token_a_mint=token_a_mint,
            token_b_mint=token_b_mint,
            token_a_amount=token_a_amount,
            token_b_amount=token_b_amount
        )
        
        if not transaction_data or 'error' in transaction_data:
            return {
                "success": False,
                "error": transaction_data.get('error', "Failed to build transaction"),
                "message": "Could not create the investment transaction. Please try again later."
            }
        
        serialized_tx = transaction_data.get('serialized_transaction')
        logger.info(f"Transaction built successfully for pool {pool_id}")
        
        # 4. Send transaction to user's wallet via WalletConnect for signing
        signing_result = await send_transaction_for_signing(
            wallet_address=wallet_address,
            serialized_transaction=serialized_tx
        )
        
        if not signing_result or 'error' in signing_result:
            return {
                "success": False,
                "error": signing_result.get('error', "Transaction was not signed"),
                "message": "The transaction was not signed. Please check your wallet and try again."
            }
        
        signature = signing_result.get('signature')
        logger.info(f"Transaction signed with signature: {signature[:10]}...")
        
        # 5. Submit signed transaction to Solana network
        submission_result = await submit_signed_transaction(signature)
        
        if not submission_result or 'error' in submission_result:
            return {
                "success": False,
                "error": submission_result.get('error', "Failed to submit transaction"),
                "message": "Failed to submit the signed transaction to the network. Please try again later."
            }
        
        # 6. Store transaction in database
        tx_hash = signature
        
        # Create investment log entry in database
        await create_investment_log(
            user_id=get_user_id_from_wallet(wallet_address),
            pool_id=pool_id,
            amount=amount,
            tx_hash=tx_hash,
            status="confirming"
        )
        
        # Update user's last transaction ID
        await update_user_last_tx(wallet_address, tx_hash)
        
        logger.info(f"Investment transaction completed and logged: {tx_hash}")
        
        # 7. Return success with transaction link
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "pool_id": pool_id,
            "amount_usd": amount,
            "tx_link": f"https://solscan.io/tx/{tx_hash}",
            "token_a_amount": token_a_amount,
            "token_b_amount": token_b_amount,
            "token_a_symbol": token_a_symbol,
            "token_b_symbol": token_b_symbol,
            "status": "confirming",
            "message": "Investment transaction initiated. Please check your wallet for status updates."
        }
        
    except Exception as e:
        logger.error(f"Error executing investment for wallet {wallet_address} in pool {pool_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute investment. Please try again later."
        }


# Helper functions for investment execution

async def fetch_pool_metadata(pool_id: str) -> Dict[str, Any]:
    """
    Fetch metadata for a pool from SolPool API
    
    Args:
        pool_id: Raydium pool ID
        
    Returns:
        Pool metadata including token information
    """
    try:
        from solpool_api_client import SolPoolClient
        
        # Initialize API client
        solpool_client = SolPoolClient()
        
        # Fetch pool data from API
        response = await solpool_client.get_pool(pool_id)
        
        if not response or "error" in response:
            logger.error(f"Error fetching pool data from SolPool API: {response.get('error', 'Unknown error')}")
            return {}
            
        # Return complete pool metadata
        return {
            "id": pool_id,
            "token_a_mint": response.get("tokenAMint"),
            "token_b_mint": response.get("tokenBMint"),
            "token_a_symbol": response.get("tokenASymbol"),
            "token_b_symbol": response.get("tokenBSymbol"),
            "apr_24h": float(response.get("apr24h", 0)),
            "tvl": float(response.get("tvlUsd", 0)),
            "pool_address": response.get("poolAddress"),
            "amm_id": response.get("ammId"),
            "lp_mint": response.get("lpMint"),
            "token_a_decimals": int(response.get("tokenADecimals", 9)),
            "token_b_decimals": int(response.get("tokenBDecimals", 6)),
            "raydium_program_id": response.get("programId", "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"),
            "prediction_score": float(response.get("predictionScore", 0)),
            "sentiment_score": float(response.get("sentimentScore", 0)),
            "risk_level": response.get("riskLevel", "moderate")
        }
        
    except Exception as e:
        logger.error(f"Error fetching pool metadata for {pool_id}: {e}")
        return {}


async def calculate_token_amounts(pool_id: str, amount_usd: float) -> Dict[str, Any]:
    """
    Calculate token amounts for investment based on current pool prices
    
    Args:
        pool_id: Raydium pool ID
        amount_usd: Investment amount in USD
        
    Returns:
        Dictionary with token_a_amount and token_b_amount
    """
    try:
        from solpool_api_client import SolPoolClient
        from filotsense_api_client import FilotSenseClient
        
        # Get pool data first
        pool_data = await fetch_pool_metadata(pool_id)
        if not pool_data:
            return {"error": "Failed to fetch pool metadata"}
            
        # Initialize API clients
        solpool_client = SolPoolClient()
        
        # Get current token prices and pool ratio
        pricing_data = await solpool_client.get_pool_pricing(pool_id)
        if not pricing_data or "error" in pricing_data:
            return {"error": "Failed to fetch current pool pricing"}
            
        # Extract token prices
        token_a_price_usd = float(pricing_data.get("tokenAPrice", 0))
        token_b_price_usd = float(pricing_data.get("tokenBPrice", 0))
        
        # Check if prices are valid
        if token_a_price_usd <= 0 or token_b_price_usd <= 0:
            return {"error": "Invalid token prices received"}
            
        # Get optimal ratio
        pool_ratio = float(pricing_data.get("tokenRatio", 0.5))  # Ratio of token_a to token_b in pool
        
        # If no ratio is available, use 50/50 split
        if pool_ratio <= 0:
            pool_ratio = 0.5
            
        # Calculate amounts based on the pool ratio
        token_a_usd_amount = amount_usd * pool_ratio
        token_b_usd_amount = amount_usd * (1 - pool_ratio)
        
        # Convert USD amounts to token amounts
        token_a_amount = token_a_usd_amount / token_a_price_usd
        token_b_amount = token_b_usd_amount / token_b_price_usd
        
        # Calculate price impact
        price_impact = float(pricing_data.get("priceImpact", 0.0))
        if not price_impact:
            # Estimate price impact based on investment size and pool TVL
            pool_tvl = float(pool_data.get("tvl", 1000000))  # Default to 1M if not available
            price_impact = min(1.0, (amount_usd / pool_tvl) * 100) if pool_tvl > 0 else 0.5
        
        logger.info(f"Calculated token amounts for ${amount_usd} investment in pool {pool_id}: " +
                    f"{token_a_amount} {pool_data.get('token_a_symbol')} and " +
                    f"{token_b_amount} {pool_data.get('token_b_symbol')} " +
                    f"with {price_impact}% price impact")
        
        return {
            "token_a_amount": token_a_amount,
            "token_b_amount": token_b_amount,
            "token_a_price_usd": token_a_price_usd,
            "token_b_price_usd": token_b_price_usd,
            "token_a_usd_value": token_a_usd_amount,
            "token_b_usd_value": token_b_usd_amount,
            "price_impact": price_impact
        }
        
    except Exception as e:
        logger.error(f"Error calculating token amounts for pool {pool_id}: {e}")
        return {"error": str(e)}


async def build_raydium_lp_transaction(
    wallet_address: str,
    pool_id: str,
    token_a_mint: str,
    token_b_mint: str,
    token_a_amount: float,
    token_b_amount: float
) -> Dict[str, Any]:
    """
    Build a Solana transaction for Raydium LP investment
    
    Args:
        wallet_address: User's Solana wallet address
        pool_id: Raydium pool ID
        token_a_mint: Token A mint address
        token_b_mint: Token B mint address
        token_a_amount: Amount of Token A to invest
        token_b_amount: Amount of Token B to invest
        
    Returns:
        Dictionary with serialized_transaction and other metadata
    """
    try:
        logger.info(f"Building Raydium LP transaction for pool {pool_id}")
        
        # Import Solana libraries
        from solana.rpc.api import Client
        from solana.transaction import Transaction, TransactionInstruction, AccountMeta
        from solana.publickey import PublicKey
        from solana.rpc.types import TxOpts
        from solders.instruction import Instruction
        from solders.pubkey import Pubkey
        import base58
        
        # Define constants for Raydium program
        RAYDIUM_LIQUIDITY_PROGRAM_ID = PublicKey("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
        SYSTEM_PROGRAM_ID = PublicKey("11111111111111111111111111111111")
        TOKEN_PROGRAM_ID = PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        ASSOCIATED_TOKEN_PROGRAM_ID = PublicKey("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
        SYSVAR_RENT_PUBKEY = PublicKey("SysvarRent111111111111111111111111111111111")
        
        # Connect to Solana network
        solana_client = Client("https://api.mainnet-beta.solana.com")
        
        # Convert addresses to PublicKey objects
        user_wallet = PublicKey(wallet_address)
        token_a_mint_pubkey = PublicKey(token_a_mint)
        token_b_mint_pubkey = PublicKey(token_b_mint)
        
        # Fetch pool data from Raydium API (normally we'd get this from our SolPool API)
        pool_pubkey = PublicKey(pool_id)
        
        # Derive associated token accounts for the user's wallet
        def find_associated_token_address(wallet_address, token_mint):
            return PublicKey.find_program_address(
                [
                    bytes(wallet_address),
                    bytes(TOKEN_PROGRAM_ID),
                    bytes(token_mint)
                ],
                ASSOCIATED_TOKEN_PROGRAM_ID
            )[0]
            
        user_token_a_account = find_associated_token_address(user_wallet, token_a_mint_pubkey)
        user_token_b_account = find_associated_token_address(user_wallet, token_b_mint_pubkey)
        
        # Get pool accounts from pool ID
        # In a real implementation, we would fetch these from either our API or
        # directly from on-chain data
        
        # For this example, we're assuming we have these pool parameters from our API
        # These would normally come from fetch_pool_metadata()
        pool_authority = PublicKey.find_program_address(
            [bytes(pool_pubkey)],
            RAYDIUM_LIQUIDITY_PROGRAM_ID
        )[0]
        
        # Normally these would be fetched from our pool data API
        pool_token_a_account = PublicKey(f"pool_token_a_{pool_id[:8]}")  # Example address
        pool_token_b_account = PublicKey(f"pool_token_b_{pool_id[:8]}")  # Example address
        lp_mint = PublicKey(f"lp_mint_{pool_id[:8]}")  # Example address
        user_lp_token_account = find_associated_token_address(user_wallet, lp_mint)
        
        # Convert token amounts to lamports (the smallest denomination)
        # For this example we're using standard 9 decimals for SOL-like tokens
        # and 6 decimals for USDC-like tokens but this would be fetched from token data
        token_a_decimals = 9 if "SOL" in token_a_mint else 6
        token_b_decimals = 6 if "USDC" in token_b_mint else 9
        
        token_a_lamports = int(token_a_amount * (10 ** token_a_decimals))
        token_b_lamports = int(token_b_amount * (10 ** token_b_decimals))
        
        logger.info(f"Token amounts in lamports: {token_a_lamports} / {token_b_lamports}")
        
        # Create a new transaction
        transaction = Transaction()
        
        # Create instructions
        
        # 1. Create associated token accounts if they don't exist
        # Check if user's token accounts exist and create them if needed
        # (This would be separate instructions added to the transaction)
        
        # 2. Approve tokens for transfer (transfer authority)
        # (This would be a token program instruction)
        
        # 3. Add main deposit liquidity instruction
        # This is the main Raydium addLiquidity instruction
        # The actual instruction layout would come from Raydium's IDL
        
        # For the Raydium addLiquidity instruction, we need to structure the data correctly
        # This is a simplified version - in production this would follow Raydium's
        # exact instruction format
        data = bytes([
            1,  # Instruction index for addLiquidity
            *list(token_a_lamports.to_bytes(8, 'little')),
            *list(token_b_lamports.to_bytes(8, 'little')),
            # Additional parameters would go here
        ])
        
        # Define accounts required for the addLiquidity instruction
        # The order and inclusion of accounts is specific to Raydium's instruction format
        accounts = [
            AccountMeta(pubkey=user_wallet, is_signer=True, is_writable=True),
            AccountMeta(pubkey=pool_token_a_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=pool_token_b_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=lp_mint, is_signer=False, is_writable=True),
            AccountMeta(pubkey=user_token_a_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=user_token_b_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=user_lp_token_account, is_signer=False, is_writable=True),
            AccountMeta(pubkey=pool_authority, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        ]
        
        # Create and add addLiquidity instruction
        add_liquidity_ix = TransactionInstruction(
            program_id=RAYDIUM_LIQUIDITY_PROGRAM_ID,
            data=data,
            keys=accounts
        )
        
        transaction.add(add_liquidity_ix)
        
        # Get a recent blockhash
        response = solana_client.get_recent_blockhash()
        if not response["result"]:
            raise ValueError("Failed to get recent blockhash")
            
        recent_blockhash = response["result"]["value"]["blockhash"]
        transaction.recent_blockhash = recent_blockhash
        
        # Set fee payer
        transaction.fee_payer = user_wallet
        
        # Serialize the transaction
        serialized_tx = base64.b64encode(transaction.serialize()).decode('ascii')
        
        logger.info(f"Transaction built successfully: {serialized_tx[:20]}...")
        
        return {
            "serialized_transaction": serialized_tx,
            "wallet_address": wallet_address,
            "pool_id": pool_id,
            "expires_at": int(time.time()) + 120,  # 2 minute expiration
            "token_a_amount": token_a_amount,
            "token_b_amount": token_b_amount
        }
        
    except Exception as e:
        logger.error(f"Error building Raydium LP transaction: {e}")
        return {"error": str(e)}


async def send_transaction_for_signing(wallet_address: str, serialized_transaction: str) -> Dict[str, Any]:
    """
    Send a transaction to the user's wallet for signing via WalletConnect
    
    Args:
        wallet_address: User's Solana wallet address
        serialized_transaction: Base64-encoded serialized transaction
        
    Returns:
        Dictionary with signature and metadata if successful
    """
    try:
        logger.info(f"Sending transaction to wallet {wallet_address[:8]}... for signing")
        
        # Get the user from the database by wallet address
        user = await get_user_by_wallet_address(wallet_address)
        if not user:
            return {
                "success": False,
                "error": "User not found",
                "message": "Could not find user with the provided wallet address."
            }
        
        # Get the user's WalletConnect session
        session_id = user.wallet_session_id
        if not session_id:
            return {
                "success": False, 
                "error": "No active wallet session",
                "message": "No active wallet connection found. Please reconnect your wallet."
            }
        
        from walletconnect_manager import wallet_connect_manager
        
        # Send transaction to wallet for signing using WalletConnect
        signing_result = await wallet_connect_manager.send_transaction(
            user_id=user.id,
            serialized_transaction=serialized_transaction
        )
        
        if not signing_result.get("success", False):
            return {
                "success": False,
                "error": signing_result.get("error", "Failed to sign transaction"),
                "message": signing_result.get("message", "Could not sign the transaction. Please try again.")
            }
        
        # Get signature from result
        signature = signing_result.get("signature")
        if not signature:
            return {
                "success": False,
                "error": "No signature returned",
                "message": "No signature was returned from your wallet. Please try again."
            }
        
        logger.info(f"Transaction signed successfully with signature: {signature[:10]}...")
        
        return {
            "success": True,
            "signature": signature,
            "wallet_address": wallet_address,
            "signed_at": int(time.time())
        }
        
    except Exception as e:
        logger.error(f"Error sending transaction for signing: {e}")
        return {"success": False, "error": str(e), "message": "An error occurred while sending the transaction for signing."}


async def submit_signed_transaction(signature: str) -> Dict[str, Any]:
    """
    Submit a signed transaction to the Solana network
    
    Args:
        signature: Transaction signature from wallet
        
    Returns:
        Dictionary with submission result
    """
    try:
        logger.info(f"Submitting signed transaction to Solana network: {signature[:10]}...")
        
        # Import Solana libraries
        from solana.rpc.api import Client
        from solana.rpc.types import TxOpts
        import base58
        
        # Connect to Solana network
        solana_client = Client("https://api.mainnet-beta.solana.com")
        
        # The signature provided by WalletConnect is actually the full signed transaction
        # We need to decode it and submit it to the network
        try:
            # Convert from base64 to binary if needed
            if signature.startswith("Base64:"):
                import base64
                signed_tx_data = base64.b64decode(signature[7:])
            else:
                # Assuming the signature is the full signed transaction in base58
                signed_tx_data = base58.b58decode(signature)
            
            # Send the transaction to the network
            send_opts = TxOpts(skip_preflight=False, preflight_commitment="confirmed")
            response = await solana_client.send_raw_transaction(
                signed_tx_data,
                opts=send_opts
            )
            
            if not response or "result" not in response:
                return {
                    "success": False,
                    "error": "Failed to submit transaction",
                    "message": "Network did not acknowledge the transaction."
                }
            
            # Extract the transaction signature from the response
            tx_signature = response["result"]
            
            logger.info(f"Transaction submitted with signature: {tx_signature}")
            
            # Wait for confirmation (optional, can be moved to a separate function)
            # This makes a synchronous check for confirmation
            confirmation_status = "finalized"  # or "confirmed" for faster but less final confirmation
            
            # Try to get confirmation a few times with backoff
            max_retries = 3
            for retry in range(max_retries):
                try:
                    await asyncio.sleep(1 * (2 ** retry))  # Exponential backoff
                    confirm_response = await solana_client.confirm_transaction(
                        tx_signature,
                        commitment=confirmation_status
                    )
                    
                    if confirm_response and confirm_response.get("result", {}).get("value", False):
                        # Transaction confirmed
                        break
                except Exception as confirm_error:
                    logger.warning(f"Confirmation check {retry+1} failed: {confirm_error}")
                    if retry == max_retries - 1:
                        # Last retry failed
                        logger.warning("Could not confirm transaction finality, continuing anyway")
            
            # Get transaction details
            tx_response = await solana_client.get_transaction(
                tx_signature,
                commitment=confirmation_status
            )
            
            slot = tx_response.get("result", {}).get("slot", 0) if tx_response else 0
            
            return {
                "success": True,
                "signature": tx_signature,
                "slot": slot,
                "submitted_at": int(time.time()),
                "tx_link": f"https://solscan.io/tx/{tx_signature}"
            }
            
        except Exception as submit_error:
            logger.error(f"Error in transaction submission: {submit_error}")
            return {
                "success": False,
                "error": str(submit_error),
                "message": "Failed to submit the transaction to the network."
            }
        
    except Exception as e:
        logger.error(f"Error submitting signed transaction: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "An unexpected error occurred while processing the transaction."
        }


async def create_investment_log(user_id: int, pool_id: str, amount: float, tx_hash: str, status: str,
                            token_a_amount: float = None, token_b_amount: float = None, apr_at_entry: float = None) -> bool:
    """
    Create a log entry for an investment in the database
    
    Args:
        user_id: Telegram user ID
        pool_id: Raydium pool ID
        amount: Investment amount in USD
        tx_hash: Transaction hash/signature
        status: Transaction status
        token_a_amount: Amount of token A invested (optional)
        token_b_amount: Amount of token B invested (optional)
        apr_at_entry: APR at time of investment (optional)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import models and db
        from models import InvestmentLog, db
        
        # Create new investment log entry
        investment_log = InvestmentLog(
            user_id=user_id,
            pool_id=pool_id,
            amount=amount,
            tx_hash=tx_hash,
            status=status,
            token_a_amount=token_a_amount,
            token_b_amount=token_b_amount,
            apr_at_entry=apr_at_entry,
            created_at=datetime.utcnow()
        )
        
        # Add and commit to database
        db.session.add(investment_log)
        db.session.commit()
        
        logger.info(f"Created investment log for user {user_id}, pool {pool_id}, amount ${amount}, tx {tx_hash}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating investment log: {e}")
        return False


async def update_user_last_tx(wallet_address: str, tx_hash: str) -> bool:
    """
    Update a user's last transaction hash in the database
    
    Args:
        wallet_address: User's Solana wallet address
        tx_hash: Transaction hash/signature
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Import necessary models
        from models import User, db
        
        # Find user by wallet address
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if not user:
            logger.error(f"No user found with wallet address {wallet_address[:8]}...")
            return False
            
        # Update last transaction ID
        user.last_tx_id = tx_hash
        db.session.commit()
        
        logger.info(f"Updated last transaction for wallet {wallet_address[:8]}... to {tx_hash[:10]}...")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user last transaction: {e}")
        return False


def get_user_id_from_wallet(wallet_address: str) -> Optional[int]:
    """
    Get a user's ID from their wallet address
    
    Args:
        wallet_address: User's Solana wallet address
        
    Returns:
        Telegram user ID if found, None otherwise
    """
    try:
        # Import User model
        from models import User
        
        # Query the database
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if user:
            return user.id
        
        logger.warning(f"No user found with wallet address {wallet_address[:8]}...")
        return None
        
    except Exception as e:
        logger.error(f"Error getting user ID from wallet {wallet_address}: {e}")
        return None


async def get_user_by_wallet_address(wallet_address: str) -> Optional[Any]:
    """
    Get a user from their wallet address
    
    Args:
        wallet_address: User's Solana wallet address
        
    Returns:
        User object if found, None otherwise
    """
    try:
        # Import User model
        from models import User
        
        # Query the database
        user = User.query.filter_by(wallet_address=wallet_address).first()
        return user
        
    except Exception as e:
        logger.error(f"Error getting user from wallet address: {e}")
        return None


def check_transaction_status(tx_hash: str) -> Dict[str, Any]:
    """
    Check the status of a transaction
    
    Args:
        tx_hash: Transaction hash
        
    Returns:
        Dict with transaction status
    """
    try:
        # In a real implementation, this would query the Solana blockchain
        # TODO: Implement actual Solana transaction status check
        
        # For now, we'll mock successful confirmation
        return {
            "success": True,
            "transaction_hash": tx_hash,
            "status": "confirmed",
            "confirmations": 32,
            "block_time": int(time.time()) - 10,
            "tx_link": f"https://solscan.io/tx/{tx_hash}"
        }
        
    except Exception as e:
        logger.error(f"Error checking transaction status for {tx_hash}: {e}")
        return {
            "success": False,
            "transaction_hash": tx_hash,
            "status": "unknown",
            "error": str(e)
        }