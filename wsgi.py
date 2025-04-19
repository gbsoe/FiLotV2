
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
    level=logging.INFO,
    handlers=[
        logging.FileHandler("logs/production.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WSGI application reference
application = app

def run_flask():
    """Run the Flask application"""
    try:
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")

async def run_bot():
    """Run the Telegram bot with proper async handling"""
    try:
        bot_app = create_application()
        await bot_app.initialize()
        await bot_app.start()
        logger.info("Bot started successfully")
        
        # Keep the bot running
        try:
            await bot_app.run_polling(allowed_updates=["message", "callback_query"])
        except Exception as polling_error:
            logger.error(f"Error during polling: {polling_error}")
        finally:
            await bot_app.stop()
            await bot_app.shutdown()
    except Exception as e:
        logger.error(f"Error running bot: {e}")

def main():
    """Main entry point with proper async handling"""
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Start Flask in a separate thread
        from threading import Thread
        flask_thread = Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        
        # Run the bot with proper async handling
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_bot())
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
