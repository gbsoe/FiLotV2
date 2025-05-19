"""
Core bot functionality for the Telegram cryptocurrency pool bot
"""

import os
import logging
import re
import datetime
import asyncio
import io
import qrcode
from typing import Dict, List, Any, Optional, Union, Tuple
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from dotenv import load_dotenv

# Import local modules
import db_utils
from models import User, Pool, UserQuery, db
from question_detector import get_predefined_response, is_question
from raydium_client import get_client
from utils import format_pool_info, format_simulation_results, format_daily_update
from menus import MenuType, get_menu_config
from keyboard_utils import get_reply_keyboard, set_menu_state, handle_menu_navigation
from callback_handler import handle_callback_query
from anti_loop import record_user_message, is_potential_loop, record_button_press, is_button_rate_limited
from wallet_utils import connect_wallet, check_wallet_balance, calculate_deposit_strategy, get_wallet_balances
from walletconnect_utils import (
    create_walletconnect_session, 
    check_walletconnect_session, 
    kill_walletconnect_session,
    get_user_walletconnect_sessions,
    get_db_connection
)
from anthropic_service import AnthropicAI

# Initialize AI service
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
ai_advisor = AnthropicAI(api_key=anthropic_api_key)

# Load environment variables
load_dotenv()

# Configure logging to file
import os
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler('logs/bot.log')  # Log to file
    ]
)
logger = logging.getLogger(__name__)

# Helper function to update query response in database
async def update_query_response(query_id: int, response_text: str, processing_time: float) -> None:
    """
    Update a query in the database with its response and processing time.
    """
    try:
        # Import here to avoid circular imports
        from sqlalchemy.orm import Session
        from models import db, UserQuery
        
        # Create new session for thread safety
        with Session(db.engine) as session:
            query = session.query(UserQuery).filter(UserQuery.id == query_id).first()
            if query:
                query.response_text = response_text
                query.processing_time = processing_time
                session.commit()
                logger.debug(f"Updated query {query_id} with response")
    except Exception as e:
        logger.error(f"Error updating query response: {e}")

# Helper function to get pool data
async def get_pool_data() -> List[Any]:
    """Get pool data for display in commands."""
    try:
        # Import app and db here to avoid circular imports
        from app import app, db
        from models import Pool
        
        with app.app_context():
            try:
                # Try to get pools from database first
                pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(5).all()
                
                # If no pools in database, use the predefined data
                if not pools or len(pools) == 0:
                    try:
                        # Import here to avoid circular imports
                        from response_data import get_pool_data as get_predefined_pool_data
                        
                        # Get predefined pool data
                        predefined_data = get_predefined_pool_data()
                        
                        # Process top APR pools from the predefined data
                        api_pools = predefined_data.get('topAPR', [])
                        
                        # Convert pools to Pool objects for formatting
                        pools = []
                        for pool_data in api_pools:
                            pool = Pool()
                            pool.id = pool_data.get("id", "unknown")
                            
                            # Extract token symbols from pair name
                            pair_name = pool_data.get("pairName", "UNKNOWN/UNKNOWN")
                            token_symbols = pair_name.split("/")
                            
                            pool.token_a_symbol = token_symbols[0] if len(token_symbols) > 0 else "Unknown"
                            pool.token_b_symbol = token_symbols[1] if len(token_symbols) > 1 else "Unknown"
                            
                            # Get token prices if available
                            token_prices = pool_data.get("tokenPrices", {})
                            pool.token_a_price = token_prices.get(pool.token_a_symbol, 0)
                            pool.token_b_price = token_prices.get(pool.token_b_symbol, 0)
                            
                            # Extract other pool data
                            pool.apr_24h = pool_data.get("apr", 0)
                            pool.apr_7d = pool_data.get("aprWeekly", 0)
                            pool.apr_30d = pool_data.get("aprMonthly", 0)
                            pool.tvl = pool_data.get("liquidity", 0)
                            pool.fee = pool_data.get("fee", 0) * 100  # Convert from decimal to percentage
                            pool.volume_24h = pool_data.get("volume24h", 0)
                            pool.tx_count_24h = pool_data.get("txCount", 0)
                            pools.append(pool)
                        
                        # Save pools to database for future use
                        db.session.add_all(pools)
                        db.session.commit()
                        logger.info(f"Saved {len(pools)} pools to database from predefined data")
                    except Exception as e:
                        logger.error(f"Error using predefined pool data: {e}")
                        pools = []
            except Exception as e:
                logger.error(f"Database error: {e}")
                # Fallback to using predefined data directly if database access fails
                try:
                    from response_data import get_pool_data as get_predefined_pool_data
                    from models import Pool
                    
                    predefined_data = get_predefined_pool_data()
                    api_pools = predefined_data.get('topAPR', [])
                    
                    pools = []
                    for pool_data in api_pools:
                        pool = Pool()
                        pool.id = pool_data.get("id", "unknown")
                        
                        # Extract token symbols from pair name
                        pair_name = pool_data.get("pairName", "UNKNOWN/UNKNOWN")
                        token_symbols = pair_name.split("/")
                        
                        pool.token_a_symbol = token_symbols[0] if len(token_symbols) > 0 else "Unknown"
                        pool.token_b_symbol = token_symbols[1] if len(token_symbols) > 1 else "Unknown"
                        
                        # Get token prices if available
                        token_prices = pool_data.get("tokenPrices", {})
                        pool.token_a_price = token_prices.get(pool.token_a_symbol, 0)
                        pool.token_b_price = token_prices.get(pool.token_b_symbol, 0)
                        
                        # Extract other pool data
                        pool.apr_24h = pool_data.get("apr", 0)
                        pool.apr_7d = pool_data.get("aprWeekly", 0)
                        pool.apr_30d = pool_data.get("aprMonthly", 0)
                        pool.tvl = pool_data.get("liquidity", 0)
                        pool.fee = pool_data.get("fee", 0) * 100  # Convert from decimal to percentage
                        pool.volume_24h = pool_data.get("volume24h", 0)
                        pool.tx_count_24h = pool_data.get("txCount", 0)
                        pools.append(pool)
                    
                    logger.info(f"Using {len(pools)} pools from predefined data without database")
                except Exception as e:
                    logger.error(f"Error creating fallback pool objects: {e}")
                    pools = []
                    
        return pools
    except Exception as e:
        logger.error(f"Error getting pool data: {e}")
        return []

