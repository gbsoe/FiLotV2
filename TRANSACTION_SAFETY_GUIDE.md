# FiLot Transaction Safety Guide

## Overview

This guide details the comprehensive transaction safety features implemented in FiLot to ensure secure and reliable cryptocurrency investments through the Telegram bot interface. These features are designed to protect users from common DeFi transaction issues such as slippage, price impact, and transaction failures.

## Slippage Protection

### What is Slippage?

Slippage refers to the difference between the expected price of a trade and the actual price at which it executes. In volatile DeFi markets, prices can change during the time it takes for a transaction to be confirmed on the blockchain.

### FiLot's Slippage Protection Features

1. **Default Slippage Tolerance**: 
   - FiLot implements a conservative 0.5% (50 basis points) default slippage tolerance
   - This protects users from minor price movements during transaction confirmation

2. **Minimum LP Token Calculation**:
   ```python
   # Apply slippage to calculate minimum acceptable LP tokens
   min_lp_tokens = expected_lp_tokens * (1 - (slippage_tolerance / 100))
   ```

3. **Transaction Data Structure**:
   - Slippage protection is encoded directly into the Raydium transaction data
   - The instruction data includes the minimum acceptable LP tokens:
   ```python
   data = bytes([
       1,  # Instruction index for addLiquidity
       *list(token_a_lamports.to_bytes(8, 'little')),
       *list(token_b_lamports.to_bytes(8, 'little')),
       *list(min_lp_lamports.to_bytes(8, 'little')),  # Slippage protection
   ])
   ```

4. **User Interface Display**:
   - Slippage tolerance is clearly shown in transaction confirmation screens
   - Users can see exactly how their investment is protected

## Pre-Transaction Validation

FiLot implements comprehensive pre-transaction checks to prevent failed transactions and protect users:

### 1. Wallet Connection Verification

```python
# Check wallet connection status
user = await get_user_by_wallet_address(wallet_address)
if not user:
    return {
        "success": False,
        "error": "Wallet not found",
        "message": "No user found with the provided wallet address. Please reconnect your wallet."
    }
    
if user.connection_status != "connected" or not user.wallet_session_id:
    return {
        "success": False,
        "error": "Wallet not connected",
        "message": "Your wallet is not properly connected. Please reconnect your wallet and try again."
    }
```

### 2. Pool Validity Checks

```python
# Check if pool exists and is active
pool_data = await fetch_pool_metadata(pool_id)
if not pool_data:
    return {
        "success": False,
        "error": "Pool not found",
        "message": "Could not retrieve pool information. The pool may no longer be active."
    }

if pool_data.get('status') == 'inactive':
    return {
        "success": False,
        "error": "Inactive pool",
        "message": "This liquidity pool is currently inactive. Please choose another pool."
    }
```

### 3. Investment Amount Limits

```python
# Check investment amount limits
min_investment = pool_data.get('min_investment_usd', 1.0)  # Default $1 minimum
max_investment = pool_data.get('max_investment_usd', 1000000.0)  # Default $1M maximum

if amount < min_investment:
    return {
        "success": False,
        "error": "Investment amount too low",
        "message": f"Minimum investment amount for this pool is ${min_investment}."
    }
    
if amount > max_investment:
    return {
        "success": False,
        "error": "Investment amount too high",
        "message": f"Maximum investment amount for this pool is ${max_investment}."
    }
```

### 4. Price Impact Analysis

```python
# Check transaction size limits and price impact
price_impact = token_amounts.get('price_impact', 0.0)
max_safe_impact = 5.0  # 5% is generally considered the safe maximum

if price_impact > max_safe_impact:
    return {
        "success": False, 
        "error": "High price impact",
        "message": f"This transaction would have a high price impact of {price_impact:.2f}%. Try a smaller amount."
    }
```

## Two-Step Confirmation Process

FiLot implements a two-step confirmation process to ensure users understand all aspects of their transaction before execution:

### Step 1: Initial Confirmation with Details

```python
# Show detailed confirmation with token amounts and slippage
confirm_keyboard = [
    [InlineKeyboardButton("✅ Confirm Transaction", callback_data=f"execute_invest:{pool_id}:{amount}")],
    [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
]

await query.edit_message_text(
    f"*🔎 Investment Details*\n\n"
    f"You're about to invest *${amount:.2f}* in the {pool_name_safe} pool.\n\n"
    f"*Token Split:*\n"
    f"• {token_a_amount:.6f} {token_a_safe}\n"
    f"• {token_b_amount:.6f} {token_b_safe}\n\n"
    f"*Transaction Details:*\n"
    f"• Pool APR: {pool_apr:.2f}%\n"
    f"• Price Impact: {price_impact:.2f}%\n"
    f"• Slippage Tolerance: {slippage_tolerance:.2f}%\n\n"
    f"Please confirm to proceed with the transaction.",
    reply_markup=InlineKeyboardMarkup(confirm_keyboard),
    parse_mode="MarkdownV2"
)
```

### Step 2: Final Transaction Execution

After confirming in the bot, users must also approve the transaction in their wallet, providing a second layer of protection.

## Comprehensive Error Handling

FiLot implements robust error handling to ensure a smooth user experience even when issues occur:

