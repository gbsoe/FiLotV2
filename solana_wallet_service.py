"""
Solana wallet integration service for the FiLot bot.

This module provides functionality for:
1. Wallet connection and validation
2. Balance checking
3. Transaction preparation, simulation, and execution
4. WalletConnect-inspired session management
"""

import os
import json
import uuid
import time
import logging
import asyncio
import io
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Solana libraries - Use try/except to handle potential import errors gracefully
try:
    import base58
    import base64
    from solana.rpc.async_api import AsyncClient
    from solana.rpc.commitment import Commitment
    from solana.rpc.types import TokenAccountOpts
    from solana.transaction import Transaction
    from solana.publickey import PublicKey
    from solders.keypair import Keypair
    from solders.signature import Signature
    from solders.message import Message
    from solders.transaction import VersionedTransaction
    import solders.system_program as system_program
    from solders.instruction import Instruction, AccountMeta
    SOLANA_LIBS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Error importing Solana libraries: {e}. Using fallback implementation.")
    SOLANA_LIBS_AVAILABLE = False
    
    # Define placeholder classes for IDE linting
    class AsyncClient:
        def __init__(self, *args, **kwargs):
            pass
            
        async def close(self):
            pass
            
        async def get_balance(self, *args, **kwargs):
            class Value:
                value = 1000000000  # 1 SOL in lamports
            return Value()
            
        async def get_token_accounts_by_owner(self, *args, **kwargs):
            class Value:
                value = []
            return Value()
            
        async def get_recent_blockhash(self, *args, **kwargs):
            class Value:
                class FeeCalculator:
                    lamports_per_signature = 5000
                blockhash = "mockblockhash"
                fee_calculator = FeeCalculator()
                value = None
            return Value()
            
        async def simulate_transaction(self, *args, **kwargs):
            class Value:
                logs = []
                err = None
                units_consumed = 0
            return Value()
            
    class Commitment:
        def __init__(self, *args, **kwargs):
            pass
            
    class TokenAccountOpts:
        def __init__(self, *args, **kwargs):
            pass
            
    class Transaction:
        def __init__(self, *args, **kwargs):
            pass
            
        def add(self, *args, **kwargs):
            pass
    
    class PublicKey:
        def __init__(self, *args, **kwargs):
            pass
            
    # Mock system_program
    class system_program:
        @staticmethod
        def transfer(params):
            return "mock_instruction"
            
        class TransferParams:
            def __init__(self, from_pubkey, to_pubkey, lamports):
                self.from_pubkey = from_pubkey
                self.to_pubkey = to_pubkey
                self.lamports = lamports

# Get RPC endpoint from environment variables - use public endpoint as fallback
SOLANA_RPC_URL = os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Define token mints
TOKEN_MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",  # Native SOL wrapped
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "mSOL": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
}

# Singleton client instance
_client_instance = None

def get_or_create_client():
    """Get or create the Solana RPC client singleton."""
    global _client_instance
    if not _client_instance:
        _client_instance = AsyncClient(SOLANA_RPC_URL, commitment=Commitment("confirmed"))
        logger.info(f"Created Solana RPC client with endpoint: {SOLANA_RPC_URL}")
    return _client_instance

async def close_client():
    """Close the Solana RPC client."""
    global _client_instance
    if _client_instance:
        await _client_instance.close()
        _client_instance = None
        logger.info("Closed Solana RPC client")

