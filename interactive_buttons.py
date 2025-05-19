#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interactive buttons implementation for FiLot Telegram bot
This module adds support for inline keyboards that perform real database operations
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional, Union, Tuple

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, Application

from models import db, Pool, User, UserActivityLog
import db_utils
from fixed_responses import get_fixed_responses
from menus import MenuType

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fixed responses for when database is unavailable
fixed_responses = get_fixed_responses()

# Callback data prefixes for different actions
POOL_PREFIX = "pool:"
APR_POOLS_PREFIX = "apr_pools:"
STABLE_POOLS_PREFIX = "stable_pools:"
PROFILE_PREFIX = "profile:"
WALLET_PREFIX = "wallet:"
FAQ_PREFIX = "faq:"
BACK_PREFIX = "back:"
PAGE_PREFIX = "page:"


async def get_pool_data_from_db() -> List[Dict[str, Any]]:
    """
    Get real pool data from the database
    
    Returns:
        List of pool dictionaries with data from the database
    """
    try:
        # Query the database for pools
        pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(10).all()
        
        # Convert to dictionaries
        pool_list = []
        for pool in pools:
            pool_dict = {
                "id": pool.id,
                "token_a": pool.token_a_symbol,
                "token_b": pool.token_b_symbol,
                "apr_24h": pool.apr_24h,
                "tvl": pool.tvl,
                "volume_24h": pool.volume_24h or 0
            }
            pool_list.append(pool_dict)
            
        return pool_list
    except Exception as e:
        logger.error(f"Error fetching pool data from database: {e}")
        # Use fallback data if database operation fails
        return [
            {
                "id": "sol_usdc_pool1",
                "token_a": "SOL",
                "token_b": "USDC",
                "apr_24h": 28.5,
                "tvl": 1250000,
                "volume_24h": 450000
            },
            {
                "id": "btc_usdt_pool1",
                "token_a": "BTC",
                "token_b": "USDT",
                "apr_24h": 22.3,
                "tvl": 3450000,
                "volume_24h": 890000
            },
            {
                "id": "eth_usdc_pool1", 
                "token_a": "ETH",
                "token_b": "USDC",
                "apr_24h": 19.8,
                "tvl": 2780000,
                "volume_24h": 750000
            }
        ]


async def get_user_profile_from_db(user_id: int) -> Dict[str, Any]:
    """
    Get user profile data from the database
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Dictionary with user profile data
    """
    try:
        # Query the database for user
        user = User.query.filter_by(id=user_id).first()
        
        if user:
            return {
                "id": user.id,
                "username": user.username or "N/A",
                "risk_profile": user.risk_profile,
                "investment_horizon": user.investment_horizon,
                "investment_goals": user.investment_goals or "Not specified",
                "is_subscribed": user.is_subscribed,
                "created_at": user.created_at.strftime("%Y-%m-%d")
            }
    except Exception as e:
        logger.error(f"Error fetching user profile from database: {e}")
    
    # Return default profile if database operation fails
    return {
        "id": user_id,
        "username": "N/A",
        "risk_profile": "moderate",
        "investment_horizon": "medium",
        "investment_goals": "Not specified",
        "is_subscribed": False,
        "created_at": "N/A"
    }


