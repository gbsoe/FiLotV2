#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram bot and Flask web application
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# Import bot command handlers
from bot import (
    start_command,
    help_command,
    info_command,
    simulate_command,
    subscribe_command,
    unsubscribe_command,
    status_command,
    verify_command,
    wallet_command,
    walletconnect_command,
    handle_message,
    handle_callback_query,
    error_handler
)

# Import Flask app for the web interface
from app import app

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main() -> None:
    """
    Main function to start the Telegram bot.
    """
    # Check for Telegram bot token
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Telegram bot token not found. Please set the TELEGRAM_BOT_TOKEN environment variable.")
        sys.exit(1)
    
    # Create the Application
    application = Application.builder().token(token).build()
    
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
    application.add_handler(CommandHandler("walletconnect", walletconnect_command))
    
    # Register callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Register message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()