#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced button handler for FiLot Telegram bot
Ensures buttons work correctly with database access
"""

import logging
import os
import json
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import db_utils
from fixed_responses import get_fixed_responses
from button_responses import handle_button_command
from menus import MenuType, get_menu_config

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global fixed responses cache
fixed_responses = get_fixed_responses()

async def handle_button_press(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Enhanced handler for button presses that works with database
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    message = update.message
    if not message or not message.text:
        return
    
    button_text = message.text.strip()
    logger.info(f"Button press detected: {button_text}")
    
    # Log the user interaction
    try:
        user_id = message.from_user.id if message.from_user else None
        if user_id:
            await db_utils.log_user_activity(
                user_id=user_id,
                activity_type="button_press",
                details=f"Button: {button_text}"
            )
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")
    
    # Map buttons to specific commands for processing
    button_mapping = {
        # Main menu buttons
        "💹 Invest": "investment_options",
        "💰 Explore Pools": "explore_pools",
        "👤 My Account": "my_account",
        "ℹ️ Help": "help_menu",
        
        # Explore submenu
        "📊 Pool Information": "pool_info",
        "📈 High APR Pools": "high_apr_pools",
        "💵 Stable Pools": "stable_pools",
        "🔍 Search Pool": "search_pool",
        "📊 All Pools": "all_pools",
        "🔮 Simulate Investment": "simulate_investment",
        "📑 Simulation History": "simulation_history",
        
        # FAQ submenu
        "💡 About Liquidity Pools": "about_liquidity_pools",
        "💱 About APR": "about_apr",
        "⚠️ About Impermanent Loss": "about_impermanent_loss",
        "💸 About DeFi": "about_defi",
        "🔑 About Wallets": "about_wallets",
        
        # Help submenu
        "📚 Commands": "commands",
        "📱 Contact": "contact",
        "🔗 Links": "links",
        
        # Investment submenu
        "🧠 Smart Invest": "smart_invest",
        "⭐ Top Pools": "top_pools",
        "💼 My Investments": "my_investments",
        
        # Account submenu
        "🔔 Subscriptions": "subscription_settings",
        "👤 Profile Settings": "profile_settings",
        "💳 Wallet Settings": "wallet_settings",
        
        # Navigation buttons
        "⬅️ Back to Main Menu": "main_menu",
        "⬅️ Back to Explore": "back_to_explore",
        "⬅️ Back to Account": "back_to_account",
        "⬅️ Back to Help": "back_to_help",
        "⬅️ Back to Invest": "back_to_invest"
    }
    
    # Process the button press
    command = button_mapping.get(button_text)
    if not command:
        logger.warning(f"Unknown button: {button_text}")
        await message.reply_text("Sorry, I don't recognize that button. Please try again.")
        return
    
    # Get the appropriate response based on the command
    try:
        # First try to get data from the database
        response_text = await get_button_response_from_db(command)
        
        # If database access fails, use the fallback system
        if not response_text:
            response_text = handle_button_command(command)
        
        # If still no response, use a default message
        if not response_text:
            response_text = "This feature is currently being updated. Please try again later."
        
        # Send the response
        await message.reply_markdown(response_text)
        
        # Handle special navigation for menu buttons
        if command in ["main_menu", "back_to_explore", "back_to_account", "back_to_help", "back_to_invest"]:
            await send_appropriate_menu(update, context, command)
            
    except Exception as e:
        logger.error(f"Error processing button {button_text}: {e}")
        await message.reply_text("Sorry, I encountered an error processing your request. Please try again later.")

async def get_button_response_from_db(command: str) -> Optional[str]:
    """
    Get button response from database
    
    Args:
        command: The command to retrieve response for
        
    Returns:
        Response text or None if not found/error
    """
    try:
        # Check for fixed responses first
        if command in ["about_liquidity_pools", "about_apr", "about_impermanent_loss"]:
            if command == "about_liquidity_pools":
                return fixed_responses.get("what is liquidity pool")
            elif command == "about_apr":
                return fixed_responses.get("what is apr")
            elif command == "about_impermanent_loss":
                return fixed_responses.get("impermanent loss")
        
        # Otherwise query the database
        # This would typically be a database query to get button texts
        # For now, we'll just return None to fall back to the memory system
        return None
    except Exception as e:
        logger.error(f"Error getting button response from DB: {e}")
        return None

async def send_appropriate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, navigation: str) -> None:
    """
    Send the appropriate menu keyboard based on navigation command
    
    Args:
        update: Telegram update object
        context: Context object for the update
        navigation: Navigation command
    """
    message = update.message
    if not message:
        return
    
    # Define menu keyboards
    main_menu = ReplyKeyboardMarkup([
        ["💹 Invest", "💰 Explore Pools"],
        ["👤 My Account", "ℹ️ Help"]
    ], resize_keyboard=True)
    
    explore_menu = ReplyKeyboardMarkup([
        ["📊 Pool Information", "🔮 Simulate Investment"],
        ["❓ FAQ", "⬅️ Back to Main Menu"]
    ], resize_keyboard=True)
    
    account_menu = ReplyKeyboardMarkup([
        ["🔔 Subscriptions", "👤 Profile Settings"],
        ["💳 Wallet Settings", "⬅️ Back to Main Menu"]
    ], resize_keyboard=True)
    
    help_menu = ReplyKeyboardMarkup([
        ["📚 Commands", "📱 Contact"],
        ["🔗 Links", "⬅️ Back to Main Menu"]
    ], resize_keyboard=True)
    
    invest_menu = ReplyKeyboardMarkup([
        ["🧠 Smart Invest", "⭐ Top Pools"],
        ["💼 My Investments", "⬅️ Back to Main Menu"]
    ], resize_keyboard=True)
    
    # Send the appropriate menu
    if navigation == "main_menu":
        await message.reply_text("🚀 FiLot - Main Menu\n\nWelcome to FiLot! Use the buttons below to navigate.", reply_markup=main_menu)
    elif navigation == "back_to_explore":
        await message.reply_text("💰 Explore Pools\n\nExplore liquidity pools and learn more about investments.", reply_markup=explore_menu)
    elif navigation == "back_to_account":
        await message.reply_text("👤 My Account\n\nManage your account settings and wallet connection.", reply_markup=account_menu)
    elif navigation == "back_to_help":
        await message.reply_text("ℹ️ Help & Support\n\nGet help with using the bot and find resources.", reply_markup=help_menu)
    elif navigation == "back_to_invest":
        await message.reply_text("💹 Investment Options\n\nDiscover investment opportunities and manage your portfolio.", reply_markup=invest_menu)