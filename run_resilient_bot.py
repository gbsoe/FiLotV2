#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Resilient Telegram bot runner for FiLot
Ensures the bot works properly even when the database is not available
"""

import os
import sys
import time
import signal
import logging
import fcntl
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
LOCK_FILE = 'bot_instance.lock'
POOL_DATA_CACHE_FILE = "pool_data_test_results.json"

def acquire_lock():
    """Acquire an exclusive lock to ensure only one bot instance runs."""
    try:
        lock_fd = open(LOCK_FILE, 'w')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
        logger.info(f"Acquired exclusive bot lock (PID: {os.getpid()})")
        return lock_fd
    except IOError:
        logger.warning("Another bot instance is already running (could not acquire lock)")
        return None

def release_lock(lock_fd):
    """Release the exclusive lock."""
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        try:
            os.unlink(LOCK_FILE)
        except:
            pass
        logger.info("Released exclusive bot lock")

def kill_competing_bots():
    """Kill any competing bot processes."""
    import psutil
    
    current_pid = os.getpid()
    terminated_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip our own process
            if proc.pid == current_pid:
                continue
                
            # Check if this is another bot process
            cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else ''
            if (proc.name() == 'python' and 
                ('main.py' in cmdline or 'run_telegram_bot' in cmdline)):
                logger.info(f"Terminating competing bot process: {proc.pid}")
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                    terminated_count += 1
                except Exception as e:
                    logger.error(f"Error terminating process: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    logger.info(f"Terminated {terminated_count} competing bot processes")
    
    # Give the terminated processes time to exit
    if terminated_count > 0:
        time.sleep(2)
    
    return terminated_count

def ensure_cache_files():
    """Ensure all required cache files exist."""
    # Create empty pool data cache file if it doesn't exist
    if not os.path.exists(POOL_DATA_CACHE_FILE):
        with open(POOL_DATA_CACHE_FILE, 'w') as f:
            f.write('[]')
        logger.info(f"Created empty pool data cache file: {POOL_DATA_CACHE_FILE}")
    
    # Import and initialize all fallback modules
    try:
        import db_fallback
        logger.info("Initialized db_fallback module")
    except ImportError:
        logger.warning("Could not import db_fallback module")
    
    try:
        import db_fallback_enhanced
        logger.info("Initialized enhanced fallback systems")
    except ImportError:
        logger.warning("Could not import enhanced fallback module")

def handle_signals():
    """Set up signal handlers."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def configure_environment():
    """Configure environment variables for resilient operation."""
    # Set a flag to indicate we're running in resilient mode
    os.environ['FILOT_RESILIENT_MODE'] = 'true'
    
    # Check if database URL is set
    if not os.environ.get('DATABASE_URL'):
        logger.warning("DATABASE_URL not set, using memory-only mode")
        
    # Configure fallback message for database connection errors
    os.environ['DB_FALLBACK_MESSAGE'] = 'Database connection is currently unavailable. Using memory-based fallback systems.'
    
    logger.info("Environment configured for resilient operation")

def main():
    """Main entry point."""
    logger.info("Starting resilient bot runner...")
    
    # Configure signal handlers
    handle_signals()
    
    # Configure environment
    configure_environment()
    
    # Kill any competing bot processes
    kill_competing_bots()
    
    # Acquire an exclusive lock
    lock_fd = acquire_lock()
    if not lock_fd:
        logger.error("Could not acquire lock, exiting")
        sys.exit(1)
    
    # Register a function to release the lock when the process exits
    import atexit
    atexit.register(release_lock, lock_fd)
    
    # Ensure cache files exist
    ensure_cache_files()
    
    # Start the main application
    try:
        logger.info("Starting main application...")
        
        # Import and run main to start the bot
        from main import main
        main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down")
    except Exception as e:
        logger.error(f"Error running main application: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()