#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram cryptocurrency pool bot
"""

import os
import logging
import threading
from dotenv import load_dotenv
from bot import setup_bot, run_bot
from app import app

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start_bot():
    """Start the Telegram bot in a separate thread."""
    # Check for required environment variables
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    if not deepseek_api_key:
        logger.warning("DEEPSEEK_API_KEY environment variable not set! AI features will be disabled.")
    
    # Set up and run the bot
    bot = setup_bot()
    run_bot(bot)

def main():
    """Main function to start both the bot and web app."""
    # Load environment variables
    load_dotenv()
    
    # Start bot in a separate thread if running locally
    if __name__ == "__main__":
        bot_thread = threading.Thread(target=start_bot)
        bot_thread.daemon = True
        bot_thread.start()
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
