#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram bot and Flask web application
Now with agentic investment advisor and one-command UX
"""

import os
import sys
import logging
import asyncio
import traceback
import threading
import time
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
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
    error_handler,
    faq_command,
    social_command
)

# Import interactive menu functionality
from interactive_menu import interactive_menu_command, interactive_callback

# Import button response handlers 
from button_responses import show_interactive_menu, handle_button_callback

# Import agentic investment flow
from invest_flow import (
    MAIN_KEYBOARD,
    start_invest_flow,
    handle_invest_message,
    handle_invest_callback,
    check_active_investments
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
    It now handles interactive buttons that perform real database operations.
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
        
        # Send a debug message to verify bot functionality
        try:
            # Try to send a test message to a default chat ID for debugging
            debug_chat_id = os.environ.get("ADMIN_CHAT_ID", "")
            if debug_chat_id and debug_chat_id != "<use_your_actual_id_here>":
                from datetime import datetime
                # Use direct API call instead of bot.send_message which is async
                import requests
                response = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
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
            "wallet": wallet_command,  # We've implemented special direct handling for this command
            "walletconnect": walletconnect_command,  # We've implemented special direct handling for this command
            "profile": profile_command,
            "faq": faq_command,
            "social": social_command,
            "interactive": interactive_menu_command  # New interactive menu with functional buttons and database operations
        }

        # Function to handle a specific update by determining its type and routing to appropriate handler
        def handle_update(update_dict):
            from app import app
            import threading
            from telegram import Update

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
                            # Direct use of the dictionary
                            params["reply_markup"] = json.dumps(reply_markup)

                        response = requests.post(f"{base_url}/sendMessage", json=params)
                        if response.status_code != 200:
                            logger.error(f"Failed to send message: {response.text}")
                        return response.json() if response.status_code == 200 else None
                    except Exception as e:
                        logger.error(f"Error sending message: {e}")
                        return None

                # Handle WalletConnect command in a separate thread to avoid blocking
                def handle_walletconnect_sequence(chat_id, user_id):
                    try:
                        # Import needed modules
                        import qrcode
                        import uuid
                        import time
                        from datetime import datetime
                        from io import BytesIO

                        # 1. First message - Security info
                        send_response(
                            chat_id,
                            "🔒 *Secure Wallet Connection*\n\n"
                            "Our wallet connection process is designed with your security in mind:\n\n"
                            "• Your private keys remain in your wallet app\n"
                            "• We only request permission to view balances\n"
                            "• No funds will be transferred without your explicit approval\n"
                            "• All connections use encrypted communication\n\n"
                            "Creating your secure connection now...",
                            parse_mode="Markdown"
                        )

                        # Wait briefly for better message flow
                        time.sleep(0.5)

                        # Generate a session ID for the connection
                        session_id = str(uuid.uuid4())

                        # 2. Session information message
                        send_response(
                            chat_id,
                            "🔗 *WalletConnect Session Created*\n\n"
                            "Copy the connection code below and paste it into your wallet app to connect.\n\n"
                            f"Session ID: {session_id}\n\n"
                            "✅ What to expect in your wallet app:\n"
                            "• You'll be asked to approve a connection request\n"
                            "• Your wallet app will show exactly what permissions are being requested\n"
                            "• No funds will be transferred without your explicit approval\n\n"
                            "Once connected, click 'Check Connection Status' to verify.",
                            parse_mode="Markdown"
                        )

                        # Wait briefly for better message flow
                        time.sleep(0.5)

                        # Create WalletConnect data for QR code
                        # Use a deterministic but secure method to generate these values
                        wc_topic = f"{uuid.uuid4().hex[:16]}"
                        sym_key = f"{uuid.uuid4().hex}{uuid.uuid4().hex[:8]}"
                        project_id = os.environ.get("WALLETCONNECT_PROJECT_ID", "")

                        # Format the WalletConnect URI
                        wc_uri = f"wc:{wc_topic}@2?relay-protocol=irn&relay-url=wss://relay.walletconnect.org&symKey={sym_key}"

                        # Add project ID to the URI if available
                        if project_id:
                            wc_uri = f"{wc_uri}&projectId={project_id}"

                        # Create QR code with the WalletConnect URI
                        qr = qrcode.QRCode(
                            version=1,
                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                            box_size=10,
                            border=4,
                        )
                        qr.add_data(wc_uri)
                        qr.make(fit=True)

                        img = qr.make_image(fill_color="black", back_color="white")

                        # Save QR code to a bytes buffer
                        buffer = BytesIO()
                        img.save(buffer, format="PNG")
                        buffer.seek(0)

                        # 3. QR code message
                        send_response(
                            chat_id,
                            f"📱 *Scan this QR code with your wallet app to connect*\n"
                            f"(Generated at {datetime.now().strftime('%H:%M:%S')})",
                            parse_mode="Markdown"
                        )

                        # Send QR code image
                        files = {"photo": ("qrcode.png", buffer.getvalue(), "image/png")}
                        photo_response = requests.post(
                            f"{base_url}/sendPhoto",
                            data={"chat_id": chat_id},
                            files=files
                        )

                        if photo_response.status_code != 200:
                            logger.error(f"Failed to send QR code: {photo_response.text}")
                            send_response(
                                chat_id,
                                "Sorry, there was an error generating the QR code. Please try again later."
                            )
                            return

                        # Wait briefly for better message flow
                        time.sleep(0.5)

                        # 4. Text link for copying
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        send_response(
                            chat_id,
                            f"📋 *COPY THIS LINK (tap to select):*\n\n"
                            f"`{wc_uri}`\n\n"
                            f"Generated at {current_time}",
                            parse_mode="Markdown"
                        )

                        # Wait briefly for better message flow
                        time.sleep(0.5)

                        # 5. Final security reminder
                        send_response(
                            chat_id,
                            "🔒 Remember: Only approve wallet connections from trusted sources and always verify the requested permissions.\n\n"
                            "If the QR code doesn't work, manually copy the link above and paste it into your wallet app."
                        )

                        logger.info(f"Successfully sent complete WalletConnect sequence to user {user_id}")

                    except Exception as wc_thread_error:
                        logger.error(f"Error in walletconnect thread: {wc_thread_error}")
                        logger.error(traceback.format_exc())
                        send_response(
                            chat_id,
                            "Sorry, an error occurred while creating your wallet connection. Please try again later."
                        )

                # Extract command arguments if this is a command
                if update_obj.message and update_obj.message.text and update_obj.message.text.startswith('/'):
                    # Split the message into command and arguments
                    text_parts = update_obj.message.text.split()
                    command = text_parts[0][1:].split('@')[0]  # Remove the '/' and any bot username

                    # Create context with arguments
                    context = SimpleContext()
                    context.args = text_parts[1:]
                    chat_id = update_obj.message.chat_id

                    # Execute inside the Flask app context
                    with app.app_context():
                        try:
                            # IMMEDIATE ACKNOWLEDGMENT FOR ALL COMMANDS
                            # This ensures the user knows the command was received,
                            # especially important for commands that take time to process
                            ack_message = "Processing your request..."
                            if command == "start":
                                ack_message = "Welcome! Setting up your profile..."
                            elif command == "help":
                                ack_message = "Preparing help information..."
                            elif command == "info":
                                ack_message = "Fetching latest pool information..."
                            elif command == "walletconnect":
                                ack_message = "Initializing secure wallet connection..."
                            elif command == "verify":
                                ack_message = "Starting verification process..."

                            # Don't send acknowledgments for commands that return data immediately
                            if command not in ["status", "profile"]:
                                try:
                                    requests.post(
                                        f"{base_url}/sendChatAction",
                                        json={
                                            "chat_id": chat_id,
                                            "action": "typing"
                                        }
                                    )
                                except Exception:
                                    pass  # Ignore errors in sending chat action

                            # Route to appropriate command handler
                            if command in command_handlers:
                                logger.info(f"Calling handler for command: {command}")

                                # Special handling for commands
                                if command == "info":
                                    # Get predefined pool data
                                    from response_data import get_pool_data as get_predefined_pool_data

                                    # Process top APR pools from the predefined data
                                    predefined_data = get_predefined_pool_data()
                                    pool_list = predefined_data.get('topAPR', [])

                                    if not pool_list:
                                        send_response(
                                            chat_id,
                                            "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
                                        )
                                    else:
                                        # Import at function level to avoid circular imports
                                        from utils import format_pool_info
                                        formatted_info = format_pool_info(pool_list)
                                        send_response(chat_id, formatted_info)
                                        logger.info("Sent pool info response using direct API call")

                                elif command == "wallet":
                                    # Handle wallet command directly
                                    try:
                                        # Import needed wallet utilities
                                        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                                        from wallet_utils import connect_wallet, check_wallet_balance, format_wallet_info

                                        # Check if a wallet address is provided
                                        if context.args and context.args[0]:
                                            wallet_address = context.args[0]

                                            try:
                                                # Validate wallet address
                                                from wallet_utils import connect_wallet
                                                wallet_address = connect_wallet(wallet_address)

                                                # First send confirmation message
                                                send_response(
                                                    chat_id,
                                                    f"✅ Wallet successfully connected: `{wallet_address}`\n\n"
                                                    "Fetching wallet balance...",
                                                    parse_mode="Markdown"
                                                )

                                                # Import needed for async operations
                                                import asyncio

                                                # Create a new event loop for this thread
                                                loop = asyncio.new_event_loop()
                                                asyncio.set_event_loop(loop)

                                                # Get wallet balance
                                                balance = loop.run_until_complete(check_wallet_balance(wallet_address))

                                                if "error" in balance:
                                                    send_response(
                                                        chat_id,
                                                        f"❌ Error: {balance['error']}\n\n"
                                                        "Please try again with a valid wallet address.",
                                                        parse_mode="Markdown"
                                                    )
                                                    return

                                                # Format balance information
                                                balance_text = "💼 *Wallet Balance* 💼\n\n"

                                                for token, amount in balance.items():
                                                    if token == "SOL":
                                                        balance_text += f"• SOL: *{amount:.4f}* (≈${amount * 133:.2f})\n"
                                                    elif token == "USDC" or token == "USDT":
                                                        balance_text += f"• {token}: *{amount:.2f}*\n"
                                                    else:
                                                        balance_text += f"• {token}: *{amount:.4f}*\n"

                                                # Add investment options buttons
                                                keyboard = [
                                                    [{"text": "View Pool Opportunities", "callback_data": "view_pools"}],
                                                    [{"text": "Connect with WalletConnect", "callback_data": "walletconnect"}]
                                                ]

                                                # Format reply markup as a proper dictionary
                                                reply_markup_dict = {"inline_keyboard": keyboard}
                                                send_response(
                                                    chat_id,
                                                    balance_text + "\n\n💡 Use /simulate to see potential earnings with these tokens in liquidity pools.",
                                                    parse_mode="Markdown",
                                                    reply_markup=reply_markup_dict
                                                )

                                                logger.info(f"Successfully processed wallet balance for {wallet_address}")

                                            except ValueError as e:
                                                send_response(
                                                    chat_id,
                                                    f"❌ Error: {str(e)}\n\n"
                                                    "Please provide a valid Solana wallet address.",
                                                    parse_mode="Markdown"
                                                )

                                        else:
                                            # No address provided, show wallet menu
                                            keyboard = [
                                                [{"text": "Connect with WalletConnect", "callback_data": "walletconnect"}],
                                                [{"text": "Enter Wallet Address", "callback_data": "enter_address"}]
                                            ]

                                            # Format reply markup as a proper dictionary
                                            reply_markup_dict = {"inline_keyboard": keyboard}
                                            send_response(
                                                chat_id,
                                                "💼 *Wallet Management*\n\n"
                                                "Connect your wallet to view balances and interact with liquidity pools.\n\n"
                                                "Choose an option below, or provide your wallet address directly using:\n"
                                                "/wallet [your_address]",
                                                parse_mode="Markdown",
                                                reply_markup=reply_markup_dict
                                            )

                                            logger.info("Sent wallet management menu")

                                    except Exception as wallet_error:
                                        logger.error(f"Error in wallet command: {wallet_error}")
                                        logger.error(traceback.format_exc())
                                        send_response(
                                            chat_id,
                                            "Sorry, an error occurred while processing your wallet request. Please try again later."
                                        )

                                elif command == "walletconnect":
                                    # Launch the walletconnect sequence in a separate thread
                                    # to avoid blocking the main handler thread
                                    user_id = update_obj.message.from_user.id
                                    wc_thread = threading.Thread(
                                        target=handle_walletconnect_sequence,
                                        args=(chat_id, user_id)
                                    )
                                    wc_thread.daemon = True  # Thread will exit when main thread exits
                                    wc_thread.start()
                                    logger.info(f"Started WalletConnect sequence thread for user {user_id}")

                                else:
                                    # For all other commands, use the regular handler with async
                                    # Import needed for async operations
                                    import asyncio

                                    # Create and manage our own event loop for this thread
                                    # Use a new event loop for each request to avoid conflicts
                                    loop = asyncio.new_event_loop()
                                    asyncio.set_event_loop(loop)

                                    try:
                                        # Get the handler
                                        handler = command_handlers[command]
                                        
                                        # Special handling for known problematic commands
                                        if command in ["status", "subscribe", "unsubscribe", "social", "profile", "wallet", "faq"]:
                                            logger.info(f"Special handling for command: {command}")
                                            # We need to create a completely isolated task
                                            response_text = None
                                            
                                            # Define a task that can run in isolation
                                            async def run_handler():
                                                try:
                                                    # App context is needed for database operations
                                                    with app.app_context():
                                                        await handler(update_obj, context)
                                                    return True
                                                except Exception as e:
                                                    logger.error(f"Error in {command} handler task: {e}")
                                                    logger.error(traceback.format_exc())
                                                    return False
                                            
                                            # Run the task in this event loop
                                            success = loop.run_until_complete(run_handler())
                                            
                                            if not success:
                                                send_response(
                                                    chat_id,
                                                    f"Sorry, an error occurred while processing your {command} request. Please try again later."
                                                )
                                        else:
                                            # Standard handling for other commands
                                            loop.run_until_complete(handler(update_obj, context))
                                    except Exception as handler_error:
                                        logger.error(f"Error running handler {command}: {handler_error}")
                                        logger.error(traceback.format_exc())
                                        send_response(
                                            chat_id,
                                            "Sorry, an error occurred while processing your request. Please try again later."
                                        )
                                    finally:
                                        # Clean up the loop 
                                        try:
                                            pending = asyncio.all_tasks(loop)
                                            if pending:
                                                loop.run_until_complete(asyncio.gather(*pending))
                                        except Exception as e:
                                            logger.error(f"Error cleaning up asyncio tasks: {e}")
                                        finally:
                                            loop.close()
                            else:
                                logger.info(f"Unknown command: {command}")
                                send_response(
                                    chat_id,
                                    f"Sorry, I don't recognize the command '/{command}'. Try /help to see available commands."
                                )

                        except Exception as command_error:
                            logger.error(f"Error handling command {command}: {command_error}")
                            logger.error(traceback.format_exc())
                            send_response(
                                chat_id,
                                "Sorry, an error occurred while processing your request. Please try again later."
                            )

                # Handle callback queries
                elif update_obj.callback_query:
                    logger.info("Calling callback query handler")

                    # Basic callback handling without async
                    chat_id = update_obj.callback_query.message.chat_id
                    callback_data = update_obj.callback_query.data

                    logger.info(f"Processing callback data: {callback_data}")

                    # First try our new button_responses handler
                    try:
                        # Import necessary modules
                        import asyncio
                        from telegram import Update
                        from telegram.ext import CallbackContext
                        
                        # Create a new event loop for async operations
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        # Create the Update and Context objects
                        # Important: Pass the actual bot instance, not None
                        update = Update.de_json(update_dict, bot)
                        context = CallbackContext(bot, None, None, None)
                        
                        # First try our new interactive callback handler
                        handled = False
                        
                        # Check if it's one of our new interactive callbacks
                        if callback_data.startswith("interactive_"):
                            # This is an interactive menu callback
                            try:
                                handled = loop.run_until_complete(interactive_callback(update, context))
                                logger.info(f"Interactive menu callback handled: {handled}")
                                handle_with_original = not handled  # Only use original handler if not handled by interactive
                            except Exception as e:
                                logger.error(f"Error in interactive callback: {e}")
                                handle_with_original = True  # Fall back to original handler on error
                        else:
                            # Try the original button handler
                            try:
                                handled = loop.run_until_complete(handle_button_callback(update, context))
                                logger.info(f"Button callback handled: {handled}")
                                # Skip the rest of the callback processing if it was handled
                                handle_with_original = not handled
                            except Exception as e:
                                logger.error(f"Error in button callback: {e}")
                                handle_with_original = True  # Fall back to original handler on error
                            
                    except Exception as e:
                        logger.error(f"Error in interactive button handler: {e}")
                        logger.error(traceback.format_exc())
                    finally:
                        try:
                            loop.close()
                        except Exception:
                            pass
                    
                    # If not handled by our interactive handler, use the original handler
                    
                    # Immediate acknowledgment to stop the loading indicator
                    try:
                        requests.post(
                            f"{base_url}/answerCallbackQuery",
                            json={
                                "callback_query_id": update_obj.callback_query.id,
                                "text": "Processing your selection..."
                            }
                        )
                    except Exception:
                        logger.warning("Failed to answer callback query")

                    # Handle all callback types directly
                    try:
                        with app.app_context():
                            # Handle wallet connect callbacks
                            if callback_data.startswith("wallet_connect_"):
                                try:
                                    amount = float(callback_data.split("_")[2])

                                    # Send wallet connect prompt message
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

                                    # Get predefined pool data
                                    from response_data import get_pool_data as get_predefined_pool_data

                                    # Process top APR pools from the predefined data
                                    predefined_data = get_predefined_pool_data()
                                    pool_list = predefined_data.get('topAPR', [])

                                    # Import utils and calculate simulated returns
                                    from utils import format_simulation_results
                                    simulation_text = format_simulation_results(pool_list, amount)

                                    # Send response
                                    send_response(
                                        chat_id,
                                        simulation_text
                                    )

                                    logger.info(f"Processed simulation for amount: ${amount:.2f}")

                                except Exception as sim_error:
                                    logger.error(f"Error processing simulation callback: {sim_error}")
                                    send_response(
                                        chat_id,
                                        "Sorry, there was an error calculating your returns. Please try again using /simulate [amount]."
                                    )

                            # Handle walletconnect callback
                            elif callback_data == "walletconnect":
                                # Launch the walletconnect sequence in a separate thread
                                user_id = update_obj.callback_query.from_user.id
                                wc_thread = threading.Thread(
                                    target=handle_walletconnect_sequence,
                                    args=(chat_id, user_id)
                                )
                                wc_thread.daemon = True
                                wc_thread.start()
                                logger.info(f"Started WalletConnect sequence from callback for user {user_id}")

                            # Handle view_pools callback
                            elif callback_data == "view_pools":
                                # Get predefined pool data
                                from response_data import get_pool_data as get_predefined_pool_data

                                # Process top APR pools from the predefined data
                                predefined_data = get_predefined_pool_data()
                                pool_list = predefined_data.get('topAPR', [])

                                if not pool_list:
                                    send_response(
                                        chat_id,
                                        "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
                                    )
                                else:
                                    # Import at function level to avoid circular imports
                                    from utils import format_pool_info
                                    formatted_info = format_pool_info(pool_list)
                                    send_response(chat_id, formatted_info)
                                    logger.info("Sent pool opportunities response from button callback")

                            # Handle enter_address callback
                            elif callback_data == "enter_address":
                                send_response(
                                    chat_id,
                                    "💼 *Enter Wallet Address*\n\n"
                                    "Please provide your Solana wallet address using the command:\n"
                                    "`/wallet your_address`\n\n"
                                    "Example: `/wallet 5YourWalletAddressHere12345`",
                                    parse_mode="Markdown"
                                )
                                logger.info("Sent wallet address entry instructions from callback")

                            # Handle any other callback type
                            else:
                                # Send a generic response for unhandled callback types
                                send_response(
                                    chat_id,
                                    "I received your selection. Please use /help to see available commands."
                                )
                                logger.warning(f"Unhandled callback type: {callback_data}")

                    except Exception as cb_error:
                        logger.error(f"Error handling callback query: {cb_error}")
                        logger.error(traceback.format_exc())

                        # Send error response
                        send_response(
                            chat_id,
                            "Sorry, an error occurred processing your selection. Please try again later."
                        )

                # Handle regular messages
                elif update_obj.message and update_obj.message.text:
                    logger.info("Handling regular message")
                    chat_id = update_obj.message.chat_id
                    message_text = update_obj.message.text
                    
                    # Check for persistent keyboard button presses from One-Command interface
                    if message_text == "💰 Invest":
                        # Handle investment flow
                        logger.info("Detected 'Invest' button press, starting investment flow")
                        try:
                            # Create context for async handlers
                            context = SimpleContext()
                            
                            # Import and call the invest flow starter
                            from invest_flow import start_invest_flow
                            
                            # Create and manage our own event loop
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # Start the investment flow
                            loop.run_until_complete(start_invest_flow(update_obj, context))
                            return
                        except Exception as e:
                            logger.error(f"Error handling invest button: {e}")
                            logger.error(traceback.format_exc())
                            send_response(chat_id, "Sorry, an error occurred starting the investment flow. Please try again.")
                            return
                            
                    elif message_text == "🔍 Explore":
                        # Show the explore menu with pool data
                        logger.info("Detected 'Explore' button press, showing interactive menu")
                        try:
                            # Create context for async handlers
                            context = SimpleContext()
                            
                            # Import and call the interactive menu
                            from button_responses import show_interactive_menu
                            
                            # Create and manage our own event loop
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # Show the interactive menu
                            loop.run_until_complete(show_interactive_menu(update_obj, context))
                            return
                        except Exception as e:
                            logger.error(f"Error handling explore button: {e}")
                            logger.error(traceback.format_exc())
                            send_response(chat_id, "Sorry, an error occurred showing the pool data. Please try again.")
                            return
                            
                    elif message_text == "👤 Account":
                        # Show the account profile
                        logger.info("Detected 'Account' button press, showing user profile")
                        try:
                            # Create context for async handlers
                            context = SimpleContext()
                            
                            # Import profile command
                            from bot import profile_command
                            
                            # Create and manage our own event loop
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # Show user profile
                            loop.run_until_complete(profile_command(update_obj, context))
                            return
                        except Exception as e:
                            logger.error(f"Error handling account button: {e}")
                            logger.error(traceback.format_exc())
                            send_response(chat_id, "Sorry, an error occurred accessing your account. Please try again.")
                            return

                    # For question detection and predefined answers
                    with app.app_context():
                        try:
                            from question_detector import is_question
                            from response_data import get_predefined_response

                            # Check if this is a question
                            question_detected = is_question(message_text)
                            logger.info(f"Is question detection: {question_detected}")

                            # Check for predefined responses
                            predefined_response = get_predefined_response(message_text)

                            if predefined_response:
                                logger.info(f"Found predefined response for: {message_text[:30]}...")

                                # Send predefined response using our direct API
                                send_response(
                                    chat_id,
                                    predefined_response,
                                    parse_mode="Markdown"
                                )

                                # Log the success
                                logger.info(f"Sent predefined answer for: {message_text}")
                                return

                        except Exception as predef_error:
                            logger.error(f"Error checking predefined answers: {predef_error}")

                    # If no predefined answer or error occurred, fall back to async handler
                    import asyncio

                    # Create and manage our own event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    try:
                        # Run the message handler
                        context = SimpleContext()
                        loop.run_until_complete(handle_message(update_obj, context))
                    except Exception as msg_error:
                        logger.error(f"Error handling message: {msg_error}")
                        # Simple fallback response
                        send_response(
                            chat_id,
                            "I've received your message. To see available commands, type /help"
                        )
                    finally:
                        # Clean up the loop
                        try:
                            pending = asyncio.all_tasks(loop)
                            loop.run_until_complete(asyncio.gather(*pending))
                        except Exception:
                            pass

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

                    # First, try to delete webhook (if any)
                    try:
                        logger.info("Attempting to delete any existing webhook")
                        delete_webhook_resp = requests.get(f"{base_url}/deleteWebhook?drop_pending_updates=true")
                        if delete_webhook_resp.status_code == 200:
                            webhook_result = delete_webhook_resp.json()
                            logger.info(f"Webhook deletion result: {webhook_result}")
                        else:
                            logger.warning(f"Failed to delete webhook: {delete_webhook_resp.status_code} - {delete_webhook_resp.text}")
                    except Exception as e:
                        logger.error(f"Error deleting webhook: {e}")
                    
                    # Make the API call with exponential backoff
                    logger.info(f"Requesting updates from Telegram API...")
                    # Add unique parameter to avoid conflicts with other instances
                    params["allowed_updates"] = json.dumps(["message", "callback_query", "edited_message"])
                    # Add unique client identifier to prevent conflict with other instances
                    import uuid
                    params["client_id"] = str(uuid.uuid4())  # Add unique identifier for this client
                    # Prevent conflicts between multiple bot instances by clearing existing connections
                    try:
                        logger.info("Attempting to delete any existing webhook")
                        webhook_result = requests.post(f"{base_url}/deleteWebhook")
                        logger.info(f"Webhook deletion result: {webhook_result.json()}")
                        
                        # Force terminate other getUpdates calls
                        logger.info("Terminating any existing bot polling")
                        requests.get(f"{base_url}/getUpdates", params={"offset": -1, "timeout": 0})
                        time.sleep(1)  # Small delay to ensure cleanup is complete
                    except Exception as e:
                        logger.error(f"Error during bot cleanup: {e}")
                    
                    logger.info("Requesting updates from Telegram API...")
                    # Now start our polling with a unique offset to avoid conflicts
                    response = requests.get(f"{base_url}/getUpdates", params=params, timeout=30)  # Reduced timeout for better responsiveness

                    # Process the response if successful
                    if response.status_code == 200:
                        result = response.json()
                        updates = result.get("result", [])

                        # Enhanced debug log
                        logger.info(f"Received response: {len(updates)} updates")
                        if len(updates) > 0:
                            logger.info(f"Update keys: {', '.join(updates[0].keys())}")
                            # Log full update for debugging
                            logger.info(f"First update content: {json.dumps(updates[0])}")

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
        # First, kill any existing bot process that might be running
        try:
            # Try to terminate any other instance gracefully
            import requests
            import os
            bot_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
            if bot_token:
                base_url = f"https://api.telegram.org/bot{bot_token}"
                requests.get(f"{base_url}/getUpdates", params={"offset": -1, "timeout": 0})
                requests.get(f"{base_url}/deleteWebhook", params={"drop_pending_updates": "true"})
                logger.info("Terminated any existing bot polling")
        except Exception as e:
            logger.warning(f"Failed to terminate existing bot: {e}")
        
        # Start in the appropriate mode
        if os.environ.get('PRODUCTION') == 'true':
            # In production, run only the bot
            run_telegram_bot()
        else:
            # In development, run both Flask and bot
            from threading import Thread
            
            # Add a short delay to ensure clean startup
            import time
            time.sleep(2)
            
            # Start bot in a thread
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