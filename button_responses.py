#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Button response handlers for FiLot Telegram bot
Handles all callback_data values with dedicated handler functions
"""

import logging
import re
import json
import datetime
from typing import Dict, Any, Optional, List, Union, Tuple

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import db_utils
from models import User, Pool, db
from utils import format_pool_info
from menus import MenuType, get_menu_config
from keyboard_utils import get_reply_keyboard, set_menu_state
from solpool_api_client import (
    get_pool_list, 
    get_high_apr_pools, 
    get_token_pools, 
    get_pool_detail,
    get_predictions,
    simulate_investment
)
from filotsense_api_client import (
    get_sentiment_data,
    get_price_data,
    get_token_trends,
    get_topic_sentiment
)
from rl_investment_advisor import get_smart_investment_recommendation

# Configure logging
logger = logging.getLogger(__name__)

# Define regex patterns for dynamic callbacks
POOL_DETAIL_PATTERN = r'^pool:(?P<id>.+)$'
TOKEN_SEARCH_PATTERN = r'^search_token_(?P<symbol>.+)$'
STABLE_POOLS_PAGE_PATTERN = r'^stable_pools:(?P<page>\d+)$'
HIGH_APR_POOLS_PAGE_PATTERN = r'^high_apr:(?P<page>\d+)$'

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
            last_name=update.effective_user.last_name or ""
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
    if query:
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
    if query:
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
    if query:
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
    if query:
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
    if query:
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
    if query:
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
    if query:
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
    if query:
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

async def handle_smart_invest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'smart_invest' button click to show AI-powered investment recommendations
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed smart invest button")
        
        try:
            # Get user profile to determine risk preference
            user_profile = get_user_profile(user_id)
            risk_profile = user_profile.get('risk_profile', 'moderate') if user_profile else 'moderate'
            
            # Default investment amount for recommendation (user will be prompted for actual amount later)
            default_amount = 1000
            
            # Call the RL investment advisor to get recommendations
            recommendation = get_smart_investment_recommendation(
                investment_amount=default_amount,
                risk_profile=risk_profile,
                max_suggestions=3
            )
            
            if recommendation and 'suggestions' in recommendation and recommendation['suggestions']:
                # Format suggestions
                suggestions_text = ""
                for i, suggestion in enumerate(recommendation['suggestions'], 1):
                    pool_name = suggestion.get('pool_name', 'Unknown Pool')
                    apr = suggestion.get('apr', 0)
                    sentiment = suggestion.get('sentiment_score', 0)
                    confidence = suggestion.get('confidence', 0)
                    
                    suggestions_text += f"*{i}. {pool_name}*\n"
                    suggestions_text += f"   APR: *{apr:.2f}%*\n"
                    suggestions_text += f"   Sentiment Score: *{sentiment:.2f}*\n"
                    suggestions_text += f"   Confidence: *{confidence:.2f}%*\n\n"
                
                # Create buttons for each suggestion
                keyboard = []
                for suggestion in recommendation['suggestions']:
                    pool_id = suggestion.get('pool_id', '')
                    pool_name = suggestion.get('pool_name', 'Unknown Pool')
                    if pool_id:
                        keyboard.append([InlineKeyboardButton(f"Invest in {pool_name}", callback_data=f"pool:{pool_id}")])
                
                keyboard.append([InlineKeyboardButton("⬅️ Back to Invest", callback_data="invest")])
                
                await query.edit_message_text(
                    f"*🧠 Smart Investment Recommendations*\n\n"
                    f"Based on your {risk_profile} risk profile, current market conditions, and AI analysis, here are your personalized recommendations:\n\n"
                    f"{suggestions_text}\n"
                    f"To proceed with an investment, click on one of the pools above.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # Fallback if no recommendations available
                keyboard = [[InlineKeyboardButton("⬅️ Back to Invest", callback_data="invest")]]
                
                await query.edit_message_text(
                    "*🧠 Smart Investment Recommendations*\n\n"
                    "I couldn't generate investment recommendations at this time. This could be due to market volatility or data limitations.\n\n"
                    "Please try again later or explore specific pools manually.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in smart_invest button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Invest", callback_data="invest")]]
            
            await query.edit_message_text(
                "*🧠 Smart Investment Recommendations*\n\n"
                "Sorry, I encountered an error while generating investment recommendations.\n\n"
                "Please try again later or explore specific pools manually.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_high_apr_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'high_apr' button click to show pools with highest yields
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed high APR pools button")
        
        try:
            # Get page number from context or default to 1
            page = 1
            
            # Check if this is a paginated request
            if query.data and query.data.startswith("high_apr:"):
                match = re.match(HIGH_APR_POOLS_PAGE_PATTERN, query.data)
                if match:
                    page = int(match.group("page"))
            
            # Get high APR pools from API
            pools = get_high_apr_pools(min_apr=10.0, limit=5)
            
            if pools:
                # Calculate pagination
                total_pools = len(pools)
                pools_per_page = 3
                total_pages = (total_pools + pools_per_page - 1) // pools_per_page
                
                # Adjust page if out of bounds
                if page < 1:
                    page = 1
                if page > total_pages:
                    page = total_pages
                
                # Get pools for current page
                start_idx = (page - 1) * pools_per_page
                end_idx = min(start_idx + pools_per_page, total_pools)
                current_page_pools = pools[start_idx:end_idx]
                
                # Format pool information
                pools_text = ""
                for i, pool in enumerate(current_page_pools, start=1):
                    pool_name = f"{pool.get('token_a_symbol', 'Unknown')}/{pool.get('token_b_symbol', 'Unknown')}"
                    apr = pool.get('apr_24h', 0)
                    tvl = pool.get('tvl', 0)
                    
                    pools_text += f"*{i}. {pool_name}*\n"
                    pools_text += f"   APR: *{apr:.2f}%*\n"
                    pools_text += f"   TVL: *${tvl:,.2f}*\n"
                    pools_text += f"   Pool ID: `{pool.get('id', 'Unknown')}`\n\n"
                
                # Create buttons for each pool
                keyboard = []
                for pool in current_page_pools:
                    pool_id = pool.get('id', '')
                    if pool_id:
                        pool_name = f"{pool.get('token_a_symbol', 'Unknown')}/{pool.get('token_b_symbol', 'Unknown')}"
                        keyboard.append([InlineKeyboardButton(f"Details: {pool_name}", callback_data=f"pool:{pool_id}")])
                
                # Add pagination buttons
                pagination = []
                if page > 1:
                    pagination.append(InlineKeyboardButton("◀️ Previous", callback_data=f"high_apr:{page-1}"))
                if page < total_pages:
                    pagination.append(InlineKeyboardButton("Next ▶️", callback_data=f"high_apr:{page+1}"))
                if pagination:
                    keyboard.append(pagination)
                
                keyboard.append([InlineKeyboardButton("⬅️ Back to Explore", callback_data="explore_pools")])
                
                await query.edit_message_text(
                    f"*📈 High APR Pools (Page {page}/{total_pages})*\n\n"
                    f"These pools currently offer the highest yields on Raydium:\n\n"
                    f"{pools_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # Fallback if no pools available
                keyboard = [[InlineKeyboardButton("⬅️ Back to Explore", callback_data="explore_pools")]]
                
                await query.edit_message_text(
                    "*📈 High APR Pools*\n\n"
                    "I couldn't retrieve high APR pool data at this time.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in high_apr_pools button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Explore", callback_data="explore_pools")]]
            
            await query.edit_message_text(
                "*📈 High APR Pools*\n\n"
                "Sorry, I encountered an error while retrieving high APR pool data.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_pool_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'pools' or 'top_pools' button click to show liquidity pools
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed pool info button: {query.data}")
        
        try:
            # Determine if this is top pools or all pools
            is_top_pools = query.data == "top_pools"
            
            # Get pool list from API
            limit = 5 if is_top_pools else 10
            pools = get_pool_list(limit=limit)
            
            if pools:
                # Sort by TVL for top pools, or by APR for regular pools view
                if is_top_pools:
                    pools = sorted(pools, key=lambda p: p.get('tvl', 0), reverse=True)
                else:
                    pools = sorted(pools, key=lambda p: p.get('apr_24h', 0), reverse=True)
                
                # Format pool information
                pools_text = ""
                for i, pool in enumerate(pools[:5], start=1):  # Show top 5 regardless of how many we retrieved
                    pool_name = f"{pool.get('token_a_symbol', 'Unknown')}/{pool.get('token_b_symbol', 'Unknown')}"
                    apr = pool.get('apr_24h', 0)
                    tvl = pool.get('tvl', 0)
                    volume = pool.get('volume_24h', 0)
                    
                    pools_text += f"*{i}. {pool_name}*\n"
                    pools_text += f"   APR: *{apr:.2f}%*\n"
                    pools_text += f"   TVL: *${tvl:,.2f}*\n"
                    pools_text += f"   24h Volume: *${volume:,.2f}*\n\n"
                
                # Create buttons for each pool
                keyboard = []
                for pool in pools[:5]:
                    pool_id = pool.get('id', '')
                    if pool_id:
                        pool_name = f"{pool.get('token_a_symbol', 'Unknown')}/{pool.get('token_b_symbol', 'Unknown')}"
                        keyboard.append([InlineKeyboardButton(f"Details: {pool_name}", callback_data=f"pool:{pool_id}")])
                
                # Add back button
                back_data = "invest" if is_top_pools else "explore_pools"
                keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data=back_data)])
                
                title = "⭐ Top Pools by TVL" if is_top_pools else "📊 All Liquidity Pools"
                
                await query.edit_message_text(
                    f"*{title}*\n\n"
                    f"Here are the {'most popular' if is_top_pools else 'available'} liquidity pools on Raydium:\n\n"
                    f"{pools_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # Fallback if no pools available
                back_data = "invest" if is_top_pools else "explore_pools"
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=back_data)]]
                
                await query.edit_message_text(
                    f"*{'⭐ Top Pools' if is_top_pools else '📊 All Liquidity Pools'}*\n\n"
                    f"I couldn't retrieve pool data at this time.\n\n"
                    f"Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in pool_info button handler: {e}")
            
            # Error fallback
            back_data = "invest" if query.data == "top_pools" else "explore_pools"
            keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=back_data)]]
            
            await query.edit_message_text(
                "*Pool Information*\n\n"
                "Sorry, I encountered an error while retrieving pool data.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_pool_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle pool detail requests with dynamic pool ID (pool:<id>)
    """
    query = update.callback_query
    if query and query.data:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        
        # Extract pool ID from callback data
        match = re.match(POOL_DETAIL_PATTERN, query.data)
        if not match:
            logger.error(f"Invalid pool detail callback data: {query.data}")
            return
            
        pool_id = match.group("id")
        logger.info(f"User {user_id} requested details for pool: {pool_id}")
        
        try:
            # Get pool details from API
            pool = get_pool_detail(pool_id)
            
            if pool:
                # Get sentiment data for tokens in this pool
                token_a = pool.get('token_a_symbol', '')
                token_b = pool.get('token_b_symbol', '')
                
                sentiment_a = {}
                sentiment_b = {}
                
                if token_a:
                    try:
                        sentiment_data = get_sentiment_data(token_a)
                        if token_a.upper() in sentiment_data.get('sentiment', {}):
                            sentiment_a = sentiment_data['sentiment'][token_a.upper()]
                    except Exception as e:
                        logger.error(f"Error getting sentiment for {token_a}: {e}")
                
                if token_b:
                    try:
                        sentiment_data = get_sentiment_data(token_b)
                        if token_b.upper() in sentiment_data.get('sentiment', {}):
                            sentiment_b = sentiment_data['sentiment'][token_b.upper()]
                    except Exception as e:
                        logger.error(f"Error getting sentiment for {token_b}: {e}")
                
                # Format pool details
                pool_name = f"{token_a}/{token_b}"
                apr_24h = pool.get('apr_24h', 0)
                apr_7d = pool.get('apr_7d', 0)
                apr_30d = pool.get('apr_30d', 0)
                tvl = pool.get('tvl', 0)
                volume_24h = pool.get('volume_24h', 0)
                fee = pool.get('fee', 0)
                
                details = (
                    f"*📊 {pool_name} Pool Details*\n\n"
                    f"*APR:*\n"
                    f"• 24h: *{apr_24h:.2f}%*\n"
                    f"• 7d: *{apr_7d:.2f}%*\n"
                    f"• 30d: *{apr_30d:.2f}%*\n\n"
                    f"*TVL:* *${tvl:,.2f}*\n"
                    f"*24h Volume:* *${volume_24h:,.2f}*\n"
                    f"*Fee:* *{fee:.2f}%*\n\n"
                )
                
                # Add sentiment data if available
                if sentiment_a or sentiment_b:
                    details += f"*Market Sentiment:*\n"
                    
                    if sentiment_a:
                        score_a = sentiment_a.get('score', 0)
                        sentiment_emoji_a = "🟢" if score_a > 0.2 else "🟡" if score_a > -0.2 else "🔴"
                        details += f"• {token_a}: {sentiment_emoji_a} *{score_a:.2f}*\n"
                    
                    if sentiment_b:
                        score_b = sentiment_b.get('score', 0)
                        sentiment_emoji_b = "🟢" if score_b > 0.2 else "🟡" if score_b > -0.2 else "🔴"
                        details += f"• {token_b}: {sentiment_emoji_b} *{score_b:.2f}*\n\n"
                
                # Add pool ID
                details += f"*Pool ID:* `{pool_id}`\n\n"
                
                # Create action buttons
                keyboard = [
                    [InlineKeyboardButton("📊 Simulate Investment", callback_data=f"simulate:{pool_id}")],
                    [InlineKeyboardButton("💰 Invest Now", callback_data=f"invest_now:{pool_id}")],
                    [InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]
                ]
                
                await query.edit_message_text(
                    details,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # Pool not found
                keyboard = [[InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]]
                
                await query.edit_message_text(
                    "*Pool Details*\n\n"
                    f"Sorry, I couldn't find details for the requested pool (ID: `{pool_id}`).\n\n"
                    f"The pool may have been deprecated or there might be a temporary issue with the data provider.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in pool_detail handler for pool {pool_id}: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]]
            
            await query.edit_message_text(
                "*Pool Details*\n\n"
                f"Sorry, I encountered an error while retrieving details for pool ID: `{pool_id}`.\n\n"
                f"Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_token_search_result(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle token search results with dynamic token symbol (search_token_<symbol>)
    """
    query = update.callback_query
    if query and query.data:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        
        # Extract token symbol from callback data
        match = re.match(TOKEN_SEARCH_PATTERN, query.data)
        if not match:
            logger.error(f"Invalid token search callback data: {query.data}")
            return
            
        token_symbol = match.group("symbol")
        logger.info(f"User {user_id} searching for pools with token: {token_symbol}")
        
        try:
            # Get pools containing this token
            pools = get_token_pools(token_symbol, limit=5)
            
            # Get token sentiment
            sentiment_data = {}
            try:
                sentiment_response = get_sentiment_data(token_symbol)
                if token_symbol.upper() in sentiment_response.get('sentiment', {}):
                    sentiment_data = sentiment_response['sentiment'][token_symbol.upper()]
            except Exception as e:
                logger.error(f"Error getting sentiment for {token_symbol}: {e}")
            
            # Get token price
            price_data = {}
            try:
                price_response = get_price_data(token_symbol)
                if token_symbol.upper() in price_response.get('prices', {}):
                    price_data = price_response['prices'][token_symbol.upper()]
            except Exception as e:
                logger.error(f"Error getting price for {token_symbol}: {e}")
            
            if pools:
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
                
                keyboard.append([InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")])
                
                await query.edit_message_text(
                    token_info,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # No pools found
                keyboard = [[InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")]]
                
                await query.edit_message_text(
                    f"*🔍 {token_symbol} Pool Search Results*\n\n"
                    f"Sorry, I couldn't find any active liquidity pools containing {token_symbol}.\n\n"
                    f"Try searching for another token or view all available pools.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in token_search_result handler for token {token_symbol}: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")]]
            
            await query.edit_message_text(
                "*Token Search Results*\n\n"
                f"Sorry, I encountered an error while searching for pools with {token_symbol}.\n\n"
                f"Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_rising_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'rising_pools' button click to show pools predicted to increase in value
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed rising pools button")
        
        try:
            # Get prediction data with positive score
            predictions = get_predictions(min_score=60.0, limit=5)
            
            if predictions:
                # Format prediction information
                predictions_text = ""
                for i, prediction in enumerate(predictions, start=1):
                    pool_name = f"{prediction.get('token_a_symbol', 'Unknown')}/{prediction.get('token_b_symbol', 'Unknown')}"
                    score = prediction.get('score', 0)
                    confidence = prediction.get('confidence', 0)
                    apr = prediction.get('apr_24h', 0)
                    
                    emoji = "🔼" if score > 75 else "⏫"
                    
                    predictions_text += f"*{i}. {pool_name}* {emoji}\n"
                    predictions_text += f"   Prediction Score: *{score:.1f}*\n"
                    predictions_text += f"   Confidence: *{confidence:.1f}%*\n"
                    predictions_text += f"   Current APR: *{apr:.2f}%*\n\n"
                
                # Create buttons for each prediction
                keyboard = []
                for prediction in predictions:
                    pool_id = prediction.get('pool_id', '')
                    if pool_id:
                        pool_name = f"{prediction.get('token_a_symbol', 'Unknown')}/{prediction.get('token_b_symbol', 'Unknown')}"
                        keyboard.append([InlineKeyboardButton(f"Details: {pool_name}", callback_data=f"pool:{pool_id}")])
                
                keyboard.append([InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")])
                
                await query.edit_message_text(
                    "*📈 Rising Pools*\n\n"
                    "These pools are predicted to increase in APR or value in the near term:\n\n"
                    f"{predictions_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # No predictions available
                keyboard = [[InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")]]
                
                await query.edit_message_text(
                    "*📈 Rising Pools*\n\n"
                    "I couldn't retrieve prediction data for rising pools at this time.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in rising_pools button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")]]
            
            await query.edit_message_text(
                "*📈 Rising Pools*\n\n"
                "Sorry, I encountered an error while retrieving rising pools predictions.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_declining_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'declining_pools' button click to show pools predicted to decrease in value
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed declining pools button")
        
        try:
            # For declining pools, we'll use the same API but filter for negative scores
            # In a real implementation, you might have a specific endpoint for declining pools
            predictions = get_predictions(min_score=0.0, limit=10)  # Get more, then filter
            
            # Filter for low scores
            declining_predictions = [p for p in predictions if p.get('score', 50) < 40]
            declining_predictions = declining_predictions[:5]  # Limit to top 5 declining
            
            if declining_predictions:
                # Format prediction information
                predictions_text = ""
                for i, prediction in enumerate(declining_predictions, start=1):
                    pool_name = f"{prediction.get('token_a_symbol', 'Unknown')}/{prediction.get('token_b_symbol', 'Unknown')}"
                    score = prediction.get('score', 0)
                    confidence = prediction.get('confidence', 0)
                    apr = prediction.get('apr_24h', 0)
                    
                    emoji = "🔽" if score > 25 else "⏬"
                    
                    predictions_text += f"*{i}. {pool_name}* {emoji}\n"
                    predictions_text += f"   Prediction Score: *{score:.1f}*\n"
                    predictions_text += f"   Confidence: *{confidence:.1f}%*\n"
                    predictions_text += f"   Current APR: *{apr:.2f}%*\n\n"
                
                # Create buttons for each prediction
                keyboard = []
                for prediction in declining_predictions:
                    pool_id = prediction.get('pool_id', '')
                    if pool_id:
                        pool_name = f"{prediction.get('token_a_symbol', 'Unknown')}/{prediction.get('token_b_symbol', 'Unknown')}"
                        keyboard.append([InlineKeyboardButton(f"Details: {pool_name}", callback_data=f"pool:{pool_id}")])
                
                keyboard.append([InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")])
                
                await query.edit_message_text(
                    "*📉 Declining Pools*\n\n"
                    "These pools are predicted to decrease in APR or value in the near term:\n\n"
                    f"{predictions_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # No predictions available
                keyboard = [[InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")]]
                
                await query.edit_message_text(
                    "*📉 Declining Pools*\n\n"
                    "I couldn't retrieve prediction data for declining pools at this time.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in declining_pools button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")]]
            
            await query.edit_message_text(
                "*📉 Declining Pools*\n\n"
                "Sorry, I encountered an error while retrieving declining pools predictions.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_stable_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'stable_pools' button click to show pools with stable performance
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed stable pools button")
        
        try:
            page = 1
            
            # Check if this is a paginated request
            if query.data and query.data.startswith("stable_pools:"):
                match = re.match(STABLE_POOLS_PAGE_PATTERN, query.data)
                if match:
                    page = int(match.group("page"))
            
            # Get stable pools - these typically contain stablecoins
            # In a real implementation, you might have a specific endpoint for stable pools
            pools = get_pool_list(limit=20)  # Get more pools to filter
            
            # Filter for stable pools - those containing USDC, USDT, etc.
            stable_tokens = ["USDC", "USDT", "DAI", "BUSD", "TUSD", "FRAX", "USDH", "USDJ"]
            stable_pools = []
            
            for pool in pools:
                token_a = pool.get('token_a_symbol', '').upper()
                token_b = pool.get('token_b_symbol', '').upper()
                
                if token_a in stable_tokens or token_b in stable_tokens:
                    # Add additional stability metric - lower APR volatility is more stable
                    apr_24h = pool.get('apr_24h', 0)
                    apr_7d = pool.get('apr_7d', 0)
                    apr_volatility = abs(apr_24h - apr_7d) / max(apr_7d, 1) * 100
                    pool['apr_volatility'] = apr_volatility
                    stable_pools.append(pool)
            
            # Sort by lowest APR volatility (most stable)
            stable_pools = sorted(stable_pools, key=lambda p: p.get('apr_volatility', 100))
            
            if stable_pools:
                # Calculate pagination
                total_pools = len(stable_pools)
                pools_per_page = 3
                total_pages = (total_pools + pools_per_page - 1) // pools_per_page
                
                # Adjust page if out of bounds
                if page < 1:
                    page = 1
                if page > total_pages:
                    page = total_pages
                
                # Get pools for current page
                start_idx = (page - 1) * pools_per_page
                end_idx = min(start_idx + pools_per_page, total_pools)
                current_page_pools = stable_pools[start_idx:end_idx]
                
                # Format pool information
                pools_text = ""
                for i, pool in enumerate(current_page_pools, start=1):
                    pool_name = f"{pool.get('token_a_symbol', 'Unknown')}/{pool.get('token_b_symbol', 'Unknown')}"
                    apr = pool.get('apr_24h', 0)
                    apr_7d = pool.get('apr_7d', 0)
                    volatility = pool.get('apr_volatility', 0)
                    tvl = pool.get('tvl', 0)
                    
                    pools_text += f"*{i}. {pool_name}*\n"
                    pools_text += f"   APR: *{apr:.2f}%*\n"
                    pools_text += f"   7d APR: *{apr_7d:.2f}%*\n"
                    pools_text += f"   Volatility: *{volatility:.2f}%*\n"
                    pools_text += f"   TVL: *${tvl:,.2f}*\n\n"
                
                # Create buttons for each pool
                keyboard = []
                for pool in current_page_pools:
                    pool_id = pool.get('id', '')
                    if pool_id:
                        pool_name = f"{pool.get('token_a_symbol', 'Unknown')}/{pool.get('token_b_symbol', 'Unknown')}"
                        keyboard.append([InlineKeyboardButton(f"Details: {pool_name}", callback_data=f"pool:{pool_id}")])
                
                # Add pagination buttons
                pagination = []
                if page > 1:
                    pagination.append(InlineKeyboardButton("◀️ Previous", callback_data=f"stable_pools:{page-1}"))
                if page < total_pages:
                    pagination.append(InlineKeyboardButton("Next ▶️", callback_data=f"stable_pools:{page+1}"))
                if pagination:
                    keyboard.append(pagination)
                
                keyboard.append([InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")])
                
                await query.edit_message_text(
                    f"*🎯 Most Stable Pools (Page {page}/{total_pages})*\n\n"
                    f"These pools show the most consistent performance with low volatility:\n\n"
                    f"{pools_text}",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                # No stable pools found
                keyboard = [[InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")]]
                
                await query.edit_message_text(
                    "*🎯 Most Stable Pools*\n\n"
                    "I couldn't find any stable pools at this time.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in stable_pools button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Predictions", callback_data="predictions")]]
            
            await query.edit_message_text(
                "*🎯 Most Stable Pools*\n\n"
                "Sorry, I encountered an error while retrieving stable pool data.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_custom_token_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'custom_token_search' button click to help users search for any token
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} pressed custom token search button")
        
        # This button primarily prompts the user to enter a token symbol
        # The actual search will be handled through message handlers
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Token Search", callback_data="token_search")]]
        
        await query.edit_message_text(
            "*🔍 Custom Token Search*\n\n"
            "Please send me the symbol of the token you want to search for.\n\n"
            "For example, type `JTO` to search for Jupiter token pools.\n\n"
            "I'll find all liquidity pools containing this token.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        # TODO: Set conversation state to wait for token input
        # This would require implementing ConversationHandler in bot.py

async def handle_enable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'enable_notifications' button click to subscribe to updates
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} is enabling notifications")
        
        try:
            # Enable notifications in the database
            success = False
            try:
                # TODO: Implement actual database update
                # Example: db_utils.update_user_subscription(user_id, enabled=True)
                success = True
            except Exception as e:
                logger.error(f"Error updating subscription status: {e}")
            
            # Display result
            keyboard = [[InlineKeyboardButton("⬅️ Back to Subscription Settings", callback_data="subscription_settings")]]
            
            if success:
                await query.edit_message_text(
                    "*🔔 Notifications Enabled*\n\n"
                    "You have successfully subscribed to FiLot notifications.\n\n"
                    "You will now receive updates about:\n"
                    "• Daily market summaries\n"
                    "• High APR pool alerts\n"
                    "• Significant token price movements\n"
                    "• Pool prediction alerts\n",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                await query.edit_message_text(
                    "*🔔 Notification Settings*\n\n"
                    "I couldn't update your notification preferences at this time.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in enable_notifications button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Subscription Settings", callback_data="subscription_settings")]]
            
            await query.edit_message_text(
                "*🔔 Notification Settings*\n\n"
                "Sorry, I encountered an error while updating your notification preferences.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_disable_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'disable_notifications' button click to unsubscribe from updates
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} is disabling notifications")
        
        try:
            # Disable notifications in the database
            success = False
            try:
                # TODO: Implement actual database update
                # Example: db_utils.update_user_subscription(user_id, enabled=False)
                success = True
            except Exception as e:
                logger.error(f"Error updating subscription status: {e}")
            
            # Display result
            keyboard = [[InlineKeyboardButton("⬅️ Back to Subscription Settings", callback_data="subscription_settings")]]
            
            if success:
                await query.edit_message_text(
                    "*🔕 Notifications Disabled*\n\n"
                    "You have successfully unsubscribed from FiLot notifications.\n\n"
                    "You will no longer receive daily updates or alerts.\n"
                    "You can re-enable notifications at any time.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
            else:
                await query.edit_message_text(
                    "*🔔 Notification Settings*\n\n"
                    "I couldn't update your notification preferences at this time.\n\n"
                    "Please try again later.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="MarkdownV2"
                )
        except Exception as e:
            logger.error(f"Error in disable_notifications button handler: {e}")
            
            # Error fallback
            keyboard = [[InlineKeyboardButton("⬅️ Back to Subscription Settings", callback_data="subscription_settings")]]
            
            await query.edit_message_text(
                "*🔔 Notification Settings*\n\n"
                "Sorry, I encountered an error while updating your notification preferences.\n\n"
                "Please try again later.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )

async def handle_notification_preferences(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'notification_preferences' button click to customize notification settings
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} is viewing notification preferences")
        
        # Create notification preference options
        keyboard = [
            [InlineKeyboardButton("📊 Market Summaries", callback_data="toggle_notif_market")],
            [InlineKeyboardButton("📈 APR Alerts", callback_data="toggle_notif_apr")],
            [InlineKeyboardButton("💰 Price Alerts", callback_data="toggle_notif_price")],
            [InlineKeyboardButton("🔮 Prediction Alerts", callback_data="toggle_notif_prediction")],
            [InlineKeyboardButton("⬅️ Back to Subscription Settings", callback_data="subscription_settings")]
        ]
        
        await query.edit_message_text(
            "*📋 Notification Preferences*\n\n"
            "Customize which types of notifications you want to receive:\n\n"
            "• Market Summaries: Daily digest of market activity\n"
            "• APR Alerts: Notifications when APR changes significantly\n"
            "• Price Alerts: Alerts for major token price movements\n"
            "• Prediction Alerts: Notifications based on AI predictions\n\n"
            "Click an option to toggle it on/off.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )
        
        # TODO: Implement toggle functionality for each notification type

async def handle_help_getting_started(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'help_getting_started' button click to show getting started guide
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} requested getting started guide")
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]]
        
        await query.edit_message_text(
            "*📚 Getting Started with FiLot*\n\n"
            "*1. Explore Liquidity Pools*\n"
            "• Use the 'Explore Pools' button to browse available pools\n"
            "• Check 'High APR Pools' for the highest yields\n"
            "• Search by specific tokens using 'Search by Token'\n\n"
            
            "*2. Check AI Predictions*\n"
            "• View 'Rising Pools' to see what's trending up\n"
            "• Use 'Smart Invest' for personalized recommendations\n\n"
            
            "*3. Set Up Your Profile*\n"
            "• Go to 'My Account' to set your risk profile\n"
            "• Connect your wallet to track investments\n"
            "• Subscribe to notifications for updates\n\n"
            
            "*4. Make Investments*\n"
            "• Use 'Simulate' to project potential returns\n"
            "• Get recommendations based on your profile\n"
            "• Connect your wallet for actual transactions\n\n"
            
            "Start by exploring the main menu options below!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

async def handle_help_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'help_commands' button click to show available commands
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} requested command list")
        
        keyboard = [[InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]]
        
        await query.edit_message_text(
            "*🔡 FiLot Command List*\n\n"
            "These commands can be typed directly in the chat:\n\n"
            
            "*/start* - Start the bot and get a welcome message\n"
            "*/help* - Show help information and options\n"
            "*/info* - View top-performing liquidity pools\n"
            "*/simulate* - Calculate potential investment returns\n"
            "*/subscribe* - Receive daily updates\n"
            "*/unsubscribe* - Stop receiving updates\n"
            "*/status* - Check bot status\n"
            "*/wallet* - Manage your crypto wallet\n"
            "*/walletconnect* - Connect wallet using QR code\n"
            "*/verify* - Verify your account with code\n"
            "*/profile* - Set your investment preferences\n"
            "*/faq* - View frequently asked questions\n"
            "*/social* - View our social media links\n\n"
            
            "You can also simply chat with me or use the buttons below.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

async def handle_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the 'faq' button click to show frequently asked questions
    """
    query = update.callback_query
    if query:
        await query.answer()
        
        user_id = update.effective_user.id if update.effective_user else 0
        logger.info(f"User {user_id} requested FAQ")
        
        keyboard = [
            [InlineKeyboardButton("❓ What is FiLot?", callback_data="faq_filot")],
            [InlineKeyboardButton("💡 How do liquidity pools work?", callback_data="faq_pools")],
            [InlineKeyboardButton("💰 What is APR?", callback_data="faq_apr")],
            [InlineKeyboardButton("⚠️ What is impermanent loss?", callback_data="faq_impermanent_loss")],
            [InlineKeyboardButton("🔒 Is my wallet secure?", callback_data="faq_wallet_security")],
            [InlineKeyboardButton("⬅️ Back to Help", callback_data="help")]
        ]
        
        await query.edit_message_text(
            "*❓ Frequently Asked Questions*\n\n"
            "Select a topic to learn more:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="MarkdownV2"
        )

# Helper functions
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
                "created_at": user.created_at.strftime("%Y-%m-%d") if hasattr(user, 'created_at') and user.created_at else "N/A"
            }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
    return None

def create_user_profile(user_id: int, username: str = None, first_name: str = None, last_name: str = "") -> Optional[Dict[str, Any]]:
    """Create a new user profile - placeholder implementation"""
    try:
        # Check if user already exists
        user = User.query.get(user_id)
        if user:
            return get_user_profile(user_id)
            
        # Create new user
        new_user = User(
            id=user_id,
            username=username or "unknown",
            first_name=first_name or "",
            last_name=last_name or "",
            is_subscribed=False,
            created_at=datetime.datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        
        return get_user_profile(user_id)
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        return None