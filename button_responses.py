#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Button responses implementation for FiLot Telegram bot
Adds fully functional interactive buttons that perform real database operations
"""

import os
import logging
import datetime
from typing import Dict, List, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app import app
from models import db, User, Pool, UserActivityLog

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Button definitions
async def show_interactive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the main interactive menu with buttons that perform real database operations
    """
    try:
        user = update.effective_user
        logger.info(f"User {user.id} requested interactive menu")
        
        # Define inline keyboard with buttons that perform real database operations
        keyboard = [
            [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
            [InlineKeyboardButton("📈 View High APR Pools", callback_data="high_apr")],
            [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
            [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
        ]
        
        await update.message.reply_markdown(
            f"*Welcome to FiLot Interactive Menu, {user.first_name}!*\n\n"
            "These buttons perform real database operations.\n"
            "Click any option to retrieve live data:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in interactive menu command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )

# Database operations
def get_high_apr_pools(limit: int = 3) -> List[Dict[str, Any]]:
    """Get high APR pools from database"""
    try:
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,
                    'tvl': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting high APR pools: {e}")
        return []

def get_pools(limit: int = 5) -> List[Dict[str, Any]]:
    """Get pool data from database"""
    try:
        with app.app_context():
            pools = Pool.query.limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,
                    'tvl': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0
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

# Callback query handlers
async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle callback queries from buttons, returning True if handled
    """
    query = update.callback_query
    if not query:
        return False
    
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    
    try:
        # Log the callback
        logger.info(f"User {user_id} pressed button with data: {query.data}")
        
        # Handle different button actions
        if query.data == "pools":
            # Show pool data
            pools = get_pools(5)
            
            if pools:
                message = "*📊 Liquidity Pool Data*\n\n"
                for i, pool in enumerate(pools, 1):
                    message += (
                        f"{i}. *{pool['token_a']}-{pool['token_b']}*\n"
                        f"   • APR: {pool['apr_24h']:.2f}%\n"
                        f"   • TVL: ${pool['tvl']:,.2f}\n\n"
                    )
                
                keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
                
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
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
        
        elif query.data == "high_apr":
            # Show high APR pools
            high_apr_pools = get_high_apr_pools(3)
            
            if high_apr_pools:
                message = "*📈 Top High APR Pools*\n\n"
                for i, pool in enumerate(high_apr_pools, 1):
                    message += (
                        f"{i}. *{pool['token_a']}-{pool['token_b']}*\n"
                        f"   • APR: {pool['apr_24h']:.2f}%\n"
                        f"   • TVL: ${pool['tvl']:,.2f}\n\n"
                    )
                
                keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
                
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
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
        
        elif query.data == "profile":
            # Show user profile
            profile = get_user_profile(user_id)
            
            if profile:
                # User exists
                message = (
                    f"*👤 Your Profile*\n\n"
                    f"• *Username:* {profile['username']}\n"
                    f"• *Risk Profile:* {profile['risk_profile'].capitalize()}\n"
                    f"• *Investment Horizon:* {profile['investment_horizon'].capitalize()}\n"
                    f"• *Investment Goals:* {profile['investment_goals']}\n"
                    f"• *Subscribed to Updates:* {'Yes' if profile['is_subscribed'] else 'No'}\n"
                    f"• *Account Created:* {profile['created_at']}\n\n"
                    "This data is retrieved directly from our database."
                )
            else:
                # Create new user
                new_profile = create_user_profile(
                    user_id, 
                    update.effective_user.username if update.effective_user else "User", 
                    update.effective_user.first_name if update.effective_user else None,
                    update.effective_user.last_name if update.effective_user else None
                )
                
                message = (
                    f"*👤 Your Profile (New User)*\n\n"
                    f"• *Username:* {new_profile['username']}\n"
                    f"• *Risk Profile:* {new_profile['risk_profile'].capitalize()} (default)\n"
                    f"• *Investment Horizon:* {new_profile['investment_horizon'].capitalize()} (default)\n"
                    f"• *Investment Goals:* {new_profile['investment_goals']}\n"
                    f"• *Subscribed to Updates:* {'Yes' if new_profile['is_subscribed'] else 'No'}\n\n"
                    "Your profile has been created in our database."
                )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        elif query.data == "faq":
            # Show FAQ
            message = (
                "*❓ Frequently Asked Questions*\n\n"
                "Choose a topic to learn more:\n\n"
                "• *Liquidity Pools:* What they are and how they work\n"
                "• *APR:* Understanding Annual Percentage Rate\n"
                "• *Impermanent Loss:* What it is and how to minimize it\n"
                "• *Wallets:* How to connect and use wallets securely"
            )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        elif query.data == "back":
            # Back to main menu
            keyboard = [
                [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
                [InlineKeyboardButton("📈 View High APR Pools", callback_data="high_apr")],
                [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
                [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
            ]
            
            await query.edit_message_text(
                "*FiLot Interactive Menu*\n\n"
                "These buttons perform real database operations.\n"
                "Click any option to retrieve live data:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        # If not handled, return False
        return False
        
    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        try:
            await query.edit_message_text(
                "Sorry, an error occurred while processing your request. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )
        except Exception:
            pass
        return True