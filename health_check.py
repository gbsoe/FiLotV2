"""
Health check module for the application
"""

import os
import logging
import threading
import time
import requests
from app import app

logger = logging.getLogger(__name__)

# Global variable to track if the bot is running
bot_running = False

def add_health_check_route():
    """Add a health check route to the Flask app if it doesn't exist."""
    if not hasattr(app, 'health_check_added'):
        @app.route('/health')
        def health_check():
            """
            Health check endpoint that responds with application status
            """
            status = {
                'app': 'running',
                'bot': 'running' if bot_running else 'stopped',
                'timestamp': time.time()
            }
            return status
        app.health_check_added = True
        logger.info("Health check endpoint added to Flask app")

def start_keep_alive_thread():
    """
    Start a thread that periodically pings the application to keep it alive.
    This helps prevent the application from being terminated due to inactivity.
    """
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    return keep_alive_thread

def keep_alive():
    """
    Function to periodically ping the application to keep it alive.
    This helps prevent the application from being terminated due to inactivity.
    """
    logger.info("Starting keep-alive thread")
    
    # Get the host from environment, default to localhost
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    
    ping_url = f"http://{host}:{port}/health"
    
    while True:
        try:
            # Make a request to the health endpoint
            response = requests.get(ping_url, timeout=5)
            logger.info(f"Keep-alive ping: {response.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ping failed: {e}")
        
        # Sleep for 30 seconds
        time.sleep(30)

def set_bot_status(status: bool):
    """
    Set the bot running status
    
    Args:
        status: True if bot is running, False otherwise
    """
    global bot_running
    bot_running = status