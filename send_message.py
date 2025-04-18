#!/usr/bin/env python3
import logging
import requests
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text):
    """Send a message to a Telegram chat."""
    bot_token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_TOKEN secret not set")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        logger.info("Message sent successfully")
        return True
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python send_message.py <chat_id> <message>")
        sys.exit(1)
        
    chat_id = sys.argv[1]
    message = sys.argv[2]
    
    success = send_telegram_message(chat_id, message)
    sys.exit(0 if success else 1)
