#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Mood tracking database utilities for the FiLot Telegram bot
"""

import logging
import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.exc import SQLAlchemyError

from models import db, MoodEntry, User

# Configure logging
logger = logging.getLogger(__name__)

def save_mood_entry(
    user_id: int,
    mood: str,
    mood_emoji: str,
    context: str,
    notes: str = ""
) -> Optional[MoodEntry]:
    """
    Save a user's mood entry to the database.
    
    Args:
        user_id: Telegram user ID
        mood: Mood value (very_happy, happy, neutral, etc.)
        mood_emoji: Emoji representation of the mood
        context: Context of the mood (before_investment, after_investment, etc.)
        notes: Optional user notes about the mood
        
    Returns:
        The created MoodEntry object, or None if there was an error
    """
    try:
        # Ensure user exists
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"Attempt to save mood for non-existent user {user_id}")
            return None
            
        # Create and save mood entry
        mood_entry = MoodEntry()
        mood_entry.user_id = user_id
        mood_entry.mood = mood
        mood_entry.mood_emoji = mood_emoji
        mood_entry.context = context
        mood_entry.notes = notes
        
        db.session.add(mood_entry)
        db.session.commit()
        
        # Log the activity without using the log_user_activity function to avoid circular imports
        logger.info(f"User {user_id} mood tracked: {mood} in context {context}")
        
        return mood_entry
        
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error saving mood entry: {e}")
        return None

def get_mood_history(
    user_id: int,
    limit: int = 10,
    context_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get a user's mood history from the database.
    
    Args:
        user_id: Telegram user ID
        limit: Maximum number of entries to return
        context_filter: Optional filter to only return entries with a specific context
        
    Returns:
        List of mood entry data, ordered by most recent first
    """
    try:
        # Query mood entries for the user
        query = MoodEntry.query.filter_by(user_id=user_id)
        
        # Apply context filter if specified
        if context_filter:
            query = query.filter_by(context=context_filter)
            
        # Order by most recent first and apply limit
        entries = query.order_by(MoodEntry.timestamp.desc()).limit(limit).all()
        
        # Format the results
        return [
            {
                "id": entry.id,
                "mood": entry.mood,
                "mood_emoji": entry.mood_emoji,
                "context": entry.context,
                "notes": entry.notes,
                "timestamp": entry.timestamp
            }
            for entry in entries
        ]
        
    except SQLAlchemyError as e:
        logger.error(f"Error fetching mood history: {e}")
        return []

def get_mood_stats(
    user_id: int,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get statistics about a user's mood entries.
    
    Args:
        user_id: Telegram user ID
        days: Number of days to include in the stats
        
    Returns:
        Dictionary with mood statistics
    """
    try:
        # Calculate the cutoff date
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        
        # Query mood entries for the user within the time frame
        entries = MoodEntry.query.filter_by(user_id=user_id).filter(
            MoodEntry.timestamp >= cutoff_date
        ).all()
        
        if not entries:
            return {
                "total_entries": 0,
                "most_common_mood": None,
                "most_common_context": None,
                "mood_counts": {},
                "context_counts": {}
            }
            
        # Count moods and contexts
        mood_counts = {}
        context_counts = {}
        
        for entry in entries:
            # Count moods
            if entry.mood in mood_counts:
                mood_counts[entry.mood] += 1
            else:
                mood_counts[entry.mood] = 1
                
            # Count contexts
            if entry.context in context_counts:
                context_counts[entry.context] += 1
            else:
                context_counts[entry.context] = 1
                
        # Determine most common mood and context safely
        most_common_mood = None
        most_common_context = None
        
        if mood_counts:
            most_common_mood = max(mood_counts.items(), key=lambda x: x[1])[0]
            
        if context_counts:
            most_common_context = max(context_counts.items(), key=lambda x: x[1])[0]
        
        return {
            "total_entries": len(entries),
            "most_common_mood": most_common_mood,
            "most_common_context": most_common_context,
            "mood_counts": mood_counts,
            "context_counts": context_counts
        }
        
    except Exception as e:
        logger.error(f"Error calculating mood stats: {e}")
        return {
            "total_entries": 0,
            "most_common_mood": None,
            "most_common_context": None,
            "mood_counts": {},
            "context_counts": {}
        }