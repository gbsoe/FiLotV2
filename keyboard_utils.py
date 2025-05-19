#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Keyboard utilities for FiLot Telegram bot
Handles the creation and management of keyboard buttons
"""

from typing import List, Dict, Any, Optional
import logging

from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from menus import MenuType, get_menu_config

# Configure logging
logger = logging.getLogger(__name__)

# Cache of user's current menu state
user_menu_state: Dict[int, MenuType] = {}


def get_reply_keyboard(menu_type: MenuType) -> ReplyKeyboardMarkup:
    """
    Generate a ReplyKeyboardMarkup for a specified menu type.
    
    Args:
        menu_type: The type of menu to generate buttons for
        
    Returns:
        ReplyKeyboardMarkup with the appropriate buttons
    """
    menu_config = get_menu_config(menu_type)
    keyboard = []
    
    # Convert string button labels to KeyboardButton objects
    for row in menu_config.buttons:
        keyboard_row = [KeyboardButton(text=button_text) for button_text in row]
        keyboard.append(keyboard_row)
    
    # Create and return the reply keyboard markup
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,  # Persistent buttons
        input_field_placeholder="Select an option"
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """
    Generate a keyboard removal object.
    
    Returns:
        ReplyKeyboardRemove object to remove the current keyboard
    """
    return ReplyKeyboardRemove()


async def set_menu_state(update: Update, context: ContextTypes.DEFAULT_TYPE, menu_type: MenuType) -> None:
    """
    Set the current menu state for a user and display the appropriate keyboard.
    
    Args:
        update: Telegram update object
        context: Context object for the update
        menu_type: The menu type to set for the user
    """
    if update.effective_user:
        user_id = update.effective_user.id
        user_menu_state[user_id] = menu_type
        
        # Get the menu configuration
        menu_config = get_menu_config(menu_type)
        
        # Generate message text
        message_text = f"{menu_config.title}\n\n{menu_config.help_text}"
        
        # Get the keyboard for the menu
        reply_markup = get_reply_keyboard(menu_type)
        
        # Send the message with the keyboard
        if update.effective_message:
            await update.effective_message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )
        
        logger.info(f"Set menu state for user {user_id} to {menu_type.value}")


async def handle_menu_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle navigation between menus based on button presses.
    
    Args:
        update: Telegram update object
        context: Context object for the update
        
    Returns:
        True if the message was a menu navigation command and was handled,
        False otherwise
    """
    if not update.effective_message or not update.effective_message.text or not update.effective_user:
        return False
        
    user_id = update.effective_user.id
    button_text = update.effective_message.text.strip()
    
    # Handle back button
    if button_text.startswith("⬅️ Back to"):
        current_menu = user_menu_state.get(user_id, MenuType.MAIN)
        menu_config = get_menu_config(current_menu)
        
        if menu_config.parent_menu:
            await set_menu_state(update, context, menu_config.parent_menu)
            return True
        else:
            # Default to main menu if no parent is specified
            await set_menu_state(update, context, MenuType.MAIN)
            return True
    
    # Handle main menu buttons
    menu_mappings = {
        "💰 Explore Pools": MenuType.EXPLORE,
        "👤 My Account": MenuType.ACCOUNT,
        "💹 Invest": MenuType.INVEST,
        "ℹ️ Help": MenuType.HELP,
    }
    
    if button_text in menu_mappings:
        await set_menu_state(update, context, menu_mappings[button_text])
        return True
    
    # Handle explore menu buttons
    explore_mappings = {
        "📊 Pool Information": MenuType.POOL_INFO,
        "🔮 Simulate Investment": MenuType.SIMULATE,
        "❓ FAQ": MenuType.FAQ,
    }
    
    if button_text in explore_mappings:
        await set_menu_state(update, context, explore_mappings[button_text])
        return True
        
    # Handle pool info menu buttons
    if button_text == "📈 High APR Pools":
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="/info high_apr"
            )
            return True
    elif button_text == "💵 Stable Pools":
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="/info stable"
            )
            return True
    elif button_text == "📊 All Pools":
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="/info all"
            )
            return True
    elif button_text == "🔍 Search Pool":
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter a token pair to search for (e.g., SOL-USDC)"
            )
            return True
    
    # Handle account menu buttons
    account_mappings = {
        "👛 Wallet": MenuType.WALLET,
        "📋 Profile": MenuType.PROFILE,
        "🔔 Subscriptions": MenuType.SUBSCRIBE,
    }
    
    if button_text in account_mappings:
        await set_menu_state(update, context, account_mappings[button_text])
        return True
        
    # Handle invest menu buttons
    invest_mappings = {
        "🧠 Smart Invest": MenuType.INVEST,  # Will need its own command handler
        "⭐ Top Pools": MenuType.POOL_INFO,
        "💼 My Investments": MenuType.INVEST,  # Will need its own command handler
    }
    
    if button_text in invest_mappings:
        await set_menu_state(update, context, invest_mappings[button_text])
        return True
        
    # Handle simulation menu buttons
    if button_text == "💲 Quick Simulate":
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="/simulate 1000"
            )
            return True
    elif button_text == "📊 Custom Simulation":
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter your custom investment amount using /simulate [amount].\nFor example: /simulate 5000"
            )
            return True
    elif button_text == "📑 Simulation History":
        # Will implement this function later - for now just stay in the current menu
        await set_menu_state(update, context, MenuType.SIMULATE)
        return True
        
    # Handle help menu buttons
    help_mappings = {
        "📚 Commands": MenuType.HELP,
        "📱 Contact": MenuType.HELP,
        "🔗 Links": MenuType.HELP,
    }
    
    if button_text in help_mappings:
        await set_menu_state(update, context, help_mappings[button_text])
        return True
    
    # If we get here, the message wasn't a menu navigation command
    return False


def get_current_menu(user_id: int) -> MenuType:
    """
    Get the current menu state for a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Current MenuType for the user, or MAIN if not set
    """
    return user_menu_state.get(user_id, MenuType.MAIN)


def reset_menu_state(user_id: int) -> None:
    """
    Reset a user's menu state.
    
    Args:
        user_id: Telegram user ID
    """
    if user_id in user_menu_state:
        del user_menu_state[user_id]