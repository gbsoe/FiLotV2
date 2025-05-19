#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main application file for the Telegram cryptocurrency pool bot
"""

import os
import logging
import json
import time
import threading
import traceback
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from app import app, db
from models import User, Pool, UserQuery

# Configure logging for main app
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global configuration 
POOL_REFRESH_INTERVAL = 3600  # Refresh pool data every hour
MAX_RETRIES = 3  # Number of retries for API requests
RETRY_DELAY = 2  # Delay between retries in seconds

# Import telegram-related imports
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# Import handlers
from button_responses import handle_button_callback
from smart_invest import get_smart_invest_conversation_handler, smart_invest_command
from mood_tracking import get_mood_tracking_conversation_handler, mood_command

# Import command handlers
from bot import (
    start_command, help_command, info_command, simulate_command,
    subscribe_command, unsubscribe_command, status_command, verify_command,
    wallet_command, profile_command, faq_command, social_command,
    walletconnect_command, update_query_response, handle_message
)

# Main bot runner
def run_telegram_bot():
    """
    Run the Telegram bot using the python-telegram-bot library
    """
    try:
        # Get telegram token from environment
        telegram_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        
        if not telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            
        # Initialize the Bot and dispatcher
        application = Application.builder().token(telegram_token).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("info", info_command))
        application.add_handler(CommandHandler("simulate", simulate_command))
        application.add_handler(CommandHandler("subscribe", subscribe_command))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("verify", verify_command))
        application.add_handler(CommandHandler("wallet", wallet_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("faq", faq_command))
        application.add_handler(CommandHandler("social", social_command))
        application.add_handler(CommandHandler("walletconnect", walletconnect_command))
        application.add_handler(CommandHandler("mood", mood_command))
        
        # Register conversation handlers
        application.add_handler(get_smart_invest_conversation_handler())
        application.add_handler(get_mood_tracking_conversation_handler())
        
        # Register callback query handlers with specific patterns
        application.add_handler(CallbackQueryHandler(handle_button_callback, pattern="^(invest|explore_pools|account|help)$"))
        
        # Register a general callback query handler for other callbacks
        application.add_handler(CallbackQueryHandler(handle_button_callback))
        
        # Register message handler as fallback for everything else
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start the Bot
        logger.info("Starting Telegram bot")
        application.run_polling(poll_interval=1.0, timeout=30)
        
    except Exception as e:
        logger.error(f"Error in telegram bot: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """
    Main function to start both the Flask app and Telegram bot
    """
    try:
        # First, kill any existing bot process that might be running
        try:
            # Try to terminate any other instance gracefully
            import requests
            import os
            bot_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
            if bot_token:
                base_url = f"https://api.telegram.org/bot{bot_token}"
                requests.get(f"{base_url}/getUpdates", params={"offset": -1, "timeout": 0})
                requests.get(f"{base_url}/deleteWebhook", params={"drop_pending_updates": "true"})
                logger.info("Terminated any existing bot polling")
        except Exception as e:
            logger.warning(f"Failed to terminate existing bot: {e}")
        
        # Start in the appropriate mode
        if os.environ.get('PRODUCTION') == 'true':
            # In production, run only the bot
            run_telegram_bot()
        else:
            # In development, run both Flask and bot
            from threading import Thread
            
            # Add a short delay to ensure clean startup
            time.sleep(1)
            
            # Start Telegram bot in a separate thread
            bot_thread = Thread(target=run_telegram_bot, daemon=True)
            bot_thread.start()
            
            # Start Flask app in the main thread
            from app import app
            
            # Only bind to 0.0.0.0 when not in production
            app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()