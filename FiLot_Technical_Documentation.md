# FiLot Technical Documentation

## 1. Project Overview

### Purpose of FiLot

FiLot is an advanced, AI-powered DeFi investment assistant implemented as a Telegram bot. It enables users to explore, analyze, simulate, and execute liquidity pool investments on the Solana blockchain with varying levels of automation. The bot serves as an agentic system that combines multiple data sources with AI models to provide intelligent investment recommendations tailored to users' risk profiles.

The primary goals of FiLot are:
- Simplify complex DeFi investment decisions through natural language interaction
- Provide data-driven insights and predictions for liquidity pool performance
- Enable secure on-chain transactions through non-custodial wallet integration
- Offer personalized investment strategies through reinforcement learning
- Ensure production-grade transaction safety with comprehensive pre-checks and error handling

### Key Technologies

FiLot leverages multiple technologies to deliver its functionality:

- **Core Frameworks**:
  - Python 3.10+ as the primary development language
  - python-telegram-bot 20.x for Telegram API integration
  - Flask for web interface and background services
  - SQLAlchemy with PostgreSQL for database operations

- **Blockchain Interaction**:
  - solana-py for Solana blockchain transaction construction
  - WalletConnect v2 protocol for secure wallet connections
  - Raydium DEX integration for liquidity pool investments

- **AI and Data Processing**:
  - Anthropic Claude API for specialized financial advice
  - DeepSeek AI for conversational interactions
  - Reinforcement Learning (RL) for adaptive investment recommendations
  - SolPool Insight API for pool data and predictions
  - FilotSense API for market sentiment analysis

### Summary of Functionality

FiLot provides the following core functionality:

1. **Pool Data Exploration**: Browse and search for Solana liquidity pools with detailed metrics
2. **Investment Simulation**: Simulate investment returns with various parameters
3. **Smart Invest**: AI-powered investment recommendations based on user risk profiles
4. **Wallet Integration**: Connect Solana wallets securely via WalletConnect
5. **Transaction Execution**: Build, submit, and verify real Solana transactions
6. **Investment Tracking**: Monitor active investments and historical performance
7. **Market Insights**: Receive AI-generated market analysis and sentiment indicators
8. **Personalization**: Set and manage risk profiles, investment preferences, and notifications

## 2. Directory and File Structure

The FiLot project is organized into logical groups of files, each with specific responsibilities:

### Core Application Files

- **`main.py`**: Application entry point that registers handlers and starts the bot
- **`bot.py`**: Core Telegram bot setup and command handlers
- **`app.py`**: Flask web application for admin interface and background services
- **`models.py`**: SQLAlchemy database models for all persistent data
- **`wsgi.py`**: WSGI entry point for production deployment

### Bot Interaction Handlers

- **`button_responses.py`**: Handlers for interactive button callbacks
- **`interactive_buttons.py`**: Button layouts and callback data generation
- **`interactive_commands.py`**: Command handlers for interactive menu options
- **`interactive_menu.py`**: Main menu structure and navigation
- **`callback_handler.py`**: Pattern-based callback router

### Investment Logic

- **`smart_invest.py`**: Smart investment conversation flow and logic
- **`smart_invest_execution.py`**: Transaction execution workflow
- **`invest_flow.py`**: Traditional investment flow handlers
- **`agentic_advisor.py`**: Intelligent investment advisor logic
- **`rl_investment_advisor.py`**: Reinforcement Learning model for recommendations

### Wallet Integration

- **`wallet_actions.py`**: Transaction building, signing, and submission
- **`walletconnect_manager.py`**: WalletConnect session management
- **`walletconnect_utils.py`**: Utility functions for WalletConnect
- **`solana_wallet_service.py`**: Solana wallet interaction service

### API Clients

- **`raydium_client.py`**: Client for Raydium DEX API
- **`solpool_api_client.py`**: Client for SolPool Insight API
- **`filotsense_api_client.py`**: Client for FilotSense sentiment API
- **`coingecko_utils.py`**: CoinGecko API utilities for token pricing

### AI Services

- **`ai_service.py`**: DeepSeek AI integration for conversational AI
- **`anthropic_service.py`**: Anthropic Claude AI integration for financial expertise

### Database Utilities

- **`db_utils.py`**: Core database utility functions
- **`db_utils_mood.py`**: User emotion tracking utilities
- **`create_tables.py`**: Database schema initialization script
- **`fix_database.py`**: Database maintenance and repair utilities

### Utility and Helper Modules

- **`utils.py`**: General utility functions
- **`token_search.py`**: Token search and lookup utilities
- **`keyboard_utils.py`**: Keyboard layout generation helpers
- **`question_detector.py`**: Natural language question detection
- **`monitoring.py`**: System monitoring and logging
- **`safeguards.py`**: Transaction and input safety checks

## 3. Core Components

### `main.py`: Bot Initialization and Handler Registration

The `main.py` file serves as the application entry point and is responsible for:
1. Setting up the application environment
2. Configuring logging
3. Initializing the bot with proper token and settings
4. Registering command handlers and callback dispatchers
5. Starting the bot polling mechanism

Key sections of `main.py`:

```python
# Initialize bot and dispatcher
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

# Register command handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("info", info_command))
application.add_handler(CommandHandler("wallet", wallet_command))
application.add_handler(CommandHandler("walletconnect", walletconnect_command))
application.add_handler(CommandHandler("smart_invest", smart_invest_command))
application.add_handler(CommandHandler("interactive", interactive_command))
# ...more command handlers

# Register conversation handlers
application.add_handler(get_investment_conversation_handler())
application.add_handler(get_wallet_conversation_handler())
application.add_handler(get_profile_conversation_handler())

# Register callback handlers
application.add_handler(CallbackQueryHandler(handle_button_press))

# Register error handler
application.add_error_handler(error_handler)

# Start the bot
application.run_polling()
```

The application structure follows the recommended python-telegram-bot pattern using the Application class with appropriate handlers registered for:
- Commands (e.g., `/start`, `/help`)
- Conversations (multi-step dialog flows)
- Callbacks (button interactions)
- Errors (exception handling)

### `button_responses.py`: Callback Query Handling

This file contains handlers for interactive buttons in the bot interface. It processes callback data to determine appropriate responses when users tap buttons. The main function is `handle_button_press`, which routes callbacks based on patterns:

