#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Entry point for running the Telegram bot
"""

import os
import asyncio
import logging
import time
import signal
import sys
from dotenv import load_dotenv
from bot import create_application, send_daily_updates

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for Telegram bot token
if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    logger.error("Telegram bot token not found in environment variables.")
    sys.exit(1)

async def main() -> None:
    """Start the bot."""
    logger.info("Starting bot...")
    
    # Create application
    application = create_application()
    
    # Schedule daily updates task
    loop = asyncio.get_event_loop()
    loop.create_task(schedule_daily_updates())
    
    # Start the bot
    await application.run_polling()

async def schedule_daily_updates() -> None:
    """Schedule daily updates at a specific time."""
    while True:
        # Get current time
        current_time = time.localtime()
        
        # Schedule updates for 9:00 AM
        target_hour = 9
        target_minute = 0
        
        if current_time.tm_hour == target_hour and current_time.tm_min == target_minute:
            try:
                await send_daily_updates()
            except Exception as e:
                logger.error(f"Error sending daily updates: {e}")
        
        # Sleep for a minute before checking again
        await asyncio.sleep(60)

def signal_handler(sig, frame):
    """Handle signals for graceful shutdown."""
    logger.info("Shutting down...")
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        task.cancel()
    loop.stop()
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the bot
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running bot: {e}")