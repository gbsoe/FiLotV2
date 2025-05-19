#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interactive menu commands for FiLot Telegram bot
Implements buttons that perform real database operations
"""

import logging
import datetime
from typing import Dict, List, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app import app
from models import db, User, Pool, UserActivityLog

# Database functions
def get_pools(limit: int = 5) -> List[Dict[str, Any]]:
    """Get pool data from database"""
    try:
        with app.app_context():
            pools = Pool.query.limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'name': f"{pool.token_a_symbol}-{pool.token_b_symbol}",
                    'tokens': f"{pool.token_a_symbol}/{pool.token_b_symbol}",
                    'token_a_symbol': pool.token_a_symbol,
                    'token_b_symbol': pool.token_b_symbol,
                    'apr': pool.apr_24h or 0,
                    'apr_24h': pool.apr_24h or 0,
                    'tvl': pool.tvl or 0,
                    'tvl_usd': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0,
                    'fee': pool.fee or 0.003
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting pools: {e}")
        # Return fallback data so UI doesn't break
        return []

def get_high_apr_pools(limit: int = 3) -> List[Dict[str, Any]]:
    """Get high APR pools from database"""
    try:
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'name': f"{pool.token_a_symbol}-{pool.token_b_symbol}",
                    'tokens': f"{pool.token_a_symbol}/{pool.token_b_symbol}",
                    'token_a_symbol': pool.token_a_symbol,
                    'token_b_symbol': pool.token_b_symbol,
                    'apr': pool.apr_24h or 0,
                    'apr_24h': pool.apr_24h or 0,
                    'tvl': pool.tvl or 0,
                    'tvl_usd': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0,
                    'fee': pool.fee or 0.003
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting high APR pools: {e}")
        return []

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Interactive menu command
async def interactive_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display interactive menu with buttons that perform real database operations."""
    try:
        user = update.effective_user
        logger.info(f"User {user.id} requested interactive menu")
        
        # Define inline keyboard with buttons that perform real database operations
        keyboard = [
            [InlineKeyboardButton("📊 View Pool Data", callback_data="interactive_pools")],
            [InlineKeyboardButton("📈 View High APR Pools", callback_data="interactive_high_apr")],
            [InlineKeyboardButton("👤 My Profile", callback_data="interactive_profile")],
            [InlineKeyboardButton("❓ FAQ / Help", callback_data="interactive_faq")]
        ]
        
        await update.message.reply_text(
            f"Welcome to FiLot Interactive Menu, {user.first_name}!\n\n"
            "These buttons perform real database operations.\n"
            "Click any option to retrieve live data:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in interactive menu command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )

# Interactive callback query handler
async def interactive_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle interactive button callbacks that perform real database operations.
    Returns True if the callback was handled, False otherwise."""
    try:
        query = update.callback_query
        if not query:
            logger.error("No callback query in update")
            return False
            
        # Acknowledge the button click to remove loading state
        try:
            await query.answer()
        except Exception as e:
            logger.error(f"Error answering callback query: {e}")
            # Continue even if answer fails
            
        try:
            user_id = update.effective_user.id if update.effective_user else "Unknown"
            callback_data = query.data if query and query.data else "Unknown"
            logger.info(f"User {user_id} pressed interactive button: {callback_data}")
            
            # Handle different button actions based on callback_data
            if not callback_data.startswith("interactive_"):
                # Not our button, let another handler deal with it
                logger.info(f"Not an interactive button: {callback_data}")
                return False
                
            if callback_data == "interactive_pools":
                await show_pool_data(update, context)
                return True
            
            elif callback_data == "interactive_high_apr":
                await show_high_apr_pools(update, context)
                return True
                
            elif callback_data == "interactive_profile":
                await show_user_profile(update, context)
                return True
                
            elif callback_data == "interactive_faq":
                await show_faq(update, context)
                return True
                
            elif callback_data == "interactive_back":
                await back_to_menu(update, context)
                return True
                
            # FAQ topic buttons
            elif callback_data == "interactive_faq_pools":
                await show_faq_topic_pools(update, context)
                return True
                
            elif callback_data == "interactive_faq_apr":
                await show_faq_topic_apr(update, context)
                return True
                
            elif callback_data == "interactive_faq_impermanent_loss":
                await show_faq_topic_impermanent_loss(update, context)
                return True
                
            elif callback_data == "interactive_faq_wallets":
                await show_faq_topic_wallets(update, context)
                return True
                
            # Error fallback - handle other interactive buttons with a generic message
            else:
                logger.warning(f"Unhandled interactive button: {callback_data}")
                try:
                    await query.edit_message_text(
                        "This button functionality is not yet implemented.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                        ]])
                    )
                    return True
                except Exception as e:
                    logger.error(f"Error sending fallback message: {e}")
                    return False
                
        except Exception as e:
            logger.error(f"Error in interactive callback specific handler: {e}")
            if query and query.message:
                try:
                    await query.edit_message_text(
                        "Sorry, an error occurred while processing your request.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                        ]])
                    )
                except Exception as edit_error:
                    logger.error(f"Error editing message after error: {edit_error}")
            return True  # Mark as handled even if there was an error
            
    except Exception as outer_e:
        logger.error(f"Critical error in interactive callback: {outer_e}")
        return False  # Could not handle this callback

# Button handlers
async def show_pool_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pool data from the database."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        logger.info(f"User {user_id} requested pool data")
        
        # Get pool data using our function
        pools_data = get_pools(5)
        
        if pools_data and len(pools_data) > 0:
            # Format message with real pool data from database
            message = "📊 *Liquidity Pool Data*\n\n"
            
            for i, pool in enumerate(pools_data):
                # Format numbers with commas and proper decimal places
                apr_formatted = f"{pool['apr_24h']:.2f}%"
                tvl_formatted = f"${pool['tvl']:,.2f}"
                fee_formatted = f"{pool['fee']*100:.3f}%"
                volume_formatted = f"${pool['volume_24h']:,.2f}" if pool['volume_24h'] else "N/A"
                
                message += (
                    f"{i+1}. *{pool['token_a_symbol']}-{pool['token_b_symbol']}*\n"
                    f"   • APR: {apr_formatted}\n"
                    f"   • TVL: {tvl_formatted}\n"
                    f"   • Fee: {fee_formatted}\n"
                    f"   • 24h Volume: {volume_formatted}\n\n"
                )
            
            # Add action buttons
            keyboard = [
                [InlineKeyboardButton("📊 View More Details", callback_data="interactive_pool_details")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "*No Pool Data Available*\n\n"
                "We couldn't find any pool data in the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                ]])
            )
    except Exception as e:
            logger.error(f"Error retrieving pool data: {e}")
            await query.edit_message_text(
                "Sorry, an error occurred while retrieving pool data.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                ]])
            )

async def show_high_apr_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pools with highest APR from the database."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        logger.info(f"User {user_id} requested high APR pools")
        
        # Get high APR pools using our function
        high_apr_pools_data = get_high_apr_pools(3)
        
        if high_apr_pools_data and len(high_apr_pools_data) > 0:
            # Format message with high APR pool data from actual database
            message = "📈 *Top High APR Pools*\n\n"
            message += "These are the highest APR pools currently available on Raydium:\n\n"
            
            for i, pool in enumerate(high_apr_pools_data):
                # Format numbers with proper presentation
                apr_formatted = f"{pool['apr_24h']:.2f}%"
                tvl_formatted = f"${pool['tvl']:,.2f}"
                fee_formatted = f"{pool['fee']*100:.3f}%"
                
                message += (
                    f"{i+1}. *{pool['token_a_symbol']}-{pool['token_b_symbol']}*\n"
                    f"   • APR: {apr_formatted} 🔥\n"
                    f"   • TVL: {tvl_formatted}\n"
                    f"   • Fee: {fee_formatted}\n\n"
                )
            
            # Log user activity for analytics
            logger.info(f"User {user_id} viewed high APR pools")
            
            # Add action buttons including 'Simulate Investment' option
            keyboard = [
                [InlineKeyboardButton("🔮 Simulate Investment", callback_data="interactive_simulate")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "*No High APR Pool Data Available*\n\n"
                "We couldn't find any high APR pool data in the database.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                ]])
            )
    except Exception as e:
        logger.error(f"Error retrieving high APR pools: {e}")
        try:
            await query.edit_message_text(
                "Sorry, an error occurred while retrieving high APR pool data.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                ]])
            )
        except Exception as inner_error:
            logger.error(f"Failed to send error message: {inner_error}")

async def show_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile from database with actual data."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    with app.app_context():
        try:
            # Get user profile from database - working with real database operations
            user = User.query.filter_by(id=user_id).first()
            
            if user:
                # Format message with real user profile data from database
                # Format dates and booleans for better readability
                created_date = user.created_at.strftime('%Y-%m-%d') if user.created_at else 'Unknown'
                last_active = user.last_active.strftime('%Y-%m-%d %H:%M') if user.last_active else 'Unknown'
                subscription_status = '✅ Yes' if user.is_subscribed else '❌ No'
                verification_status = '✅ Yes' if user.is_verified else '❌ No'
                
                message = (
                    f"👤 *Your Profile*\n\n"
                    f"• *Username:* {user.username or 'Not set'}\n"
                    f"• *Name:* {user.first_name or ''} {user.last_name or ''}\n"
                    f"• *Risk Profile:* {user.risk_profile.capitalize()}\n"
                    f"• *Investment Horizon:* {user.investment_horizon.capitalize()}\n"
                    f"• *Investment Goals:* {user.investment_goals or 'Not specified'}\n"
                    f"• *Subscribed to Updates:* {subscription_status}\n"
                    f"• *Verified:* {verification_status}\n"
                    f"• *Account Created:* {created_date}\n"
                    f"• *Last Active:* {last_active}\n\n"
                    f"This data is retrieved directly from our database."
                )
                
                # Log activity for analytics
                logger.info(f"User {user_id} viewed their profile")
                
                # Create action buttons for profile management
                keyboard = [
                    [InlineKeyboardButton("✏️ Edit Profile", callback_data="interactive_edit_profile")],
                    [InlineKeyboardButton("🔔 Manage Subscriptions", callback_data="interactive_subscriptions")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
                ]
            else:
                # Create new user profile if doesn't exist - real database operation
                try:
                    new_user = User(
                        id=user_id,
                        username=update.effective_user.username or "User",
                        first_name=update.effective_user.first_name,
                        last_name=update.effective_user.last_name,
                        risk_profile="moderate",
                        investment_horizon="medium",
                        created_at=datetime.datetime.utcnow(),
                        last_active=datetime.datetime.utcnow(),
                        is_subscribed=False,
                        is_verified=False,
                        message_count=1
                    )
                    
                    db.session.add(new_user)
                    db.session.commit()
                    
                    logger.info(f"Created new user profile for user {user_id}")
                    
                    message = (
                        f"👤 *Your Profile (New User)*\n\n"
                        f"• *Username:* {update.effective_user.username or 'Not set'}\n"
                        f"• *Name:* {update.effective_user.first_name or ''} {update.effective_user.last_name or ''}\n"
                        f"• *Risk Profile:* Moderate (default)\n"
                        f"• *Investment Horizon:* Medium (default)\n"
                        f"• *Investment Goals:* Not specified\n"
                        f"• *Subscribed to Updates:* ❌ No\n"
                        f"• *Verified:* ❌ No\n\n"
                        f"Welcome! Your profile has been created in our database."
                    )
                    
                    # Create welcome message with profile setup buttons
                    keyboard = [
                        [InlineKeyboardButton("🛠️ Complete Profile Setup", callback_data="interactive_setup_profile")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
                    ]
                except Exception as e:
                    logger.error(f"Error creating new user: {e}")
                    message = "Sorry, there was an error creating your profile. Please try again later."
                    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}")
            await query.edit_message_text(
                "Sorry, an error occurred while retrieving your profile data.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")
                ]])
            )

async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ topics with interactive buttons for each topic."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Log user interaction with FAQ section
    logger.info(f"User {user_id} accessed FAQ section")
    
    message = (
        "❓ *Frequently Asked Questions*\n\n"
        "Choose a topic to learn more about cryptocurrency investments:"
    )
    
    # Create buttons for different FAQ topics
    keyboard = [
        [InlineKeyboardButton("💰 About Liquidity Pools", callback_data="interactive_faq_pools")],
        [InlineKeyboardButton("📈 Understanding APR", callback_data="interactive_faq_apr")],
        [InlineKeyboardButton("⚠️ Impermanent Loss Explained", callback_data="interactive_faq_impermanent_loss")],
        [InlineKeyboardButton("🔐 Wallet Security", callback_data="interactive_faq_wallets")],
        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
    ]
    
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to the main interactive menu."""
    query = update.callback_query
    
    # Define inline keyboard for main menu
    keyboard = [
        [InlineKeyboardButton("📊 View Pool Data", callback_data="interactive_pools")],
        [InlineKeyboardButton("📈 View High APR Pools", callback_data="interactive_high_apr")],
        [InlineKeyboardButton("👤 My Profile", callback_data="interactive_profile")],
        [InlineKeyboardButton("❓ FAQ / Help", callback_data="interactive_faq")]
    ]
    
    await query.edit_message_text(
        "*FiLot Interactive Menu*\n\n"
        "These buttons perform real database operations.\n"
        "Click any option to retrieve live data:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# FAQ Topic handlers
async def show_faq_topic_pools(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ about liquidity pools with real pool examples from database."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        # Log user interaction with pools FAQ
        logger.info(f"User {user_id} accessed pools FAQ")
        
        message = (
            "💰 *Liquidity Pools FAQ*\n\n"
            "*What are liquidity pools?*\n"
            "Liquidity pools are collections of funds locked in smart contracts that facilitate trading between different tokens. When you provide liquidity, you deposit an equal value of two tokens and receive LP tokens in return.\n\n"
            "*How do liquidity pools generate returns?*\n"
            "Liquidity providers earn a share of the trading fees generated by the pool, proportional to their share of the total liquidity. Many pools also offer additional rewards in the form of token incentives.\n\n"
            "*What is Total Value Locked (TVL)?*\n"
            "TVL represents the total value of all assets deposited in a liquidity pool, expressed in USD. Higher TVL generally indicates more stable pools with less slippage.\n\n"
            "*Are some pools better than others?*\n"
            "Yes! Pools differ in terms of APR, fees, volume, and risk. Generally, stablecoin pairs have lower risk but also lower returns, while volatile token pairs offer higher potential returns with increased risk."
        )
        
        # Instead of using SQLAlchemy directly, use our helper function
        try:
            # Get pools using our helper function
            pools = get_pools(1)  # Just get one pool for the example
            
            if pools and len(pools) > 0:
                pool = pools[0]
                # Make sure we safely access pool data with fallbacks
                token_a = pool.get('token_a_symbol', 'Token A')
                token_b = pool.get('token_b_symbol', 'Token B')
                apr = pool.get('apr_24h', 0)
                tvl = pool.get('tvl_usd', 0)
                fee = pool.get('fee', 0)
                
                message += f"\n\n*Real Pool Example:*\n{token_a}-{token_b}\n"
                message += f"• APR: {apr:.2f}%\n"
                message += f"• TVL: ${tvl:,.2f}\n"
                message += f"• Fee: {fee*100:.3f}%"
        except Exception as e:
            logger.error(f"Error retrieving pool example for FAQ: {e}")
            # Continue without the example if there's an error
        
        # Add navigation buttons
        keyboard = [
            [InlineKeyboardButton("↩️ Back to FAQ", callback_data="interactive_faq")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
        ]
        
        # Only try to edit if we have a valid query and message
        if query and query.message:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            logger.error("Cannot update message - missing query or message object")
            
    except Exception as e:
        logger.error(f"Error showing pools FAQ: {e}")
        # Try to acknowledge the button press even if we can't update the message
        try:
            if update.callback_query:
                await update.callback_query.answer("Sorry, there was an error displaying the FAQ")
        except Exception as answer_err:
            logger.error(f"Error sending answer: {answer_err}")

async def show_faq_topic_apr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ about APR with real examples from database."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        # Log user interaction with APR FAQ
        logger.info(f"User {user_id} accessed APR FAQ")
        
        message = (
            "📈 *Understanding APR FAQ*\n\n"
            "*What is APR?*\n"
            "APR (Annual Percentage Rate) represents the yearly rate of return on your investment. In liquidity pools, APR typically comes from trading fees and additional token rewards.\n\n"
            "*Why do APRs vary between pools?*\n"
            "APRs differ based on several factors: trading volume (more trades = more fees), pool size (smaller pools often have higher APR), token volatility, and additional incentives from protocols.\n\n"
            "*Are high APRs sustainable?*\n"
            "High APRs (>100%) are typically not sustainable long-term. They usually result from temporary token incentives or new pools with low liquidity. As more liquidity enters high-APR pools, returns tend to normalize.\n\n"
            "*How is APR different from APY?*\n"
            "APR shows the simple annual rate without compounding. APY (Annual Percentage Yield) includes the effect of compounding returns, making it higher than APR if you reinvest your earnings."
        )
        
        # Use helper function to get pools
        try:
            # Get sample pools for examples using our helper function
            pools = get_pools(5)  # Get 5 pools to choose from
            
            if pools and len(pools) > 1:
                # Sort pools by APR to get high and low examples
                sorted_pools = sorted(pools, key=lambda x: x.get('apr_24h', 0) if x.get('apr_24h') is not None else 0)
                
                # Find a pool with APR > 0 for the low example
                low_apr_pool = None
                for pool in sorted_pools:
                    if pool.get('apr_24h', 0) > 0:
                        low_apr_pool = pool
                        break
                
                # Get highest APR pool
                high_apr_pool = sorted_pools[-1] if sorted_pools else None
                
                if high_apr_pool and low_apr_pool:
                    # Add real APR comparison with safe access to pool properties
                    message += "\n\n*Real APR Examples:*\n"
                    message += f"• High APR pool: {high_apr_pool.get('token_a_symbol', 'Token A')}-{high_apr_pool.get('token_b_symbol', 'Token B')} at {high_apr_pool.get('apr_24h', 0):.2f}%\n"
                    message += f"• Low APR pool: {low_apr_pool.get('token_a_symbol', 'Token A')}-{low_apr_pool.get('token_b_symbol', 'Token B')} at {low_apr_pool.get('apr_24h', 0):.2f}%"
        except Exception as e:
            logger.error(f"Error retrieving APR examples for FAQ: {e}")
            # Continue without examples if there's an error
        
        # Add navigation buttons
        keyboard = [
            [InlineKeyboardButton("↩️ Back to FAQ", callback_data="interactive_faq")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
        ]
        
        # Only try to edit if we have a valid query and message
        if query and query.message:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            logger.error("Cannot update message - missing query or message object")
            
    except Exception as e:
        logger.error(f"Error showing APR FAQ: {e}")
        # Try to acknowledge the button press even if we can't update the message
        try:
            if update and update.callback_query:
                await update.callback_query.answer("Sorry, there was an error displaying the FAQ")
        except Exception as answer_err:
            logger.error(f"Error sending answer: {answer_err}")

async def show_faq_topic_impermanent_loss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ about impermanent loss with clear explanations."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        # Log user interaction with impermanent loss FAQ
        logger.info(f"User {user_id} accessed impermanent loss FAQ")
        
        message = (
            "⚠️ *Impermanent Loss Explained*\n\n"
            "*What is impermanent loss?*\n"
            "Impermanent loss occurs when the price ratio of tokens in your liquidity pool changes after you deposit them. This creates a difference between holding tokens versus providing liquidity.\n\n"
            "*Why 'impermanent'?*\n"
            "The loss is only 'impermanent' until you withdraw your funds. If token prices return to their original ratio when you deposited, the impermanent loss disappears.\n\n"
            "*How to minimize impermanent loss?*\n"
            "• Provide liquidity to stablecoin pairs (USDC-USDT)\n"
            "• Choose correlated tokens (wBTC-ETH)\n"
            "• Look for pools with high fees that can offset potential losses\n"
            "• Consider concentrated liquidity options that limit your price range\n\n"
            "*Example scenario:*\n"
            "You deposit 1 SOL ($100) and 100 USDC ($100) into a pool. If SOL price doubles to $200, the pool balances to ~0.7 SOL and ~141 USDC. When you withdraw, you'd get assets worth $240, but simply holding would be worth $300 – that $60 difference is impermanent loss."
        )
        
        # Add navigation buttons
        keyboard = [
            [InlineKeyboardButton("↩️ Back to FAQ", callback_data="interactive_faq")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
        ]
        
        # Only try to edit if we have a valid query and message
        if query and query.message:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            logger.error("Cannot update message - missing query or message object")
            
    except Exception as e:
        logger.error(f"Error showing impermanent loss FAQ: {e}")
        # Try to acknowledge the button press even if we can't update the message
        try:
            if update and update.callback_query:
                await update.callback_query.answer("Sorry, there was an error displaying the FAQ")
        except Exception as answer_err:
            logger.error(f"Error sending answer: {answer_err}")

async def show_faq_topic_wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show FAQ about wallet security and best practices."""
    try:
        query = update.callback_query
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        
        # Log user interaction with wallet security FAQ
        logger.info(f"User {user_id} accessed wallet security FAQ")
        
        message = (
            "🔐 *Wallet Security FAQ*\n\n"
            "*Which Solana wallets are recommended?*\n"
            "Popular Solana wallets include Phantom, Solflare, and Backpack. All offer good security features, dApp connections, and regular updates to protect your assets.\n\n"
            "*How does WalletConnect work?*\n"
            "WalletConnect creates an encrypted connection between your wallet and dApps through a QR code or deep link. Your private keys remain in your wallet app and are never shared with the dApp or our bot.\n\n"
            "*Best security practices:*\n"
            "• Use hardware wallets (Ledger, Trezor) for large holdings\n"
            "• Never share your seed phrase or private keys with anyone\n"
            "• Enable biometrics and 2FA when available\n"
            "• Review transactions carefully before signing\n"
            "• Use different wallets for different purposes\n\n"
            "*What to do if compromised:*\n"
            "If you suspect your wallet is compromised, immediately transfer your assets to a new, secure wallet with a different seed phrase. Report the incident to the wallet provider and relevant blockchain authorities."
        )
        
        # Add navigation buttons
        keyboard = [
            [InlineKeyboardButton("↩️ Back to FAQ", callback_data="interactive_faq")],
            [InlineKeyboardButton("⬅️ Back to Menu", callback_data="interactive_back")]
        ]
        
        # Only try to edit if we have a valid query and message
        if query and query.message:
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            logger.error("Cannot update message - missing query or message object")
            
    except Exception as e:
        logger.error(f"Error showing wallet security FAQ: {e}")
        # Try to acknowledge the button press even if we can't update the message
        try:
            if update and update.callback_query:
                await update.callback_query.answer("Sorry, there was an error displaying the FAQ")
        except Exception as answer_err:
            logger.error(f"Error sending answer: {answer_err}")