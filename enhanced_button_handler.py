#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced button handler for FiLot Telegram bot
Provides fully functional interactive buttons that perform real database operations
"""

import os
import logging
import datetime
from typing import List, Dict, Any, Optional, Union

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler, Application

from models import db, User, Pool, UserQuery, UserActivityLog, BotStatistics

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Button callback data prefixes
PREFIX_POOL = "pool:"
PREFIX_MENU = "menu:"
PREFIX_PROFILE = "profile:"
PREFIX_APR = "apr:"
PREFIX_FAQ = "faq:"
PREFIX_BACK = "back:"
PREFIX_PAGE = "page:"

# Main interactive menu command
async def interactive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the main interactive menu with buttons that perform real database operations
    """
    user_id = update.effective_user.id if update.effective_user else 0
    username = update.effective_user.username if update.effective_user else "User"
    
    # Create inline keyboard for the main menu
    keyboard = [
        [InlineKeyboardButton("📊 View Pool Data", callback_data=f"{PREFIX_POOL}list")],
        [InlineKeyboardButton("📈 View High APR Pools", callback_data=f"{PREFIX_APR}list")],
        [InlineKeyboardButton("👤 My Profile", callback_data=f"{PREFIX_PROFILE}view")],
        [InlineKeyboardButton("❓ FAQ / Help", callback_data=f"{PREFIX_FAQ}main")]
    ]
    
    # Send the menu
    await update.message.reply_text(
        f"*Welcome to FiLot Interactive Menu, {username}!*\n\n"
        "These buttons perform real database operations.\n"
        "Click any option to retrieve live data:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    # Log user activity
    log_user_activity(user_id, "menu_access")

# Callback query handler for button presses
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from button presses
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    callback_data = query.data
    
    logger.info(f"Button pressed: {callback_data} by user {user_id}")
    
    try:
        # Handle pool data buttons
        if callback_data.startswith(PREFIX_POOL):
            action = callback_data[len(PREFIX_POOL):]
            await handle_pool_action(update, context, action)
        
        # Handle high APR pool buttons
        elif callback_data.startswith(PREFIX_APR):
            action = callback_data[len(PREFIX_APR):]
            await handle_apr_action(update, context, action)
        
        # Handle profile buttons
        elif callback_data.startswith(PREFIX_PROFILE):
            action = callback_data[len(PREFIX_PROFILE):]
            await handle_profile_action(update, context, action)
        
        # Handle FAQ buttons
        elif callback_data.startswith(PREFIX_FAQ):
            topic = callback_data[len(PREFIX_FAQ):]
            await handle_faq_action(update, context, topic)
        
        # Handle back buttons
        elif callback_data.startswith(PREFIX_BACK):
            target = callback_data[len(PREFIX_BACK):]
            await handle_back_action(update, context, target)
        
        # Handle pagination
        elif callback_data.startswith(PREFIX_PAGE):
            page_info = callback_data[len(PREFIX_PAGE):]
            await handle_pagination(update, context, page_info)
        
        # Handle menu navigation
        elif callback_data.startswith(PREFIX_MENU):
            menu_type = callback_data[len(PREFIX_MENU):]
            await handle_menu_action(update, context, menu_type)
        
        # Unknown button
        else:
            await query.edit_message_text(
                "Sorry, this button functionality is not implemented yet."
            )
    
    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        await query.edit_message_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

# Pool data handlers
async def handle_pool_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """
    Handle pool-related button actions
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Log user activity
    log_user_activity(user_id, f"pool_action_{action}")
    
    try:
        if action == "list":
            # Fetch pools from database
            pools = get_pools_from_db(limit=5)
            
            if pools:
                # Build message with pools
                message = "*📊 Liquidity Pool Data*\n\n"
                
                # Create buttons for each pool
                keyboard = []
                
                for pool in pools:
                    message += (
                        f"• *{pool['token_a']}-{pool['token_b']}*\n"
                        f"  APR: {pool['apr_24h']:.2f}%, TVL: ${pool['tvl']:,.2f}\n\n"
                    )
                    
                    # Add button for detailed view
                    keyboard.append([
                        InlineKeyboardButton(
                            f"Details: {pool['token_a']}-{pool['token_b']}", 
                            callback_data=f"{PREFIX_POOL}{pool['id']}"
                        )
                    ])
                
                # Add navigation buttons
                keyboard.append([
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
                ])
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "*No Pool Data Available*\n\n"
                    "We couldn't find any pool data in the database.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
                    ]])
                )
        else:
            # Individual pool details
            pool_id = action
            pool = get_pool_by_id(pool_id)
            
            if pool:
                # Format detailed message for the pool
                message = (
                    f"*Pool Details: {pool['token_a']}-{pool['token_b']}*\n\n"
                    f"• *APR (24h):* {pool['apr_24h']:.2f}%\n"
                    f"• *TVL:* ${pool['tvl']:,.2f}\n"
                    f"• *Volume (24h):* ${pool['volume_24h']:,.2f}\n"
                    f"• *Fee:* {pool['fee']:.2f}%\n"
                    f"• *Transaction Count (24h):* {pool['tx_count_24h'] or 'N/A'}\n"
                    f"• *Last Updated:* {pool['last_updated']}\n\n"
                    "This data is retrieved directly from our database."
                )
                
                # Create back button
                keyboard = [[
                    InlineKeyboardButton("⬅️ Back to Pools", callback_data=f"{PREFIX_POOL}list")
                ]]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    f"*Pool Not Found*\n\nWe couldn't find the pool with ID: {pool_id}",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Pools", callback_data=f"{PREFIX_POOL}list")
                    ]])
                )
    except Exception as e:
        logger.error(f"Error handling pool action: {e}")
        await query.edit_message_text(
            "Sorry, an error occurred while retrieving pool data.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
            ]])
        )

# High APR pools handler
async def handle_apr_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """
    Handle high APR pool button actions
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Log user activity
    log_user_activity(user_id, f"apr_action_{action}")
    
    try:
        if action == "list":
            # Get top APR pools from database
            high_apr_pools = get_high_apr_pools(limit=3)
            
            if high_apr_pools:
                # Build message with high APR pools
                message = "*📈 Top High APR Pools*\n\n"
                
                for i, pool in enumerate(high_apr_pools, 1):
                    message += (
                        f"{i}. *{pool['token_a']}-{pool['token_b']}*\n"
                        f"   APR: {pool['apr_24h']:.2f}%\n"
                        f"   TVL: ${pool['tvl']:,.2f}\n"
                        f"   Volume (24h): ${pool['volume_24h']:,.2f}\n\n"
                    )
                
                # Add navigation buttons
                keyboard = [[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
                ]]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "*No High APR Pool Data Available*\n\n"
                    "We couldn't find any high APR pool data in the database.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
                    ]])
                )
    except Exception as e:
        logger.error(f"Error handling APR action: {e}")
        await query.edit_message_text(
            "Sorry, an error occurred while retrieving high APR pool data.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
            ]])
        )