```python
async def handle_button_press(update: Update, context: CallbackContext) -> None:
    """Handle button presses (callback queries)."""
    query = update.callback_query
    await query.answer()  # Stop loading animation
    
    data = query.data
    user = update.effective_user
    
    # Log button press
    logger.info(f"Button press from {user.id}: {data}")
    
    # Check for rate limiting
    if is_button_rate_limited(user.id, data):
        await query.edit_message_text(
            "Please slow down! You're pressing buttons too quickly.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⬅️ Main Menu", callback_data="main_menu")
            ]])
        )
        return
    
    # Record the button press
    record_button_press(user.id, data)
    
    # Route to specific handlers based on callback patterns
    if data == "main_menu":
        await show_main_menu(update, context)
    elif data.startswith("pool:"):
        await handle_pool_detail(update, context)
    elif data == "pools":
        await show_pool_list(update, context)
    elif data.startswith("invest_now:"):
        await handle_invest_now(update, context)
    elif data.startswith("walletconnect"):
        await handle_wallet_connect(update, context)
    # ...more callback routing
```

The button handling system uses pattern matching to route callbacks to appropriate handlers. This allows for dynamic callbacks with parameters (e.g., `pool:SOL-USDC`) while maintaining clean code organization.

### `smart_invest.py`: RL Engine and Investment Flow

The Smart Invest feature uses Reinforcement Learning to provide optimized investment recommendations. This file manages the conversation flow and integration with the RL model:

```python
def get_rl_recommendations(user_id: int, risk_profile: str = "moderate", amount: float = 100.0) -> List[Dict[str, Any]]:
    """
    Get investment recommendations using the RL model
    
    Args:
        user_id: Telegram user ID
        risk_profile: User's risk profile (conservative, moderate, aggressive)
        amount: Investment amount in USD
        
    Returns:
        List of recommended pools with scores and explanations
    """
    # Initialize the RL advisor
    from rl_investment_advisor import RLInvestmentAdvisor
    advisor = RLInvestmentAdvisor()
    
    # Get user's investment history and preferences
    from models import User, InvestmentLog, db
    user = User.query.filter_by(id=user_id).first()
    
    # Get pool data from SolPool API
    from solpool_api_client import get_all_pools
    pools = get_all_pools()
    
    # Get sentiment data from FilotSense API
    from filotsense_api_client import get_market_sentiment
    sentiment = get_market_sentiment()
    
    # Generate features for the RL model
    features = generate_pool_features(pools, sentiment)
    
    # Get recommendations from the RL model
    recommendations = advisor.get_recommendations(
        features=features,
        risk_profile=risk_profile,
        investment_amount=amount,
        user_history=get_user_investment_history(user_id)
    )
    
    return recommendations
```

The RL model combines multiple data sources:
- Technical pool data (APR, TVL, volume)
- Prediction scores from SolPool Insight API
- Sentiment data from FilotSense API
- User's investment history

These inputs are processed to create a feature vector for each pool, which is then fed to the RL model to generate recommendations with confidence scores.

### `wallet_actions.py`: Transaction Building and Execution

This file handles all Solana transaction operations, including:
1. Transaction building with slippage protection
2. Transaction signing via WalletConnect
3. Transaction submission to the Solana network
4. Transaction status verification

The core of the transaction building logic:

```python
async def build_raydium_lp_transaction(
    wallet_address: str,
    pool_id: str,
    token_a_mint: str,
    token_b_mint: str,
    token_a_amount: float,
    token_b_amount: float,
    slippage_tolerance: float = 0.5,  # Default slippage of 0.5% (50 basis points)
    min_lp_tokens: Optional[float] = None  # Optional minimum LP tokens to receive
) -> Dict[str, Any]:
    """
    Build a Solana transaction for Raydium LP investment
    
    Args:
        wallet_address: User's Solana wallet address
        pool_id: Raydium pool ID
        token_a_mint: Token A mint address
        token_b_mint: Token B mint address
        token_a_amount: Amount of Token A to invest
        token_b_amount: Amount of Token B to invest
        slippage_tolerance: Maximum allowed slippage in percentage (default 0.5%)
        min_lp_tokens: Optional minimum LP tokens to receive (calculated if None)
        
    Returns:
        Dictionary with serialized_transaction and other metadata
    """
    # Implementation details for creating a Raydium LP transaction
    # ...
```

The transaction execution flow:

```python
async def execute_investment(wallet_address: str, pool_id: str, amount: float, slippage_tolerance: float = 0.5) -> Dict[str, Any]:
    """
    Execute an investment in a Raydium liquidity pool
    
    Args:
        wallet_address: User's Solana wallet address
        pool_id: Raydium pool ID
        amount: Investment amount in USD
        slippage_tolerance: Maximum allowed slippage in percentage
        
    Returns:
        Dict with transaction information
    """
    try:
        # PRECHECKS: Verify all conditions before starting transaction process
        # 1. Check wallet connection status
        # 2. Check if pool exists and is active
        # 3. Check investment amount limits
        # 4. Check if user has sufficient balance
        
        # Calculate token amounts
        token_amounts = await calculate_token_amounts(pool_id, amount)
        
        # Check price impact
        price_impact = token_amounts.get('price_impact', 0.0)
        if price_impact > 5.0:  # 5% is generally considered the safe maximum
            return {
                "success": False, 
                "error": "High price impact",
                "message": f"This transaction would have a high price impact of {price_impact:.2f}%. Try a smaller amount."
            }
            
        # Build transaction
        transaction_data = await build_raydium_lp_transaction(
            wallet_address=wallet_address,
            pool_id=pool_id,
            # ...other parameters
            slippage_tolerance=slippage_tolerance
        )
        
        # Send for signing
        signing_result = await send_transaction_for_signing(
            wallet_address=wallet_address,
            serialized_transaction=transaction_data.get('serialized_transaction')
        )
        
        # Submit signed transaction
        submission_result = await submit_signed_transaction(
            signature=signing_result.get('signature')
        )
        
        # Log the investment
        await create_investment_log(
            user_id=get_user_id_from_wallet(wallet_address),
            pool_id=pool_id,
            amount=amount,
            tx_hash=signature,
            status="confirming",
            # ...additional fields
        )
        
        # Return success with transaction details
        return {
            "success": True,
            "transaction_hash": tx_hash,
            # ...additional fields
        }
        
    except Exception as e:
        logger.error(f"Error executing investment: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute investment. Please try again later."
        }
```

### `models.py`: Database Schema

This file defines the SQLAlchemy models for persistent data storage:

