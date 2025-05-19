#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Single-instance bot runner that prevents conflicts
"""

import os
import sys
import time
import logging
import requests
import sqlite3
import threading
import signal
import atexit
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

class BotInstanceManager:
    """Manages single-instance bot execution with proper locking"""
    
    def __init__(self):
        self.lock_file = "bot_lock.db"
        self.connection = None
        self.locked = False
        self.terminate_flag = False
        
        # Create the lock database if it doesn't exist
        self._init_lock_db()
        
        # Set up cleanup handlers for proper termination
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)
        atexit.register(self._cleanup)
    
    def _init_lock_db(self):
        """Initialize the lock database"""
        conn = sqlite3.connect(self.lock_file)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_lock (
            id INTEGER PRIMARY KEY,
            pid INTEGER NOT NULL,
            timestamp INTEGER NOT NULL
        )
        ''')
        conn.commit()
        conn.close()
    
    def _attempt_lock(self):
        """Try to acquire the lock"""
        try:
            self.connection = sqlite3.connect(self.lock_file, timeout=10)
            cursor = self.connection.cursor()
            
            # Check if there's an existing lock
            cursor.execute("SELECT pid, timestamp FROM bot_lock LIMIT 1")
            result = cursor.fetchone()
            
            current_time = int(time.time())
            current_pid = os.getpid()
            
            if result:
                pid, timestamp = result
                
                # Check if the process is still running
                if self._is_process_running(pid):
                    # Lock is valid and process is running
                    logger.info(f"Another bot instance is already running (PID: {pid})")
                    return False
                
                # Process not running or lock too old, try to acquire
                logger.info(f"Previous lock found (PID: {pid}) but process is not running. Taking over.")
                cursor.execute("DELETE FROM bot_lock")
            
            # Create new lock
            cursor.execute("INSERT INTO bot_lock (pid, timestamp) VALUES (?, ?)", 
                          (current_pid, current_time))
            self.connection.commit()
            self.locked = True
            logger.info(f"Lock acquired by this process (PID: {current_pid})")
            return True
        
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def _is_process_running(self, pid):
        """Check if a process with given PID is running"""
        try:
            # POSIX-compliant way to check if process exists
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    
    def _release_lock(self):
        """Release the lock if we have it"""
        if self.locked and self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute("DELETE FROM bot_lock WHERE pid = ?", (os.getpid(),))
                self.connection.commit()
                self.locked = False
                logger.info("Lock released")
            except sqlite3.Error as e:
                logger.error(f"Error releasing lock: {e}")
            finally:
                self.connection.close()
                self.connection = None
    
    def _cleanup(self):
        """Clean up resources on exit"""
        logger.info("Cleaning up resources")
        self._release_lock()
    
    def _handle_exit(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.terminate_flag = True
        self._cleanup()
        sys.exit(0)
    
    def _delete_telegram_webhook(self):
        """Ensure no webhook is active for the bot"""
        if not TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment variables")
            return False
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
        try:
            response = requests.get(url)
            result = response.json()
            logger.info(f"Webhook deletion result: {result}")
            return result.get('ok', False)
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    def run_bot(self):
        """Run the bot with proper locking and conflict prevention"""
        if not self._attempt_lock():
            logger.error("Could not acquire lock, exiting")
            return
        
        try:
            # Delete any existing webhook to ensure polling works
            self._delete_telegram_webhook()
            
            # Import here to avoid circular imports
            from app import app, init_app  # Import the Flask app
            
            # Initialize the Flask app
            init_thread = threading.Thread(target=init_app)
            init_thread.daemon = True
            init_thread.start()
            
            # Keep the main thread alive
            logger.info("Bot started successfully. Press Ctrl+C to exit.")
            while not self.terminate_flag:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            traceback.print_exc()
        finally:
            self._cleanup()

if __name__ == "__main__":
    manager = BotInstanceManager()
    manager.run_bot()