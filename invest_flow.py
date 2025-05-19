#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Investment flow for FiLot Telegram bot
Implements the one-command invest flow with slot-filling conversation
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple, Union

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import agentic_advisor
from models import db, User, Pool
from app import app

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# User state constants
AWAITING_AMOUNT = "awaiting_amount"
AWAITING_RISK_PROFILE = "awaiting_risk_profile"
AWAITING_TOKEN_PREFERENCE = "awaiting_token_preference"
AWAITING_CONFIRMATION = "awaiting_confirmation"
COMPLETED = "completed"

# Define persistent keyboard
MAIN_KEYBOARD = ReplyKeyboardMarkup(
    [["💰 Invest"], ["🔍 Explore", "👤 Account"]],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Risk profile keyboards
RISK_PROFILE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🟢 Conservative", callback_data="risk_conservative")],
    [InlineKeyboardButton("🟡 Moderate", callback_data="risk_moderate")],
    [InlineKeyboardButton("🔴 Aggressive", callback_data="risk_aggressive")]
])

# Token preference keyboards (common tokens)
TOKEN_PREFERENCE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("SOL", callback_data="token_SOL"), 
     InlineKeyboardButton("USDC", callback_data="token_USDC")],
    [InlineKeyboardButton("BONK", callback_data="token_BONK"), 
     InlineKeyboardButton("JTO", callback_data="token_JTO")],
    [InlineKeyboardButton("No Preference", callback_data="token_none")]
])

# User context storage (in-memory for now, could be moved to database)
user_investment_context = {}