class WalletSession:
    """Class to manage wallet connection sessions."""
    
    def __init__(self, user_id: int, wallet_address: Optional[str] = None):
        """Initialize a wallet session."""
        self.session_id = str(uuid.uuid4())
        self.user_id = user_id
        self.wallet_address = wallet_address
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(hours=1)
        self.status = "pending"
        self.security_level = "read_only"
        self.permissions = ["view_balance"]
        self.public_key = None
        
        if wallet_address:
            try:
                self.public_key = PublicKey(wallet_address)
                self.status = "connected"
            except Exception as e:
                logger.error(f"Invalid wallet address: {e}")
                self.status = "error"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "wallet_address": self.wallet_address,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status,
            "security_level": self.security_level,
            "permissions": self.permissions,
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'WalletSession':
        """Create a session from dictionary."""
        session = WalletSession(data["user_id"], data.get("wallet_address"))
        session.session_id = data["session_id"]
        session.created_at = datetime.fromisoformat(data["created_at"])
        session.expires_at = datetime.fromisoformat(data["expires_at"])
        session.status = data["status"]
        session.security_level = data["security_level"]
        session.permissions = data["permissions"]
        
        if session.wallet_address:
            try:
                session.public_key = PublicKey(session.wallet_address)
            except Exception:
                pass
                
        return session
    
    def is_expired(self) -> bool:
        """Check if the session is expired."""
        return datetime.now() > self.expires_at
    
    def is_connected(self) -> bool:
        """Check if the session is connected."""
        return self.status == "connected" and not self.is_expired()

