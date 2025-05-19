#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced database fallback mechanisms for FiLot Telegram bot
Provides complete memory-based storage when the database is unavailable
"""

import time
import logging
import json
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# In-memory storage for various data
user_menu_states = {}  # User ID -> Menu state
user_activity_log = []  # List of user activity records
session_data = {}  # Session ID -> Session data
cached_pool_data = {}  # Cache for pool data
cached_token_prices = {}  # Cache for token prices
user_profiles = {}  # User ID -> User profile data
verification_codes = {}  # User ID -> Verification code
subscription_status = {}  # User ID -> Subscription status
blocked_users = set()  # Set of blocked user IDs

# File paths for persistent storage
POOL_DATA_CACHE_FILE = "pool_data_test_results.json"
TOKEN_PRICES_CACHE_FILE = "token_price_cache.json"
USER_PROFILES_FILE = "user_profiles_backup.json"

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
    logger.debug(f"Stored menu state for user {user_id}: {menu_type}")

def get_menu_state(user_id: int) -> Optional[str]:
    """
    Get a user's menu state from memory when database is unavailable.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Menu type as a string or None if not found
    """
    state = user_menu_states.get(user_id)
    if state:
        return state.get('menu_type')
    return None

def reset_menu_state(user_id: int) -> None:
    """
    Reset a user's menu state in memory.
    
    Args:
        user_id: Telegram user ID
    """
    if user_id in user_menu_states:
        del user_menu_states[user_id]
        logger.debug(f"Reset menu state for user {user_id}")

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
    logger.debug(f"Logged user activity for user {user_id}: {activity_type}")

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
    logger.debug(f"Stored session data for session {session_id}")

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

def store_user_profile(user_id: int, profile_data: Dict[str, Any]) -> None:
    """
    Store user profile data in memory.
    
    Args:
        user_id: Telegram user ID
        profile_data: User's profile data
    """
    user_profiles[user_id] = {
        'data': profile_data,
        'timestamp': time.time()
    }
    logger.debug(f"Stored profile data for user {user_id}")
    
    # Attempt to save to disk
    try:
        save_user_profiles_to_disk()
    except Exception as e:
        logger.warning(f"Failed to save user profiles to disk: {e}")

def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get user profile data from memory.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        User profile data dictionary or None if not found
    """
    profile = user_profiles.get(user_id)
    if profile:
        return profile.get('data')
    return None

def save_user_profiles_to_disk() -> None:
    """Save all user profile data to disk for persistence."""
    try:
        data_to_save = {}
        for user_id, profile in user_profiles.items():
            data_to_save[str(user_id)] = profile['data']
            
        with open(USER_PROFILES_FILE, 'w') as f:
            json.dump(data_to_save, f)
            logger.info(f"Saved {len(data_to_save)} user profiles to disk")
    except Exception as e:
        logger.error(f"Error saving user profiles to disk: {e}")

def load_user_profiles_from_disk() -> None:
    """Load all user profile data from disk."""
    try:
        if os.path.exists(USER_PROFILES_FILE):
            with open(USER_PROFILES_FILE, 'r') as f:
                data = json.load(f)
                
                for user_id_str, profile_data in data.items():
                    try:
                        user_id = int(user_id_str)
                        user_profiles[user_id] = {
                            'data': profile_data,
                            'timestamp': time.time()
                        }
                    except ValueError:
                        logger.warning(f"Invalid user ID in profiles file: {user_id_str}")
                
                logger.info(f"Loaded {len(user_profiles)} user profiles from disk")
    except Exception as e:
        logger.error(f"Error loading user profiles from disk: {e}")

def update_user_profile(user_id: int, field: str, value: Any) -> bool:
    """
    Update a specific field in a user's profile.
    
    Args:
        user_id: Telegram user ID
        field: The field to update
        value: The new value for the field
        
    Returns:
        True if successful, False otherwise
    """
    profile = get_user_profile(user_id)
    if not profile:
        profile = {}
        
    profile[field] = value
    store_user_profile(user_id, profile)
    return True

