#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database fallback mechanism for FiLot Telegram bot
Provides in-memory storage when the database is unavailable
"""

import logging
import time
from typing import Dict, Any, List, Optional

# Setup logging
logger = logging.getLogger(__name__)

# In-memory storage for user menu states
user_menu_states = {}

# In-memory storage for user activity
user_activity_log = []

# In-memory storage for session data
session_data = {}

def store_menu_state(user_id: int, menu_type: str) -> None:
    """
    Store a user's menu state in memory when database is unavailable.
    
    Args:
        user_id: Telegram user ID
        menu_type: Current menu type the user is in
    """
    user_menu_states[user_id] = {
        'menu_type': menu_type,
        'timestamp': time.time()
    }
    logger.debug(f"Stored menu state {menu_type} for user {user_id} in fallback storage")

async def store_menu_state_async(user_id: int, menu_type: str) -> None:
    """
    Async version of store_menu_state.
    
    Args:
        user_id: Telegram user ID
        menu_type: Current menu type the user is in
    """
    store_menu_state(user_id, menu_type)

def get_menu_state(user_id: int) -> Optional[str]:
    """
    Get a user's menu state from memory when database is unavailable.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Menu type as a string or None if not found
    """
    user_state = user_menu_states.get(user_id)
    if user_state:
        return user_state.get('menu_type')
    return None

async def get_menu_state_async(user_id: int) -> Optional[str]:
    """
    Async version of get_menu_state.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Menu type as a string or None if not found
    """
    return get_menu_state(user_id)

def log_user_activity(user_id: int, activity_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Log user activity to memory when database is unavailable.
    
    Args:
        user_id: Telegram user ID
        activity_type: Type of activity being logged
        metadata: Optional additional data about the activity
    """
    user_activity_log.append({
        'user_id': user_id,
        'activity_type': activity_type,
        'metadata': metadata or {},
        'timestamp': time.time()
    })
    
    # Keep the log from growing too large
    if len(user_activity_log) > 1000:
        user_activity_log.pop(0)
        
    logger.debug(f"Logged activity {activity_type} for user {user_id} in fallback storage")

async def log_user_activity_async(user_id: int, activity_type: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """
    Async version of log_user_activity.
    
    Args:
        user_id: Telegram user ID
        activity_type: Type of activity being logged
        metadata: Optional additional data about the activity
    """
    log_user_activity(user_id, activity_type, metadata)

def store_session_data(session_id: str, data: Dict[str, Any]) -> None:
    """
    Store session data in memory when database is unavailable.
    
    Args:
        session_id: Unique session identifier
        data: Data to store for the session
    """
    session_data[session_id] = {
        'data': data,
        'timestamp': time.time()
    }
    logger.debug(f"Stored session data for {session_id} in fallback storage")

async def store_session_data_async(session_id: str, data: Dict[str, Any]) -> None:
    """
    Async version of store_session_data.
    
    Args:
        session_id: Unique session identifier
        data: Data to store for the session
    """
    store_session_data(session_id, data)

def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session data from memory when database is unavailable.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Session data dictionary or None if not found
    """
    session = session_data.get(session_id)
    if session:
        return session.get('data')
    return None

async def get_session_data_async(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Async version of get_session_data.
    
    Args:
        session_id: Unique session identifier
        
    Returns:
        Session data dictionary or None if not found
    """
    return get_session_data(session_id)

def clear_old_data() -> None:
    """
    Clean up old data to prevent memory leaks.
    Should be called periodically.
    """
    current_time = time.time()
    
    # Clear menu states older than 24 hours
    expired_users = []
    for user_id, state in user_menu_states.items():
        if current_time - state.get('timestamp', 0) > 86400:  # 24 hours
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del user_menu_states[user_id]
    
    # Clear session data older than 48 hours
    expired_sessions = []
    for session_id, session in session_data.items():
        if current_time - session.get('timestamp', 0) > 172800:  # 48 hours
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del session_data[session_id]
    
    # Clean up activity log to prevent it from growing too large
    if len(user_activity_log) > 5000:  # Keep last 5000 activities
        # Sort by timestamp (oldest first) and keep only the newest entries
        sorted_log = sorted(user_activity_log, key=lambda x: x.get('timestamp', 0))
        user_activity_log.clear()
        user_activity_log.extend(sorted_log[-5000:])  # Keep newest 5000 entries
    
    logger.debug(f"Cleaned up {len(expired_users)} user states and {len(expired_sessions)} sessions from fallback storage")

async def clear_old_data_async() -> None:
    """
    Async version of clear_old_data.
    """
    clear_old_data()