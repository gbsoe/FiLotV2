"""
Core bot functionality for the Telegram cryptocurrency pool bot
"""

import os
import logging
import re
import datetime
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
import traceback

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from dotenv import load_dotenv

# Import local modules
import db_utils
from models import User, Pool, UserQuery, db
from response_data import get_predefined_response
from raydium_client import get_pools, get_token_prices
from utils import format_pool_info, format_simulation_results, format_daily_update
from wallet_utils import connect_wallet, check_wallet_balance, calculate_deposit_strategy
from walletconnect_utils import (
    create_walletconnect_session, 
    check_walletconnect_session, 
    kill_walletconnect_session,
    get_user_walletconnect_sessions
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
        # Try to get pools from database first
        pools = Pool.query.order_by(Pool.apr_24h.desc()).limit(5).all()
        
        # If no pools in database, fetch from API
        if not pools or len(pools) == 0:
            api_pools = await get_pools(limit=5)
            # Convert API pools to Pool objects for formatting
            pools = []
            for pool_data in api_pools:
                pool = Pool()
                pool.id = pool_data.get("id", "unknown")
                pool.token_a_symbol = pool_data.get("token_a", {}).get("symbol", "Unknown")
                pool.token_b_symbol = pool_data.get("token_b", {}).get("symbol", "Unknown")
                pool.token_a_price = pool_data.get("token_a", {}).get("price", 0)
                pool.token_b_price = pool_data.get("token_b", {}).get("price", 0)
                pool.apr_24h = pool_data.get("apr_24h", 0)
                pool.apr_7d = pool_data.get("apr_7d", 0)
                pool.apr_30d = pool_data.get("apr_30d", 0)
                pool.tvl = pool_data.get("tvl", 0)
                pool.fee = pool_data.get("fee", 0)
                pool.volume_24h = pool_data.get("volume_24h", 0)
                pool.tx_count_24h = pool_data.get("tx_count_24h", 0)
                pools.append(pool)
        
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
            "🔹 Use /info to see top-performing liquidity pools\n"
            "🔹 Use /simulate [amount] to calculate potential earnings\n"
            "🔹 Use /subscribe to receive daily updates\n"
            "🔹 Use /wallet to manage your crypto wallet\n"
            "🔹 Use /help to see all available commands\n\n"
            "You can also ask me any questions about FiLot, LA! Token, or crypto investing in general."
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    try:
        user = update.effective_user
        db_utils.log_user_activity(user.id, "help_command")
        
        await update.message.reply_markdown(
            "🤖 *FiLot Bot Commands*\n\n"
            "• /start - Start the bot and get a welcome message\n"
            "• /info - View top-performing liquidity pools\n"
            "• /simulate [amount] - Calculate potential earnings\n"
            "• /subscribe - Receive daily updates\n"
            "• /unsubscribe - Stop receiving updates\n"
            "• /status - Check bot status\n"
            "• /wallet - Manage your crypto wallet\n"
            "• /verify [code] - Verify your account\n"
            "• /help - Show this help message\n\n"
            "You can also ask me questions about FiLot, LA! Token, or DeFi concepts."
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show information about cryptocurrency pools when the command /info is issued."""
    try:
        user = update.effective_user
        db_utils.log_user_activity(user.id, "info_command")
        
        await update.message.reply_text("Fetching the latest pool data...")
        
        pools = await get_pool_data()
        if not pools:
            await update.message.reply_text(
                "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
            )
            return
            
        formatted_info = format_pool_info(pools)
        await update.message.reply_markdown(formatted_info)
    except Exception as e:
        logger.error(f"Error in info command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def simulate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Simulate investment returns when the command /simulate is issued."""
    try:
        user = update.effective_user
        db_utils.log_user_activity(user.id, "simulate_command")
        
        # Check if amount is provided
        if not context.args or not context.args[0]:
            await update.message.reply_text(
                "Please provide an investment amount. Example: /simulate 1000"
            )
            return
            
        # Parse amount
        try:
            amount = float(context.args[0])
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await update.message.reply_text(
                "Please provide a valid positive number. Example: /simulate 1000"
            )
            return
            
        await update.message.reply_text("Calculating potential returns...")
        
        pools = await get_pool_data()
        if not pools:
            await update.message.reply_text(
                "Sorry, I couldn't retrieve pool data at the moment. Please try again later."
            )
            return
            
        formatted_simulation = format_simulation_results(pools, amount)
        
        # Add wallet connection option
        keyboard = [
            [InlineKeyboardButton("Connect Wallet", callback_data=f"wallet_connect_{amount}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_markdown(formatted_simulation, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in simulate command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def subscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Subscribe to daily updates when the command /subscribe is issued."""
    try:
        user = update.effective_user
        
        # Subscribe user in database
        success = db_utils.subscribe_user(user.id)
        
        if success:
            db_utils.log_user_activity(user.id, "subscribe")
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
        logger.error(f"Error in subscribe command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def unsubscribe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Unsubscribe from daily updates when the command /unsubscribe is issued."""
    try:
        user = update.effective_user
        
        # Unsubscribe user in database
        success = db_utils.unsubscribe_user(user.id)
        
        if success:
            db_utils.log_user_activity(user.id, "unsubscribe")
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
        logger.error(f"Error in unsubscribe command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check bot status when the command /status is issued."""
    try:
        user = update.effective_user
        db_utils.log_user_activity(user.id, "status_command")
        
        # Get user status
        db_user = db_utils.get_or_create_user(user.id)
        
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
        
        await update.message.reply_markdown(status_text)
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Verify the user when the command /verify is issued."""
    try:
        user = update.effective_user
        
        # Check if code is provided
        if not context.args or not context.args[0]:
            # Generate verification code
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
            
        # Verify with provided code
        code = context.args[0]
        success = db_utils.verify_user(user.id, code)
        
        if success:
            db_utils.log_user_activity(user.id, "verified")
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
        logger.error(f"Error in verify command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def wallet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manage wallet when the command /wallet is issued."""
    try:
        user = update.effective_user
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
    except Exception as e:
        logger.error(f"Error in wallet command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set user investment profile when the command /profile is issued."""
    try:
        user = update.effective_user
        db_utils.log_user_activity(user.id, "profile_command")
        
        # Get current user profile data
        db_user = db_utils.get_or_create_user(user.id)
        
        # If no parameters provided, show current profile
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
            await update.message.reply_markdown(profile_text)
            return
            
        # Process command parameters
        if len(context.args) >= 2:
            setting_type = context.args[0].lower()
            setting_value = " ".join(context.args[1:])
            
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
        logger.error(f"Error in profile command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def walletconnect_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a WalletConnect session when the command /walletconnect is issued."""
    try:
        user = update.effective_user
        db_utils.log_user_activity(user.id, "walletconnect_command")
        
        # Create a WalletConnect session
        result = await create_walletconnect_session(user.id)
        
        if not result["success"]:
            await update.message.reply_markdown(
                f"❌ Error: {result.get('error', 'Unknown error')}\n\n"
                "Please try again later."
            )
            return
            
        # Format the QR code data
        uri = result["uri"]
        session_id = result["session_id"]
        
        # Save session to context
        if not context.user_data:
            context.user_data = {}
        context.user_data["walletconnect_session"] = session_id
        
        # Create keyboard with deep link
        keyboard = [
            [InlineKeyboardButton("Open in Wallet App", url=uri)],
            [InlineKeyboardButton("Check Connection Status", callback_data=f"check_wc_{session_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_markdown(
            "🔗 *WalletConnect Session Created*\n\n"
            "Scan the QR code with your wallet app to connect, or click the button below to open in your wallet app.\n\n"
            f"Session ID: `{session_id}`\n\n"
            "Once connected, click 'Check Connection Status' to verify.",
            reply_markup=reply_markup
        )
        
        # Send the QR code URL separately
        await update.message.reply_text(
            f"Connect your wallet with this link: {uri}"
        )
    except Exception as e:
        logger.error(f"Error in walletconnect command: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your request. Please try again later."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages that are not commands."""
    try:
        user = update.effective_user
        message_text = update.message.text
        
        # Log the query
        query = db_utils.log_user_query(
            user_id=user.id,
            command=None,
            query_text=message_text
        )
        
        # First check for predefined responses
        response = get_predefined_response(message_text)
        
        if response:
            # Send predefined response
            await update.message.reply_markdown(response)
        else:
            # No predefined response available, use Anthropic AI for specialized financial advice
            
            # Send typing indicator while processing
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Try to identify if this is a financial question
            classification = await ai_advisor.classify_financial_question(message_text)
            
            # Get user profile if available
            user_db = db_utils.get_or_create_user(user.id)
            risk_profile = getattr(user_db, 'risk_profile', 'moderate')
            investment_horizon = getattr(user_db, 'investment_horizon', 'medium')
            
            # Get pool data for context
            pools = await get_pool_data()
            
            if classification == "pool_advice":
                # Question about specific liquidity pools
                ai_response = await ai_advisor.get_financial_advice(
                    message_text, 
                    pool_data=pools,
                    risk_profile=risk_profile,
                    investment_horizon=investment_horizon
                )
                await update.message.reply_markdown(ai_response)
                
            elif classification == "strategy_help":
                # Question about investment strategies
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
                await update.message.reply_markdown(ai_response)
                
            elif classification == "risk_assessment":
                # Question about risk assessment
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
                
                ai_response = await ai_advisor.assess_investment_risk(highest_apr_pool)
                
                # Format risk assessment response
                risk_level = ai_response.get('risk_level', 'medium')
                explanation = ai_response.get('explanation', 'No detailed explanation available.')
                
                if risk_level.lower() == 'high' or risk_level.lower() == 'very high':
                    risk_emoji = "🔴"
                elif risk_level.lower() == 'medium':
                    risk_emoji = "🟠"
                else:
                    risk_emoji = "🟢"
                    
                formatted_response = (
                    f"*Risk Assessment: {risk_level.upper()}* {risk_emoji}\n\n"
                    f"{explanation}\n\n"
                    f"*Key Considerations:*\n• {ai_response.get('key_factors', 'N/A')}\n\n"
                    f"*Impermanent Loss Risk:*\n• {ai_response.get('impermanent_loss', 'N/A')}\n\n"
                    f"*Volatility:*\n• {ai_response.get('volatility', 'N/A')}\n\n"
                    f"*Liquidity:*\n• {ai_response.get('liquidity', 'N/A')}\n\n"
                    "Remember that all cryptocurrency investments carry inherent risks."
                )
                
                await update.message.reply_markdown(formatted_response)
                
            elif classification == "defi_explanation":
                # Question about DeFi concepts - extract the concept
                concept_match = re.search(r'(what is|explain|how does|tell me about) ([\w\s]+)', message_text.lower())
                concept = concept_match.group(2).strip() if concept_match else message_text
                
                ai_response = await ai_advisor.explain_financial_concept(concept)
                await update.message.reply_markdown(ai_response)
                
            else:
                # General financial advice
                ai_response = await ai_advisor.get_financial_advice(
                    message_text, 
                    pool_data=pools,
                    risk_profile=risk_profile,
                    investment_horizon=investment_horizon
                )
                await update.message.reply_markdown(ai_response)
                
            # Update the query with the response
            if query:
                query.response_text = ai_response
                query.processing_time = (datetime.datetime.now() - query.timestamp).total_seconds() * 1000
                # Save to db in a non-blocking way
                asyncio.create_task(update_query_response(query.id, ai_response, query.processing_time))
                
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text(
            "Sorry, an error occurred while processing your message. Please try again later."
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
        query = update.callback_query
        user = query.from_user
        callback_data = query.data
        
        # Log user activity
        db_utils.log_user_activity(user.id, f"callback_{callback_data}")
        
        # Acknowledge the callback query
        await query.answer()
        
        if callback_data == "walletconnect":
            # Create a new context.args with empty list for the walletconnect command
            context.args = []
            await walletconnect_command(update, context)
            
        elif callback_data.startswith("check_wc_"):
            # Check WalletConnect session status
            session_id = callback_data.replace("check_wc_", "")
            session_info = await check_walletconnect_session(session_id)
            
            if not session_info["success"]:
                await query.message.reply_markdown(
                    f"❌ Error: {session_info.get('error', 'Session not found')}\n\n"
                    "Please try again with a new session."
                )
                return
                
            status = session_info["status"]
            
            if status == "connected":
                await query.message.reply_markdown(
                    "✅ *Wallet Connected Successfully!*\n\n"
                    "You can now interact with liquidity pools and perform other wallet operations.\n\n"
                    "Use /info to see available pools or /simulate to calculate potential earnings."
                )
            else:
                # Create updated keyboard with check status button
                keyboard = [
                    [InlineKeyboardButton("Open in Wallet App", url=session_info["session_data"]["uri"])],
                    [InlineKeyboardButton("Check Connection Status", callback_data=f"check_wc_{session_id}")],
                    [InlineKeyboardButton("Cancel Connection", callback_data=f"cancel_wc_{session_id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.edit_reply_markup(reply_markup=reply_markup)
                
                await query.message.reply_markdown(
                    "⏳ *Waiting for Connection*\n\n"
                    "The wallet connection is still pending. Please open your wallet app and approve the connection.\n\n"
                    "Click 'Check Connection Status' after approving in your wallet."
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
            await info_command(update, context)
            
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
    """Register all necessary handlers to the application."""
    pass  # This is handled in run_bot.py