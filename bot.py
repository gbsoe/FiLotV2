#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core bot functionality for the Telegram cryptocurrency pool bot
"""

import os
import logging
import asyncio
import json
import re
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

# Local imports
import raydium_client
import utils
from response_data import get_response_for_question, format_start_response, format_about_response, format_no_match_response
# These will be imported when fully implemented:
# import db_utils
# import safeguards
# import monitoring
# from ai_service import DeepSeekAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global variables
START_TIME = datetime.now()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAX_POOLS_TO_SHOW = 5  # Maximum number of pools to show in /info command

# Initialize DeepSeek AI client (commented out until implemented)
# deepseek_ai = None
# if DEEPSEEK_API_KEY:
#     deepseek_ai = DeepSeekAI(DEEPSEEK_API_KEY)
#     logger.info("DeepSeek AI client initialized")
# else:
#     logger.warning("DeepSeek API key not found in environment, AI features will be limited")

# Command handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user = update.effective_user
    is_new_user = True  # This would be determined by database check
    
    # Track user activity (would be implemented with db_utils)
    # db_utils.get_or_create_user(user.id, user.username, user.first_name, user.last_name)
    # db_utils.log_user_activity(user.id, "command", "/start")
    
    # Get start message from response data
    message = format_start_response(is_new_user)
    
    await update.message.reply_markdown(
        message,
        disable_web_page_preview=True,
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    from response_data import PREDEFINED_RESPONSES
    
    # Track user activity (would be implemented with db_utils)
    # db_utils.log_user_activity(update.effective_user.id, "command", "/help")
    
    await update.message.reply_markdown(
        PREDEFINED_RESPONSES["help"],
        disable_web_page_preview=True,
    )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show information about cryptocurrency pools when the command /info is issued."""
    # Track user activity (would be implemented with db_utils)
    # db_utils.log_user_activity(update.effective_user.id, "command", "/info")
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Fetch pool data
        pools_data = await raydium_client.get_pools(limit=30)
        
        # Sort by APR (descending)
        pools_data.sort(key=lambda p: p["apr_24h"], reverse=True)
        
        # Take top N pools
        top_pools = pools_data[:MAX_POOLS_TO_SHOW]
        
        # Convert to Pool objects for formatting
        from models import Pool
        pool_objects = []
        
        for pool_data in top_pools:
            pool = Pool(
                pool_id=pool_data["id"],
                token_a_symbol=pool_data["token_a"]["symbol"],
                token_b_symbol=pool_data["token_b"]["symbol"],
                token_a_price=pool_data["token_a"]["price"],
                token_b_price=pool_data["token_b"]["price"],
                apr_24h=pool_data["apr_24h"],
                apr_7d=pool_data["apr_7d"],
                apr_30d=pool_data["apr_30d"],
                tvl=pool_data["tvl"],
                fee=pool_data["fee"],
                volume_24h=pool_data.get("volume_24h", 0),
                tx_count_24h=pool_data.get("tx_count_24h", 0)
            )
            pool_objects.append(pool)
        
        # Format the pool information
        formatted_info = utils.format_pool_info(pool_objects)
        
        # Send the formatted message
        await update.message.reply_markdown(
            formatted_info,
            disable_web_page_preview=True,
        )
        
    except Exception as e:
        logger.error(f"Error in info_command: {e}")
        await update.message.reply_text(
            "Sorry, I couldn't fetch pool information at the moment. Please try again later."
        )

async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulate investment returns when the command /simulate is issued."""
    # Track user activity (would be implemented with db_utils)
    # db_utils.log_user_activity(update.effective_user.id, "command", "/simulate")
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Check if amount is provided
        if not context.args or not context.args[0].replace(".", "", 1).isdigit():
            await update.message.reply_text(
                "Please provide an investment amount. Example: /simulate 1000"
            )
            return
        
        # Parse the amount
        amount = float(context.args[0])
        
        # Validate the amount
        if amount <= 0:
            await update.message.reply_text(
                "Please provide a positive investment amount. Example: /simulate 1000"
            )
            return
        
        # Fetch pool data
        pools_data = await raydium_client.get_pools(limit=30)
        
        # Sort by APR (descending)
        pools_data.sort(key=lambda p: p["apr_24h"], reverse=True)
        
        # Take top N pools
        top_pools = pools_data[:MAX_POOLS_TO_SHOW]
        
        # Convert to Pool objects for formatting
        from models import Pool
        pool_objects = []
        
        for pool_data in top_pools:
            pool = Pool(
                pool_id=pool_data["id"],
                token_a_symbol=pool_data["token_a"]["symbol"],
                token_b_symbol=pool_data["token_b"]["symbol"],
                token_a_price=pool_data["token_a"]["price"],
                token_b_price=pool_data["token_b"]["price"],
                apr_24h=pool_data["apr_24h"],
                apr_7d=pool_data["apr_7d"],
                apr_30d=pool_data["apr_30d"],
                tvl=pool_data["tvl"],
                fee=pool_data["fee"],
                volume_24h=pool_data.get("volume_24h", 0),
                tx_count_24h=pool_data.get("tx_count_24h", 0)
            )
            pool_objects.append(pool)
        
        # Format the simulation results
        formatted_simulation = utils.format_simulation_results(pool_objects, amount)
        
        # Send the formatted message
        await update.message.reply_markdown(
            formatted_simulation,
            disable_web_page_preview=True,
        )
        
    except Exception as e:
        logger.error(f"Error in simulate_command: {e}")
        await update.message.reply_text(
            "Sorry, I couldn't simulate investment returns at the moment. Please try again later."
        )

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to daily updates when the command /subscribe is issued."""
    # This would be implemented with db_utils
    # subscribed = db_utils.subscribe_user(update.effective_user.id)
    
    # For now, just send a placeholder message
    await update.message.reply_text(
        "You have been subscribed to daily updates about the best performing pools. "
        "You will receive a notification every day at 12:00 UTC. "
        "Use /unsubscribe to stop receiving updates."
    )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from daily updates when the command /unsubscribe is issued."""
    # This would be implemented with db_utils
    # unsubscribed = db_utils.unsubscribe_user(update.effective_user.id)
    
    # For now, just send a placeholder message
    await update.message.reply_text(
        "You have been unsubscribed from daily updates. "
        "You will no longer receive notifications. "
        "Use /subscribe to start receiving updates again."
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check bot status when the command /status is issued."""
    # Calculate uptime
    uptime = datetime.now() - START_TIME
    
    # Format uptime
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    
    # This would be fetched from BotStatistics in the database
    # stats = db_utils.update_bot_statistics()
    
    # For now, just send a placeholder message
    await update.message.reply_markdown(
        f"*Bot Status*\n\n"
        f"• *Uptime:* {uptime_str}\n"
        f"• *Database:* Connected\n"
        f"• *API Services:* Online\n"
        f"• *Last Health Check:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
        f"All systems are operational."
    )

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify the user when the command /verify is issued."""
    # This would be implemented with db_utils and safeguards
    # code = db_utils.generate_verification_code(update.effective_user.id)
    
    # For now, just send a placeholder message
    await update.message.reply_text(
        "Verification is not required at this time. Your account is already active."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages that are not commands."""
    # Check if this is a private message (not in a group)
    if update.effective_chat.type != "private":
        return
    
    # Get the user's message
    message_text = update.message.text
    
    # Track the user query (would be implemented with db_utils)
    # db_utils.log_user_query(update.effective_user.id, "message", message_text)
    
    # Send typing action
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Check if there's a predefined response
        response = get_response_for_question(message_text)
        
        if response:
            await update.message.reply_markdown(
                response,
                disable_web_page_preview=True,
            )
            return
        
        # If no predefined response, use DeepSeek AI (when implemented)
        # if deepseek_ai:
        #     ai_response = await deepseek_ai.generate_response(message_text)
        #     await update.message.reply_markdown(
        #         ai_response,
        #         disable_web_page_preview=True,
        #     )
        #     return
        
        # If AI is not available, fallback to a generic response
        await update.message.reply_markdown(
            format_no_match_response(),
            disable_web_page_preview=True,
        )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            "Sorry, I couldn't process your message. Please try again later."
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in updates."""
    # Log the error
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Get user id if available
    user_id = None
    if update and hasattr(update, "effective_user") and update.effective_user:
        user_id = update.effective_user.id
    
    # Log the error to the database (would be implemented with db_utils)
    # db_utils.log_error("telegram_update", str(context.error), traceback.format_exc(), "bot.py", user_id)
    
    # Send message to the user if update is available
    if update and hasattr(update, "effective_message") and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong. Please try again later."
        )

async def send_daily_updates() -> None:
    """Send daily updates to subscribed users."""
    # This would be implemented with db_utils
    # subscribed_users = db_utils.get_subscribed_users()
    
    # Fetch pool data
    pools_data = await raydium_client.get_pools(limit=30)
    
    # Sort by APR (descending)
    pools_data.sort(key=lambda p: p["apr_24h"], reverse=True)
    
    # Take top N pools
    top_pools = pools_data[:MAX_POOLS_TO_SHOW]
    
    # Convert to Pool objects for formatting
    from models import Pool
    pool_objects = []
    
    for pool_data in top_pools:
        pool = Pool(
            pool_id=pool_data["id"],
            token_a_symbol=pool_data["token_a"]["symbol"],
            token_b_symbol=pool_data["token_b"]["symbol"],
            token_a_price=pool_data["token_a"]["price"],
            token_b_price=pool_data["token_b"]["price"],
            apr_24h=pool_data["apr_24h"],
            apr_7d=pool_data["apr_7d"],
            apr_30d=pool_data["apr_30d"],
            tvl=pool_data["tvl"],
            fee=pool_data["fee"],
            volume_24h=pool_data.get("volume_24h", 0),
            tx_count_24h=pool_data.get("tx_count_24h", 0)
        )
        pool_objects.append(pool)
    
    # Format the pool information
    formatted_info = utils.format_pool_info(pool_objects)
    
    # Add a header
    today = datetime.now().strftime("%Y-%m-%d")
    message = f"*Daily Pool Update - {today}*\n\n" + formatted_info
    
    # This would send messages to all subscribed users
    # for user in subscribed_users:
    #     try:
    #         await application.bot.send_message(
    #             chat_id=user.telegram_id,
    #             text=message,
    #             parse_mode="Markdown",
    #             disable_web_page_preview=True,
    #         )
    #     except Exception as e:
    #         logger.error(f"Error sending daily update to user {user.telegram_id}: {e}")

def create_application() -> Application:
    """Create the Application and add command handlers."""
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("simulate", simulate_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("verify", verify_command))
    
    # Add message handler (for non-command messages)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application