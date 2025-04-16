#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core bot functionality for the Telegram cryptocurrency pool bot
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable

from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
)

import db_utils
import utils
import safeguards
import monitoring
from monitoring import performance_tracker
from safeguards import apply_all_safeguards
import raydium_client

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Command handlers

@apply_all_safeguards
@performance_tracker
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    username = user.username
    first_name = user.first_name
    last_name = user.last_name
    
    # Get or create user in database
    db_user = db_utils.get_or_create_user(user_id, username, first_name, last_name)
    
    # Log the command
    db_utils.log_user_query(user_id, "/start", "User started the bot")
    
    # Log user activity
    db_utils.log_user_activity(user_id, "bot_start", "User started the bot")
    
    welcome_message = (
        f"👋 Welcome to the Crypto Pool Tracker Bot!\n\n"
        f"I can help you track cryptocurrency pools on Raydium and simulate investment returns.\n\n"
        f"Here are the available commands:\n"
        f"/info - Get information about cryptocurrency pools\n"
        f"/simulate <amount> - Simulate investment returns\n"
        f"/subscribe - Subscribe to daily updates\n"
        f"/unsubscribe - Unsubscribe from daily updates\n"
        f"/status - Check bot status\n"
        f"/help - Show help message\n\n"
        f"You can also ask me questions about cryptocurrency pools and investments!"
    )
    
    # Create subscription button
    keyboard = [
        [InlineKeyboardButton("Subscribe to Updates", callback_data="subscribe")],
        [InlineKeyboardButton("View Top Pools", callback_data="info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

@apply_all_safeguards
@performance_tracker
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    user_id = update.effective_user.id
    
    # Log the command
    db_utils.log_user_query(user_id, "/help", "User requested help")
    
    help_message = (
        f"📚 Crypto Pool Tracker Bot Help\n\n"
        f"Available Commands:\n"
        f"/start - Start the bot\n"
        f"/info - Get information about cryptocurrency pools\n"
        f"/simulate <amount> - Simulate investment returns\n"
        f"/subscribe - Subscribe to daily updates\n"
        f"/unsubscribe - Unsubscribe from daily updates\n"
        f"/status - Check bot status\n"
        f"/help - Show this help message\n\n"
        f"Features:\n"
        f"- Track APR and TVL for cryptocurrency pools\n"
        f"- Simulate investment returns\n"
        f"- Get daily updates on the best pools\n"
        f"- Ask questions about crypto investments\n\n"
        f"If you have any questions or suggestions, feel free to contact us!"
    )
    
    await update.message.reply_text(help_message)

@apply_all_safeguards
@performance_tracker
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show information about cryptocurrency pools when the command /info is issued."""
    user_id = update.effective_user.id
    
    # Log the command
    db_utils.log_user_query(user_id, "/info", "User requested pool information")
    
    await update.message.reply_text("🔍 Fetching the latest cryptocurrency pool data...")
    
    # Get pools from database or fetch if needed
    pools = db_utils.get_high_apr_pools(limit=5)
    
    if not pools:
        # No pools in database, fetch from API
        await update.message.reply_text("📊 Fetching data from Raydium API...")
        
        try:
            pool_data = await raydium_client.get_pools()
            db_utils.save_pool_data(pool_data)
            pools = db_utils.get_high_apr_pools(limit=5)
        except Exception as e:
            logger.error(f"Error fetching pool data: {e}")
            await update.message.reply_text(
                "❌ Sorry, there was an error fetching pool data. Please try again later."
            )
            return
    
    # Format pool information
    info_message = utils.format_pool_info(pools)
    
    # Create button for simulation
    keyboard = [
        [InlineKeyboardButton("Simulate Investment", callback_data="simulate")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(info_message, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

@apply_all_safeguards
@performance_tracker
async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulate investment returns when the command /simulate is issued."""
    user_id = update.effective_user.id
    
    # Check if amount is provided
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "⚠️ Please provide an investment amount.\n"
            "Example: /simulate 1000"
        )
        return
    
    # Get investment amount
    amount = float(context.args[0])
    
    # Log the command
    db_utils.log_user_query(
        user_id, 
        "/simulate", 
        f"User simulated investment with amount: {amount}"
    )
    
    # Get top pools
    pools = db_utils.get_high_apr_pools(limit=3)
    
    if not pools:
        await update.message.reply_text(
            "❌ No pool data available for simulation. Please try again later."
        )
        return
    
    # Format simulation results
    simulation_message = utils.format_simulation_results(pools, amount)
    
    await update.message.reply_text(simulation_message, parse_mode=ParseMode.MARKDOWN)

@apply_all_safeguards
@performance_tracker
async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to daily updates when the command /subscribe is issued."""
    user_id = update.effective_user.id
    
    # Log the command
    db_utils.log_user_query(user_id, "/subscribe", "User subscribed to updates")
    
    # Subscribe user
    result = db_utils.subscribe_user(user_id)
    
    if result:
        await update.message.reply_text(
            "✅ You have successfully subscribed to daily updates!\n"
            "You will receive information about the best cryptocurrency pools every day."
        )
    else:
        await update.message.reply_text(
            "❌ There was an error subscribing you to updates. Please try again later."
        )

@apply_all_safeguards
@performance_tracker
async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from daily updates when the command /unsubscribe is issued."""
    user_id = update.effective_user.id
    
    # Log the command
    db_utils.log_user_query(user_id, "/unsubscribe", "User unsubscribed from updates")
    
    # Unsubscribe user
    result = db_utils.unsubscribe_user(user_id)
    
    if result:
        await update.message.reply_text(
            "✅ You have successfully unsubscribed from daily updates.\n"
            "You will no longer receive daily information about cryptocurrency pools."
        )
    else:
        await update.message.reply_text(
            "❌ There was an error unsubscribing you from updates. Please try again later."
        )

@apply_all_safeguards
@performance_tracker
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check bot status when the command /status is issued."""
    user_id = update.effective_user.id
    
    # Log the command
    db_utils.log_user_query(user_id, "/status", "User checked bot status")
    
    # Get system health
    health_data = monitoring.get_system_health()
    
    # Format status message
    status_message = (
        f"🤖 Bot Status: {health_data['status']}\n\n"
        f"⏱️ Uptime: {health_data['uptime_formatted']}\n"
        f"👥 Total Users: {health_data['total_users']}\n"
        f"👤 Active Users: {health_data['active_users']}\n"
        f"🔄 Commands Processed: {health_data['command_count']}\n"
        f"⚡ Average Response Time: {health_data['average_response_time']:.2f} ms\n"
        f"🔼 Uptime Percentage: {health_data['uptime_percentage']:.2f}%\n\n"
        f"Last Updated: {health_data['timestamp']}"
    )
    
    await update.message.reply_text(status_message)

@apply_all_safeguards
@performance_tracker
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify the user when the command /verify is issued."""
    user_id = update.effective_user.id
    
    # Check if code is provided
    if not context.args:
        # Generate verification code
        code = safeguards.user_verification.generate_verification_code(user_id)
        
        if code:
            await update.message.reply_text(
                f"🔐 Your verification code is: `{code}`\n\n"
                f"Please verify your account by sending:\n"
                f"/verify {code}\n\n"
                f"This code will expire in 1 hour.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "❌ There was an error generating your verification code. Please try again later."
            )
        
        return
    
    # Verify code
    code = context.args[0]
    result = safeguards.user_verification.verify_code(user_id, code)
    
    # Log the command
    db_utils.log_user_query(
        user_id, 
        "/verify", 
        f"User verification attempt: {'Successful' if result else 'Failed'}"
    )
    
    if result:
        await update.message.reply_text(
            "✅ Your account has been successfully verified!\n"
            "You now have access to all bot features."
        )
    else:
        await update.message.reply_text(
            "❌ Invalid verification code. Please try again or generate a new code."
        )

# Message and callback handlers

@apply_all_safeguards
@performance_tracker
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    # Log the interaction
    db_utils.log_user_query(user_id, f"button_{data}", f"User clicked {data} button")
    
    if data == "subscribe":
        # Subscribe user
        result = db_utils.subscribe_user(user_id)
        
        if result:
            await query.edit_message_text(
                "✅ You have successfully subscribed to daily updates!\n"
                "You will receive information about the best cryptocurrency pools every day."
            )
        else:
            await query.edit_message_text(
                "❌ There was an error subscribing you to updates. Please try again later."
            )
    
    elif data == "info":
        # Show pool information
        pools = db_utils.get_high_apr_pools(limit=5)
        
        if not pools:
            await query.edit_message_text(
                "❌ No pool data available. Please try again later."
            )
            return
        
        # Format pool information
        info_message = utils.format_pool_info(pools)
        
        # Create button for simulation
        keyboard = [
            [InlineKeyboardButton("Simulate Investment", callback_data="simulate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            info_message, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "simulate":
        # Ask for investment amount
        keyboard = [
            [
                InlineKeyboardButton("$100", callback_data="simulate_100"),
                InlineKeyboardButton("$500", callback_data="simulate_500"),
                InlineKeyboardButton("$1000", callback_data="simulate_1000"),
                InlineKeyboardButton("$5000", callback_data="simulate_5000")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "💰 Please select an investment amount or use the /simulate command with a custom amount:",
            reply_markup=reply_markup
        )
    
    elif data.startswith("simulate_"):
        # Get investment amount
        amount = float(data.split("_")[1])
        
        # Get top pools
        pools = db_utils.get_high_apr_pools(limit=3)
        
        if not pools:
            await query.edit_message_text(
                "❌ No pool data available for simulation. Please try again later."
            )
            return
        
        # Format simulation results
        simulation_message = utils.format_simulation_results(pools, amount)
        
        # Create back button
        keyboard = [
            [InlineKeyboardButton("Back to Pools", callback_data="info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            simulation_message, 
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

@apply_all_safeguards
@performance_tracker
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages that are not commands."""
    message_text = update.message.text
    user_id = update.effective_user.id
    
    # Log the message
    db_utils.log_user_query(user_id, "message", message_text)
    
    # For now, just reply with a simple message
    # This will be enhanced with AI capabilities in the future
    await update.message.reply_text(
        "I'm currently only able to respond to commands. Please use /help to see available commands."
    )

# Error handler

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in updates."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Log error to database
    error_message = str(context.error)
    traceback = ''.join(context.error.__traceback__.format())
    
    # Try to get user ID
    user_id = None
    if update and isinstance(update, Update) and update.effective_user:
        user_id = update.effective_user.id
    
    db_utils.log_error("Telegram Bot Error", error_message, traceback, "bot.error_handler", user_id)
    
    # Notify user if possible
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Sorry, an error occurred while processing your request. Please try again later."
        )

# Daily update task

async def send_daily_updates() -> None:
    """Send daily updates to subscribed users."""
    logger.info("Sending daily updates...")
    
    # Get subscribed users
    subscribed_users = db_utils.get_subscribed_users()
    
    if not subscribed_users:
        logger.info("No subscribed users found.")
        return
    
    # Get top pools
    pools = db_utils.get_high_apr_pools(limit=5)
    
    if not pools:
        logger.error("No pool data available for daily updates.")
        return
    
    # Format pool information
    update_message = (
        f"📊 *Daily Cryptocurrency Pool Update*\n\n"
        f"{utils.format_pool_info(pools)}\n\n"
        f"Use /simulate to see potential returns from these pools!"
    )
    
    # Send updates to each subscribed user
    for user in subscribed_users:
        try:
            # Create application instance for sending messages
            token = os.environ.get("TELEGRAM_BOT_TOKEN")
            application = Application.builder().token(token).build()
            
            # Send message
            await application.bot.send_message(
                chat_id=user.id,
                text=update_message,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Log daily update
            db_utils.log_user_activity(user.id, "daily_update_sent", "Daily pool update sent to user")
            
            # Wait a bit to avoid hitting rate limits
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error sending daily update to user {user.id}: {e}")
            db_utils.log_error(
                "Daily Update Error", 
                f"Failed to send daily update to user {user.id}: {e}",
                module="bot.send_daily_updates"
            )
    
    logger.info(f"Daily updates sent to {len(subscribed_users)} users.")

# Create the Application and add handlers
def create_application() -> Application:
    """Create the Application and add command handlers."""
    # Get token from environment
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Telegram bot token not found in environment variables.")
    
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("simulate", simulate_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("verify", verify_command))
    
    # Add button callback handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application