```python
class User(db.Model):
    """User model representing a Telegram user."""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True)  # Telegram user ID
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_blocked = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Financial profile settings
    risk_profile = Column(String(20), default="moderate")  # conservative, moderate, aggressive
    investment_horizon = Column(String(20), default="medium")  # short, medium, long
    preferred_pools = Column(JSON, nullable=True)  # User's favorite pool types
    
    # Wallet connection settings
    wallet_address = Column(String(255), nullable=True)  # Solana wallet public address
    wallet_connected_at = Column(DateTime, nullable=True)  # When wallet was connected
    connection_status = Column(String(20), default="disconnected")  # disconnected, connecting, connected, failed
    wallet_session_id = Column(String(100), nullable=True)  # For WalletConnect session tracking
    last_tx_id = Column(String(100), nullable=True)  # Last transaction signature
    
    # Relationships
    queries = relationship("UserQuery", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("InvestmentLog", back_populates="user", cascade="all, delete-orphan")

class InvestmentLog(db.Model):
    """InvestmentLog model for tracking user investments in liquidity pools."""
    __tablename__ = "investment_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    pool_id = Column(String(255), ForeignKey("pools.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount in USD
    tx_hash = Column(String(100), nullable=False)  # Transaction signature/hash
    status = Column(String(20), nullable=False)  # confirming, confirmed, failed, etc.
    
    # Token details
    token_a_amount = Column(Float, nullable=True)
    token_b_amount = Column(Float, nullable=True)
    token_a_symbol = Column(String(20), nullable=True)
    token_b_symbol = Column(String(20), nullable=True)
    
    # Investment parameters
    apr_at_entry = Column(Float, nullable=True)
    slippage_tolerance = Column(Float, nullable=True)
    price_impact = Column(Float, nullable=True)
    
    # LP token information
    expected_lp_tokens = Column(Float, nullable=True)
    min_lp_tokens = Column(Float, nullable=True)
    actual_lp_tokens = Column(Float, nullable=True)
    
    # Additional metadata
    notes = Column(Text, nullable=True)  # For error descriptions or info
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="investments")
    pool = relationship("Pool", backref="investments")

class Pool(db.Model):
    """Pool model representing a cryptocurrency pool."""
    __tablename__ = "pools"
    
    id = Column(String(255), primary_key=True)  # Pool ID
    token_a_symbol = Column(String(10), nullable=False)
    token_b_symbol = Column(String(10), nullable=False)
    token_a_price = Column(Float, nullable=False)
    token_b_price = Column(Float, nullable=False)
    apr_24h = Column(Float, nullable=False)
    apr_7d = Column(Float, nullable=True)
    apr_30d = Column(Float, nullable=True)
    tvl = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    tx_count_24h = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
```

### `walletconnect_manager.py`: WalletConnect Flow

This file manages the WalletConnect protocol integration for wallet connections:

```python
class WalletConnectManager:
    """Manager for WalletConnect session handling."""
    
    def __init__(self, project_id: str):
        """Initialize the WalletConnect manager."""
        self.project_id = project_id
        self.sessions = {}  # User ID -> WalletConnect session info
        # ...other initialization
    
    async def create_session(self, user_id: int) -> Dict[str, Any]:
        """Create a new WalletConnect session for a user."""
        # Generate a new session with WalletConnect v2
        # ...session creation logic
        
        # Generate QR code for scanning
        qr_code_base64 = self.generate_qr_code(uri)
        
        # Store session information
        self.sessions[user_id] = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "status": "pending",
            "wallet_address": None,
            "uri": uri
        }
        
        return {
            "session_id": session_id,
            "qr_code_base64": qr_code_base64,
            "uri": uri,
            "expires_at": expires_at
        }
    
    async def check_session(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Check the status of a WalletConnect session."""
        # ...session status check logic
    
    async def send_transaction(self, user_id: int, serialized_transaction: str) -> Dict[str, Any]:
        """Send a transaction to the user's wallet for signing."""
        # ...transaction sending logic
        
        return {
            "success": True,
            "signature": signature,
            "expires_at": expires_at
        }
    
    def generate_qr_code(self, uri: str) -> str:
        """Generate a QR code image for the WalletConnect URI."""
        # ...QR code generation logic
```

## 4. Command & Callback Flow

### Bot Commands

| Command | Handler | Description |
|---------|---------|-------------|
| `/start` | `start` | Introduction to the bot and initial setup |
| `/help` | `help_command` | List available commands and usage instructions |
| `/info` | `info_command` | Show current market information and stats |
| `/simulate` | `simulate_command` | Simulate investment returns |
| `/smart_invest` | `smart_invest_command` | Start the AI-powered investment process |
| `/invest` | `invest_command` | Start the traditional investment flow |
| `/wallet` | `wallet_command` | Manage wallet connections |
| `/walletconnect` | `walletconnect_command` | Connect wallet via WalletConnect |
| `/profile` | `profile_command` | Set risk profile and preferences |
| `/subscribe` | `subscribe_command` | Subscribe to regular updates |
| `/unsubscribe` | `unsubscribe_command` | Unsubscribe from updates |
| `/interactive` | `interactive_command` | Display interactive menu with buttons |

### Callback Patterns

| Callback Pattern | Handler | Description |
|------------------|---------|-------------|
| `main_menu` | `show_main_menu` | Display the main menu |
| `pools` | `show_pool_list` | Show list of available pools |
| `pool:<id>` | `handle_pool_detail` | Show details for a specific pool |
| `invest_now:<pool_id>` | `handle_invest_now` | Start investment flow for a pool |
| `confirm_invest:<pool_id>:<amount>` | `handle_investment_confirmation` | Confirm investment details |
| `execute_invest:<pool_id>:<amount>` | `handle_execute_investment` | Execute investment after final confirmation |
| `check_tx:<tx_hash>` | `handle_check_transaction` | Check transaction status |
| `walletconnect` | `handle_wallet_connect` | Initiate WalletConnect session |
| `check_wallet:<session_id>` | `handle_check_wallet` | Check wallet connection status |
| `disconnect_wallet` | `handle_disconnect_wallet` | Disconnect wallet |
| `set_risk:<profile>` | `handle_set_risk` | Set user risk profile |
| `preset_amount:<amount>` | `handle_preset_amount` | Use preset investment amount |

### Conversation Handlers

The bot uses ConversationHandler to manage multi-step dialogs:

1. **Investment Conversation**:
   - Entry: `CallbackQueryHandler(start_investment, pattern=INVEST_POOL_PATTERN)`
   - States:
     - `AMOUNT_INPUT`: User enters investment amount
     - `CONFIRM_INVESTMENT`: User confirms investment details
     - `AWAITING_FINAL_CONFIRMATION`: User reviews final transaction details
     - `PROCESSING_TRANSACTION`: Transaction is being processed

2. **Wallet Conversation**:
   - Entry: `CommandHandler("walletconnect", walletconnect_command)`
   - States:
     - `CONNECTING`: Wallet connection in progress
     - `CONNECTION_CHECKING`: Checking wallet connection status

3. **Profile Conversation**:
   - Entry: `CommandHandler("profile", profile_command)`
   - States:
     - `SELECTING_RISK`: User selecting risk profile
     - `ENTERING_HORIZON`: User entering investment horizon

## 5. Investment Execution Flow

The investment execution process follows these steps:

### 1. Pool Selection

The user can select a pool in two ways:
- Browse pools and select one manually
- Use the Smart Invest feature to get AI recommendations

**Smart Invest Flow**:
```
User -> /smart_invest command
Bot -> Analyzes pools using RL model
Bot -> Presents top recommendations with scores
User -> Selects pool from recommendations
```