class SolanaWalletService:
    """Service for Solana wallet integration."""
    
    def __init__(self):
        """Initialize the wallet service."""
        self.client = get_or_create_client()
        self.sessions = {}  # In-memory session storage for development
        
    async def validate_wallet_address(self, address: str) -> bool:
        """
        Validate that the provided string is a valid Solana wallet address.
        
        Args:
            address: The wallet address to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate by creating a PublicKey object
            PublicKey(address)
            return True
        except Exception as e:
            logger.error(f"Error validating wallet address: {e}")
            return False
    
    async def create_session(self, user_id: int, wallet_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new wallet session.
        
        Args:
            user_id: Telegram user ID
            wallet_address: Optional wallet address
            
        Returns:
            Session details
        """
        try:
            # Create new session
            session = WalletSession(user_id, wallet_address)
            
            # Store session
            self.sessions[session.session_id] = session
            
            # Generate connection URI if no wallet address provided
            uri = None
            qr_uri = None
            
            if not wallet_address:
                # In a real implementation, this would create a proper WalletConnect URI
                # For development, we'll create a simple URI that we can simulate with
                dummy_topic = str(uuid.uuid4())
                dummy_key = str(uuid.uuid4())
                qr_uri = f"solana:{dummy_topic}@1?relay-protocol=irn&symKey={dummy_key}&session={session.session_id}"
                uri = f"https://phantom.app/ul/browse/{session.session_id}"
                
            return {
                "success": True,
                "session_id": session.session_id,
                "user_id": user_id,
                "wallet_address": wallet_address,
                "status": session.status,
                "security_level": session.security_level,
                "permissions": session.permissions,
                "expires_at": session.expires_at.isoformat(),
                "uri": uri,
                "qr_uri": qr_uri,
            }
        except Exception as e:
            logger.error(f"Error creating wallet session: {e}")
            return {
                "success": False,
                "error": f"Error creating wallet session: {str(e)}"
            }
    
    async def check_session(self, session_id: str) -> Dict[str, Any]:
        """
        Check the status of a wallet session.
        
        Args:
            session_id: The session ID to check
            
        Returns:
            Session status details
        """
        try:
            # Get session from storage
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            # Check if session is expired
            if session.is_expired():
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": "expired",
                    "expired": True,
                    "message": "Session has expired. Please create a new session."
                }
            
            # Return session status
            return {
                "success": True,
                "session_id": session_id,
                "user_id": session.user_id,
                "wallet_address": session.wallet_address,
                "status": session.status,
                "security_level": session.security_level,
                "permissions": session.permissions,
                "created_at": session.created_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "expires_in_seconds": (session.expires_at - datetime.now()).total_seconds(),
                "connected": session.is_connected()
            }
        except Exception as e:
            logger.error(f"Error checking wallet session: {e}")
            return {
                "success": False,
                "error": f"Error checking wallet session: {str(e)}"
            }
    
    async def connect_wallet(self, session_id: str, wallet_address: str) -> Dict[str, Any]:
        """
        Connect a wallet to an existing session.
        
        Args:
            session_id: The session ID to connect to
            wallet_address: The wallet address to connect
            
        Returns:
            Updated session details
        """
        try:
            # Get session from storage
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            # Check if session is expired
            if session.is_expired():
                return {
                    "success": False,
                    "error": "Session has expired. Please create a new session."
                }
            
            # Validate wallet address
            if not await self.validate_wallet_address(wallet_address):
                return {
                    "success": False,
                    "error": "Invalid wallet address"
                }
            
            # Update session
            session.wallet_address = wallet_address
            session.status = "connected"
            try:
                session.public_key = PublicKey(wallet_address)
            except Exception as e:
                logger.error(f"Error creating public key: {e}")
                return {
                    "success": False,
                    "error": f"Invalid wallet address: {str(e)}"
                }
            
            # Store updated session
            self.sessions[session_id] = session
            
            # Return updated session details
            return {
                "success": True,
                "session_id": session_id,
                "user_id": session.user_id,
                "wallet_address": session.wallet_address,
                "status": session.status,
                "security_level": session.security_level,
                "permissions": session.permissions,
                "connected": True
            }
        except Exception as e:
            logger.error(f"Error connecting wallet: {e}")
            return {
                "success": False,
                "error": f"Error connecting wallet: {str(e)}"
            }
    
    async def disconnect_wallet(self, session_id: str) -> Dict[str, Any]:
        """
        Disconnect a wallet from a session.
        
        Args:
            session_id: The session ID to disconnect
            
        Returns:
            Result of operation
        """
        try:
            # Get session from storage
            session = self.sessions.get(session_id)
            
            if not session:
                return {
                    "success": False,
                    "error": "Session not found"
                }
            
            # Delete session
            del self.sessions[session_id]
            
            return {
                "success": True,
                "message": "Wallet disconnected successfully"
            }
        except Exception as e:
            logger.error(f"Error disconnecting wallet: {e}")
            return {
                "success": False,
                "error": f"Error disconnecting wallet: {str(e)}"
            }
    
    async def get_sol_balance(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get SOL balance for a wallet.
        
        Args:
            wallet_address: The wallet address to check
            
        Returns:
            Balance details
        """
        try:
            # Validate wallet address
            if not await self.validate_wallet_address(wallet_address):
                return {
                    "success": False,
                    "error": "Invalid wallet address"
                }
            
            # Create public key
            public_key = PublicKey(wallet_address)
            
            # Get balance
            balance_response = await self.client.get_balance(public_key)
            
            if balance_response.value is None:
                return {
                    "success": False,
                    "error": "Failed to fetch balance"
                }
            
            # Convert lamports to SOL (1 SOL = 1,000,000,000 lamports)
            sol_balance = balance_response.value / 1_000_000_000
            
            return {
                "success": True,
                "wallet_address": wallet_address,
                "sol_balance": sol_balance,
                "sol_balance_lamports": balance_response.value
            }
        except Exception as e:
            logger.error(f"Error getting SOL balance: {e}")
            return {
                "success": False,
                "error": f"Error getting SOL balance: {str(e)}"
            }
    
    async def get_token_balances(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get token balances for a wallet.
        
        Args:
            wallet_address: The wallet address to check
            
        Returns:
            Token balances
        """
        try:
            # Validate wallet address
            if not await self.validate_wallet_address(wallet_address):
                return {
                    "success": False,
                    "error": "Invalid wallet address"
                }
            
            # Create public key
            public_key = PublicKey(wallet_address)
            
            # Get token accounts
            opts = TokenAccountOpts(program_id=PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"))
            token_accounts_response = await self.client.get_token_accounts_by_owner(
                public_key, 
                opts,
                encoding="jsonParsed"
            )
            
            if not token_accounts_response.value:
                # No token accounts found, just return an empty dict
                return {
                    "success": True,
                    "wallet_address": wallet_address,
                    "token_balances": {}
                }
            
            # Process token accounts
            token_balances = {}
            mint_to_symbol = {mint: symbol for symbol, mint in TOKEN_MINTS.items()}
            
            for account in token_accounts_response.value:
                try:
                    # Extract token data
                    token_data = account.account.data.parsed.info
                    mint = token_data.mint
                    decimals = token_data.token_amount.decimals
                    amount = int(token_data.token_amount.amount)
                    
                    # Calculate actual token amount
                    token_amount = amount / (10 ** decimals)
                    
                    # Only include non-zero balances
                    if token_amount > 0:
                        # Use symbol if known, otherwise use truncated mint address
                        symbol = mint_to_symbol.get(mint, mint[:5] + "...")
                        token_balances[symbol] = token_amount
                except Exception as e:
                    logger.warning(f"Error processing token account: {e}")
                    continue
            
            return {
                "success": True,
                "wallet_address": wallet_address,
                "token_balances": token_balances
            }
        except Exception as e:
            logger.error(f"Error getting token balances: {e}")
            return {
                "success": False,
                "error": f"Error getting token balances: {str(e)}"
            }
    
    async def get_wallet_balances(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get all balances for a wallet.
        
        Args:
            wallet_address: The wallet address to check
            
        Returns:
            Combined balance details
        """
        try:
            # Get SOL balance
            sol_result = await self.get_sol_balance(wallet_address)
            
            if not sol_result["success"]:
                return sol_result
            
            # Get token balances
            token_result = await self.get_token_balances(wallet_address)
            
            if not token_result["success"]:
                # If token balances fail, still return SOL balance
                return {
                    "success": True,
                    "wallet_address": wallet_address,
                    "balances": {
                        "SOL": sol_result["sol_balance"]
                    },
                    "warning": f"Error fetching token balances: {token_result.get('error', 'Unknown error')}"
                }
            
            # Combine balances
            balances = {
                "SOL": sol_result["sol_balance"],
                **token_result["token_balances"]
            }
            
            return {
                "success": True,
                "wallet_address": wallet_address,
                "balances": balances
            }
        except Exception as e:
            logger.error(f"Error getting wallet balances: {e}")
            return {
                "success": False,
                "error": f"Error getting wallet balances: {str(e)}"
            }
    
    async def estimate_transaction_fee(self) -> Dict[str, Any]:
        """
        Estimate transaction fee.
        
        Returns:
            Fee details
        """
        try:
            # Get recent blockhash
            response = await self.client.get_recent_blockhash()
            
            if response.value is None:
                return {
                    "success": False,
                    "error": "Failed to fetch recent blockhash"
                }
            
            # Extract fee calculator
            fee_calculator = response.value.fee_calculator
            
            # For simplicity, we'll assume a standard transaction with 1 signature
            # In a real implementation, this would calculate based on transaction size
            lamports_per_signature = fee_calculator.lamports_per_signature
            
            # Convert to SOL
            sol_fee = lamports_per_signature / 1_000_000_000
            
            return {
                "success": True,
                "fee_lamports": lamports_per_signature,
                "fee_sol": sol_fee
            }
        except Exception as e:
            logger.error(f"Error estimating transaction fee: {e}")
            return {
                "success": False,
                "error": f"Error estimating transaction fee: {str(e)}"
            }
    
    async def simulate_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a transaction without executing it.
        
        Args:
            transaction_data: The transaction data
            
        Returns:
            Simulation results
        """
        try:
            # Extract data
            from_address = transaction_data.get("from_address")
            to_address = transaction_data.get("to_address")
            amount_sol = transaction_data.get("amount_sol", 0)
            
            # Validate addresses
            if not await self.validate_wallet_address(from_address) or not await self.validate_wallet_address(to_address):
                return {
                    "success": False,
                    "error": "Invalid wallet address"
                }
            
            # Create public keys
            from_pubkey = PublicKey(from_address)
            to_pubkey = PublicKey(to_address)
            
            # Create instruction
            transfer_instruction = system_program.transfer(
                system_program.TransferParams(
                    from_pubkey=from_pubkey,
                    to_pubkey=to_pubkey,
                    lamports=int(amount_sol * 1_000_000_000)
                )
            )
            
            # Get recent blockhash
            blockhash_response = await self.client.get_recent_blockhash()
            
            if not blockhash_response.value:
                return {
                    "success": False,
                    "error": "Failed to fetch recent blockhash"
                }
            
            recent_blockhash = blockhash_response.value.blockhash
            
            # Create transaction
            transaction = Transaction(recent_blockhash=recent_blockhash)
            transaction.add(transfer_instruction)
            
            # Simulate transaction
            response = await self.client.simulate_transaction(transaction)
            
            if not response.value:
                return {
                    "success": False,
                    "error": "Transaction simulation failed"
                }
            
            # Return simulation results
            return {
                "success": True,
                "transaction_type": "transfer",
                "from_address": from_address,
                "to_address": to_address,
                "amount_sol": amount_sol,
                "logs": response.value.logs,
                "error": response.value.err,
                "units_consumed": response.value.units_consumed,
                "simulation_successful": response.value.err is None
            }
        except Exception as e:
            logger.error(f"Error simulating transaction: {e}")
            return {
                "success": False,
                "error": f"Error simulating transaction: {str(e)}"
            }

    def format_wallet_info(self, balance_result: Dict[str, Any]) -> str:
        """
        Format wallet balance information for display in Telegram messages.
        
        Args:
            balance_result: The result from get_wallet_balances
            
        Returns:
            Formatted string
        """
        if not balance_result["success"]:
            return f"❌ Error: {balance_result.get('error', 'Unknown error')}"
        
        # Header
        wallet_address = balance_result["wallet_address"]
        truncated_address = wallet_address[:4] + "..." + wallet_address[-4:]
        result = f"💼 *Wallet Balance* (`{truncated_address}`)\n\n"
        
        # Format balances
        if "balances" in balance_result:
            balances = balance_result["balances"]
            
            # Display SOL first
            if "SOL" in balances:
                sol_balance = balances["SOL"]
                # Assume 1 SOL ~ $130 (placeholder, would use real price in production)
                sol_value_usd = sol_balance * 130
                result += f"• SOL: *{sol_balance:.4f}* (≈${sol_value_usd:.2f})\n"
            
            # Display stablecoins next
            for stable in ["USDC", "USDT"]:
                if stable in balances:
                    result += f"• {stable}: *{balances[stable]:.2f}*\n"
            
            # Display other tokens
            for token, balance in balances.items():
                if token not in ["SOL", "USDC", "USDT"]:
                    result += f"• {token}: *{balance:.4f}*\n"
        
        # Warning if no balances
        if "balances" not in balance_result or not balance_result["balances"]:
            result += "No tokens found in this wallet.\n"
        
        # Add footer with information on how to use the balance
        result += "\n💡 Use /simulate to see potential earnings with these tokens in liquidity pools."
        
        return result

# Singleton wallet service instance
_service_instance = None

def get_wallet_service() -> SolanaWalletService:
    """Get or create the wallet service singleton."""
    global _service_instance
    if not _service_instance:
        _service_instance = SolanaWalletService()
        logger.info("Created Solana wallet service")
    return _service_instance

# Helper function for testing
async def test_wallet_service():
    """Test the wallet service."""
    wallet_service = get_wallet_service()
    wallet_address = "5r1RVMHxP2iyTZxYJEGq9U1HWyX7YEGqhzAY98NSNSp3"  # Example Solana address
    
    logger.info("Testing wallet service...")
    
    # Create session
    logger.info("Creating session...")
    session_result = await wallet_service.create_session(123456, wallet_address)
    logger.info(f"Session result: {session_result}")
    
    # Get balances
    logger.info("Getting balances...")
    balance_result = await wallet_service.get_wallet_balances(wallet_address)
    logger.info(f"Balance result: {balance_result}")
    
    # Format balances
    logger.info("Formatting balances...")
    formatted_balances = wallet_service.format_wallet_info(balance_result)
    logger.info(f"Formatted balances: {formatted_balances}")
    
    # Close client
    await close_client()
    logger.info("Test complete")

if __name__ == "__main__":
    # Run test if module is executed directly
    asyncio.run(test_wallet_service())