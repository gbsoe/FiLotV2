#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entry point for running the Telegram bot
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
from bot import setup_bot

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    # Load environment variables
    load_dotenv()
    
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
    
    # Start the Bot using polling (run_polling is non-blocking)
    bot.run_polling()

if __name__ == "__main__":
    main()