**Manual Selection Flow**:
```
User -> "🏊‍♂️ Pools" button
Bot -> Shows list of top pools
User -> Selects a specific pool
Bot -> Shows detailed pool information
User -> Taps "💰 Invest Now" button
```

### 2. Investment Amount

After selecting a pool:
```
Bot -> Prompts for investment amount
User -> Enters amount or selects preset
Bot -> Shows investment summary
User -> Taps "✅ Confirm" button
```

### 3. Detailed Transaction Review

Before proceeding:
```
Bot -> Shows detailed transaction information:
       - Token amounts
       - Price impact
       - Slippage tolerance
       - Expected LP tokens
User -> Reviews details and taps "✅ Confirm Transaction"
```

### 4. Wallet Connection (if needed)

If wallet not already connected:
```
Bot -> Initiates WalletConnect session
Bot -> Generates and displays QR code
User -> Scans QR code with wallet app
User -> Approves connection in wallet
Bot -> Verifies connection established
```

### 5. Transaction Building and Signing

Once wallet is connected:
```
Bot -> Builds Raydium LP transaction with slippage protection
Bot -> Sends transaction to user's wallet via WalletConnect
User -> Reviews transaction in wallet app
User -> Signs transaction in wallet
Bot -> Receives signed transaction
```

### 6. Transaction Submission

After signing:
```
Bot -> Submits signed transaction to Solana network
Bot -> Logs transaction details in database
Bot -> Shows transaction confirmation screen with hash
```

### 7. Transaction Verification

After submission:
```
Bot -> Monitors transaction status
User -> Can check status with "📊 Check Status" button
Bot -> Updates status (confirming, confirmed, failed)
Bot -> Shows final confirmation when transaction completes
```

### 8. Database Logging

Throughout the process:
```
Bot -> Creates InvestmentLog record with:
       - User ID
       - Pool ID
       - Amount
       - Transaction hash
       - Token amounts
       - APR at entry
       - Slippage settings
       - Status updates
```

## 6. API Integration

### SolPool Insight API

The SolPool Insight API provides real-time data about Solana liquidity pools, including:
- Pool metrics (APR, TVL, volume)
- Token prices and ratios
- Prediction scores
- Historical performance

Key endpoints used:

| Endpoint | Purpose | Sample Response |
|----------|---------|-----------------|
| `/pools` | Get all available pools | `[{"id": "SOL-USDC", "token_a_symbol": "SOL", ...}]` |
| `/pools/{id}` | Get details for a specific pool | `{"id": "SOL-USDC", "apr_24h": 24.5, ...}` |
| `/pools/{id}/pricing` | Get current pricing data | `{"tokenAPrice": 150.25, "tokenBPrice": 1.0, ...}` |
| `/pools/{id}/prediction` | Get prediction score | `{"score": 85, "confidence": "high", ...}` |
| `/simulate` | Simulate investment returns | `{"expected_return": 15.2, "risk_score": 45, ...}` |

Client implementation:

```python
class SolPoolClient:
    """Client for interacting with SolPool Insight API."""
    
    def __init__(self, api_key: str = None):
        """Initialize the SolPool client."""
        self.api_key = api_key or os.environ.get("SOLPOOL_API_KEY")
        self.base_url = "https://api.solpool.io/v1"
        self.session = None
    
    async def get_all_pools(self) -> List[Dict[str, Any]]:
        """Get all available pools."""
        return await self._request("GET", "/pools")
    
    async def get_pool(self, pool_id: str) -> Dict[str, Any]:
        """Get details for a specific pool."""
        return await self._request("GET", f"/pools/{pool_id}")
    
    async def get_pool_pricing(self, pool_id: str) -> Dict[str, Any]:
        """Get current pricing data for a pool."""
        return await self._request("GET", f"/pools/{pool_id}/pricing")
    
    async def get_pool_prediction(self, pool_id: str) -> Dict[str, Any]:
        """Get prediction score for a pool."""
        return await self._request("GET", f"/pools/{pool_id}/prediction")
    
    async def simulate_investment(self, pool_id: str, amount: float, 
                                days: int = 30) -> Dict[str, Any]:
        """Simulate investment returns for a pool."""
        payload = {
            "pool_id": pool_id,
            "amount_usd": amount,
            "days": days
        }
        return await self._request("POST", "/simulate", json=payload)
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make a request to the SolPool API."""
        # Request logic with error handling
```

### FilotSense API

The FilotSense API provides sentiment analysis and market insight data:

Key endpoints used:

| Endpoint | Purpose | Sample Response |
|----------|---------|-----------------|
| `/sentiment/market` | Overall market sentiment | `{"score": 65, "trend": "bullish", ...}` |
| `/sentiment/token/{symbol}` | Token-specific sentiment | `{"score": 78, "mentions": 1250, ...}` |
| `/trending/tokens` | Currently trending tokens | `[{"symbol": "SOL", "buzz_score": 92, ...}]` |
| `/search/{query}` | Search for tokens | `[{"symbol": "SOL", "name": "Solana", ...}]` |

Client implementation:

```python
class FilotSenseClient:
    """Client for interacting with FilotSense API."""
    
    def __init__(self, api_key: str = None):
        """Initialize the FilotSense client."""
        self.api_key = api_key or os.environ.get("FILOTSENSE_API_KEY")
        self.base_url = "https://api.filotsense.io/v1"
        self.session = None
    
    async def get_market_sentiment(self) -> Dict[str, Any]:
        """Get overall market sentiment."""
        return await self._request("GET", "/sentiment/market")
    
    async def get_token_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment for a specific token."""
        return await self._request("GET", f"/sentiment/token/{symbol}")
    
    async def get_trending_tokens(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get currently trending tokens."""
        return await self._request("GET", f"/trending/tokens?limit={limit}")
    
    async def search_tokens(self, query: str) -> List[Dict[str, Any]]:
        """Search for tokens by name or symbol."""
        return await self._request("GET", f"/search/{query}")
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        """Make a request to the FilotSense API."""
        # Request logic with error handling
```

### Integration in Investment Advisor

The APIs are combined in the agentic investment advisor:

