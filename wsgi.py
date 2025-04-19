#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the Flask web application and Telegram bot
"""

import os
import sys
import logging
import asyncio
from app import app
from bot import create_application

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# WSGI application reference
application = app

async def main():
    """Run both the Flask app and Telegram bot"""
    try:
        # Create and initialize the bot
        bot_app = create_application()

        # Start the Flask app in a separate thread
        from threading import Thread
        web_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
        web_thread.daemon = True
        web_thread.start()

        # Run the bot in the main thread
        await bot_app.initialize()
        await bot_app.run_polling()

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())