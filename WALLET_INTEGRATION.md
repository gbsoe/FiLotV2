# FiLot Wallet Integration Implementation

## Overview

This document details the implementation of a secure wallet connection system for the FiLot Telegram bot, allowing users to connect their Solana wallets to enable investment functionality.

The implementation uses the WalletConnect v2 protocol to establish secure connections between the Telegram bot and users' Solana wallets. This enables the bot to execute investment transactions in liquidity pools while maintaining high security standards.

## Database Schema Updates

### User Model Extensions

The User database model has been extended with the following fields to support wallet connections:

```python
# Wallet connection settings
wallet_address = Column(String(255), nullable=True)  # Solana wallet public address
wallet_connected_at = Column(DateTime, nullable=True)  # When wallet was connected
connection_status = Column(String(20), default="disconnected")  # disconnected, connecting, connected, failed
wallet_session_id = Column(String(100), nullable=True)  # For WalletConnect session tracking
last_tx_id = Column(String(100), nullable=True)  # Last transaction signature
```

### New InvestmentLog Model

A new `InvestmentLog` model has been created to track user investments in liquidity pools:

```python
class InvestmentLog(db.Model):
    """InvestmentLog model for tracking user investments in liquidity pools."""
    __tablename__ = "investment_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    pool_id = Column(String(255), ForeignKey("pools.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount in USD
    tx_hash = Column(String(100), nullable=False)  # Transaction signature/hash
    status = Column(String(20), nullable=False)  # confirming, confirmed, failed, etc.
    token_a_amount = Column(Float, nullable=True)  # Amount of token A invested
    token_b_amount = Column(Float, nullable=True)  # Amount of token B invested
    apr_at_entry = Column(Float, nullable=True)  # APR at time of investment
    notes = Column(Text, nullable=True)  # Optional notes or error messages
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="investments")
    pool = relationship("Pool", backref="investments")
```

## WalletConnect Manager Implementation

A new `WalletConnectManager` class has been created to handle all aspects of wallet connection:

### Class Structure

```python
class WalletConnectManager:
    """Manager for WalletConnect v2 integration with Solana wallets."""
    
    def __init__(self):
        """Initialize the WalletConnect manager."""
        self.active_sessions = {}  # {session_id: {user_id, created_at, expires_at, ...}}
        
    async def create_connection_session(self, user_id: int) -> Dict[str, Any]:
        """Create a new WalletConnect session for a user."""
        # Implementation details...
    
    def _generate_qr_code(self, data: str) -> str:
        """Generate a QR code image for the WalletConnect URI."""
        # Implementation details...
    
    async def check_session_status(self, session_id: str) -> Dict[str, Any]:
        """Check the status of a WalletConnect session."""
        # Implementation details...
    
    async def cancel_session(self, session_id: str) -> Dict[str, Any]:
        """Cancel a WalletConnect session."""
        # Implementation details...
    
    async def disconnect_wallet(self, user_id: int) -> Dict[str, Any]:
        """Disconnect a user's wallet."""
        # Implementation details...
    
    async def send_transaction(self, user_id: int, serialized_transaction: str) -> Dict[str, Any]:
        """Send a transaction to the user's wallet for signing."""
        # Implementation details...
```

### Key Features

1. **Session Management**: The manager creates and tracks wallet connection sessions with unique IDs and expiration times.
2. **QR Code Generation**: It generates scannable QR codes containing connection URIs for wallet apps.
3. **Status Checking**: It allows checking the current status of connection sessions.
4. **Wallet Disconnection**: It provides functionality to disconnect wallets securely.
5. **Transaction Handling**: It facilitates sending transactions to wallets for signing.

## Wallet Actions Module

A `wallet_actions.py` module has been implemented to provide high-level functions for wallet operations:

### Key Functions

1. **initiate_wallet_connection**: Starts a new wallet connection process.
2. **check_connection_status**: Checks the status of an ongoing connection.
3. **disconnect_wallet**: Disconnects a user's wallet.
4. **execute_investment**: Executes an investment in a liquidity pool.

