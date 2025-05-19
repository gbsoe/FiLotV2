#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Emoji-Based Mood Tracking for Financial Decisions in FiLot Telegram Bot
Tracks user mood before and after investment decisions to help users understand
emotional patterns in their investment behavior.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, ConversationHandler,
    MessageHandler, filters, CallbackQueryHandler
)

import db_utils
from db_utils_mood import save_mood_entry, get_mood_history, get_mood_stats
from models import User, db
from keyboard_utils import get_reply_keyboard, set_menu_state

# Configure logging for mood tracking module
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_MOOD, SELECTING_CONTEXT, RECORDING_NOTES, VIEWING_HISTORY = range(4)

# Mood emojis and their descriptions
MOOD_EMOJIS = {
    "😁": "very_happy",
    "🙂": "happy",
    "😐": "neutral",
    "🙁": "sad",
    "😟": "anxious",
    "😠": "angry",
    "🤔": "confused"
}

# Context categories for mood entries
CONTEXT_CATEGORIES = [
    "before_investment", 
    "after_investment",
    "market_up",
    "market_down",
    "news_reaction",
    "general_market"
]

async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the mood tracking conversation.
    """
    if update.effective_user and update.effective_message:
        user_id = update.effective_user.id
        
        # Get or create user in the database
        user = db_utils.get_user_by_id(user_id)
        if not user:
            username = update.effective_user.username or "unknown"
            first_name = update.effective_user.first_name or ""
            last_name = update.effective_user.last_name or ""
            user = db_utils.create_user(user_id, username, first_name, last_name)
        
        # Create keyboard with mood emojis
        keyboard = []
        row = []
        
        for emoji, _ in MOOD_EMOJIS.items():
            if len(row) == 4:  # 4 emojis per row
                keyboard.append(row)
                row = []
            row.append(InlineKeyboardButton(emoji, callback_data=f"mood_{emoji}"))
        
        if row:  # Add any remaining buttons
            keyboard.append(row)
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="mood_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(
            "How are you feeling about your investments right now? Select a mood:",
            reply_markup=reply_markup
        )
        
        return SELECTING_MOOD
    return ConversationHandler.END

async def mood_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the mood selection.
    """
    if update.callback_query and update.callback_query.data:
        query = update.callback_query
        await query.answer()
        
        # Check if user cancelled
        if query.data == "mood_cancel":
            await query.message.reply_text("Mood tracking cancelled.")
            return ConversationHandler.END
        
        # Extract the mood emoji from the callback data
        selected_mood = query.data.replace("mood_", "")
        context.user_data["selected_mood"] = selected_mood
        context.user_data["mood_value"] = MOOD_EMOJIS.get(selected_mood, "unknown")
        
        # Create keyboard with context categories
        keyboard = []
        for category in CONTEXT_CATEGORIES:
            # Make the category more readable for display
            display_name = category.replace("_", " ").title()
            keyboard.append([InlineKeyboardButton(display_name, callback_data=f"context_{category}")])
        
        # Add cancel button
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="context_cancel")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            f"You selected mood: {selected_mood}\n\nWhat's the context of your mood?",
            reply_markup=reply_markup
        )
        
        return SELECTING_CONTEXT
    return ConversationHandler.END

async def context_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the context selection.
    """
    if update.callback_query and update.callback_query.data:
        query = update.callback_query
        await query.answer()
        
        # Check if user cancelled
        if query.data == "context_cancel":
            await query.message.reply_text("Mood tracking cancelled.")
            return ConversationHandler.END
        
        # Extract the context from the callback data
        selected_context = query.data.replace("context_", "")
        context.user_data["selected_context"] = selected_context
        
        # Ask for optional notes
        keyboard = [
            [InlineKeyboardButton("Skip Notes", callback_data="notes_skip")],
            [InlineKeyboardButton("Cancel", callback_data="notes_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "Would you like to add any notes about your mood? Type your notes or click 'Skip Notes'.",
            reply_markup=reply_markup
        )
        
        return RECORDING_NOTES
    return ConversationHandler.END

async def record_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Record any notes the user wants to add.
    """
    if update.callback_query and update.callback_query.data:
        # Handle button clicks for skip or cancel
        query = update.callback_query
        await query.answer()
        
        if query.data == "notes_cancel":
            await query.message.reply_text("Mood tracking cancelled.")
            return ConversationHandler.END
        
        if query.data == "notes_skip":
            context.user_data["notes"] = ""
            return await save_mood_entry(update, context)
    
    elif update.message and update.message.text:
        # Record the notes text
        context.user_data["notes"] = update.message.text
        return await save_mood_entry(update, context)
    
    return ConversationHandler.END

