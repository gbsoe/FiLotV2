
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
    """Run the Telegram bot"""
    try:
        # First, try to delete any existing webhook
        token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        if token:
            import requests
            requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true")
            # Clear existing updates to prevent conflicts
            requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params={"offset": -1, "timeout": 0})
        
        # Create and initialize the bot application
        bot_app = create_application()
        
        # Run the bot with proper cleanup
        bot_app.run_polling(
            allowed_updates=["message", "callback_query"],
            close_loop=False,
            drop_pending_updates=True,
            stop_signals=None  # Prevent automatic signal handling
        )
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(traceback.format_exc())

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

        # Run bot directly in main thread
        run_bot()

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
