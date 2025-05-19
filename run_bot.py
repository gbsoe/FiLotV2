#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Production-ready bot runner for FiLot Telegram bot
This script is designed to be run as a standalone process in production
"""

import os
import sys
import time
import logging
import requests
import threading
import traceback
from bot import create_application

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

def check_and_clear_webhooks():
    """Delete any existing webhooks and clear pending updates"""
    try:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            token = os.environ.get("TELEGRAM_TOKEN")
            
        if not token:
            logger.error("No Telegram token found in environment variables")
            return False
            
        # Delete webhook
        webhook_url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
        response = requests.get(webhook_url)
        logger.info(f"Webhook deletion result: {response.json()}")
        
        # Clear updates
        clear_url = f"https://api.telegram.org/bot{token}/getUpdates"
        params = {"offset": -1, "timeout": 1}
        response = requests.get(clear_url, params=params)
        logger.info(f"Update clearing result: {response.json()}")
        
        return True
    except Exception as e:
        logger.error(f"Error clearing webhooks: {e}")
        return False

def keep_alive_thread():
    """Thread to periodically ping database to prevent connection idle timeout"""
    from db_utils import ping_database
    
    while True:
        try:
            success, result = ping_database()
            logger.info(f"Keep-alive database ping: {success}, result={result}")
        except Exception as e:
            logger.error(f"Error in keep-alive ping: {e}")
        
        time.sleep(60)  # Ping every minute

def run_bot_with_recovery():
    """Run the bot with automatic recovery from crashes"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Clear webhooks before starting
            if not check_and_clear_webhooks():
                logger.error("Failed to clear webhooks, waiting before retry")
                time.sleep(10)
                retry_count += 1
                continue
                
            # Create and start the bot
            logger.info("Starting Telegram bot...")
            bot_app = create_application()
            
            # Run the bot
            bot_app.run_polling(
                allowed_updates=["message", "callback_query"],
                close_loop=False,
                drop_pending_updates=True,
                stop_signals=None  # Handle signals manually
            )
            
            # If we get here, the bot exited gracefully
            logger.info("Bot exited normally")
            break
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Bot crashed with error: {e}")
            logger.error(traceback.format_exc())
            logger.info(f"Retrying in 10 seconds... (Attempt {retry_count}/{max_retries})")
            time.sleep(10)
    
    if retry_count >= max_retries:
        logger.critical("Maximum retry attempts reached. Bot failed to start.")
        return False
        
    return True

def main():
    """Main entry point with proper error handling"""
    try:
        # Start keep-alive thread
        alive_thread = threading.Thread(target=keep_alive_thread)
        alive_thread.daemon = True
        alive_thread.start()
        logger.info("Keep-alive thread started")
        
        # Run the bot with recovery
        success = run_bot_with_recovery()
        if not success:
            sys.exit(1)
            
    except Exception as e:
        logger.critical(f"Fatal error in main function: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()