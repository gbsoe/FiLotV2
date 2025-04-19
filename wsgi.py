
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the Flask web application and Telegram bot
"""

import os
import sys
import threading
import logging
import time
import traceback
from app import app  # Import the Flask app from app.py
application = app  # Add WSGI application reference

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize or verify database tables
with app.app_context():
    from models import db
    db.create_all()
    logger.info("Database tables created or verified successfully")

def start_telegram_bot():
    """Start the Telegram bot in a separate thread"""
    logger.info("Starting Telegram bot thread")
    
    # Check for bot token
    token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("CRITICAL: No TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN found in environment!")
        logger.error("Bot cannot start without a token")
        return None
    
    # Log token presence (don't log the actual token!)
    token_start = token[:4] if token else "None"
    logger.info(f"Found Telegram token (starting with {token_start}...)")
    
    def run_bot():
        try:
            # Import and run the bot application creation function directly
            logger.info("Creating Telegram bot application directly")
            from bot import create_application
            
            # Create the application
            application = create_application()
            if not application:
                logger.error("Failed to create Telegram bot application")
                return
                
            logger.info("Telegram bot application created successfully")
            
            # Log handler count
            for group, handlers in application.handlers.items():
                logger.info(f"Bot handlers group {group} has {len(handlers)} handler(s)")
            
            # Start polling for updates - use Flask app context for database operations
            logger.info("Starting bot polling with Flask app context")
            with app.app_context():  # This is the Flask app context, not Telegram's
                application.run_polling(allowed_updates=["message", "callback_query"])
                
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
            logger.error(traceback.format_exc())
    
    # Start the bot in a new thread
    bot_thread = threading.Thread(target=run_bot, name="TelegramBotThread")
    bot_thread.daemon = True  # daemon thread will exit when main thread exits
    bot_thread.start()
    logger.info(f"Telegram bot thread started with ID {bot_thread.ident}")
    return bot_thread

# Anti-idle thread to keep the application alive
def start_anti_idle_thread():
    """Start anti-idle thread"""
    logger.info("Starting anti-idle thread in WSGI app")
    
    def keep_alive():
        logger.info("Anti-idle thread active")
        while True:
            try:
                with app.app_context():
                    from sqlalchemy import text
                    from models import db, ErrorLog, BotStatistics
                    
                    # Log health status
                    result = db.session.execute(text("SELECT 1")).fetchone()
                    logger.info(f"WSGI anti-idle: Database ping successful, result={result}")
                    
                    # Create a log entry to show activity
                    log = ErrorLog(
                        error_type="keep_alive_wsgi",
                        error_message="WSGI anti-idle activity to prevent timeout",
                        module="wsgi.py",
                        resolved=True
                    )
                    db.session.add(log)
                    
                    # Update statistics
                    stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
                    if stats:
                        stats.uptime_percentage += 0.01
                        db.session.commit()
                        logger.info("WSGI anti-idle: Statistics updated")
            except Exception as e:
                logger.error(f"WSGI anti-idle error: {e}")
            time.sleep(60)
    
    idle_thread = threading.Thread(target=keep_alive, daemon=True)
    idle_thread.start()
    logger.info("WSGI anti-idle thread started")
    return idle_thread

# Start the anti-idle thread
anti_idle_thread = start_anti_idle_thread()

# Start the Telegram bot when the WSGI app starts
if 'TELEGRAM_TOKEN' in os.environ or 'TELEGRAM_BOT_TOKEN' in os.environ:
    try:
        bot_thread = start_telegram_bot()
        if bot_thread:
            logger.info("Telegram bot thread started successfully")
        else:
            logger.error("Failed to start Telegram bot thread")
    except Exception as e:
        logger.error(f"Exception starting Telegram bot: {e}")
        logger.error(traceback.format_exc())
else:
    logger.error("CRITICAL: No TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN found in environment!")

# This variable is used by gunicorn to serve the application
application = app

# If run directly, start the development server
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
