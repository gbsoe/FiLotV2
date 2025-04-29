#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WSGI entry point for the Flask web application and Telegram bot
"""

import os
import sys
import time
import json
import signal
import requests
import logging
import threading
import traceback
from datetime import datetime

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

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# WSGI application reference
from app import app
application = app

# Flag to indicate shutdown is requested
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {sig}, initiating graceful shutdown...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_flask():
    """Run the Flask application"""
    try:
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Error running Flask app: {e}")

def run_telegram_bot():
    """Run the Telegram bot with direct API access (no async)"""
    global shutdown_requested
    
    try:
        # Get the bot token from environment variables
        bot_token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("No TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN found in environment variables")
            return
        
        logger.info("Starting Telegram bot...")
        
        # Set up the API URL
        base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Send startup notification if admin chat ID is available
        try:
            debug_chat_id = os.environ.get("ADMIN_CHAT_ID", "")
            if debug_chat_id and debug_chat_id != "<use_your_actual_id_here>":
                response = requests.post(
                    f"{base_url}/sendMessage",
                    json={
                        "chat_id": debug_chat_id,
                        "text": f"🤖 Bot started in production mode at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    logger.info(f"Sent startup message to admin {debug_chat_id}")
                else:
                    logger.error(f"Failed to send admin message: {response.text}")
        except Exception as e:
            logger.error(f"Error sending startup message: {e}")
        
        # Delete any existing webhook to ensure polling works
        try:
            logger.info("Deleting any existing webhook...")
            response = requests.post(f"{base_url}/deleteWebhook", timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Webhook deletion result: {result}")
            else:
                logger.error(f"Failed to delete webhook: {response.text}")
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
        
        # Function to send messages directly via API
        def send_message(chat_id, text, parse_mode=None, reply_markup=None):
            try:
                params = {
                    "chat_id": chat_id,
                    "text": text
                }
                
                if parse_mode:
                    params["parse_mode"] = parse_mode
                
                if reply_markup:
                    params["reply_markup"] = json.dumps(reply_markup)
                
                response = requests.post(
                    f"{base_url}/sendMessage",
                    json=params,
                    timeout=10
                )
                return response.json() if response.status_code == 200 else None
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return None
        
        # Main polling loop
        offset = 0
        logger.info("Starting update polling loop...")
        
        while not shutdown_requested:
            try:
                # Get updates with long polling
                params = {
                    "offset": offset + 1 if offset else 0,
                    "timeout": 30
                }
                
                # Use a shorter timeout when shutdown is requested
                if shutdown_requested:
                    params["timeout"] = 1
                
                response = requests.get(
                    f"{base_url}/getUpdates",
                    params=params,
                    timeout=35  # Slightly longer than the polling timeout
                )
                
                if response.status_code != 200:
                    logger.error(f"Error getting updates: {response.text}")
                    time.sleep(5)
                    continue
                
                result = response.json()
                
                if not result.get("ok", False):
                    logger.error(f"API returned error: {result}")
                    time.sleep(5)
                    continue
                
                updates = result.get("result", [])
                logger.info(f"Received {len(updates)} updates")
                
                # Process each update
                for update in updates:
                    if shutdown_requested:
                        logger.info("Shutdown requested, stopping update processing")
                        break
                    
                    update_id = update.get("update_id", 0)
                    if update_id >= offset:
                        offset = update_id
                    
                    # Handle message
                    message = update.get("message", {})
                    if message:
                        chat_id = message.get("chat", {}).get("id")
                        text = message.get("text", "")
                        
                        if chat_id and text:
                            logger.info(f"Received message from {chat_id}: {text}")
                            
                            # Handle commands
                            if text.startswith('/'):
                                command = text.split()[0][1:].split('@')[0]
                                
                                # Simple command responses
                                if command == "start":
                                    send_message(
                                        chat_id, 
                                        "👋 Welcome to FiLot - Your Cryptocurrency Pool Assistant! 🚀\n\n"
                                        "I can help you find the best liquidity pools, track your investments, "
                                        "and optimize your DeFi strategy.\n\n"
                                        "Use /help to see available commands."
                                    )
                                elif command == "help":
                                    help_text = (
                                        "🔍 *Available Commands* 🔍\n\n"
                                        "• /start - Start the bot and get a welcome message\n"
                                        "• /help - Display this help message\n"
                                        "• /info - Get information about top liquidity pools\n"
                                        "• /simulate - Simulate investment returns\n"
                                        "• /wallet - Manage your connected wallet\n"
                                        "• /subscribe - Subscribe to daily updates\n"
                                        "• /unsubscribe - Unsubscribe from daily updates\n"
                                        "• /status - Check current system status\n"
                                        "• /profile - Set your investment profile\n"
                                        "• /verify - Verify your identity\n"
                                        "• /faq - Frequently asked questions\n"
                                        "• /social - Our social media links\n\n"
                                        "You can also ask me questions about cryptocurrency pools, investments, "
                                        "and DeFi strategies!"
                                    )
                                    send_message(chat_id, help_text, parse_mode="Markdown")
                                else:
                                    # For other commands, send a maintenance message
                                    send_message(
                                        chat_id,
                                        f"The command /{command} is currently in maintenance mode. Please try again later!"
                                    )
                            else:
                                # Non-command message
                                send_message(
                                    chat_id,
                                    "I'm currently in maintenance mode and can only respond to commands. "
                                    "Please use /help to see available commands."
                                )
                
                # A small delay to avoid tight looping if no updates
                if not updates:
                    time.sleep(1)
                    
            except requests.RequestException as e:
                logger.error(f"Network error in polling loop: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error in polling loop: {e}")
                logger.error(traceback.format_exc())
                time.sleep(5)
        
        logger.info("Bot polling loop ended gracefully")
        
    except Exception as e:
        logger.error(f"Fatal error in bot: {e}")
        logger.error(traceback.format_exc())

def main():
    """Main entry point with proper signal handling"""
    try:
        # Start Flask in a separate thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()
        logger.info("Started Flask thread")

        # Run the Telegram bot in the main thread
        # This ensures proper signal handling
        bot_thread = threading.Thread(target=run_telegram_bot)
        bot_thread.daemon = True
        bot_thread.start()
        logger.info("Started Telegram bot thread")
        
        # Keep the main thread alive until shutdown is requested
        while not shutdown_requested:
            time.sleep(1)
            
        # Allow time for threads to clean up
        logger.info("Waiting for threads to terminate...")
        time.sleep(3)
        logger.info("Shutdown complete")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()