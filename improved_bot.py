#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Improved Telegram bot launcher that ensures button functionality works properly
"""

import os
import sys
import logging
import subprocess
import time
import signal
import atexit

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def stop_existing_processes():
    """Stop any existing bot or Flask processes"""
    try:
        logger.info("Stopping any existing bot processes...")
        subprocess.run("pkill -f 'python main.py' || true", shell=True)
        subprocess.run("pkill -f 'python wsgi.py' || true", shell=True)
        time.sleep(2)  # Give processes time to terminate
    except Exception as e:
        logger.error(f"Error stopping processes: {e}")

def cleanup():
    """Cleanup function for graceful shutdown"""
    logger.info("Performing cleanup...")
    stop_existing_processes()

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    cleanup()
    sys.exit(0)

def integrate_button_handler():
    """
    Integrate enhanced button handler into the bot system
    """
    try:
        # Import the main bot.py module to check contents
        from bot import handle_message
        
        # Modify the bot.py file to include our enhanced handler
        with open('bot.py', 'r') as f:
            bot_code = f.read()
        
        # Check if we need to integrate the enhanced button handler
        if 'from enhanced_button_handler import handle_button_press' not in bot_code:
            logger.info("Integrating enhanced button handler...")
            
            # Find the handle_message function
            with open('bot.py', 'r') as f:
                lines = f.readlines()
                
            # Add import at the top
            new_lines = []
            imports_section = True
            
            for line in lines:
                if imports_section and line.strip() == '':
                    new_lines.append('from enhanced_button_handler import handle_button_press\n')
                    imports_section = False
                new_lines.append(line)
            
            # Write back the modified file
            with open('bot.py', 'w') as f:
                f.writelines(new_lines)
            
            logger.info("Enhanced button handler integrated successfully")
            return True
        else:
            logger.info("Enhanced button handler already integrated")
            return True
    except Exception as e:
        logger.error(f"Error integrating button handler: {e}")
        return False

def run_bot():
    """
    Run the bot with enhanced button functionality
    """
    # Register cleanup handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup)
    
    try:
        # Stop any existing processes
        stop_existing_processes()
        
        # Integrate enhanced button handler
        if not integrate_button_handler():
            logger.error("Failed to integrate button handler, aborting")
            return 1
        
        # Start the bot in a new process
        logger.info("Starting the Telegram bot with enhanced button handling...")
        bot_process = subprocess.Popen([sys.executable, "main.py"])
        
        # Keep running until terminated
        logger.info("Bot started successfully. Press Ctrl+C to stop.")
        bot_process.wait()
        
        return 0
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_bot())