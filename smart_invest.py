#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Smart investment module for the FiLot Telegram bot
Provides AI-powered investment recommendations using Reinforcement Learning
"""

import logging
import time
import asyncio
import traceback
import os
from typing import Dict, List, Any, Optional, Union, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import rl_investment_advisor
import db_utils
from models import User, db
from utils import format_number, escape_markdown
from anti_loop import record_user_message, is_potential_loop

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine if in production mode
IS_PRODUCTION = os.environ.get("ENVIRONMENT", "development").lower() == "production"

# Conversation states
AMOUNT = 1
RISK_PROFILE = 2
TOKEN_PREFERENCE = 3
CONFIRMATION = 4
FEEDBACK = 5

# Risk profile options
RISK_PROFILES = {
    "conservative": "Conservative (lower risk, stable returns)",
    "moderate": "Moderate (balanced risk and returns)",
    "aggressive": "Aggressive (higher risk, higher potential returns)"
}

async def start_smart_invest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the smart investment process with AI-powered recommendations"""
    try:
        user_id = update.effective_user.id
        
        # Check for message loop/spam
        if update.effective_message and update.effective_message.text:
            record_user_message(user_id, update.effective_message.text)
            if is_potential_loop(user_id, update.effective_message.text):
                await update.effective_message.reply_text(
                    "I noticed you're sending the same message repeatedly. "
                    "Please let me know how I can help you differently."
                )
                return ConversationHandler.END
                
        # Get or create user
        user = db_utils.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username or "",
            first_name=update.effective_user.first_name or "",
            last_name=update.effective_user.last_name or ""
        )
        
        # Welcome message with proper escaped markdown
        welcome_text = (
            "🤖 *Smart Investment Advisor* 🤖\n\n"
            "I'll use advanced AI to recommend the best liquidity pools for your investment\\.\n\n"
            "Let's start with how much you'd like to invest \\(in USD\\)\\.\n"
            "Example: `100` for $100"
        )
        
        await update.effective_message.reply_text(
            welcome_text,
            parse_mode="MarkdownV2"
        )
        
        return AMOUNT
    except Exception as e:
        logger.error(f"Error starting smart investment: {e}")
        if update.effective_message:
            error_msg = "Sorry, there was an error starting the smart investment process. Please try again later."
            if not IS_PRODUCTION:
                error_msg += f"\n\nDebug info: {str(e)}"
            await update.effective_message.reply_text(error_msg)
        return ConversationHandler.END

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the investment amount input"""
    try:
        text = update.effective_message.text.strip()
        
        # Try to convert to float
        try:
            amount = float(text.replace('$', '').replace(',', ''))
            
            # Validate amount
            if amount <= 0:
                await update.effective_message.reply_text(
                    "Please enter a positive amount."
                )
                return AMOUNT
                
            if amount < 10:
                await update.effective_message.reply_text(
                    "The minimum investment amount is $10. Please enter a larger amount."
                )
                return AMOUNT
                
            if amount > 1000000:
                await update.effective_message.reply_text(
                    "The maximum investment amount for this simulation is $1,000,000. "
                    "Please enter a smaller amount."
                )
                return AMOUNT
                
            # Store the amount in context
            context.user_data["investment_amount"] = amount
            
            # Ask for risk profile
            keyboard = [
                [InlineKeyboardButton(RISK_PROFILES["conservative"], callback_data="risk_conservative")],
                [InlineKeyboardButton(RISK_PROFILES["moderate"], callback_data="risk_moderate")],
                [InlineKeyboardButton(RISK_PROFILES["aggressive"], callback_data="risk_aggressive")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Format the amount with proper escaping
            amount_str = f"${format_number(amount)}"
            formatted_amount = escape_markdown(amount_str)
            
            message_text = f"Investment amount: *{formatted_amount}*\n\nPlease select your risk profile:"
            
            await update.effective_message.reply_text(
                message_text,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
            
            return RISK_PROFILE
            
        except ValueError:
            invalid_message = (
                "Please enter a valid number for the investment amount\\.\n"
                "Example: `100` for $100"
            )
            
            await update.effective_message.reply_text(
                invalid_message,
                parse_mode="MarkdownV2"
            )
            return AMOUNT
            
    except Exception as e:
        logger.error(f"Error handling investment amount: {e}")
        error_msg = "Sorry, there was an error processing your input. Please try again."
        if not IS_PRODUCTION:
            error_msg += f"\n\nDebug info: {str(e)}"
        await update.effective_message.reply_text(error_msg)
        return AMOUNT

async def handle_risk_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the risk profile selection"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in handle_risk_profile")
            return ConversationHandler.END
            
        await query.answer()
        
        # Extract risk profile from callback data
        risk_profile = query.data.replace("risk_", "")
        
        # Validate risk profile
        if risk_profile not in RISK_PROFILES:
            await query.edit_message_text(
                "Invalid risk profile. Please restart the process."
            )
            return ConversationHandler.END
            
        # Store risk profile in context
        context.user_data["risk_profile"] = risk_profile
        
        # Get the display name of the risk profile
        risk_profile_display = escape_markdown(RISK_PROFILES[risk_profile])
        
        # Ask for token preference
        keyboard = [
            [InlineKeyboardButton("No preference", callback_data="token_none")],
            [InlineKeyboardButton("SOL", callback_data="token_SOL")],
            [InlineKeyboardButton("USDC", callback_data="token_USDC")],
            [InlineKeyboardButton("BONK", callback_data="token_BONK")],
            [InlineKeyboardButton("JTO", callback_data="token_JTO")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format the amount with proper escaping
        amount = context.user_data.get("investment_amount", 0)
        amount_str = f"${format_number(amount)}"
        formatted_amount = escape_markdown(amount_str)
        
        message_text = (
            f"Investment amount: *{formatted_amount}*\n"
            f"Risk profile: *{risk_profile_display}*\n\n"
            f"Select a preferred token \\(optional\\):"
        )
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        
        return TOKEN_PREFERENCE
        
    except Exception as e:
        logger.error(f"Error handling risk profile: {e}")
        error_msg = "Sorry, there was an error processing your selection. Please try again."
        if not IS_PRODUCTION:
            error_msg += f"\n\nDebug info: {str(e)}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return ConversationHandler.END

async def handle_token_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle token preference selection"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in handle_token_preference")
            return ConversationHandler.END
            
        await query.answer()
        
        # Extract token preference from callback data
        token_pref = query.data.replace("token_", "")
        
        # If "none" was selected, set to None
        if token_pref.lower() == "none":
            token_pref = None
            token_display = "No specific token"
        else:
            token_display = token_pref
            
        # Store token preference in context
        context.user_data["token_preference"] = token_pref
        
        # Get values from context
        amount = context.user_data.get("investment_amount", 0)
        risk_profile = context.user_data.get("risk_profile", "moderate")
        risk_profile_display = RISK_PROFILES[risk_profile]
        
        # Confirm details
        keyboard = [
            [InlineKeyboardButton("Get AI Recommendations", callback_data="confirm_smart_invest")],
            [InlineKeyboardButton("Cancel", callback_data="cancel_smart_invest")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Format all values with proper escaping
        amount_str = f"${format_number(amount)}"
        formatted_amount = escape_markdown(amount_str)
        escaped_risk_profile = escape_markdown(risk_profile_display)
        escaped_token_display = escape_markdown(token_display)
        
        message_text = (
            f"📊 *Smart Investment Details* 📊\n\n"
            f"Amount: *{formatted_amount}*\n"
            f"Risk profile: *{escaped_risk_profile}*\n"
            f"Token preference: *{escaped_token_display}*\n\n"
            f"Ready to see AI\\-powered investment recommendations?"
        )
        
        await query.edit_message_text(
            message_text,
            reply_markup=reply_markup,
            parse_mode="MarkdownV2"
        )
        
        return CONFIRMATION
        
    except Exception as e:
        logger.error(f"Error handling token preference: {e}")
        error_msg = "Sorry, there was an error processing your selection. Please try again."
        if not IS_PRODUCTION:
            error_msg += f"\n\nDebug info: {str(e)}"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return ConversationHandler.END

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the confirmation and provide smart investment recommendations"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in handle_confirmation")
            return ConversationHandler.END
            
        await query.answer()
        
        # Check if cancelled
        if query.data == "cancel_smart_invest":
            await query.edit_message_text(
                "Smart investment process cancelled\\. Feel free to start again when you're ready\\.",
                parse_mode="MarkdownV2"
            )
            return ConversationHandler.END
            
        # Show loading message
        loading_text = (
            "🔍 *Analyzing investment opportunities\\.\\.\\.*\n\n"
            "Our AI is crunching the numbers to find the best pools for your investment\\. "
            "This may take a few moments\\."
        )
        
        await query.edit_message_text(
            loading_text,
            parse_mode="MarkdownV2"
        )
        
        # Get parameters from context
        amount = context.user_data.get("investment_amount", 0)
        risk_profile = context.user_data.get("risk_profile", "moderate")
        token_preference = context.user_data.get("token_preference")
        
        try:
            # Generate RL-powered recommendations using executor to avoid blocking
            loop = asyncio.get_event_loop()
            recommendations = await loop.run_in_executor(
                None,
                lambda: rl_investment_advisor.get_smart_investment_recommendation(
                    investment_amount=amount,
                    risk_profile=risk_profile,
                    token_preference=token_preference,
                    max_suggestions=3
                )
            )
            
            # Store recommendations in context
            context.user_data["recommendations"] = recommendations
            
            # Check if we have suggestions
            if not recommendations.get("suggestions") or len(recommendations["suggestions"]) == 0:
                no_results_text = (
                    "Sorry, I couldn't find any suitable investment opportunities matching your criteria\\. "
                    "Please try again with different parameters\\."
                )
                
                await query.edit_message_text(
                    no_results_text,
                    parse_mode="MarkdownV2"
                )
                return ConversationHandler.END
                
            # Format the recommendations
            message = "🤖 *AI\\-Powered Investment Recommendations* 🤖\n\n"
            
            # Add explanation
            explanation = recommendations.get('explanation', 'Based on your preferences, here are my recommendations:')
            message += escape_markdown(explanation) + "\n\n"
            
            # Add each suggestion
            for i, pool in enumerate(recommendations["suggestions"], 1):
                confidence = pool.get("confidence", 0) * 100
                confidence_display = f"{confidence:.1f}%" if confidence > 0 else "N/A"
                
                pair = pool.get('pair', 'Unknown')
                apr = pool.get('apr', 0.0)
                tvl = pool.get('tvl', 0.0)
                
                apr_str = f"{apr:.2f}%"
                tvl_str = f"${format_number(tvl)}"
                
                pool_info = (
                    f"*{i}\\. {escape_markdown(pair)}*\n"
                    f"• APR: {escape_markdown(apr_str)}\n"
                    f"• TVL: {escape_markdown(tvl_str)}\n"
                    f"• AI Confidence: {escape_markdown(confidence_display)}\n"
                )
                
                message += pool_info
                
                # Add reasons if available
                if pool.get("reasons") and len(pool["reasons"]) > 0:
                    reasons_list = [escape_markdown(reason) for reason in pool["reasons"]]
                    escaped_reasons = ", ".join(reasons_list)
                    message += f"• Reasons: {escaped_reasons}\n"
                    
                message += "\n"
                
            # Add powered by note    
            if recommendations.get("rl_powered", False):
                message += "🧠 _Powered by Reinforcement Learning AI_\n\n"
            
            # Add feedback options
            keyboard = [
                [InlineKeyboardButton("👍 Helpful", callback_data="feedback_helpful")],
                [InlineKeyboardButton("👎 Not helpful", callback_data="feedback_not_helpful")],
                [InlineKeyboardButton("🔄 Try different parameters", callback_data="feedback_try_again")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode="MarkdownV2"
            )
            
            return FEEDBACK
            
        except Exception as ai_error:
            logger.error(f"Error in AI recommendation: {ai_error}")
            error_msg = (
                "Sorry, there was an error generating investment recommendations. "
                "This could be due to API connectivity issues. Please try again later."
            )
            if not IS_PRODUCTION:
                error_msg += f"\n\nDebug info: {str(ai_error)}"
                
            await query.edit_message_text(error_msg)
            return ConversationHandler.END
            
    except Exception as e:
        logger.error(f"Error handling confirmation: {e}")
        error_msg = (
            "Sorry, there was an error processing your request. "
            "Please try again later."
        )
        if not IS_PRODUCTION:
            error_msg += f"\n\nDebug info: {str(e)}"
            
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return ConversationHandler.END

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user feedback on the recommendations"""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in handle_feedback")
            return ConversationHandler.END
            
        await query.answer()
        
        feedback = query.data.replace("feedback_", "")
        
        if feedback == "helpful":
            # Record positive feedback for RL training
            user_id = update.effective_user.id
            
            # Get first recommended pool for simple feedback
            recs = context.user_data.get("recommendations", {})
            suggestions = recs.get("suggestions", [])
            
            if suggestions and len(suggestions) > 0:
                top_pool = suggestions[0]
                if "pool_id" in top_pool:
                    try:
                        # Record a high rating (4/5) for helpful feedback
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None,
                            lambda: rl_investment_advisor.feedback_smart_investment(user_id, top_pool["pool_id"], rating=4)
                        )
                    except Exception as feedback_error:
                        logger.error(f"Error recording positive feedback: {feedback_error}")
            
            positive_text = (
                "Thank you for your feedback\\! I'm glad the recommendations were helpful\\.\n\n"
                "You can use /smart\\_invest anytime to get more AI\\-powered recommendations\\."
            )
            
            await query.edit_message_text(
                positive_text,
                parse_mode="MarkdownV2"
            )
            
        elif feedback == "not_helpful":
            # Record negative feedback for RL training
            user_id = update.effective_user.id
            
            # Get first recommended pool for simple feedback
            recs = context.user_data.get("recommendations", {})
            suggestions = recs.get("suggestions", [])
            
            if suggestions and len(suggestions) > 0:
                top_pool = suggestions[0]
                if "pool_id" in top_pool:
                    try:
                        # Record a low rating (2/5) for unhelpful feedback
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(
                            None,
                            lambda: rl_investment_advisor.feedback_smart_investment(user_id, top_pool["pool_id"], rating=2)
                        )
                    except Exception as feedback_error:
                        logger.error(f"Error recording negative feedback: {feedback_error}")
            
            negative_text = (
                "I appreciate your feedback\\. I'll use it to improve future recommendations\\.\n\n"
                "You can use /smart\\_invest anytime to try again with different parameters\\."
            )
            
            await query.edit_message_text(
                negative_text,
                parse_mode="MarkdownV2"
            )
            
        elif feedback == "try_again":
            retry_text = (
                "Sure, let's try again with different parameters\\.\n\n"
                "Please use /smart\\_invest to start a new recommendation session\\."
            )
            
            await query.edit_message_text(
                retry_text,
                parse_mode="MarkdownV2"
            )
            
        else:
            default_text = (
                "Thank you for using the Smart Investment Advisor\\.\n\n"
                "You can use /smart\\_invest anytime to get more AI\\-powered recommendations\\."
            )
            
            await query.edit_message_text(
                default_text,
                parse_mode="MarkdownV2"
            )
            
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")
        error_msg = (
            "Sorry, there was an error processing your feedback. "
            "You can use /smart_invest anytime to get more recommendations."
        )
        if not IS_PRODUCTION:
            error_msg += f"\n\nDebug info: {str(e)}"
            
        if update.callback_query:
            await update.callback_query.edit_message_text(error_msg)
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    cancel_text = (
        "Smart investment process cancelled\\. Feel free to start again when you're ready\\."
    )
    
    await update.effective_message.reply_text(
        cancel_text,
        parse_mode="MarkdownV2"
    )
    return ConversationHandler.END

async def smart_invest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Entry point for the /smart_invest command"""
    await start_smart_invest(update, context)

# Setup conversation handler (to be imported and used in main.py)
def get_smart_invest_conversation_handler():
    """Return a conversation handler for the smart invest flow"""
    from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
    
    return ConversationHandler(
        entry_points=[CommandHandler("smart_invest", smart_invest_command)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            RISK_PROFILE: [CallbackQueryHandler(handle_risk_profile, pattern=r"^risk_(conservative|moderate|aggressive)$")],
            TOKEN_PREFERENCE: [CallbackQueryHandler(handle_token_preference, pattern=r"^token_(none|SOL|USDC|BONK|JTO)$")],
            CONFIRMATION: [CallbackQueryHandler(handle_confirmation, pattern=r"^(confirm|cancel)_smart_invest$")],
            FEEDBACK: [CallbackQueryHandler(handle_feedback, pattern=r"^feedback_(helpful|not_helpful|try_again)$")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )