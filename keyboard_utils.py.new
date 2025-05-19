#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Keyboard utilities for FiLot Telegram bot
Handles the creation and management of keyboard buttons
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from menus import MenuType, get_menu_config
import db_fallback  # Import our fallback mechanism

# Configure logging
logger = logging.getLogger(__name__)

# Cache of user's current menu state
user_menu_state: Dict[int, MenuType] = {}

# Determine which menus should use one-time keyboard
ONE_TIME_KEYBOARD_MENUS = {
    MenuType.SIMULATE,
    MenuType.WALLET,
    MenuType.PROFILE,
    MenuType.FAQ,
}

# Main menu buttons with standardized callback_data values
MAIN_MENU_BUTTONS = [
    [KeyboardButton("💰 Invest")],
    [KeyboardButton("🧭 Explore Pools")],
    [KeyboardButton("👤 My Account")],
    [KeyboardButton("ℹ️ Help")]
]

# Main menu inline keyboard buttons with standardized callback_data values
MAIN_MENU_INLINE_BUTTONS = [
    [InlineKeyboardButton("💰 Invest", callback_data="invest")],
    [InlineKeyboardButton("🧭 Explore Pools", callback_data="explore_pools")],
    [InlineKeyboardButton("👤 My Account", callback_data="account")],
    [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
]

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
    
    # Determine if this menu should use one-time keyboard
    one_time = menu_type in ONE_TIME_KEYBOARD_MENUS
    
    # Create and return the reply keyboard markup
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=one_time,
        input_field_placeholder="Select an option"
    )

def get_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Generate an InlineKeyboardMarkup for main menu actions.
    
    Returns:
        InlineKeyboardMarkup with the main menu buttons
    """
    return InlineKeyboardMarkup(MAIN_MENU_INLINE_BUTTONS)

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
    if not update.effective_user:
        logger.warning("No user information available in update")
        return
        
    user_id = update.effective_user.id
    
    # Store in memory cache
    user_menu_state[user_id] = menu_type
    
    # Also store in fallback storage
    try:
        await db_fallback.store_menu_state_async(user_id, menu_type.value)
        logger.debug(f"Stored menu state in fallback: {user_id} -> {menu_type.value}")
    except Exception as e:
        logger.warning(f"Failed to store menu state in fallback: {e}")
    
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

async def log_menu_navigation(user_id: int, from_menu: str, to_menu: str) -> None:
    """
    Log menu navigation to the fallback storage.
    
    Args:
        user_id: User ID
        from_menu: Source menu
        to_menu: Destination menu
    """
    try:
        await db_fallback.log_user_activity_async(
            user_id,
            "menu_navigation",
            {"from": from_menu, "to": to_menu}
        )
        logger.debug(f"Logged menu navigation: {user_id} {from_menu} -> {to_menu}")
    except Exception as e:
        logger.warning(f"Failed to log menu navigation: {e}")

async def get_current_menu(user_id: int) -> MenuType:
    """
    Get the current menu state for a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Current MenuType for the user, or MAIN if not set
    """
    # First check in-memory cache
    if user_id in user_menu_state:
        menu = user_menu_state.get(user_id)
        if menu is not None:
            return menu
    
    # Then try the fallback storage
    try:
        menu_str = await db_fallback.get_menu_state_async(user_id)
        if menu_str:
            try:
                # Convert string back to enum
                return MenuType(menu_str)
            except (ValueError, KeyError):
                logger.warning(f"Invalid menu state '{menu_str}' for user {user_id}")
    except Exception as e:
        logger.warning(f"Error retrieving menu state from fallback: {e}")
    
    # Default to MAIN menu and cache it
    default_menu = MenuType.MAIN
    user_menu_state[user_id] = default_menu
    
    # Try to store the default in the database too
    try:
        await db_fallback.store_menu_state_async(user_id, default_menu.value)
    except Exception as e:
        logger.debug(f"Failed to store default menu state: {e}")
        
    return default_menu

async def reset_menu_state(user_id: int) -> None:
    """
    Reset a user's menu state.
    
    Args:
        user_id: Telegram user ID
    """
    # Remove from in-memory cache
    if user_id in user_menu_state:
        del user_menu_state[user_id]
    
    # Store main menu in fallback system
    try:
        await db_fallback.store_menu_state_async(user_id, MenuType.MAIN.value)
        # Log the reset action
        await db_fallback.log_user_activity_async(
            user_id, 
            "menu_reset", 
            {"new_menu": MenuType.MAIN.value}
        )
        logger.info(f"Reset menu state for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to reset menu state in fallback system: {e}")