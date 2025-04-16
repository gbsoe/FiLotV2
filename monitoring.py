#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Monitoring capabilities for the Telegram cryptocurrency pool bot
"""

import os
import time
import json
import logging
import datetime
import threading
import traceback
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps

import db_utils
from models import ErrorLog, BotStatistics, User, UserQuery

# Configure logging
logger = logging.getLogger(__name__)

# Global variables for tracking performance
start_time = time.time()
uptime_checks = []  # List of uptime check timestamps and results
error_count = 0
command_processing_times = []  # List of command processing times
health_status = "STARTING"  # Current health status (HEALTHY, DEGRADED, UNHEALTHY)

def performance_tracker(func):
    """Decorator to track function performance."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # Track time taken
            time_taken = (time.time() - start) * 1000  # Convert to ms
            
            # Store processing time
            command_processing_times.append(time_taken)
            
            # Keep only the last 1000 times
            if len(command_processing_times) > 1000:
                command_processing_times.pop(0)
            
            return result
        except Exception as e:
            # Track error and re-raise
            global error_count
            error_count += 1
            
            # Log error details
            log_error(str(e), func.__name__, traceback.format_exc())
            
            raise
    
    return wrapper

def scheduled_task(interval: int):
    """Decorator for scheduled tasks."""
    def decorator(func):
        def wrapper():
            while True:
                try:
                    func()
                except Exception as e:
                    logger.error(f"Error in scheduled task {func.__name__}: {e}")
                    
                    # Log error
                    log_error(str(e), f"scheduled_task.{func.__name__}", traceback.format_exc())
                
                # Sleep for the interval
                time.sleep(interval)
        
        # Start the task in a new thread
        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()
        
        return func
    
    return decorator

def log_error(error_message: str, module: str = None, tb: str = None, user_id: int = None) -> None:
    """
    Log an error to the database.
    
    Args:
        error_message: Error message
        module: Module where the error occurred (optional)
        tb: Traceback (optional)
        user_id: User ID if error is related to a user (optional)
    """
    try:
        # Log to database
        db_utils.log_error("Runtime Error", error_message, tb, module, user_id)
    except Exception as e:
        # If we can't log to the database, at least log to the file
        logger.error(f"Failed to log error to database: {e}")
        logger.error(f"Original error: {error_message}")
        if tb:
            logger.error(f"Traceback: {tb}")

def get_system_health() -> Dict[str, Any]:
    """
    Get the current system health status.
    
    Returns:
        Dictionary with health information
    """
    now = time.time()
    uptime = now - start_time
    
    # Calculate average response time
    avg_response_time = 0
    if command_processing_times:
        avg_response_time = sum(command_processing_times) / len(command_processing_times)
    
    # Calculate uptime percentage from the checks
    uptime_percentage = 100.0
    if uptime_checks:
        successful_checks = sum(1 for _, success in uptime_checks if success)
        uptime_percentage = (successful_checks / len(uptime_checks)) * 100
    
    # Get user statistics
    try:
        total_users = User.query.count()
        active_users = User.query.filter(
            User.last_active > (datetime.datetime.utcnow() - datetime.timedelta(days=1))
        ).count()
        command_count = UserQuery.query.count()
    except Exception as e:
        logger.error(f"Error getting user statistics: {e}")
        total_users = 0
        active_users = 0
        command_count = 0
    
    # Determine health status
    global health_status
    if error_count > 100 or uptime_percentage < 90:
        health_status = "UNHEALTHY"
    elif error_count > 10 or uptime_percentage < 98 or avg_response_time > 1000:
        health_status = "DEGRADED"
    else:
        health_status = "HEALTHY"
    
    return {
        "status": health_status,
        "uptime": uptime,
        "uptime_formatted": str(datetime.timedelta(seconds=int(uptime))),
        "uptime_percentage": uptime_percentage,
        "error_count": error_count,
        "average_response_time": avg_response_time,
        "total_users": total_users,
        "active_users": active_users,
        "command_count": command_count,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@scheduled_task(interval=300)  # 5 minutes
def update_system_statistics():
    """Update system statistics in the database."""
    try:
        # Calculate uptime percentage
        uptime_percentage = 100.0
        if uptime_checks:
            successful_checks = sum(1 for _, success in uptime_checks if success)
            uptime_percentage = (successful_checks / len(uptime_checks)) * 100
        
        # Calculate average response time
        avg_response_time = 0
        if command_processing_times:
            avg_response_time = sum(command_processing_times) / len(command_processing_times)
        
        # Update statistics in the database
        stats = db_utils.update_bot_statistics()
        if stats:
            stats.error_count = error_count
            stats.uptime_percentage = uptime_percentage
            stats.average_response_time = avg_response_time
            db_utils.db.session.commit()
        
        logger.info("System statistics updated")
    except Exception as e:
        logger.error(f"Error updating system statistics: {e}")

@scheduled_task(interval=3600)  # 1 hour
def create_database_backup():
    """Create a backup of the database."""
    try:
        db_utils.create_database_backup()
        logger.info("Database backup created")
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")

@scheduled_task(interval=60)  # 1 minute
def health_check():
    """Perform a health check and record the result."""
    try:
        # Simple health check: Check if we can query the database
        user_count = User.query.count()
        
        # Record success
        uptime_checks.append((time.time(), True))
        
        # Keep only the last 1000 checks
        if len(uptime_checks) > 1000:
            uptime_checks.pop(0)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        # Record failure
        uptime_checks.append((time.time(), False))
        
        # Keep only the last 1000 checks
        if len(uptime_checks) > 1000:
            uptime_checks.pop(0)
        
        # Log error
        log_error(f"Health check failed: {e}", "monitoring.health_check")

# Initialize monitoring system
def init_monitoring():
    """Initialize the monitoring system."""
    logger.info("Initializing monitoring system")
    
    # Start scheduled tasks
    update_system_statistics()
    health_check()
    
    # Create initial database backup
    create_database_backup()
    
    logger.info("Monitoring system initialized")

# Health check endpoint for the web app
def health_check_endpoint():
    """
    Health check endpoint for external monitoring.
    
    Returns:
        Health status in JSON format
    """
    health_data = get_system_health()
    
    # Return health status with appropriate HTTP status code
    if health_data["status"] == "UNHEALTHY":
        return json.dumps(health_data), 500
    elif health_data["status"] == "DEGRADED":
        return json.dumps(health_data), 200
    else:
        return json.dumps(health_data), 200