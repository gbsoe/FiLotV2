# FiLot Solana Transaction Integration

## Overview

This document details the implementation of real Solana transaction capabilities for the FiLot Telegram bot, allowing users to execute actual investments in Raydium liquidity pools using their connected wallets.

The implementation uses the `solana-py` and `anchorpy` libraries to construct and submit transactions to the Solana blockchain through WalletConnect integration, providing users with a seamless investment experience directly from Telegram.

## Core Components Implemented

### 1. Transaction Building

#### Raydium LP Transaction Construction
In `wallet_actions.py`, the `build_raydium_lp_transaction()` function has been implemented to:

- Create a proper Solana transaction for depositing into Raydium liquidity pools
- Use the correct program IDs and account metadata for the Raydium protocol
- Convert token amounts to the correct denominations (lamports) based on token decimals
- Structure instruction data according to Raydium's requirements
- Set proper account permissions (signers, writability) for transaction validation

```python
async def build_raydium_lp_transaction(
    wallet_address: str,
    pool_id: str,
    token_a_mint: str,
    token_b_mint: str,
    token_a_amount: float,
    token_b_amount: float
) -> Dict[str, Any]:
    # Implementation details...
    
    # Define accounts required for the addLiquidity instruction
    accounts = [
        AccountMeta(pubkey=user_wallet, is_signer=True, is_writable=True),
        AccountMeta(pubkey=pool_token_a_account, is_signer=False, is_writable=True),
        AccountMeta(pubkey=pool_token_b_account, is_signer=False, is_writable=True),
        # ... other accounts
    ]
    
    # Create and add addLiquidity instruction
    add_liquidity_ix = TransactionInstruction(
        program_id=RAYDIUM_LIQUIDITY_PROGRAM_ID,
        data=data,
        keys=accounts
    )
    
    # Transaction serialization
    serialized_tx = base64.b64encode(transaction.serialize()).decode('ascii')
    # ...
```

### 2. Real API Integration

#### SolPool API Client Integration
The function `fetch_pool_metadata()` has been updated to retrieve actual pool data from the SolPool API:

```python
async def fetch_pool_metadata(pool_id: str) -> Dict[str, Any]:
    # Implementation using real API calls
    from solpool_api_client import SolPoolClient
    
    # Initialize API client
    solpool_client = SolPoolClient()
    
    # Fetch pool data from API
    response = await solpool_client.get_pool(pool_id)
    
    # Process response into standardized format
    return {
        "id": pool_id,
        "token_a_mint": response.get("tokenAMint"),
        "token_b_mint": response.get("tokenBMint"),
        # ... other fields mapped from API response
    }
```

#### Token Amount Calculation
The `calculate_token_amounts()` function now uses real pricing data to calculate optimal token amounts:

```python
async def calculate_token_amounts(pool_id: str, amount_usd: float) -> Dict[str, Any]:
    # Implementation using real pricing data
    
    # Get pool data and pricing information
    pricing_data = await solpool_client.get_pool_pricing(pool_id)
    
    # Extract token prices
    token_a_price_usd = float(pricing_data.get("tokenAPrice", 0))
    token_b_price_usd = float(pricing_data.get("tokenBPrice", 0))
    
    # Calculate optimal amounts based on pool ratio
    pool_ratio = float(pricing_data.get("tokenRatio", 0.5))
    
    # Convert USD to token amounts
    token_a_amount = (amount_usd * pool_ratio) / token_a_price_usd
    token_b_amount = (amount_usd * (1 - pool_ratio)) / token_b_price_usd
    
    # Calculate price impact
    # ...
```

### 3. Transaction Signing and Submission

#### WalletConnect Integration
The `send_transaction_for_signing()` function has been implemented to send transactions to users' wallets through WalletConnect:

```python
async def send_transaction_for_signing(wallet_address: str, serialized_transaction: str) -> Dict[str, Any]:
    # Implementation using WalletConnect
    
    # Get user and session information
    user = await get_user_by_wallet_address(wallet_address)
    session_id = user.wallet_session_id
    
    # Send transaction to wallet via WalletConnect
    from walletconnect_manager import wallet_connect_manager
    signing_result = await wallet_connect_manager.send_transaction(
        user_id=user.id,
        serialized_transaction=serialized_transaction
    )
    
    # Process signature result
    # ...
```

#### Solana Network Submission
The `submit_signed_transaction()` function now submits signed transactions to the Solana network:

