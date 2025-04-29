#!/usr/bin/env python3
"""
Main entry point for the Telegram bot and Flask web application
"""

import os
import sys
import time
import json
import requests
import logging
import threading
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/bot.log')
    ]
)

logger = logging.getLogger(__name__)

# Import flask app (this will initialize the database)
from app import app

def main():
    """
    Main function to start both the Flask app and Telegram bot
    """
    # Set up a web server to serve the Flask app 
    from app import app
    # Create a thread to run the Flask app
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5001))
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Started Flask app thread")
    
    # Start the Telegram bot
    try:
        # Get the bot token from environment variables
        bot_token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            logger.error("No TELEGRAM_TOKEN or TELEGRAM_BOT_TOKEN found in environment variables")
            return
        
        logger.info("Terminated any existing bot polling")
        
        # Create a bot instance directly
        base_url = f"https://api.telegram.org/bot{bot_token}"
        logger.info("Created Telegram bot instance")
        
        # Send a debug message to verify bot functionality
        try:
            # Try to send a test message to a default chat ID for debugging
            debug_chat_id = os.environ.get("ADMIN_CHAT_ID", "")
            if debug_chat_id and debug_chat_id != "<use_your_actual_id_here>":
                # Use direct API call instead of bot.send_message which is async
                response = requests.post(
                    f"{base_url}/sendMessage",
                    json={
                        "chat_id": debug_chat_id,
                        "text": f"🤖 Bot restarted and online at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                )
                if response.status_code == 200:
                    logger.info(f"Sent startup message to debug chat {debug_chat_id}")
                else:
                    logger.error(f"Failed to send debug message: {response.text}")
            else:
                logger.info("No valid ADMIN_CHAT_ID found for debug messages")
        except Exception as e:
            logger.error(f"Error sending debug message: {e}")
            
        # Import command handlers from bot.py
        from bot import (
            start_command, help_command, info_command, simulate_command,
            subscribe_command, unsubscribe_command, status_command,
            verify_command, wallet_command, walletconnect_command,
            profile_command, faq_command, social_command,
            handle_message, handle_callback_query
        )
        
        # Start update polling thread
        logger.info("Starting update polling thread")
        
        # First delete any existing webhook to ensure polling works
        logger.info("Attempting to delete any existing webhook")
        response = requests.post(f"{base_url}/deleteWebhook")
        webhook_result = response.json() if response.status_code == 200 else {"ok": False, "error": response.text}
        logger.info(f"Webhook deletion result: {webhook_result}")
    
        # Function to send a direct response using the Telegram API
        def send_response(chat_id, text, parse_mode=None, reply_markup=None):
            try:
                params = {
                    "chat_id": chat_id,
                    "text": text,
                }
                
                if parse_mode:
                    params["parse_mode"] = parse_mode
                    
                if reply_markup:
                    # Direct use of the dictionary
                    params["reply_markup"] = json.dumps(reply_markup)
                    
                response = requests.post(f"{base_url}/sendMessage", json=params)
                if response.status_code != 200:
                    logger.error(f"Failed to send message: {response.text}")
                return response.json() if response.status_code == 200 else None
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                return None
                
        # Main polling loop to fetch and process updates
        last_update_id = 0
        
        while True:
            try:
                logger.info("Requesting updates from Telegram API...")
                response = requests.get(
                    f"{base_url}/getUpdates",
                    params={
                        "offset": last_update_id + 1,
                        "timeout": 30
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Error getting updates: {response.text}")
                    time.sleep(5)
                    continue
                    
                updates = response.json()
                logger.info(f"Received response: {len(updates.get('result', []))} updates")
                
                if not updates.get('ok', False):
                    logger.error(f"Error in updates response: {updates}")
                    time.sleep(5)
                    continue
                    
                for update in updates.get('result', []):
                    # Process each update
                    update_id = update.get('update_id')
                    if update_id > last_update_id:
                        last_update_id = update_id
                    
                    # Extract message data if it exists
                    message = update.get('message', {})
                    callback_query = update.get('callback_query', {})
                    
                    if message:
                        chat_id = message.get('chat', {}).get('id')
                        text = message.get('text', '')
                        user_id = message.get('from', {}).get('id')
                        username = message.get('from', {}).get('username', 'unknown')
                        
                        if chat_id:
                            logger.info(f"Received message from user {user_id} (@{username}): {text}")
                            
                            # Special handling for commands (messages starting with '/')
                            if text and text.startswith('/'):
                                # Parse command
                                parts = text.split()
                                command = parts[0][1:].split('@')[0]  # Remove '/' and any bot username
                                args = parts[1:] if len(parts) > 1 else []
                                
                                logger.info(f"Received command: /{command} with args: {args}")
                                
                                # Send immediate acknowledgment to user
                                ack_message = f"Received command: /{command}"
                                if command == "start":
                                    ack_message = "Welcome to FiLot! Setting up your profile..."
                                elif command == "help":
                                    ack_message = "Preparing help information..."
                                elif command == "info":
                                    ack_message = "Fetching latest pool information..."
                                elif command == "wallet":
                                    ack_message = "Accessing wallet functions..."
                                elif command == "simulate":
                                    ack_message = "Setting up investment simulation..."
                                    
                                # Send the acknowledgment message
                                send_response(chat_id, ack_message)
                                
                                # Process the command
                                try:
                                    if command == "start":
                                        # Special direct handling for start command
                                        send_response(
                                            chat_id, 
                                            "👋 Welcome to FiLot - Your Cryptocurrency Pool Assistant! 🚀\n\n"
                                            "I can help you find the best liquidity pools, track your investments, "
                                            "and optimize your DeFi strategy.\n\n"
                                            "Use /help to see available commands."
                                        )
                                    elif command == "help":
                                        # Direct handling for help command
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
                                        send_response(chat_id, help_text, parse_mode="Markdown")
                                    elif command == "info":
                                        # Special direct handling for pool info
                                        from response_data import get_pool_data as get_predefined_pool_data
                                        from utils import format_pool_info
                                        
                                        # Get predefined pool data
                                        pool_data = get_predefined_pool_data()
                                        top_pools = pool_data.get('topAPR', [])
                                        
                                        if top_pools:
                                            formatted_info = format_pool_info(top_pools)
                                            send_response(chat_id, formatted_info)
                                        else:
                                            send_response(
                                                chat_id, 
                                                "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
                                            )
                                    else:
                                        # For all other commands, send a temporary message
                                        send_response(
                                            chat_id,
                                            f"The command /{command} is currently in maintenance mode. Please try again later!"
                                        )
                                except Exception as cmd_error:
                                    logger.error(f"Error processing command /{command}: {cmd_error}")
                                    logger.error(traceback.format_exc())
                                    send_response(
                                        chat_id,
                                        "Sorry, an error occurred while processing your request. Our team has been notified."
                                    )
                            else:
                                # Handle regular messages
                                try:
                                    # Simple non-command message handling
                                    send_response(
                                        chat_id,
                                        "I'm currently in maintenance mode and can only respond to commands. "
                                        "Please use /help to see available commands."
                                    )
                                except Exception as msg_error:
                                    logger.error(f"Error processing message: {msg_error}")
                    
                    elif callback_query:
                        # Handle callback queries (button clicks)
                        callback_id = callback_query.get('id')
                        chat_id = callback_query.get('message', {}).get('chat', {}).get('id')
                        data = callback_query.get('data')
                        user_id = callback_query.get('from', {}).get('id')
                        
                        if callback_id and chat_id and data:
                            logger.info(f"Received callback query from user {user_id}: {data}")
                            
                            # Acknowledge the callback query
                            try:
                                requests.post(
                                    f"{base_url}/answerCallbackQuery",
                                    json={"callback_query_id": callback_id}
                                )
                            except Exception:
                                pass
                            
                            # Respond to the button click
                            try:
                                send_response(
                                    chat_id,
                                    f"Button action '{data}' is currently in maintenance mode. Please try again later!"
                                )
                            except Exception as cb_error:
                                logger.error(f"Error processing callback query: {cb_error}")
                
                # Sleep a bit to avoid hitting API limits if there were no updates
                if not updates.get('result'):
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in main polling loop: {e}")
                logger.error(traceback.format_exc())
                time.sleep(5)
                
    except Exception as e:
        logger.error(f"Fatal error in bot: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    logger.info("Starting bot application")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot terminated by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)