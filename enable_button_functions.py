#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to enable fully interactive button functionality for FiLot Telegram bot
This integrates enhanced_button_handler.py with the main bot code
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def modify_main_file():
    """
    Modify main.py to integrate interactive button functionality
    """
    main_file = Path("main.py")
    
    if not main_file.exists():
        logger.error("main.py not found")
        return False
    
    # Read the current content
    content = main_file.read_text()
    
    # Check if already integrated
    if "from enhanced_button_handler import register_handlers" in content:
        logger.info("Enhanced button functionality already integrated")
        return True
    
    # Add import for enhanced button handler
    import_line = "from enhanced_button_handler import register_handlers"
    
    # Find appropriate location to add the import
    import_section_end = content.find("# Initialize the bot")
    if import_section_end == -1:
        import_section_end = content.find("def create_application")
    
    if import_section_end == -1:
        logger.error("Could not find appropriate import location")
        return False
    
    # Split content
    first_part = content[:import_section_end]
    second_part = content[import_section_end:]
    
    # Add import
    new_content = first_part + import_line + "\n\n" + second_part
    
    # Find where to register handlers
    handler_registration = "    # Register enhanced interactive button handlers\n    register_handlers(application)\n"
    
    # Look for application.add_handler or run_polling section
    if "def create_application" in new_content:
        # Find the end of handler registration in create_application function
        create_app_start = new_content.find("def create_application")
        create_app_end = new_content.find("return application", create_app_start)
        
        if create_app_end == -1:
            logger.error("Could not find handler registration location")
            return False
        
        # Split content again
        first_part = new_content[:create_app_end]
        second_part = new_content[create_app_end:]
        
        # Add handler registration
        new_content = first_part + handler_registration + second_part
    else:
        # Direct call to add_handler in the main script
        run_polling_pos = new_content.find("application.run_polling")
        
        if run_polling_pos == -1:
            logger.error("Could not find run_polling location")
            return False
        
        # Find the line beginning before run_polling
        line_start = new_content.rfind("\n", 0, run_polling_pos) + 1
        
        # Split content again
        first_part = new_content[:line_start]
        second_part = new_content[line_start:]
        
        # Add handler registration
        new_content = first_part + handler_registration + second_part
    
    # Write back to file
    main_file.write_text(new_content)
    logger.info("Successfully integrated enhanced button functionality")
    
    return True

def main():
    """
    Main function to enable interactive button functionality
    """
    logger.info("Enabling fully interactive button functionality for FiLot Telegram bot")
    
    if modify_main_file():
        logger.info("✅ Integration successful")
        logger.info("The bot now has fully interactive buttons that perform real database operations")
        logger.info("Users can access the interactive menu with the /interactive command")
        return 0
    else:
        logger.error("❌ Integration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())