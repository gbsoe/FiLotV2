"""
Smart investment module for the FiLot Telegram bot
Provides AI-powered investment recommendations using Reinforcement Learning
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

import rl_investment_advisor
import db_utils
from models import User, db
from utils import format_number
from anti_loop import record_user_message, is_potential_loop

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        if update.message and update.message.text:
            record_user_message(user_id, update.message.text)
            if is_potential_loop(user_id, update.message.text):
                await update.message.reply_text(
                    "I noticed you're sending the same message repeatedly. "
                    "Please let me know how I can help you differently."
                )
                return ConversationHandler.END
                
        # Get or create user
        user = db_utils.get_or_create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
        
        # Welcome message
        await update.message.reply_text(
            "🤖 *Smart Investment Advisor* 🤖\n\n"
            "I'll use advanced AI to recommend the best liquidity pools for your investment.\n\n"
            "Let's start with how much you'd like to invest (in USD).\n"
            "Example: `100` for $100",
            parse_mode="Markdown"
        )
        
        return AMOUNT
    except Exception as e:
        logger.error(f"Error starting smart investment: {e}")
        if update.message:
            await update.message.reply_text(
                "Sorry, there was an error starting the smart investment process. Please try again later."
            )
        return ConversationHandler.END

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the investment amount input"""
    try:
        text = update.message.text.strip()
        
        # Try to convert to float
        try:
            amount = float(text.replace('$', '').replace(',', ''))
            
            # Validate amount
            if amount <= 0:
                await update.message.reply_text(
                    "Please enter a positive amount."
                )
                return AMOUNT
                
            if amount < 10:
                await update.message.reply_text(
                    "The minimum investment amount is $10. Please enter a larger amount."
                )
                return AMOUNT
                
            if amount > 1000000:
                await update.message.reply_text(
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
            
            await update.message.reply_text(
                f"Investment amount: *${format_number(amount)}*\n\n"
                f"Please select your risk profile:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            
            return RISK_PROFILE
            
        except ValueError:
            await update.message.reply_text(
                "Please enter a valid number for the investment amount.\n"
                "Example: `100` for $100"
            )
            return AMOUNT
            
    except Exception as e:
        logger.error(f"Error handling investment amount: {e}")
        await update.message.reply_text(
            "Sorry, there was an error processing your input. Please try again."
        )
        return AMOUNT

async def handle_risk_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the risk profile selection"""
    try:
        query = update.callback_query
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
        risk_profile_display = RISK_PROFILES[risk_profile]
        
        # Ask for token preference
        keyboard = [
            [InlineKeyboardButton("No preference", callback_data="token_none")],
            [InlineKeyboardButton("SOL", callback_data="token_SOL")],
            [InlineKeyboardButton("USDC", callback_data="token_USDC")],
            [InlineKeyboardButton("BONK", callback_data="token_BONK")],
            [InlineKeyboardButton("JTO", callback_data="token_JTO")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Investment amount: *${format_number(context.user_data['investment_amount'])}*\n"
            f"Risk profile: *{risk_profile_display}*\n\n"
            f"Select a preferred token (optional):",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return TOKEN_PREFERENCE
        
    except Exception as e:
        logger.error(f"Error handling risk profile: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error processing your selection. Please try again."
            )
        return ConversationHandler.END

async def handle_token_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle token preference selection"""
    try:
        query = update.callback_query
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
        amount = context.user_data["investment_amount"]
        risk_profile = context.user_data["risk_profile"]
        risk_profile_display = RISK_PROFILES[risk_profile]
        
        # Confirm details
        keyboard = [
            [InlineKeyboardButton("Get AI Recommendations", callback_data="confirm_smart_invest")],
            [InlineKeyboardButton("Cancel", callback_data="cancel_smart_invest")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📊 *Smart Investment Details* 📊\n\n"
            f"Amount: *${format_number(amount)}*\n"
            f"Risk profile: *{risk_profile_display}*\n"
            f"Token preference: *{token_display}*\n\n"
            f"Ready to see AI-powered investment recommendations?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        
        return CONFIRMATION
        
    except Exception as e:
        logger.error(f"Error handling token preference: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error processing your selection. Please try again."
            )
        return ConversationHandler.END

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the confirmation and provide smart investment recommendations"""
    try:
        query = update.callback_query
        await query.answer()
        
        # Check if cancelled
        if query.data == "cancel_smart_invest":
            await query.edit_message_text(
                "Smart investment process cancelled. Feel free to start again when you're ready."
            )
            return ConversationHandler.END
            
        # Show loading message
        await query.edit_message_text(
            "🔍 *Analyzing investment opportunities...*\n\n"
            "Our AI is crunching the numbers to find the best pools for your investment. "
            "This may take a few moments.",
            parse_mode="Markdown"
        )
        
        # Get parameters from context
        amount = context.user_data["investment_amount"]
        risk_profile = context.user_data["risk_profile"]
        token_preference = context.user_data.get("token_preference")
        
        # Generate RL-powered recommendations
        recommendations = rl_investment_advisor.get_smart_investment_recommendation(
            investment_amount=amount,
            risk_profile=risk_profile,
            token_preference=token_preference,
            max_suggestions=3
        )
        
        # Store recommendations in context
        context.user_data["recommendations"] = recommendations
        
        # Check if we have suggestions
        if not recommendations.get("suggestions") or len(recommendations["suggestions"]) == 0:
            await query.edit_message_text(
                "Sorry, I couldn't find any suitable investment opportunities matching your criteria. "
                "Please try again with different parameters.",
                parse_mode="Markdown"
            )
            return ConversationHandler.END
            
        # Format the recommendations
        message = f"🤖 *AI-Powered Investment Recommendations* 🤖\n\n"
        
        # Add explanation
        message += f"{recommendations.get('explanation', 'Based on your preferences, here are my recommendations:')}\n\n"
        
        # Add each suggestion
        for i, pool in enumerate(recommendations["suggestions"], 1):
            confidence = pool.get("confidence", 0) * 100
            confidence_display = f"{confidence:.1f}%" if confidence > 0 else "N/A"
            
            message += (
                f"*{i}. {pool['pair']}*\n"
                f"• APR: {pool['apr']:.2f}%\n"
                f"• TVL: ${format_number(pool['tvl'])}\n"
                f"• AI Confidence: {confidence_display}\n"
            )
            
            # Add reasons if available
            if pool.get("reasons") and len(pool["reasons"]) > 0:
                message += f"• Reasons: {', '.join(pool['reasons'])}\n"
                
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
            parse_mode="Markdown"
        )
        
        return FEEDBACK
        
    except Exception as e:
        logger.error(f"Error generating smart investment recommendations: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error generating investment recommendations. "
                "This could be due to API connectivity issues. Please try again later."
            )
        return ConversationHandler.END

async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle user feedback on the recommendations"""
    try:
        query = update.callback_query
        await query.answer()
        
        feedback = query.data.replace("feedback_", "")
        
        if feedback == "helpful":
            # Record positive feedback for RL training
            user_id = update.effective_user.id
            
            # Get first recommended pool for simple feedback
            if context.user_data.get("recommendations") and context.user_data["recommendations"].get("suggestions"):
                top_pool = context.user_data["recommendations"]["suggestions"][0]
                if "pool_id" in top_pool:
                    # Record a high rating (4/5) for helpful feedback
                    rl_investment_advisor.feedback_smart_investment(user_id, top_pool["pool_id"], rating=4)
            
            await query.edit_message_text(
                "Thank you for your feedback! I'm glad the recommendations were helpful.\n\n"
                "You can use /smart_invest anytime to get more AI-powered recommendations.",
                parse_mode="Markdown"
            )
            
        elif feedback == "not_helpful":
            # Record negative feedback for RL training
            user_id = update.effective_user.id
            
            # Get first recommended pool for simple feedback
            if context.user_data.get("recommendations") and context.user_data["recommendations"].get("suggestions"):
                top_pool = context.user_data["recommendations"]["suggestions"][0]
                if "pool_id" in top_pool:
                    # Record a low rating (2/5) for unhelpful feedback
                    rl_investment_advisor.feedback_smart_investment(user_id, top_pool["pool_id"], rating=2)
            
            await query.edit_message_text(
                "I appreciate your feedback. I'll use it to improve future recommendations.\n\n"
                "You can use /smart_invest anytime to try again with different parameters.",
                parse_mode="Markdown"
            )
            
        elif feedback == "try_again":
            await query.edit_message_text(
                "Sure, let's try again with different parameters.\n\n"
                "Please use /smart_invest to start a new recommendation session.",
                parse_mode="Markdown"
            )
            
        else:
            await query.edit_message_text(
                "Thank you for using the Smart Investment Advisor.\n\n"
                "You can use /smart_invest anytime to get more AI-powered recommendations.",
                parse_mode="Markdown"
            )
            
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error handling feedback: {e}")
        if update.callback_query:
            await update.callback_query.edit_message_text(
                "Sorry, there was an error processing your feedback. "
                "You can use /smart_invest anytime to get more recommendations."
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
            RISK_PROFILE: [CallbackQueryHandler(handle_risk_profile, pattern=r"^risk_")],
            TOKEN_PREFERENCE: [CallbackQueryHandler(handle_token_preference, pattern=r"^token_")],
            CONFIRMATION: [CallbackQueryHandler(handle_confirmation, pattern=r"^(confirm|cancel)_smart_invest$")],
            FEEDBACK: [CallbackQueryHandler(handle_feedback, pattern=r"^feedback_")]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )