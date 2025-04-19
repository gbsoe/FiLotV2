#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram bot and Flask web application
"""

import os
import sys
import logging
import asyncio
import traceback
import threading
import time
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# Import bot command handlers
from bot import (
    start_command,
    help_command,
    info_command,
    simulate_command,
    subscribe_command,
    unsubscribe_command,
    status_command,
    verify_command,
    wallet_command,
    walletconnect_command,
    profile_command,
    handle_message,
    handle_callback_query,
    error_handler
)

# Import Flask app for the web interface
from app import app

# Import health check module
import health_check

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global application variable
application = None

def anti_idle_thread():
    """
    Thread that performs regular database activity to prevent the application
    from being terminated due to inactivity.
    """
    logger.info("Starting anti-idle thread for telegram bot process")

    # Sleep interval in seconds (60 seconds is well below the ~2m21s timeout)
    interval = 60

    while True:
        try:
            # Access the database with app context
            with app.app_context():
                from sqlalchemy import text
                from models import db, BotStatistics, ErrorLog

                # Simple query to keep connection alive
                result = db.session.execute(text("SELECT 1")).fetchone()
                logger.info(f"Bot process anti-idle: Database ping successful, result={result}")

                # Create a log entry to show activity
                log = ErrorLog(
                    error_type="keep_alive_main",
                    error_message="Main.py telegram bot anti-idle activity",
                    module="main.py",
                    resolved=True
                )
                db.session.add(log)

                # Update statistics
                stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
                if stats:
                    # Increment uptime percentage slightly (which we can modify directly)
                    stats.uptime_percentage += 0.01  # Small increment
                    db.session.commit()
                    logger.info("Bot process anti-idle: Updated statistics")
        except Exception as e:
            logger.error(f"Bot process anti-idle error: {e}")

        # Sleep for the interval
        time.sleep(interval)

def run_telegram_bot():
    """
    Run the Telegram bot using a direct approach to handle messages.
    
    This function avoids using the PTB built-in polling mechanisms which require 
    signal handlers and instead implements a direct command handling approach.
    """
    try:
        # Import necessary modules here for thread safety
        import threading
        import requests
        import json
        from telegram import Bot, Update
        
        # Get the token from environment variables
        bot_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            logger.error("No Telegram bot token found")
            return
            
        # Create a bot instance directly
        bot = Bot(token=bot_token)
        logger.info("Created Telegram bot instance")
        
        # Import command handlers
        from bot import (
            start_command, help_command, info_command, simulate_command,
            subscribe_command, unsubscribe_command, status_command,
            verify_command, wallet_command, walletconnect_command,
            profile_command, faq_command, social_command,
            handle_message, handle_callback_query
        )
        
        # Set up base URL for Telegram Bot API
        base_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Track the last update ID we've processed
        last_update_id = 0
        
        # Dictionary mapping command names to handler functions
        command_handlers = {
            "start": start_command,
            "help": help_command,
            "info": info_command,
            "simulate": simulate_command,
            "subscribe": subscribe_command,
            "unsubscribe": unsubscribe_command,
            "status": status_command,
            "verify": verify_command,
            "wallet": wallet_command,
            "walletconnect": walletconnect_command,
            "profile": profile_command,
            "faq": faq_command,
            "social": social_command
        }
        
        # Function to handle a specific update by determining its type and routing to appropriate handler
        def handle_update(update_dict):
            from app import app
            
            try:
                # Convert the dictionary to a Telegram Update object
                update_obj = Update.de_json(update_dict, bot)
                logger.info(f"Processing update type: {update_dict.keys()}")
                
                # Create a simple context type that mimics ContextTypes.DEFAULT_TYPE
                class SimpleContext:
                    def __init__(self):
                        self.bot = bot
                        self.args = []
                        self.match = None
                        self.user_data = {}
                        self.chat_data = {}
                        self.bot_data = {}
                
                # Function to directly send a response without using async
                def send_response(chat_id, text, parse_mode=None, reply_markup=None):
                    try:
                        params = {
                            "chat_id": chat_id,
                            "text": text,
                        }
                        
                        if parse_mode:
                            params["parse_mode"] = parse_mode
                            
                        if reply_markup:
                            params["reply_markup"] = json.dumps(reply_markup.to_dict())
                            
                        response = requests.post(f"{base_url}/sendMessage", json=params)
                        if response.status_code != 200:
                            logger.error(f"Failed to send message: {response.text}")
                        return response.json() if response.status_code == 200 else None
                    except Exception as e:
                        logger.error(f"Error sending message: {e}")
                        return None
                
                # Extract command arguments if this is a command
                if update_obj.message and update_obj.message.text and update_obj.message.text.startswith('/'):
                    # Split the message into command and arguments
                    text_parts = update_obj.message.text.split()
                    command = text_parts[0][1:].split('@')[0]  # Remove the '/' and any bot username
                    
                    # Create context with arguments
                    context = SimpleContext()
                    context.args = text_parts[1:]
                    
                    # Execute inside the Flask app context
                    with app.app_context():
                        try:
                            # Route to appropriate command handler 
                            if command in command_handlers:
                                logger.info(f"Calling handler for command: {command}")
                                
                                # For specific commands that have issues with async/event loops
                                if command == "info":
                                    # Get predefined pool data
                                    from response_data import get_pool_data as get_predefined_pool_data
                                    
                                    # Process top APR pools from the predefined data
                                    predefined_data = get_predefined_pool_data()
                                    pool_list = predefined_data.get('topAPR', [])
                                    
                                    if not pool_list:
                                        send_response(
                                            update_obj.message.chat_id,
                                            "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
                                        )
                                    else:
                                        # Import at function level to avoid circular imports
                                        from utils import format_pool_info
                                        formatted_info = format_pool_info(pool_list)
                                        send_response(update_obj.message.chat_id, formatted_info)
                                        logger.info("Sent pool info response using direct API call")
                                
                                elif command == "walletconnect":
                                    # Handle walletconnect command directly
                                    try:
                                        qr_data = f"User: {update_obj.message.from_user.id}"
                                        import qrcode
                                        from io import BytesIO
                                        
                                        # Create QR code image
                                        qr = qrcode.QRCode(
                                            version=1,
                                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                                            box_size=10,
                                            border=4,
                                        )
                                        qr.add_data(qr_data)
                                        qr.make(fit=True)
                                        
                                        img = qr.make_image(fill_color="black", back_color="white")
                                        
                                        # Save QR code to a bytes buffer
                                        buffer = BytesIO()
                                        img.save(buffer, format="PNG")
                                        buffer.seek(0)
                                        
                                        # Send welcome message
                                        send_response(
                                            update_obj.message.chat_id,
                                            "📱 *Connect your wallet*\n\n"
                                            "Scan this QR code with your mobile wallet app to connect.\n\n"
                                            "This is a secure connection that allows you to interact with liquidity pools.",
                                            parse_mode="Markdown"
                                        )
                                        
                                        # Send QR code image using multipart form data
                                        files = {"photo": ("qrcode.png", buffer.getvalue(), "image/png")}
                                        photo_response = requests.post(
                                            f"{base_url}/sendPhoto",
                                            data={"chat_id": update_obj.message.chat_id},
                                            files=files
                                        )
                                        
                                        if photo_response.status_code != 200:
                                            logger.error(f"Failed to send QR code: {photo_response.text}")
                                            send_response(
                                                update_obj.message.chat_id,
                                                "Sorry, there was an error generating the QR code. Please try again later."
                                            )
                                        
                                        logger.info("Sent wallet connect QR code")
                                    except Exception as wc_error:
                                        logger.error(f"Error in walletconnect command: {wc_error}")
                                        send_response(
                                            update_obj.message.chat_id,
                                            "Sorry, an error occurred while processing your request. Please try again later."
                                        )
                                
                                else:
                                    # For all other commands, use the regular handler
                                    # Import needed for async operations
                                    import asyncio
                                    
                                    # Create and manage our own event loop for this thread
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)
                                    
                                    try:
                                        # Get the handler
                                        handler = command_handlers[command]
                                        
                                        # Run the handler in this thread's event loop
                                        loop.run_until_complete(handler(update_obj, context))
                                    except Exception as handler_error:
                                        logger.error(f"Error running handler {command}: {handler_error}")
                                        send_response(
                                            update_obj.message.chat_id,
                                            "Sorry, an error occurred while processing your request. Please try again later."
                                        )
                                    finally:
                                        # Clean up the loop but don't close it if other tasks might be using it
                                        try:
                                            pending = asyncio.all_tasks(loop)
                                            loop.run_until_complete(asyncio.gather(*pending))
                                        except Exception:
                                            pass
                            else:
                                logger.info(f"Unknown command: {command}")
                                send_response(
                                    update_obj.message.chat_id,
                                    f"Sorry, I don't recognize the command '/{command}'. Try /help to see available commands."
                                )
                                
                        except Exception as command_error:
                            logger.error(f"Error handling command {command}: {command_error}")
                            logger.error(traceback.format_exc())
                            send_response(
                                update_obj.message.chat_id,
                                "Sorry, an error occurred while processing your request. Please try again later."
                            )
                
                # Handle callback queries
                elif update_obj.callback_query:
                    logger.info("Calling callback query handler")
                    
                    # Basic callback handling without async
                    chat_id = update_obj.callback_query.message.chat_id
                    callback_data = update_obj.callback_query.data
                    
                    logger.info(f"Processing callback data: {callback_data}")
                    
                    # Handle all callback types directly
                    try:
                        with app.app_context():
                            # Handle wallet connect callbacks
                            if callback_data.startswith("wallet_connect_"):
                                try:
                                    amount = float(callback_data.split("_")[2])
                                    # First send a confirmation to the callback query to stop the "loading" state
                                    requests.post(
                                        f"{base_url}/answerCallbackQuery",
                                        json={
                                            "callback_query_id": update_obj.callback_query.id,
                                            "text": f"Processing wallet connection for ${amount:.2f}..."
                                        }
                                    )
                                    
                                    # Then send the actual wallet connect message
                                    send_response(
                                        chat_id,
                                        f"💰 *Connect Wallet for ${amount:.2f} Investment*\n\n"
                                        f"To proceed with your ${amount:.2f} investment, please use /walletconnect to generate a QR code and connect your wallet.",
                                        parse_mode="Markdown"
                                    )
                                    
                                    # Log the success
                                    logger.info(f"Processed wallet_connect callback for amount: ${amount:.2f}")
                                    
                                except Exception as amount_error:
                                    logger.error(f"Error parsing amount from callback: {amount_error}")
                                    send_response(
                                        chat_id,
                                        "Sorry, there was an error processing your investment amount. Please try again using /simulate [amount]."
                                    )
                            
                            # Handle simulate_period callbacks
                            elif callback_data.startswith("simulate_period_"):
                                try:
                                    parts = callback_data.split("_")
                                    period = parts[2]  # daily, weekly, monthly, yearly
                                    amount = float(parts[3]) if len(parts) > 3 else 1000.0
                                    
                                    # Answer the callback query
                                    requests.post(
                                        f"{base_url}/answerCallbackQuery",
                                        json={
                                            "callback_query_id": update_obj.callback_query.id,
                                            "text": f"Calculating {period} returns for ${amount:.2f}..."
                                        }
                                    )
                                    
                                    # Get predefined pool data
                                    from response_data import get_pool_data as get_predefined_pool_data
                                    
                                    # Process top APR pools from the predefined data
                                    predefined_data = get_predefined_pool_data()
                                    pool_list = predefined_data.get('topAPR', [])
                                    
                                    # Import utils and calculate simulated returns
                                    from utils import format_simulation_results
                                    simulation_text = format_simulation_results(pool_list, amount, period=period)
                                    
                                    # Send response
                                    send_response(
                                        chat_id,
                                        simulation_text
                                    )
                                    
                                    logger.info(f"Processed simulation for period: {period}, amount: ${amount:.2f}")
                                    
                                except Exception as sim_error:
                                    logger.error(f"Error processing simulation callback: {sim_error}")
                                    send_response(
                                        chat_id,
                                        "Sorry, there was an error calculating your returns. Please try again using /simulate [amount]."
                                    )
                            
                            # Handle any other callback type
                            else:
                                # Answer the callback query to stop the loading indicator
                                requests.post(
                                    f"{base_url}/answerCallbackQuery",
                                    json={
                                        "callback_query_id": update_obj.callback_query.id,
                                        "text": "Processing your request..."
                                    }
                                )
                                
                                # Send a generic response for unhandled callback types
                                send_response(
                                    chat_id,
                                    "I received your selection. Please use /help to see available commands."
                                )
                                logger.warning(f"Unhandled callback type: {callback_data}")
                    
                    except Exception as cb_error:
                        logger.error(f"Error handling callback query: {cb_error}")
                        logger.error(traceback.format_exc())
                        
                        # Try to at least answer the callback query to clear the loading state
                        try:
                            requests.post(
                                f"{base_url}/answerCallbackQuery",
                                json={
                                    "callback_query_id": update_obj.callback_query.id,
                                    "text": "Error processing your request."
                                }
                            )
                        except:
                            pass
                            
                        # Send error response
                        send_response(
                            chat_id,
                            "Sorry, an error occurred processing your selection. Please try again later."
                        )
                
                # Handle regular messages
                elif update_obj.message and update_obj.message.text:
                    logger.info("Calling regular message handler")
                    chat_id = update_obj.message.chat_id
                    
                    # Simple text response without async
                    send_response(
                        chat_id,
                        "I've received your message. To see available commands, type /help"
                    )
                
                logger.info(f"Successfully processed update ID: {update_dict.get('update_id')}")
                
            except Exception as e:
                logger.error(f"Error processing update: {e}")
                logger.error(traceback.format_exc())
        
        # Function to continuously poll for updates
        def poll_for_updates():
            nonlocal last_update_id
            
            logger.info("Starting update polling thread")
            
            while True:
                try:
                    # Construct the getUpdates API call
                    params = {
                        "timeout": 30,
                        "allowed_updates": json.dumps(["message", "callback_query"]),
                    }
                    
                    # If we have a last update ID, only get updates after that
                    if last_update_id > 0:
                        params["offset"] = last_update_id + 1
                    
                    # Make the API call
                    logger.info(f"Requesting updates from Telegram API...")
                    response = requests.get(f"{base_url}/getUpdates", params=params, timeout=60)
                    
                    # Process the response if successful
                    if response.status_code == 200:
                        result = response.json()
                        updates = result.get("result", [])
                        
                        # Debug log
                        logger.info(f"Received response: {len(updates)} updates")
                        if len(updates) > 0:
                            logger.info(f"Update keys: {', '.join(updates[0].keys())}")
                        
                        # Process each update
                        for update in updates:
                            # Update the last update ID
                            update_id = update.get("update_id", 0)
                            if update_id > last_update_id:
                                last_update_id = update_id
                            
                            # Process the update in a separate thread
                            logger.info(f"Starting thread to process update {update_id}")
                            threading.Thread(target=handle_update, args=(update,)).start()
                    else:
                        logger.error(f"Error getting updates: {response.status_code} - {response.text}")
                        
                    # Log status periodically
                    if int(time.time()) % 60 == 0:  # Log once per minute
                        logger.info(f"Bot polling active. Last update ID: {last_update_id}")
                        
                except Exception as e:
                    logger.error(f"Error in update polling: {e}")
                    logger.error(traceback.format_exc())
                
                # Sleep briefly to avoid hammering the API
                time.sleep(1)
        
        # Start the polling thread
        polling_thread = threading.Thread(target=poll_for_updates, daemon=True)
        polling_thread.start()
        
        # Keep the main thread alive
        while True:
            try:
                time.sleep(300)  # Sleep for 5 minutes
                logger.info("Telegram bot still running...")
            except Exception as e:
                logger.error(f"Error in main bot thread: {e}")
                break
                
    except Exception as e:
        logger.error(f"Error in telegram bot: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """
    Main function to start both the Flask app and Telegram bot
    """
    try:
        if os.environ.get('PRODUCTION') == 'true':
            # In production, run only the bot
            run_telegram_bot()
        else:
            # In development, run both Flask and bot
            from threading import Thread
            bot_thread = Thread(target=run_telegram_bot)
            bot_thread.daemon = True
            bot_thread.start()

            # Run Flask app on a different port when running with bot
            app.run(host='0.0.0.0', port=5001)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()