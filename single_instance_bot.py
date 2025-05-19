#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Single-instance Telegram bot launcher with reliable button handling
"""

import os
import sys
import logging
import fcntl
import time
import requests
import signal
import atexit
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

class BotLauncher:
    """Ensures only one instance of the bot runs and buttons work correctly"""
    
    def __init__(self):
        self.lock_file = "/tmp/filot_bot.lock"
        self.lock_fd = None
        self.bot_process = None
        
        # Register cleanup handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        atexit.register(self._cleanup)
    
    def _acquire_lock(self):
        """Acquire an exclusive file lock to ensure single instance"""
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.info("Lock acquired, we are the only instance")
            return True
        except IOError:
            logger.error("Another instance is already running")
            return False
    
    def _release_lock(self):
        """Release the file lock"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
                logger.info("Lock released")
            except IOError as e:
                logger.error(f"Error releasing lock: {e}")
    
    def _delete_webhook(self):
        """Delete any existing webhook to ensure getUpdates works properly"""
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not found in environment")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{token}/deleteWebhook?drop_pending_updates=true"
            response = requests.get(url, timeout=10)
            data = response.json()
            logger.info(f"Webhook deletion result: {data}")
            return data.get('ok', False)
        except Exception as e:
            logger.error(f"Error deleting webhook: {e}")
            return False
    
    def _cleanup(self):
        """Perform cleanup operations"""
        logger.info("Performing cleanup...")
        
        # Terminate any running bot process
        if self.bot_process and self.bot_process.poll() is None:
            try:
                logger.info("Terminating bot process...")
                self.bot_process.terminate()
                # Give it 5 seconds to terminate gracefully
                for i in range(5):
                    if self.bot_process.poll() is not None:
                        break
                    time.sleep(1)
                    
                # If still running, force kill
                if self.bot_process.poll() is None:
                    logger.info("Forcing bot process to exit...")
                    self.bot_process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
        
        # Release lock
        self._release_lock()
    
    def _handle_signal(self, signum, frame):
        """Handle termination signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self._cleanup()
        sys.exit(0)
    
    def launch(self):
        """Launch the bot in single-instance mode"""
        # First, check if we can acquire the lock
        if not self._acquire_lock():
            logger.error("Cannot acquire lock, exiting")
            return 1
        
        # Delete any existing webhook
        self._delete_webhook()
        
        # Clear any previous instances that might be waiting for updates
        self._kill_previous_instances()
        
        # Set environment variables to enable proper button handling
        os.environ['USE_DATABASE_FALLBACK'] = 'False'  # Force using the database
        os.environ['ENABLE_BUTTON_FUNCTIONS'] = 'True'  # Enable button functionality

        # Launch the bot process
        try:
            logger.info("Starting bot process...")
            
            # Start with a database check to verify connectivity
            self._verify_database_connection()
            
            # Start the bot in a separate process
            self.bot_process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Monitor the bot process
            self._monitor_process()
            
            return 0
        except Exception as e:
            logger.error(f"Error launching bot: {e}")
            return 1
    
    def _kill_previous_instances(self):
        """Kill any previous bot instances that might be running"""
        try:
            # Find and kill any Python processes running main.py
            subprocess.run("pkill -f 'python main.py'", shell=True)
            time.sleep(2)  # Give them time to exit
        except Exception as e:
            logger.error(f"Error killing previous instances: {e}")
    
    def _verify_database_connection(self):
        """Verify database connection to ensure buttons will work"""
        try:
            # Create a small script to test database connection
            with open('_test_db.py', 'w') as f:
                f.write("""
import os
from sqlalchemy import create_engine
from sqlalchemy.sql import text

try:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        exit(1)
        
    engine = create_engine(db_url)
    conn = engine.connect()
    result = conn.execute(text("SELECT 1"))
    print(f"Database connection successful: {result.fetchone()}")
    conn.close()
    exit(0)
except Exception as e:
    print(f"Database connection error: {e}")
    exit(1)
""")

            # Run the test script
            result = subprocess.run([sys.executable, '_test_db.py'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Database connection failed: {result.stdout or result.stderr}")
                raise Exception("Database connection failed")
            else:
                logger.info(f"Database connection verified: {result.stdout.strip()}")
            
            # Clean up
            os.unlink('_test_db.py')
        except Exception as e:
            logger.error(f"Database verification error: {e}")
            raise
    
    def _monitor_process(self):
        """Monitor the bot process and log its output"""
        logger.info("Monitoring bot process...")
        
        if not self.bot_process:
            logger.error("No bot process to monitor")
            return
        
        try:
            # Read and log output
            for line in self.bot_process.stdout:
                line = line.strip()
                if line:
                    logger.info(f"Bot: {line}")
            
            # Wait for the process to complete
            return_code = self.bot_process.wait()
            logger.info(f"Bot process exited with code {return_code}")
            
            # If the process died unexpectedly, restart it
            if return_code != 0:
                logger.warning("Bot process died, restarting...")
                time.sleep(5)  # Wait a bit before restarting
                self.launch()
            
        except Exception as e:
            logger.error(f"Error monitoring process: {e}")

if __name__ == "__main__":
    launcher = BotLauncher()
    sys.exit(launcher.launch())