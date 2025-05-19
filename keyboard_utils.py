#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Keyboard utilities for FiLot Telegram bot
Handles the creation and management of keyboard buttons
"""

from typing import List, Dict, Any, Optional, Tuple, Callable, Awaitable, Union
import logging

from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from menus import MenuType, get_menu_config
import db_fallback  # Import our fallback mechanism

# Configure logging
logger = logging.getLogger(__name__)

# Cache of user's current menu state
user_menu_state: Dict[int, MenuType] = {}

# Handler type definition
CommandHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]

# Comprehensive button mapping
# Format: {button_text: (action_type, action_value)}
# action_type can be: "menu", "command", "message", "function"
BUTTON_ACTIONS = {
    # Main menu buttons
    "💰 Explore Pools": ("menu", MenuType.EXPLORE),
    "👤 My Account": ("menu", MenuType.ACCOUNT),
    "💹 Invest": ("menu", MenuType.INVEST),
    "ℹ️ Help": ("menu", MenuType.HELP),
    
    # Explore menu buttons
    "📊 Pool Information": ("menu", MenuType.POOL_INFO),
    "📈 High APR Pools": ("command", "/info high_apr"),
    "💵 Stable Pools": ("command", "/info stable"),
    "📊 All Pools": ("command", "/info all"),
    "🔍 Search Pool": ("message", "Please enter a token pair to search for (e.g., SOL-USDC)"),
    "🔮 Simulate Investment": ("menu", MenuType.SIMULATE),
    
    # Account menu buttons
    "👛 Wallet": ("menu", MenuType.WALLET),
    "📋 Profile": ("menu", MenuType.PROFILE),
    "🔔 Subscriptions": ("menu", MenuType.SUBSCRIBE),
    
    # Invest menu buttons
    "🧠 Smart Invest": ("command", "/invest smart"),
    "⭐ Top Pools": ("command", "/info top"),
    "💼 My Investments": ("command", "/status"),
    
    # Simulation menu buttons
    "💲 Quick Simulate": ("command", "/simulate 1000"),
    "📊 Custom Simulation": ("message", "Please enter your custom investment amount using /simulate [amount].\nFor example: /simulate 5000"),
    "📑 Simulation History": ("menu", MenuType.SIMULATE),  # Placeholder until implemented
    
    # Help menu buttons
    "📚 Commands": ("command", "/help"),
    "📱 Contact": ("command", "/contact"),
    "🔗 Links": ("command", "/social"),
    
    # FAQ menu buttons
    "💡 About Liquidity Pools": ("command", "/faq liquidity"),
    "💱 About APR": ("command", "/faq apr"),
    "⚠️ About Impermanent Loss": ("command", "/faq impermanent"),
    "💸 About DeFi": ("command", "/faq defi"),
    "🔑 About Wallets": ("command", "/faq wallets"),
    
    # Wallet and profile buttons
    "💳 Wallet Settings": ("command", "/wallet"),
    "👤 Profile Settings": ("command", "/profile"),
    
    # Back buttons (will be handled separately)
    "⬅️ Back to Main Menu": ("special", "back_to_main"),
}

# Determine which menus should use one-time keyboard
ONE_TIME_KEYBOARD_MENUS = {
    MenuType.SIMULATE,
    MenuType.WALLET,
    MenuType.PROFILE,
    MenuType.FAQ,
}


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
    
    # Handle back button navigation
    if button_text.startswith("⬅️ Back to"):
        try:
            # Get current menu with fallback support
            current_menu = await get_current_menu(user_id)
            menu_config = get_menu_config(current_menu)
            
            if menu_config.parent_menu:
                target_menu = menu_config.parent_menu
                await set_menu_state(update, context, target_menu)
                await log_menu_navigation(user_id, current_menu.value, target_menu.value)
                return True
            else:
                # Default to main menu if no parent is specified
                await set_menu_state(update, context, MenuType.MAIN)
                await log_menu_navigation(user_id, current_menu.value, "MAIN")
                return True
        except Exception as e:
            logger.error(f"Error handling back button: {e}")
            # Default to main menu in case of error
            await set_menu_state(update, context, MenuType.MAIN)
            return True
    
    # Look up the button in our comprehensive mapping
    if button_text in BUTTON_ACTIONS:
        action_type, action_value = BUTTON_ACTIONS[button_text]
        
        try:
            if action_type == "menu":
                # Action is to navigate to a menu
                target_menu = action_value
                current_menu = await get_current_menu(user_id)
                await set_menu_state(update, context, target_menu)
                await log_menu_navigation(user_id, current_menu.value, target_menu.value)
                return True
                
            elif action_type == "command":
                # Action is to execute a command
                if update.effective_chat:
                    # Send the command as a regular message
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=action_value
                    )
                    logger.info(f"Executed button command: {action_value}")
                    return True
                    
            elif action_type == "message":
                # Action is to send a message
                if update.effective_chat:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=action_value
                    )
                    logger.info(f"Sent message from button: {button_text}")
                    return True
                    
            elif action_type == "function":
                # For future use - would call a specific handler function
                # This would require registering handler functions
                logger.warning(f"Function action type not implemented yet: {button_text}")
                return False
                
            elif action_type == "special":
                # Special actions like back navigation
                if action_value == "back_to_main":
                    current_menu = await get_current_menu(user_id)
                    await set_menu_state(update, context, MenuType.MAIN)
                    await log_menu_navigation(user_id, current_menu.value, "MAIN")
                    return True
                    
        except Exception as e:
            logger.error(f"Error handling button '{button_text}': {e}")
            # Try to go back to main menu in case of error
            await set_menu_state(update, context, MenuType.MAIN)
            return True
    else:
        # No matching action found for this button text
        logger.warning(f"No action defined for button text: '{button_text}'")
        
    # If we get here, the message wasn't a menu navigation command
    return False


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