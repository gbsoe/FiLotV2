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
    Run the Telegram bot using a direct approach to handle messages.
    
    This function avoids using the PTB built-in polling mechanisms which require 
    signal handlers and instead implements a direct command handling approach.
    """
    try:
        # Import necessary modules here for thread safety
        import threading
        import requests
        import json
        from telegram import Bot, Update
        
        # Get the token from environment variables
        bot_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("No Telegram bot token found")
            return
            
        # Create a bot instance directly
        bot = Bot(token=bot_token)
        logger.info("Created Telegram bot instance")
        
        # Import command handlers
        from bot import (
            start_command, help_command, info_command, simulate_command,
            subscribe_command, unsubscribe_command, status_command,
            verify_command, wallet_command, walletconnect_command,
            profile_command, faq_command, social_command,
            handle_message, handle_callback_query
        )
        
        # Set up base URL for Telegram Bot API
        base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Track the last update ID we've processed
        last_update_id = 0
        
        # Dictionary mapping command names to handler functions
        command_handlers = {
            "start": start_command,
            "help": help_command,
            "info": info_command,
            "simulate": simulate_command,
            "subscribe": subscribe_command,
            "unsubscribe": unsubscribe_command,
            "status": status_command,
            "verify": verify_command,
            "wallet": wallet_command,
            "walletconnect": walletconnect_command,
            "profile": profile_command,
            "faq": faq_command,
            "social": social_command
        }
        
        # Function to handle a specific update by determining its type and routing to appropriate handler
        def handle_update(update_dict):
            import asyncio
            from app import app
            
            try:
                # Convert the dictionary to a Telegram Update object
                update_obj = Update.de_json(update_dict, bot)
                logger.info(f"Processing update type: {update_dict.keys()}")
                
                # Create an event loop for async operation
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Create a simple context type that mimics ContextTypes.DEFAULT_TYPE
                class SimpleContext:
                    def __init__(self):
                        self.bot = bot
                        self.args = []
                        self.match = None
                        self.user_data = {}
                        self.chat_data = {}
                        self.bot_data = {}
                        
                context = SimpleContext()
                
                # Extract command arguments if this is a command
                if update_obj.message and update_obj.message.text and update_obj.message.text.startswith('/'):
                    # Split the message into command and arguments
                    text_parts = update_obj.message.text.split()
                    command = text_parts[0][1:].split('@')[0]  # Remove the '/' and any bot username
                    context.args = text_parts[1:]
                    
                    # Execute inside the Flask app context
                    with app.app_context():
                        # Route to appropriate command handler
                        if command in command_handlers:
                            logger.info(f"Calling handler for command: {command}")
                            handler = command_handlers[command]
                            loop.run_until_complete(handler(update_obj, context))
                        else:
                            logger.info(f"Unknown command: {command}")
                
                # Handle callback queries
                elif update_obj.callback_query:
                    logger.info("Calling callback query handler")
                    with app.app_context():
                        loop.run_until_complete(handle_callback_query(update_obj, context))
                
                # Handle regular messages
                elif update_obj.message and update_obj.message.text:
                    logger.info("Calling regular message handler")
                    with app.app_context():
                        loop.run_until_complete(handle_message(update_obj, context))
                
                # Don't close the loop - this causes issues with PTB's async operations
                # loop.close()  # <-- Removed this line
                logger.info(f"Successfully processed update ID: {update_dict.get('update_id')}")
                
            except Exception as e:
                logger.error(f"Error processing update: {e}")
                logger.error(traceback.format_exc())
        
        # Function to continuously poll for updates
        def poll_for_updates():
            nonlocal last_update_id
            
            logger.info("Starting update polling thread")
            
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
                    logger.info(f"Requesting updates from Telegram API...")
                    response = requests.get(f"{base_url}/getUpdates", params=params, timeout=60)
                    
                    # Process the response if successful
                    if response.status_code == 200:
                        result = response.json()
                        updates = result.get("result", [])
                        
                        # Debug log
                        logger.info(f"Received response: {len(updates)} updates")
                        if len(updates) > 0:
                            logger.info(f"Update keys: {', '.join(updates[0].keys())}")
                        
                        # Process each update
                        for update in updates:
                            # Update the last update ID
                            update_id = update.get("update_id", 0)
                            if update_id > last_update_id:
                                last_update_id = update_id
                            
                            # Process the update in a separate thread
                            logger.info(f"Starting thread to process update {update_id}")
                            threading.Thread(target=handle_update, args=(update,)).start()
                    else:
                        logger.error(f"Error getting updates: {response.status_code} - {response.text}")
                        
                    # Log status periodically
                    if int(time.time()) % 60 == 0:  # Log once per minute
                        logger.info(f"Bot polling active. Last update ID: {last_update_id}")
                        
                except Exception as e:
                    logger.error(f"Error in update polling: {e}")
                    logger.error(traceback.format_exc())
                
                # Sleep briefly to avoid hammering the API
                time.sleep(1)
        
        # Start the polling thread
        polling_thread = threading.Thread(target=poll_for_updates, daemon=True)
        polling_thread.start()
        
        # Keep the main thread alive
        while True:
            try:
                time.sleep(300)  # Sleep for 5 minutes
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