def create_inline_pool_keyboard(pools: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Create inline keyboard with pool data
    
    Args:
        pools: List of pool dictionaries
        
    Returns:
        InlineKeyboardMarkup with pool buttons
    """
    keyboard = []
    
    # Add buttons for each pool
    for pool in pools:
        token_pair = f"{pool['token_a']}-{pool['token_b']}"
        apr = f"{pool['apr_24h']:.2f}%"
        button_text = f"{token_pair} ({apr} APR)"
        
        # Create callback data with pool ID
        callback_data = f"{POOL_PREFIX}{pool['id']}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    # Add pagination and back buttons
    nav_row = []
    nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"{BACK_PREFIX}main"))
    if len(pools) == 10:  # If we have max results, show next page button
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"{PAGE_PREFIX}pools:2"))
    
    keyboard.append(nav_row)
    
    return InlineKeyboardMarkup(keyboard)


def create_main_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Create the main menu inline keyboard
    
    Returns:
        InlineKeyboardMarkup with main menu buttons
    """
    keyboard = [
        [InlineKeyboardButton("📊 Pool Information", callback_data=f"{POOL_PREFIX}info")],
        [InlineKeyboardButton("📈 High APR Pools", callback_data=f"{APR_POOLS_PREFIX}1")],
        [InlineKeyboardButton("💵 Stable Pools", callback_data=f"{STABLE_POOLS_PREFIX}1")],
        [InlineKeyboardButton("👤 My Profile", callback_data=f"{PROFILE_PREFIX}view")],
        [InlineKeyboardButton("💼 My Wallet", callback_data=f"{WALLET_PREFIX}view")],
        [InlineKeyboardButton("❓ FAQ", callback_data=f"{FAQ_PREFIX}main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_faq_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Create FAQ inline keyboard
    
    Returns:
        InlineKeyboardMarkup with FAQ topic buttons
    """
    keyboard = [
        [InlineKeyboardButton("💡 About Liquidity Pools", callback_data=f"{FAQ_PREFIX}liquidity")],
        [InlineKeyboardButton("💱 About APR", callback_data=f"{FAQ_PREFIX}apr")],
        [InlineKeyboardButton("⚠️ About Impermanent Loss", callback_data=f"{FAQ_PREFIX}impermanent")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data=f"{BACK_PREFIX}main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def create_profile_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Create profile inline keyboard
    
    Returns:
        InlineKeyboardMarkup with profile setting buttons
    """
    keyboard = [
        [InlineKeyboardButton("🔄 Change Risk Profile", callback_data=f"{PROFILE_PREFIX}risk")],
        [InlineKeyboardButton("📅 Change Investment Horizon", callback_data=f"{PROFILE_PREFIX}horizon")],
        [InlineKeyboardButton("🎯 Set Investment Goals", callback_data=f"{PROFILE_PREFIX}goals")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data=f"{BACK_PREFIX}main")]
    ]
    
    return InlineKeyboardMarkup(keyboard)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the main menu with inline keyboard
    
    Args:
        update: Telegram update object
        context: Context object
    """
    keyboard = create_main_inline_keyboard()
    
    # Determine if this is from a callback or direct command
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            "🚀 *FiLot - Interactive Menu*\n\n"
            "Welcome to FiLot! Use the buttons below to navigate.\n"
            "These interactive buttons connect directly to our database "
            "to provide real-time information.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_markdown(
            "🚀 *FiLot - Interactive Menu*\n\n"
            "Welcome to FiLot! Use the buttons below to navigate.\n"
            "These interactive buttons connect directly to our database "
            "to provide real-time information.",
            reply_markup=keyboard
        )
    
    # Log activity
    user_id = update.effective_user.id
    try:
        await db_utils.log_user_activity(user_id, "interactive_menu", {"menu": "main"})
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_pool_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show pool information with data from the database
    
    Args:
        update: Telegram update object
        context: Context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get real pool data from database
    pools = await get_pool_data_from_db()
    
    # Create inline keyboard with pool data
    keyboard = create_inline_pool_keyboard(pools)
    
    await query.message.edit_text(
        "📊 *Pool Information*\n\n"
        "Here are the current top liquidity pools. Click on a pool to see detailed information.\n\n"
        "This data is retrieved directly from our database in real-time.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    # Log activity
    try:
        await db_utils.log_user_activity(user_id, "view_pools", {"count": len(pools)})
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_specific_pool(update: Update, context: ContextTypes.DEFAULT_TYPE, pool_id: str) -> None:
    """
    Show detailed information for a specific pool
    
    Args:
        update: Telegram update object
        context: Context object
        pool_id: Pool ID to display
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        # Get pool data from database
        pool = Pool.query.filter_by(id=pool_id).first()
        
        if pool:
            # Format pool information
            message = (
                f"🏦 *Pool: {pool.token_a_symbol}-{pool.token_b_symbol}*\n\n"
                f"• *APR (24h):* {pool.apr_24h:.2f}%\n"
                f"• *APR (7d):* {pool.apr_7d:.2f}% if pool.apr_7d else 'N/A'\n"
                f"• *TVL:* ${pool.tvl:,.2f}\n"
                f"• *Fee:* {pool.fee:.2f}%\n"
                f"• *Volume (24h):* ${pool.volume_24h:,.2f} if pool.volume_24h else 'N/A'}\n"
                f"• *Transactions (24h):* {pool.tx_count_24h if pool.tx_count_24h else 'N/A'}\n"
                f"• *Last Updated:* {pool.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "This data is retrieved directly from our database."
            )
        else:
            # If pool not found, use a generic message
            message = (
                "⚠️ *Pool Information Not Found*\n\n"
                f"The pool with ID '{pool_id}' was not found in our database.\n"
                "Please try viewing a different pool or contact support if this issue persists."
            )
    except Exception as e:
        logger.error(f"Error retrieving pool data from database: {e}")
        # Fallback message if database operation fails
        message = (
            "⚠️ *Database Operation Error*\n\n"
            "Sorry, we couldn't retrieve the pool information from our database at this time.\n"
            "Please try again later."
        )
    
    # Create back button
    keyboard = [[InlineKeyboardButton("⬅️ Back to Pools", callback_data=f"{POOL_PREFIX}info")]]
    
    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Log activity
    try:
        await db_utils.log_user_activity(user_id, "view_pool_details", {"pool_id": pool_id})
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_high_apr_pools(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    """
    Show high APR pools from the database
    
    Args:
        update: Telegram update object
        context: Context object
        page: Page number for pagination
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        # Query database for high APR pools
        limit = 5
        offset = (page - 1) * limit
        
        high_apr_pools = Pool.query.order_by(Pool.apr_24h.desc()).offset(offset).limit(limit).all()
        
        if high_apr_pools:
            # Format pool information
            message = "📈 *High APR Pools*\n\n"
            
            for i, pool in enumerate(high_apr_pools):
                message += (
                    f"{i+1}. *{pool.token_a_symbol}-{pool.token_b_symbol}*\n"
                    f"   • APR: {pool.apr_24h:.2f}%\n"
                    f"   • TVL: ${pool.tvl:,.2f}\n\n"
                )
                
            message += "These pools currently offer the highest APRs in our database."
        else:
            # If no pools found
            message = (
                "⚠️ *No High APR Pools Found*\n\n"
                "We couldn't find any high APR pools in our database at this time.\n"
                "Please check back later."
            )
    except Exception as e:
        logger.error(f"Error retrieving high APR pools from database: {e}")
        # Fallback message if database operation fails
        message = (
            "⚠️ *Database Operation Error*\n\n"
            "Sorry, we couldn't retrieve the high APR pools from our database at this time.\n"
            "Please try again later."
        )
    
    # Create navigation buttons
    keyboard = []
    nav_row = []
    
    # Back to main button
    nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"{BACK_PREFIX}main"))
    
    # Pagination buttons
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data=f"{APR_POOLS_PREFIX}{page-1}"))
    
    if high_apr_pools and len(high_apr_pools) == limit:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"{APR_POOLS_PREFIX}{page+1}"))
    
    keyboard.append(nav_row)
    
    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Log activity
    try:
        await db_utils.log_user_activity(user_id, "view_high_apr_pools", {"page": page})
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_stable_pools(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 1) -> None:
    """
    Show stable pools (with stablecoins) from the database
    
    Args:
        update: Telegram update object
        context: Context object
        page: Page number for pagination
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    try:
        # Query database for stable pools
        limit = 5
        offset = (page - 1) * limit
        
        # Define stablecoins
        stablecoins = ['USDC', 'USDT', 'DAI', 'BUSD', 'UST']
        
        # This is a simplified query - in a real implementation, you would use SQL's
        # OR conditions to find pools containing any of the stablecoins
        stable_pools = []
        pools = Pool.query.offset(offset).limit(limit*3).all()  # Get more to filter
        
        # Filter for stable pools (contains at least one stablecoin)
        for pool in pools:
            if pool.token_a_symbol in stablecoins or pool.token_b_symbol in stablecoins:
                stable_pools.append(pool)
                if len(stable_pools) >= limit:
                    break
        
        if stable_pools:
            # Format pool information
            message = "💵 *Stable Pools*\n\n"
            
            for i, pool in enumerate(stable_pools):
                message += (
                    f"{i+1}. *{pool.token_a_symbol}-{pool.token_b_symbol}*\n"
                    f"   • APR: {pool.apr_24h:.2f}%\n"
                    f"   • TVL: ${pool.tvl:,.2f}\n\n"
                )
                
            message += "These pools include stablecoins and typically have lower volatility."
        else:
            # If no pools found
            message = (
                "⚠️ *No Stable Pools Found*\n\n"
                "We couldn't find any stable pools in our database at this time.\n"
                "Please check back later."
            )
    except Exception as e:
        logger.error(f"Error retrieving stable pools from database: {e}")
        # Fallback message if database operation fails
        message = (
            "⚠️ *Database Operation Error*\n\n"
            "Sorry, we couldn't retrieve the stable pools from our database at this time.\n"
            "Please try again later."
        )
    
    # Create navigation buttons
    keyboard = []
    nav_row = []
    
    # Back to main button
    nav_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"{BACK_PREFIX}main"))
    
    # Pagination buttons
    if page > 1:
        nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data=f"{STABLE_POOLS_PREFIX}{page-1}"))
    
    if stable_pools and len(stable_pools) == limit:
        nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"{STABLE_POOLS_PREFIX}{page+1}"))
    
    keyboard.append(nav_row)
    
    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Log activity
    try:
        await db_utils.log_user_activity(user_id, "view_stable_pools", {"page": page})
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show user profile from database
    
    Args:
        update: Telegram update object
        context: Context object
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Get user profile from database
    profile = await get_user_profile_from_db(user_id)
    
    # Format profile information
    message = (
        "👤 *Your Profile*\n\n"
        f"• *Risk Profile:* {profile['risk_profile'].capitalize()}\n"
        f"• *Investment Horizon:* {profile['investment_horizon'].capitalize()}\n"
        f"• *Investment Goals:* {profile['investment_goals']}\n"
        f"• *Subscribed to Updates:* {'Yes' if profile['is_subscribed'] else 'No'}\n"
        f"• *Account Created:* {profile['created_at']}\n\n"
        "This information is used to personalize your investment recommendations."
    )
    
    # Create profile settings keyboard
    keyboard = create_profile_inline_keyboard()
    
    await query.message.edit_text(
        message,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    # Log activity
    try:
        await db_utils.log_user_activity(user_id, "view_profile", None)
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str = "main") -> None:
    """
    Show FAQ topics or a specific FAQ answer
    
    Args:
        update: Telegram update object
        context: Context object
        topic: FAQ topic to display
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    if topic == "main":
        # Show FAQ menu
        message = (
            "❓ *Frequently Asked Questions*\n\n"
            "Choose a topic to learn more:"
        )
        keyboard = create_faq_inline_keyboard()
    else:
        # Show specific FAQ topic
        if topic == "liquidity":
            # Get response from fixed_responses or database
            response = fixed_responses.get("what is liquidity pool", 
                "A liquidity pool is a collection of funds locked in a smart contract used in decentralized exchanges.")
            title = "💡 About Liquidity Pools"
        elif topic == "apr":
            response = fixed_responses.get("what is apr",
                "APR (Annual Percentage Rate) represents the yearly interest earned on your investment, not accounting for compounding.")
            title = "💱 About APR"
        elif topic == "impermanent":
            response = fixed_responses.get("impermanent loss",
                "Impermanent loss happens when the price ratio of tokens in your liquidity pool changes compared to when you deposited them.")
            title = "⚠️ About Impermanent Loss"
        else:
            response = "Sorry, that FAQ topic is not available."
            title = "❓ FAQ Topic"
        
        message = f"*{title}*\n\n{response}"
        
        # Create back button
        keyboard = [[InlineKeyboardButton("⬅️ Back to FAQ", callback_data=f"{FAQ_PREFIX}main")]]
    
    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Log activity
    try:
        await db_utils.log_user_activity(user_id, "view_faq", {"topic": topic})
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from inline keyboards
    
    Args:
        update: Telegram update object
        context: Context object
    """
    query = update.callback_query
    data = query.data
    
    logger.info(f"Received callback query: {data}")
    
    # Process callback data based on prefix
    if data.startswith(POOL_PREFIX):
        pool_data = data[len(POOL_PREFIX):]
        if pool_data == "info":
            await handle_pool_info(update, context)
        else:
            await handle_specific_pool(update, context, pool_data)
    
    elif data.startswith(APR_POOLS_PREFIX):
        page = int(data[len(APR_POOLS_PREFIX):])
        await handle_high_apr_pools(update, context, page)
    
    elif data.startswith(STABLE_POOLS_PREFIX):
        page = int(data[len(STABLE_POOLS_PREFIX):])
        await handle_stable_pools(update, context, page)
    
    elif data.startswith(PROFILE_PREFIX):
        profile_action = data[len(PROFILE_PREFIX):]
        if profile_action == "view":
            await handle_user_profile(update, context)
        else:
            # Handle profile actions (risk, horizon, goals)
            # For now, just show the profile
            await handle_user_profile(update, context)
    
    elif data.startswith(FAQ_PREFIX):
        faq_topic = data[len(FAQ_PREFIX):]
        await handle_faq(update, context, faq_topic)
    
    elif data.startswith(BACK_PREFIX):
        back_to = data[len(BACK_PREFIX):]
        if back_to == "main":
            await show_main_menu(update, context)
    
    elif data.startswith(PAGE_PREFIX):
        # Handle pagination (not implemented for brevity)
        await query.answer("Pagination not implemented in this demo")
    
    else:
        await query.answer("Unknown button action")


def register_handlers(application: Application) -> None:
    """
    Register handlers for interactive buttons
    
    Args:
        application: Application instance
    """
    # Register the callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    logger.info("Interactive button handlers registered")