async def save_mood_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Save the mood entry to the database.
    """
    if update.effective_user:
        user_id = update.effective_user.id
        
        # Get all mood tracking data
        selected_mood = context.user_data.get("selected_mood", "😐")
        mood_value = context.user_data.get("mood_value", "neutral")
        selected_context = context.user_data.get("selected_context", "general_market")
        notes = context.user_data.get("notes", "")
        
        # Log the mood data for debugging
        logger.info(f"Saving mood for user {user_id}: {selected_mood} ({mood_value}) - Context: {selected_context}")
        
        # Save to database
        try:
            from db_utils_mood import save_mood_entry as db_save_mood
            
            db_save_mood(
                user_id=user_id,
                mood=mood_value,
                mood_emoji=selected_mood,
                context=selected_context,
                notes=notes
            )
            
            # Show success message
            reply_text = (
                f"Mood tracked: {selected_mood}\n"
                f"Context: {selected_context.replace('_', ' ').title()}\n"
            )
            
            if notes:
                reply_text += f"Notes: {notes}\n"
                
            reply_text += "\nThank you for tracking your mood! This helps build awareness of how emotions affect your investment decisions."
            
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(reply_text)
            elif update.message:
                await update.message.reply_text(reply_text)
            
            # Ask if user wants to view mood history
            keyboard = [
                [InlineKeyboardButton("View Mood History", callback_data="view_mood_history")],
                [InlineKeyboardButton("Done", callback_data="mood_done")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(
                    "Would you like to view your mood history?",
                    reply_markup=reply_markup
                )
            elif update.message:
                await update.message.reply_text(
                    "Would you like to view your mood history?",
                    reply_markup=reply_markup
                )
                
            return VIEWING_HISTORY
            
        except Exception as e:
            logger.error(f"Error saving mood entry: {e}")
            if update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(
                    "Sorry, there was an error saving your mood. Please try again later."
                )
            elif update.message:
                await update.message.reply_text(
                    "Sorry, there was an error saving your mood. Please try again later."
                )
    
    return ConversationHandler.END

async def view_mood_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Show the user's mood history.
    """
    if update.callback_query and update.callback_query.data:
        query = update.callback_query
        await query.answer()
        
        if query.data == "mood_done":
            await query.message.reply_text("Mood tracking completed. Use /mood anytime to record a new mood entry.")
            return ConversationHandler.END
        
        if query.data == "view_mood_history":
            if update.effective_user:
                user_id = update.effective_user.id
                
                # Get mood history from database
                from db_utils_mood import get_mood_history as db_get_mood_history
                history = db_get_mood_history(user_id, limit=10)
                
                if not history or len(history) == 0:
                    await query.message.reply_text(
                        "You don't have any mood history yet. Use /mood to start tracking!"
                    )
                else:
                    # Format the history for display
                    history_text = "Your recent mood history:\n\n"
                    
                    for entry in history:
                        date = entry.get('timestamp', datetime.now()).strftime("%Y-%m-%d %H:%M")
                        mood_emoji = entry.get('mood_emoji', '😐')
                        context = entry.get('context', 'general').replace('_', ' ').title()
                        notes = entry.get('notes', '')
                        
                        history_text += f"{date}: {mood_emoji} - {context}\n"
                        if notes:
                            history_text += f"  Notes: {notes}\n"
                        history_text += "\n"
                    
                    # Add a simple mood pattern analysis if we have enough entries
                    if len(history) >= 3:
                        history_text += "\nMood pattern insights:\n"
                        
                        # Get detailed mood stats
                        from db_utils_mood import get_mood_stats as db_get_mood_stats
                        mood_stats = db_get_mood_stats(user_id, days=30)
                        
                        # Check for repeated contexts
                        contexts = [entry.get('context') for entry in history]
                        most_common_context = max(set(contexts), key=contexts.count)
                        context_count = contexts.count(most_common_context)
                        
                        if context_count >= 2:
                            history_text += f"• You most frequently record moods during '{most_common_context.replace('_', ' ').title()}' ({context_count} times)\n"
                        
                        # Check for mood trends from stats
                        mood_counts = mood_stats.get('mood_counts', {})
                        
                        negative_moods = sum(mood_counts.get(m, 0) for m in ['anxious', 'sad', 'angry'])
                        if negative_moods > 0:
                            history_text += f"• You've experienced {negative_moods} negative emotions around investing recently\n"
                        
                        positive_moods = sum(mood_counts.get(m, 0) for m in ['very_happy', 'happy'])
                        if positive_moods > 0:
                            history_text += f"• You've had {positive_moods} positive emotions around investing recently\n"
                    
                    # Add a reminder about emotional investing
                    history_text += "\nRemember: Being aware of your emotions can help you make more rational investment decisions!"
                    
                    await query.message.reply_text(history_text)
            
            # Give option to go back to main menu
            keyboard = [[InlineKeyboardButton("Done", callback_data="mood_done")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "Any other actions?",
                reply_markup=reply_markup
            )
            
            return VIEWING_HISTORY
    
    return ConversationHandler.END

def get_mood_tracking_conversation_handler() -> ConversationHandler:
    """
    Return the conversation handler for mood tracking.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("mood", mood_command)],
        states={
            SELECTING_MOOD: [
                CallbackQueryHandler(mood_selected, pattern=r"^mood_")
            ],
            SELECTING_CONTEXT: [
                CallbackQueryHandler(context_selected, pattern=r"^context_")
            ],
            RECORDING_NOTES: [
                CallbackQueryHandler(record_notes, pattern=r"^notes_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, record_notes)
            ],
            VIEWING_HISTORY: [
                CallbackQueryHandler(view_mood_history, pattern=r"^view_mood_history$|^mood_done$")
            ]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        name="mood_tracking_conversation",
        persistent=False
    )