#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Core bot functionality and command handlers for the Telegram cryptocurrency pool bot
"""

import os
import logging
import time
import datetime
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, 
    CallbackQueryHandler, ContextTypes
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton

from config import load_config
from raydium_client import RaydiumClient
from ai_service import DeepSeekAI
from response_data import get_predefined_response
from utils import (
    get_cache, set_cache, format_pool_data, format_simulation_results,
    calculate_impermanent_loss, calculate_returns
)

# Configure logging
logger = logging.getLogger(__name__)

# Global variables
start_time = time.time()
command_count = 0
active_users = set()
subscribed_users = set()

# Initialize clients
config = load_config()
raydium_client = RaydiumClient(config.get("pools", []))
ai_service = DeepSeekAI(os.getenv("DEEPSEEK_API_KEY", ""))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    global command_count, active_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    user = update.effective_user
    await update.message.reply_html(
        f"👋 Hi {user.mention_html()}!\n\n"
        f"Welcome to the Cryptocurrency Pool Tracking Bot. This bot helps you track "
        f"crypto pools on Raydium and simulate investment returns.\n\n"
        f"Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    global command_count, active_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    help_text = (
        "🔍 *Available Commands:*\n\n"
        "• /start - Start the bot\n"
        "• /help - Show this help message\n"
        "• /info - Get information about crypto pools\n"
        "• /simulate <amount> - Simulate investment returns\n"
        "• /status - Check bot status\n"
        "• /subscribe - Subscribe to daily pool updates\n"
        "• /unsubscribe - Unsubscribe from updates\n"
        "• /ask <question> - Ask an AI-powered question about crypto\n\n"
        "You can also just send a message, and I'll try to understand and respond!"
    )
    
    await update.message.reply_markdown(help_text)

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show information about crypto pools."""
    global command_count, active_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    # Check if we have cached data
    cached_data = get_cache("pool_data")
    if cached_data:
        await update.message.reply_markdown(cached_data)
        return
    
    await update.message.reply_text("Fetching pool data... Please wait.")
    
    try:
        # Fetch pool data from Raydium
        pool_data = await raydium_client.fetch_pool_data()
        
        # Format the pool data into a readable message
        formatted_data = format_pool_data(pool_data)
        
        # Cache the formatted data for future requests
        set_cache("pool_data", formatted_data, 300)  # Cache for 5 minutes
        
        # Create keyboard for simulation
        keyboard = [
            [InlineKeyboardButton("Simulate Investment", callback_data="simulate")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_markdown(formatted_data, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error fetching pool data: {e}")
        await update.message.reply_text(
            "⚠️ Failed to fetch pool data. Please try again later."
        )

async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulate investment returns based on pool data."""
    global command_count, active_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    args = context.args
    
    if not args:
        await update.message.reply_text(
            "Please provide an investment amount. Example: /simulate 1000"
        )
        return
    
    try:
        amount = float(args[0])
        
        if amount <= 0:
            await update.message.reply_text("Investment amount must be positive.")
            return
        
        # Get pool data (from cache if available)
        cached_data = get_cache("raw_pool_data")
        if not cached_data:
            await update.message.reply_text("Fetching pool data... Please wait.")
            cached_data = await raydium_client.fetch_pool_data()
            set_cache("raw_pool_data", cached_data, 300)  # Cache for 5 minutes
        
        # Calculate returns
        results = calculate_returns(cached_data, amount)
        
        # Calculate impermanent loss risk
        il_risk = calculate_impermanent_loss(cached_data)
        
        # Format the results into a readable message
        formatted_results = format_simulation_results(results, il_risk, amount)
        
        await update.message.reply_markdown(formatted_results)
    except ValueError:
        await update.message.reply_text("Invalid amount. Please provide a number.")
    except Exception as e:
        logger.error(f"Error simulating investment: {e}")
        await update.message.reply_text(
            "⚠️ Failed to simulate investment. Please try again later."
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot status information."""
    global command_count, active_users, start_time
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    uptime = time.time() - start_time
    uptime_str = str(datetime.timedelta(seconds=int(uptime)))
    
    # Check API status
    raydium_status = "✅ Online" if await raydium_client.check_status() else "❌ Offline"
    ai_status = "✅ Online" if ai_service.api_key and await ai_service.check_status() else "❌ Offline"
    
    status_text = (
        "🤖 *Bot Status*\n\n"
        f"• Uptime: {uptime_str}\n"
        f"• Active Users: {len(active_users)}\n"
        f"• Subscribed Users: {len(subscribed_users)}\n"
        f"• Commands Processed: {command_count}\n\n"
        f"*API Status*\n"
        f"• Raydium API: {raydium_status}\n"
        f"• DeepSeek AI API: {ai_status}\n"
    )
    
    await update.message.reply_markdown(status_text)

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe user to daily updates."""
    global command_count, active_users, subscribed_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    user_id = update.effective_user.id
    
    if user_id in subscribed_users:
        await update.message.reply_text("You are already subscribed to daily updates.")
        return
    
    subscribed_users.add(user_id)
    await update.message.reply_text(
        "✅ You have successfully subscribed to daily pool updates. "
        "You will receive daily notifications about the best performing pools."
    )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe user from daily updates."""
    global command_count, active_users, subscribed_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    user_id = update.effective_user.id
    
    if user_id not in subscribed_users:
        await update.message.reply_text("You are not currently subscribed to updates.")
        return
    
    subscribed_users.remove(user_id)
    await update.message.reply_text(
        "✅ You have successfully unsubscribed from daily pool updates."
    )

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle AI-powered question answering."""
    global command_count, active_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    if not ai_service.api_key:
        await update.message.reply_text(
            "⚠️ AI features are currently unavailable. Please try again later."
        )
        return
    
    query = " ".join(context.args)
    
    if not query:
        await update.message.reply_text(
            "Please provide a question. Example: /ask What is impermanent loss?"
        )
        return
    
    try:
        await update.message.reply_text("Thinking... 🤔")
        response = await ai_service.generate_response(query)
        await update.message.reply_markdown(response)
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        await update.message.reply_text(
            "⚠️ Failed to generate an AI response. Please try again later."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle regular messages and try to understand them."""
    global command_count, active_users
    
    command_count += 1
    active_users.add(update.effective_user.id)
    
    message_text = update.message.text.lower()
    
    # Check for predefined responses
    response = get_predefined_response(message_text)
    if response:
        await update.message.reply_text(response)
        return
    
    # If no predefined response and AI is available, use AI
    if ai_service.api_key:
        try:
            await update.message.reply_text("Thinking... 🤔")
            response = await ai_service.generate_response(message_text)
            await update.message.reply_markdown(response)
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            await update.message.reply_text(
                "I'm not sure how to respond to that. Try using a specific command like /help."
            )
    else:
        await update.message.reply_text(
            "I'm not sure how to respond to that. Try using a specific command like /help."
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "simulate":
        await query.message.reply_text(
            "Please use /simulate command followed by an investment amount. Example: /simulate 1000"
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")
    
    # Notify user about the error
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "An error occurred while processing your request. Please try again later."
        )

def setup_bot() -> Application:
    """Set up the bot with all handlers."""
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("simulate", simulate_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("ask", ask_command))
    
    # Add callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Add message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    return application

def run_bot(application: Application) -> None:
    """Run the bot."""
    # Start the Bot
    application.run_polling()

