#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run script for the Telegram cryptocurrency pool bot
"""

import os
import sys
import logging
import asyncio
from dotenv import load_dotenv
from bot import create_application

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Check if Telegram bot token is available
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("CRITICAL: TELEGRAM_BOT_TOKEN is not set in environment variables")
    sys.exit(1)

async def main() -> None:
    """Run the bot."""
    # Create the application
    application = create_application()
    
    # Start the bot
    await application.initialize()
    logger.info("Bot initialized, starting...")
    
    # Start the bot and run until Ctrl+C is pressed
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    logger.info("Bot started. Press Ctrl+C to stop.")
    
    # Run until the application is stopped
    try:
        await asyncio.Event().wait()  # Run forever
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopping...")
    finally:
        # Stop the bot gracefully
        await application.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        sys.exit(1)