"""
Test script to verify that the wallet integration is working properly.
"""

import asyncio
import logging
from solana_wallet_service import get_wallet_service
from walletconnect_utils import create_walletconnect_session, check_walletconnect_session, kill_walletconnect_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Example Solana wallet address (Binance hot wallet for testing)
TEST_WALLET_ADDRESS = "3VX9DDKtKUE3V2Rs2HyUHFuVh8VnvJ8D1NQpKsxFJQYN"

async def test_wallet_service():
    """Test the SolanaWalletService functionality."""
    logger.info("Testing SolanaWalletService")
    
    # Get the wallet service
    wallet_service = get_wallet_service()
    
    # Create a session without a wallet address
    logger.info("Creating a new wallet session without address...")
    session_result = await wallet_service.create_session(user_id=123456)
    
    if not session_result["success"]:
        logger.error(f"Failed to create session: {session_result.get('error', 'Unknown error')}")
        return
    
    session_id = session_result["session_id"]
    logger.info(f"Session created with ID: {session_id}")
    logger.info(f"Session details: {session_result}")
    
    # Check the session status
    logger.info("Checking session status...")
    status_result = await wallet_service.check_session(session_id)
    logger.info(f"Session status: {status_result}")
    
    # Connect a wallet to the session
    logger.info(f"Connecting wallet {TEST_WALLET_ADDRESS} to the session...")
    connect_result = await wallet_service.connect_wallet(session_id, TEST_WALLET_ADDRESS)
    
    if not connect_result["success"]:
        logger.error(f"Failed to connect wallet: {connect_result.get('error', 'Unknown error')}")
    else:
        logger.info(f"Wallet connected: {connect_result}")
        
        # Check wallet balance
        logger.info("Getting wallet balance...")
        balance_result = await wallet_service.get_wallet_balances(TEST_WALLET_ADDRESS)
        logger.info(f"Wallet balance: {balance_result}")
        
        # Format balance for display
        formatted_balance = wallet_service.format_wallet_info(balance_result)
        logger.info(f"Formatted balance: {formatted_balance}")
    
    # Disconnect the wallet
    logger.info("Disconnecting wallet from session...")
    disconnect_result = await wallet_service.disconnect_wallet(session_id)
    logger.info(f"Disconnect result: {disconnect_result}")

async def test_walletconnect_integration():
    """Test the WalletConnect integration."""
    logger.info("Testing WalletConnect integration")
    
    # Create a wallet session
    logger.info("Creating WalletConnect session...")
    session_result = await create_walletconnect_session(telegram_user_id=123456)
    
    if not session_result["success"]:
        logger.error(f"Failed to create WalletConnect session: {session_result.get('error', 'Unknown error')}")
        return
    
    session_id = session_result["session_id"]
    logger.info(f"WalletConnect session created with ID: {session_id}")
    logger.info(f"WalletConnect URI: {session_result.get('uri', 'N/A')}")
    logger.info(f"Raw WalletConnect URI for QR code: {session_result.get('raw_wc_uri', 'N/A')}")
    
    # Check the session status
    logger.info("Checking WalletConnect session status...")
    status_result = await check_walletconnect_session(session_id)
    logger.info(f"WalletConnect session status: {status_result}")
    
    # Kill the session
    logger.info("Killing WalletConnect session...")
    kill_result = await kill_walletconnect_session(session_id)
    logger.info(f"Kill result: {kill_result}")

async def run_tests():
    """Run all tests."""
    logger.info("Starting wallet integration tests")
    
    try:
        # Test SolanaWalletService
        await test_wallet_service()
        
        # Test WalletConnect integration
        await test_walletconnect_integration()
        
        logger.info("All tests completed!")
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_tests())