#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
STANDALONE PRODUCTION BOT RUNNER
This file contains everything needed to run the bot in production.
It does not require any other Python modules except what's imported here.
"""

import os
import sys
import time
import logging
import datetime
import traceback
import threading
import json
import sqlite3
from logging.handlers import RotatingFileHandler

# Set up logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            "logs/production_bot.log", 
            maxBytes=10_000_000, 
            backupCount=5
        )
    ]
)
logger = logging.getLogger("PRODUCTION_BOT")

# Create a simple status database if using SQLite
DB_FILE = "bot_status.db"
def init_status_db():
    """Initialize a simple status database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_status (
        id INTEGER PRIMARY KEY,
        timestamp TEXT,
        status TEXT,
        message TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS keep_alive (
        id INTEGER PRIMARY KEY,
        timestamp TEXT
    )
    ''')
    conn.commit()
    conn.close()
    logger.info("Status database initialized")

def log_status(status, message):
    """Log status to the database"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO bot_status (timestamp, status, message) VALUES (?, ?, ?)",
            (datetime.datetime.now().isoformat(), status, message)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log status: {e}")

def keep_alive_ping():
    """Record a keep-alive ping"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO keep_alive (timestamp) VALUES (?)",
            (datetime.datetime.now().isoformat(),)
        )
        # Keep only the last 100 records
        cursor.execute(
            "DELETE FROM keep_alive WHERE id NOT IN (SELECT id FROM keep_alive ORDER BY id DESC LIMIT 100)"
        )
        conn.commit()
        conn.close()
        logger.info("Keep-alive ping recorded")
    except Exception as e:
        logger.error(f"Failed to record keep-alive: {e}")

# Initialize database
init_status_db()

# Check for Telegram token
telegram_token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
if not telegram_token:
    logger.error("CRITICAL: No TELEGRAM_TOKEN found in environment!")
    log_status("ERROR", "No Telegram token found")
    sys.exit(1)

logger.info(f"Found Telegram token (starting with {telegram_token[:4]}...)")
log_status("INFO", "Telegram token found")

# Try to import the required libraries
try:
    import requests
    from telegram import Update, Bot
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
    
    logger.info("Successfully imported telegram libraries")
    log_status("INFO", "Telegram libraries imported successfully")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    log_status("ERROR", f"Import error: {e}")
    logger.error("Please install the required packages:")
    logger.error("pip install python-telegram-bot requests")
    sys.exit(1)

# Keep-alive thread
def keep_alive_thread():
    """Thread that performs regular activity to prevent the application from being terminated due to inactivity."""
    logger.info("Starting keep-alive thread")
    
    while True:
        try:
            keep_alive_ping()
            time.sleep(60)  # Every minute
        except Exception as e:
            logger.error(f"Error in keep-alive thread: {e}")
            time.sleep(10)  # On error, wait less time before retrying

# Simple command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "🚀 Welcome to the Crypto Pool Bot! I'm here to help you with cryptocurrency liquidity pools.\n\n"
        "Use /help to see available commands."
    )
    log_status("INFO", f"User {update.effective_user.id} used /start command")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "🔍 Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/status - Check bot status\n"
        "\nYou can also ask me questions about crypto pools!"
    )
    log_status("INFO", f"User {update.effective_user.id} used /help command")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot status when the command /status is issued."""
    uptime = int(time.time() - start_time)
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    await update.message.reply_text(
        f"✅ Bot is active and running!\n\n"
        f"🕒 Uptime: {hours}h {minutes}m {seconds}s\n"
        f"🔄 Production mode: Active\n"
        f"📊 Status: Operational\n"
    )
    log_status("INFO", f"User {update.effective_user.id} checked status")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    text = update.message.text
    response = f"I received your message: '{text}'\n\nThis bot is running in production mode. Please use commands like /help to interact with me."
    
    await update.message.reply_text(response)
    log_status("INFO", f"User {update.effective_user.id} sent a message")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the dispatcher."""
    logger.error(f"Exception while handling an update: {context.error}")
    log_status("ERROR", f"Exception in update handler: {context.error}")
    
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong while processing your request."
        )

# Create and start the bot
def run_bot():
    """Set up and run the Telegram bot."""
    global start_time
    start_time = time.time()
    
    # Log the start
    logger.info("Starting bot in production mode")
    log_status("INFO", "Bot starting in production mode")
    
    try:
        # Create the Application
        application = Application.builder().token(telegram_token).build()
        
        # Register handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Register error handler
        application.add_error_handler(error_handler)
        
        # Log successful registration
        logger.info("All handlers registered successfully")
        log_status("INFO", "Handlers registered")
        
        # Start keep-alive thread
        threading.Thread(target=keep_alive_thread, daemon=True).start()
        
        # Start the Bot
        logger.info("Starting bot polling")
        log_status("INFO", "Bot polling started")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Fatal error starting bot: {e}")
        logger.error(traceback.format_exc())
        log_status("ERROR", f"Fatal error: {e}")
        sys.exit(1)

# Run the bot if executed directly
if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        log_status("INFO", "Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        log_status("ERROR", f"Unhandled exception: {e}")
        sys.exit(1)