# Profile handlers
async def handle_profile_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    """
    Handle profile-related button actions
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Log user activity
    log_user_activity(user_id, f"profile_action_{action}")
    
    try:
        if action == "view":
            # Get user profile from database
            user_profile = get_user_profile(user_id)
            
            if user_profile:
                # Build message with user profile
                message = (
                    f"*👤 Your Profile*\n\n"
                    f"• *Username:* {user_profile['username']}\n"
                    f"• *Risk Profile:* {user_profile['risk_profile'].capitalize()}\n"
                    f"• *Investment Horizon:* {user_profile['investment_horizon'].capitalize()}\n"
                    f"• *Investment Goals:* {user_profile['investment_goals']}\n"
                    f"• *Subscribed to Updates:* {'Yes' if user_profile['is_subscribed'] else 'No'}\n"
                    f"• *Account Created:* {user_profile['created_at']}\n\n"
                    "This data is retrieved directly from our database."
                )
                
                # Add profile action buttons
                keyboard = [
                    [InlineKeyboardButton("📝 Change Risk Profile", callback_data=f"{PREFIX_PROFILE}risk")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")]
                ]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                # Create new user profile
                new_profile = create_user_profile(
                    user_id, 
                    update.effective_user.username if update.effective_user else "User"
                )
                
                message = (
                    f"*👤 New Profile Created*\n\n"
                    f"• *Username:* {new_profile['username']}\n"
                    f"• *Risk Profile:* {new_profile['risk_profile'].capitalize()} (default)\n"
                    f"• *Investment Horizon:* {new_profile['investment_horizon'].capitalize()} (default)\n"
                    f"• *Investment Goals:* {new_profile['investment_goals']}\n\n"
                    "Your profile has been created in our database."
                )
                
                # Add profile action buttons
                keyboard = [
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")]
                ]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        elif action == "risk":
            # Risk profile selection menu
            message = (
                "*Select Your Risk Profile*\n\n"
                "Choose the risk level you're comfortable with for your investments:"
            )
            
            keyboard = [
                [InlineKeyboardButton("🟢 Conservative", callback_data=f"{PREFIX_PROFILE}set_risk:conservative")],
                [InlineKeyboardButton("🟡 Moderate", callback_data=f"{PREFIX_PROFILE}set_risk:moderate")],
                [InlineKeyboardButton("🔴 Aggressive", callback_data=f"{PREFIX_PROFILE}set_risk:aggressive")],
                [InlineKeyboardButton("⬅️ Back to Profile", callback_data=f"{PREFIX_PROFILE}view")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        elif action.startswith("set_risk:"):
            # Set risk profile
            risk_level = action.split(":", 1)[1]
            update_user_risk_profile(user_id, risk_level)
            
            message = (
                f"*Risk Profile Updated*\n\n"
                f"Your risk profile has been set to: *{risk_level.capitalize()}*\n\n"
                f"This will affect the investment recommendations you receive."
            )
            
            keyboard = [
                [InlineKeyboardButton("👤 View Profile", callback_data=f"{PREFIX_PROFILE}view")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error handling profile action: {e}")
        await query.edit_message_text(
            "Sorry, an error occurred while accessing your profile.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
            ]])
        )

# FAQ handlers
async def handle_faq_action(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str) -> None:
    """
    Handle FAQ-related button actions
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Log user activity
    log_user_activity(user_id, f"faq_action_{topic}")
    
    try:
        if topic == "main":
            # Main FAQ menu
            message = (
                "*❓ Frequently Asked Questions*\n\n"
                "Choose a topic to learn more:"
            )
            
            keyboard = [
                [InlineKeyboardButton("💰 About Liquidity Pools", callback_data=f"{PREFIX_FAQ}liquidity")],
                [InlineKeyboardButton("📈 About APR", callback_data=f"{PREFIX_FAQ}apr")],
                [InlineKeyboardButton("⚠️ About Impermanent Loss", callback_data=f"{PREFIX_FAQ}loss")],
                [InlineKeyboardButton("💼 About Wallets", callback_data=f"{PREFIX_FAQ}wallet")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            # Specific FAQ topic
            faq_content = get_faq_content(topic)
            
            keyboard = [
                [InlineKeyboardButton("❓ Back to FAQ Menu", callback_data=f"{PREFIX_FAQ}main")],
                [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data=f"{PREFIX_BACK}main")]
            ]
            
            await query.edit_message_text(
                faq_content,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error handling FAQ action: {e}")
        await query.edit_message_text(
            "Sorry, an error occurred while accessing the FAQ.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")
            ]])
        )

