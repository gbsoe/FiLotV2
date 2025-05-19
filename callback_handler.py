#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Callback handler for FiLot Telegram bot
Processes callback queries from inline keyboards and button interactions
"""

import logging
from typing import Dict, Any, Optional, Callable, Awaitable, Union
import json

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import db_utils
from menus import MenuType, get_menu_config
from keyboard_utils import set_menu_state, get_current_menu

# Configure logging
logger = logging.getLogger(__name__)

# Type definitions for callback handlers
CallbackHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE, Union[str, Dict[str, Any]]], Awaitable[None]]

# Registry of callback handlers
callback_handlers: Dict[str, CallbackHandler] = {}


def register_callback(prefix: str):
    """
    Decorator to register a callback handler function.
    
    Args:
        prefix: The callback data prefix this handler should respond to
    """
    def decorator(func: CallbackHandler):
        callback_handlers[prefix] = func
        return func
    return decorator


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Main handler for callback queries from inline keyboards.
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    if not update.callback_query or not update.effective_user:
        return
    
    query = update.callback_query
    
    try:
        # Parse the callback data
        callback_data = query.data
        if not callback_data:
            logger.warning("Received callback query with no data")
            await query.answer(text="Invalid button data")
            return
        
        # Log the callback for debugging
        logger.info(f"Received callback: {callback_data} from user {update.effective_user.id}")
        
        # Find appropriate handler based on prefix
        handler = None
        handler_prefix = ""
        
        for prefix, callback_handler in callback_handlers.items():
            if callback_data.startswith(prefix):
                handler = callback_handler
                handler_prefix = prefix
                break
        
        if handler:
            # Extract the parameters from callback_data
            params_str = callback_data[len(handler_prefix):]
            
            try:
                # Try to parse as JSON if it's complex data
                if params_str and params_str.startswith(':'):
                    params_json = params_str[1:]
                    params_dict = json.loads(params_json)
                    # Call the handler with dictionary params
                    await handler(update, context, params_dict)
                else:
                    # Call the handler with string params
                    await handler(update, context, params_str)
            except json.JSONDecodeError:
                # If not valid JSON, pass as string
                await handler(update, context, params_str)
        else:
            # No handler found
            logger.warning(f"No handler found for callback: {callback_data}")
            await query.answer(text="This button is not yet implemented.")
    
    except Exception as e:
        logger.error(f"Error handling callback query: {e}", exc_info=True)
        if query:
            await query.answer(text="An error occurred while processing your request.")


# --- Main menu callbacks ---

@register_callback("main:")
async def handle_main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, params: Any) -> None:
    """
    Handle callbacks from the main menu.
    
    Args:
        update: Telegram update object
        context: Context object for the update
        params: Additional parameters from the callback
    """
    if not update.callback_query:
        return
        
    query = update.callback_query
    await query.answer()
    
    if params == "explore":
        await set_menu_state(update, context, MenuType.EXPLORE)
    elif params == "account":
        await set_menu_state(update, context, MenuType.ACCOUNT)
    elif params == "invest":
        await set_menu_state(update, context, MenuType.INVEST)
    elif params == "help":
        await set_menu_state(update, context, MenuType.HELP)
    else:
        logger.warning(f"Unknown main menu param: {params}")


# --- Pool information callbacks ---

@register_callback("pool:")
async def handle_pool_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, params: Any) -> None:
    """
    Handle callbacks related to pool information.
    
    Args:
        update: Telegram update object
        context: Context object for the update
        params: Additional parameters from the callback
    """
    query = update.callback_query
    await query.answer()
    
    if isinstance(params, dict):
        action = params.get("action")
        pool_id = params.get("id")
        
        if action == "view" and pool_id:
            # Logic to display specific pool information
            await query.edit_message_text(
                text=f"Loading information for pool {pool_id}...",
                reply_markup=None
            )
            # Here you would fetch and display the actual pool information
        
        elif action == "list":
            # Logic to list available pools
            pool_type = params.get("type", "all")
            # Here you would fetch and display pools based on type
            await query.edit_message_text(
                text=f"Loading {pool_type} pools...",
                reply_markup=None
            )
    else:
        logger.warning(f"Invalid pool callback params: {params}")


# --- Wallet callbacks ---

@register_callback("wallet:")
async def handle_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, params: Any) -> None:
    """
    Handle callbacks related to wallet management.
    
    Args:
        update: Telegram update object
        context: Context object for the update
        params: Additional parameters from the callback
    """
    query = update.callback_query
    await query.answer()
    
    if isinstance(params, dict):
        action = params.get("action")
        
        if action == "connect":
            # Logic to initiate wallet connection
            await query.edit_message_text(
                text="To connect your wallet, please use the /walletconnect command.",
                reply_markup=None
            )
        
        elif action == "balance":
            # Logic to check wallet balance
            await query.edit_message_text(
                text="Fetching your wallet balance...",
                reply_markup=None
            )
            # Here you would fetch and display the actual wallet balance
        
        elif action == "disconnect":
            # Logic to disconnect wallet
            await query.edit_message_text(
                text="Disconnecting your wallet...",
                reply_markup=None
            )
            # Here you would handle the wallet disconnection
    else:
        logger.warning(f"Invalid wallet callback params: {params}")


# --- Navigation callbacks ---

@register_callback("nav:")
async def handle_navigation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, params: Any) -> None:
    """
    Handle navigation callbacks for moving between menus.
    
    Args:
        update: Telegram update object
        context: Context object for the update
        params: Additional parameters from the callback
    """
    query = update.callback_query
    await query.answer()
    
    if params == "back":
        # Get current menu and navigate to its parent
        user_id = update.effective_user.id
        current_menu = get_current_menu(user_id)
        menu_config = get_menu_config(current_menu)
        
        if menu_config.parent_menu:
            await set_menu_state(update, context, menu_config.parent_menu)
        else:
            # Default to main menu if no parent is specified
            await set_menu_state(update, context, MenuType.MAIN)
    
    elif params == "main":
        # Go directly to main menu
        await set_menu_state(update, context, MenuType.MAIN)
    
    elif params.startswith("to_"):
        # Navigate to a specific menu
        try:
            menu_name = params[3:].upper()  # Extract menu name and convert to uppercase
            target_menu = MenuType[menu_name]
            await set_menu_state(update, context, target_menu)
        except (KeyError, ValueError):
            logger.warning(f"Invalid menu specified in navigation: {params}")
            await query.edit_message_text(
                text="Sorry, that menu option is not available.",
                reply_markup=None
            )
    else:
        logger.warning(f"Unknown navigation param: {params}")


# --- Create inline keyboard utilities ---

def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for the main menu.
    
    Returns:
        InlineKeyboardMarkup with main menu buttons
    """
    keyboard = [
        [
            InlineKeyboardButton("💰 Explore", callback_data="main:explore"),
            InlineKeyboardButton("👤 Account", callback_data="main:account")
        ],
        [
            InlineKeyboardButton("💹 Invest", callback_data="main:invest"),
            InlineKeyboardButton("ℹ️ Help", callback_data="main:help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_back_button(menu_type: MenuType = None) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with a back button.
    
    Args:
        menu_type: Optional target menu for the back button
        
    Returns:
        InlineKeyboardMarkup with a back button
    """
    if menu_type:
        callback_data = f"nav:to_{menu_type.value}"
    else:
        callback_data = "nav:back"
    
    keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)