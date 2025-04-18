#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Simplified standalone script to run only the Telegram bot
"""

import os
import sys
import time
import logging
import traceback
import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def check_token():
    """Check if telegram token is available"""
    token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        logger.error("CRITICAL: No TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN found in environment variables!")
        logger.error("Bot cannot start without a token")
        sys.exit(1)
    
    token_start = token[:4] if token else "None"
    logger.info(f"Using Telegram token (starting with {token_start}...)")
    return token

def keep_alive():
    """Perform a database query to prevent the server from shutting down due to inactivity"""
    try:
        # Import inside the function to allow app context
        from app import app
        
        # Access the database
        with app.app_context():
            from sqlalchemy import text
            from models import db, ErrorLog
            
            # Execute a simple query
            result = db.session.execute(text("SELECT 1")).fetchone()
            logger.info(f"Keep-alive: Database ping successful, result={result}")
            
            # Create a log entry
            log = ErrorLog(
                error_type="bot_keepalive",
                error_message=f"Bot keep-alive ping at {datetime.datetime.utcnow().isoformat()}",
                module="run_bot_only.py",
                resolved=True
            )
            db.session.add(log)
            db.session.commit()
            
            logger.info("Keep-alive: Log entry created")
    except Exception as e:
        logger.error(f"Keep-alive error: {e}")

def run_bot():
    """Run the Telegram bot directly"""
    
    # Check for token
    check_token()
    
    try:
        # Import with special handling for errors
        try:
            from bot import create_application
        except Exception as e:
            logger.error(f"Failed to import create_application from bot.py: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        
        # Import flask app
        try:
            from app import app
        except Exception as e:
            logger.error(f"Failed to import Flask app: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
            
        # Create telegram application
        logger.info("Creating Telegram bot application")
        try:
            application = create_application()
        except Exception as e:
            logger.error(f"Failed to create Telegram application: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
            
        # Log handlers for verification
        for group, handlers in application.handlers.items():
            logger.info(f"Bot handlers group {group} has {len(handlers)} handler(s)")
            for handler in handlers:
                logger.info(f"    - {handler}")
        
        # Now start the application with database access
        logger.info("Starting Telegram bot polling")
        
        # Do a keep-alive ping before starting
        keep_alive()
        
        # Start polling with Flask context
        with app.app_context():
            from telegram import Update
            
            # Set up a timer for keep-alive
            last_ping_time = time.time()
            ping_interval = 60  # seconds
            
            # Define an error callback that includes keep-alive
            def custom_error_handler(update, context):
                """Error handler that also does keep-alive"""
                nonlocal last_ping_time
                now = time.time()
                
                # Log the error
                logger.error(f"Update {update} caused error: {context.error}")
                
                # Keep-alive if needed
                if now - last_ping_time > ping_interval:
                    logger.info("Doing keep-alive during error handling")
                    keep_alive()
                    last_ping_time = now
            
            # Add custom error handler
            application.add_error_handler(custom_error_handler)
            
            # Run the bot with built-in keep-alive checks
            logger.info("Telegram bot starting with keep-alive checks")
            
            # Define custom polling method with keep-alive
            def polling_with_keepalive():
                nonlocal last_ping_time
                
                while True:
                    try:
                        # Check if we need to do a keep-alive
                        now = time.time()
                        if now - last_ping_time > ping_interval:
                            logger.info("Performing scheduled keep-alive")
                            keep_alive()
                            last_ping_time = now
                        
                        # Process updates for a short time
                        application.process_update(
                            update=Update.de_json(
                                application.bot.get_updates()[0].to_dict(),
                                application.bot
                            )
                        )
                        
                        # Short sleep to avoid using too much CPU
                        time.sleep(1)
                    except Exception as e:
                        logger.error(f"Error in polling loop: {e}")
                        time.sleep(5)  # Sleep longer on error
            
            # Start our custom polling
            polling_with_keepalive()
            
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting standalone bot process")
    run_bot()