### Connection Status Enum

A `WalletConnectionStatus` enum class provides standardized status values:

```python
class WalletConnectionStatus:
    """Enumeration of wallet connection statuses"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
```

## Telegram Bot Integration

### Button Handlers

Four new button handlers have been added to the Telegram bot to handle wallet operations:

1. **handle_walletconnect**: Initiates the wallet connection process when a user clicks the "Connect Wallet" button.
   - Calls `initiate_wallet_connection` to start a new connection.
   - Generates and displays a QR code for the user to scan.
   - Provides a deep link for mobile users.
   - Offers options to check connection status or cancel the connection.

2. **handle_check_wallet_status**: Checks the status of an ongoing wallet connection when a user clicks the "Check Connection Status" button.
   - Retrieves the session ID from the context or database.
   - Calls `check_connection_status` to get the current status.
   - Displays appropriate messages based on the connection state.
   - Provides next steps based on the connection result.

3. **handle_cancel_wallet_connection**: Cancels an ongoing wallet connection when a user clicks the "Cancel Connection" button.
   - Calls `disconnect_wallet` to clear the connection.
   - Updates the UI to reflect the cancellation.
   - Offers options to start a new connection.

4. **handle_disconnect_wallet**: Disconnects a connected wallet when a user clicks the "Disconnect Wallet" button.
   - Calls `disconnect_wallet` to terminate the connection.
   - Updates the UI to show the wallet is disconnected.
   - Provides reconnection options.

### Callback Registration

All handlers have been registered in main.py to respond to appropriate button clicks:

```python
# Wallet connection handlers
application.add_handler(CallbackQueryHandler(handle_walletconnect, pattern="^walletconnect$"))
application.add_handler(CallbackQueryHandler(handle_check_wallet_status, pattern="^check_wallet_status$"))
application.add_handler(CallbackQueryHandler(handle_cancel_wallet_connection, pattern="^cancel_wallet_connection$"))
application.add_handler(CallbackQueryHandler(handle_disconnect_wallet, pattern="^disconnect_wallet$"))
```

### UI Improvements

The wallet settings screen has been updated to show different information based on the wallet connection status:

1. **Connected**: Shows the wallet address, connection status, and options to disconnect.
2. **Connecting**: Shows connection progress and options to check status or cancel.
3. **Disconnected**: Shows options to connect a wallet.

## User Flow

1. User accesses wallet settings from their account menu.
2. User clicks "Connect Wallet" to initiate a connection.
3. Bot generates a QR code for the user to scan with their Solana wallet app.
4. User scans the QR code with their wallet app and approves the connection.
5. User clicks "Check Connection Status" to verify the connection.
6. Once connected, the user sees their wallet address and can proceed to investments.
7. The user can disconnect their wallet at any time from the wallet settings.

## Security Considerations

1. **Read-Only Mode**: Wallet connections are established in read-only mode initially.
2. **Explicit Approval**: All transactions require explicit approval in the user's wallet app.
3. **No Private Keys**: The bot never has access to users' private keys.
4. **Session Expiry**: Wallet connection sessions expire after 15 minutes if not completed.
5. **Session Tracking**: Active sessions are tracked with unique IDs.

## Future Enhancements

1. **Multi-Wallet Support**: Add support for connecting multiple wallets.
2. **Transaction History**: Implement a UI for viewing past transactions.
3. **Auto-Reconnect**: Add functionality to reconnect wallets automatically.
4. **Enhanced Security**: Implement additional security measures for wallet connections.
5. **Full WalletConnect Integration**: Complete the integration with the actual WalletConnect protocol.

## Technical Notes

1. The WalletConnect manager is currently implemented with a mock version of the protocol for development purposes.
2. QR code generation uses the qrcode library to create scannable images.
3. Asynchronous functions are used throughout to maintain responsiveness.
4. Database operations are handled through SQLAlchemy transactions.
5. Error handling is implemented at multiple levels with detailed logging.