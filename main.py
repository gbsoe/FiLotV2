#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram bot and Flask web application
"""

import os
import sys
import logging
import asyncio
import traceback
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
    profile_command,
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
    # Import the create_application function from bot.py
    from bot import create_application
    
    # Create the Application using the function from bot.py
    try:
        application = create_application()
        
        # Start the bot inside Flask application context
        logger.info("Starting bot using application from bot.py create_application()")
        
        # Log environment and settings
        for group, handlers in application.handlers.items():
            logger.info("Bot handlers group %s has %d handler(s)", group, len(handlers))
            for handler in handlers:
                logger.info("    - %s", handler)
        
        # Start the bot with Flask context
        with app.app_context():
            logger.info("Running bot polling within Flask app context")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error("Error creating or starting Telegram bot: %s", e)
        logger.error("Traceback: %s", traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()