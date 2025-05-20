#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart Invest execution module for FiLot Telegram bot
Handles the investment execution flow with wallet integration
"""

import logging
import re
from typing import Dict, Any, Optional, List, Union, Tuple
from decimal import Decimal

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, filters, CallbackQueryHandler
)

from wallet_actions import (
    get_wallet_status, connect_wallet, disconnect_wallet,
    initiate_wallet_connection, check_connection_status,
    execute_investment, check_transaction_status,
    WalletConnectionStatus
)
from solpool_api_client import get_pool_detail, simulate_investment
from models import User, db

# Configure logging
logger = logging.getLogger(__name__)

# Define conversation states
AMOUNT_INPUT = 1
CONFIRM_INVESTMENT = 2
PROCESSING_TRANSACTION = 3

# Regular expressions
INVEST_POOL_PATTERN = r'^invest_now:(?P<pool_id>.+)$'
CONFIRM_PATTERN = r'^confirm_invest:(?P<pool_id>.+):(?P<amount>\d+\.?\d*)$'
CHECK_TX_PATTERN = r'^check_tx:(?P<tx_hash>.+)$'

async def start_investment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the investment process for a specific pool
    
    This is triggered by the "Invest Now" button on pool details
    """
    query = update.callback_query
    if not query:
        return ConversationHandler.END
        
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Extract pool ID from callback data
    match = re.match(INVEST_POOL_PATTERN, query.data)
    if not match:
        logger.error(f"Invalid invest pattern: {query.data}")
        return ConversationHandler.END
        
    pool_id = match.group("pool_id")
    logger.info(f"User {user_id} starting investment in pool: {pool_id}")
    
    # Store pool_id in user data for the conversation
    context.user_data["invest_pool_id"] = pool_id
    
    # Check if user has a connected wallet
    wallet_status, wallet_address = get_wallet_status(user_id)
    
    if wallet_status != WalletConnectionStatus.CONNECTED:
        # User needs to connect wallet first
        keyboard = [
            [InlineKeyboardButton("🔌 Connect Wallet", callback_data="walletconnect")],
            [InlineKeyboardButton("⬅️ Back to Pool", callback_data=f"pool:{pool_id}")]
        ]
        
        await query.edit_message_text(
            "*💰 Invest in Pool*\n\n"
            "You need to connect your wallet before you can invest in this pool.\n\n"
            "Click 'Connect Wallet' to secure your wallet connection.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return ConversationHandler.END
    
    # User has a wallet connected, get pool details
    try:
        pool = get_pool_detail(pool_id)
        
        if not pool:
            # Pool not found
            keyboard = [[InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]]
            
            await query.edit_message_text(
                "*❌ Pool Not Found*\n\n"
                f"Sorry, I couldn't find details for the requested pool.\n\n"
                f"The pool may have been deprecated or there might be a temporary issue with the data provider.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            
            return ConversationHandler.END
            
        # Store pool info in user data for the conversation
        context.user_data["pool_info"] = pool
        
        # Format pool name
        token_a = pool.get('token_a_symbol', 'Unknown')
        token_b = pool.get('token_b_symbol', 'Unknown')
        pool_name = f"{token_a}/{token_b}"
        
        # Show investment amount input prompt
        keyboard = [
            [
                InlineKeyboardButton("$50", callback_data=f"preset_amount:50"),
                InlineKeyboardButton("$100", callback_data=f"preset_amount:100"),
                InlineKeyboardButton("$500", callback_data=f"preset_amount:500")
            ],
            [InlineKeyboardButton("⬅️ Cancel", callback_data=f"pool:{pool_id}")]
        ]
        
        await query.edit_message_text(
            f"*💰 Invest in {pool_name} Pool*\n\n"
            f"How much would you like to invest?\n\n"
            f"• You can select a preset amount below\n"
            f"• Or type any amount (e.g., '250' for $250)\n"
            f"• Your wallet address: `{wallet_address[:8]}...{wallet_address[-4:]}`\n\n"
            f"*Current Pool Stats:*\n"
            f"• APR: *{pool.get('apr_24h', 0):.2f}%*\n"
            f"• TVL: *${pool.get('tvl', 0):,.2f}*\n"
            f"• Fee: *{pool.get('fee', 0):.2f}%*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return AMOUNT_INPUT
        
    except Exception as e:
        logger.error(f"Error starting investment for pool {pool_id}: {e}")
        
        # Error handling
        keyboard = [[InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]]
        
        await query.edit_message_text(
            "*❌ Investment Error*\n\n"
            "Sorry, I encountered an error while retrieving pool information.\n\n"
            "Please try again later.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return ConversationHandler.END

async def handle_preset_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle preset investment amount selection
    """
    query = update.callback_query
    if not query:
        return ConversationHandler.END
        
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Extract amount from callback data
    amount_match = re.match(r'^preset_amount:(\d+)$', query.data)
    if not amount_match:
        logger.error(f"Invalid preset amount format: {query.data}")
        return ConversationHandler.END
        
    # Get the selected amount and pool info
    amount = float(amount_match.group(1))
    pool_id = context.user_data.get("invest_pool_id")
    pool_info = context.user_data.get("pool_info", {})
    
    if not pool_id or not pool_info:
        logger.error(f"Missing pool information in user data for user {user_id}")
        return ConversationHandler.END
    
    # Store the amount in user data
    context.user_data["invest_amount"] = amount
    
    # Process to confirmation step
    return await show_investment_confirmation(update, context, amount)

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle custom investment amount input from user
    """
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Get the amount from the message text
    try:
        # Parse the amount, handling different formats
        text = update.message.text.strip()
        
        # Remove currency symbols and commas
        cleaned_text = text.replace('$', '').replace(',', '').strip()
        
        # Convert to float
        amount = float(cleaned_text)
        
        # Validate the amount
        if amount <= 0:
            await update.message.reply_text(
                "*❌ Invalid Amount*\n\n"
                "Please enter a positive amount greater than zero.",
                parse_mode="MarkdownV2"
            )
            return AMOUNT_INPUT
            
        if amount > 10000:
            await update.message.reply_text(
                "*⚠️ Large Investment*\n\n"
                "For security reasons, the maximum investment through the bot is limited to $10,000.\n\n"
                "Please enter a smaller amount or use Raydium directly for larger investments.",
                parse_mode="MarkdownV2"
            )
            return AMOUNT_INPUT
        
        # Store the amount in user data
        context.user_data["invest_amount"] = amount
        
        # Get the pool info from user data
        pool_id = context.user_data.get("invest_pool_id")
        pool_info = context.user_data.get("pool_info", {})
        
        if not pool_id or not pool_info:
            logger.error(f"Missing pool information in user data for user {user_id}")
            
            await update.message.reply_text(
                "*❌ Session Error*\n\n"
                "Sorry, your investment session has expired.\n\n"
                "Please start over by selecting a pool from the list.",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")
                ]])
            )
            return ConversationHandler.END
        
        # Process to confirmation step
        # Instead of editing the message, send a new one since this is a text message handler
        token_a = pool_info.get('token_a_symbol', 'Unknown')
        token_b = pool_info.get('token_b_symbol', 'Unknown')
        pool_name = f"{token_a}/{token_b}"
        
        # Get wallet status
        wallet_status, wallet_address = get_wallet_status(user_id)
        
        # Simulate investment to get expected returns
        try:
            simulation = simulate_investment(pool_id, amount)
            
            # Format simulation results
            token_a_amount = simulation.get('token_a_amount', 0)
            token_b_amount = simulation.get('token_b_amount', 0)
            expected_apr = simulation.get('expected_apr', pool_info.get('apr_24h', 0))
            daily_yield = (amount * expected_apr / 100) / 365
            
            simulation_text = (
                f"*Expected Investment:*\n"
                f"• *{token_a_amount:.4f} {token_a}*\n"
                f"• *{token_b_amount:.4f} {token_b}*\n\n"
                f"*Expected Daily Yield:* *${daily_yield:.2f}*\n"
                f"*Expected APR:* *{expected_apr:.2f}%*\n\n"
            )
        except Exception as e:
            logger.error(f"Error simulating investment: {e}")
            simulation_text = ""
        
        keyboard = [
            [InlineKeyboardButton("✅ Confirm Investment", callback_data=f"confirm_invest:{pool_id}:{amount}")],
            [InlineKeyboardButton("🔄 Change Amount", callback_data=f"invest_now:{pool_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"pool:{pool_id}")]
        ]
        
        await update.message.reply_text(
            f"*💰 Confirm Investment in {pool_name}*\n\n"
            f"You are about to invest *${amount:.2f}* in the {pool_name} liquidity pool.\n\n"
            f"{simulation_text}"
            f"*Wallet Address:* `{wallet_address[:8]}...{wallet_address[-4:]}`\n\n"
            f"Please confirm to proceed with this investment.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return CONFIRM_INVESTMENT
        
    except ValueError:
        # Invalid amount format
        await update.message.reply_text(
            "*❌ Invalid Amount*\n\n"
            "Please enter a valid number (e.g., '100' or '250.50').",
            parse_mode="MarkdownV2"
        )
        return AMOUNT_INPUT
        
    except Exception as e:
        logger.error(f"Error processing investment amount: {e}")
        
        await update.message.reply_text(
            "*❌ Processing Error*\n\n"
            "Sorry, I encountered an error while processing your investment amount.\n\n"
            "Please try again or start over.",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")
            ]])
        )
        return ConversationHandler.END

async def show_investment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, amount: float) -> int:
    """
    Show investment confirmation with simulated returns
    """
    query = update.callback_query
    if not query:
        return ConversationHandler.END
    
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Get pool info from user data
    pool_id = context.user_data.get("invest_pool_id")
    pool_info = context.user_data.get("pool_info", {})
    
    if not pool_id or not pool_info:
        logger.error(f"Missing pool information in user data for user {user_id}")
        
        await query.edit_message_text(
            "*❌ Session Error*\n\n"
            "Sorry, your investment session has expired.\n\n"
            "Please start over by selecting a pool from the list.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")
            ]]),
            parse_mode="MarkdownV2"
        )
        return ConversationHandler.END
    
    # Format pool name
    token_a = pool_info.get('token_a_symbol', 'Unknown')
    token_b = pool_info.get('token_b_symbol', 'Unknown')
    pool_name = f"{token_a}/{token_b}"
    
    # Get wallet status
    wallet_status, wallet_address = get_wallet_status(user_id)
    
    # Simulate investment to get expected returns
    try:
        simulation = simulate_investment(pool_id, amount)
        
        # Format simulation results
        token_a_amount = simulation.get('token_a_amount', 0)
        token_b_amount = simulation.get('token_b_amount', 0)
        expected_apr = simulation.get('expected_apr', pool_info.get('apr_24h', 0))
        daily_yield = (amount * expected_apr / 100) / 365
        
        simulation_text = (
            f"*Expected Investment:*\n"
            f"• *{token_a_amount:.4f} {token_a}*\n"
            f"• *{token_b_amount:.4f} {token_b}*\n\n"
            f"*Expected Daily Yield:* *${daily_yield:.2f}*\n"
            f"*Expected APR:* *{expected_apr:.2f}%*\n\n"
        )
    except Exception as e:
        logger.error(f"Error simulating investment: {e}")
        simulation_text = ""
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Investment", callback_data=f"confirm_invest:{pool_id}:{amount}")],
        [InlineKeyboardButton("🔄 Change Amount", callback_data=f"invest_now:{pool_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"pool:{pool_id}")]
    ]
    
    await query.edit_message_text(
        f"*💰 Confirm Investment in {pool_name}*\n\n"
        f"You are about to invest *${amount:.2f}* in the {pool_name} liquidity pool.\n\n"
        f"{simulation_text}"
        f"*Wallet Address:* `{wallet_address[:8]}...{wallet_address[-4:]}`\n\n"
        f"Please confirm to proceed with this investment.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )
    
    return CONFIRM_INVESTMENT

async def handle_investment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process investment confirmation and execute the transaction
    """
    query = update.callback_query
    if not query:
        return ConversationHandler.END
        
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Extract pool ID and amount from callback data
    match = re.match(CONFIRM_PATTERN, query.data)
    if not match:
        logger.error(f"Invalid confirmation pattern: {query.data}")
        return ConversationHandler.END
        
    pool_id = match.group("pool_id")
    amount = float(match.group("amount"))
    
    logger.info(f"User {user_id} confirmed investment of ${amount} in pool: {pool_id}")
    
    # Get pool info from user data
    pool_info = context.user_data.get("pool_info", {})
    
    # Format pool name
    token_a = pool_info.get('token_a_symbol', 'Unknown')
    token_b = pool_info.get('token_b_symbol', 'Unknown')
    pool_name = f"{token_a}/{token_b}"
    
    # Get wallet status and address
    wallet_status, wallet_address = get_wallet_status(user_id)
    
    if wallet_status != WalletConnectionStatus.CONNECTED or not wallet_address:
        await query.edit_message_text(
            "*❌ Wallet Connection Error*\n\n"
            "Your wallet is no longer connected. Please reconnect your wallet and try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔌 Connect Wallet", callback_data="walletconnect")
            ]]),
            parse_mode="MarkdownV2"
        )
        return ConversationHandler.END
    
    # Show processing message
    await query.edit_message_text(
        f"*⏳ Processing Investment*\n\n"
        f"I'm processing your investment of *${amount:.2f}* in the {pool_name} pool.\n\n"
        f"Please approve the transaction in your wallet app when prompted.",
        reply_markup=InlineKeyboardMarkup([]),
        parse_mode="MarkdownV2"
    )
    
    # Execute the investment
    try:
        # Call the investment execution function
        result = execute_investment(wallet_address, pool_id, amount)
        
        if result.get("success", False):
            # Transaction successful
            tx_hash = result.get("transaction_hash", "unknown")
            tx_link = result.get("tx_link", f"https://solscan.io/tx/{tx_hash}")
            
            # Store transaction information
            context.user_data["tx_hash"] = tx_hash
            context.user_data["tx_link"] = tx_link
            
            # Present success message with transaction link
            keyboard = [
                [InlineKeyboardButton("🔍 View Transaction", url=tx_link)],
                [InlineKeyboardButton("📊 Check Status", callback_data=f"check_tx:{tx_hash}")],
                [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
            ]
            
            await query.edit_message_text(
                f"*✅ Investment Initiated*\n\n"
                f"Your investment of *${amount:.2f}* in the {pool_name} pool has been initiated.\n\n"
                f"*Transaction Hash:* `{tx_hash[:10]}...{tx_hash[-6:]}`\n\n"
                f"Please wait for the transaction to be confirmed on the Solana blockchain. "
                f"You can check the status using the buttons below.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            
            return PROCESSING_TRANSACTION
            
        else:
            # Transaction failed
            error = result.get("error", "Unknown error")
            message = result.get("message", "Failed to execute investment. Please try again later.")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data=f"invest_now:{pool_id}")],
                [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
            ]
            
            await query.edit_message_text(
                f"*❌ Investment Failed*\n\n"
                f"I couldn't complete your investment in the {pool_name} pool.\n\n"
                f"*Error:* {message}\n\n"
                f"You can try again or go back to the pool list.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error executing investment: {e}")
        
        # Error fallback
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data=f"invest_now:{pool_id}")],
            [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
        ]
        
        await query.edit_message_text(
            f"*❌ Investment Error*\n\n"
            f"I encountered an error while processing your investment in the {pool_name} pool.\n\n"
            f"*Error:* An unexpected error occurred. Please try again later.\n\n"
            f"You can try again or go back to the pool list.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return ConversationHandler.END

async def handle_check_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Check the status of a transaction
    """
    query = update.callback_query
    if not query:
        return ConversationHandler.END
        
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Extract transaction hash from callback data
    match = re.match(CHECK_TX_PATTERN, query.data)
    if not match:
        logger.error(f"Invalid check transaction pattern: {query.data}")
        return ConversationHandler.END
        
    tx_hash = match.group("tx_hash")
    
    logger.info(f"User {user_id} checking transaction status: {tx_hash}")
    
    # Get transaction status
    try:
        # Call transaction status check function
        result = check_transaction_status(tx_hash)
        
        # Get pool info from user data for display
        pool_info = context.user_data.get("pool_info", {})
        amount = context.user_data.get("invest_amount", 0)
        
        # Format pool name
        token_a = pool_info.get('token_a_symbol', 'Unknown')
        token_b = pool_info.get('token_b_symbol', 'Unknown')
        pool_name = f"{token_a}/{token_b}" if token_a != 'Unknown' and token_b != 'Unknown' else "liquidity pool"
        
        if result.get("success", False):
            # Get transaction details
            status = result.get("status", "unknown")
            confirmations = result.get("confirmations", 0)
            tx_link = result.get("tx_link", f"https://solscan.io/tx/{tx_hash}")
            
            if status == "confirmed":
                # Transaction confirmed
                keyboard = [
                    [InlineKeyboardButton("🔍 View Transaction", url=tx_link)],
                    [InlineKeyboardButton("💼 My Investments", callback_data="my_investments")],
                    [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
                ]
                
                await query.edit_message_text(
                    f"*✅ Investment Confirmed*\n\n"
                    f"Your investment of *${amount:.2f}* in the {pool_name} pool has been confirmed on the blockchain!\n\n"
                    f"*Transaction Hash:* `{tx_hash[:10]}...{tx_hash[-6:]}`\n"
                    f"*Confirmations:* {confirmations}\n\n"
                    f"You can now view this position in 'My Investments' or explore more pools.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
                
                return ConversationHandler.END
                
            elif status == "confirming":
                # Transaction still confirming
                keyboard = [
                    [InlineKeyboardButton("🔍 View Transaction", url=tx_link)],
                    [InlineKeyboardButton("🔄 Check Again", callback_data=f"check_tx:{tx_hash}")],
                    [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
                ]
                
                await query.edit_message_text(
                    f"*⏳ Investment Confirming*\n\n"
                    f"Your investment of *${amount:.2f}* in the {pool_name} pool is still being confirmed.\n\n"
                    f"*Transaction Hash:* `{tx_hash[:10]}...{tx_hash[-6:]}`\n"
                    f"*Confirmations:* {confirmations}\n\n"
                    f"Please check again in a few moments.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
                
                return PROCESSING_TRANSACTION
                
            else:
                # Other status (failed, etc.)
                keyboard = [
                    [InlineKeyboardButton("🔍 View Transaction", url=tx_link)],
                    [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
                ]
                
                await query.edit_message_text(
                    f"*ℹ️ Investment Status: {status.capitalize()}*\n\n"
                    f"Your investment of *${amount:.2f}* in the {pool_name} pool has status: *{status}*.\n\n"
                    f"*Transaction Hash:* `{tx_hash[:10]}...{tx_hash[-6:]}`\n\n"
                    f"You can view the transaction details on Solscan for more information.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
                
                return ConversationHandler.END
                
        else:
            # Error getting transaction status
            error = result.get("error", "Unknown error")
            
            keyboard = [
                [InlineKeyboardButton("🔄 Check Again", callback_data=f"check_tx:{tx_hash}")],
                [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
            ]
            
            await query.edit_message_text(
                f"*⚠️ Status Check Error*\n\n"
                f"I couldn't retrieve the status of your investment transaction.\n\n"
                f"*Transaction Hash:* `{tx_hash[:10]}...{tx_hash[-6:]}`\n"
                f"*Error:* {error}\n\n"
                f"This could be due to network congestion. Please try checking again in a few moments.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            
            return PROCESSING_TRANSACTION
            
    except Exception as e:
        logger.error(f"Error checking transaction status: {e}")
        
        # Error fallback
        keyboard = [
            [InlineKeyboardButton("🔄 Check Again", callback_data=f"check_tx:{tx_hash}")],
            [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
        ]
        
        await query.edit_message_text(
            f"*⚠️ Status Check Error*\n\n"
            f"I encountered an error while checking your transaction status.\n\n"
            f"*Transaction Hash:* `{tx_hash[:10]}...{tx_hash[-6:]}`\n\n"
            f"Please try checking again in a few moments.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return PROCESSING_TRANSACTION

async def cancel_investment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the investment process
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} cancelled investment process")
        
        # Get pool id from user data
        pool_id = context.user_data.get("invest_pool_id")
        
        if pool_id:
            # Return to pool details
            await query.edit_message_text(
                "*❌ Investment Cancelled*\n\n"
                "You've cancelled the investment process.\n\n"
                "Returning to pool details...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Pool", callback_data=f"pool:{pool_id}")
                ]]),
                parse_mode="MarkdownV2"
            )
        else:
            # Return to pools list
            await query.edit_message_text(
                "*❌ Investment Cancelled*\n\n"
                "You've cancelled the investment process.\n\n"
                "Returning to pool list...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")
                ]]),
                parse_mode="MarkdownV2"
            )
    
    # Clear user data
    if 'invest_pool_id' in context.user_data:
        del context.user_data['invest_pool_id']
    if 'pool_info' in context.user_data:
        del context.user_data['pool_info']
    if 'invest_amount' in context.user_data:
        del context.user_data['invest_amount']
    
    return ConversationHandler.END

def get_investment_conversation_handler() -> ConversationHandler:
    """
    Create and return the investment conversation handler.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_investment, pattern=INVEST_POOL_PATTERN)
        ],
        states={
            AMOUNT_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input),
                CallbackQueryHandler(handle_preset_amount, pattern=r'^preset_amount:\d+$'),
                CallbackQueryHandler(cancel_investment, pattern=r'^pool:.+$')
            ],
            CONFIRM_INVESTMENT: [
                CallbackQueryHandler(handle_investment_confirmation, pattern=CONFIRM_PATTERN),
                CallbackQueryHandler(start_investment, pattern=INVEST_POOL_PATTERN),  # Change amount
                CallbackQueryHandler(cancel_investment, pattern=r'^pool:.+$')
            ],
            PROCESSING_TRANSACTION: [
                CallbackQueryHandler(handle_check_transaction, pattern=CHECK_TX_PATTERN),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=r'^pools$'),  # Back to pools
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=r'^my_investments$')  # My investments
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel_investment, pattern=r'^pool:.+$'),
            CommandHandler("cancel", cancel_investment)
        ],
        name="investment_conversation",
        persistent=False,
        conversation_timeout=1800  # 30 minutes timeout
    )