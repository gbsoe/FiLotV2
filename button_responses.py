#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Button response handlers for FiLot Telegram bot
Handles all callback_data values with dedicated handler functions
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
import json
import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import db_utils
from models import User, Pool, db
from utils import format_pool_info
from menus import MenuType, get_menu_config
from keyboard_utils import get_reply_keyboard, set_menu_state

# Configure logging
logger = logging.getLogger(__name__)

async def handle_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle the 'account' button click
    """
    query = update.callback_query
    if not query:
        return False
        
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    
    logger.info(f"User {user_id} pressed account button")
    
    # Get user profile from database
    user_profile = get_user_profile(user_id)
    
    # If user doesn't exist, create a new profile
    if not user_profile:
        user_profile = create_user_profile(
            user_id=user_id,
            username=update.effective_user.username or "unknown",
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
    
    # Format user profile data
    if user_profile:
        message = (
            f"*👤 Account Profile*\n\n"
            f"Username: *{user_profile.get('username', 'Unknown')}*\n"
            f"Risk Profile: *{user_profile.get('risk_profile', 'Moderate')}*\n"
            f"Investment Horizon: *{user_profile.get('investment_horizon', 'Medium')}*\n"
            f"Subscription: *{'Active' if user_profile.get('is_subscribed') else 'Not Active'}*\n"
            f"Member Since: *{user_profile.get('created_at', 'N/A')}*\n\n"
        )
    else:
        message = (
            "*👤 Account Profile*\n\n"
            "We couldn't retrieve your profile information\\. "
            "Please try again later\\.\n\n"
        )
    
    # Create account options keyboard
    keyboard = [
        [InlineKeyboardButton("💳 Wallet Settings", callback_data="wallet_settings")],
        [InlineKeyboardButton("⚙️ Update Profile", callback_data="update_profile")],
        [InlineKeyboardButton("🔔 Subscription Settings", callback_data="subscription_settings")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )
    
    return True

async def handle_invest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle the 'invest' button click
    """
    query = update.callback_query
    if not query:
        return False
        
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    
    logger.info(f"User {user_id} pressed invest button")
    
    # Create investment options keyboard
    keyboard = [
        [InlineKeyboardButton("🧠 Smart Invest", callback_data="smart_invest")],
        [InlineKeyboardButton("📈 High APR Pools", callback_data="high_apr")],
        [InlineKeyboardButton("⭐ Top Pools", callback_data="top_pools")],
        [InlineKeyboardButton("💼 My Investments", callback_data="my_investments")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "*💰 Investment Options*\n\n"
        "Choose how you'd like to invest:\n\n"
        "• *Smart Invest*: AI-powered investment recommendations\n"
        "• *High APR Pools*: Pools with highest yields\n"
        "• *Top Pools*: Most popular liquidity pools\n"
        "• *My Investments*: Track your existing investments",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )
    
    return True

async def handle_explore_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle the 'explore_pools' button click
    """
    query = update.callback_query
    if not query:
        return False
        
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    
    logger.info(f"User {user_id} pressed explore pools button")
    
    # Show pool exploration options
    keyboard = [
        [InlineKeyboardButton("📊 View All Pools", callback_data="pools")],
        [InlineKeyboardButton("📈 High APR Pools", callback_data="high_apr")],
        [InlineKeyboardButton("🔍 Search by Token", callback_data="token_search")],
        [InlineKeyboardButton("🔮 View Predictions", callback_data="predictions")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "*🧭 Explore Liquidity Pools*\n\n"
        "What would you like to explore?\n\n"
        "• *View All Pools*: See all available liquidity pools\n"
        "• *High APR Pools*: Find the highest yield opportunities\n"
        "• *Search by Token*: Find pools containing a specific token\n"
        "• *View Predictions*: See AI predictions for pool performance",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )
    
    return True

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'help' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed help button")
    
    keyboard = [
        [InlineKeyboardButton("📚 Getting Started", callback_data="help_getting_started")],
        [InlineKeyboardButton("🔡 Command List", callback_data="help_commands")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("🌐 Visit Website", url="https://filot.ai")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "*ℹ️ Help & Support*\n\n"
        "What can we help you with today?\n\n"
        "• *Getting Started*: Learn how to use FiLot bot\n"
        "• *Command List*: See all available commands\n"
        "• *FAQ*: Browse frequently asked questions\n"
        "• *Visit Website*: View our full documentation",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def handle_back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'back_to_main' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed back to main menu button")
    
    # Create main menu keyboard
    keyboard = [
        [InlineKeyboardButton("💰 Invest", callback_data="invest")],
        [InlineKeyboardButton("🧭 Explore Pools", callback_data="explore_pools")],
        [InlineKeyboardButton("👤 My Account", callback_data="account")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]
    
    await query.edit_message_text(
        "*🤖 FiLot - Your Agentic Financial Assistant*\n\n"
        "Welcome to FiLot, your intelligent cryptocurrency investment companion.\n\n"
        "What would you like to do today?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )
    
    # Update user's menu state
    await set_menu_state(update, context, MenuType.MAIN)

async def handle_wallet_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'wallet_settings' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed wallet settings button")
    
    keyboard = [
        [InlineKeyboardButton("🔌 Connect Wallet", callback_data="walletconnect")],
        [InlineKeyboardButton("📝 Enter Address Manually", callback_data="enter_address")],
        [InlineKeyboardButton("🔄 Refresh Wallet Data", callback_data="refresh_wallet")],
        [InlineKeyboardButton("⬅️ Back to Account", callback_data="account")]
    ]
    
    await query.edit_message_text(
        "*💳 Wallet Settings*\n\n"
        "Manage your wallet connections and settings.\n\n"
        "• Connect your wallet to enable automated investment features\n"
        "• Your wallet is connected in read-only mode for security\n"
        "• FiLot never has access to your private keys",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def handle_update_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'update_profile' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed update profile button")
    
    keyboard = [
        [InlineKeyboardButton("🎯 Update Risk Profile", callback_data="update_risk")],
        [InlineKeyboardButton("⏱️ Update Investment Horizon", callback_data="update_horizon")],
        [InlineKeyboardButton("🏆 Update Investment Goals", callback_data="update_goals")],
        [InlineKeyboardButton("⬅️ Back to Account", callback_data="account")]
    ]
    
    await query.edit_message_text(
        "*⚙️ Update Profile*\n\n"
        "Update your investment preferences and profile settings.\n\n"
        "These settings help us provide personalized recommendations tailored to your investment style.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def handle_subscription_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'subscription_settings' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed subscription settings button")
    
    keyboard = [
        [InlineKeyboardButton("🔔 Enable Notifications", callback_data="enable_notifications")],
        [InlineKeyboardButton("🔕 Disable Notifications", callback_data="disable_notifications")],
        [InlineKeyboardButton("📋 Notification Preferences", callback_data="notification_preferences")],
        [InlineKeyboardButton("⬅️ Back to Account", callback_data="account")]
    ]
    
    await query.edit_message_text(
        "*🔔 Subscription Settings*\n\n"
        "Manage your notification preferences and subscriptions.\n\n"
        "Stay informed about market movements, pool performance, and investment opportunities.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def handle_token_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'token_search' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed token search button")
    
    # List of popular tokens for quick search
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

async def handle_predictions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'predictions' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed predictions button")
    
    keyboard = [
        [InlineKeyboardButton("📈 Rising Pools", callback_data="rising_pools")],
        [InlineKeyboardButton("📉 Declining Pools", callback_data="declining_pools")],
        [InlineKeyboardButton("🎯 Most Stable", callback_data="stable_pools")],
        [InlineKeyboardButton("⬅️ Back to Explore", callback_data="explore_pools")]
    ]
    
    await query.edit_message_text(
        "*🔮 Pool Predictions & Analytics*\n\n"
        "View AI-powered predictions on pool performance.\n\n"
        "Our proprietary algorithms analyze historical data and market trends to predict pool performance over different time horizons.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def handle_my_investments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'my_investments' button click
    """
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"User {user_id} pressed my investments button")
    
    # Check if user has wallet connected
    has_wallet = False  # Replace with actual check
    
    if not has_wallet:
        keyboard = [
            [InlineKeyboardButton("🔌 Connect Wallet", callback_data="walletconnect")],
            [InlineKeyboardButton("⬅️ Back to Invest", callback_data="invest")]
        ]
        
        await query.edit_message_text(
            "*💼 My Investments*\n\n"
            "To view your investments, you need to connect your wallet first.\n\n"
            "Connect your wallet to track your liquidity positions and investment performance.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📊 Performance Overview", callback_data="investment_performance")],
            [InlineKeyboardButton("📋 Active Positions", callback_data="active_positions")],
            [InlineKeyboardButton("📜 Transaction History", callback_data="transaction_history")],
            [InlineKeyboardButton("⬅️ Back to Invest", callback_data="invest")]
        ]
        
        await query.edit_message_text(
            "*💼 My Investments*\n\n"
            "View and manage your current investment positions.\n\n"
            "Monitor performance, track active positions, and review your transaction history.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

# Helper functions (stubs)
def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile from database - placeholder implementation"""
    try:
        user = User.query.get(user_id)
        if user:
            return {
                "username": user.username,
                "risk_profile": user.risk_profile,
                "investment_horizon": user.investment_horizon,
                "is_subscribed": user.is_subscribed,
                "created_at": user.created_at.strftime("%Y-%m-%d")
            }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
    return None

def create_user_profile(user_id: int, username: str = None, first_name: str = None, last_name: str = None) -> Optional[Dict[str, Any]]:
    """Create a new user profile - placeholder implementation"""
    try:
        # Check if user already exists
        user = User.query.get(user_id)
        if user:
            return get_user_profile(user_id)
            
        # Create new user
        new_user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_subscribed=False,
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        
        return get_user_profile(user_id)
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return None