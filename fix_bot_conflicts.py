#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to fix competing Telegram bot instances and establish database fallbacks.
Run this before starting the bot to ensure a clean environment.
"""

import os
import sys
import time
import signal
import logging
import psutil
import fcntl
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
LOCK_FILE = 'bot_instance.lock'

def acquire_lock():
    """
    Acquire an exclusive lock to ensure only one bot instance runs.
    Returns the lock file descriptor if successful, None otherwise.
    """
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
    """Release the exclusive lock and remove the lock file."""
    if lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()
        try:
            os.unlink(LOCK_FILE)
        except:
            pass
        logger.info("Released exclusive bot lock")

def terminate_competing_bots():
    """Find and terminate any competing bot processes."""
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    
    # Count of terminated processes
    terminated_count = 0
    
    # Get all Python processes
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip if this is our own process
            if proc.pid == current_pid:
                continue
                
            # Check if this is a bot process
            cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else ''
            if proc.name() == 'python' and 'main.py' in cmdline:
                logger.info(f"Found competing bot process (PID: {proc.pid}), terminating it")
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                    terminated_count += 1
                except Exception as e:
                    logger.error(f"Failed to terminate competing process: {e}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    logger.info(f"Terminated {terminated_count} competing bot processes")
    
    # If we terminated any processes, wait a moment for them to shut down
    if terminated_count > 0:
        time.sleep(2)

def initialize_fallback_systems():
    """
    Initialize memory-based fallback systems for database-independent operation.
    Returns True if successful, False otherwise.
    """
    try:
        # Import fallback modules
        import db_fallback
        
        # Create empty pool data cache file if it doesn't exist
        cache_file = "pool_data_test_results.json"
        if not os.path.exists(cache_file):
            with open(cache_file, 'w') as f:
                f.write('[]')
            logger.info(f"Created empty pool data cache file: {cache_file}")
        
        logger.info("Initialized memory-based fallback systems for database-independent operation")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize fallback systems: {e}")
        return False

def main():
    """Main entry point."""
    logger.info("Starting bot instance conflict resolution...")
    
    # Step 1: Terminate any competing bot processes
    terminate_competing_bots()
    
    # Step 2: Acquire an exclusive lock
    lock_fd = acquire_lock()
    if not lock_fd:
        logger.error("Could not acquire exclusive lock, exiting")
        sys.exit(1)
    
    # Register function to release lock on exit
    atexit.register(release_lock, lock_fd)
    
    # Step 3: Initialize fallback systems
    if initialize_fallback_systems():
        logger.info("Bot environment prepared successfully")
    else:
        logger.warning("Bot environment preparation incomplete, but will continue")
    
    logger.info("Ready to start bot with exclusive access")

if __name__ == "__main__":
    main()