
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the Flask web application and Telegram bot
"""

import os
import sys
import logging
import threading
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

def run_bot():
    """Run the Telegram bot with proper event loop handling"""
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Create and run the bot application
        bot_app = create_application()
        
        # Run the bot with the new event loop
        loop.run_until_complete(bot_app.initialize())
        loop.run_until_complete(bot_app.run_polling(allowed_updates=["message", "callback_query"]))
    except Exception as e:
        logger.error(f"Error in bot thread: {e}")
    finally:
        try:
            # Clean up pending tasks
            pending = asyncio.all_tasks(loop)
            loop.run_until_complete(asyncio.gather(*pending))
        except Exception as e:
            logger.error(f"Error cleaning up tasks: {e}")
        finally:
            loop.close()

def main():
    """Main entry point with proper async handling"""
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        # Start bot in a separate thread
        bot_thread = threading.Thread(target=run_bot)
        bot_thread.daemon = True
        bot_thread.start()

        # Keep main thread alive
        while True:
            try:
                flask_thread.join(1)
                bot_thread.join(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
