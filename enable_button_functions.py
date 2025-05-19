#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to enable functional button responses for the FiLot Telegram bot
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

def update_handle_message_function():
    """Update the handle_message function to properly process button presses"""
    try:
        # Read the bot.py file
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check if we need to update the file
        if "if await handle_menu_navigation(update, context):" in content:
            logger.info("Bot.py already contains the required button handling code")
            return True
        
        # Find the handle_message async def line
        import re
        match = re.search(r'async def handle_message\(update: Update, context: ContextTypes\.DEFAULT_TYPE\) -> None:', content)
        
        if not match:
            logger.error("Could not find handle_message function in bot.py")
            return False
        
        # Find the function body start
        start_pos = match.end()
        
        # Count the indentation at the function body start
        next_line = content[start_pos:].lstrip('\n')
        indentation = len(next_line) - len(next_line.lstrip())
        
        # Create the code to insert
        button_handling_code = """
    # First, check if this is a menu navigation button press
    if await handle_menu_navigation(update, context):
        logger.info("Handled as menu navigation button press")
        return
        
    # Now continue with regular message processing
"""
        
        # Format with the correct indentation
        button_handling_code = button_handling_code.replace('\n    ', '\n' + ' ' * indentation)
        
        # Insert the code right after the function starts and initial try block
        # Find the try statement
        try_match = re.search(r'\n\s*try:\s*\n', content[start_pos:])
        if not try_match:
            logger.error("Could not find try block in handle_message function")
            return False
        
        try_pos = start_pos + try_match.end()
        
        # Update the content
        updated_content = content[:try_pos] + button_handling_code + content[try_pos:]
        
        # Write the updated content back to the file
        with open('bot.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Successfully updated bot.py with button handling code")
        return True
    except Exception as e:
        logger.error(f"Error updating bot.py: {e}")
        return False

def update_button_responses_import():
    """Ensure button_responses is imported in bot.py"""
    try:
        # Read the bot.py file
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check if we need to add the import
        if "import button_responses" in content:
            logger.info("Bot.py already imports button_responses")
            return True
        
        # Find the appropriate place to add the import
        import_section_end = content.find("from keyboard_utils import")
        if import_section_end == -1:
            import_section_end = content.find("# Configure logging")
        
        if import_section_end == -1:
            logger.error("Could not find appropriate place to add import")
            return False
        
        # Add import statement
        import_statement = "import button_responses\n"
        updated_content = content[:import_section_end] + import_statement + content[import_section_end:]
        
        # Write the updated content back to the file
        with open('bot.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Successfully added button_responses import to bot.py")
        return True
    except Exception as e:
        logger.error(f"Error updating imports in bot.py: {e}")
        return False

def main():
    """Main function to enable button functionality"""
    logger.info("Enabling button functions for FiLot Telegram bot")
    
    # Update handle_message function
    if not update_handle_message_function():
        logger.error("Failed to update handle_message function")
        return 1
    
    # Update imports
    if not update_button_responses_import():
        logger.error("Failed to update imports")
        return 1
    
    # Restart the Telegram bot workflow
    logger.info("Restarting Telegram bot workflow...")
    
    # Use subprocess to restart the workflow
    subprocess.run([sys.executable, "-c", 
                   "import replit; replit.restart_workflow('run_telegram_bot')"])
    
    logger.info("Button functions have been enabled successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())