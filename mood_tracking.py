#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Emoji-Based Mood Tracking for Financial Decisions
Helps users track their emotional state when making investment decisions
to improve future financial choices
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import db_utils
from utils import escape_markdown
from models import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_MOOD = 1
ENTERING_NOTES = 2
VIEWING_HISTORY = 3
CONFIRMATION = 4

# Mood options with emojis and sentiment values (negative to positive scale -1.0 to 1.0)
MOOD_OPTIONS = {
    "very_negative": {"emoji": "😡", "label": "Very Negative", "value": -1.0},
    "negative": {"emoji": "😞", "label": "Negative", "value": -0.5},
    "neutral": {"emoji": "😐", "label": "Neutral", "value": 0.0},
    "positive": {"emoji": "😊", "label": "Positive", "value": 0.5},
    "very_positive": {"emoji": "🤩", "label": "Very Positive", "value": 1.0}
}

# Investment types
INVESTMENT_TYPES = {
    "buy": "Buy/Enter Position",
    "sell": "Sell/Exit Position",
    "hold": "Hold/No Action",
    "research": "Just Researching"
}

async def start_mood_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the mood tracking process"""
    try:
        user_id = update.effective_user.id
        
        # Get or create user
        user = db_utils.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username or "",
            first_name=update.effective_user.first_name or "",
            last_name=update.effective_user.last_name or ""
        )
        
        # First ask about the investment type
        keyboard = []
        for inv_type, label in INVESTMENT_TYPES.items():
            keyboard.append([InlineKeyboardButton(label, callback_data=f"invtype_{inv_type}")])
        
        # Add option to view history
        keyboard.append([InlineKeyboardButton("📊 View Mood History", callback_data="view_history")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_mood")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = (
            "🧠 *Financial Mood Tracker* 🧠\n\n"
            "Understanding your emotions when making financial decisions can help improve "
            "future investment choices\\.\n\n"
            "What type of investment decision are you making today?"
        )
        
        await update.effective_message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        
        context.user_data["mood_tracking"] = {}
        return SELECTING_MOOD
        
    except Exception as e:
        logger.error(f"Error starting mood tracking: {e}")
        await update.effective_message.reply_text(
            "Sorry, there was an error starting the mood tracking. Please try again later."
        )
        return ConversationHandler.END

async def handle_investment_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle investment type selection"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in handle_investment_type")
            return ConversationHandler.END
            
        await query.answer()
        
        # Check for view history option
        if query.data == "view_history":
            return await show_mood_history(update, context)
            
        # Check for cancel option
        if query.data == "cancel_mood":
            await query.edit_message_text(
                "Mood tracking cancelled\\. You can track your mood anytime using /mood"
            )
            return ConversationHandler.END
            
        # Extract investment type from callback data
        inv_type = query.data.replace("invtype_", "")
        
        # Validate investment type
        if inv_type not in INVESTMENT_TYPES:
            await query.edit_message_text(
                "Invalid selection. Please try again."
            )
            return ConversationHandler.END
            
        # Store investment type in context
        context.user_data["mood_tracking"]["investment_type"] = inv_type
        context.user_data["mood_tracking"]["investment_label"] = INVESTMENT_TYPES[inv_type]
        
        # Now ask for the mood
        keyboard = []
        for mood_key, mood_data in MOOD_OPTIONS.items():
            button_text = f"{mood_data['emoji']} {mood_data['label']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"mood_{mood_key}")])
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get investment type label
        inv_type_label = escape_markdown(INVESTMENT_TYPES[inv_type])
        
        message_text = (
            f"Decision Type: *{inv_type_label}*\n\n"
            f"How are you feeling about this financial decision?"
        )
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        
        return ENTERING_NOTES
        
    except Exception as e:
        logger.error(f"Error handling investment type: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error processing your selection. Please try again."
            )
        return ConversationHandler.END

async def handle_mood_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle mood selection and prompt for notes"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in handle_mood_selection")
            return ConversationHandler.END
            
        await query.answer()
        
        # Extract mood from callback data
        mood_key = query.data.replace("mood_", "")
        
        # Validate mood
        if mood_key not in MOOD_OPTIONS:
            await query.edit_message_text(
                "Invalid mood selection. Please try again."
            )
            return ConversationHandler.END
            
        # Store mood data in context
        mood_data = MOOD_OPTIONS[mood_key]
        context.user_data["mood_tracking"]["mood_key"] = mood_key
        context.user_data["mood_tracking"]["mood_emoji"] = mood_data["emoji"]
        context.user_data["mood_tracking"]["mood_label"] = mood_data["label"]
        context.user_data["mood_tracking"]["mood_value"] = mood_data["value"]
        context.user_data["mood_tracking"]["timestamp"] = datetime.now().isoformat()
        
        # Get stored data
        inv_type_label = escape_markdown(context.user_data["mood_tracking"]["investment_label"])
        mood_emoji = mood_data["emoji"]
        mood_label = escape_markdown(mood_data["label"])
        
        message_text = (
            f"Decision Type: *{inv_type_label}*\n"
            f"Current Mood: {mood_emoji} *{mood_label}*\n\n"
            f"Would you like to add notes about why you feel this way? If so, please type them now\\.\n"
            f"Or click 'Skip Notes' to finish\\."
        )
        
        # Create keyboard with skip option
        keyboard = [[InlineKeyboardButton("⏩ Skip Notes", callback_data="skip_notes")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        
        return CONFIRMATION
        
    except Exception as e:
        logger.error(f"Error handling mood selection: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error processing your mood selection. Please try again."
            )
        return ConversationHandler.END

async def handle_notes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user notes or skipping notes"""
    try:
        # Check if user clicked skip
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            if query.data == "skip_notes":
                context.user_data["mood_tracking"]["notes"] = ""
                return await save_mood_data(update, context)
        
        # Otherwise, process the text message as notes
        if update.effective_message and update.effective_message.text:
            notes = update.effective_message.text.strip()
            context.user_data["mood_tracking"]["notes"] = notes
            
            # Create confirmation keyboard
            keyboard = [
                [InlineKeyboardButton("✅ Save", callback_data="save_mood")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_mood")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Get stored data
            inv_type_label = escape_markdown(context.user_data["mood_tracking"]["investment_label"])
            mood_emoji = context.user_data["mood_tracking"]["mood_emoji"]
            mood_label = escape_markdown(context.user_data["mood_tracking"]["mood_label"])
            escaped_notes = escape_markdown(notes)
            
            message_text = (
                f"Decision Type: *{inv_type_label}*\n"
                f"Current Mood: {mood_emoji} *{mood_label}*\n"
                f"Notes: _{escaped_notes}_\n\n"
                f"Would you like to save this mood entry?"
            )
            
            await update.effective_message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
            
            return CONFIRMATION
            
        # If we get here, something went wrong
        await update.effective_message.reply_text(
            "Sorry, I couldn't understand your notes. Please try again or click 'Skip Notes'."
        )
        return CONFIRMATION
        
    except Exception as e:
        logger.error(f"Error handling notes: {e}")
        await update.effective_message.reply_text(
            "Sorry, there was an error processing your notes. Please try again."
        )
        return ConversationHandler.END

async def save_mood_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save mood data to database"""
    try:
        query = None
        
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            
            if query.data == "cancel_mood":
                await query.edit_message_text(
                    "Mood tracking cancelled\\. You can track your mood anytime using /mood",
                    parse_mode="MarkdownV2"
                )
                return ConversationHandler.END
        
        user_id = update.effective_user.id
        mood_data = context.user_data.get("mood_tracking", {})
        
        # Save to database
        try:
            # Create a data dictionary for database storage
            mood_entry = {
                "user_id": user_id,
                "timestamp": mood_data.get("timestamp", datetime.now().isoformat()),
                "investment_type": mood_data.get("investment_type", "unknown"),
                "mood_key": mood_data.get("mood_key", "neutral"),
                "mood_value": mood_data.get("mood_value", 0.0),
                "notes": mood_data.get("notes", "")
            }
            
            # Use db_utils to save mood entry
            await db_utils.save_mood_entry(mood_entry)
            
            success_message = (
                f"✅ Mood tracked successfully\\!\n\n"
                f"Type: *{escape_markdown(mood_data.get('investment_label', 'Unknown'))}*\n"
                f"Mood: {mood_data.get('mood_emoji', '😐')} *{escape_markdown(mood_data.get('mood_label', 'Neutral'))}*\n"
            )
            
            if mood_data.get("notes"):
                success_message += f"Notes: _{escape_markdown(mood_data.get('notes', ''))}\\.\n_"
                
            success_message += (
                f"\nThank you for tracking your mood\\! This helps build awareness of "
                f"emotional patterns in your financial decisions\\.\n\n"
                f"Use /mood anytime to track more entries or view your history\\."
            )
            
            if query:
                await query.edit_message_text(
                    success_message,
                    parse_mode="MarkdownV2"
                )
            else:
                await update.effective_message.reply_text(
                    success_message,
                    parse_mode="MarkdownV2"
                )
                
        except Exception as db_error:
            logger.error(f"Database error saving mood: {db_error}")
            error_message = "Sorry, there was an error saving your mood data. Please try again later."
            
            if query:
                await query.edit_message_text(error_message)
            else:
                await update.effective_message.reply_text(error_message)
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in save_mood_data: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error saving your mood data. Please try again later."
            )
        elif update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, there was an error saving your mood data. Please try again later."
            )
        return ConversationHandler.END

async def show_mood_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show mood history for the user"""
    try:
        user_id = update.effective_user.id
        
        # Query for mood history
        mood_history = await db_utils.get_mood_history(user_id)
        
        if not mood_history or len(mood_history) == 0:
            # No history found
            message_text = (
                "You don't have any mood entries yet\\.\n\n"
                "Start tracking your moods during financial decisions to build your history\\."
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    message_text,
                    parse_mode="MarkdownV2"
                )
            else:
                await update.effective_message.reply_text(
                    message_text,
                    parse_mode="MarkdownV2"
                )
                
            return ConversationHandler.END
            
        # Format mood history
        message_text = "📊 *Your Financial Mood History* 📊\n\n"
        
        # Process the most recent 10 entries
        for entry in mood_history[:10]:
            entry_date = datetime.fromisoformat(entry.get("timestamp")).strftime("%b %d, %Y %H:%M")
            mood_key = entry.get("mood_key", "neutral")
            mood_emoji = MOOD_OPTIONS.get(mood_key, {}).get("emoji", "😐")
            mood_label = MOOD_OPTIONS.get(mood_key, {}).get("label", "Neutral")
            inv_type = entry.get("investment_type", "unknown")
            inv_label = INVESTMENT_TYPES.get(inv_type, "Unknown")
            
            message_text += (
                f"*{escape_markdown(entry_date)}*\n"
                f"{mood_emoji} *{escape_markdown(mood_label)}* | {escape_markdown(inv_label)}\n"
            )
            
            if entry.get("notes"):
                message_text += f"_{escape_markdown(entry.get('notes', '')[:50])}";
                if len(entry.get("notes", "")) > 50:
                    message_text += "\\.\\.\\."
                message_text += "_\n"
                
            message_text += "\n"
            
        # Add summary statistics if enough entries
        if len(mood_history) >= 3:
            # Calculate average mood value
            total_value = sum(entry.get("mood_value", 0.0) for entry in mood_history)
            avg_value = total_value / len(mood_history)
            
            # Determine most common mood
            mood_counts = {}
            for entry in mood_history:
                mood_key = entry.get("mood_key", "neutral")
                mood_counts[mood_key] = mood_counts.get(mood_key, 0) + 1
                
            most_common_mood = max(mood_counts.items(), key=lambda x: x[1])[0]
            common_emoji = MOOD_OPTIONS.get(most_common_mood, {}).get("emoji", "😐")
            common_label = MOOD_OPTIONS.get(most_common_mood, {}).get("label", "Neutral")
            
            # Add summary
            message_text += (
                f"*Summary Stats:*\n"
                f"Total Entries: *{len(mood_history)}*\n"
                f"Average Mood: *{avg_value:.2f}*\n"
                f"Most Common: {common_emoji} *{escape_markdown(common_label)}*\n\n"
            )
            
        message_text += "Use /mood to track a new mood entry."
        
        # Create return keyboard
        keyboard = [[InlineKeyboardButton("↩️ Back to Mood Tracking", callback_data="back_to_mood")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
        else:
            await update.effective_message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
            
        return VIEWING_HISTORY
        
    except Exception as e:
        logger.error(f"Error showing mood history: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error retrieving your mood history. Please try again later."
            )
        elif update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, there was an error retrieving your mood history. Please try again later."
            )
        return ConversationHandler.END

async def handle_history_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle navigation from history view"""
    try:
        query = update.callback_query
        if not query:
            return ConversationHandler.END
            
        await query.answer()
        
        if query.data == "back_to_mood":
            return await start_mood_tracking(update, context)
            
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error in history navigation: {e}")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.effective_message.reply_text(
        "Mood tracking cancelled\\. You can track your mood anytime using /mood",
        parse_mode="MarkdownV2"
    )
    return ConversationHandler.END

async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Entry point for the /mood command"""
    await start_mood_tracking(update, context)

# Setup conversation handler (to be imported and used in main.py)
def get_mood_tracking_conversation_handler():
    """Return a conversation handler for the mood tracking flow"""
    from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    return ConversationHandler(
        entry_points=[CommandHandler("mood", mood_command)],
        states={
            SELECTING_MOOD: [
                CallbackQueryHandler(handle_investment_type, pattern=r"^invtype_"),
                CallbackQueryHandler(show_mood_history, pattern=r"^view_history$"),
                CallbackQueryHandler(cancel, pattern=r"^cancel_mood$")
            ],
            ENTERING_NOTES: [
                CallbackQueryHandler(handle_mood_selection, pattern=r"^mood_")
            ],
            CONFIRMATION: [
                CallbackQueryHandler(save_mood_data, pattern=r"^(save_mood|skip_notes)$"),
                CallbackQueryHandler(cancel, pattern=r"^cancel_mood$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_notes)
            ],
            VIEWING_HISTORY: [
                CallbackQueryHandler(handle_history_navigation, pattern=r"^back_to_mood$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )