#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix button functionality in FiLot Telegram bot
This adds interactive buttons that perform real database operations
"""

import os
import sys
import logging
import re
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def add_interactive_command():
    """Add an interactive menu command to main.py."""
    main_file = Path("main.py")
    
    if not main_file.exists():
        logger.error("main.py not found")
        return False
    
    # Read the current content
    with open(main_file, 'r') as f:
        content = f.read()
    
    # Check if already has interactive command
    if '"interactive": interactive_menu_command' in content:
        logger.info("Interactive command already in main.py")
        return True
    
    # Create interactive_menu_command in bot.py
    bot_file = Path("bot.py")
    if not bot_file.exists():
        logger.error("bot.py not found")
        return False
    
    with open(bot_file, 'r') as f:
        bot_content = f.read()
    
    # Check if already has interactive menu command
    if "async def interactive_menu_command" in bot_content:
        logger.info("interactive_menu_command already in bot.py")
    else:
        # Find a good position to add our function - after the last command function
        command_pattern = r'async def (\w+)_command\(update: Update, context: .*?\):'
        command_matches = list(re.finditer(command_pattern, bot_content))
        
        if not command_matches:
            logger.error("Could not find command functions in bot.py")
            return False
        
        # Get the position after the last command function
        last_position = command_matches[-1].start()
        
        # Find the end of this function to insert after it
        function_body_start = bot_content.find(":", last_position) + 1
        next_function_start = bot_content.find("async def", function_body_start)
        
        if next_function_start == -1:
            logger.error("Could not determine where to add new function")
            return False
        
        # Prepare the interactive menu command function
        interactive_function = """

