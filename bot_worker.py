#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dedicated worker process for the Telegram bot
This file is designed to be run as a separate process that doesn't bind to any ports
"""

import os
import sys
import logging
import traceback
import time
import requests
from dotenv import load_dotenv
from flask import Flask
from telegram import Update
from telegram.ext import Application

# Import the Flask app but don't run it
from app import app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def keep_alive_thread():
    """
    Function to periodically ping the application to keep it alive.
    """
    # Get the host from environment or use production URL
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    
    # If PRODUCTION_URL is set, use that instead of local host/port
    production_url = os.environ.get("PRODUCTION_URL")
    if production_url:
        ping_url = f"{production_url.rstrip('/')}/health"
    else:
        ping_url = f"http://{host}:{port}/health"
    
    logger.info(f"Starting keep-alive thread, will ping {ping_url}")
    
    while True:
        try:
            response = requests.get(ping_url, timeout=10)
            logger.info(f"Keep-alive ping: {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        
        # Sleep for 30 seconds
        time.sleep(30)

def run_bot():
    """
    Run the Telegram bot as a standalone worker
    """
    # Import the create_application function from bot.py
    from bot import create_application
    
    try:
        # Create the Telegram bot application
        application = create_application()
        
        # Log handlers
        for group, handlers in application.handlers.items():
            logger.info(f"Bot handlers group {group} has {len(handlers)} handler(s)")
            for handler in handlers:
                logger.info(f"    - {handler}")
        
        # Start the bot with Flask context
        with app.app_context():
            logger.info("Running bot polling within Flask app context")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error(f"Error creating or starting Telegram bot: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    import threading
    
    # Start keep-alive thread
    keep_alive = threading.Thread(target=keep_alive_thread, daemon=True)
    keep_alive.start()
    
    # Run the bot
    run_bot()