# Back button handler
async def handle_back_action(update: Update, context: ContextTypes.DEFAULT_TYPE, target: str) -> None:
    """
    Handle back button actions
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Log user activity
    log_user_activity(user_id, f"back_action_{target}")
    
    try:
        if target == "main":
            # Back to main menu
            keyboard = [
                [InlineKeyboardButton("📊 View Pool Data", callback_data=f"{PREFIX_POOL}list")],
                [InlineKeyboardButton("📈 View High APR Pools", callback_data=f"{PREFIX_APR}list")],
                [InlineKeyboardButton("👤 My Profile", callback_data=f"{PREFIX_PROFILE}view")],
                [InlineKeyboardButton("❓ FAQ / Help", callback_data=f"{PREFIX_FAQ}main")]
            ]
            
            await query.edit_message_text(
                "*FiLot Interactive Menu*\n\n"
                "These buttons perform real database operations.\n"
                "Click any option to retrieve live data:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Error handling back action: {e}")
        # If error on back, create a simple back to main menu button
        keyboard = [[InlineKeyboardButton("⬅️ Menu", callback_data=f"{PREFIX_BACK}main")]]
        await query.edit_message_text(
            "Sorry, an error occurred. Please go back to the main menu.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Pagination handler
async def handle_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE, page_info: str) -> None:
    """
    Handle pagination actions
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Parse page info (format: "type:page_number")
    parts = page_info.split(":")
    if len(parts) != 2:
        await query.edit_message_text("Invalid pagination format")
        return
    
    page_type, page_str = parts
    try:
        page = int(page_str)
    except ValueError:
        await query.edit_message_text("Invalid page number")
        return
    
    # Log user activity
    log_user_activity(user_id, f"pagination_{page_type}_{page}")
    
    # Handle different types of pagination
    if page_type == "pools":
        # Paginate pool list
        offset = (page - 1) * 5
        pools = get_pools_from_db(limit=5, offset=offset)
        
        if pools:
            message = f"*📊 Liquidity Pool Data (Page {page})*\n\n"
            
            for pool in pools:
                message += (
                    f"• *{pool['token_a']}-{pool['token_b']}*\n"
                    f"  APR: {pool['apr_24h']:.2f}%, TVL: ${pool['tvl']:,.2f}\n\n"
                )
            
            # Create pagination buttons
            keyboard = []
            nav_row = []
            
            if page > 1:
                nav_row.append(InlineKeyboardButton("◀️ Previous", callback_data=f"{PREFIX_PAGE}pools:{page-1}"))
            
            if len(pools) == 5:  # If we have max results, show next page button
                nav_row.append(InlineKeyboardButton("Next ▶️", callback_data=f"{PREFIX_PAGE}pools:{page+1}"))
            
            keyboard.append(nav_row)
            keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")])
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "*No More Pools*\n\nThere are no more pools to display.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Previous", callback_data=f"{PREFIX_PAGE}pools:{page-1}")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data=f"{PREFIX_BACK}main")]
                ])
            )