async def interactive_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Show the interactive menu with buttons that perform real database operations
    try:
        user = update.effective_user
        logger.info(f"User {user.id} requested interactive menu")
        
        # Define inline keyboard with buttons that perform real database operations
        keyboard = [
            [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
            [InlineKeyboardButton("📈 View High APR Pools", callback_data="high_apr")],
            [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
            [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
        ]
        
        await update.message.reply_markdown(
            f"*Welcome to FiLot Interactive Menu, {user.first_name}!*\\n\\n"
            "These buttons perform real database operations.\\n"
            "Click any option to retrieve live data:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in interactive menu command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )

"""
        
        # Insert the function
        new_bot_content = bot_content[:next_function_start] + interactive_function + bot_content[next_function_start:]
        
        # Write the updated content
        with open(bot_file, 'w') as f:
            f.write(new_bot_content)
        
        logger.info("Added interactive_menu_command to bot.py")
    
    # Add to command_handlers in main.py
    command_handlers_pattern = r'command_handlers\s*=\s*{'
    match = re.search(command_handlers_pattern, content)
    
    if not match:
        logger.error("Could not find command_handlers dictionary in main.py")
        return False
    
    # Find position to insert new command - after the last command handler
    last_command_pos = content.find("}", match.end())
    
    if last_command_pos == -1:
        logger.error("Could not find end of command_handlers dictionary")
        return False
    
    # Insert our new command handler
    updated_content = (
        content[:last_command_pos] + 
        '            "interactive": interactive_menu_command,\n' + 
        content[last_command_pos:]
    )
    
    # Update import section to include interactive_menu_command
    import_section = r'from bot import \(\s*.*?\s*\)'
    if re.search(import_section, updated_content, re.DOTALL):
        updated_content = re.sub(
            import_section,
            lambda m: m.group(0).replace(
                "profile_command", 
                "profile_command, interactive_menu_command"
            ),
            updated_content,
            flags=re.DOTALL
        )
    
    # Write the updated content
    with open(main_file, 'w') as f:
        f.write(updated_content)
    
    logger.info("Added interactive command to main.py")
    return True


def add_callback_handler():
    """Enhance callback_query handling to support interactive buttons."""
    bot_file = Path("bot.py")
    
    if not bot_file.exists():
        logger.error("bot.py not found")
        return False
    
    # Read the current content
    with open(bot_file, 'r') as f:
        content = f.read()
    
    # Find the callback query handler
    callback_handler_pattern = r'async def handle_callback_query\(update: Update, context: .*?\):'
    match = re.search(callback_handler_pattern, content)
    
    if not match:
        logger.error("Could not find handle_callback_query function in bot.py")
        return False
    
    # Check if already enhanced
    if "with app.app_context():" in content[match.start():match.start() + 2000]:
        logger.info("Callback handler already enhanced")
        return True
    
    # Find the function body
    function_start = content.find(":", match.end()) + 1
    next_function_start = content.find("async def", function_start)
    
    if next_function_start == -1:
        logger.error("Could not determine end of callback handler function")
        return False
    
    function_body = content[function_start:next_function_start].strip()
    
    # Create enhanced callback handler
    enhanced_handler = """
    """Handles callback queries from button presses."""
    query = update.callback_query
    
    try:
        # Log the callback
        logger.info(f"Received callback query: {query.data}")
        await query.answer()
        
        # Handle different button actions
        if query.data == "pools":
            # Show pool data from database
            with app.app_context():
                try:
                    from models import Pool
                    
                    # Get pools from database
                    pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(5).all()
                    
                    if pools:
                        # Format message with pool data
                        message = "*📊 Liquidity Pool Data*\\n\\n"
                        
                        for i, pool in enumerate(pools):
                            message += (
                                f"{i+1}. *{pool.token_a_symbol}-{pool.token_b_symbol}*\\n"
                                f"   • APR: {pool.apr_24h:.2f}%\\n"
                                f"   • TVL: ${pool.tvl:,.2f}\\n\\n"
                            )
                        
                        # Add back button
                        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
                        
                        await query.edit_message_text(
                            message,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode="Markdown"
                        )
                    else:
                        await query.edit_message_text(
                            "*No Pool Data Available*\\n\\n"
                            "We couldn't find any pool data in the database.",
                            parse_mode="Markdown",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                            ]])
                        )
                except Exception as e:
                    logger.error(f"Error retrieving pool data: {e}")
                    await query.edit_message_text(
                        "Sorry, an error occurred while retrieving pool data.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                        ]])
                    )
        
        elif query.data == "high_apr":
            # Show high APR pools from database
            with app.app_context():
                try:
                    from models import Pool
                    
                    # Get high APR pools from database
                    high_apr_pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(3).all()
                    
                    if high_apr_pools:
                        # Format message with high APR pool data
                        message = "*📈 Top High APR Pools*\\n\\n"
                        
                        for i, pool in enumerate(high_apr_pools):
                            message += (
                                f"{i+1}. *{pool.token_a_symbol}-{pool.token_b_symbol}*\\n"
                                f"   • APR: {pool.apr_24h:.2f}%\\n"
                                f"   • TVL: ${pool.tvl:,.2f}\\n\\n"
                            )
                        
                        # Add back button
                        keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
                        
                        await query.edit_message_text(
                            message,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode="Markdown"
                        )
                    else:
                        await query.edit_message_text(
                            "*No High APR Pool Data Available*\\n\\n"
                            "We couldn't find any high APR pool data in the database.",
                            parse_mode="Markdown",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                            ]])
                        )
                except Exception as e:
                    logger.error(f"Error retrieving high APR pools: {e}")
                    await query.edit_message_text(
                        "Sorry, an error occurred while retrieving high APR pool data.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                        ]])
                    )
        
        elif query.data == "profile":
            # Show user profile from database
            with app.app_context():
                try:
                    from models import User
                    
                    user_id = update.effective_user.id
                    user = User.query.filter_by(id=user_id).first()
                    
                    if user:
                        # Format message with user profile data
                        message = (
                            f"*👤 Your Profile*\\n\\n"
                            f"• *Username:* {user.username or 'Not set'}\\n"
                            f"• *Risk Profile:* {user.risk_profile.capitalize()}\\n"
                            f"• *Investment Horizon:* {user.investment_horizon.capitalize()}\\n"
                            f"• *Investment Goals:* {user.investment_goals or 'Not specified'}\\n"
                            f"• *Subscribed to Updates:* {'Yes' if user.is_subscribed else 'No'}\\n"
                            f"• *Account Created:* {user.created_at.strftime('%Y-%m-%d')}"
                        )
                    else:
                        # Create new user profile
                        user = User(
                            id=user_id,
                            username=update.effective_user.username,
                            first_name=update.effective_user.first_name,
                            last_name=update.effective_user.last_name,
                            risk_profile="moderate",
                            investment_horizon="medium"
                        )
                        from models import db
                        db.session.add(user)
                        db.session.commit()
                        
                        message = (
                            f"*👤 Your Profile (New User)*\\n\\n"
                            f"• *Username:* {update.effective_user.username or 'Not set'}\\n"
                            f"• *Risk Profile:* Moderate (default)\\n"
                            f"• *Investment Horizon:* Medium (default)\\n"
                            f"• *Investment Goals:* Not specified\\n"
                            f"• *Subscribed to Updates:* No\\n\\n"
                            f"Your profile has been created in our database."
                        )
                    
                    # Add back button
                    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error retrieving user profile: {e}")
                    await query.edit_message_text(
                        "Sorry, an error occurred while retrieving your profile data.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")
                        ]])
                    )
        
        elif query.data == "faq":
            # Show FAQ topics
            message = (
                "*❓ Frequently Asked Questions*\\n\\n"
                "Choose a topic to learn more:\\n\\n"
                "• *Liquidity Pools:* What they are and how they work\\n"
                "• *APR:* Understanding Annual Percentage Rate\\n"
                "• *Impermanent Loss:* What it is and how to minimize it\\n"
                "• *Wallets:* How to connect and use wallets securely"
            )
            
            # Add back button
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back_to_menu")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        elif query.data == "back_to_menu":
            # Return to main menu
            keyboard = [
                [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
                [InlineKeyboardButton("📈 View High APR Pools", callback_data="high_apr")],
                [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
                [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
            ]
            
            await query.edit_message_text(
                f"*FiLot Interactive Menu*\\n\\n"
                "These buttons perform real database operations.\\n"
                "Click any option to retrieve live data:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        
        # Handle existing callback operations
        else:
"""
    
    # Combine with the existing function body
    new_function_body = enhanced_handler + function_body
    
    # Create complete updated function
    updated_function = content[match.start():function_start] + new_function_body
    
    # Update the bot.py file
    updated_content = content[:match.start()] + updated_function + content[next_function_start:]
    
    # Add import for app
    if "from app import app" not in updated_content:
        updated_content = updated_content.replace(
            "from telegram.ext import", 
            "from app import app\nfrom telegram.ext import"
        )
    
    # Save the updated file
    with open(bot_file, 'w') as f:
        f.write(updated_content)
    
    logger.info("Enhanced callback handler in bot.py")
    return True


def main():
    """Main function to fix button functionality."""
    logger.info("FiLot Telegram Bot - Fixing button functionality")
    
    # Step 1: Add interactive menu command
    if not add_interactive_command():
        logger.error("Failed to add interactive menu command")
        return 1
    
    # Step 2: Enhance callback handler
    if not add_callback_handler():
        logger.error("Failed to enhance callback handler")
        return 1
    
    logger.info("✅ Successfully fixed button functionality")
    logger.info("The bot now has interactive buttons that perform real database operations")
    logger.info("Users can access the interactive menu with the /interactive command")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())