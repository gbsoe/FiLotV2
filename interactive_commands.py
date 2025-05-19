#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interactive commands that perform real database operations for FiLot Telegram bot
"""

import os
import logging
import datetime
from typing import List, Dict, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from sqlalchemy import text

from app import app
from models import db, User, Pool, UserQuery, UserActivityLog, BotStatistics

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def interactive_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display an interactive menu with buttons that perform real database operations."""
    try:
        if update.effective_user:
            user_id = update.effective_user.id
            username = update.effective_user.username or "Unknown"
            
            # Log this action to the database
            with app.app_context():
                try:
                    # Log user activity 
                    activity = UserActivityLog(
                        user_id=user_id,
                        activity_type="interactive_menu",
                        details="Command issued",
                        timestamp=datetime.datetime.utcnow()
                    )
                    db.session.add(activity)
                    db.session.commit()
                    logger.info(f"Logged interactive menu activity for user {user_id}")
                except Exception as e:
                    logger.error(f"Error logging activity: {e}")
                    db.session.rollback()
        
            # Create interactive buttons that will perform real database operations
            keyboard = [
                [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
                [InlineKeyboardButton("👤 My Profile Details", callback_data="profile")],
                [InlineKeyboardButton("📈 Top 3 Highest APR Pools", callback_data="high_apr")],
                [InlineKeyboardButton("📊 Bot Statistics", callback_data="stats")],
                [InlineKeyboardButton("🔍 Search For Pool", callback_data="search")]
            ]
            
            await update.message.reply_markdown(
                f"*Welcome to the Interactive FiLot Menu, {username}!*\n\n"
                "These buttons perform real database operations. Click any button below to retrieve live data:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            logger.info(f"Sent interactive menu to user {user_id}")
            
    except Exception as e:
        logger.error(f"Error in interactive menu command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from interactive buttons."""
    query = update.callback_query
    await query.answer()
    
    if not query.data:
        return
    
    user_id = update.effective_user.id if update.effective_user else None
    
    # Log this callback to the database
    with app.app_context():
        try:
            # Log user activity
            activity = UserActivityLog(
                user_id=user_id,
                activity_type="button_press",
                details=f"Button: {query.data}",
                timestamp=datetime.datetime.utcnow()
            )
            db.session.add(activity)
            db.session.commit()
            logger.info(f"Logged button press for user {user_id}: {query.data}")
        except Exception as e:
            logger.error(f"Error logging button press: {e}")
            db.session.rollback()
    
    try:
        # Handle different button actions with real database operations
        if query.data == "pools":
            await show_pool_data(update, context)
        elif query.data == "profile":
            await show_user_profile(update, context)
        elif query.data == "high_apr":
            await show_high_apr_pools(update, context)
        elif query.data == "stats":
            await show_bot_statistics(update, context) 
        elif query.data == "search":
            await prompt_pool_search(update, context)
        elif query.data == "back":
            await back_to_menu(update, context)
        elif query.data.startswith("pool:"):
            pool_id = query.data.split(":")[1]
            await show_pool_details(update, context, pool_id)
        else:
            await query.edit_message_text("Unknown button action")
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        await query.edit_message_text(
            "Sorry, an error occurred processing your request. Please try again later."
        )


async def show_pool_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show liquidity pool data from the database."""
    query = update.callback_query
    
    with app.app_context():
        try:
            # Get actual pool data from database
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(5).all()
            
            if pools:
                # Format message with real pool data
                message = "*📊 Liquidity Pool Data (Live Database)*\n\n"
                
                # Create inline keyboard for pool details
                keyboard = []
                
                for pool in pools:
                    pair = f"{pool.token_a_symbol}-{pool.token_b_symbol}"
                    apr = f"{pool.apr_24h:.2f}%"
                    message += f"• *{pair}*: APR {apr}, TVL ${pool.tvl:,.2f}\n"
                    
                    # Add button to view details of this specific pool
                    keyboard.append([
                        InlineKeyboardButton(f"View {pair} Details", callback_data=f"pool:{pool.id}")
                    ])
                
                # Add back button
                keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")])
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                await query.edit_message_text(
                    "*No Pool Data Found*\n\nThe database currently has no pool data.",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
        except Exception as e:
            logger.error(f"Error fetching pool data: {e}")
            await query.edit_message_text(
                "*Database Error*\n\nCould not retrieve pool data from the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )


async def show_pool_details(update: Update, context: ContextTypes.DEFAULT_TYPE, pool_id: str) -> None:
    """Show detailed information for a specific pool."""
    query = update.callback_query
    
    with app.app_context():
        try:
            # Get pool details from database
            pool = Pool.query.filter_by(id=pool_id).first()
            
            if pool:
                # Format message with pool details
                message = (
                    f"*Pool Details: {pool.token_a_symbol}-{pool.token_b_symbol}*\n\n"
                    f"• *APR (24h):* {pool.apr_24h:.2f}%\n"
                    f"• *APR (7d):* {pool.apr_7d:.2f}%\n"
                    f"• *TVL:* ${pool.tvl:,.2f}\n"
                    f"• *Fee:* {pool.fee:.2f}%\n"
                    f"• *Volume (24h):* ${pool.volume_24h:,.2f}\n"
                    f"• *Transactions (24h):* {pool.tx_count_24h if pool.tx_count_24h else 'N/A'}\n"
                    f"• *Last Updated:* {pool.last_updated.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "This data is retrieved directly from our database."
                )
            else:
                message = f"*Pool Not Found*\n\nPool with ID {pool_id} was not found in the database."
                
            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error fetching pool details: {e}")
            await query.edit_message_text(
                "*Database Error*\n\nCould not retrieve pool details from the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Pools", callback_data="pools")
                ]])
            )


async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile information from the database."""
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else None
    
    if not user_id:
        await query.edit_message_text(
            "*Error*\n\nCould not identify user.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
            ]])
        )
        return
    
    with app.app_context():
        try:
            # Get user from database
            user = User.query.filter_by(id=user_id).first()
            
            if user:
                # Get user activity count
                activity_count = UserActivityLog.query.filter_by(user_id=user_id).count()
                
                # Format message with user profile
                message = (
                    f"*👤 Your Profile (User ID: {user.id})*\n\n"
                    f"• *Username:* {user.username or 'Not set'}\n"
                    f"• *Risk Profile:* {user.risk_profile.capitalize()}\n"
                    f"• *Investment Horizon:* {user.investment_horizon.capitalize()}\n"
                    f"• *Investment Goals:* {user.investment_goals or 'Not specified'}\n"
                    f"• *Subscribed to Updates:* {'Yes' if user.is_subscribed else 'No'}\n"
                    f"• *Account Created:* {user.created_at.strftime('%Y-%m-%d')}\n"
                    f"• *Total Bot Interactions:* {activity_count}\n\n"
                    "This data is retrieved directly from our database."
                )
            else:
                # Create user in database if not exists
                new_user = User(
                    id=user_id,
                    username=update.effective_user.username,
                    first_name=update.effective_user.first_name,
                    last_name=update.effective_user.last_name,
                    risk_profile="moderate",
                    investment_horizon="medium",
                    created_at=datetime.datetime.utcnow()
                )
                db.session.add(new_user)
                db.session.commit()
                
                message = (
                    f"*👤 Your Profile (New User)*\n\n"
                    f"• *Username:* {update.effective_user.username or 'Not set'}\n"
                    f"• *Risk Profile:* Moderate (default)\n"
                    f"• *Investment Horizon:* Medium (default)\n"
                    f"• *Investment Goals:* Not specified\n"
                    f"• *Subscribed to Updates:* No\n"
                    f"• *Account Created:* Just now\n\n"
                    "Your profile has been created in our database."
                )
                
            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error fetching user profile: {e}")
            await query.edit_message_text(
                "*Database Error*\n\nCould not retrieve your profile from the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )


async def show_high_apr_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pools with highest APR from the database."""
    query = update.callback_query
    
    with app.app_context():
        try:
            # Query for top 3 pools by APR
            high_apr_pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(3).all()
            
            if high_apr_pools:
                # Format message with high APR pools
                message = "*📈 Top High APR Pools*\n\n"
                
                for i, pool in enumerate(high_apr_pools):
                    message += (
                        f"{i+1}. *{pool.token_a_symbol}-{pool.token_b_symbol}*\n"
                        f"   • APR: {pool.apr_24h:.2f}%\n"
                        f"   • TVL: ${pool.tvl:,.2f}\n"
                        f"   • Volume (24h): ${pool.volume_24h:,.2f if pool.volume_24h else 0}\n\n"
                    )
                
                message += "These pools currently have the highest APRs in our database."
            else:
                message = "*No High APR Pools Found*\n\nThe database currently has no pool data."
                
            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error fetching high APR pools: {e}")
            await query.edit_message_text(
                "*Database Error*\n\nCould not retrieve high APR pools from the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )


async def show_bot_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics from the database."""
    query = update.callback_query
    
    with app.app_context():
        try:
            # Get database statistics
            user_count = User.query.count()
            activity_count = UserActivityLog.query.count()
            query_count = UserQuery.query.count()
            pool_count = Pool.query.count()
            
            # Get bot uptime
            stats = BotStatistics.query.first()
            
            # Format message with statistics
            message = (
                "*📊 FiLot Bot Statistics*\n\n"
                f"• *Registered Users:* {user_count}\n"
                f"• *Total User Actions:* {activity_count}\n"
                f"• *User Queries Processed:* {query_count}\n"
                f"• *Pools in Database:* {pool_count}\n"
            )
            
            if stats:
                message += (
                    f"• *Average Response Time:* {stats.average_response_time:.2f}ms\n"
                    f"• *Bot Start Time:* {stats.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
            
            message += "\nThis data is retrieved directly from our database."
                
            # Create back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error fetching bot statistics: {e}")
            await query.edit_message_text(
                "*Database Error*\n\nCould not retrieve bot statistics from the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )


async def prompt_pool_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user to search for a pool."""
    query = update.callback_query
    
    # Store in context that we're waiting for a pool search query
    context.user_data["waiting_for_pool_search"] = True
    
    await query.edit_message_text(
        "*🔍 Search for Pool*\n\n"
        "Please type the name of the pool you want to search for (e.g., SOL-USDC).\n\n"
        "I'll search the database for matching pools.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Cancel Search", callback_data="back")
        ]])
    )


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to the main interactive menu."""
    query = update.callback_query
    
    # Clear any waiting states
    if "waiting_for_pool_search" in context.user_data:
        del context.user_data["waiting_for_pool_search"]
    
    # Create keyboard for main menu
    keyboard = [
        [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
        [InlineKeyboardButton("👤 My Profile Details", callback_data="profile")],
        [InlineKeyboardButton("📈 Top 3 Highest APR Pools", callback_data="high_apr")],
        [InlineKeyboardButton("📊 Bot Statistics", callback_data="stats")],
        [InlineKeyboardButton("🔍 Search For Pool", callback_data="search")]
    ]
    
    await query.edit_message_text(
        "*Interactive FiLot Menu*\n\n"
        "These buttons perform real database operations. Click any button below to retrieve live data:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def handle_search_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user's response to pool search prompt."""
    # Check if we're waiting for a pool search query
    if not context.user_data.get("waiting_for_pool_search"):
        return False
    
    # Clear the waiting flag
    del context.user_data["waiting_for_pool_search"]
    
    search_query = update.message.text.strip().upper()
    
    with app.app_context():
        try:
            # Search for pools matching the query
            pools = []
            
            # Search by token pair
            tokens = search_query.split('-') if '-' in search_query else [search_query]
            
            if len(tokens) == 2:
                token_a, token_b = tokens
                pools = Pool.query.filter(
                    ((Pool.token_a_symbol == token_a) & (Pool.token_b_symbol == token_b)) |
                    ((Pool.token_a_symbol == token_b) & (Pool.token_b_symbol == token_a))
                ).all()
            else:
                token = tokens[0]
                pools = Pool.query.filter(
                    (Pool.token_a_symbol == token) | (Pool.token_b_symbol == token)
                ).all()
            
            if pools:
                message = f"*🔍 Search Results for '{search_query}'*\n\n"
                
                for i, pool in enumerate(pools):
                    message += (
                        f"{i+1}. *{pool.token_a_symbol}-{pool.token_b_symbol}*\n"
                        f"   • APR: {pool.apr_24h:.2f}%\n"
                        f"   • TVL: ${pool.tvl:,.2f}\n\n"
                    )
            else:
                message = f"*No Results Found*\n\nNo pools matching '{search_query}' were found in the database."
            
            # Create new interactive menu
            keyboard = [
                [InlineKeyboardButton("🔍 New Search", callback_data="search")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
            ]
            
            await update.message.reply_markdown(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return True
        except Exception as e:
            logger.error(f"Error searching pools: {e}")
            
            await update.message.reply_markdown(
                "*Database Error*\n\nCould not search for pools in the database.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )
            
            return True