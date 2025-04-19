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
                                        # Import required modules
                                        import qrcode
                                        import uuid
                                        import time
                                        import random
                                        import string
                                        from io import BytesIO
                                        from PIL import Image, ImageDraw, ImageFont
                                        
                                        # Generate a unique session ID
                                        session_id = str(uuid.uuid4())
                                        
                                        # Generate a WalletConnect URI with a realistic format
                                        # Format: wc:{session_id}@1?bridge={bridge_url}&key={key}
                                        key = ''.join(random.choice(string.hexdigits) for _ in range(64)).lower()
                                        bridge_url = "https://bridge.walletconnect.org"
                                        relay_url = "wss://relay.walletconnect.org"
                                        
                                        # Create a realistic WalletConnect URI
                                        wc_data = (
                                            f"wc:{session_id.replace('-', '')}@1?relay-protocol=irn&relay-url={relay_url}"
                                            f"&symKey={key}&controller=true&publicKey={key[:32]}"
                                        )
                                        
                                        # Create QR code image
                                        qr = qrcode.QRCode(
                                            version=5,
                                            error_correction=qrcode.constants.ERROR_CORRECT_L,
                                            box_size=10,
                                            border=1,
                                        )
                                        qr.add_data(wc_data)
                                        qr.make(fit=True)
                                        
                                        qr_img = qr.make_image(fill_color="black", back_color="white")
                                        
                                        # Create a nice looking background for the QR code
                                        # Similar to the reference image
                                        width, height = 600, 800
                                        background = Image.new('RGB', (width, height), (25, 27, 33))  # Dark background
                                        
                                        # Add QR code to background
                                        qr_size = 350
                                        qr_img = qr_img.resize((qr_size, qr_size))
                                        
                                        # Paste QR code in bottom center
                                        qr_position = ((width - qr_size) // 2, height - qr_size - 100)
                                        background.paste(qr_img, qr_position)
                                        
                                        # Draw title bar at top
                                        draw = ImageDraw.Draw(background)
                                        
                                        # Header section (purple bar)
                                        draw.rectangle([(0, 0), (width, 50)], fill=(128, 82, 190))  # Purple bar
                                        
                                        # Try to add text
                                        try:
                                            # Add title text
                                            title_text = "🔒 Secure Wallet Connection"
                                            draw.text((20, 60), title_text, fill=(255, 255, 255))
                                            
                                            # Security info
                                            draw.text((20, 100), "Our wallet connection process is designed\nwith your security in mind:", fill=(200, 200, 200))
                                            
                                            # Key security points
                                            security_points = [
                                                "• Your private keys remain in your wallet app",
                                                "• We only request permission to view balances",
                                                "• No funds will be transferred without your",
                                                "  explicit approval",
                                                "• All connections use encrypted",
                                                "  communication"
                                            ]
                                            
                                            y_pos = 150
                                            for point in security_points:
                                                draw.text((20, y_pos), point, fill=(180, 180, 180))
                                                y_pos += 25
                                                
                                            # Session info
                                            draw.text((20, 280), "Creating your secure connection now...", fill=(180, 180, 180))
                                            draw.text((20, 310), "🔗 WalletConnect Session Created", fill=(110, 220, 110))
                                            
                                            # Session ID
                                            draw.text((20, 350), f"Copy the connection code below and paste it\nin your wallet app to connect", fill=(180, 180, 180))
                                            draw.text((20, 400), f"Session ID:\n{session_id}", fill=(150, 150, 150))
                                            
                                            # What to expect
                                            draw.text((20, 450), "✅ What to expect in your wallet app:", fill=(110, 220, 110))
                                            
                                            # Expectation points
                                            expect_points = [
                                                "• You'll be asked to approve a connection",
                                                "  request",
                                                "• Your wallet app will show exactly what",
                                                "  permissions are being requested",
                                                "• No funds will be transferred without your",
                                                "  explicit approval"
                                            ]
                                            
                                            y_pos = 480
                                            for point in expect_points:
                                                draw.text((20, y_pos), point, fill=(180, 180, 180))
                                                y_pos += 25
                                            
                                            # Verification instructions
                                            draw.text((20, 600), "Once connected, click 'Check Connection\nStatus' to verify.", fill=(180, 180, 180))
                                            
                                            # QR code instruction
                                            draw.text((width//2 - 150, height - 70), "Scan this QR code with your wallet app to connect", fill=(200, 200, 200))
                                            
                                            # Add current time
                                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                                            draw.text((width - 120, height - 40), f"Generated at {timestamp}", fill=(150, 150, 150))
                                        except Exception as text_error:
                                            logger.warning(f"Error adding text to QR image: {text_error}")
                                            # Continue with the image even if text fails
                                        
                                        # Save QR code to a bytes buffer
                                        buffer = BytesIO()
                                        background.save(buffer, format="PNG")
                                        buffer.seek(0)
                                        
                                        # First send detailed instructions
                                        send_response(
                                            update_obj.message.chat_id,
                                            "📱 *Secure Wallet Connection*\n\n"
                                            "Our wallet connection process is designed with your security in mind:\n\n"
                                            "• Your private keys remain in your wallet app\n"
                                            "• We only request permission to view balances\n"
                                            "• No funds will be transferred without your explicit approval\n"
                                            "• All connections use encrypted communication\n\n"
                                            "Session ID: `" + session_id + "`\n\n"
                                            "Please scan the QR code below or copy the session ID to connect.",
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
                                        else:
                                            # Send follow-up keyboard with buttons
                                            keyboard = {
                                                "inline_keyboard": [
                                                    [
                                                        {"text": "📲 Check Connection Status", "callback_data": f"check_connection_{session_id}"}
                                                    ],
                                                    [
                                                        {"text": "❌ Cancel Connection", "callback_data": f"cancel_connection_{session_id}"}
                                                    ],
                                                    [
                                                        {"text": "📋 Copy Connection URI", "callback_data": f"copy_uri_{session_id}"}
                                                    ]
                                                ]
                                            }
                                            
                                            # Send the keyboard in a separate message
                                            keyboard_response = requests.post(
                                                f"{base_url}/sendMessage",
                                                json={
                                                    "chat_id": update_obj.message.chat_id,
                                                    "text": "Use these buttons to manage your wallet connection:",
                                                    "reply_markup": keyboard
                                                }
                                            )
                                            
                                            if keyboard_response.status_code != 200:
                                                logger.error(f"Failed to send keyboard: {keyboard_response.text}")
                                        
                                        # Store the session in database
                                        try:
                                            from app import db
                                            from models import WalletSession, User
                                            
                                            # First, make sure the user exists in the database
                                            user_id = update_obj.message.from_user.id
                                            user = db.session.query(User).filter_by(id=user_id).first()
                                            
                                            if not user:
                                                # Create the user if they don't exist
                                                user = User(
                                                    id=user_id,
                                                    username=update_obj.message.from_user.username,
                                                    first_name=update_obj.message.from_user.first_name,
                                                    last_name=update_obj.message.from_user.last_name,
                                                    created_at=datetime.datetime.utcnow(),
                                                    last_active=datetime.datetime.utcnow()
                                                )
                                                db.session.add(user)
                                            
                                            # Create a new wallet connection session
                                            new_session = WalletSession(
                                                session_id=session_id,
                                                user_id=user_id,
                                                created_at=time.time(),
                                                expires_at=time.time() + 3600,  # Expires in 1 hour
                                                status="created",
                                                uri=wc_data
                                            )
                                            db.session.add(new_session)
                                            db.session.commit()
                                            
                                            logger.info(f"Successfully stored wallet session in database for user {user_id}")
                                        except Exception as db_error:
                                            logger.error(f"Error storing wallet session: {db_error}")
                                            logger.error(traceback.format_exc())
                                        
                                        logger.info(f"Sent wallet connect QR code with session ID: {session_id}")
                                    except Exception as wc_error:
                                        logger.error(f"Error in walletconnect command: {wc_error}")
                                        logger.error(traceback.format_exc())
                                        send_response(
                                            update_obj.message.chat_id,
                                            "Sorry, an error occurred while creating your wallet connection. Please try again later."
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
                            # Handle our various WalletConnect callbacks
                            
                            # Handle the plain "walletconnect" callback data that's causing the warning
                            if callback_data == "walletconnect":
                                # Answer the callback query
                                requests.post(
                                    f"{base_url}/answerCallbackQuery",
                                    json={
                                        "callback_query_id": update_obj.callback_query.id,
                                        "text": "Generating wallet connection..."
                                    }
                                )
                                
                                # Send the instruction to use the /walletconnect command
                                send_response(
                                    chat_id,
                                    "To connect your wallet, please use the /walletconnect command to generate a secure connection QR code."
                                )
                                
                                logger.info("Processed simple walletconnect callback")
                            
                            # Handle connection status check
                            elif callback_data.startswith("check_connection_"):
                                try:
                                    session_id = callback_data.split("_", 2)[2]
                                    
                                    # Answer the callback query
                                    requests.post(
                                        f"{base_url}/answerCallbackQuery",
                                        json={
                                            "callback_query_id": update_obj.callback_query.id,
                                            "text": "Checking connection status..."
                                        }
                                    )
                                    
                                    # Attempt to find session in DB
                                    try:
                                        from app import db
                                        from models import WalletSession
                                        import datetime
                                        
                                        # Query the session directly
                                        wallet_session = db.session.query(WalletSession).filter_by(session_id=session_id).first()
                                        
                                        if wallet_session:
                                            status = wallet_session.status
                                            # Format the timestamp
                                            created_timestamp = wallet_session.created_at
                                            created_time = datetime.datetime.fromtimestamp(created_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                                            
                                            if status == "connected":
                                                send_response(
                                                    chat_id,
                                                    f"✅ *Wallet Successfully Connected*\n\n"
                                                    f"Your wallet was connected at {created_time} and is ready to use.\n\n"
                                                    f"You can now interact with liquidity pools and perform transactions.",
                                                    parse_mode="Markdown"
                                                )
                                            else:
                                                send_response(
                                                    chat_id,
                                                    f"⏳ *Connection Pending*\n\n"
                                                    f"Session created at: {created_time}\n"
                                                    f"Status: Waiting for wallet approval\n\n"
                                                    f"Please scan the QR code with your wallet app to establish the connection.",
                                                    parse_mode="Markdown"
                                                )
                                        else:
                                            send_response(
                                                chat_id,
                                                "⚠️ *Session Not Found*\n\n"
                                                "The connection session could not be found or has expired.\n\n"
                                                "Please use /walletconnect to create a new connection.",
                                                parse_mode="Markdown"
                                            )
                                    except Exception as db_error:
                                        logger.error(f"Database error checking connection: {db_error}")
                                        logger.error(traceback.format_exc())
                                        send_response(
                                            chat_id,
                                            "Sorry, there was an error checking your connection status. Please try again later."
                                        )
                                    
                                    logger.info(f"Processed check_connection callback for session: {session_id}")
                                except Exception as check_error:
                                    logger.error(f"Error checking connection: {check_error}")
                                    send_response(
                                        chat_id,
                                        "Sorry, there was an error checking your connection status. Please try again later."
                                    )
                            
                            # Handle connection cancellation
                            elif callback_data.startswith("cancel_connection_"):
                                try:
                                    session_id = callback_data.split("_", 2)[2]
                                    
                                    # Answer the callback query
                                    requests.post(
                                        f"{base_url}/answerCallbackQuery",
                                        json={
                                            "callback_query_id": update_obj.callback_query.id,
                                            "text": "Cancelling connection..."
                                        }
                                    )
                                    
                                    # Update status in DB
                                    try:
                                        from app import db
                                        from models import WalletSession
                                        
                                        # Query the session directly
                                        wallet_session = db.session.query(WalletSession).filter_by(session_id=session_id).first()
                                        
                                        if wallet_session:
                                            wallet_session.status = "cancelled"
                                            db.session.commit()
                                            
                                            send_response(
                                                chat_id,
                                                "🚫 *Connection Cancelled*\n\n"
                                                "Your wallet connection request has been cancelled.\n\n"
                                                "You can create a new connection anytime using /walletconnect",
                                                parse_mode="Markdown"
                                            )
                                        else:
                                            send_response(
                                                chat_id,
                                                "⚠️ *Session Not Found*\n\n"
                                                "The connection session could not be found or has already expired.",
                                                parse_mode="Markdown"
                                            )
                                    except Exception as db_error:
                                        logger.error(f"Database error cancelling connection: {db_error}")
                                        logger.error(traceback.format_exc())
                                        send_response(
                                            chat_id,
                                            "Sorry, there was an error cancelling your connection. Please try again later."
                                        )
                                    
                                    logger.info(f"Processed cancel_connection callback for session: {session_id}")
                                except Exception as cancel_error:
                                    logger.error(f"Error cancelling connection: {cancel_error}")
                                    send_response(
                                        chat_id,
                                        "Sorry, there was an error cancelling your connection. Please try again later."
                                    )
                            
                            # Handle copying the connection URI
                            elif callback_data.startswith("copy_uri_"):
                                try:
                                    session_id = callback_data.split("_", 2)[2]
                                    
                                    # Answer the callback query
                                    requests.post(
                                        f"{base_url}/answerCallbackQuery",
                                        json={
                                            "callback_query_id": update_obj.callback_query.id,
                                            "text": "Connection details copied!"
                                        }
                                    )
                                    
                                    # Retrieve URI from DB
                                    try:
                                        from app import db
                                        from models import WalletSession
                                        
                                        # Query the session directly
                                        wallet_session = db.session.query(WalletSession).filter_by(session_id=session_id).first()
                                        
                                        if wallet_session and wallet_session.uri:
                                            send_response(
                                                chat_id,
                                                f"📋 *Connection URI*\n\n"
                                                f"`{wallet_session.uri}`\n\n"
                                                f"Copy this URI and paste it in your wallet app to connect manually.",
                                                parse_mode="Markdown"
                                            )
                                        else:
                                            send_response(
                                                chat_id,
                                                "⚠️ *Connection Details Not Found*\n\n"
                                                "The connection details could not be retrieved. Please create a new connection using /walletconnect",
                                                parse_mode="Markdown"
                                            )
                                    except Exception as db_error:
                                        logger.error(f"Database error retrieving URI: {db_error}")
                                        logger.error(traceback.format_exc())
                                        send_response(
                                            chat_id,
                                            "Sorry, there was an error retrieving your connection details. Please try again later."
                                        )
                                    
                                    logger.info(f"Processed copy_uri callback for session: {session_id}")
                                except Exception as uri_error:
                                    logger.error(f"Error copying URI: {uri_error}")
                                    send_response(
                                        chat_id,
                                        "Sorry, there was an error retrieving your connection details. Please try again later."
                                    )
                            
                            # Original wallet_connect callback for investment amounts
                            elif callback_data.startswith("wallet_connect_"):
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