```python
def get_investment_recommendation(investment_amount: float, risk_profile: str, token_preference: str = None):
    """Generate an investment recommendation."""
    # 1. Get pool data from SolPool API
    pools = solpool_client.get_all_pools()
    
    # 2. Get sentiment data from FilotSense API
    market_sentiment = filotsense_client.get_market_sentiment()
    
    # 3. If token preference exists, get token-specific sentiment
    if token_preference:
        token_sentiment = filotsense_client.get_token_sentiment(token_preference)
    
    # 4. Calculate scores for each pool
    scored_pools = []
    for pool in pools:
        # Get pool prediction
        prediction = solpool_client.get_pool_prediction(pool["id"])
        
        # Get token sentiments for pool tokens
        token_a_sentiment = filotsense_client.get_token_sentiment(pool["token_a_symbol"])
        token_b_sentiment = filotsense_client.get_token_sentiment(pool["token_b_symbol"])
        
        # Calculate weighted score
        score = (
            pool["apr_24h"] * 0.3 +               # 30% weight on APR
            math.log10(pool["tvl"]) * 0.2 +       # 20% weight on TVL (log-scaled)
            prediction["score"] * 0.25 +           # 25% weight on prediction
            ((token_a_sentiment["score"] + token_b_sentiment["score"]) / 2) * 0.25  # 25% on sentiment
        )
        
        # Adjust score based on risk profile
        if risk_profile == "conservative":
            # Favor higher TVL, lower volatility pools
            score = score * (math.log10(pool["tvl"]) / 8) * (1 - pool["volatility"] / 100)
        elif risk_profile == "aggressive":
            # Favor higher APR pools
            score = score * (pool["apr_24h"] / 50)
        
        scored_pools.append({
            "pool": pool,
            "score": score,
            "prediction": prediction,
            "sentiment": {
                "token_a": token_a_sentiment,
                "token_b": token_b_sentiment
            }
        })
    
    # 5. Sort pools by score
    scored_pools.sort(key=lambda x: x["score"], reverse=True)
    
    # 6. Return top recommendations
    return scored_pools[:3]
```

## 7. Data Models

### Core Models Overview

The database schema consists of several primary models:

1. **User**: Represents a Telegram user with profile and wallet information
2. **Pool**: Represents a liquidity pool with metrics and token data
3. **InvestmentLog**: Records of user investments with transaction details
4. **UserQuery**: Tracks user queries and bot responses
5. **UserActivityLog**: General user activity tracking
6. **MoodEntry**: User emotional states related to investments
7. **ErrorLog**: System error tracking

### Database Interaction Patterns

Various handlers read from and write to the database:

| Handler | Database Operations |
|---------|---------------------|
| `start` | Creates new User record if first interaction |
| `profile_command` | Reads/writes User.risk_profile |
| `wallet_command` | Reads User.wallet_address and connection_status |
| `handle_wallet_connect` | Updates User wallet connection details |
| `handle_investment_confirmation` | Creates new InvestmentLog record |
| `handle_check_transaction` | Updates InvestmentLog.status |
| `smart_invest_command` | Reads User.risk_profile for recommendations |

### Investment Logging

The InvestmentLog model stores comprehensive details about each investment:

```python
class InvestmentLog(db.Model):
    """InvestmentLog model for tracking user investments in liquidity pools."""
    __tablename__ = "investment_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    pool_id = Column(String(255), ForeignKey("pools.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount in USD
    tx_hash = Column(String(100), nullable=False)  # Transaction signature/hash
    status = Column(String(20), nullable=False)  # confirming, confirmed, failed, etc.
    
    # Token amounts and symbols
    token_a_amount = Column(Float, nullable=True)
    token_b_amount = Column(Float, nullable=True)
    token_a_symbol = Column(String(20), nullable=True)
    token_b_symbol = Column(String(20), nullable=True)
    
    # Investment parameters
    apr_at_entry = Column(Float, nullable=True)
    slippage_tolerance = Column(Float, nullable=True)
    price_impact = Column(Float, nullable=True)
    
    # LP token information
    expected_lp_tokens = Column(Float, nullable=True)
    min_lp_tokens = Column(Float, nullable=True)
    actual_lp_tokens = Column(Float, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)  # For error descriptions or additional info
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
```

The investment logging function:

```python
async def create_investment_log(user_id: int, pool_id: str, amount: float, tx_hash: str, status: str,
                            token_a_amount: float = None, token_b_amount: float = None, 
                            token_a_symbol: str = None, token_b_symbol: str = None,
                            apr_at_entry: float = None, slippage_tolerance: float = None,
                            price_impact: float = None, expected_lp_tokens: float = None,
                            min_lp_tokens: float = None, actual_lp_tokens: float = None,
                            notes: str = None) -> bool:
    """Create a log entry for an investment in the database."""
    try:
        # Create new investment log entry
        investment_log = InvestmentLog(
            user_id=user_id,
            pool_id=pool_id,
            amount=amount,
            tx_hash=tx_hash,
            status=status,
            token_a_amount=token_a_amount,
            token_b_amount=token_b_amount,
            token_a_symbol=token_a_symbol,
            token_b_symbol=token_b_symbol,
            apr_at_entry=apr_at_entry,
            slippage_tolerance=slippage_tolerance,
            price_impact=price_impact,
            expected_lp_tokens=expected_lp_tokens,
            min_lp_tokens=min_lp_tokens,
            actual_lp_tokens=actual_lp_tokens,
            notes=notes,
            created_at=datetime.utcnow()
        )
        
        # Add and commit to database
        db.session.add(investment_log)
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating investment log: {e}")
        return False
```

### Wallet Information Storage

User wallet information is stored securely in the User model:

```python
# User model fields for wallet data
wallet_address = Column(String(255), nullable=True)  # Solana wallet public address
wallet_connected_at = Column(DateTime, nullable=True)  # When wallet was connected
connection_status = Column(String(20), default="disconnected")  # disconnected, connecting, connected, failed
wallet_session_id = Column(String(100), nullable=True)  # For WalletConnect session tracking
last_tx_id = Column(String(100), nullable=True)  # Last transaction signature
```

The system never stores private keys or seed phrases, maintaining a non-custodial architecture.

## 8. Security and Error Handling

### Transaction Security Measures

FiLot implements several security measures to protect users:

1. **Slippage Protection**:
   ```python
   # Calculate minimum acceptable LP tokens based on slippage tolerance
   min_lp_tokens = expected_lp_tokens * (1 - (slippage_tolerance / 100))
   
   # Include in transaction data
   data = bytes([
       1,  # Instruction index for addLiquidity
       *list(token_a_lamports.to_bytes(8, 'little')),
       *list(token_b_lamports.to_bytes(8, 'little')),
       *list(min_lp_lamports.to_bytes(8, 'little')),  # Minimum LP tokens (slippage protection)
   ])
   ```

2. **Pre-Transaction Validations**:
   ```python
   # Check wallet connection status
   if user.connection_status != "connected" or not user.wallet_session_id:
       return {
           "success": False,
           "error": "Wallet not connected",
           "message": "Your wallet is not properly connected. Please reconnect your wallet and try again."
       }
       
   # Check if pool exists and is active
   if not pool_data or pool_data.get('status') == 'inactive':
       return {
           "success": False,
           "error": "Inactive pool",
           "message": "This liquidity pool is currently inactive. Please choose another pool."
       }
   
   # Check investment amount limits
   if amount < min_investment or amount > max_investment:
       return {
           "success": False,
           "error": "Investment amount invalid",
           "message": f"Investment amount must be between ${min_investment} and ${max_investment}."
       }
       
   # Check price impact
   if price_impact > max_safe_impact:
       return {
           "success": False, 
           "error": "High price impact",
           "message": f"This transaction would have a high price impact of {price_impact:.2f}%. Try a smaller amount."
       }
   ```

