#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Anti-loop protection for FiLot Telegram bot
Prevents message loops and detects repeated actions to improve user experience
"""

import time
import logging
from typing import Dict, Set, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

# Store user message history for loop detection
# Key: user_id, Value: List of (message_text, timestamp) tuples
user_message_history: Dict[int, List[Tuple[str, float]]] = {}

# Store button presses to detect repetitive button clicks
# Key: user_id, Value: Dict of button_text -> List of timestamps
user_button_presses: Dict[int, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

# Store last sent messages to each user to prevent duplicate notifications
# Key: user_id, Value: (message_text, timestamp)
last_sent_messages: Dict[int, Tuple[str, float]] = {}

# Maximum number of messages to keep in history per user
MAX_HISTORY_SIZE = 20

# Maximum allowed duplicate messages in a short time window
MAX_DUPLICATES = 3

# Time window for duplicate detection (in seconds)
DUPLICATE_WINDOW = 10.0

# Button press rate limiting window (in seconds)
BUTTON_RATE_LIMIT_WINDOW = 2.0

# Minimum time between duplicate messages (in seconds)
MIN_DUPLICATE_INTERVAL = 2.0


def record_user_message(user_id: int, message_text: str) -> None:
    """
    Record a user's message to detect potential loops.
    
    Args:
        user_id: Telegram user ID
        message_text: Message text content
    """
    timestamp = time.time()
    
    # Initialize history for new users
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    
    # Add the current message
    user_message_history[user_id].append((message_text, timestamp))
    
    # Keep history size limited
    if len(user_message_history[user_id]) > MAX_HISTORY_SIZE:
        user_message_history[user_id].pop(0)
    
    # Log for debugging
    logger.debug(f"Recorded message from user {user_id}: {message_text[:20]}...")


def is_potential_loop(user_id: int, message_text: str) -> bool:
    """
    Check if the current message is part of a potential message loop.
    
    Args:
        user_id: Telegram user ID
        message_text: Message text content
        
    Returns:
        True if this appears to be a loop, False otherwise
    """
    if user_id not in user_message_history:
        return False
    
    # Get recent history
    history = user_message_history[user_id]
    
    # Count occurrences of this message in the recent past
    now = time.time()
    recent_count = 0
    
    for hist_text, hist_time in history:
        if hist_text == message_text and now - hist_time < DUPLICATE_WINDOW:
            recent_count += 1
    
    # If we've seen this message too many times recently, it's a potential loop
    if recent_count >= MAX_DUPLICATES:
        logger.warning(f"Detected potential message loop for user {user_id}: {message_text[:20]}...")
        return True
    
    return False


def record_button_press(user_id: int, button_text: str) -> None:
    """
    Record a button press to detect rapid repeated clicks.
    
    Args:
        user_id: Telegram user ID
        button_text: Text of the pressed button
    """
    timestamp = time.time()
    user_button_presses[user_id][button_text].append(timestamp)
    
    # Clean up old button presses to prevent memory growth
    cutoff_time = timestamp - DUPLICATE_WINDOW
    user_button_presses[user_id][button_text] = [
        t for t in user_button_presses[user_id][button_text] if t >= cutoff_time
    ]


def is_button_rate_limited(user_id: int, button_text: str) -> bool:
    """
    Check if the user is pressing a button too frequently.
    
    Args:
        user_id: Telegram user ID
        button_text: Text of the pressed button
        
    Returns:
        True if the button press should be rate limited, False otherwise
    """
    # If no history, allow the button press
    if user_id not in user_button_presses or button_text not in user_button_presses[user_id]:
        return False
    
    # Check if there's already a recent press of this button
    now = time.time()
    recent_presses = [
        t for t in user_button_presses[user_id][button_text] 
        if now - t < BUTTON_RATE_LIMIT_WINDOW
    ]
    
    # If we have multiple recent presses, rate limit
    if len(recent_presses) > 1:
        logger.info(f"Rate limiting button '{button_text}' for user {user_id}")
        return True
    
    return False


def record_sent_message(user_id: int, message_text: str) -> None:
    """
    Record a message sent to a user to prevent duplicate notifications.
    
    Args:
        user_id: Telegram user ID
        message_text: Message text content
    """
    last_sent_messages[user_id] = (message_text, time.time())


def is_duplicate_outgoing(user_id: int, message_text: str) -> bool:
    """
    Check if a message is a duplicate of one recently sent to the user.
    
    Args:
        user_id: Telegram user ID
        message_text: Message text content
        
    Returns:
        True if this appears to be a duplicate, False otherwise
    """
    if user_id not in last_sent_messages:
        return False
    
    last_text, last_time = last_sent_messages[user_id]
    now = time.time()
    
    # If it's the same message and sent too soon after the last one
    if last_text == message_text and now - last_time < MIN_DUPLICATE_INTERVAL:
        logger.info(f"Prevented duplicate message to user {user_id}")
        return True
    
    return False


def clean_expired_records() -> None:
    """
    Clean up expired records to prevent memory leaks.
    Should be called periodically.
    """
    cutoff_time = time.time() - DUPLICATE_WINDOW * 2
    
    # Clean up message history
    for user_id in list(user_message_history.keys()):
        user_message_history[user_id] = [
            (text, timestamp) for text, timestamp in user_message_history[user_id]
            if timestamp >= cutoff_time
        ]
        
        # Remove empty histories
        if not user_message_history[user_id]:
            del user_message_history[user_id]
    
    # Clean up button press history
    for user_id in list(user_button_presses.keys()):
        for button_text in list(user_button_presses[user_id].keys()):
            user_button_presses[user_id][button_text] = [
                t for t in user_button_presses[user_id][button_text]
                if t >= cutoff_time
            ]
            
            # Remove empty button histories
            if not user_button_presses[user_id][button_text]:
                del user_button_presses[user_id][button_text]
        
        # Remove empty user entries
        if not user_button_presses[user_id]:
            del user_button_presses[user_id]
    
    # Clean up sent messages
    for user_id in list(last_sent_messages.keys()):
        if last_sent_messages[user_id][1] < cutoff_time:
            del last_sent_messages[user_id]