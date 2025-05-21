#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Custom token search conversation handler for FiLot Telegram bot
Implements a conversation flow for searching liquidity pools by token symbol
"""

import logging
from typing import Dict, Any, Optional, List

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, filters, CallbackQueryHandler
)

from solpool_api_client import get_token_pools
from filotsense_api_client import get_sentiment_simple, get_prices_latest, get_token_sentiment, get_token_price

# Configure logging
logger = logging.getLogger(__name__)

# Define conversation states
WAITING_FOR_TOKEN = 1

async def start_token_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the token search conversation.
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} started custom token search")
        
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data="cancel_token_search")]]
        
        await query.edit_message_text(
            "*🔍 Custom Token Search*\n\n"
            "Please send me the symbol of the token you want to search for.\n\n"
            "For example, type `JTO` to search for Jupiter token pools.\n\n"
            "I'll find all liquidity pools containing this token.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        return WAITING_FOR_TOKEN
    
    return ConversationHandler.END

async def handle_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Process the token symbol input from the user.
    """
    # Get the token symbol from the user's message
    token_symbol = update.message.text.strip().upper()
    user_id = update.effective_user.id if update.effective_user else 0
    
    logger.info(f"User {user_id} searching for token: {token_symbol}")
    
    # Store the token symbol in user_data for potential later use
    context.user_data["search_token"] = token_symbol
    
    # Send a processing message
    processing_message = await update.message.reply_text(
        f"*🔍 Searching for {token_symbol} pools...*\n\n"
        f"Please wait while I retrieve the data.",
        parse_mode="MarkdownV2"
    )
    
    try:
        # Call the SolPool API to get pools containing this token
        pools = get_token_pools(token_symbol, limit=5)
        
        # Try to get sentiment and price data for additional context
        sentiment_data = {}
        price_data = {}
        
        try:
            sentiment_response = get_token_sentiment(token_symbol)
            if token_symbol in sentiment_response.get('sentiment', {}):
                sentiment_data = sentiment_response['sentiment'][token_symbol]
        except Exception as e:
            logger.error(f"Error getting sentiment for {token_symbol}: {e}")
            
        try:
            price_response = get_price_data(token_symbol)
            if token_symbol in price_response.get('prices', {}):
                price_data = price_response['prices'][token_symbol]
        except Exception as e:
            logger.error(f"Error getting price for {token_symbol}: {e}")
        
        # Format the search results message
        if pools:
            # Delete the processing message
            await processing_message.delete()
            
            # Format token information
            token_info = f"*🔍 {token_symbol} Pool Search Results*\n\n"
            
            if price_data:
                price = price_data.get('price_usd', 0)
                change_24h = price_data.get('percent_change_24h', 0)
                change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                
                token_info += f"*Current Price:* *${price:,.6f}*\n"
                token_info += f"*24h Change:* {change_emoji} *{change_24h:+.2f}%*\n\n"
            
            if sentiment_data:
                score = sentiment_data.get('score', 0)
                sentiment_emoji = "🟢" if score > 0.2 else "🟡" if score > -0.2 else "🔴"
                
                token_info += f"*Sentiment Score:* {sentiment_emoji} *{score:.2f}*\n\n"
            
            token_info += f"*Pools Containing {token_symbol}:*\n\n"
            
            # Format pool information
            for i, pool in enumerate(pools, start=1):
                other_token = pool.get('token_b_symbol', 'Unknown') if pool.get('token_a_symbol') == token_symbol else pool.get('token_a_symbol', 'Unknown')
                pool_name = f"{token_symbol}/{other_token}"
                apr = pool.get('apr_24h', 0)
                tvl = pool.get('tvl', 0)
                
                token_info += f"*{i}. {pool_name}*\n"
                token_info += f"   APR: *{apr:.2f}%*\n"
                token_info += f"   TVL: *${tvl:,.2f}*\n\n"
            
            # Create buttons for each pool
            keyboard = []
            for pool in pools:
                pool_id = pool.get('id', '')
                if pool_id:
                    other_token = pool.get('token_b_symbol', 'Unknown') if pool.get('token_a_symbol') == token_symbol else pool.get('token_a_symbol', 'Unknown')
                    pool_name = f"{token_symbol}/{other_token}"
                    keyboard.append([InlineKeyboardButton(f"Details: {pool_name}", callback_data=f"pool:{pool_id}")])
            
            keyboard.append([InlineKeyboardButton("🔍 New Search", callback_data="custom_token_search")])
            keyboard.append([InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")])
            
            await update.message.reply_text(
                token_info,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            
        else:
            # No pools found
            await processing_message.delete()
            
            keyboard = [
                [InlineKeyboardButton("🔍 Try Another Token", callback_data="custom_token_search")],
                [InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")]
            ]
            
            await update.message.reply_text(
                f"*🔍 {token_symbol} Pool Search Results*\n\n"
                f"Sorry, I couldn't find any active liquidity pools containing {token_symbol}.\n\n"
                f"Try searching for another token or view all available pools.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            
    except Exception as e:
        logger.error(f"Error in token search for {token_symbol}: {e}")
        
        # Error handling
        await processing_message.delete()
        
        keyboard = [
            [InlineKeyboardButton("🔍 Try Again", callback_data="custom_token_search")],
            [InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")]
        ]
        
        await update.message.reply_text(
            "*🔍 Search Error*\n\n"
            f"Sorry, I encountered an error while searching for pools with {token_symbol}.\n\n"
            f"Please try again with a different token symbol.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
    
    # End the conversation
    return ConversationHandler.END

async def cancel_token_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel the token search conversation.
    """
    query = update.callback_query
    if query:
        await query.answer()
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} cancelled token search")
        
        # Return to the token search menu
        keyboard = [
            [
                InlineKeyboardButton("SOL", callback_data="search_token_SOL"),
                InlineKeyboardButton("USDC", callback_data="search_token_USDC"),
                InlineKeyboardButton("ETH", callback_data="search_token_ETH")
            ],
            [
                InlineKeyboardButton("USDT", callback_data="search_token_USDT"),
                InlineKeyboardButton("BTC", callback_data="search_token_BTC"),
                InlineKeyboardButton("BONK", callback_data="search_token_BONK")
            ],
            [InlineKeyboardButton("🔍 Custom Token Search", callback_data="custom_token_search")],
            [InlineKeyboardButton("⬅️ Back to Explore", callback_data="explore_pools")]
        ]
        
        await query.edit_message_text(
            "*🔍 Search Pools by Token*\n\n"
            "Find liquidity pools containing a specific token.\n\n"
            "Select from popular tokens below or use custom search for other tokens:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
    
    return ConversationHandler.END

async def token_search_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle conversation timeout.
    """
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"Token search conversation timed out for user {user_id}")
    
    await update.message.reply_text(
        "*⏱️ Search Timeout*\n\n"
        "Your token search has timed out. If you still want to search for a token, "
        "please select 'Custom Token Search' again.",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔍 New Search", callback_data="custom_token_search")
        ]])
    )
    
    return ConversationHandler.END

def get_token_search_conversation_handler() -> ConversationHandler:
    """
    Create and return the token search conversation handler.
    """
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_token_search, pattern="^custom_token_search$")
        ],
        states={
            WAITING_FOR_TOKEN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_input),
                CallbackQueryHandler(cancel_token_search, pattern="^cancel_token_search$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_token_search, pattern="^cancel_token_search$"),
            CommandHandler("cancel", cancel_token_search)
        ],
        name="token_search_conversation",
        persistent=False,
        conversation_timeout=300  # 5 minutes timeout
    )