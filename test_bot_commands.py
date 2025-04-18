#!/usr/bin/env python3
import logging
import requests
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_bot_updates():
    """Get bot updates."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data["ok"] and data["result"]:
            logger.info(f"Got {len(data['result'])} updates")
            return data["result"]
        return []
    except Exception as e:
        logger.error(f"Error getting updates: {e}")
        return []

if __name__ == "__main__":
    logger.info("Checking for updates every 5 seconds for 30 seconds...")
    start_time = time.time()
    while time.time() - start_time < 30:
        updates = get_bot_updates()
        for update in updates:
            if "message" in update and "text" in update["message"]:
                logger.info(f"Message: {update['message']['text']}")
        time.sleep(5)
