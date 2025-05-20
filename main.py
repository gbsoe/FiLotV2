#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main application file for the Telegram cryptocurrency pool bot
"""

import os
import logging
import json
import time
import threading
import traceback
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from app import app, db
from models import User, Pool, UserQuery

# Configure logging for main app
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global configuration 
POOL_REFRESH_INTERVAL = 3600  # Refresh pool data every hour
MAX_RETRIES = 3  # Number of retries for API requests
RETRY_DELAY = 2  # Delay between retries in seconds

# Import telegram-related imports
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

# Import handlers
from smart_invest import get_smart_invest_conversation_handler, smart_invest_command
from mood_tracking import get_mood_tracking_conversation_handler, mood_command

# Import button response handlers
from button_responses import (
    handle_account, handle_invest, handle_explore_pools, handle_help,
    handle_back_to_main, handle_wallet_settings, handle_update_profile,
    handle_subscription_settings, handle_token_search, handle_predictions,
    handle_my_investments, handle_smart_invest, handle_high_apr_pools,
    handle_pool_info, handle_pool_detail, handle_token_search_result,
    handle_rising_pools, handle_declining_pools, handle_stable_pools,
    handle_custom_token_search, handle_enable_notifications, 
    handle_disable_notifications, handle_notification_preferences,
    handle_help_getting_started, handle_help_commands, handle_faq,
    handle_faq_filot, handle_faq_pools, handle_faq_apr, 
    handle_faq_impermanent_loss, handle_faq_wallet_security,
    handle_toggle_notif_market, handle_toggle_notif_apr,
    handle_toggle_notif_price, handle_toggle_notif_prediction
)

# Import token search conversation flow
from token_search import get_token_search_conversation_handler

# Import wallet and investment execution
from wallet_actions import (
    get_wallet_status, connect_wallet, disconnect_wallet,
    initiate_wallet_connection, check_connection_status,
    execute_investment, check_transaction_status
)
from smart_invest_execution import get_investment_conversation_handler

# Import command handlers
from bot import (
    start_command, help_command, info_command, simulate_command,
    subscribe_command, unsubscribe_command, status_command, verify_command,
    wallet_command, profile_command, faq_command, social_command,
    walletconnect_command, update_query_response, handle_message
)

# Main bot runner
def run_telegram_bot():
    """
    Run the Telegram bot using the python-telegram-bot library
    """
    try:
        # Get telegram token from environment
        telegram_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
        
        if not telegram_token:
            logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
            
        # Initialize the Bot and dispatcher
        application = Application.builder().token(telegram_token).build()
        
        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("info", info_command))
        application.add_handler(CommandHandler("simulate", simulate_command))
        application.add_handler(CommandHandler("subscribe", subscribe_command))
        application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(CommandHandler("verify", verify_command))
        application.add_handler(CommandHandler("wallet", wallet_command))
        application.add_handler(CommandHandler("profile", profile_command))
        application.add_handler(CommandHandler("faq", faq_command))
        application.add_handler(CommandHandler("social", social_command))
        application.add_handler(CommandHandler("walletconnect", walletconnect_command))
        application.add_handler(CommandHandler("mood", mood_command))
        
        # Register conversation handlers
        application.add_handler(get_smart_invest_conversation_handler())
        application.add_handler(get_mood_tracking_conversation_handler())
        application.add_handler(get_token_search_conversation_handler())
        application.add_handler(get_investment_conversation_handler())
        
        # Register callback query handlers with specific patterns
        
        # Main navigation buttons
        application.add_handler(CallbackQueryHandler(handle_account, pattern="^account$"))
        application.add_handler(CallbackQueryHandler(handle_invest, pattern="^invest$"))
        application.add_handler(CallbackQueryHandler(handle_explore_pools, pattern="^explore_pools$"))
        application.add_handler(CallbackQueryHandler(handle_help, pattern="^help$"))
        application.add_handler(CallbackQueryHandler(handle_back_to_main, pattern="^back_to_main$"))
        
        # Account/profile options
        application.add_handler(CallbackQueryHandler(handle_wallet_settings, pattern="^wallet_settings$"))
        application.add_handler(CallbackQueryHandler(handle_update_profile, pattern="^update_profile$"))
        application.add_handler(CallbackQueryHandler(handle_subscription_settings, pattern="^subscription_settings$"))
        
        # Investment options
        application.add_handler(CallbackQueryHandler(handle_smart_invest, pattern="^smart_invest$"))
        application.add_handler(CallbackQueryHandler(handle_high_apr_pools, pattern="^high_apr$"))
        application.add_handler(CallbackQueryHandler(handle_pool_info, pattern="^top_pools$"))
        application.add_handler(CallbackQueryHandler(handle_my_investments, pattern="^my_investments$"))
        
        # Pool exploration
        application.add_handler(CallbackQueryHandler(handle_pool_info, pattern="^pools$"))
        application.add_handler(CallbackQueryHandler(handle_token_search, pattern="^token_search$"))
        application.add_handler(CallbackQueryHandler(handle_predictions, pattern="^predictions$"))
        
        # Dynamic pattern handlers with regex
        application.add_handler(CallbackQueryHandler(handle_pool_detail, pattern="^pool:"))
        application.add_handler(CallbackQueryHandler(handle_token_search_result, pattern="^search_token_"))
        application.add_handler(CallbackQueryHandler(handle_stable_pools, pattern="^stable_pools:"))
        application.add_handler(CallbackQueryHandler(handle_high_apr_pools, pattern="^high_apr:"))
        
        # Pool predictions
        application.add_handler(CallbackQueryHandler(handle_rising_pools, pattern="^rising_pools$"))
        application.add_handler(CallbackQueryHandler(handle_declining_pools, pattern="^declining_pools$"))
        application.add_handler(CallbackQueryHandler(handle_stable_pools, pattern="^stable_pools$"))
        
        # Notifications & subscriptions
        application.add_handler(CallbackQueryHandler(handle_enable_notifications, pattern="^enable_notifications$"))
        application.add_handler(CallbackQueryHandler(handle_disable_notifications, pattern="^disable_notifications$"))
        application.add_handler(CallbackQueryHandler(handle_notification_preferences, pattern="^notification_preferences$"))
        
        # Help & FAQ
        application.add_handler(CallbackQueryHandler(handle_help_getting_started, pattern="^help_getting_started$"))
        application.add_handler(CallbackQueryHandler(handle_help_commands, pattern="^help_commands$"))
        application.add_handler(CallbackQueryHandler(handle_faq, pattern="^faq$"))
        application.add_handler(CallbackQueryHandler(handle_faq_filot, pattern="^faq_filot$"))
        application.add_handler(CallbackQueryHandler(handle_faq_pools, pattern="^faq_pools$"))
        application.add_handler(CallbackQueryHandler(handle_faq_apr, pattern="^faq_apr$"))
        application.add_handler(CallbackQueryHandler(handle_faq_impermanent_loss, pattern="^faq_impermanent_loss$"))
        application.add_handler(CallbackQueryHandler(handle_faq_wallet_security, pattern="^faq_wallet_security$"))
        
        # Notification toggles
        application.add_handler(CallbackQueryHandler(handle_toggle_notif_market, pattern="^toggle_notif_market$"))
        application.add_handler(CallbackQueryHandler(handle_toggle_notif_apr, pattern="^toggle_notif_apr$"))
        application.add_handler(CallbackQueryHandler(handle_toggle_notif_price, pattern="^toggle_notif_price$"))
        application.add_handler(CallbackQueryHandler(handle_toggle_notif_prediction, pattern="^toggle_notif_prediction$"))
        
        # Custom token search
        application.add_handler(CallbackQueryHandler(handle_custom_token_search, pattern="^custom_token_search$"))
        
        # Register message handler as fallback for everything else
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start the Bot
        logger.info("Starting Telegram bot")
        application.run_polling(poll_interval=1.0, timeout=30)
        
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
            time.sleep(1)
            
            # Start Telegram bot in a separate thread
            bot_thread = Thread(target=run_telegram_bot, daemon=True)
            bot_thread.start()
            
            # Start Flask app in the main thread
            from app import app
            
            # Only bind to 0.0.0.0 when not in production
            app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()