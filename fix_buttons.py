#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Quick fix for button functionality in FiLot Telegram bot
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def update_keyboard_utils():
    """Update keyboard_utils.py to handle button presses correctly"""
    try:
        # Read the current file
        with open('keyboard_utils.py', 'r') as f:
            content = f.readlines()
        
        # Check if the fix is already applied
        for line in content:
            if "# Call the appropriate command based on the button text" in line:
                logger.info("Fix already applied to keyboard_utils.py")
                return True
        
        # Find where to insert our code
        line_to_modify = -1
        for i, line in enumerate(content):
            if "# Handle pool info menu buttons" in line:
                line_to_modify = i
                break
        
        if line_to_modify == -1:
            logger.error("Could not find insertion point in keyboard_utils.py")
            return False
        
        # Create the improved button handling code
        button_command_code = [
            "    # Call the appropriate command based on the button text\n",
            "    button_commands = {\n",
            "        \"📊 Pool Information\": \"/info\",\n",
            "        \"📈 High APR Pools\": \"/info high_apr\",\n", 
            "        \"💵 Stable Pools\": \"/info stable\",\n",
            "        \"📊 All Pools\": \"/info all\",\n",
            "        \"🔍 Search Pool\": \"/search\",\n",
            "        \"🔮 Simulate Investment\": \"/simulate\",\n",
            "        \"💡 About Liquidity Pools\": \"/faq liquidity\",\n",
            "        \"💱 About APR\": \"/faq apr\",\n", 
            "        \"⚠️ About Impermanent Loss\": \"/faq impermanent\",\n",
            "        \"💸 About DeFi\": \"/faq defi\",\n",
            "        \"🔑 About Wallets\": \"/faq wallets\",\n",
            "        \"📚 Commands\": \"/help\",\n",
            "        \"📱 Contact\": \"/contact\",\n",
            "        \"🔗 Links\": \"/social\",\n",
            "        \"🧠 Smart Invest\": \"/invest smart\",\n",
            "        \"⭐ Top Pools\": \"/info top\",\n",
            "        \"💼 My Investments\": \"/status\",\n",
            "        \"🔔 Subscriptions\": \"/subscribe\",\n",
            "        \"👤 Profile Settings\": \"/profile\",\n",
            "        \"💳 Wallet Settings\": \"/wallet\"\n",
            "    }\n",
            "    \n",
            "    if button_text in button_commands:\n",
            "        if update.effective_chat:\n",
            "            cmd = button_commands[button_text]\n",
            "            logger.info(f\"Executing button command: {cmd}\")\n",
            "            await context.bot.send_message(\n",
            "                chat_id=update.effective_chat.id,\n",
            "                text=cmd\n",
            "            )\n",
            "            return True\n",
            "    \n"
        ]
        
        # Insert our code
        content = content[:line_to_modify] + button_command_code + content[line_to_modify:]
        
        # Update the file
        with open('keyboard_utils.py', 'w') as f:
            f.writelines(content)
        
        logger.info("Successfully updated keyboard_utils.py with improved button handling")
        return True
    except Exception as e:
        logger.error(f"Error updating keyboard_utils.py: {e}")
        return False

def update_bot_py():
    """Update bot.py to handle button text commands"""
    try:
        # Read the current file
        with open('bot.py', 'r') as f:
            content = f.read()
        
        # Check if we need to update
        if "# Handle button text that looks like a command" in content:
            logger.info("Fix already applied to bot.py")
            return True
        
        # Find the handle_message function
        import re
        message_func = re.search(r'async def handle_message\([^)]+\):[^\n]*\n', content)
        
        if not message_func:
            logger.error("Could not find handle_message function in bot.py")
            return False
        
        # Find the end of the current menu button handling
        start_pos = message_func.end()
        text_check_pos = content.find("message_text = update.message.text", start_pos)
        
        if text_check_pos == -1:
            logger.error("Could not find message_text assignment in bot.py")
            return False
        
        # Find where to insert our button command handler
        menu_check_end = content.find("# Check if this is a potential menu button but not properly handled", start_pos)
        
        if menu_check_end == -1:
            menu_check_end = content.find("current_menu = get_current_menu(user.id)", start_pos)
        
        if menu_check_end == -1:
            logger.error("Could not find insertion point in bot.py")
            return False
        
        # Insert our button command processing code
        # This ensures that if a user presses a button that should trigger a command, it works
        button_command_code = """
            # Handle button text that looks like a command
            if message_text.startswith('/'):
                # Execute the command directly
                logger.info(f"Processing button text as command: {message_text}")
                entities = [{"type": "bot_command", "offset": 0, "length": message_text.find(' ') if ' ' in message_text else len(message_text)}]
                update.message._entities = entities
                await context.dispatcher.process_update(update)
                return
                
        """
        
        # Get the indentation level
        lines_before = content[:menu_check_end].split('\n')
        if lines_before:
            last_line = lines_before[-1]
            indentation = len(last_line) - len(last_line.lstrip())
            button_command_code = button_command_code.replace('            ', ' ' * indentation)
        
        # Insert our code
        updated_content = content[:menu_check_end] + button_command_code + content[menu_check_end:]
        
        # Write the updated content
        with open('bot.py', 'w') as f:
            f.write(updated_content)
        
        logger.info("Successfully updated bot.py with improved button command handling")
        return True
    except Exception as e:
        logger.error(f"Error updating bot.py: {e}")
        return False

def main():
    """Apply fixes to make buttons function properly"""
    logger.info("Applying fixes for FiLot Telegram bot button functionality")
    
    # Update keyboard_utils.py to handle button presses properly
    if not update_keyboard_utils():
        logger.error("Failed to update keyboard_utils.py")
        return 1
    
    # Update bot.py to handle button text commands
    if not update_bot_py():
        logger.error("Failed to update bot.py")
        return 1
    
    logger.info("All fixes applied successfully! Buttons should now function properly.")
    logger.info("Please restart the bot workflow for the changes to take effect.")
    return 0

if __name__ == "__main__":
    sys.exit(main())