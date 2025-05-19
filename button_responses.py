#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Button responses implementation for FiLot Telegram bot
Adds fully functional interactive buttons that perform real database operations
"""

import logging
import datetime
from typing import Dict, List, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app import app
from models import db, User, Pool
import solpool_api_client as solpool_api
import filotsense_api_client as sentiment_api
from smart_invest import start_smart_invest
from rl_investment_advisor import get_smart_investment_recommendation

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Button definitions for main menu callbacks
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

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle the 'help' button click
    """
    query = update.callback_query
    if not query:
        return False
        
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    
    logger.info(f"User {user_id} pressed help button")
    
    # Create help options keyboard
    keyboard = [
        [InlineKeyboardButton("📚 Commands", callback_data="commands")],
        [InlineKeyboardButton("❓ FAQ", callback_data="faq")],
        [InlineKeyboardButton("📱 Contact Support", callback_data="contact")],
        [InlineKeyboardButton("🔗 Social Links", callback_data="social")],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        "*ℹ️ Help Center*\n\n"
        "What can I help you with?\n\n"
        "• *Commands*: List of available bot commands\n"
        "• *FAQ*: Frequently asked questions\n"
        "• *Contact Support*: Get in touch with our team\n"
        "• *Social Links*: Our official social media accounts",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )
    
    return True

async def handle_smart_invest_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle smart_invest button press by redirecting to the conversation handler"""
    query = update.callback_query
    if not query:
        return False
        
    await query.answer()
    
    # First send a message to acknowledge
    await query.edit_message_text(
        "Starting Smart Investment flow...\n\n"
        "Please follow the prompts to get AI-powered investment recommendations."
    )
    
    # Create a new message for the conversation handler to work with
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="/smart_invest"
    )
    
    return True

async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle callback queries from main menu buttons, returning True if handled
    """
    if not update.callback_query:
        return False
        
    data = update.callback_query.data
    
    if data == "invest":
        return await handle_invest(update, context)
        
    elif data == "explore_pools":
        return await handle_explore_pools(update, context)
        
    elif data == "account":
        return await handle_account(update, context)
        
    elif data == "help":
        return await handle_help(update, context)
        
    elif data == "smart_invest":
        return await handle_smart_invest_button(update, context)
        
    # If we reach here, the callback wasn't handled
    logger.warning(f"Unhandled button callback: {data}")
    return False

# Database operations
def get_high_apr_pools(limit: int = 3) -> List[Dict[str, Any]]:
    """Get high APR pools from SolPool API with database fallback"""
    try:
        # First try to get data from SolPool API
        api_pools = None
        try:
            api_pools = solpool_api.get_high_apr_pools(limit)
        except Exception as api_error:
            logger.warning(f"Error accessing SolPool API: {api_error}")
        
        if api_pools and len(api_pools) > 0:
            logger.info(f"Successfully retrieved {len(api_pools)} high APR pools from SolPool API")
            
            # Convert to our expected format
            result = []
            for pool in api_pools:
                result.append({
                    'id': pool.get('id', ''),
                    'token_a': pool.get('token_a_symbol', ''),
                    'token_b': pool.get('token_b_symbol', ''),
                    'apr_24h': pool.get('apr_24h', 0),  # This is annual APR
                    'tvl': pool.get('tvl', 0),
                    'volume_24h': pool.get('volume_24h', 0),
                    'fee': pool.get('fee', 0),
                    'prediction_score': pool.get('prediction_score', 0),
                    'data_source': 'SolPool API'
                })
            return result
            
        # If API fails, fall back to database
        logger.warning("Failed to get high APR pools from API, falling back to database")
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,  # This is annual APR
                    'tvl': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0,
                    'fee': pool.fee or 0,
                    'data_source': 'Database'
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting high APR pools: {e}")
        return []

def get_pools(limit: int = 5) -> List[Dict[str, Any]]:
    """Get pool data from SolPool API with database fallback"""
    try:
        # First try to get data from SolPool API
        api_pools = None
        try:
            api_pools = solpool_api.get_pools(limit=limit)
        except Exception as api_error:
            logger.warning(f"Error accessing SolPool API: {api_error}")
        
        if api_pools and len(api_pools) > 0:
            logger.info(f"Successfully retrieved {len(api_pools)} pools from SolPool API")
            
            # Convert to our expected format
            result = []
            for pool in api_pools:
                result.append({
                    'id': pool.get('id', ''),
                    'token_a': pool.get('token_a_symbol', ''),
                    'token_b': pool.get('token_b_symbol', ''),
                    'apr_24h': pool.get('apr_24h', 0),  # This is annual APR
                    'tvl': pool.get('tvl', 0),
                    'volume_24h': pool.get('volume_24h', 0),
                    'fee': pool.get('fee', 0),
                    'dex': pool.get('dex', ''),
                    'data_source': 'SolPool API'
                })
            return result
            
        # If API fails, fall back to database
        logger.warning("Failed to get pools from API, falling back to database")
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,  # This is annual APR
                    'tvl': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0,
                    'fee': pool.fee or 0,
                    'data_source': 'Database'
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting pools: {e}")
        return []

def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile from database"""
    try:
        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            
            if user:
                return {
                    'id': user.id,
                    'username': user.username or 'Unknown',
                    'risk_profile': user.risk_profile or 'moderate',
                    'investment_horizon': user.investment_horizon or 'medium',
                    'investment_goals': user.investment_goals or 'Not specified',
                    'is_subscribed': user.is_subscribed or False,
                    'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
                }
            
            return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

def create_user_profile(user_id: int, username: str, first_name: str = None, last_name: str = None) -> Dict[str, Any]:
    """Create a new user profile in the database"""
    try:
        with app.app_context():
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                risk_profile='moderate',
                investment_horizon='medium',
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'id': user.id,
                'username': user.username or 'Unknown',
                'risk_profile': user.risk_profile or 'moderate',
                'investment_horizon': user.investment_horizon or 'medium',
                'investment_goals': user.investment_goals or 'Not specified',
                'is_subscribed': user.is_subscribed or False,
                'created_at': user.created_at.strftime('%Y-%m-%d')
            }
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        
        # Return fallback profile on error
        return {
            'id': user_id,
            'username': username or 'Unknown',
            'risk_profile': 'moderate',
            'investment_horizon': 'medium',
            'investment_goals': 'Not specified',
            'is_subscribed': False,
            'created_at': 'N/A'
        }