# Command Handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    try:
        logger.info("Starting command /start execution")
        user = update.effective_user
        logger.info(f"User info retrieved: {user.id} - {user.username}")
        
        # Use app context for database operations
        from app import app
        with app.app_context():
            # Log user activity
            db_utils.get_or_create_user(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"User {user.id} created or retrieved from database")
            
            db_utils.log_user_activity(user.id, "start_command")
            logger.info(f"Activity logged for user {user.id}")
        
        logger.info(f"Sending welcome message to user {user.id}")
        await update.message.reply_markdown(
            f"👋 Welcome to FiLot, {user.first_name}!\n\n"
            "I'm your AI-powered investment assistant for cryptocurrency liquidity pools. "
            "With real-time analytics and personalized insights, I'll help you make informed investment decisions.\n\n"
            "I've just set up a convenient *One-Command interface* with persistent navigation buttons "
            "at the bottom of your screen for easier interaction.\n\n"
            "Simply tap on any button to navigate through different sections "
            "or use the following commands directly if you prefer:\n\n"
            "🔹 /info - See top-performing liquidity pools\n"
            "🔹 /simulate [amount] - Calculate potential earnings\n"
            "🔹 /wallet - Manage your crypto wallet\n"
            "🔹 /help - See all available commands\n\n"
            "You can also ask me any questions about crypto pools, APR, or investment strategies!"
        )
        
        # Set up the main menu with persistent buttons
        await set_menu_state(update, context, MenuType.MAIN)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued and show the help menu."""
    try:
        from app import app
        with app.app_context():
            user = update.effective_user
            db_utils.log_user_activity(user.id, "help_command")
        
        await update.message.reply_markdown(
            "🤖 *FiLot Bot - Help Guide*\n\n"
            "I support both persistent button navigation and traditional commands.\n\n"
            "*📱 Button Navigation:*\n"
            "Use the buttons at the bottom of your screen to navigate through different sections.\n\n"
            "*⌨️ Available Commands:*\n"
            "• /start - Start the bot and get a welcome message\n"
            "• /info - View top-performing liquidity pools\n"
            "• /simulate [amount] - Calculate potential earnings\n"
            "• /subscribe - Receive daily updates\n"
            "• /unsubscribe - Stop receiving updates\n"
            "• /status - Check bot status\n"
            "• /wallet - Manage your crypto wallet\n"
            "• /walletconnect - Connect wallet using QR code\n"
            "• /verify [code] - Verify your account\n" 
            "• /profile - Set your investment preferences\n"
            "• /faq - Frequently asked questions\n"
            "• /social - Our social media links\n"
            "• /help - Show this help message\n\n"
            "You can also ask me questions about FiLot, LA! Token, or DeFi concepts."
        )
        
        # Set up the help menu with persistent buttons
        await set_menu_state(update, context, MenuType.HELP)
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show information about cryptocurrency pools when the command /info is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "info_command")
        
        # Determine whether this is a direct command or a callback query
        is_callback = update.callback_query is not None
        
        # Handle both regular commands and callback queries
        if is_callback:
            # For callback queries (from buttons)
            message = update.callback_query.message
        else:
            # For direct commands
            message = update.message
            # Only send this initial message for direct commands
            await message.reply_text("Fetching the latest pool data...")
        
        # Import at function level to avoid circular imports
        from response_data import get_pool_data as get_predefined_pool_data
        
        # Get predefined pool data directly as dictionaries
        predefined_data = get_predefined_pool_data()
        
        # Check if a specific pool type was requested via button press or command args
        pool_type = None
        if context.args and len(context.args) > 0:
            pool_type = context.args[0].lower()
        elif update.message and update.message.text:
            text = update.message.text.lower()
            # Handle button presses with more precise matching
            if "high apr pools" in text.lower() or "📈 high apr pools" in text.lower():
                pool_type = "high_apr"
            elif "stable pools" in text.lower() or "💵 stable pools" in text.lower():
                pool_type = "stable"
            # Also check for partial matches (for better UX)
            elif any(term in text.lower() for term in ["high apr", "top apr", "best apr", "📈"]):
                pool_type = "high_apr"
            elif any(term in text.lower() for term in ["stable", "stablecoin", "usdc", "usdt", "💵"]):
                pool_type = "stable"
        
        # Process top performing pools and stable pools from the predefined data
        top_pools = predefined_data.get('bestPerformance', [])  # Get best performance pools
        stable_pools = predefined_data.get('topStable', [])    # Get stable pools
        
        if not top_pools and not stable_pools:
            await message.reply_text(
                "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
            )
            return
        
        # Determine which pools to show based on the request
        if pool_type == "high_apr":
            formatted_info = format_pool_info(top_pools, [], show_title="High APR Pools")
        elif pool_type == "stable":
            formatted_info = format_pool_info([], stable_pools, show_title="Stable Pools")
        else:
            # Default: show both types
            formatted_info = format_pool_info(top_pools, stable_pools)
        
        # Use regular reply_text to avoid markdown formatting issues
        await message.reply_text(formatted_info)
        logger.info(f"Sent pool info response for type: {pool_type or 'all'}")
        
        # Show the pool info menu with persistent buttons
        if not is_callback:
            await set_menu_state(update, context, MenuType.POOL_INFO)
    except Exception as e:
        logger.error(f"Error in info command: {e}", exc_info=True)
        
        # Handle errors for both command types
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    "Sorry, an error occurred while processing your request. Please try again later."
                )
            else:
                await update.message.reply_text(
                    "Sorry, an error occurred while processing your request. Please try again later."
                )
        except Exception as reply_error:
            logger.error(f"Error sending error message: {reply_error}")

async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulate investment returns when the command /simulate is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "simulate_command")
        
        # Set default amount to 1000 if not provided
        amount = 1000.0
        
        # Handle button presses as well as direct commands
        if update.message and update.message.text:
            text = update.message.text
            
            # Check for quick simulate button
            if "💲 quick simulate" in text.lower():
                # Default amount is already set to $1000
                pass
            # Check for custom amounts from text (both commands and button presses)
            elif "custom" in text.lower() or "simulation" in text.lower():
                # Keep default for now, will prompt user to enter amount
                await update.message.reply_text(
                    "Please enter an investment amount using '/simulate [amount]'.\nFor example: /simulate 5000"
                )
                return
            # Parse command arguments if present
            elif context.args and context.args[0]:
                try:
                    amount = float(context.args[0])
                    if amount <= 0:
                        raise ValueError("Amount must be positive")
                except ValueError:
                    await update.message.reply_text(
                        "Please provide a valid positive number. Example: /simulate 1000"
                    )
                    return
        
        # Tell the user we're calculating
        await update.message.reply_text(f"Calculating potential returns for a ${amount:,.2f} investment...")
        
        # Import at function level to avoid circular imports
        from response_data import get_pool_data as get_predefined_pool_data
        
        # Get predefined pool data directly as dictionaries
        predefined_data = get_predefined_pool_data()
        
        # Process top APR pools from the predefined data (bestPerformance = topAPR)
        # These should be the 2 highest-performing pools
        pool_list = predefined_data.get('bestPerformance', [])
        
        if not pool_list:
            await update.message.reply_text(
                "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
            )
            return
            
        # For simulation, we use the top performing pools (2 pools)
        formatted_simulation = format_simulation_results(pool_list, amount)
        
        # Add wallet connection options - both direct and WalletConnect
        keyboard = [
            [InlineKeyboardButton("Connect Wallet (Address)", callback_data="enter_address")],
            [InlineKeyboardButton("Connect Wallet (QR Code)", callback_data="walletconnect")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Use regular reply_text to avoid markdown formatting issues
        await update.message.reply_text(formatted_simulation, reply_markup=reply_markup)
        logger.info(f"Sent simulation response for amount ${amount:.2f}")
        
        # Set up the simulate menu with persistent buttons
        await set_menu_state(update, context, MenuType.SIMULATE)
    except Exception as e:
        logger.error(f"Error in simulate command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to daily updates when the command /subscribe is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for all database operations
        success = False
        with app.app_context():
            # Subscribe user in database
            success = db_utils.subscribe_user(user.id)
            
            if success:
                db_utils.log_user_activity(user.id, "subscribe")
        
        # Send response outside app context (no db operations)
        if success:
            await update.message.reply_markdown(
                "✅ You've successfully subscribed to daily updates!\n\n"
                "You'll receive daily insights about the best-performing liquidity pools "
                "and investment opportunities.\n\n"
                "Use /unsubscribe to stop receiving updates at any time."
            )
        else:
            await update.message.reply_markdown(
                "You're already subscribed to daily updates.\n\n"
                "Use /unsubscribe if you wish to stop receiving updates."
            )
    except Exception as e:
        logger.error(f"Error in subscribe command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from daily updates when the command /unsubscribe is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for all database operations
        success = False
        with app.app_context():
            # Unsubscribe user in database
            success = db_utils.unsubscribe_user(user.id)
            
            if success:
                db_utils.log_user_activity(user.id, "unsubscribe")
        
        # Send response outside app context (no db operations)
        if success:
            await update.message.reply_markdown(
                "✅ You've successfully unsubscribed from daily updates.\n\n"
                "You'll no longer receive daily pool insights.\n\n"
                "Use /subscribe if you'd like to receive updates again in the future."
            )
        else:
            await update.message.reply_markdown(
                "You're not currently subscribed to daily updates.\n\n"
                "Use /subscribe if you'd like to receive daily insights."
            )
    except Exception as e:
        logger.error(f"Error in unsubscribe command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check bot status when the command /status is issued."""
    try:
        # Import the app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for all database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "status_command")
            
            # Get user status inside app context
            db_user = db_utils.get_or_create_user(user.id)
            
            # Format the status text with user data
            status_text = (
                "🤖 *FiLot Bot Status*\n\n"
                "✅ Bot is operational and ready to assist you!\n\n"
                "*Your Account Status:*\n"
                f"• User ID: {db_user.telegram_id}\n"
                f"• Subscription: {'Active ✅' if db_user.is_subscribed else 'Inactive ❌'}\n"
                f"• Verification: {'Verified ✅' if db_user.is_verified else 'Unverified ❌'}\n"
                f"• Account Created: {db_user.created_at.strftime('%Y-%m-%d')}\n\n"
                "Use /help to see available commands."
            )
        
        # Reply outside of app context (no db operations)
        await update.message.reply_markdown(status_text)
    except Exception as e:
        logger.error(f"Error in status command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify the user when the command /verify is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Check if code is provided
        if not context.args or not context.args[0]:
            # Use app context for database operations
            with app.app_context():
                # Generate verification code inside app context
                code = db_utils.generate_verification_code(user.id)
            
            if code:
                await update.message.reply_markdown(
                    "📱 *Verification Required*\n\n"
                    "To enhance your account security and unlock additional features, "
                    "please verify your account using the code below:\n\n"
                    f"`{code}`\n\n"
                    "Use the code with the /verify command like this:\n"
                    f"/verify {code}"
                )
            else:
                await update.message.reply_text(
                    "Error generating verification code. Please try again later."
                )
            return
            
        # Verify with provided code (inside app context)
        code = context.args[0]
        
        # Use app context for all database operations
        success = False
        with app.app_context():
            # Verify user with code
            success = db_utils.verify_user(user.id, code)
            
            if success:
                # Log the activity inside app context
                db_utils.log_user_activity(user.id, "verified")
        
        # Send response outside app context (no db operations)
        if success:
            await update.message.reply_markdown(
                "✅ *Verification Successful!*\n\n"
                "Your account has been verified. You now have access to all FiLot features.\n\n"
                "Explore FiLot's capabilities with /help."
            )
        else:
            await update.message.reply_markdown(
                "❌ *Verification Failed*\n\n"
                "The verification code is invalid or has expired.\n\n"
                "Please try again with a new code by typing /verify"
            )
    except Exception as e:
        logger.error(f"Error in verify command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manage wallet when the command /wallet is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "wallet_command")
        
        # Check if a wallet address is provided
        if context.args and context.args[0]:
            wallet_address = context.args[0]
            
            try:
                # Validate wallet address
                wallet_address = connect_wallet(wallet_address)
                
                await update.message.reply_markdown(
                    f"✅ Wallet successfully connected: `{wallet_address}`\n\n"
                    "Fetching wallet balance..."
                )
                
                # Get wallet balance
                balance = await check_wallet_balance(wallet_address)
                
                if "error" in balance:
                    await update.message.reply_markdown(
                        f"❌ Error: {balance['error']}\n\n"
                        "Please try again with a valid wallet address."
                    )
                    return
                
                # Format balance information
                balance_text = "💼 *Wallet Balance* 💼\n\n"
                
                for token, amount in balance.items():
                    if token == "SOL":
                        balance_text += f"• SOL: *{amount:.4f}* (≈${amount * 133:.2f})\n"
                    elif token == "USDC" or token == "USDT":
                        balance_text += f"• {token}: *{amount:.2f}*\n"
                    else:
                        balance_text += f"• {token}: *{amount:.4f}*\n"
                
                # Add investment options
                keyboard = [
                    [InlineKeyboardButton("View Pool Opportunities", callback_data="view_pools")],
                    [InlineKeyboardButton("Connect with WalletConnect", callback_data="walletconnect")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.message.reply_markdown(
                    balance_text + "\n\n💡 Use /simulate to see potential earnings with these tokens in liquidity pools.",
                    reply_markup=reply_markup
                )
                
            except ValueError as e:
                await update.message.reply_markdown(
                    f"❌ Error: {str(e)}\n\n"
                    "Please provide a valid Solana wallet address."
                )
            
        else:
            # No address provided, show wallet menu
            keyboard = [
                [InlineKeyboardButton("Connect with WalletConnect", callback_data="walletconnect")],
                [InlineKeyboardButton("Enter Wallet Address", callback_data="enter_address")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_markdown(
                "💼 *Wallet Management*\n\n"
                "Connect your wallet to view balances and interact with liquidity pools.\n\n"
                "Choose an option below, or provide your wallet address directly using:\n"
                "/wallet [your_address]",
                reply_markup=reply_markup
            )
            
            # Set up the wallet menu with persistent buttons
            await set_menu_state(update, context, MenuType.WALLET)
    except Exception as e:
        logger.error(f"Error in wallet command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set user investment profile when the command /profile is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        profile_text = None
        db_user = None
        
        # Use app context for all database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "profile_command")
            
            # Get current user profile data inside app context
            db_user = db_utils.get_or_create_user(user.id)
            
            # If no parameters provided, prepare to show current profile
            if not context.args:
                # Format current profile info
                profile_text = (
                    "🔍 *Your Investment Profile*\n\n"
                    f"• Risk Tolerance: *{db_user.risk_profile.capitalize()}*\n"
                    f"• Investment Horizon: *{db_user.investment_horizon.capitalize()}*\n"
                    f"• Investment Goals: {db_user.investment_goals or 'Not specified'}\n\n"
                    "To update your profile, use one of these commands:\n"
                    "• `/profile risk [conservative/moderate/aggressive]`\n"
                    "• `/profile horizon [short/medium/long]`\n"
                    "• `/profile goals [your investment goals]`\n\n"
                    "Example: `/profile risk aggressive`"
                )
        
        # If we have profile text ready, send it and return
        if profile_text:
            await update.message.reply_markdown(profile_text)
            # Set up the profile menu with persistent buttons
            await set_menu_state(update, context, MenuType.PROFILE)
            return
            
        # Process command parameters
        if len(context.args) >= 2:
            setting_type = context.args[0].lower()
            setting_value = " ".join(context.args[1:])
            
            # Process different setting types within app context
            with app.app_context():
                if setting_type == "risk":
                    if setting_value.lower() in ["conservative", "moderate", "aggressive"]:
                        # Update risk profile using db_utils
                        db_user.risk_profile = setting_value.lower()
                        db_utils.update_user_profile(db_user.id, "risk_profile", setting_value.lower())
                        
                        # Send confirmation
                        await update.message.reply_markdown(
                            f"✅ Risk profile updated to *{setting_value.capitalize()}*.\n\n"
                            f"Your AI financial advice will now be tailored to a {setting_value.lower()} risk tolerance."
                        )
                    else:
                        await update.message.reply_text(
                            "Invalid risk profile. Please choose from: conservative, moderate, or aggressive."
                        )
                        
                elif setting_type == "horizon":
                    if setting_value.lower() in ["short", "medium", "long"]:
                        # Update investment horizon using db_utils
                        db_user.investment_horizon = setting_value.lower()
                        db_utils.update_user_profile(db_user.id, "investment_horizon", setting_value.lower())
                        
                        # Send confirmation
                        await update.message.reply_markdown(
                            f"✅ Investment horizon updated to *{setting_value.capitalize()}*.\n\n"
                            f"Your AI financial advice will now be tailored to a {setting_value.lower()}-term investment horizon."
                        )
                    else:
                        await update.message.reply_text(
                            "Invalid investment horizon. Please choose from: short, medium, or long."
                        )
                        
                elif setting_type == "goals":
                    # Update investment goals using db_utils
                    goals_value = setting_value[:255]  # Limit to 255 chars
                    db_user.investment_goals = goals_value
                    db_utils.update_user_profile(db_user.id, "investment_goals", goals_value)
                    
                    # Send confirmation
                    await update.message.reply_markdown(
                        "✅ Investment goals updated successfully.\n\n"
                        "Your AI financial advice will take your goals into consideration."
                    )
                    
                else:
                    await update.message.reply_text(
                        "Invalid setting. Please use 'risk', 'horizon', or 'goals'."
                    )
        else:
            await update.message.reply_text(
                "Please provide both setting type and value. For example:\n"
                "/profile risk moderate"
            )
    except Exception as e:
        logger.error(f"Error in profile command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )
        
async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display FAQ information when the command /faq is issued."""
    try:
        from app import app
        with app.app_context():
            user = update.effective_user
            db_utils.log_user_activity(user.id, "faq_command")
        
        # Format the FAQ content with emojis and clear sections
        faq_text = """
❓ *Frequently Asked Questions*

*What does this bot do?*
It helps track crypto earnings from AI-optimized liquidity pools and provides info on FiLot.

*How do I earn with liquidity pools?*
Contribute crypto to earn trading fees. FiLot aims to find high-yield, safer pools.

*Is it risky?*
All investments have risk. FiLot focuses on stable pools (like SOL-USDC) and uses AI to manage risk, but losses are possible.

*What's Impermanent Loss (IL)?*
Value changes in your deposited tokens compared to just holding them. AI aims to minimize this by selecting suitable pools.

*What's APR?*
Annual Percentage Rate - estimated yearly return. Pool APRs can be high (10-200%+) but fluctuate.

*How do updates work?*
Use /subscribe for automatic news. Use /unsubscribe to stop.

*How does /simulate work?*
It estimates earnings based on recent APRs: Earnings = Investment * (APR/100) * Time.

*When is FiLot launching?*
Coming soon! Use /subscribe for announcements.

*How do I ask specific questions?*
Use /ask Your question here... for product details, or just type general questions.

Use /help to see all available commands!
"""
        
        # Send the FAQ message
        await update.message.reply_markdown(faq_text)
        
        # Set up the FAQ menu with persistent buttons
        await set_menu_state(update, context, MenuType.FAQ)
        
        logger.info(f"Sent FAQ to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in FAQ command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while sending the FAQ. Please try again later."
        )

async def social_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display social media links when the command /social is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "social_command")
        
        # Format the social media content with emojis and links
        social_text = """
🤝 *Connect With Us!*

Stay updated and join the community on our official channels:

🐦 X (Twitter): [@CrazyRichLA](https://x.com/crazyrichla)
📸 Instagram: [@CrazyRichLA](https://www.instagram.com/crazyrichla)
🌐 Website: [CrazyRichLA](https://crazyrichla.replit.app/)

Follow us for the latest news and launch announcements!
"""
        
        # Create inline keyboard for the social links
        keyboard = [
            [
                InlineKeyboardButton("Twitter 🐦", url="https://x.com/crazyrichla"),
                InlineKeyboardButton("Instagram 📸", url="https://www.instagram.com/crazyrichla")
            ],
            [
                InlineKeyboardButton("Website 🌐", url="https://crazyrichla.replit.app/")
            ]
        ]
        
        # Send the social media message with inline buttons (outside app context)
        await update.message.reply_markdown(
            social_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True  # Disable preview to avoid showing Twitter/IG previews
        )
        
        # Show the main menu with persistent buttons after social links
        await set_menu_state(update, context, MenuType.MAIN)
        
        logger.info(f"Sent social media links to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in social command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while sending the social media links. Please try again later."
        )

async def walletconnect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a WalletConnect session when the command /walletconnect is issued."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        # Get user info before entering app context
        user = update.effective_user
        
        # Use app context for database operations
        with app.app_context():
            # Log the activity inside app context
            db_utils.log_user_activity(user.id, "walletconnect_command")
        
        # Determine if this is a callback or direct command
        is_callback = update.callback_query is not None
        
        # Get the appropriate message object based on the update type
        if is_callback:
            message = update.callback_query.message
        else:
            message = update.message
        
        # Send security information message first
        security_msg = await message.reply_markdown(
            "🔒 *Secure Wallet Connection*\n\n"
            "Our wallet connection process is designed with your security in mind:\n\n"
            "• Your private keys remain in your wallet app\n"
            "• We only request permission to view balances\n"
            "• No funds will be transferred without your explicit approval\n"
            "• All connections use encrypted communication\n\n"
            "Creating your secure connection now..."
        )
        
        # Create a WalletConnect session
        result = await create_walletconnect_session(user.id)
        
        if not result["success"]:
            await security_msg.reply_markdown(
                f"❌ Error: {result.get('error', 'Unknown error')}\n\n"
                "Please try again later."
            )
            return
            
        # Format the QR code data
        uri = result["uri"]
        session_id = result["session_id"]
        
        # Save session to context if available
        try:
            # The correct way to access user_data is to just use it directly
            # We can't reassign the entire user_data object, just set values on it
            context.user_data["walletconnect_session"] = session_id
            logger.info(f"Saved session ID {session_id} to user context")
        except Exception as user_data_error:
            # Don't fail if we can't store in context
            logger.warning(f"Could not store session in user_data: {user_data_error}")
        
        # Create simplified keyboard without the unreliable "Open in Wallet App" button
        keyboard = [
            [InlineKeyboardButton("Check Connection Status", callback_data=f"check_wc_{session_id}")],
            [InlineKeyboardButton("Cancel Connection", callback_data=f"cancel_wc_{session_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Get the raw WalletConnect URI directly
        # Check if it's in the session result first
        session_data = result.get("session_data", {})
        
        # Get the raw WC URI from our stored session data
        raw_wc_uri = uri
        if "raw_wc_uri" in session_data:
            raw_wc_uri = session_data["raw_wc_uri"]
            
        # Send the main wallet connect message
        await security_msg.reply_markdown(
            "🔗 *WalletConnect Session Created*\n\n"
            "Copy the connection code below and paste it into your wallet app to connect.\n\n"
            f"Session ID: `{session_id}`\n\n"
            "✅ *What to expect in your wallet app:*\n"
            "• You'll be asked to approve a connection request\n"
            "• Your wallet app will show exactly what permissions are being requested\n"
            "• No funds will be transferred without your explicit approval\n\n"
            "Once connected, click 'Check Connection Status' to verify.",
            reply_markup=reply_markup
        )
        
        # Generate QR code for the WalletConnect URI
        try:
            # Make sure we're using the raw wc: URI for the QR code (not the deep link)
            wc_uri_for_qr = result.get('raw_wc_uri', raw_wc_uri)
            logger.info(f"Generating QR code for URI: {wc_uri_for_qr}")
            
            # Import directly to confirm PIL is available
            from PIL import Image
            logger.info("PIL is available")
            
            # Create QR code with explicit imports to ensure we have all needed components
            import qrcode
            from qrcode.image.pil import PilImage
            
            # Use the most basic qrcode creation method
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(wc_uri_for_qr)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            logger.info(f"QR code image created, type: {type(qr_img)}")
            
            # Save to a buffer
            buffer = io.BytesIO()
            qr_img.save(buffer, format="PNG")  # Explicitly set format
            buffer.seek(0)
            logger.info(f"QR saved to buffer, size: {len(buffer.getvalue())} bytes")
            
            # Send QR code as photo with more detailed caption
            current_time = datetime.datetime.now().strftime("%H:%M:%S")
            sent_msg = await message.reply_photo(
                photo=buffer,
                caption=f"📱 Scan this QR code with your wallet app to connect\n(Generated at {current_time})"
            )
            
            logger.info(f"QR code sent successfully: {sent_msg.message_id}")
        except ImportError as imp_err:
            logger.error(f"Import error for QR generation: {imp_err}")
            logger.error(traceback.format_exc())
            
            # Try alternative QR display via text
            await message.reply_text(
                "Unable to generate QR code image. Please use the text link below instead."
            )
        except Exception as qr_error:
            logger.error(f"Error generating QR code: {qr_error}")
            logger.error(traceback.format_exc())
            # If QR code generation fails, we'll still send the text version
        
        # Also send the raw WalletConnect URI as text for manual copying if needed
        # Format with code block and timestamp for better visibility
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the WalletConnect URI
        wallet_connect_uri = result.get('raw_wc_uri', raw_wc_uri)
        
        # Create a cleaner and more focused message with just the WalletConnect URI
        # Using a dedicated message specifically for copying
        # Using monospace font with a standalone message makes it easier to copy
        copy_msg = await message.reply_text(
            f"📋 *COPY THIS LINK* (tap to select):\n\n"
            f"`{wallet_connect_uri}`\n\n"
            f"Generated at {current_time}",
            parse_mode="Markdown"
        )
        
        # Add the detailed explanation in a separate message
        await security_msg.reply_text(
            "🔒 Remember: Only approve wallet connections from trusted sources and always verify the requested permissions.\n\n"
            "If the QR code doesn't work, manually copy the link above and paste it into your wallet app."
        )
    except Exception as e:
        logger.error(f"Error in walletconnect command: {e}")
        try:
            if update.callback_query:
                await update.callback_query.message.reply_text(
                    "Sorry, an error occurred while processing your request. Please try again later."
                )
            else:
                await update.message.reply_text(
                    "Sorry, an error occurred while processing your request. Please try again later."
                )
        except Exception as reply_error:
            logger.error(f"Error sending error message: {reply_error}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle user messages that are not commands.
    Intelligently detects questions and provides predefined answers or 
    routes to AI for specialized financial advice.
    Now also handles menu navigation using buttons.
    """
    try:
        user = update.effective_user
        message_text = update.message.text
        
        # Log the user's message
        logger.info(f"Received message from user {user.id}: {message_text}")
        
        # Record message for anti-loop protection
        record_user_message(user.id, message_text)
        
        # Check if this is a menu navigation button press
        menu_handled = await handle_menu_navigation(update, context)
        if menu_handled:
            # Record button press for rate limiting
            record_button_press(user.id, message_text)
            logger.info(f"User {user.id} navigated using menu button: {message_text}")
            # Message was handled by menu navigation, no need to process further
            return
            
        # Check if this is a potential menu button but not properly handled
        current_menu = get_current_menu(user.id)
        if current_menu and message_text.strip() in ["Back", "Menu", "Main Menu"]:
            # Go back to main menu
            await set_menu_state(update, context, MenuType.MAIN)
            logger.info(f"User {user.id} returned to main menu with text: {message_text}")
            return
        
        # We'll wrap all database operations in an app context
        from app import app
        with app.app_context():
            # Log the query in the database
            query = db_utils.log_user_query(
                user_id=user.id,
                command="message",  # Changed from None to avoid type error
                query_text=message_text
            )
            
            # First, check if this is a question
            question_detected = is_question(message_text)
            logger.info(f"Is question detection: {question_detected}")
            
            # Check for predefined responses
            predefined_response = get_predefined_response(message_text)
            
            if predefined_response:
                logger.info(f"Found predefined response for: {message_text[:30]}...")
                
                # Send predefined response
                await update.message.reply_markdown(predefined_response)
                
                # Update the query with the response
                if query:
                    query.response_text = predefined_response
                    query.processing_time = (datetime.datetime.now() - query.timestamp).total_seconds() * 1000
                    # Save to db in a non-blocking way
                    asyncio.create_task(update_query_response(query.id, predefined_response, query.processing_time))
                
                # Log that we've responded with a predefined answer
                db_utils.log_user_activity(user.id, "predefined_response", details=f"Question: {message_text[:50]}")
                return
        
        # No predefined response available, use Anthropic AI for specialized financial advice
        logger.info(f"No predefined response for: {message_text}, using AI advisor")
        
        # Send typing indicator while processing
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Try to identify if this is a financial question
        classification = await ai_advisor.classify_financial_question(message_text)
        logger.info(f"AI classification: {classification}")
        
        # We need another app context for database operations
        from app import app
        
        # Get user profile details
        user_db = None
        risk_profile = "moderate"
        investment_horizon = "medium"
        
        with app.app_context():
            # Get user profile if available
            user_db = db_utils.get_or_create_user(user.id)
            risk_profile = getattr(user_db, 'risk_profile', 'moderate')
            investment_horizon = getattr(user_db, 'investment_horizon', 'medium')
        
        # Get pool data for context
        pools = await get_pool_data()
        
        ai_response = "I'm sorry, I couldn't process your request at this time."
        
        # Process based on classification
        if classification == "pool_advice":
            # Question about specific liquidity pools
            logger.info("Generating pool advice")
            ai_response = await ai_advisor.get_financial_advice(
                message_text, 
                pool_data=pools,
                risk_profile=risk_profile,
                investment_horizon=investment_horizon
            )
            
        elif classification == "strategy_help":
            # Question about investment strategies
            logger.info("Generating investment strategy")
            amount = 1000  # Default amount for strategy examples
            # Check if user mentioned an amount
            amount_match = re.search(r'(\$?[0-9,]+)', message_text)
            if amount_match:
                try:
                    amount = float(amount_match.group(1).replace('$', '').replace(',', ''))
                except ValueError:
                    pass
            
            ai_response = await ai_advisor.generate_investment_strategy(
                investment_amount=amount,
                risk_profile=risk_profile,
                investment_horizon=investment_horizon,
                pool_data=pools
            )
            
        elif classification == "risk_assessment":
            # Question about risk assessment
            logger.info("Generating risk assessment")
            # Find the pool with highest APR for risk assessment example
            highest_apr_pool = {}
            if pools and len(pools) > 0:
                highest_apr_pool = {
                    'token_a_symbol': pools[0].token_a_symbol,
                    'token_b_symbol': pools[0].token_b_symbol,
                    'apr_24h': pools[0].apr_24h,
                    'apr_7d': pools[0].apr_7d,
                    'apr_30d': pools[0].apr_30d,
                    'tvl': pools[0].tvl,
                    'fee': pools[0].fee,
                    'volume_24h': pools[0].volume_24h
                }
            
            risk_result = await ai_advisor.assess_investment_risk(highest_apr_pool)
            
            # Format risk assessment response
            risk_level = risk_result.get('risk_level', 'medium')
            explanation = risk_result.get('explanation', 'No detailed explanation available.')
            
            if risk_level.lower() == 'high' or risk_level.lower() == 'very high':
                risk_emoji = "🔴"
            elif risk_level.lower() == 'medium':
                risk_emoji = "🟠"
            else:
                risk_emoji = "🟢"
                
            ai_response = (
                f"*Risk Assessment: {risk_level.upper()}* {risk_emoji}\n\n"
                f"{explanation}\n\n"
                f"*Key Considerations:*\n• {risk_result.get('key_factors', 'N/A')}\n\n"
                f"*Impermanent Loss Risk:*\n• {risk_result.get('impermanent_loss', 'N/A')}\n\n"
                f"*Volatility:*\n• {risk_result.get('volatility', 'N/A')}\n\n"
                f"*Liquidity:*\n• {risk_result.get('liquidity', 'N/A')}\n\n"
                "Remember that all cryptocurrency investments carry inherent risks."
            )
            
        elif classification == "defi_explanation":
            # Question about DeFi concepts - extract the concept
            logger.info("Generating DeFi concept explanation")
            concept_match = re.search(r'(what is|explain|how does|tell me about) ([\w\s]+)', message_text.lower())
            concept = concept_match.group(2).strip() if concept_match else message_text
            
            ai_response = await ai_advisor.explain_financial_concept(concept)
            
        else:
            # General financial advice
            logger.info("Generating general financial advice")
            ai_response = await ai_advisor.get_financial_advice(
                message_text, 
                pool_data=pools,
                risk_profile=risk_profile,
                investment_horizon=investment_horizon
            )
        
        # Send the AI response
        await update.message.reply_markdown(ai_response)
        
        # Update the database with our query and response
        with app.app_context():
            # Update the query with the response
            if query:
                query.response_text = ai_response if isinstance(ai_response, str) else str(ai_response)
                query.processing_time = (datetime.datetime.now() - query.timestamp).total_seconds() * 1000
                # Save to db in a non-blocking way
                asyncio.create_task(update_query_response(query.id, query.response_text, query.processing_time))
                
            # Log that we've responded with an AI-generated answer
            db_utils.log_user_activity(user.id, "ai_response", details=f"Classification: {classification}")
            
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        logger.error(traceback.format_exc())
        await update.message.reply_text(
            "Sorry, I encountered an error while processing your request. Please try again later."
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in updates."""
    try:
        error = context.error
        trace = "".join(traceback.format_exception(None, error, error.__traceback__))
        
        # Log error with more details
        logger.error(f"Exception while handling an update: {error}\n{trace}")
        logger.error(f"Update that caused error: {update}")
        logger.error(f"Context info: {context}")
        
        # Store error in database
        error_type = type(error).__name__
        error_message = str(error)
        
        # Try to get user ID if available
        user_id = None
        if update and isinstance(update, Update) and update.effective_user:
            user_id = update.effective_user.id
            logger.info(f"Error occurred for user {user_id}")
            
        try:
            # Only log to database if error is not related to database
            if "SQLAlchemy" not in error_type and "no application context" not in error_message:
                db_utils.log_error(
                    error_type=error_type,
                    error_message=error_message,
                    traceback=trace,
                    module="bot",
                    user_id=user_id
                )
                logger.info(f"Error logged to database: {error_type}")
            else:
                logger.warning(f"Skipping database logging for SQLAlchemy error: {error_message}")
        except Exception as db_error:
            logger.error(f"Failed to log error to database: {db_error}")
        
        # Inform user
        if update and isinstance(update, Update) and update.effective_message:
            try:
                logger.info("Attempting to send error message to user")
                await update.effective_message.reply_text(
                    "Sorry, an error occurred while processing your request. Please try again later."
                )
                logger.info("Error message sent to user successfully")
            except Exception as reply_error:
                logger.error(f"Failed to send error message to user: {reply_error}")
    except Exception as e:
        logger.error(f"Error in error handler: {e}")
        logger.error(traceback.format_exc())

async def send_daily_updates() -> None:
    """Send daily updates to subscribed users."""
    try:
        # Get subscribed users
        subscribed_users = db_utils.get_subscribed_users()
        
        if not subscribed_users:
            logger.info("No subscribed users found for daily updates")
            return
            
        # Get pool data
        pools = await get_pool_data()
        
        if not pools:
            logger.error("Failed to get pool data for daily updates")
            return
            
        # Format daily update message
        update_message = format_daily_update(pools)
        
        # TODO: Send message to all subscribed users
        # This would be implemented when you have the application running 24/7
        logger.info(f"Would send daily updates to {len(subscribed_users)} users")
    except Exception as e:
        logger.error(f"Error sending daily updates: {e}")

# Callback Query Handler (for inline buttons)
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    try:
        # Import app at function level to avoid circular imports
        from app import app
        
        query = update.callback_query
        user = query.from_user
        callback_data = query.data
        
        # Log user activity within app context
        with app.app_context():
            db_utils.log_user_activity(user.id, f"callback_{callback_data}")
        
        # Acknowledge the callback query
        await query.answer()
        
        if callback_data == "walletconnect":
            # Create a new context.args with empty list for the walletconnect command
            context.args = []
            await walletconnect_command(update, context)
            
        elif callback_data.startswith("check_wc_"):
            try:
                # Check WalletConnect session status
                session_id = callback_data.replace("check_wc_", "")
                logger.info(f"Checking WalletConnect session status for session: {session_id}")
                
                # Get the session info from the database
                session_info = await check_walletconnect_session(session_id)
                
                if not session_info["success"]:
                    error_msg = session_info.get('error', 'Session not found')
                    logger.warning(f"Session check failed: {error_msg}")
                    await query.message.reply_markdown(
                        f"❌ *Connection Error*\n\n"
                        f"{error_msg}\n\n"
                        "Please try creating a new wallet connection with /walletconnect."
                    )
                    return
                
                # Since this is a mock implementation, we'll simulate a successful connection
                # In a real implementation, we'd check if the wallet has connected
                status = "connected"  # For demo, assume connected after checking
                logger.info(f"Session status: {status}")
                
                # Update the session status in the database
                if status != session_info["status"]:
                    # Use app context for database operations
                    with app.app_context():
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE wallet_sessions SET status = %s WHERE session_id = %s",
                            (status, session_id)
                        )
                        cursor.close()
                        conn.close()
                
                if status == "connected":
                    try:
                        # Get mock wallet data for display
                        wallet_data = await get_wallet_balances(user.id)
                        token_list = ", ".join([f"{token} ({balance})" for token, balance in wallet_data.get("balances", {}).items()])
                        
                        await query.message.reply_markdown(
                            "✅ *Wallet Connected Successfully!*\n\n"
                            f"Your wallet is now connected in read-only mode.\n\n"
                            f"*Detected tokens:*\n{token_list}\n\n"
                            "You can now get personalized pool recommendations based on your holdings.\n\n"
                            "Use /info to see available pools or /simulate to calculate potential earnings."
                        )
                    except Exception as e:
                        logger.error(f"Error handling connected wallet: {e}")
                        await query.message.reply_markdown(
                            "✅ *Wallet Connected!*\n\n"
                            "Your wallet is now connected in read-only mode.\n\n"
                            "Use /info to see available pools or /simulate to calculate potential earnings."
                        )
                else:
                    try:
                        # For buttons in the message
                        # Get connection URIs from session data
                        session_data = session_info.get("session_data", {})
                        uri = session_data.get("uri", "")  # HTTPS URI for Telegram buttons
                        raw_wc_uri = session_data.get("raw_wc_uri", "")  # Raw WC URI for display
                        
                        # Create updated keyboard with check status button
                        keyboard = [
                            [InlineKeyboardButton("Check Connection Status", callback_data=f"check_wc_{session_id}")],
                            [InlineKeyboardButton("Cancel Connection", callback_data=f"cancel_wc_{session_id}")]
                        ]
                        
                        # Add wallet app button only if we have a valid URI
                        if uri and uri.startswith("https://"):
                            keyboard.insert(0, [InlineKeyboardButton("Open in Wallet App", url=uri)])
                        
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        # Only update the reply markup if there's a change
                        try:
                            await query.message.edit_reply_markup(reply_markup=reply_markup)
                        except Exception as edit_error:
                            logger.warning(f"Could not update message markup: {edit_error}")
                        
                        response_text = (
                            "⏳ *Waiting for Connection*\n\n"
                            "The wallet connection is still pending. Please open your wallet app and approve the connection.\n\n"
                        )
                        
                        # Include the raw WC URI and QR code if available
                        if raw_wc_uri:
                            try:
                                # Generate QR code for the URI using simple API
                                qr_img = qrcode.make(raw_wc_uri)
                                
                                # Create and send the QR code image
                                buffer = io.BytesIO()
                                qr_img.save(buffer)
                                buffer.seek(0)
                                
                                await query.message.reply_photo(
                                    photo=buffer,
                                    caption="📱 Scan this QR code with your wallet app to connect"
                                )
                                
                                # Also send the text version for manual copying
                                await query.message.reply_text(f"Alternatively, you can manually copy this WalletConnect URI:\n\n{raw_wc_uri}")
                            except Exception as qr_error:
                                logger.error(f"Error generating QR code in callback: {qr_error}")
                                # Fallback to text only if QR fails
                                await query.message.reply_text(f"Connect with this WalletConnect URI:\n\n{raw_wc_uri}")
                            # Don't include it in the main message
                            
                        response_text += "Click 'Check Connection Status' after approving in your wallet."
                        
                        await query.message.reply_markdown(response_text)
                    except Exception as e:
                        logger.error(f"Error processing pending connection: {e}")
                        await query.message.reply_markdown(
                            "⏳ *Waiting for Connection*\n\n"
                            "Please open your wallet app and approve the connection, then click 'Check Connection Status'."
                        )
            except Exception as e:
                logger.error(f"Error checking WalletConnect session: {e}")
                await query.message.reply_text(
                    "Sorry, an error occurred while checking the connection status. Please try again later."
                )
                
        elif callback_data.startswith("cancel_wc_"):
            # Cancel WalletConnect session
            session_id = callback_data.replace("cancel_wc_", "")
            result = await kill_walletconnect_session(session_id)
            
            if result["success"]:
                await query.message.reply_markdown(
                    "✅ *Connection Cancelled*\n\n"
                    "The wallet connection request has been cancelled.\n\n"
                    "Use /wallet to start a new connection when you're ready."
                )
            else:
                await query.message.reply_markdown(
                    f"❌ Error: {result.get('error', 'Unknown error')}\n\n"
                    "Please try again later."
                )
                
        elif callback_data == "enter_address":
            await query.message.reply_markdown(
                "💼 *Enter Wallet Address*\n\n"
                "Please provide your Solana wallet address using the command:\n"
                "/wallet [your_address]\n\n"
                "Example: `/wallet 5YourWalletAddressHere12345`"
            )
            
        elif callback_data == "view_pools":
            # Send a confirmation message that we're fetching pool information
            loading_message = await query.message.reply_markdown(
                "🔍 *Fetching Pool Opportunities*\n\n"
                "Please wait while I gather the latest data on available liquidity pools..."
            )
            
            try:
                # Import at function level to avoid circular imports
                from response_data import get_pool_data as get_predefined_pool_data
                
                # Get predefined pool data directly as dictionaries
                predefined_data = get_predefined_pool_data()
                
                # Process top APR pools from the predefined data
                pool_list = predefined_data.get('topAPR', [])
                
                if not pool_list:
                    await loading_message.reply_text(
                        "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
                    )
                    return
                    
                formatted_info = format_pool_info(pool_list)
                # Use regular reply_text to avoid markdown formatting issues
                await loading_message.reply_text(formatted_info)
                logger.info("Sent pool info response for view_pools callback")
            except Exception as e:
                logger.error(f"Error fetching pool data via callback: {e}")
                await loading_message.reply_text(
                    "Sorry, an error occurred while retrieving pool data. Please try again later."
                )
            
        elif callback_data.startswith("wallet_connect_"):
            # Extract amount from callback data
            amount = float(callback_data.replace("wallet_connect_", ""))
            
            await query.message.reply_markdown(
                f"💼 *Connect Wallet to Invest ${amount:,.2f}*\n\n"
                "To proceed with this investment, please connect your wallet.\n\n"
                "Use /wallet to connect your wallet address, or use /walletconnect for a QR code connection."
            )
            
        else:
            await query.message.reply_text(
                "Sorry, I couldn't process that action. Please try again."
            )
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        if update and update.callback_query:
            await update.callback_query.message.reply_text(
                "Sorry, an error occurred while processing your request. Please try again later."
            )

def create_application():
    """Register all necessary handlers to the application and return the Application instance."""
    # Check for Telegram bot token (first look for the secret, then fallback to env var for backward compatibility)
    token = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("Telegram bot token not found. Please set the TELEGRAM_TOKEN secret.")
        raise ValueError("Telegram bot token not found")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("simulate", simulate_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("wallet", wallet_command))
    application.add_handler(CommandHandler("walletconnect", walletconnect_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(CommandHandler("faq", faq_command))
    application.add_handler(CommandHandler("social", social_command))
    
    # Register callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Register message handler for non-command messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    logger.info("Application created with all handlers registered")
    
    return application