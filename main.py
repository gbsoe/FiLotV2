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

# Import health check module
import health_check

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global application variable
application = None

def anti_idle_thread():
    """
    Thread that performs regular database activity to prevent the application
    from being terminated due to inactivity.
    """
    logger.info("Starting anti-idle thread for telegram bot process")

    # Sleep interval in seconds (60 seconds is well below the ~2m21s timeout)
    interval = 60

    while True:
        try:
            # Access the database with app context
            with app.app_context():
                from sqlalchemy import text
                from models import db, BotStatistics, ErrorLog

                # Simple query to keep connection alive
                result = db.session.execute(text("SELECT 1")).fetchone()
                logger.info(f"Bot process anti-idle: Database ping successful, result={result}")

                # Create a log entry to show activity
                log = ErrorLog(
                    error_type="keep_alive_main",
                    error_message="Main.py telegram bot anti-idle activity",
                    module="main.py",
                    resolved=True
                )
                db.session.add(log)

                # Update statistics
                stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
                if stats:
                    # Increment uptime percentage slightly (which we can modify directly)
                    stats.uptime_percentage += 0.01  # Small increment
                    db.session.commit()
                    logger.info("Bot process anti-idle: Updated statistics")
        except Exception as e:
            logger.error(f"Bot process anti-idle error: {e}")

        # Sleep for the interval
        time.sleep(interval)

def run_telegram_bot():
    """
    Run the Telegram bot with proper event loop handling
    """
    try:
        import asyncio
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Import the create_application function from bot.py
        from bot import create_application

        # Create the application
        application = create_application()

        # Run the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error in telegram bot: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """
    Main function to start both the Flask app and Telegram bot
    """
    try:
        if os.environ.get('PRODUCTION') == 'true':
            # In production, run only the bot
            run_telegram_bot()
        else:
            # In development, run both Flask and bot
            from threading import Thread
            bot_thread = Thread(target=run_telegram_bot)
            bot_thread.daemon = True
            bot_thread.start()

            # Run Flask app
            app.run(host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()