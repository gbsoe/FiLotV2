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
import threading
import time
import requests
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

# Global variable to track if the bot is running
bot_running = False
application = None

def keep_alive():
    """
    Function to periodically ping the application to keep it alive.
    This helps prevent the application from being terminated due to inactivity.
    """
    logger.info("Starting keep-alive thread")
    
    # Get the host from environment, default to localhost
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    
    ping_url = f"http://{host}:{port}/health"
    
    while True:
        try:
            # Make a request to the health endpoint
            response = requests.get(ping_url, timeout=5)
            logger.info(f"Keep-alive ping: {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        
        # Sleep for 30 seconds
        time.sleep(30)

def run_telegram_bot():
    """
    Run the Telegram bot in a separate thread
    """
    global bot_running, application
    
    # Import the create_application function from bot.py
    from bot import create_application
    
    # Create the Application using the function from bot.py
    try:
        # Set the global flag
        bot_running = True
        
        # Create the application
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
        bot_running = False

def main() -> None:
    """
    Main function to start the Flask app and Telegram bot.
    """
    try:
        # Create health check endpoint
        @app.route('/health')
        def health_check():
            status = {
                'app': 'running',
                'bot': 'running' if bot_running else 'stopped',
                'timestamp': time.time()
            }
            return status
        
        # Start the keep-alive thread
        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        
        # Start the Telegram bot in a separate thread
        bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        bot_thread.start()
        
        # Run the Flask app
        logger.info("Starting Flask web application")
        app.run(host='0.0.0.0', port=5000, use_reloader=False)
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()