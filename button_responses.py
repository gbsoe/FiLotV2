#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Button responses implementation for FiLot Telegram bot
Adds fully functional interactive buttons that perform real database operations
"""

import os
import logging
import datetime
from typing import Dict, List, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app import app
from models import db, User, Pool, UserActivityLog
import solpool_api_client as solpool_api
import filotsense_api_client as sentiment_api

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Button definitions
async def show_interactive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the main interactive menu with buttons that perform real database operations
    and connect to the SolPool Insight API and FilotSense APIs
    """
    try:
        user = update.effective_user
        if not user:
            logger.warning("No user information available in update")
            return
            
        logger.info(f"User {user.id} requested interactive menu")
        
        # Define inline keyboard with buttons that perform real operations
        keyboard = [
            [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
            [InlineKeyboardButton("📈 View High APR Pools", callback_data="high_apr")],
            [InlineKeyboardButton("🔍 Search by Token", callback_data="token_search")],
            [InlineKeyboardButton("🔮 View AI Predictions", callback_data="predictions")],
            [InlineKeyboardButton("💬 Market Sentiment", callback_data="sentiment")],
            [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
            [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
        ]
        
        # Check if APIs are available
        is_pool_api_available = solpool_api.api_health_check()
        is_sentiment_api_available = sentiment_api.api_health_check()
        
        message_parts = [f"*Welcome to FiLot Interactive Menu, {user.first_name}!*\n\n"]
        
        if is_pool_api_available and is_sentiment_api_available:
            message_parts.append("✅ Connected to SolPool Insight API for real-time pool data")
            message_parts.append("✅ Connected to FilotSense API for market sentiment analysis\n")
            message_parts.append("Click any option to retrieve live data:")
        elif is_pool_api_available:
            message_parts.append("✅ Connected to SolPool Insight API for real-time pool data")
            message_parts.append("❌ Market sentiment data currently unavailable\n")
            message_parts.append("Click any option to retrieve pool data:")
        elif is_sentiment_api_available:
            message_parts.append("❌ Pool data API currently unavailable")
            message_parts.append("✅ Connected to FilotSense API for market sentiment analysis\n")
            message_parts.append("Click any option to explore available data:")
        else:
            message_parts.append("These buttons connect to our local database for information.\n")
            message_parts.append("External APIs currently unavailable. Limited data may be shown.")
        
        message = "\n".join(message_parts)
        
        await update.message.reply_markdown(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in interactive menu command: {e}")
        try:
            if update.message:
                await update.message.reply_text(
                    "Sorry, an error occurred. Please try again later."
                )
        except Exception as inner_e:
            logger.error(f"Error sending error message: {inner_e}")

# Database operations
def get_high_apr_pools(limit: int = 3) -> List[Dict[str, Any]]:
    """Get high APR pools from SolPool API with database fallback"""
    try:
        # First try to get data from SolPool API
        api_pools = solpool_api.get_high_apr_pools(limit)
        
        if api_pools and len(api_pools) > 0:
            logger.info(f"Successfully retrieved {len(api_pools)} high APR pools from SolPool API")
            
            # Convert to our expected format
            result = []
            for pool in api_pools:
                result.append({
                    'id': pool.get('id', ''),
                    'token_a': pool.get('token_a_symbol', ''),
                    'token_b': pool.get('token_b_symbol', ''),
                    'apr_24h': pool.get('apr_24h', 0),
                    'tvl': pool.get('tvl', 0),
                    'volume_24h': pool.get('volume_24h', 0),
                    'fee': pool.get('fee', 0),
                    'prediction_score': pool.get('prediction_score', 0),
                    'data_source': 'SolPool API'
                })
            return result
            
        # If API fails, fall back to database
        logger.warning("Failed to get high APR pools from API, falling back to database")
        with app.app_context():
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,
                    'tvl': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0,
                    'fee': pool.fee or 0,
                    'data_source': 'Database'
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting high APR pools: {e}")
        return []

def get_pools(limit: int = 5) -> List[Dict[str, Any]]:
    """Get pool data from SolPool API with database fallback"""
    try:
        # First try to get data from SolPool API
        api_pools = solpool_api.get_pools(limit=limit)
        
        if api_pools and len(api_pools) > 0:
            logger.info(f"Successfully retrieved {len(api_pools)} pools from SolPool API")
            
            # Convert to our expected format
            result = []
            for pool in api_pools:
                result.append({
                    'id': pool.get('id', ''),
                    'token_a': pool.get('token_a_symbol', ''),
                    'token_b': pool.get('token_b_symbol', ''),
                    'apr_24h': pool.get('apr_24h', 0),
                    'tvl': pool.get('tvl', 0),
                    'volume_24h': pool.get('volume_24h', 0),
                    'fee': pool.get('fee', 0),
                    'dex': pool.get('dex', ''),
                    'data_source': 'SolPool API'
                })
            return result
            
        # If API fails, fall back to database
        logger.warning("Failed to get pools from API, falling back to database")
        with app.app_context():
            pools = Pool.query.limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,
                    'tvl': pool.tvl or 0,
                    'volume_24h': pool.volume_24h or 0,
                    'fee': pool.fee or 0,
                    'data_source': 'Database'
                })
            
            return result
    except Exception as e:
        logger.error(f"Error getting pools: {e}")
        return []

def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user profile from database"""
    try:
        with app.app_context():
            user = User.query.filter_by(id=user_id).first()
            
            if user:
                return {
                    'id': user.id,
                    'username': user.username or 'Unknown',
                    'risk_profile': user.risk_profile or 'moderate',
                    'investment_horizon': user.investment_horizon or 'medium',
                    'investment_goals': user.investment_goals or 'Not specified',
                    'is_subscribed': user.is_subscribed or False,
                    'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else 'N/A'
                }
            
            return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

def create_user_profile(user_id: int, username: str, first_name: str = None, last_name: str = None) -> Dict[str, Any]:
    """Create a new user profile in the database"""
    try:
        with app.app_context():
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                risk_profile='moderate',
                investment_horizon='medium',
                created_at=datetime.datetime.utcnow()
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'id': user.id,
                'username': user.username or 'Unknown',
                'risk_profile': user.risk_profile or 'moderate',
                'investment_horizon': user.investment_horizon or 'medium',
                'investment_goals': user.investment_goals or 'Not specified',
                'is_subscribed': user.is_subscribed or False,
                'created_at': user.created_at.strftime('%Y-%m-%d')
            }
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        
        # Return fallback profile on error
        return {
            'id': user_id,
            'username': username or 'Unknown',
            'risk_profile': 'moderate',
            'investment_horizon': 'medium',
            'investment_goals': 'Not specified',
            'is_subscribed': False,
            'created_at': 'N/A'
        }

# Callback query handlers
async def handle_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Handle callback queries from buttons, returning True if handled
    """
    query = update.callback_query
    if not query:
        return False
    
    await query.answer()
    user_id = update.effective_user.id if update.effective_user else 0
    
    try:
        # Log the callback
        logger.info(f"User {user_id} pressed button with data: {query.data}")
        
        # Handle different button actions
        if query.data == "pools":
            # Show pool data
            pools = get_pools(5)
            
            if pools:
                message = "*📊 Liquidity Pool Data*\n\n"
                for i, pool in enumerate(pools, 1):
                    fee_percentage = pool.get('fee', 0) * 100
                    volume = pool.get('volume_24h', 0)
                    
                    message += (
                        f"{i}. *{pool['token_a']}-{pool['token_b']}*\n"
                        f"   • APR: {pool['apr_24h']:.2f}%\n"
                        f"   • TVL: ${pool['tvl']:,.2f}\n"
                        f"   • Fee: {fee_percentage:.3f}%\n"
                        f"   • 24h Volume: ${volume:,.2f}\n"
                    )
                    
                    if 'dex' in pool:
                        message += f"   • DEX: {pool['dex']}\n"
                    
                    message += "\n"
                
                # Add note about data source
                if pools and 'data_source' in pools[0]:
                    message += f"_Data source: {pools[0]['data_source']}_\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔍 Get Predictions", callback_data="predictions")],
                    [InlineKeyboardButton("📈 Historical Data", callback_data="history")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
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
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
        
        elif query.data == "high_apr":
            # Show high APR pools
            high_apr_pools = get_high_apr_pools(3)
            
            if high_apr_pools:
                message = "*📈 Top High APR Pools*\n\n"
                message += "These are the highest APR pools currently available on Raydium:\n\n"
                
                for i, pool in enumerate(high_apr_pools, 1):
                    fee_percentage = pool.get('fee', 0) * 100
                    volume = pool.get('volume_24h', 0)
                    
                    message += (
                        f"{i}. *{pool['token_a']}-{pool['token_b']}*\n"
                        f"   • APR: {pool['apr_24h']:.2f}% 🔥\n"
                        f"   • TVL: ${pool['tvl']:,.2f}\n"
                        f"   • Fee: {fee_percentage:.3f}%\n"
                        f"   • 24h Volume: ${volume:,.2f}\n"
                    )
                    
                    # Add prediction score if available
                    if 'prediction_score' in pool and pool['prediction_score'] > 0:
                        message += f"   • Prediction Score: {pool['prediction_score']}/100\n"
                        
                    message += "\n"
                
                # Add note about data source
                if high_apr_pools and 'data_source' in high_apr_pools[0]:
                    message += f"_Data source: {high_apr_pools[0]['data_source']}_\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔮 Simulate Investment", callback_data="simulate")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
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
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
            
        elif query.data == "predictions":
            # Get prediction data from SolPool API
            try:
                # Try to get prediction data
                predictions = solpool_api.get_predictions(min_score=70, limit=3)
                
                if predictions and len(predictions) > 0:
                    message = "*🔮 Top Pool Predictions*\n\n"
                    message += "AI-powered predictions for the best performing pools:\n\n"
                    
                    for i, pred in enumerate(predictions, 1):
                        message += (
                            f"{i}. *{pred.get('name', '')}*\n"
                            f"   • Current APR: {pred.get('current_apr', 0):.2f}%\n"
                            f"   • Predicted APR: {pred.get('predicted_apr_mid', 0):.2f}%\n"
                            f"   • Confidence: {pred.get('prediction_score', 0)}/100\n"
                            f"   • TVL: ${pred.get('current_tvl', 0):,.2f}\n"
                        )
                        
                        # Add key factors if available
                        factors = pred.get('key_factors', [])
                        if factors and len(factors) > 0:
                            message += "   • Key Factors:\n"
                            for factor in factors[:2]:  # Limit to 2 factors for readability
                                message += f"     - {factor}\n"
                        
                        message += "\n"
                    
                    message += "_Data source: SolPool Insight API_\n"
                    
                else:
                    message = "*🔮 Pool Predictions*\n\n"
                    message += "Currently unable to retrieve prediction data. Please try again later.\n"
            
            except Exception as e:
                logger.error(f"Error getting predictions: {e}")
                message = "*🔮 Pool Predictions*\n\n"
                message += "Currently unable to retrieve prediction data. Please try again later.\n"
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
            
        elif query.data == "history":
            # Show historical pool performance
            try:
                # First, get a top pool to analyze
                pools = get_pools(1)
                
                if pools and len(pools) > 0:
                    pool = pools[0]
                    pool_id = pool.get('id', '')
                    pool_name = f"{pool['token_a']}-{pool['token_b']}"
                    
                    # Try to get historical data for this pool
                    history = []
                    if pool_id:
                        history = solpool_api.get_pool_history(pool_id, days=14, interval="day")
                    
                    message = f"*📈 Historical Performance: {pool_name}*\n\n"
                    
                    if history and len(history) > 0:
                        # Calculate trends
                        apr_values = [h.get('apr', 0) for h in history if 'apr' in h]
                        tvl_values = [h.get('liquidity', 0) for h in history if 'liquidity' in h]
                        volume_values = [h.get('volume', 0) for h in history if 'volume' in h]
                        
                        if apr_values and len(apr_values) > 1:
                            apr_change = ((apr_values[0] / apr_values[-1]) - 1) * 100 if apr_values[-1] else 0
                            apr_trend = "↗️" if apr_change > 0 else "↘️" if apr_change < 0 else "➡️"
                            message += f"*APR Trend (14 days):* {apr_trend} {abs(apr_change):.2f}%\n"
                        
                        if tvl_values and len(tvl_values) > 1:
                            tvl_change = ((tvl_values[0] / tvl_values[-1]) - 1) * 100 if tvl_values[-1] else 0
                            tvl_trend = "↗️" if tvl_change > 0 else "↘️" if tvl_change < 0 else "➡️"
                            message += f"*TVL Trend (14 days):* {tvl_trend} {abs(tvl_change):.2f}%\n"
                        
                        if volume_values and len(volume_values) > 1:
                            vol_change = ((volume_values[0] / volume_values[-1]) - 1) * 100 if volume_values[-1] else 0
                            vol_trend = "↗️" if vol_change > 0 else "↘️" if vol_change < 0 else "➡️"
                            message += f"*Volume Trend (14 days):* {vol_trend} {abs(vol_change):.2f}%\n\n"
                        
                        # Include some daily data points
                        message += "*Recent Daily Performance:*\n"
                        for i, day_data in enumerate(history[:5]):  # Show only the most recent 5 days
                            date = day_data.get('timestamp', '').split('T')[0] if 'timestamp' in day_data else f"Day {i+1}"
                            apr = day_data.get('apr', 0)
                            liquidity = day_data.get('liquidity', 0)
                            
                            message += f"• {date}: APR {apr:.2f}%, TVL ${liquidity:,.2f}\n"
                        
                        message += "\n_Data source: SolPool Insight API_"
                    else:
                        message += "Historical performance data is not available for this pool at the moment.\n\n"
                        message += "You can still view current data and predictions."
                else:
                    message = "*📈 Historical Performance*\n\n"
                    message += "Unable to retrieve pool data for historical analysis.\n"
                    message += "Please try again later."
                
                keyboard = [
                    [InlineKeyboardButton("🔍 View More Pools", callback_data="pools")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ]
                
            except Exception as e:
                logger.error(f"Error retrieving historical data: {e}")
                message = "*📈 Historical Performance*\n\n"
                message += "Sorry, we encountered an error while retrieving historical data.\n"
                message += "Please try again later."
                
                keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        elif query.data == "profile":
            # Show user profile
            profile = get_user_profile(user_id)
            
            if profile:
                # User exists
                message = (
                    f"*👤 Your Profile*\n\n"
                    f"• *Username:* {profile['username']}\n"
                    f"• *Risk Profile:* {profile['risk_profile'].capitalize()}\n"
                    f"• *Investment Horizon:* {profile['investment_horizon'].capitalize()}\n"
                    f"• *Investment Goals:* {profile['investment_goals']}\n"
                    f"• *Subscribed to Updates:* {'Yes' if profile['is_subscribed'] else 'No'}\n"
                    f"• *Account Created:* {profile['created_at']}\n\n"
                    "This data is retrieved directly from our database."
                )
            else:
                # Create new user
                new_profile = create_user_profile(
                    user_id, 
                    update.effective_user.username if update.effective_user else "User", 
                    update.effective_user.first_name if update.effective_user else None,
                    update.effective_user.last_name if update.effective_user else None
                )
                
                message = (
                    f"*👤 Your Profile (New User)*\n\n"
                    f"• *Username:* {new_profile['username']}\n"
                    f"• *Risk Profile:* {new_profile['risk_profile'].capitalize()} (default)\n"
                    f"• *Investment Horizon:* {new_profile['investment_horizon'].capitalize()} (default)\n"
                    f"• *Investment Goals:* {new_profile['investment_goals']}\n"
                    f"• *Subscribed to Updates:* {'Yes' if new_profile['is_subscribed'] else 'No'}\n\n"
                    "Your profile has been created in our database."
                )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        elif query.data == "faq":
            # Show FAQ
            message = (
                "*❓ Frequently Asked Questions*\n\n"
                "Choose a topic to learn more:\n\n"
                "• *Liquidity Pools:* What they are and how they work\n"
                "• *APR:* Understanding Annual Percentage Rate\n"
                "• *Impermanent Loss:* What it is and how to minimize it\n"
                "• *Wallets:* How to connect and use wallets securely"
            )
            
            keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        elif query.data == "simulate":
            # Simulate investment returns for a user
            try:
                # Get high APR pools for simulation
                high_apr_pools = get_high_apr_pools(1)  # Just get the top pool
                
                if high_apr_pools and len(high_apr_pools) > 0:
                    pool = high_apr_pools[0]
                    
                    # Get user profile for risk assessment
                    profile = get_user_profile(user_id)
                    risk_profile = profile.get('risk_profile', 'moderate') if profile else 'moderate'
                    
                    # Set sample investment amount based on risk profile
                    if risk_profile == 'conservative':
                        investment_amount = 1000
                        timeframe = 30  # 1 month
                    elif risk_profile == 'aggressive':
                        investment_amount = 5000
                        timeframe = 365  # 1 year
                    else:  # moderate
                        investment_amount = 2500
                        timeframe = 180  # 6 months
                    
                    # Calculate investment returns
                    apr = pool['apr_24h']
                    daily_rate = apr / 365 / 100
                    
                    # Calculate expected return for the timeframe
                    expected_return = investment_amount * (1 + daily_rate) ** timeframe
                    profit = expected_return - investment_amount
                    profit_percentage = (profit / investment_amount) * 100
                    
                    # Add some variability based on the prediction score if available
                    prediction_score = pool.get('prediction_score', 75)
                    confidence_factor = prediction_score / 100
                    
                    # Calculate low and high range estimates
                    optimistic_return = expected_return * (1 + (1 - confidence_factor) * 0.2)
                    pessimistic_return = expected_return * (1 - (1 - confidence_factor) * 0.3)
                    
                    # Format the message
                    message = (
                        f"*🔮 Investment Simulation for {pool['token_a']}-{pool['token_b']}*\n\n"
                        f"Based on your {risk_profile} risk profile, here's a simulation:\n\n"
                        f"• Initial Investment: ${investment_amount:,.2f}\n"
                        f"• Current APR: {apr:.2f}%\n"
                        f"• Timeframe: {timeframe} days\n\n"
                        f"*Expected Returns:*\n"
                        f"• Final Balance: ${expected_return:,.2f}\n"
                        f"• Profit: ${profit:,.2f} ({profit_percentage:.2f}%)\n\n"
                    )
                    
                    # Add range if prediction score is available
                    if 'prediction_score' in pool:
                        message += (
                            f"*Prediction Range (Confidence: {prediction_score}/100):*\n"
                            f"• Conservative Estimate: ${pessimistic_return:,.2f}\n"
                            f"• Optimistic Estimate: ${optimistic_return:,.2f}\n\n"
                        )
                    
                    message += (
                        "_This is a simulation based on current rates. "
                        "Actual returns may vary due to market conditions._\n\n"
                        "_Data source: " + (pool.get('data_source', 'SolPool API')) + "_"
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 View All Pools", callback_data="pools")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ]
                    
                else:
                    message = (
                        "*🔮 Investment Simulation*\n\n"
                        "Sorry, we couldn't retrieve pool data for simulation. "
                        "Please try again later."
                    )
                    
                    keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            except Exception as e:
                logger.error(f"Error in investment simulation: {e}")
                message = (
                    "*🔮 Investment Simulation*\n\n"
                    "Sorry, we encountered an error while running the simulation. "
                    "Please try again later."
                )
                
                keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
            
        elif query.data == "token_search":
            # Show the token search menu
            common_tokens = ["SOL", "USDC", "BONK", "JTO", "PYTH", "RAY"]
            keyboard = []
            
            # Add popular tokens as buttons
            for token in common_tokens:
                keyboard.append([InlineKeyboardButton(f"Search {token} Pools", callback_data=f"search_token_{token}")])
            
            # Add back button
            keyboard.append([InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")])
            
            message = (
                "*🔍 Search Pools by Token*\n\n"
                "Select a token to find all liquidity pools that include it:\n\n"
                "This will show you pool data, APR, and market sentiment in one view."
            )
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
            
        elif query.data.startswith("search_token_"):
            # Search for pools containing the selected token
            token = query.data.replace("search_token_", "")
            
            try:
                # Get pools containing this token
                token_pools = solpool_api.get_token_pools(token, limit=3)
                
                # Try to get sentiment data for this token
                sentiment_data = sentiment_api.get_sentiment_data(token)
                price_data = sentiment_api.get_price_data(token)
                
                # Build the message
                message = f"*🔍 {token} Pools and Market Data*\n\n"
                
                # Add sentiment data if available
                if sentiment_data.get("status") == "success" and token.upper() in sentiment_data.get("sentiment", {}):
                    token_sentiment = sentiment_data["sentiment"][token.upper()]
                    sentiment_score = token_sentiment.get("score", 0)
                    
                    # Convert sentiment score to emoji and description
                    if sentiment_score >= 0.5:
                        sentiment_emoji = "🟢"
                        sentiment_desc = "Very Positive"
                    elif sentiment_score >= 0.2:
                        sentiment_emoji = "🟢"
                        sentiment_desc = "Positive"
                    elif sentiment_score >= -0.2:
                        sentiment_emoji = "🟡"
                        sentiment_desc = "Neutral"
                    elif sentiment_score >= -0.5:
                        sentiment_emoji = "🔴"
                        sentiment_desc = "Negative"
                    else:
                        sentiment_emoji = "🔴"
                        sentiment_desc = "Very Negative"
                    
                    message += f"*Market Sentiment:* {sentiment_emoji} {sentiment_desc} ({sentiment_score:.2f})\n"
                
                # Add price data if available
                if price_data.get("status") == "success" and token.upper() in price_data.get("prices", {}):
                    token_price = price_data["prices"][token.upper()]
                    price = token_price.get("price_usd", 0)
                    change_24h = token_price.get("percent_change_24h", 0)
                    
                    # Add emoji based on price change
                    change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                    
                    message += f"*Current Price:* ${price:,.6f}\n"
                    message += f"*24h Change:* {change_emoji} {change_24h:.2f}%\n\n"
                
                # Add pools data
                if token_pools and len(token_pools) > 0:
                    message += "*Available Liquidity Pools:*\n\n"
                    
                    for i, pool in enumerate(token_pools, 1):
                        pair = f"{pool.get('token_a_symbol', '')}-{pool.get('token_b_symbol', '')}"
                        apr = pool.get('apr_24h', 0)
                        tvl = pool.get('tvl', 0)
                        
                        message += (
                            f"{i}. *{pair}*\n"
                            f"   • APR: {apr:.2f}%\n"
                            f"   • TVL: ${tvl:,.2f}\n"
                        )
                        
                        # Add prediction score if available
                        if 'prediction_score' in pool and pool['prediction_score'] > 0:
                            message += f"   • AI Score: {pool['prediction_score']}/100\n"
                        
                        message += "\n"
                        
                    message += "_Data sources: SolPool Insight API, FilotSense API_"
                else:
                    message += "*No pools found for this token*\n\n"
                    message += "This token may not have active liquidity pools or our data sources may not track it yet."
                
                # Add navigation buttons
                keyboard = [
                    [InlineKeyboardButton("🔍 Search Another Token", callback_data="token_search")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Error searching for token {token}: {e}")
                message = (
                    f"*Error Searching for {token}*\n\n"
                    "Sorry, we encountered an error while searching for pools with this token.\n"
                    "Please try again later or select a different token."
                )
                
                keyboard = [
                    [InlineKeyboardButton("🔍 Try Another Token", callback_data="token_search")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            
            return True
            
        elif query.data == "sentiment":
            # Show overall market sentiment data
            try:
                # Get sentiment data for major tokens
                sentiment_data = sentiment_api.get_sentiment_data()
                
                if sentiment_data.get("status") == "success" and sentiment_data.get("sentiment"):
                    message = "*💬 Market Sentiment Analysis*\n\n"
                    message += "Current sentiment for major cryptocurrencies:\n\n"
                    
                    # Select important tokens to display
                    important_tokens = ["SOL", "BTC", "ETH", "USDC", "BONK", "JTO"]
                    sentiment_dict = sentiment_data.get("sentiment", {})
                    
                    for token in important_tokens:
                        if token in sentiment_dict:
                            score = sentiment_dict[token].get("score", 0)
                            
                            # Convert sentiment score to emoji and description
                            if score >= 0.5:
                                emoji = "🟢"
                                desc = "Very Positive"
                            elif score >= 0.2:
                                emoji = "🟢"
                                desc = "Positive"
                            elif score >= -0.2:
                                emoji = "🟡"
                                desc = "Neutral"
                            elif score >= -0.5:
                                emoji = "🔴"
                                desc = "Negative"
                            else:
                                emoji = "🔴"
                                desc = "Very Negative"
                            
                            message += f"*{token}:* {emoji} {desc} ({score:.2f})\n"
                    
                    # Try to get topic sentiment for SOL
                    topic_data = sentiment_api.get_topic_sentiment("SOL")
                    if topic_data.get("status") == "success" and "SOL" in topic_data.get("data", {}):
                        message += "\n*Solana (SOL) Sentiment by Topic:*\n"
                        
                        topics = topic_data["data"]["SOL"].get("topics", {})
                        for topic, score in topics.items():
                            # Convert topic sentiment score to emoji
                            if score >= 0.3:
                                emoji = "🟢"
                            elif score >= -0.3:
                                emoji = "🟡"
                            else:
                                emoji = "🔴"
                            
                            message += f"• {topic.capitalize()}: {emoji} ({score:.2f})\n"
                    
                    message += "\n_Data source: FilotSense API_"
                    
                else:
                    message = "*💬 Market Sentiment Analysis*\n\n"
                    message += "Unable to retrieve sentiment data at this time.\n"
                    message += "Please try again later."
                
                keyboard = [
                    [InlineKeyboardButton("🔍 Search Token Pools", callback_data="token_search")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                
            except Exception as e:
                logger.error(f"Error retrieving sentiment data: {e}")
                message = (
                    "*💬 Market Sentiment Analysis*\n\n"
                    "Sorry, we encountered an error while retrieving sentiment data.\n"
                    "Please try again later."
                )
                
                keyboard = [[InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]]
                
                await query.edit_message_text(
                    message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
            
            return True
            
        elif query.data == "back":
            # Back to main menu
            keyboard = [
                [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
                [InlineKeyboardButton("📈 View High APR Pools", callback_data="high_apr")],
                [InlineKeyboardButton("🔍 Search by Token", callback_data="token_search")],
                [InlineKeyboardButton("🔮 View AI Predictions", callback_data="predictions")],
                [InlineKeyboardButton("💬 Market Sentiment", callback_data="sentiment")],
                [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
                [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
            ]
            
            # Check if APIs are available for status message
            is_pool_api_available = solpool_api.api_health_check()
            is_sentiment_api_available = sentiment_api.api_health_check()
            
            message = "*FiLot Interactive Menu*\n\n"
            
            if is_pool_api_available and is_sentiment_api_available:
                message += "Connected to real-time pool data and sentiment analysis.\n"
            elif is_pool_api_available:
                message += "Connected to real-time pool data. Sentiment analysis unavailable.\n"
            elif is_sentiment_api_available:
                message += "Connected to sentiment analysis. Pool data limited.\n"
            else:
                message += "Using database fallbacks. External APIs unavailable.\n"
                
            message += "Click any option to explore:"
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return True
        
        # If not handled, return False
        return False
        
    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        try:
            await query.edit_message_text(
                "Sorry, an error occurred while processing your request. Please try again later.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )
        except Exception:
            pass
        return True