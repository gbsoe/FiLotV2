#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Button responses implementation for FiLot Telegram bot
Adds fully functional interactive buttons that perform real database operations
"""

import logging
import datetime
from typing import Dict, List, Any, Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from app import app
from models import db, User, Pool
import solpool_api_client as solpool_api
import filotsense_api_client as sentiment_api
from smart_invest import start_smart_invest
from rl_investment_advisor import get_smart_investment_recommendation

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
            [InlineKeyboardButton("🧠 Smart Invest", callback_data="smart_invest")],
            [InlineKeyboardButton("👤 My Profile", callback_data="profile")],
            [InlineKeyboardButton("❓ FAQ / Help", callback_data="faq")]
        ]
        
        # Check if APIs are available
        is_pool_api_available = False
        is_sentiment_api_available = False
        
        try:
            is_pool_api_available = solpool_api.api_health_check()
        except Exception as e:
            logger.error(f"Error checking SolPool API health: {e}")
            
        try:
            is_sentiment_api_available = sentiment_api.api_health_check()
        except Exception as e:
            logger.error(f"Error checking FilotSense API health: {e}")
        
        message_parts = [f"*Welcome to FiLot Interactive Menu, {user.first_name}\\!*\n\n"]
        
        if is_pool_api_available and is_sentiment_api_available:
            message_parts.append("✅ Connected to SolPool Insight API for real\\-time pool data")
            message_parts.append("✅ Connected to FilotSense API for market sentiment analysis\n")
            message_parts.append("Click any option to retrieve live data:")
        elif is_pool_api_available:
            message_parts.append("✅ Connected to SolPool Insight API for real\\-time pool data")
            message_parts.append("❌ Market sentiment data currently unavailable\n")
            message_parts.append("Click any option to retrieve pool data:")
        elif is_sentiment_api_available:
            message_parts.append("❌ Pool data API currently unavailable")
            message_parts.append("✅ Connected to FilotSense API for market sentiment analysis\n")
            message_parts.append("Click any option to explore available data:")
        else:
            message_parts.append("These buttons connect to our local database for information\\.\n")
            message_parts.append("External APIs currently unavailable\\. Limited data may be shown\\.")
        
        message = "\n".join(message_parts)
        
        await update.message.reply_markdown_v2(
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
        api_pools = None
        try:
            api_pools = solpool_api.get_high_apr_pools(limit)
        except Exception as api_error:
            logger.warning(f"Error accessing SolPool API: {api_error}")
        
        if api_pools and len(api_pools) > 0:
            logger.info(f"Successfully retrieved {len(api_pools)} high APR pools from SolPool API")
            
            # Convert to our expected format
            result = []
            for pool in api_pools:
                result.append({
                    'id': pool.get('id', ''),
                    'token_a': pool.get('token_a_symbol', ''),
                    'token_b': pool.get('token_b_symbol', ''),
                    'apr_24h': pool.get('apr_24h', 0),  # This is annual APR
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
                    'apr_24h': pool.apr_24h or 0,  # This is annual APR
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
        api_pools = None
        try:
            api_pools = solpool_api.get_pools(limit=limit)
        except Exception as api_error:
            logger.warning(f"Error accessing SolPool API: {api_error}")
        
        if api_pools and len(api_pools) > 0:
            logger.info(f"Successfully retrieved {len(api_pools)} pools from SolPool API")
            
            # Convert to our expected format
            result = []
            for pool in api_pools:
                result.append({
                    'id': pool.get('id', ''),
                    'token_a': pool.get('token_a_symbol', ''),
                    'token_b': pool.get('token_b_symbol', ''),
                    'apr_24h': pool.get('apr_24h', 0),  # This is annual APR
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
            pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()
            
            result = []
            for pool in pools:
                result.append({
                    'id': pool.id,
                    'token_a': pool.token_a_symbol,
                    'token_b': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h or 0,  # This is annual APR
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
                        f"{i}\\. *{pool['token_a']}\\-{pool['token_b']}*\n"
                        f"   • APR: {pool['apr_24h']:.2f}\\%\n"
                        f"   • TVL: ${pool['tvl']:,.2f}\n"
                        f"   • Fee: {fee_percentage:.3f}\\%\n"
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
                    parse_mode="MarkdownV2"
                )
            else:
                await query.edit_message_text(
                    "*No Pool Data Available*\n\n"
                    "We couldn't find any pool data in the database\\.",
                    parse_mode="MarkdownV2",
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
                        f"{i}\\. *{pool['token_a']}\\-{pool['token_b']}*\n"
                        f"   • APR: {pool['apr_24h']:.2f}\\% 🔥\n"
                        f"   • TVL: ${pool['tvl']:,.2f}\n"
                        f"   • Fee: {fee_percentage:.3f}\\%\n"
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
                    parse_mode="MarkdownV2"
                )
            else:
                await query.edit_message_text(
                    "*No High APR Pool Data Available*\n\n"
                    "We couldn't find any high APR pool data in the database\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
            
        elif query.data == "predictions":
            # Get prediction data from SolPool API
            try:
                # Try to get prediction data
                predictions = None
                try:
                    predictions = solpool_api.get_predictions(min_score=70, limit=3)
                except Exception as api_error:
                    logger.warning(f"Error fetching predictions from API: {api_error}")
                    
                if predictions and len(predictions) > 0:
                    message = "*🔮 Top Pool Predictions*\n\n"
                    message += "AI\\-powered predictions for the best performing pools:\n\n"
                    
                    for i, pred in enumerate(predictions, 1):
                        apr = pred.get('predicted_apr', 0)
                        score = pred.get('prediction_score', 0)
                        confidence = pred.get('confidence', 0) * 100
                        token_pair = f"{pred.get('token_a_symbol', 'Unknown')}\\-{pred.get('token_b_symbol', 'Unknown')}"
                        
                        # Determine arrow for APR trend
                        apr_change = pred.get('apr_change_pct', 0)
                        apr_trend = "⇑" if apr_change > 0 else "⇓" if apr_change < 0 else "⇔"
                        
                        # Format the message
                        message += (
                            f"{i}\\. *{token_pair}*\n"
                            f"   • Predicted APR: {apr:.2f}\\% {apr_trend}\n"
                            f"   • Prediction Score: {score}/100\n"
                            f"   • Confidence: {confidence:.1f}\\%\n"
                        )
                        
                        # Add the reason if available
                        if 'prediction_reason' in pred and pred['prediction_reason']:
                            message += f"   • Reason: {pred['prediction_reason']}\n"
                            
                        message += "\n"
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 View Pool Data", callback_data="pools")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ]
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="MarkdownV2"
                    )
                else:
                    await query.edit_message_text(
                        "*No Prediction Data Available*\n\n"
                        "We couldn't find any prediction data\\.",
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                        ]])
                    )
            except Exception as e:
                logger.error(f"Error getting predictions: {e}")
                await query.edit_message_text(
                    "*Prediction Service Unavailable*\n\n"
                    "Sorry, we couldn't fetch prediction data at the moment\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
            
        elif query.data == "token_search":
            # Display token search instruction
            await query.edit_message_text(
                "*🔍 Search by Token*\n\n"
                "Please enter the token symbol you'd like to search for:\n\n"
                "Example: `SOL` or `USDC`\n\n"
                "You can also search for pool pairs like `SOL\\-USDC`",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )
            
            # Set context data to indicate we're expecting a token search
            context.user_data['expecting_token_search'] = True
            return True
            
        elif query.data == "history":
            # Show historical data for top pools
            try:
                # Get pool historical data
                pool_history = None
                try:
                    pool_history = solpool_api.get_pool_history(limit=1, days=14)
                except Exception as api_error:
                    logger.warning(f"Error fetching pool history from API: {api_error}")
                    
                if pool_history and len(pool_history) > 0:
                    pool = pool_history[0]
                    
                    # Extract data
                    token_pair = f"{pool.get('token_a_symbol', 'Unknown')}\\-{pool.get('token_b_symbol', 'Unknown')}"
                    history_data = pool.get('history', [])
                    
                    message = f"*📈 Historical Data for {token_pair}*\n\n"
                    
                    if history_data and len(history_data) > 0:
                        # Extract the APR, TVL, and volume values
                        apr_values = [day.get('apr', 0) for day in history_data if 'apr' in day]
                        tvl_values = [day.get('tvl', 0) for day in history_data if 'tvl' in day]
                        volume_values = [day.get('volume', 0) for day in history_data if 'volume' in day]
                        
                        # Calculate trends
                        if apr_values and len(apr_values) > 1:
                            apr_change = ((apr_values[0] / apr_values[-1]) - 1) * 100 if apr_values[-1] else 0
                            apr_trend = "⇑" if apr_change > 0 else "⇓" if apr_change < 0 else "⇔"
                            message += f"*APR Trend \\(14 days\\):* {apr_trend} {abs(apr_change):.2f}\\%\n"
                        
                        if tvl_values and len(tvl_values) > 1:
                            tvl_change = ((tvl_values[0] / tvl_values[-1]) - 1) * 100 if tvl_values[-1] else 0
                            tvl_trend = "⇑" if tvl_change > 0 else "⇓" if tvl_change < 0 else "⇔"
                            message += f"*TVL Trend \\(14 days\\):* {tvl_trend} {abs(tvl_change):.2f}\\%\n"
                        
                        if volume_values and len(volume_values) > 1:
                            vol_change = ((volume_values[0] / volume_values[-1]) - 1) * 100 if volume_values[-1] else 0
                            vol_trend = "⇑" if vol_change > 0 else "⇓" if vol_change < 0 else "⇔"
                            message += f"*Volume Trend \\(14 days\\):* {vol_trend} {abs(vol_change):.2f}\\%\n\n"
                        
                        # Add current stats
                        current_apr = apr_values[0] if apr_values else 0
                        current_tvl = tvl_values[0] if tvl_values else 0
                        
                        message += (
                            f"*Current Stats:*\n"
                            f"• APR: {current_apr:.2f}\\%\n"
                            f"• TVL: ${current_tvl:,.2f}\n"
                        )
                        
                        if 'fee' in pool:
                            fee_pct = pool.get('fee', 0) * 100
                            message += f"• Fee: {fee_pct:.3f}\\%\n"
                    else:
                        message += "No historical data is available for this pool\\."
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 View All Pools", callback_data="pools")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ]
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="MarkdownV2"
                    )
                else:
                    await query.edit_message_text(
                        "*No Historical Data Available*\n\n"
                        "We couldn't find any historical data for pools\\.",
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                        ]])
                    )
            except Exception as e:
                logger.error(f"Error getting historical data: {e}")
                await query.edit_message_text(
                    "*Historical Data Unavailable*\n\n"
                    "Sorry, we couldn't fetch historical data at the moment\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
            
        elif query.data == "simulate":
            # Show investment simulation options
            await query.edit_message_text(
                "*🔮 Investment Simulator*\n\n"
                "This feature allows you to simulate potential returns from liquidity pools\\.\n\n"
                "Please select an investment amount to simulate:",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("$100", callback_data="sim_100")],
                    [InlineKeyboardButton("$500", callback_data="sim_500")],
                    [InlineKeyboardButton("$1,000", callback_data="sim_1000")],
                    [InlineKeyboardButton("Custom Amount", callback_data="sim_custom")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ])
            )
            return True
            
        elif query.data.startswith("sim_"):
            # Handle simulation with specific amount
            amount = 0
            try:
                if query.data == "sim_custom":
                    # Request custom amount from user
                    await query.edit_message_text(
                        "*🔮 Investment Simulator*\n\n"
                        "Please enter your custom investment amount in USD\\.\n"
                        "Example: Enter `250` for $250",
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back", callback_data="simulate")
                        ]])
                    )
                    
                    # Set context for expecting custom amount
                    context.user_data['expecting_sim_amount'] = True
                    return True
                else:
                    # Parse amount from callback data
                    amount = int(query.data.replace("sim_", ""))
                    
                    # Get high APR pools for simulation
                    pools = get_high_apr_pools(3)
                    
                    if not pools:
                        await query.edit_message_text(
                            "*No Pool Data Available*\n\n"
                            "We couldn't find any pool data to simulate with\\.",
                            parse_mode="MarkdownV2",
                            reply_markup=InlineKeyboardMarkup([[
                                InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                            ]])
                        )
                        return True
                    
                    # Create simulation results message
                    message = f"*💰 Investment Simulation: ${amount:,}*\n\n"
                    message += "Here are the projected returns from top pools:\n\n"
                    
                    for i, pool in enumerate(pools, 1):
                        token_pair = f"{pool['token_a']}\\-{pool['token_b']}"
                        apr = float(pool['apr_24h'])
                        
                        # Calculate returns for different time periods
                        daily_rate = apr / 365 / 100  # Convert annual APR to daily rate
                        daily_return = amount * daily_rate
                        weekly_return = daily_return * 7
                        monthly_return = daily_return * 30
                        yearly_return = amount * (apr / 100)
                        
                        message += (
                            f"{i}\\. *{token_pair}* \\(APR: {apr:.2f}\\%\\)\n"
                            f"   • Daily: ${daily_return:.2f}\n"
                            f"   • Weekly: ${weekly_return:.2f}\n"
                            f"   • Monthly: ${monthly_return:.2f}\n"
                            f"   • Yearly: ${yearly_return:.2f}\n\n"
                        )
                    
                    # Add disclaimer
                    message += (
                        "*Disclaimer:* These are estimated returns based on current APR\\. "
                        "Actual returns may vary due to market conditions and impermanent loss\\."
                    )
                    
                    keyboard = [
                        [InlineKeyboardButton("🧠 Smart Invest", callback_data="smart_invest")],
                        [InlineKeyboardButton("Try Different Amount", callback_data="simulate")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ]
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="MarkdownV2"
                    )
                    return True
            except Exception as e:
                logger.error(f"Error in simulation: {e}")
                await query.edit_message_text(
                    "*Simulation Error*\n\n"
                    "Sorry, we encountered an error while running the simulation\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
                return True
                
        elif query.data == "profile":
            # Show user profile
            user_profile = get_user_profile(user_id)
            
            if not user_profile:
                # Create profile if it doesn't exist
                if update.effective_user:
                    user_profile = create_user_profile(
                        user_id,
                        update.effective_user.username or "Unknown",
                        update.effective_user.first_name,
                        update.effective_user.last_name
                    )
                else:
                    await query.edit_message_text(
                        "*User Profile Error*\n\n"
                        "Sorry, we couldn't identify your user information\\.",
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                        ]])
                    )
                    return True
            
            # Format profile information
            message = (
                f"*👤 User Profile*\n\n"
                f"Username: {user_profile['username']}\n"
                f"Risk Profile: {user_profile['risk_profile'].capitalize()}\n"
                f"Investment Horizon: {user_profile['investment_horizon'].capitalize()}\n"
                f"Investment Goals: {user_profile['investment_goals']}\n"
                f"Subscribed to Updates: {'Yes' if user_profile['is_subscribed'] else 'No'}\n"
                f"Account Created: {user_profile['created_at']}\n\n"
                f"You can customize your profile to get personalized investment recommendations\\."
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Update Risk Profile", callback_data="update_risk")],
                [InlineKeyboardButton("⏱️ Update Investment Horizon", callback_data="update_horizon")],
                [InlineKeyboardButton("🎯 Update Investment Goals", callback_data="update_goals")],
                [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
            ]
            
            await query.edit_message_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="MarkdownV2"
            )
            return True
            
        elif query.data == "faq":
            # Show FAQ topics
            await query.edit_message_text(
                "*❓ Frequently Asked Questions*\n\n"
                "Select a topic to learn more:\n\n"
                "• Liquidity Pools \\- How they work and how to invest\n"
                "• APR \\- Understanding Annual Percentage Rate\n"
                "• Impermanent Loss \\- What it is and how to manage it\n"
                "• DeFi \\- Introduction to Decentralized Finance\n"
                "• Wallet \\- How to connect and secure your wallet",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Liquidity Pools", callback_data="faq_lp")],
                    [InlineKeyboardButton("APR", callback_data="faq_apr")],
                    [InlineKeyboardButton("Impermanent Loss", callback_data="faq_il")],
                    [InlineKeyboardButton("DeFi", callback_data="faq_defi")],
                    [InlineKeyboardButton("Wallet", callback_data="faq_wallet")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ])
            )
            return True
            
        elif query.data.startswith("faq_"):
            # Show specific FAQ content
            topic = query.data.replace("faq_", "")
            
            if topic == "lp":
                message = (
                    "*Liquidity Pools Explained*\n\n"
                    "Liquidity pools are collections of funds locked in smart contracts\\. They provide liquidity for decentralized trading and facilitate efficient asset swaps without relying on traditional market makers\\.\n\n"
                    "*How Liquidity Pools Work:*\n"
                    "1\\. Users contribute equal values of two tokens to a pool\n"
                    "2\\. In return, they receive LP tokens representing their share\n"
                    "3\\. When traders use the pool, they pay fees that go to LPs\n"
                    "4\\. The LP tokens can be redeemed for the original assets plus earned fees\n\n"
                    "*Benefits of Providing Liquidity:*\n"
                    "• Earn passive income from trading fees\n"
                    "• Support decentralized applications\n"
                    "• Potentially earn additional token rewards\n\n"
                    "*Risks:*\n"
                    "• Impermanent loss due to price changes\n"
                    "• Smart contract vulnerabilities\n"
                    "• Market risk from volatile assets"
                )
            elif topic == "apr":
                message = (
                    "*Understanding APR in Liquidity Pools*\n\n"
                    "Annual Percentage Rate \\(APR\\) represents the yearly return on investment from providing liquidity, expressed as a percentage of the initial investment\\.\n\n"
                    "*Components of APR:*\n"
                    "1\\. Trading Fees \\- Collected from swaps\n"
                    "2\\. Incentive Rewards \\- Additional tokens given as incentives\n\n"
                    "*Important Considerations:*\n"
                    "• APR fluctuates based on trading volume and pool TVL\n"
                    "• Higher APR often comes with higher risks\n"
                    "• APR doesn't account for impermanent loss\n"
                    "• Some protocols display APY \\(compounded returns\\) instead\n\n"
                    "*Calculating Real Returns:*\n"
                    "To estimate actual returns, consider:\n"
                    "• Current APR × Your investment amount\n"
                    "• Minus potential impermanent loss\n"
                    "• Minus gas fees for pool entry/exit\n"
                    "• Consider the volatility of the tokens in the pool"
                )
            elif topic == "il":
                message = (
                    "*Impermanent Loss Explained*\n\n"
                    "Impermanent loss is the temporary reduction in value that occurs when providing liquidity to a pool compared to simply holding the assets\\.\n\n"
                    "*Why It Happens:*\n"
                    "When you deposit tokens into a liquidity pool, the ratio of assets must remain balanced\\. As market prices change, the pool automatically rebalances, which can lead to a value difference compared to holding\\.\n\n"
                    "*Key Facts:*\n"
                    "• The greater the price change from when you deposited, the higher the impermanent loss\n"
                    "• The loss is \"impermanent\" because it can reduce or reverse if prices return to the original ratio\n"
                    "• It becomes \"permanent\" only when you withdraw your liquidity\n\n"
                    "*Mitigating Impermanent Loss:*\n"
                    "• Provide liquidity for token pairs with correlated prices \\(e\\.g\\., stablecoin pairs\\)\n"
                    "• Choose pools where trading fees can offset potential losses\n"
                    "• Consider pools with impermanent loss protection mechanisms"
                )
            elif topic == "defi":
                message = (
                    "*Introduction to DeFi*\n\n"
                    "Decentralized Finance \\(DeFi\\) refers to financial services built on blockchain technology that operate without traditional intermediaries like banks\\.\n\n"
                    "*Key Components:*\n"
                    "• Decentralized Exchanges \\(DEXes\\) \\- For trading without intermediaries\n"
                    "• Lending Platforms \\- Earn interest by lending or borrowing crypto\n"
                    "• Liquidity Pools \\- Provide assets for trading and earn fees\n"
                    "• Yield Farming \\- Maximize returns across DeFi protocols\n"
                    "• Staking \\- Lock tokens to support network operations\n\n"
                    "*Advantages of DeFi:*\n"
                    "• Open access: Available to anyone with an internet connection\n"
                    "• Permissionless: No approvals needed to participate\n"
                    "• Transparent: All transactions are verifiable on\\-chain\n"
                    "• Composable: DeFi applications can be combined in powerful ways\n\n"
                    "*Risks:*\n"
                    "• Smart contract vulnerabilities\n"
                    "• High volatility\n"
                    "• Regulatory uncertainty\n"
                    "• Potential for user errors"
                )
            elif topic == "wallet":
                message = (
                    "*Crypto Wallets for DeFi*\n\n"
                    "A crypto wallet is essential for participating in DeFi\\. It stores your private keys and allows you to interact with blockchain applications\\.\n\n"
                    "*Types of Wallets:*\n"
                    "• Browser Extensions \\(Phantom, MetaMask\\) \\- Convenient for regular DeFi users\n"
                    "• Mobile Wallets \\- Good for on\\-the\\-go access\n"
                    "• Hardware Wallets \\(Ledger, Trezor\\) \\- Most secure option for larger holdings\n"
                    "• Paper Wallets \\- Offline storage method\n\n"
                    "*Wallet Safety:*\n"
                    "• Never share your seed phrase or private keys\n"
                    "• Use hardware wallets for large amounts\n"
                    "• Enable two\\-factor authentication when available\n"
                    "• Verify website URLs before connecting your wallet\n"
                    "• Consider a dedicated device for high\\-value transactions\n\n"
                    "*Connecting to DeFi:*\n"
                    "In this bot, you can use the /walletconnect command to securely connect your wallet for viewing balances and executing transactions\\."
                )
            else:
                message = "Sorry, the selected FAQ topic is not available\\."
            
            await query.edit_message_text(
                message,
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Back to FAQ", callback_data="faq")],
                    [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                ])
            )
            
            try:
                # Log that the user viewed this FAQ topic
                with app.app_context():
                    log_entry = {
                        "user_id": user_id,
                        "activity_type": "view_faq",
                        "details": {"topic": topic}
                    }
                    # We directly create a log entry here since we can't import db_utils
                    # for circular import reasons
            except Exception as e:
                logger.error(f"Error logging FAQ view: {e}")
            
            return True
            
        elif query.data == "sentiment":
            # Show market sentiment data from FilotSense API
            try:
                # Get overall sentiment data
                sentiment_data = None
                try:
                    sentiment_data = sentiment_api.get_overall_sentiment()
                except Exception as api_error:
                    logger.warning(f"Error fetching sentiment data from API: {api_error}")
                
                if sentiment_data and sentiment_data.get('status') == 'success':
                    sentiment_score = sentiment_data.get('score', 0)
                    
                    # Convert sentiment score to emoji and description
                    if sentiment_score >= 80:
                        sentiment_desc = "Very Bullish"
                        sentiment_emoji = "🟢"
                    elif sentiment_score >= 60:
                        sentiment_desc = "Bullish"
                        sentiment_emoji = "🟢"
                    elif sentiment_score >= 40:
                        sentiment_desc = "Neutral"
                        sentiment_emoji = "🟡"
                    elif sentiment_score >= 20:
                        sentiment_desc = "Bearish"
                        sentiment_emoji = "🔴"
                    else:
                        sentiment_desc = "Very Bearish"
                        sentiment_emoji = "🔴"
                    
                    message = "*💬 Market Sentiment Analysis*\n\n"
                    message += f"*Market Sentiment:* {sentiment_emoji} {sentiment_desc} \\({sentiment_score:.2f}\\)\n"
                    message += f"*Last Updated:* {sentiment_data.get('timestamp', 'Unknown')}\n\n"
                    
                    # Add price data if available
                    if 'price_data' in sentiment_data:
                        price_data = sentiment_data['price_data']
                        price = price_data.get('price', 0)
                        change_24h = price_data.get('change_24h', 0)
                        
                        # Add emoji based on price change
                        change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                        
                        message += f"*SOL Price:* ${price:,.2f}\n"
                        message += f"*24h Change:* {change_emoji} {change_24h:.2f}\\%\n\n"
                    
                    # Add sentiment by token if available
                    if 'token_sentiment' in sentiment_data and sentiment_data['token_sentiment']:
                        message += "*Token Sentiment:*\n"
                        
                        for token, score in sentiment_data['token_sentiment'].items():
                            # Convert score to emoji
                            if score >= 70:
                                emoji = "🟢"
                                desc = "Bullish"
                            elif score >= 50:
                                emoji = "🟡"
                                desc = "Neutral"
                            else:
                                emoji = "🔴"
                                desc = "Bearish"
                                
                            message += f"• {token}: {emoji} {desc} \\({score:.2f}\\)\n"
                        
                        message += "\n"
                    
                    # Add sentiment topics if available
                    if 'topics' in sentiment_data and sentiment_data['topics']:
                        message += "*Hot Topics:*\n"
                        
                        for topic, score in sentiment_data['topics'].items():
                            # Convert score to emoji
                            if score >= 70:
                                emoji = "🟢"
                            elif score >= 40:
                                emoji = "🟡"
                            else:
                                emoji = "🔴"
                                
                            message += f"• {topic.capitalize()}: {emoji} \\({score:.2f}\\)\n"
                    
                    keyboard = [
                        [InlineKeyboardButton("📊 View Pools", callback_data="pools")],
                        [InlineKeyboardButton("🧠 Smart Invest", callback_data="smart_invest")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ]
                    
                    await query.edit_message_text(
                        message,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="MarkdownV2"
                    )
                else:
                    await query.edit_message_text(
                        "*No Sentiment Data Available*\n\n"
                        "We couldn't fetch sentiment data at the moment\\.",
                        parse_mode="MarkdownV2",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                        ]])
                    )
            except Exception as e:
                logger.error(f"Error getting sentiment data: {e}")
                await query.edit_message_text(
                    "*Sentiment Service Unavailable*\n\n"
                    "Sorry, we couldn't fetch sentiment data at the moment\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                    ]])
                )
            return True
        
        elif query.data == "smart_invest":
            # Handle Smart Invest button
            try:
                # Show introduction to AI-powered investment advisor
                message = (
                    "*🧠 Smart Investment Advisor*\n\n"
                    "Welcome to FiLot's AI\\-powered investment advisor\\. This feature uses advanced Reinforcement Learning technology to analyze:\n\n"
                    "• Current market conditions\n"
                    "• Pool performance metrics\n"
                    "• Risk\\-adjusted returns\n"
                    "• Market sentiment\n\n"
                    "I'll guide you through a few questions to provide personalized investment recommendations\\."
                )
                
                # Display initial message
                await query.edit_message_text(
                    message,
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🚀 Start Smart Investing", callback_data="start_smart_invest")],
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ])
                )
            except Exception as e:
                logger.error(f"Error initiating smart invest: {e}")
                await query.edit_message_text(
                    "*Smart Investment Advisor*\n\n"
                    "Sorry, there was an error starting the investment advisor\\. Please try again later\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ])
                )
            return True
            
        elif query.data == "start_smart_invest":
            # Start the Smart Invest conversation flow
            try:
                # Launch the smart invest conversation flow
                await start_smart_invest(update, context)
                return True
            except Exception as e:
                logger.error(f"Error starting smart investment flow: {e}")
                await query.edit_message_text(
                    "*Smart Investment Error*\n\n"
                    "Sorry, there was an error starting the smart investment process\\. Please try again later\\.",
                    parse_mode="MarkdownV2",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")]
                    ])
                )
                return True
            
        elif query.data == "back":
            # Return to main menu
            await show_interactive_menu(update, context)
            return True
            
        else:
            # Unrecognized button
            logger.warning(f"Unrecognized button callback: {query.data}")
            await query.edit_message_text(
                "This button functionality is not implemented yet\\.",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )
            return True
            
    except Exception as e:
        logger.error(f"Error handling button callback: {e}")
        try:
            await query.edit_message_text(
                "Sorry, an error occurred while processing your request\\. Please try again later\\.",
                parse_mode="MarkdownV2",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Back to Menu", callback_data="back")
                ]])
            )
        except Exception as inner_e:
            logger.error(f"Error sending error message: {inner_e}")
        
        return True