### 1. User Wallet Rejection Handling

```python
# Special case for user rejection
if "rejected" in str(error_msg).lower() or "declined" in str(error_msg).lower():
    # Log the rejection in the database
    user_id = get_user_id_from_wallet(wallet_address)
    if user_id:
        await create_investment_log(
            user_id=user_id,
            pool_id=pool_id,
            amount=amount,
            tx_hash="user_rejected",
            status="failed",
            token_a_amount=token_a_amount,
            token_b_amount=token_b_amount,
            notes="User rejected transaction in wallet"
        )
    
    return {
        "success": False,
        "error": "Transaction rejected",
        "message": "You declined to sign the transaction in your wallet."
    }
```

### 2. RPC Error Handling

```python
# Log the failure in the database
user_id = get_user_id_from_wallet(wallet_address)
if user_id:
    await create_investment_log(
        user_id=user_id,
        pool_id=pool_id,
        amount=amount,
        tx_hash=signature,
        status="failed",
        token_a_amount=token_a_amount,
        token_b_amount=token_b_amount,
        notes=f"RPC error: {error_msg}"
    )
```

### 3. Exception Handling with Detailed Logs

```python
except Exception as submit_error:
    logger.error(f"Error submitting transaction: {submit_error}")
    
    # Log the exception in the database
    user_id = get_user_id_from_wallet(wallet_address)
    if user_id:
        await create_investment_log(
            user_id=user_id,
            pool_id=pool_id,
            amount=amount,
            tx_hash=signature,
            status="failed",
            token_a_amount=token_a_amount,
            token_b_amount=token_b_amount,
            notes=f"Exception: {str(submit_error)}"
        )
```

## Enhanced Transaction Logging

FiLot implements comprehensive transaction logging for audit purposes and user transparency:

### Extended Investment Log Model

```python
class InvestmentLog(db.Model):
    # Basic information
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    pool_id = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)  # Amount in USD
    tx_hash = Column(String(100), nullable=False)  # Transaction signature/hash
    status = Column(String(20), nullable=False)  # confirming, confirmed, failed, etc.
    
    # Token details
    token_a_amount = Column(Float, nullable=True)
    token_b_amount = Column(Float, nullable=True)
    token_a_symbol = Column(String(20), nullable=True)
    token_b_symbol = Column(String(20), nullable=True)
    
    # Investment parameters
    apr_at_entry = Column(Float, nullable=True)
    slippage_tolerance = Column(Float, nullable=True)
    price_impact = Column(Float, nullable=True)
    
    # LP token information
    expected_lp_tokens = Column(Float, nullable=True)
    min_lp_tokens = Column(Float, nullable=True)
    actual_lp_tokens = Column(Float, nullable=True)
    
    # Error tracking
    notes = Column(Text, nullable=True)  # For error descriptions or additional info
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Transaction Logging Function

```python
async def create_investment_log(user_id: int, pool_id: str, amount: float, tx_hash: str, status: str,
                            token_a_amount: float = None, token_b_amount: float = None, 
                            token_a_symbol: str = None, token_b_symbol: str = None,
                            apr_at_entry: float = None, slippage_tolerance: float = None,
                            price_impact: float = None, expected_lp_tokens: float = None,
                            min_lp_tokens: float = None, actual_lp_tokens: float = None,
                            notes: str = None) -> bool:
    """
    Create a log entry for an investment in the database with comprehensive details
    """
    # Implementation...
```

## Transaction Success Display

After successful transaction submission, FiLot displays comprehensive details to the user:

```python
# Create success message with comprehensive details
success_message = (
    f"*✅ Investment Initiated*\n\n"
    f"Your investment of *${amount:.2f}* in the {pool_name_safe} pool has been initiated\\.\n\n"
)

# Add token details
success_message += (
    f"*Token Amounts:*\n"
    f"• {token_a_amount:.6f} {token_a_safe}\n"
    f"• {token_b_amount:.6f} {token_b_safe}\n\n"
)

# Add transaction details
success_message += (
    f"*Transaction Details:*\n"
    f"• Transaction Hash: `{tx_hash[:10]}\\.\\.\\.{tx_hash[-6:]}`\n"
    f"• Price Impact: {price_impact:.2f}%\n"
    f"• Slippage Protection: {slippage_tolerance:.2f}%\n"
)

# Add LP token info if available
if expected_lp_tokens > 0:
    success_message += f"• Expected LP Tokens: {expected_lp_tokens:.6f}\n"
```

## Best Practices for Users

When using FiLot's production-grade transaction features, users should follow these best practices:

1. **Review all transaction details** before confirming, especially the token amounts and price impact
2. **Be cautious of high price impact** warnings, which indicate the transaction may significantly move the market
3. **Verify transaction details** in both the bot interface and your wallet before approving
4. **Check transaction status** after submission using the built-in status check feature
5. **Report any unusual behavior** using the support contact information

## Conclusion

FiLot's production-grade transaction safety features provide a secure, transparent, and user-friendly investment experience. By implementing slippage protection, comprehensive pre-checks, detailed information display, and robust error handling, FiLot sets a new standard for secure DeFi interactions through conversational interfaces.