```python
async def submit_signed_transaction(signature: str) -> Dict[str, Any]:
    # Implementation using Solana RPC
    
    # Connect to Solana network
    solana_client = Client("https://api.mainnet-beta.solana.com")
    
    # Decode and submit transaction
    signed_tx_data = base58.b58decode(signature)
    response = await solana_client.send_raw_transaction(
        signed_tx_data,
        opts=send_opts
    )
    
    # Wait for confirmation
    tx_signature = response["result"]
    confirm_response = await solana_client.confirm_transaction(
        tx_signature,
        commitment="finalized"
    )
    
    # Return transaction details
    # ...
```

### 4. Database Integration

#### Investment Logging
The `create_investment_log()` function has been updated to record all transaction details in the database:

```python
async def create_investment_log(user_id: int, pool_id: str, amount: float, tx_hash: str, status: str,
                           token_a_amount: float = None, token_b_amount: float = None, 
                           apr_at_entry: float = None) -> bool:
    # Implementation using database models
    from models import InvestmentLog, db
    
    # Create database record
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
    # ...
```

#### User Wallet Management
New functions have been added to manage user wallet connections:

```python
async def get_user_by_wallet_address(wallet_address: str) -> Optional[Any]:
    # Get user from database by wallet address
    # ...

def get_user_id_from_wallet(wallet_address: str) -> Optional[int]:
    # Get user ID from wallet address
    # ...

async def update_user_last_tx(wallet_address: str, tx_hash: str) -> bool:
    # Update user's last transaction hash
    # ...
```

## Technical Implementation Details

### Transaction Data Format

The Raydium protocol requires specific data structures for LP deposit transactions:

1. **Instruction Data**: Binary packed data with instruction index and parameters:
   ```python
   data = bytes([
       1,  # Instruction index for addLiquidity
       *list(token_a_lamports.to_bytes(8, 'little')),
       *list(token_b_lamports.to_bytes(8, 'little')),
       # Additional parameters
   ])
   ```

2. **Account List**: Ordered list of accounts needed for the transaction:
   ```python
   accounts = [
       # User accounts
       AccountMeta(pubkey=user_wallet, is_signer=True, is_writable=True),
       
       # Pool accounts
       AccountMeta(pubkey=pool_token_a_account, is_signer=False, is_writable=True),
       AccountMeta(pubkey=pool_token_b_account, is_signer=False, is_writable=True),
       AccountMeta(pubkey=lp_mint, is_signer=False, is_writable=True),
       
       # User token accounts
       AccountMeta(pubkey=user_token_a_account, is_signer=False, is_writable=True),
       AccountMeta(pubkey=user_token_b_account, is_signer=False, is_writable=True),
       AccountMeta(pubkey=user_lp_token_account, is_signer=False, is_writable=True),
       
       # Program accounts
       AccountMeta(pubkey=pool_authority, is_signer=False, is_writable=False),
       AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
   ]
   ```

### Token Amount Calculation

The token amount calculation process follows these steps:

1. Fetch current token prices from the SolPool API
2. Get the optimal token ratio for the pool
3. Split the investment amount according to the pool ratio
4. Convert USD amounts to token amounts based on current prices
5. Calculate the expected price impact of the transaction

### Transaction Flow

The complete transaction flow is as follows:

1. User initiates investment through the Telegram bot
2. Bot retrieves pool metadata and calculates token amounts
3. Bot builds a Raydium LP deposit transaction
4. Transaction is sent to user's wallet via WalletConnect
5. User approves the transaction in their wallet
6. Signed transaction is submitted to the Solana network
7. Bot verifies transaction confirmation and updates database
8. User receives confirmation and transaction details

## Future Enhancements

1. **Transaction Monitoring**: Add real-time monitoring of transaction status
2. **Slippage Protection**: Implement slippage tolerance settings for users
3. **Multi-pool Investments**: Support investing in multiple pools in a single transaction
4. **Investment Optimization**: Add AI-driven optimization of investment amounts
5. **Transaction History**: Implement detailed transaction history for users

## Technical Notes

1. The transaction building uses the Solana PublicKey, Transaction, and TransactionInstruction classes
2. Token amounts are converted to lamports (smallest denomination) using the appropriate decimals for each token
3. The WalletConnect integration sends Base64-encoded serialized transactions to users' wallets
4. Transaction submissions use the Solana RPC API with configurable confirmation levels
5. All transactions are recorded in the database for tracking and analytics