async def start_invest_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start the investment flow conversation
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    user_id = update.effective_user.id if update.effective_user else 0
    logger.info(f"Starting investment flow for user {user_id}")
    
    # Initialize user context
    user_investment_context[user_id] = {
        "state": AWAITING_AMOUNT,
        "amount": None,
        "risk_profile": None,
        "token_preference": None,
        "recommendation": None,
        "selected_pool": None
    }
    
    # Ask for investment amount
    message = (
        "*🚀 FiLot Investment Assistant*\n\n"
        "I'll help you select the best liquidity pools for your investment.\n\n"
        "*Step 1:* How much would you like to invest (in USD)?\n\n"
        "Example: 100, 500, 1000"
    )
    
    # Check if we're responding to a message or callback query
    if update.callback_query:
        await update.callback_query.edit_message_text(
            message,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_markdown(
            message
        )

async def process_investment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process the investment amount input and advance to risk profile question
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Extract amount from text
    try:
        amount_text = update.message.text.strip()
        # Remove currency symbols and commas
        amount_text = re.sub(r'[$,£€]', '', amount_text)
        amount = float(amount_text)
        
        # Check for reasonable amount
        if amount <= 0:
            await update.message.reply_markdown(
                "*Invalid Amount*\n\n"
                "Please enter an amount greater than 0."
            )
            return
        
        if amount > 1000000:  # Cap at $1M for reasonability
            await update.message.reply_markdown(
                "*Amount Too Large*\n\n"
                "For demonstration purposes, please enter an amount less than $1,000,000."
            )
            return
        
        # Update user context
        if user_id in user_investment_context:
            user_investment_context[user_id]["amount"] = amount
            user_investment_context[user_id]["state"] = AWAITING_RISK_PROFILE
            
            # Ask for risk profile
            message = (
                f"*Step 2:* Select your risk profile for investing ${amount:,.2f}:\n\n"
                "🟢 *Conservative*: Lower risk, stable returns\n"
                "🟡 *Moderate*: Balanced risk-reward\n"
                "🔴 *Aggressive*: Higher risk, potentially higher returns\n\n"
                "Your risk profile helps us recommend the most suitable pools."
            )
            
            await update.message.reply_markdown(
                message,
                reply_markup=RISK_PROFILE_KEYBOARD
            )
        else:
            # User context missing, restart flow
            await start_invest_flow(update, context)
            
    except ValueError:
        # Not a valid number
        await update.message.reply_markdown(
            "*Invalid Amount*\n\n"
            "Please enter a valid number. For example: 100"
        )
    except Exception as e:
        logger.error(f"Error processing investment amount: {e}")
        await update.message.reply_markdown(
            "*Error*\n\n"
            "Sorry, something went wrong processing your input. Please try again."
        )

async def process_risk_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process the risk profile selection and advance to token preference
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    try:
        await query.answer()
        
        # Extract risk profile from callback data
        callback_data = query.data
        if callback_data.startswith("risk_"):
            risk_profile = callback_data.replace("risk_", "")
            
            # Update user context
            if user_id in user_investment_context:
                user_investment_context[user_id]["risk_profile"] = risk_profile
                user_investment_context[user_id]["state"] = AWAITING_TOKEN_PREFERENCE
                
                # Get investment amount for message
                amount = user_investment_context[user_id]["amount"]
                
                # Ask for token preference
                message = (
                    f"*Step 3:* Do you have a preferred token for investing ${amount:,.2f}?\n\n"
                    "Selecting a token will prioritize pools containing that token.\n"
                    "You can also select \"No Preference\" to see all recommended pools."
                )
                
                await query.edit_message_text(
                    message,
                    reply_markup=TOKEN_PREFERENCE_KEYBOARD,
                    parse_mode="Markdown"
                )
            else:
                # User context missing, restart flow
                await start_invest_flow(update, context)
        else:
            # Invalid callback data
            logger.warning(f"Invalid risk profile callback data: {callback_data}")
            
    except Exception as e:
        logger.error(f"Error processing risk profile: {e}")
        try:
            await query.edit_message_text(
                "*Error*\n\n"
                "Sorry, something went wrong processing your selection. Please try again.",
                parse_mode="Markdown"
            )
        except:
            pass

async def process_token_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process the token preference and generate investment recommendations
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    try:
        await query.answer()
        
        # Extract token preference from callback data
        callback_data = query.data
        if callback_data.startswith("token_"):
            token_preference = callback_data.replace("token_", "")
            if token_preference.lower() == "none":
                token_preference = None
            
            # Update user context
            if user_id in user_investment_context:
                user_investment_context[user_id]["token_preference"] = token_preference
                user_investment_context[user_id]["state"] = AWAITING_CONFIRMATION
                
                # Get investment parameters
                amount = user_investment_context[user_id]["amount"]
                risk_profile = user_investment_context[user_id]["risk_profile"]
                
                # Show processing message while we generate recommendations
                await query.edit_message_text(
                    "*🔄 Analyzing Market Data*\n\n"
                    "Analyzing pools and market sentiment to find the best investment options...",
                    parse_mode="Markdown"
                )
                
                # Generate investment recommendations
                recommendation = agentic_advisor.get_investment_recommendation(
                    investment_amount=amount,
                    risk_profile=risk_profile,
                    token_preference=token_preference,
                    max_suggestions=3
                )
                
                # Save recommendation to user context
                user_investment_context[user_id]["recommendation"] = recommendation
                
                # Format message with recommendations
                message_parts = [
                    f"*💰 Investment Recommendation for ${amount:,.2f}*\n",
                    f"{recommendation['explanation']}\n"
                ]
                
                # Add action recommendation
                if recommendation['action'] == 'invest':
                    message_parts.append("*💡 Analysis:* Good market conditions for investment\n")
                elif recommendation['action'] == 'wait':
                    message_parts.append("*💡 Analysis:* Consider waiting for better market conditions\n")
                elif recommendation['action'] == 'reduced_exposure':
                    message_parts.append("*💡 Analysis:* Consider a smaller position size\n")
                elif recommendation['action'] == 'diversify':
                    message_parts.append("*💡 Analysis:* Recommend diversifying across multiple pools\n")
                
                # Add suggestions
                if recommendation['suggestions']:
                    message_parts.append("\n*Recommended Pools:*\n")
                    
                    for i, suggestion in enumerate(recommendation['suggestions'], 1):
                        message_parts.append(f"{i}. *{suggestion['pair']}*")
                        message_parts.append(f"   • APR: {suggestion['apr']:.2f}%")
                        message_parts.append(f"   • Expected 30-day return: ${suggestion['expected_return_30d']:,.2f}")
                        message_parts.append(f"   • Profit: ${suggestion['profit_30d']:,.2f}")
                        
                        if suggestion.get('prediction_score'):
                            message_parts.append(f"   • AI Score: {suggestion['prediction_score']}/100")
                            
                        message_parts.append(f"   • {suggestion['description'].capitalize()}")
                        message_parts.append("")
                else:
                    message_parts.append("\n*No suitable pools found*\n")
                    message_parts.append("Based on your criteria, no suitable pools were found at this time.")
                
                # Add confirmation buttons if we have suggestions
                keyboard = []
                
                if recommendation['suggestions']:
                    # Add buttons for each suggestion
                    for i, suggestion in enumerate(recommendation['suggestions'], 1):
                        # Truncate very long pool names
                        pool_name = suggestion['pair']
                        if len(pool_name) > 12:
                            pool_name = f"{pool_name[:10]}..."
                        
                        keyboard.append([
                            InlineKeyboardButton(
                                f"Invest in {pool_name}",
                                callback_data=f"invest_{i}"
                            )
                        ])
                
                # Add options to change parameters
                keyboard.append([
                    InlineKeyboardButton("Change Amount", callback_data="restart_invest"),
                    InlineKeyboardButton("Change Risk Profile", callback_data="change_risk")
                ])
                keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel_invest")])
                
                # Finalize message
                message = "\n".join(message_parts)
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            else:
                # User context missing, restart flow
                await start_invest_flow(update, context)
        else:
            # Invalid callback data
            logger.warning(f"Invalid token preference callback data: {callback_data}")
            
    except Exception as e:
        logger.error(f"Error processing token preference: {e}")
        try:
            await query.edit_message_text(
                "*Error*\n\n"
                "Sorry, something went wrong generating recommendations. Please try again.",
                parse_mode="Markdown"
            )
        except:
            pass

async def process_investment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process the investment confirmation and execute the investment
    
    Args:
        update: Telegram update object
        context: Context object for the update
    """
    query = update.callback_query
    user_id = update.effective_user.id if update.effective_user else 0
    
    try:
        await query.answer()
        
        # Extract pool selection from callback data
        callback_data = query.data
        
        if callback_data.startswith("invest_"):
            # User selected a pool to invest in
            selection_index = int(callback_data.replace("invest_", "")) - 1
            
            # Check user context
            if user_id in user_investment_context and user_investment_context[user_id]["recommendation"]:
                recommendation = user_investment_context[user_id]["recommendation"]
                
                if selection_index < len(recommendation["suggestions"]):
                    # Get selected pool
                    selected_pool = recommendation["suggestions"][selection_index]
                    user_investment_context[user_id]["selected_pool"] = selected_pool
                    user_investment_context[user_id]["state"] = COMPLETED
                    
                    # Save investment to database (if we had full back-end implementation)
                    # For now, we'll just send a confirmation message
                    
                    amount = user_investment_context[user_id]["amount"]
                    
                    # Processing message
                    await query.edit_message_text(
                        "*🔄 Processing Investment*\n\n"
                        "Your investment request is being processed...",
                        parse_mode="Markdown"
                    )
                    
                    # Simulate investment processing time
                    # In a real implementation, this would execute the transaction
                    # await asyncio.sleep(2)
                    
                    # Format confirmation message
                    message = (
                        "*🎉 Investment Successful!*\n\n"
                        f"You have successfully invested ${amount:,.2f} in *{selected_pool['pair']}*\n\n"
                        "*Investment Details:*\n"
                        f"• Pool: {selected_pool['pair']}\n"
                        f"• Amount: ${amount:,.2f}\n"
                        f"• Current APR: {selected_pool['apr']:.2f}%\n"
                        f"• Expected 30-day return: ${selected_pool['expected_return_30d']:,.2f}\n"
                        f"• Expected profit: ${selected_pool['profit_30d']:,.2f}\n\n"
                        "*What's Next?*\n"
                        "• Your investment is now active and earning returns\n"
                        "• You'll receive notifications about significant APR changes\n"
                        "• Use the Account menu to track your investments\n\n"
                        "Want to invest more or check your portfolio?"
                    )
                    
                    # Add post-investment buttons
                    keyboard = [
                        [InlineKeyboardButton("💰 Invest More", callback_data="restart_invest")],
                        [InlineKeyboardButton("👤 View Portfolio", callback_data="view_portfolio")],
                        [InlineKeyboardButton("📊 Market Overview", callback_data="market_overview")]
                    ]
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown"
                    )
                    
                    # Clean up user context (keeping only completed investment for reference)
                    completed_investment = user_investment_context[user_id].copy()
                    user_investment_context[user_id] = {
                        "state": COMPLETED,
                        "last_investment": completed_investment
                    }
                else:
                    # Invalid selection index
                    logger.warning(f"Invalid selection index: {selection_index}")
                    await query.edit_message_text(
                        "*Error*\n\n"
                        "Invalid selection. Please try again.",
                        parse_mode="Markdown"
                    )
            else:
                # User context missing, restart flow
                await start_invest_flow(update, context)
                
        elif callback_data == "restart_invest":
            # Restart investment flow
            await start_invest_flow(update, context)
            
        elif callback_data == "change_risk":
            # Go back to risk profile selection
            if user_id in user_investment_context:
                amount = user_investment_context[user_id]["amount"]
                user_investment_context[user_id]["state"] = AWAITING_RISK_PROFILE
                
                message = (
                    f"*Update Risk Profile*\n\n"
                    f"Select your risk profile for investing ${amount:,.2f}:\n\n"
                    "🟢 *Conservative*: Lower risk, stable returns\n"
                    "🟡 *Moderate*: Balanced risk-reward\n"
                    "🔴 *Aggressive*: Higher risk, potentially higher returns"
                )
                
                await query.edit_message_text(
                    message,
                    reply_markup=RISK_PROFILE_KEYBOARD,
                    parse_mode="Markdown"
                )
            else:
                # User context missing, restart flow
                await start_invest_flow(update, context)
                
        elif callback_data == "cancel_invest":
            # Cancel investment
            if user_id in user_investment_context:
                user_investment_context.pop(user_id)
            
            await query.edit_message_text(
                "*Investment Cancelled*\n\n"
                "Your investment has been cancelled. You can start a new investment at any time.",
                parse_mode="Markdown"
            )
            
        elif callback_data == "view_portfolio":
            # Show portfolio (placeholder for now)
            amount = user_investment_context[user_id]["amount"]
            selected_pool = user_investment_context[user_id]["selected_pool"]
            
            message = (
                "*👤 Your Investment Portfolio*\n\n"
                "*Active Investments:*\n"
                f"• ${amount:,.2f} in {selected_pool['pair']} ({selected_pool['apr']:.2f}% APR)\n\n"
                "*Total Invested:* ${amount:,.2f}\n"
                f"*Expected Monthly Return:* ${selected_pool['profit_30d']:,.2f}\n\n"
                "Your investments are performing as expected."
            )
            
            keyboard = [
                [InlineKeyboardButton("💰 Invest More", callback_data="restart_invest")],
                [InlineKeyboardButton("📊 Market Overview", callback_data="market_overview")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        elif callback_data == "market_overview":
            # Show market overview (placeholder for now)
            message = (
                "*📊 Market Overview*\n\n"
                "*Top Performing Pools:*\n"
                "1. BONK-SOL: 42.5% APR\n"
                "2. JTO-USDC: 38.2% APR\n"
                "3. SOL-USDC: 12.8% APR\n\n"
                "*Market Sentiment:*\n"
                "• SOL: 🟢 Positive (0.45)\n"
                "• Overall: 🟡 Neutral (0.12)\n\n"
                "Market conditions are favorable for investing."
            )
            
            keyboard = [
                [InlineKeyboardButton("💰 Invest Now", callback_data="restart_invest")],
                [InlineKeyboardButton("👤 View Portfolio", callback_data="view_portfolio")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
        else:
            # Invalid callback data
            logger.warning(f"Invalid investment confirmation callback data: {callback_data}")
            
    except Exception as e:
        logger.error(f"Error processing investment confirmation: {e}")
        try:
            await query.edit_message_text(
                "*Error*\n\n"
                "Sorry, something went wrong processing your investment. Please try again.",
                parse_mode="Markdown"
            )
        except:
            pass

async def handle_invest_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle a message that starts or continues the investment flow
    
    Args:
        update: Telegram update object
        context: Context object for the update
        
    Returns:
        True if the message was handled, False otherwise
    """
    user_id = update.effective_user.id if update.effective_user else 0
    
    # Check if message contains investment-related text
    if hasattr(update, 'message') and update.message and update.message.text:
        message_text = update.message.text.lower()
        
        # "Invest" keyword to start flow
        if "invest" in message_text or message_text == "💰 invest":
            # Check if we should extract amount and risk from natural language
            amount_match = re.search(r'(\d+(?:\.\d+)?)', message_text)
            has_amount = amount_match is not None
            
            risk_profile = None
            if "conservative" in message_text or "safe" in message_text or "low risk" in message_text:
                risk_profile = "conservative"
            elif "aggressive" in message_text or "high risk" in message_text:
                risk_profile = "aggressive"
            elif "moderate" in message_text or "balanced" in message_text or "medium risk" in message_text:
                risk_profile = "moderate"
            
            # If we have both amount and risk profile, we can skip those steps
            if has_amount and risk_profile:
                amount = float(amount_match.group(1))
                
                # Initialize user context
                user_investment_context[user_id] = {
                    "state": AWAITING_TOKEN_PREFERENCE,
                    "amount": amount,
                    "risk_profile": risk_profile,
                    "token_preference": None,
                    "recommendation": None,
                    "selected_pool": None
                }
                
                # Ask for token preference
                message = (
                    f"*🚀 FiLot Investment Assistant*\n\n"
                    f"Great! I'll help you invest ${amount:,.2f} with a {risk_profile} risk profile.\n\n"
                    f"*Step 3:* Do you have a preferred token for your investment?\n\n"
                    "Selecting a token will prioritize pools containing that token."
                )
                
                await update.message.reply_markdown(
                    message,
                    reply_markup=TOKEN_PREFERENCE_KEYBOARD
                )
                return True
                
            # Just the amount, ask for risk profile
            elif has_amount:
                amount = float(amount_match.group(1))
                
                # Initialize user context
                user_investment_context[user_id] = {
                    "state": AWAITING_RISK_PROFILE,
                    "amount": amount,
                    "risk_profile": None,
                    "token_preference": None,
                    "recommendation": None,
                    "selected_pool": None
                }
                
                # Ask for risk profile
                message = (
                    f"*🚀 FiLot Investment Assistant*\n\n"
                    f"Great! I'll help you invest ${amount:,.2f}.\n\n"
                    f"*Step 2:* Select your risk profile:\n\n"
                    "🟢 *Conservative*: Lower risk, stable returns\n"
                    "🟡 *Moderate*: Balanced risk-reward\n"
                    "🔴 *Aggressive*: Higher risk, potentially higher returns"
                )
                
                await update.message.reply_markdown(
                    message,
                    reply_markup=RISK_PROFILE_KEYBOARD
                )
                return True
                
            # Just "invest", start the full flow
            else:
                await start_invest_flow(update, context)
                return True
    
    # Check if we're in the middle of a flow and need to handle state
    if user_id in user_investment_context:
        state = user_investment_context[user_id]["state"]
        
        if state == AWAITING_AMOUNT and update.message and update.message.text:
            await process_investment_amount(update, context)
            return True
    
    # Not handled
    return False

async def handle_invest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle callback queries for the investment flow
    
    Args:
        update: Telegram update object
        context: Context object for the update
        
    Returns:
        True if the callback was handled, False otherwise
    """
    query = update.callback_query
    if not query:
        return False
        
    user_id = update.effective_user.id if update.effective_user else 0
    callback_data = query.data
    
    # Handle investment-related callbacks
    if callback_data.startswith("risk_"):
        await process_risk_profile(update, context)
        return True
        
    elif callback_data.startswith("token_"):
        await process_token_preference(update, context)
        return True
        
    elif callback_data.startswith("invest_") or callback_data in [
        "restart_invest", "change_risk", "cancel_invest", 
        "view_portfolio", "market_overview"
    ]:
        await process_investment_confirmation(update, context)
        return True
        
    elif callback_data == "start_invest":
        await start_invest_flow(update, context)
        return True
    
    # Not handled
    return False

async def check_active_investments(user_id: int) -> List[Dict[str, Any]]:
    """
    Check if a user has active investments
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        List of active investments with exit recommendations
    """
    # In a real implementation, this would query the database
    # For now, we'll return a placeholder
    
    # Check if user has a completed investment in context
    if user_id in user_investment_context and "last_investment" in user_investment_context[user_id]:
        last_investment = user_investment_context[user_id]["last_investment"]
        if "selected_pool" in last_investment and last_investment["selected_pool"]:
            pool = last_investment["selected_pool"]
            amount = last_investment["amount"]
            
            # Use the agentic advisor to check if user should exit
            exit_rec = agentic_advisor.should_exit_position(
                pool_id=pool.get("pool_id", "unknown"),
                entry_apr=pool["apr"],
                entry_time_days=7,  # Placeholder, assuming 7 days since entry
                risk_profile=last_investment["risk_profile"]
            )
            
            return [{
                "pool": pool,
                "amount": amount,
                "entry_date": "2025-05-12",  # Placeholder
                "entry_apr": pool["apr"],
                "current_apr": exit_rec["data"]["current_apr"] if "data" in exit_rec else pool["apr"],
                "exit_recommended": exit_rec["exit_recommended"],
                "exit_confidence": exit_rec["confidence"],
                "exit_explanation": exit_rec["explanation"]
            }]
    
    return []