3. **Two-Step Confirmation**:
   - Initial confirmation after entering amount
   - Detailed confirmation with token amounts and price impact
   - Final approval in wallet app

4. **Non-Custodial Architecture**:
   - Private keys never leave user's wallet
   - Transactions are signed in the user's wallet app
   - FiLot only builds and submits transactions

### Error Handling

FiLot implements comprehensive error handling at multiple levels:

1. **Global Error Handler**:
   ```python
   async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
       """Handle errors in bot commands and callbacks."""
       try:
           if update and update.effective_user:
               user_id = update.effective_user.id
           else:
               user_id = None
               
           # Get error details
           error = context.error
           tb_string = ''.join(traceback.format_exception(None, error, error.__traceback__))
           
           # Log error to database
           from models import ErrorLog, db
           error_log = ErrorLog(
               error_type=type(error).__name__,
               error_message=str(error),
               traceback=tb_string,
               module=error.__module__,
               user_id=user_id
           )
           db.session.add(error_log)
           db.session.commit()
           
           # Send user-friendly message
           if update and update.effective_message:
               await update.effective_message.reply_text(
                   "I encountered an error processing your request. Please try again later."
               )
               
           # Log to system logger
           logger.error(f"Exception while handling an update: {error}\n{tb_string}")
           
       except Exception as e:
           logger.error(f"Error in error handler: {e}")
   ```

2. **Transaction-Specific Error Handling**:
   ```python
   try:
       # Attempt transaction execution
       # ...
   except Exception as e:
       # Log the error
       logger.error(f"Error executing investment: {e}")
       
       # Log to database
       await create_investment_log(
           user_id=user_id,
           pool_id=pool_id,
           amount=amount,
           tx_hash="error",
           status="failed",
           notes=f"Error: {str(e)}"
       )
       
       # Handle specific error types
       if isinstance(e, InsufficientFundsError):
           message = "You don't have enough funds to complete this transaction."
       elif isinstance(e, WalletConnectionError):
           message = "Your wallet is no longer connected. Please reconnect and try again."
       elif isinstance(e, RpcError):
           message = "There was an issue connecting to the blockchain. Please try again later."
       else:
           message = "An unexpected error occurred. Please try again later."
           
       # Return user-friendly error
       return {
           "success": False,
           "error": str(e),
           "message": message
       }
   ```

3. **User Rejection Handling**:
   ```python
   # Special case for user rejection in wallet
   if "rejected" in str(error_msg).lower() or "declined" in str(error_msg).lower():
       # Log the rejection
       await create_investment_log(
           user_id=user_id,
           pool_id=pool_id,
           amount=amount,
           tx_hash="user_rejected",
           status="failed",
           notes="User rejected transaction in wallet"
       )
       
       return {
           "success": False,
           "error": "Transaction rejected",
           "message": "You declined to sign the transaction in your wallet."
       }
   ```

4. **API Error Handling**:
   ```python
   async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
       """Make a request to the API."""
       try:
           # Build and execute request
           # ...
           
           # Check response status
           if response.status == 200:
               return await response.json()
           else:
               error_text = await response.text()
               logger.error(f"API error ({response.status}): {error_text}")
               
               # Return error information
               return {"error": f"API error: {response.status}", "details": error_text}
               
       except aiohttp.ClientError as e:
           logger.error(f"Request error: {e}")
           return {"error": f"Connection error: {str(e)}"}
           
       except Exception as e:
           logger.error(f"Unexpected error in API request: {e}")
           return {"error": f"Unexpected error: {str(e)}"}
   ```

## 9. Session, State, and Persistence

### Wallet Session Management

Wallet sessions are managed by the WalletConnectManager class:

```python
class WalletConnectManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.sessions = {}  # User ID -> Session info
        
    async def create_session(self, user_id: int) -> Dict[str, Any]:
        """Create a new WalletConnect session."""
        # Generate session
        session_id = str(uuid.uuid4())
        uri = f"wc:{session_id}?bridge=https://bridge.walletconnect.org&key={session_key}"
        
        # Store session info
        self.sessions[user_id] = {
            "session_id": session_id,
            "created_at": datetime.utcnow(),
            "status": "pending",
            "wallet_address": None,
            "uri": uri
        }
        
        # Also update user in database
        user = User.query.filter_by(id=user_id).first()
        if user:
            user.wallet_session_id = session_id
            user.connection_status = "connecting"
            db.session.commit()
        
        return {
            "session_id": session_id,
            "qr_code_base64": self.generate_qr_code(uri),
            "uri": uri,
            "expires_at": datetime.utcnow() + timedelta(minutes=15)
        }
```

### User State Management

User states are managed through:

1. **Conversation Handlers**:
   - The python-telegram-bot ConversationHandler manages conversation states
   - State transitions happen in response to user input
   - Timeouts automatically end conversations after inactivity

2. **User Data in Context**:
   - Temporary data is stored in `context.user_data` dictionary
   - Example: During investment flow, pool data is stored in context.user_data["pool_info"]

3. **Database Persistence**:
   - Long-term user data is stored in database models
   - User preferences, wallet info, and transaction history are persistent

### Caching and Fallback Logic

FiLot implements caching strategies to improve performance and resilience:

1. **Token Price Caching**:
   ```python
   class TokenPriceCache:
       """Cache for token prices to reduce API calls."""
       
       def __init__(self, cache_file: str = "token_price_cache.json", max_age: int = 15 * 60):
           """Initialize the token price cache."""
           self.cache_file = cache_file
           self.max_age = max_age  # Maximum age in seconds (default 15 minutes)
           self.cache = self._load_cache()
           
       def get(self, token_symbol: str) -> Optional[float]:
           """Get a cached token price if available and fresh."""
           now = time.time()
           if token_symbol in self.cache:
               entry = self.cache[token_symbol]
               if now - entry["timestamp"] < self.max_age:
                   return entry["price"]
           return None
           
       def set(self, token_symbol: str, price: float) -> None:
           """Cache a token price."""
           self.cache[token_symbol] = {
               "price": price,
               "timestamp": time.time()
           }
           self._save_cache()
   ```

2. **Database Fallbacks**:
   ```python
   class DBFallback:
       """Fallback mechanisms for database operations."""
       
       @staticmethod
       async def get_pools(max_age: int = 60 * 60) -> List[Dict[str, Any]]:
           """Get pools from API or fallback to database if API fails."""
           try:
               # Try API first
               from solpool_api_client import get_all_pools
               pools = await get_all_pools()
               
               if pools and not isinstance(pools, dict):
                   # API succeeded, update cache in database
                   from models import Pool, db
                   
                   # Update pool records
                   for pool_data in pools:
                       pool = Pool.query.filter_by(id=pool_data["id"]).first()
                       if pool:
                           # Update existing pool
                           for key, value in pool_data.items():
                               if hasattr(pool, key):
                                   setattr(pool, key, value)
                       else:
                           # Create new pool
                           pool = Pool(**pool_data)
                           db.session.add(pool)
                   
                   db.session.commit()
                   return pools
           except Exception as e:
               logger.error(f"API error in get_pools, using database fallback: {e}")
           
           # API failed or returned error, use database
           try:
               pools = Pool.query.filter(
                   Pool.last_updated > datetime.utcnow() - timedelta(seconds=max_age)
               ).all()
               
               return [
                   {
                       "id": pool.id,
                       "token_a_symbol": pool.token_a_symbol,
                       "token_b_symbol": pool.token_b_symbol,
                       "apr_24h": pool.apr_24h,
                       "tvl": pool.tvl,
                       # ... other fields
                   }
                   for pool in pools
               ]
           except Exception as db_error:
               logger.error(f"Database fallback also failed: {db_error}")
               return []
   ```

## 10. How It Runs

### Concurrent Operation

FiLot runs with concurrent processes:

1. **Telegram Bot**: Handles user interactions and commands
2. **Flask Web App**: Provides web interface and REST API endpoints
3. **Background Tasks**: Cron jobs and scheduled tasks

### Startup Sequence

1. **Environment Setup**:
   ```python
   # Load environment variables
   load_dotenv()
   
   # Configure logging
   logging.basicConfig(
       format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
       level=logging.INFO
   )
   ```

2. **Database Initialization**:
   ```python
   # Initialize database connection
   app = Flask(__name__)
   app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
   db.init_app(app)
   
   # Create tables if needed
   with app.app_context():
       db.create_all()
   ```

3. **API Clients Setup**:
   ```python
   # Initialize API clients
   solpool_client = SolPoolClient(os.environ.get("SOLPOOL_API_KEY"))
   filotsense_client = FilotSenseClient(os.environ.get("FILOTSENSE_API_KEY"))
   ```

4. **WalletConnect Setup**:
   ```python
   # Initialize WalletConnect manager
   wallet_connect_manager = WalletConnectManager(os.environ.get("WALLETCONNECT_PROJECT_ID"))
   ```

5. **Bot Initialization**:
   ```python
   # Create application and register handlers
   application = ApplicationBuilder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()
   
   # Register command handlers
   application.add_handler(CommandHandler("start", start))
   # ... other handlers
   
   # Start the application
   application.run_polling()
   ```

6. **Web App Start**:
   ```python
   # In a separate process or thread
   if __name__ == "__main__":
       port = int(os.environ.get("PORT", 5000))
       app.run(host="0.0.0.0", port=port)
   ```

### Background Tasks

FiLot runs several background tasks:

1. **Pool Data Update**:
   ```python
   def update_pool_data():
       """Update pool data from API."""
       while True:
           try:
               # Fetch fresh pool data
               pools = solpool_client.get_all_pools()
               
               # Update database
               with app.app_context():
                   for pool_data in pools:
                       pool = Pool.query.filter_by(id=pool_data["id"]).first()
                       if pool:
                           # Update existing pool
                           for key, value in pool_data.items():
                               if hasattr(pool, key):
                                   setattr(pool, key, value)
                           pool.last_updated = datetime.utcnow()
                       else:
                           # Create new pool
                           pool = Pool(**pool_data, last_updated=datetime.utcnow())
                           db.session.add(pool)
                   
                   db.session.commit()
           except Exception as e:
               logger.error(f"Error updating pool data: {e}")
           
           # Sleep for 15 minutes
           time.sleep(15 * 60)
   
   # Start the background thread
   threading.Thread(target=update_pool_data, daemon=True).start()
   ```

2. **Transaction Status Monitor**:
   ```python
   def monitor_transactions():
       """Monitor and update transaction statuses."""
       while True:
           try:
               with app.app_context():
                   # Find transactions in 'confirming' status
                   confirming_txs = InvestmentLog.query.filter_by(status="confirming").all()
                   
                   for tx in confirming_txs:
                       # Check transaction status
                       status = check_transaction_status(tx.tx_hash)
                       
                       if status["confirmed"]:
                           # Update to confirmed
                           tx.status = "confirmed"
                       elif time.time() - tx.created_at.timestamp() > 24 * 60 * 60:
                           # More than 24 hours old, mark as timed out
                           tx.status = "timed_out"
                           tx.notes = "Transaction timed out waiting for confirmation"
                   
                   db.session.commit()
           except Exception as e:
               logger.error(f"Error monitoring transactions: {e}")
           
           # Sleep for 5 minutes
           time.sleep(5 * 60)
   
   # Start the background thread
   threading.Thread(target=monitor_transactions, daemon=True).start()
   ```

3. **Anti-Idle Thread**:
   ```python
   def start_anti_idle_thread():
       """Start a thread that keeps the application active."""
       def keep_alive():
           """Keep the application alive by performing regular database activity."""
           while True:
               try:
                   with app.app_context():
                       # Perform a simple query to keep connection active
                       db.session.execute(text("SELECT 1"))
                       db.session.commit()
               except Exception as e:
                   logger.error(f"Error in keep-alive thread: {e}")
               
               # Sleep for 5 minutes
               time.sleep(5 * 60)
       
       # Start the thread
       thread = threading.Thread(target=keep_alive, daemon=True)
       thread.start()
       logger.info("Anti-idle thread started")
   ```

## 11. Future Architecture Hooks

FiLot's architecture is designed with extension points for future enhancements:

### Slippage Tolerance Configurability

The system is ready to support user-configurable slippage tolerance:

```python
# Current implementation (fixed 0.5% slippage)
async def build_raydium_lp_transaction(
    # ...other parameters
    slippage_tolerance: float = 0.5,
    # ...
):
    # ...

# Future implementation with user preferences
async def build_raydium_lp_transaction(
    # ...other parameters
    slippage_tolerance: float = None,
    # ...
):
    # Get user's preferred slippage if not specified
    if slippage_tolerance is None:
        user = User.query.filter_by(wallet_address=wallet_address).first()
        if user and user.preferred_slippage:
            slippage_tolerance = user.preferred_slippage
        else:
            slippage_tolerance = 0.5  # Default
    
    # ...rest of implementation
```

User interface for setting slippage:

