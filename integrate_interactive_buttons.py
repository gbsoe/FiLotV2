#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Integration script for interactive buttons in FiLot Telegram bot
This implements proper database-connected buttons for the Telegram bot
"""

import os
import sys
import logging
import subprocess
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def modify_main_py():
    """
    Modify main.py to add interactive buttons
    """
    try:
        with open('main.py', 'r') as f:
            content = f.readlines()
        
        # Check if already modified
        for line in content:
            if "from interactive_buttons import register_handlers" in line:
                logger.info("main.py already modified for interactive buttons")
                return True
        
        # Find the place to insert the import
        import_index = -1
        application_creation_index = -1
        
        for i, line in enumerate(content):
            if "from telegram.ext import" in line:
                import_index = i + 1
            if "application = Application.builder" in line:
                application_creation_index = i
        
        if import_index == -1 or application_creation_index == -1:
            logger.error("Could not find insertion points in main.py")
            return False
        
        # Add import
        content.insert(import_index, "from interactive_buttons import register_handlers\n")
        
        # Find where to register the handlers
        register_index = -1
        for i, line in enumerate(content[application_creation_index:], application_creation_index):
            if "application.add_handler" in line:
                register_index = i
                break
        
        if register_index == -1:
            # If no handlers found, find end of application creation
            for i, line in enumerate(content[application_creation_index:], application_creation_index):
                if "application.run_polling" in line:
                    register_index = i
                    break
        
        if register_index == -1:
            logger.error("Could not find where to register handlers in main.py")
            return False
        
        # Add registration for interactive buttons
        # Find the indentation level
        indent = ""
        for char in content[register_index]:
            if char.isspace():
                indent += char
            else:
                break
        
        # Add the registration line with proper indentation before starting polling
        register_line = f"{indent}# Register interactive button handlers\n{indent}register_handlers(application)\n"
        content.insert(register_index, register_line)
        
        # Write modified content back to file
        with open('main.py', 'w') as f:
            f.writelines(content)
        
        logger.info("Successfully modified main.py for interactive buttons")
        return True
    except Exception as e:
        logger.error(f"Error modifying main.py: {e}")
        return False

def add_command_handler():
    """
    Add a command handler for interactive menu in bot.py
    """
    try:
        with open('bot.py', 'r') as f:
            content = f.readlines()
        
        # Check if already modified
        for line in content:
            if "async def interactive_menu_command" in line:
                logger.info("bot.py already has interactive menu command")
                return True
        
        # Find the last command function
        last_command_index = -1
        for i, line in enumerate(content):
            if line.startswith("async def") and "_command(" in line:
                last_command_index = i
        
        if last_command_index == -1:
            logger.error("Could not find where to add interactive menu command in bot.py")
            return False
        
        # Find the next function after the last command (where to insert)
        next_function_index = -1
        for i, line in enumerate(content[last_command_index+1:], last_command_index+1):
            if line.startswith("async def") and "handle_" in line:
                next_function_index = i
                break
        
        if next_function_index == -1:
            logger.error("Could not find where to insert interactive menu command")
            return False
        
        # Create the interactive menu command function
        interactive_command = """
async def interactive_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the interactive menu when the command /interactive is issued."""
    try:
        user = update.effective_user
        
        # Import interactive buttons functions
        from interactive_buttons import show_main_menu
        
        # Log the activity
        from app import app
        with app.app_context():
            db_utils.log_user_activity(user.id, "interactive_menu_command")
        
        # Show the interactive main menu
        await show_main_menu(update, context)
        
        logger.info(f"Showed interactive menu to user {user.id}")
    except Exception as e:
        logger.error(f"Error in interactive menu command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while showing the interactive menu. Please try again later."
        )

"""
        
        # Insert the command
        content.insert(next_function_index, interactive_command)
        
        # Find where to register the command
        register_index = -1
        for i, line in enumerate(content):
            if "def create_application():" in line:
                register_index = i
                break
        
        if register_index == -1:
            logger.error("Could not find create_application function")
            return False
        
        # Find the section where handlers are added
        handler_section = -1
        for i, line in enumerate(content[register_index:], register_index):
            if "application.add_handler" in line:
                handler_section = i
                break
        
        if handler_section == -1:
            logger.error("Could not find handler section in create_application")
            return False
        
        # Find the last handler
        last_handler = -1
        first_handler = handler_section
        for i, line in enumerate(content[handler_section:], handler_section):
            if "application.add_handler" in line:
                last_handler = i
            elif "application.add_error_handler" in line:
                break
        
        if last_handler == -1:
            logger.error("Could not find last handler")
            return False
        
        # Get the indentation
        indent = ""
        for char in content[last_handler]:
            if char.isspace():
                indent += char
            else:
                break
        
        # Create the handler registration
        handler_registration = f"{indent}application.add_handler(CommandHandler('interactive', interactive_menu_command))\n"
        
        # Insert the handler
        content.insert(last_handler + 1, handler_registration)
        
        # Write modified content back to file
        with open('bot.py', 'w') as f:
            f.writelines(content)
        
        logger.info("Successfully added interactive menu command to bot.py")
        return True
    except Exception as e:
        logger.error(f"Error adding interactive menu command: {e}")
        return False

def main():
    """
    Main function to integrate interactive buttons
    """
    logger.info("Integrating interactive buttons into FiLot Telegram bot")
    
    # Modify main.py to add interactive buttons
    if not modify_main_py():
        logger.error("Failed to modify main.py")
        return 1
    
    # Add command handler for interactive menu
    if not add_command_handler():
        logger.error("Failed to add command handler")
        return 1
    
    logger.info("Interactive buttons successfully integrated!")
    logger.info("Restart the bot workflow to use the new features")
    logger.info("Users can now access the interactive menu with the /interactive command")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())