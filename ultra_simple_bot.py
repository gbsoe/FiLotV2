#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ULTRA SIMPLE TELEGRAM BOT RUNNER
This file contains the absolute minimum code needed to run the bot.
It should work in any production environment.
"""

import os
import sys
import time
import logging
import traceback
from logging.handlers import RotatingFileHandler

# Set up logging
os.makedirs("logs", exist_ok=True)
log_file = os.path.join("logs", "ultra_simple_bot.log")
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(log_file, maxBytes=10_000_000, backupCount=5)
    ]
)
logger = logging.getLogger("ULTRA_SIMPLE_BOT")

# Log startup
logger.info("Ultra simple bot starting")

# Check environment variables
token = os.environ.get('TELEGRAM_TOKEN') or os.environ.get('TELEGRAM_BOT_TOKEN')
if not token:
    logger.error("CRITICAL: No TELEGRAM_TOKEN found in environment!")
    sys.exit(1)

logger.info(f"Found Telegram token (starting with {token[:4]}...)")

# Try to import the required libraries
try:
    from telegram import Update
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        CallbackQueryHandler, ContextTypes, filters
    )
    logger.info("Successfully imported telegram libraries")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    logger.error("Please install the required packages:")
    logger.error("pip install python-telegram-bot")
    sys.exit(1)

# Simple command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "🚀 Welcome to the Crypto Pool Bot!\n\n"
        "I'm running in ULTRA SIMPLE mode for troubleshooting.\n\n"
        "Use /help to see available commands."
    )
    logger.info(f"User {update.effective_user.id} used /start command")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "🔍 Available commands:\n\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/status - Check bot status\n"
    )
    logger.info(f"User {update.effective_user.id} used /help command")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check bot status when the command /status is issued."""
    uptime = int(time.time() - start_time)
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    await update.message.reply_text(
        f"✅ Bot is active and running in ULTRA SIMPLE mode!\n\n"
        f"🕒 Uptime: {hours}h {minutes}m {seconds}s\n"
        f"🔄 Ultra simple mode: Active\n"
        f"📊 Status: Operational\n"
    )
    logger.info(f"User {update.effective_user.id} checked status")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    text = update.message.text
    response = f"I received your message: '{text}'\n\nThis bot is running in ultra simple mode for troubleshooting."
    
    await update.message.reply_text(response)
    logger.info(f"User {update.effective_user.id} sent a message: {text[:20]}...")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the dispatcher."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Sorry, something went wrong while processing your request."
        )

def main():
    """Run the bot in ultra simple mode."""
    global start_time
    start_time = time.time()
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    logger.info("All handlers registered")
    
    # Start the Bot with error handling
    try:
        logger.info("Starting bot polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Error in polling: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("Bot stopped")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)