def store_verification_code(user_id: int, code: str) -> None:
    """
    Store a verification code for a user.
    
    Args:
        user_id: Telegram user ID
        code: Verification code
    """
    verification_codes[user_id] = {
        'code': code,
        'timestamp': time.time()
    }
    logger.debug(f"Stored verification code for user {user_id}")

def get_verification_code(user_id: int) -> Optional[str]:
    """
    Get a verification code for a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Verification code or None if not found or expired
    """
    code_data = verification_codes.get(user_id)
    if code_data:
        # Check if code is expired (24 hours)
        if time.time() - code_data.get('timestamp', 0) < 86400:
            return code_data.get('code')
    return None

def verify_user(user_id: int, code: str) -> bool:
    """
    Verify a user with the provided code.
    
    Args:
        user_id: Telegram user ID
        code: Verification code
        
    Returns:
        True if verification is successful, False otherwise
    """
    stored_code = get_verification_code(user_id)
    if stored_code and stored_code == code:
        # Mark user as verified in profile
        update_user_profile(user_id, 'is_verified', True)
        # Clear the verification code
        if user_id in verification_codes:
            del verification_codes[user_id]
        return True
    return False

def block_user(user_id: int) -> bool:
    """
    Block a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    blocked_users.add(user_id)
    update_user_profile(user_id, 'is_blocked', True)
    logger.info(f"Blocked user {user_id}")
    return True

def unblock_user(user_id: int) -> bool:
    """
    Unblock a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    if user_id in blocked_users:
        blocked_users.remove(user_id)
    update_user_profile(user_id, 'is_blocked', False)
    logger.info(f"Unblocked user {user_id}")
    return True

def is_user_blocked(user_id: int) -> bool:
    """
    Check if a user is blocked.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if the user is blocked, False otherwise
    """
    if user_id in blocked_users:
        return True
        
    profile = get_user_profile(user_id)
    if profile and profile.get('is_blocked'):
        return True
        
    return False

def subscribe_user(user_id: int) -> bool:
    """
    Subscribe a user to updates.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    subscription_status[user_id] = True
    update_user_profile(user_id, 'is_subscribed', True)
    logger.info(f"Subscribed user {user_id}")
    return True

def unsubscribe_user(user_id: int) -> bool:
    """
    Unsubscribe a user from updates.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    subscription_status[user_id] = False
    update_user_profile(user_id, 'is_subscribed', False)
    logger.info(f"Unsubscribed user {user_id}")
    return True

def is_user_subscribed(user_id: int) -> bool:
    """
    Check if a user is subscribed to updates.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if the user is subscribed, False otherwise
    """
    if user_id in subscription_status:
        return subscription_status[user_id]
        
    profile = get_user_profile(user_id)
    if profile and profile.get('is_subscribed'):
        return True
        
    return False

def get_subscribed_users() -> List[int]:
    """
    Get a list of user IDs that are subscribed to updates.
    
    Returns:
        List of user IDs
    """
    subscribed_users = []
    
    # First check direct subscription status
    for user_id, status in subscription_status.items():
        if status:
            subscribed_users.append(user_id)
    
    # Then check profiles
    for user_id, profile in user_profiles.items():
        if user_id not in subscribed_users and profile.get('data', {}).get('is_subscribed'):
            subscribed_users.append(user_id)
    
    return subscribed_users

def cache_pool_data(pool_data: Dict[str, Any]) -> None:
    """
    Cache pool data in memory.
    
    Args:
        pool_data: Pool data to cache
    """
    global cached_pool_data
    cached_pool_data = pool_data
    
    # Also save to disk for persistence
    try:
        with open(POOL_DATA_CACHE_FILE, 'w') as f:
            json.dump(pool_data, f)
            logger.info(f"Cached pool data saved to disk")
    except Exception as e:
        logger.error(f"Error saving cached pool data to disk: {e}")