```python
async def handle_set_slippage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle slippage tolerance setting."""
    query = update.callback_query
    await query.answer()
    
    # Extract slippage value
    match = re.match(r"set_slippage:(\d+\.\d+)", query.data)
    if not match:
        return ConversationHandler.END
        
    slippage = float(match.group(1))
    user_id = update.effective_user.id
    
    # Update user preferences
    user = User.query.filter_by(id=user_id).first()
    if user:
        user.preferred_slippage = slippage
        db.session.commit()
    
    # Confirm to user
    await query.edit_message_text(
        f"Slippage tolerance set to {slippage}%",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Back to Settings", callback_data="settings")
        ]])
    )
    
    return ConversationHandler.END
```

### AI Advisor Upgrades

The current AI advisor system can be extended with more sophisticated models:

```python
# Current simple weighting system
score = (
    pool["apr_24h"] * 0.3 +               # 30% weight on APR
    math.log10(pool["tvl"]) * 0.2 +       # 20% weight on TVL (log-scaled)
    prediction["score"] * 0.25 +           # 25% weight on prediction
    ((token_a_sentiment["score"] + token_b_sentiment["score"]) / 2) * 0.25  # 25% on sentiment
)

# Future ML-based approach
def get_ml_score(pool_data, prediction, sentiment, user_history):
    """Get score from ML model."""
    # Prepare features
    features = {
        "apr_24h": pool_data["apr_24h"],
        "tvl": math.log10(pool_data["tvl"]),
        "volume_24h": math.log10(pool_data["volume_24h"] + 1),
        "prediction_score": prediction["score"],
        "token_a_sentiment": sentiment["token_a"]["score"],
        "token_b_sentiment": sentiment["token_b"]["score"],
        "volatility": pool_data["volatility"],
        "age_days": pool_data["age_days"],
        "fee": pool_data["fee"],
    }
    
    # Call trained model
    import pickle
    with open("models/pool_scorer.pkl", "rb") as f:
        model = pickle.load(f)
    
    return model.predict_proba([list(features.values())])[0][1]  # Probability of good investment
```

### DeFi Aggregator Integration

The system is designed to support integration with DeFi aggregators:

```python
# Future Jupiter integration for best execution
async def execute_jupiter_swap(wallet_address: str, input_token: str, output_token: str, amount: float) -> Dict[str, Any]:
    """Execute a swap via Jupiter aggregator."""
    try:
        # Initialize Jupiter client
        from jupiter_client import JupiterClient
        jupiter = JupiterClient()
        
        # Get quote
        quote = await jupiter.get_quote(
            input_mint=input_token,
            output_mint=output_token,
            amount=amount
        )
        
        # Build transaction
        tx_data = await jupiter.build_swap_transaction(
            wallet_address=wallet_address,
            quote=quote
        )
        
        # Send for signing
        signing_result = await send_transaction_for_signing(
            wallet_address=wallet_address,
            serialized_transaction=tx_data["serialized_transaction"]
        )
        
        # Submit signed transaction
        return await submit_signed_transaction(signing_result["signature"])
        
    except Exception as e:
        logger.error(f"Error in Jupiter swap: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to execute swap via Jupiter."
        }
```

### Transaction History and Analysis

The system can be extended with comprehensive transaction history:

```python
# Future transaction history query
async def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Get user's transaction history with performance metrics."""
    try:
        # Get basic transaction data
        transactions = InvestmentLog.query.filter_by(user_id=user_id).order_by(InvestmentLog.created_at.desc()).limit(limit).all()
        
        result = []
        for tx in transactions:
            # Get pool current data
            pool_data = await solpool_client.get_pool(tx.pool_id)
            
            # Calculate performance metrics
            apr_then = tx.apr_at_entry or 0
            apr_now = pool_data.get("apr_24h", 0)
            apr_change = apr_now - apr_then
            
            # Estimate current value
            days_since = (datetime.utcnow() - tx.created_at).days
            estimated_value = tx.amount * (1 + (apr_then / 100 / 365) * days_since)
            
            result.append({
                "id": tx.id,
                "pool_id": tx.pool_id,
                "amount": tx.amount,
                "status": tx.status,
                "tx_hash": tx.tx_hash,
                "created_at": tx.created_at.isoformat(),
                "token_a_symbol": tx.token_a_symbol,
                "token_b_symbol": tx.token_b_symbol,
                "apr_then": apr_then,
                "apr_now": apr_now,
                "apr_change": apr_change,
                "days_held": days_since,
                "estimated_value": estimated_value,
                "tx_link": f"https://solscan.io/tx/{tx.tx_hash}"
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting user transactions: {e}")
        return []
```

### Automated Exit Recommendations

The system can be extended with exit recommendations:

```python
# Future exit recommendation engine
async def get_exit_recommendations(user_id: int) -> List[Dict[str, Any]]:
    """Get recommendations for which positions to exit."""
    try:
        # Get user's active investments
        investments = InvestmentLog.query.filter_by(
            user_id=user_id, 
            status="confirmed"
        ).all()
        
        recommendations = []
        for inv in investments:
            # Get current pool data
            pool_data = await solpool_client.get_pool(inv.pool_id)
            
            # Get prediction and sentiment
            prediction = await solpool_client.get_pool_prediction(inv.pool_id)
            
            # Calculate exit score (higher = stronger exit recommendation)
            exit_score = 0
            
            # Factor 1: APR decrease
            apr_then = inv.apr_at_entry or 0
            apr_now = pool_data.get("apr_24h", 0)
            apr_change = apr_now - apr_then
            
            if apr_change < -5:  # APR decreased by more than 5%
                exit_score += 30
            elif apr_change < -2:  # APR decreased by more than 2%
                exit_score += 15
                
            # Factor 2: Prediction score decline
            if prediction["score"] < 40:  # Low prediction score
                exit_score += 25
                
            # Factor 3: Time held
            days_held = (datetime.utcnow() - inv.created_at).days
            if days_held > 30:  # Held for more than 30 days
                exit_score += 10
                
            # Add to recommendations if score is high enough
            if exit_score >= 40:
                recommendations.append({
                    "investment_id": inv.id,
                    "pool_id": inv.pool_id,
                    "token_a_symbol": inv.token_a_symbol,
                    "token_b_symbol": inv.token_b_symbol,
                    "amount": inv.amount,
                    "days_held": days_held,
                    "apr_change": apr_change,
                    "exit_score": exit_score,
                    "reason": get_exit_reason(apr_change, prediction["score"], days_held)
                })
        
        # Sort by exit score (highest first)
        recommendations.sort(key=lambda x: x["exit_score"], reverse=True)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting exit recommendations: {e}")
        return []
```

## Conclusion

FiLot is a comprehensive, production-ready Telegram bot for DeFi investments on Solana. Its architecture combines:

- Secure wallet integration via WalletConnect
- Real blockchain transactions with comprehensive safety features
- AI-powered investment recommendations
- Extensive error handling and fallback mechanisms
- Comprehensive database integration for persistence and tracking

The modular design allows for easy extension and enhancement of existing features, while the focus on security and error handling ensures a reliable user experience.