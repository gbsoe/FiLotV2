# FiLot User Transaction Guide

## Introduction

This guide explains the investment process in FiLot, the agentic AI-powered Telegram bot for cryptocurrency investments. FiLot provides a secure, user-friendly way to invest in Solana liquidity pools with comprehensive safety features and detailed information at every step.

## Starting an Investment

### One-Command Investment

You can start an investment in two ways:

1. Using the `/smart_invest` command
2. Using the "🧠 Smart Invest" button in the main menu

### Pool Selection

FiLot will analyze available pools and recommend the best options based on:
- Current APR (Annual Percentage Rate)
- Total Value Locked (TVL)
- SolPool prediction scores
- FilotSense sentiment analysis
- Your personal risk profile

Each recommendation includes:
- Pool name (Token A/Token B)
- Current APR
- Risk assessment
- Confidence score
- Expected returns

## Investment Process

### Step 1: Select Investment Amount

After selecting a pool, you'll be prompted to enter your investment amount in USD. You can:
- Type a custom amount (e.g., "100")
- Use preset buttons ($10, $50, $100, $500)

FiLot will verify your amount is within the pool's limits.

### Step 2: Initial Review

You'll see a summary of your investment with basic details:
- Pool name
- Investment amount
- Current APR
- Estimated returns

### Step 3: Detailed Confirmation

Before executing the transaction, FiLot shows comprehensive details:

```
🔎 Investment Details

You're about to invest $100.00 in the SOL/USDC pool.

Token Split:
• 0.345678 SOL
• 52.456789 USDC

Transaction Details:
• Pool APR: 24.56%
• Price Impact: 0.15%
• Slippage Tolerance: 0.50%

Please confirm to proceed with the transaction.
```

This screen includes important safety information:
- **Token Split**: Exact amounts of each token for your investment
- **Pool APR**: Current annual percentage rate
- **Price Impact**: How much your transaction will affect the pool price
- **Slippage Tolerance**: Your protection against price movements (default 0.5%)

### Step 4: Wallet Connection

If your wallet isn't already connected, FiLot will guide you through the secure connection process using WalletConnect v2:
1. Scan the QR code with your mobile wallet app
2. Approve the connection request in your wallet

### Step 5: Transaction Approval

After confirming in FiLot:
1. Your wallet will receive a transaction request
2. Review all transaction details in your wallet app
3. Approve the transaction to execute the investment

### Step 6: Transaction Processing

FiLot will show a processing screen while your transaction is being confirmed on the Solana blockchain:

```
⏳ Processing Investment

I'm processing your investment of $100.00 in the SOL/USDC pool.

Please approve the transaction in your wallet app when prompted.
```

### Step 7: Transaction Confirmation

Once submitted, you'll see detailed transaction information:

```
✅ Investment Initiated

Your investment of $100.00 in the SOL/USDC pool has been initiated.

Token Amounts:
• 0.345678 SOL
• 52.456789 USDC

Transaction Details:
• Transaction Hash: BvYkR3G...4fDs9J
• Price Impact: 0.15%
• Slippage Protection: 0.50%
• Expected LP Tokens: 0.123456

Please wait for the transaction to be confirmed on the Solana blockchain. You can check the status using the buttons below.
```

From this screen, you can:
- View the transaction on Solscan
- Check the transaction status
- Return to the pools list

## Transaction Status Checking

After submitting a transaction, you can check its status at any time:

1. Click the "📊 Check Status" button
2. FiLot will query the Solana blockchain for confirmation status
3. You'll see the current status (confirming, confirmed, or failed)

### Status Screens

#### Confirming
```
⏳ Investment Confirming

Your investment of $100.00 in the SOL/USDC pool is still being confirmed.

Transaction Hash: BvYkR3G...4fDs9J
Confirmations: 23

Please check again in a few moments.
```

#### Confirmed
```
✅ Investment Confirmed

Your investment of $100.00 in the SOL/USDC pool has been confirmed on the blockchain!

Transaction Hash: BvYkR3G...4fDs9J
Confirmations: 32

You can now view this position in 'My Investments' or explore more pools.
```

## Investment Safety Features

FiLot includes advanced safety features to protect your investments:

### Pre-Transaction Checks

Before allowing a transaction, FiLot verifies:
- Wallet is properly connected
- Pool is active and valid
- Investment amount is within acceptable limits
- Price impact is not excessive

### Slippage Protection

All transactions include automatic slippage protection (default 0.5%) to protect against price movements during confirmation.

### Price Impact Warnings

If your transaction would significantly impact the pool price, FiLot will warn you and may prevent the transaction to protect your investment.

### Detailed Error Handling

If any issues occur, FiLot provides clear, user-friendly error messages with:
- Description of the issue
- Suggested next steps
- Options to retry or choose a different pool

## Understanding Your Investment

### Liquidity Pool Basics

When you invest in a liquidity pool, you:
1. Provide both tokens in the pool pair
2. Receive LP (Liquidity Provider) tokens representing your share
3. Earn fees from trades that happen in the pool

### Key Metrics Explained

- **APR (Annual Percentage Rate)**: Estimated yearly return based on current trading volume and fees
- **TVL (Total Value Locked)**: Total value of assets in the pool
- **Price Impact**: How much your transaction will move the pool price
- **Slippage**: The difference between expected execution price and actual price
- **LP Tokens**: Tokens representing your share of the pool

## Tracking Your Investments

After investing, you can track your positions:

1. Use the "💼 My Investments" command or button
2. View all current positions with performance metrics
3. Get AI-powered recommendations on when to exit positions

## Tips for Successful Investing

1. **Start small** to get comfortable with the process
2. **Check price impact** carefully - smaller pools have higher impact
3. **Review all details** before confirming transactions
4. **Diversify** across multiple pools for better risk management
5. **Use Smart Invest** for AI-driven recommendations based on your risk profile

## Getting Help

If you encounter any issues during the investment process, you can:
- Use the `/help` command for general guidance
- Contact support through the "📞 Support" button
- Join the FiLot community channel for peer assistance

## Security Best Practices

1. **Always verify transactions** in both FiLot and your wallet app
2. **Never share your wallet seed phrase** with anyone
3. **Check transaction details** carefully before approving
4. **Set reasonable investment limits** for your risk tolerance
5. **Disconnect your wallet** when not actively using FiLot