def get_cached_pool_data() -> Dict[str, Any]:
    """
    Get cached pool data from memory.
    
    Returns:
        Cached pool data or empty dict if not available
    """
    global cached_pool_data
    
    # If we don't have pool data in memory, try to load from disk
    if not cached_pool_data:
        try:
            if os.path.exists(POOL_DATA_CACHE_FILE):
                with open(POOL_DATA_CACHE_FILE, 'r') as f:
                    cached_pool_data = json.load(f)
                    logger.info(f"Loaded cached pool data from disk")
        except Exception as e:
            logger.error(f"Error loading cached pool data from disk: {e}")
    
    return cached_pool_data or {}

def cache_token_price(token_symbol: str, price: float) -> None:
    """
    Cache a token price in memory.
    
    Args:
        token_symbol: Token symbol (e.g., SOL, BTC)
        price: Token price in USD
    """
    cached_token_prices[token_symbol] = {
        'price': price,
        'timestamp': time.time()
    }
    
    # Save to disk occasionally
    try:
        with open(TOKEN_PRICES_CACHE_FILE, 'w') as f:
            # Convert to serializable format
            data_to_save = {}
            for symbol, data in cached_token_prices.items():
                data_to_save[symbol] = {
                    'price': data['price'],
                    'timestamp': data['timestamp']
                }
            
            json.dump(data_to_save, f)
            logger.info(f"Cached token prices saved to disk")
    except Exception as e:
        logger.error(f"Error saving cached token prices to disk: {e}")

def get_cached_token_price(token_symbol: str) -> Optional[float]:
    """
    Get a cached token price from memory.
    
    Args:
        token_symbol: Token symbol (e.g., SOL, BTC)
        
    Returns:
        Cached token price or None if not available or expired
    """
    # Try to load from disk if our cache is empty
    if not cached_token_prices:
        try:
            if os.path.exists(TOKEN_PRICES_CACHE_FILE):
                with open(TOKEN_PRICES_CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    for symbol, price_data in data.items():
                        cached_token_prices[symbol] = price_data
                    logger.info(f"Loaded cached token prices from disk")
        except Exception as e:
            logger.error(f"Error loading cached token prices from disk: {e}")
    
    price_data = cached_token_prices.get(token_symbol)
    if price_data:
        # Check if price is expired (1 hour)
        if time.time() - price_data.get('timestamp', 0) < 3600:
            return price_data.get('price')
    return None

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
    
    # Clean up verification codes older than 24 hours
    expired_codes = []
    for user_id, code_data in verification_codes.items():
        if current_time - code_data.get('timestamp', 0) > 86400:  # 24 hours
            expired_codes.append(user_id)
    
    for user_id in expired_codes:
        del verification_codes[user_id]
    
    logger.debug(f"Cleaned up {len(expired_users)} user states, {len(expired_sessions)} sessions, and {len(expired_codes)} verification codes from fallback storage")

def initialization_check() -> bool:
    """
    Check if the fallback systems are initialized and working correctly.
    This is a simple check to make sure the files exist and are readable.
    
    Returns:
        True if all checks pass, False otherwise
    """
    try:
        # Try to load cached pool data (creates file if it doesn't exist)
        if not os.path.exists(POOL_DATA_CACHE_FILE):
            with open(POOL_DATA_CACHE_FILE, 'w') as f:
                json.dump({}, f)
            
        # Try to load cached token prices (creates file if it doesn't exist)
        if not os.path.exists(TOKEN_PRICES_CACHE_FILE):
            with open(TOKEN_PRICES_CACHE_FILE, 'w') as f:
                json.dump({}, f)
                
        # Try to load user profiles (creates file if it doesn't exist)
        if not os.path.exists(USER_PROFILES_FILE):
            with open(USER_PROFILES_FILE, 'w') as f:
                json.dump({}, f)
                
        # Load any existing data
        load_user_profiles_from_disk()
        
        logger.info("Fallback systems initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing fallback systems: {e}")
        return False

# Initialize the fallback systems when this module is imported
initialization_check()