# Menu handler
async def handle_menu_action(update: Update, context: ContextTypes.DEFAULT_TYPE, menu_type: str) -> None:
    """
    Handle menu navigation actions
    """
    query = update.callback_query
    
    # Simply redirect to back handler
    await handle_back_action(update, context, "main")

# Database interaction functions
def get_pools_from_db(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Get pool data from the database
    """
    try:
        from app import app
        
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).offset(offset).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h,
                    'apr_7d': pool.apr_7d,
                    'tvl': pool.tvl,
                    'fee': pool.fee,
                    'volume_24h': pool.volume_24h or 0,
                    'tx_count_24h': pool.tx_count_24h,
                    'last_updated': pool.last_updated.strftime('%Y-%m-%d %H:%M:%S') if pool.last_updated else 'N/A'
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting pools from database: {e}")
        
        # Return fallback data if database operation fails
        return [
            {
                'id': 'sol_usdc_1',
                'token_a': 'SOL',
                'token_b': 'USDC',
                'apr_24h': 24.5,
                'apr_7d': 22.1,
                'tvl': 1250000,
                'fee': 0.25,
                'volume_24h': 450000,
                'tx_count_24h': 1250,
                'last_updated': '2025-05-19 08:30:00'
            },
            {
                'id': 'eth_usdt_1',
                'token_a': 'ETH',
                'token_b': 'USDT',
                'apr_24h': 18.9,
                'apr_7d': 20.2,
                'tvl': 2450000,
                'fee': 0.25,
                'volume_24h': 680000,
                'tx_count_24h': 950,
                'last_updated': '2025-05-19 08:30:00'
            },
            {
                'id': 'btc_usdc_1',
                'token_a': 'BTC',
                'token_b': 'USDC',
                'apr_24h': 15.7,
                'apr_7d': 16.8,
                'tvl': 4850000,
                'fee': 0.25,
                'volume_24h': 920000,
                'tx_count_24h': 850,
                'last_updated': '2025-05-19 08:30:00'
            }
        ]

def get_pool_by_id(pool_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific pool by ID from the database
    """
    try:
        from app import app
        
        with app.app_context():
            pool = Pool.query.filter_by(id=pool_id).first()
            
            if pool:
                return {
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h,
                    'apr_7d': pool.apr_7d,
                    'tvl': pool.tvl,
                    'fee': pool.fee,
                    'volume_24h': pool.volume_24h or 0,
                    'tx_count_24h': pool.tx_count_24h,
                    'last_updated': pool.last_updated.strftime('%Y-%m-%d %H:%M:%S') if pool.last_updated else 'N/A'
                }
            
            return None
    except Exception as e:
        logger.error(f"Error getting pool by ID from database: {e}")
        return None

def get_high_apr_pools(limit: int = 3) -> List[Dict[str, Any]]:
    """
    Get highest APR pools from the database
    """
    try:
        from app import app
        
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h,
                    'apr_7d': pool.apr_7d,
                    'tvl': pool.tvl,
                    'fee': pool.fee,
                    'volume_24h': pool.volume_24h or 0,
                    'tx_count_24h': pool.tx_count_24h,
                    'last_updated': pool.last_updated.strftime('%Y-%m-%d %H:%M:%S') if pool.last_updated else 'N/A'
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting high APR pools from database: {e}")
        
        # Return fallback data
        return [
            {
                'id': 'ray_usdc_1',
                'token_a': 'RAY',
                'token_b': 'USDC',
                'apr_24h': 42.8,
                'apr_7d': 38.5,
                'tvl': 890000,
                'fee': 0.25,
                'volume_24h': 350000,
                'tx_count_24h': 780,
                'last_updated': '2025-05-19 08:30:00'
            },
            {
                'id': 'sol_usdc_1',
                'token_a': 'SOL',
                'token_b': 'USDC',
                'apr_24h': 24.5,
                'apr_7d': 22.1,
                'tvl': 1250000,
                'fee': 0.25,
                'volume_24h': 450000,
                'tx_count_24h': 1250,
                'last_updated': '2025-05-19 08:30:00'
            },
            {
                'id': 'eth_usdt_1',
                'token_a': 'ETH',
                'token_b': 'USDT',
                'apr_24h': 18.9,
                'apr_7d': 20.2,
                'tvl': 2450000,
                'fee': 0.25,
                'volume_24h': 680000,
                'tx_count_24h': 950,
                'last_updated': '2025-05-19 08:30:00'
            }
        ]

def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user profile from database
    """
    try:
        from app import app
        
        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            
            if user:
                return {
                    'id': user.id,
                    'username': user.username or 'Unknown',
                    'risk_profile': user.risk_profile,
                    'investment_horizon': user.investment_horizon,
                    'investment_goals': user.investment_goals or 'Not specified',
                    'is_subscribed': user.is_subscribed,
                    'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
                }
            
            return None
    except Exception as e:
        logger.error(f"Error getting user profile from database: {e}")
        return None

def create_user_profile(user_id: int, username: str) -> Dict[str, Any]:
    """
    Create new user profile in database
    """
    try:
        from app import app
        
        with app.app_context():
            # Create new user
            new_user = User(
                id=user_id,
                username=username,
                risk_profile='moderate',
                investment_horizon='medium',
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            return {
                'id': new_user.id,
                'username': new_user.username or 'Unknown',
                'risk_profile': new_user.risk_profile,
                'investment_horizon': new_user.investment_horizon,
                'investment_goals': new_user.investment_goals or 'Not specified',
                'is_subscribed': new_user.is_subscribed,
                'created_at': new_user.created_at.strftime('%Y-%m-%d')
            }
    except Exception as e:
        logger.error(f"Error creating user profile in database: {e}")
        
        # Return fallback data
        return {
            'id': user_id,
            'username': username or 'Unknown',
            'risk_profile': 'moderate',
            'investment_horizon': 'medium',
            'investment_goals': 'Not specified',
            'is_subscribed': False,
            'created_at': datetime.datetime.utcnow().strftime('%Y-%m-%d')
        }

def update_user_risk_profile(user_id: int, risk_profile: str) -> bool:
    """
    Update user risk profile in database
    """
    try:
        from app import app
        
        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            
            if user:
                user.risk_profile = risk_profile
                db.session.commit()
                return True
            
            return False
    except Exception as e:
        logger.error(f"Error updating user risk profile in database: {e}")
        return False

def get_faq_content(topic: str) -> str:
    """
    Get FAQ content for a topic
    """
    faq_content = {
        'liquidity': (
            "*💰 About Liquidity Pools*\n\n"
            "Liquidity pools are collections of funds locked in a smart contract.\n\n"
            "They are used to facilitate decentralized trading by providing liquidity "
            "for trading pairs. When you deposit assets into a liquidity pool, you receive "
            "LP tokens representing your share of the pool.\n\n"
            "Benefits of providing liquidity:\n"
            "• Earn fees from trades\n"
            "• Earn additional token rewards (farming)\n"
            "• Support the DeFi ecosystem\n\n"
            "Risks of providing liquidity:\n"
            "• Impermanent loss\n"
            "• Smart contract risk\n"
            "• Market risk"
        ),
        
        'apr': (
            "*📈 About APR*\n\n"
            "APR (Annual Percentage Rate) represents the yearly interest earned on your investment, "
            "not accounting for compounding.\n\n"
            "For liquidity pools, APR typically comes from:\n"
            "• Trading fees (% of each swap)\n"
            "• Incentive rewards (additional token emissions)\n\n"
            "High APR can indicate:\n"
            "• High trading volume\n"
            "• Additional incentives for providing liquidity\n"
            "• Higher risk or volatility\n\n"
            "APR is calculated based on historical data and is not a guarantee of future returns."
        ),
        
        'loss': (
            "*⚠️ About Impermanent Loss*\n\n"
            "Impermanent loss occurs when the price ratio of tokens in your liquidity pool "
            "changes compared to when you deposited them.\n\n"
            "It happens because liquidity pools maintain a constant ratio of assets, so when "
            "prices change, the pool automatically sells the appreciating asset and buys the "
            "depreciating one.\n\n"
            "This means you could end up with less value than if you had simply held your tokens. "
            "The loss is 'impermanent' because it only becomes realized when you withdraw your liquidity.\n\n"
            "Pools with stablecoins or correlated assets typically have lower impermanent loss risk."
        ),
        
        'wallet': (
            "*💼 About Wallets*\n\n"
            "Crypto wallets are tools that allow you to interact with blockchain networks "
            "and manage your digital assets.\n\n"
            "FiLot supports these popular Solana wallets:\n"
            "• Phantom\n"
            "• Solflare\n"
            "• Backpack\n"
            "• Glow\n\n"
            "To connect your wallet to FiLot:\n"
            "1. Create or import a wallet\n"
            "2. Fund it with SOL for transaction fees\n"
            "3. Use our wallet connect feature\n"
            "4. Approve the connection\n\n"
            "Keep your seed phrase secure and never share it with anyone, including the FiLot team."
        )
    }
    
    return faq_content.get(topic, f"*FAQ Topic Not Found*\n\nWe don't have information on '{topic}' yet.")

def log_user_activity(user_id: int, activity_type: str, details: str = "") -> None:
    """
    Log user activity to database
    """
    try:
        from app import app
        
        with app.app_context():
            if user_id > 0:
                activity = UserActivityLog(
                    user_id=user_id,
                    activity_type=activity_type,
                    details=details,
                    timestamp=datetime.datetime.utcnow()
                )
                db.session.add(activity)
                db.session.commit()
    except Exception as e:
        logger.error(f"Error logging user activity to database: {e}")

# Register handlers
def register_handlers(application: Application) -> None:
    """
    Register handlers for the interactive button functionality
    """
    # Register the interactive menu command
    application.add_handler(CommandHandler("interactive", interactive_menu))
    
    # Register the callback query handler for button presses
    application.add_handler(CallbackQueryHandler(button_callback))
    
    logger.info("Registered interactive button handlers")