# FiLot: Agentic AI Investment Advisor

FiLot is a cutting-edge Telegram bot designed to revolutionize cryptocurrency investment experiences through intelligent, user-friendly technologies. It serves as an agentic AI-powered system that analyzes liquidity pools, recommends optimal investments, and executes trades securely with production-grade transaction safety and slippage protection.

## Core Features

- **Data-Driven Insights**: Real-time data ingestion from Raydium and external sources
- **Advanced AI Models**: Financial analysis and personalized recommendations
- **Reinforcement Learning**: Adaptive investment recommendations with risk-adjusted returns
- **User-Friendly Interface**: Intuitive Telegram interactions with detailed transaction information
- **Production-Grade Transaction Safety**: Comprehensive pre-checks, slippage protection, and price impact analysis
- **Secure Wallet Integration**: WalletConnect v2 protocol support with full transaction lifecycle management
- **Personalized Risk Management**: Customized strategies based on user profiles
- **Enhanced Error Handling**: Detailed error logging and user-friendly recovery paths

## Project Structure

### Main Components

- **Telegram Bot**: Core user interface via Telegram messaging platform
- **Flask Web Server**: Administrative interface and background services
- **AI Services**: Integrated AI models for financial advice and decision-making
- **Database**: PostgreSQL database for storing user profiles, transactions, and market data
- **Blockchain Integration**: Services for interacting with Solana blockchain and liquidity pools

### Key Files

- `main.py`: Application entry point
- `bot.py`: Telegram bot command handlers and logic
- `app.py`: Flask web application
- `models.py`: SQLAlchemy database models with enhanced investment tracking
- `raydium_client.py`: Integration with Raydium API for pool data
- `wallet_actions.py`: Real Solana transaction execution with slippage protection
- `walletconnect_manager.py`: WalletConnect v2 integration for secure wallet connectivity
- `smart_invest_execution.py`: Production-grade investment flows with comprehensive safety checks
- `solpool_api_client.py`: Client for SolPool Insight API with real-time pool data and price impact analysis
- `ai_service.py`: DeepSeek AI integration
- `anthropic_service.py`: Anthropic Claude AI integration
- `agentic_advisor.py`: Intelligent investment advisor combining technical data with sentiment
- `rl_investment_advisor.py`: Reinforcement Learning model for adaptive investment recommendations
- `db_utils.py`: Database utility functions
- `coingecko_utils.py`: Token price retrieval utilities

## Installation and Setup

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Telegram Bot Token
- DeepSeek API Key (optional)
- Anthropic API Key (optional)
- WalletConnect Project ID (optional)
- Solana RPC URL (optional)
- SolPool Insight API Key (required for pool data)
- FilotSense API Key (required for sentiment analysis)

### Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://username:password@localhost:5432/filot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
WALLETCONNECT_PROJECT_ID=your_walletconnect_project_id
SOLANA_RPC_URL=your_solana_rpc_url
SOLPOOL_API_KEY=your_solpool_api_key
FILOTSENSE_API_KEY=your_filotsense_api_key
```

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up the database:
   ```
   python create_tables.py
   ```

### Development Mode

Start the application in development mode:
```
python main.py
```

### Production Deployment

For production deployment, use one of these methods:

1. **Using Procfile** (recommended for platforms like Heroku):
   ```
   web: gunicorn --bind 0.0.0.0:$PORT wsgi:application
   worker: python run_bot.py
   ```

2. **Using shell script**:
   ```
   chmod +x run_production.sh
   ./run_production.sh
   ```

See the [Production Deployment Guide](PRODUCTION_DEPLOYMENT_GUIDE.md) for detailed instructions.

## Bot Commands

- `/start`: Introduction to the bot
- `/help`: List available commands
- `/info`: Show current pool information
- `/simulate [amount]`: Simulate investment returns
- `/smart_invest`: Start the AI-powered investment advisor using Reinforcement Learning
- `/invest`: Traditional investment flow
- `/subscribe`: Subscribe to daily updates
- `/unsubscribe`: Unsubscribe from updates
- `/profile`: Set risk profile and preferences
- `/wallet`: Connect and manage wallet
- `/walletconnect`: Connect wallet via WalletConnect
- `/interactive`: Access the interactive menu with button controls

## Smart Invest: AI-Powered Investment Advisor

The `/smart_invest` command and "🧠 Smart Invest" button activate FiLot's advanced Reinforcement Learning-based investment advisor:

### Features

- **Adaptive Learning**: The system learns and improves recommendations based on historical performance
- **Personalized Risk Assessment**: Tailors recommendations to user's specific risk profile
- **Multi-factor Analysis**: Analyzes APR, TVL, volume, volatility, and other key metrics
- **Confidence Ratings**: Provides AI confidence scores for each recommendation
- **Market Timing Insights**: Suggests optimal entry and exit points based on market conditions
- **Exit Recommendations**: Helps determine when to exit positions based on changing conditions

### How It Works

1. The system uses a DQN (Deep Q-Network) architecture with experience replay
2. Features are extracted from real-time pool data (APR, TVL, volatility, etc.)
3. Recommendations are weighted based on:
   - 50% technical factors (APR, TVL, volume)
   - 25% prediction scores from SolPool Insight API
   - 25% sentiment data from FilotSense API
4. Users provide feedback on investments, which trains the model further

Access Smart Invest through the `/smart_invest` command or by clicking "🧠 Smart Invest" in the Investment Options menu.

## Development Roadmap

See the [Development Roadmap](FiLot_Development_Roadmap.md) for detailed information on project phases and progress.

## Technical Documentation

- [Project Summary](FiLot_Project_Summary.md): Overview of current status and next steps
- [Agentic Investment Technical Specification](FiLot_Agentic_Investment_Technical_Spec.md): Technical details of the agentic investment system
- [Implementation Plan](FiLot_Implementation_Plan.md): Phased approach to implementing agentic capabilities
- [Production Ready Report](FILOT_PRODUCTION_READY_REPORT.md): Detailed report on transaction safety features
- [Solana Transaction Integration](SOLANA_TRANSACTION_INTEGRATION.md): Documentation of real Solana transaction implementation

## Security

FiLot implements comprehensive security measures:

- Non-custodial architecture (users maintain control of funds)
- WalletConnect v2 for secure wallet integration
- Read-only wallet access by default with explicit transaction authorization
- Production-grade transaction safety features:
  - Default 0.5% slippage protection with minimum LP token calculation
  - Price impact warnings for large transactions
  - Comprehensive pre-transaction checks for wallet connection, pool validity, and investment limits
  - Two-step confirmation process with detailed transaction information
  - Complete transaction lifecycle management with failure handling
- Enhanced transaction logging with detailed tracking for audit purposes
- User-friendly error handling with clear recovery paths

## Contact Information

- Product Owner: george@justhodl.la
- Telegram Channel: https://t.me/CrazyRichLAToken
- Telegram Bot: https://t.me/crazyrichlabot
- Instagram: https://www.instagram.com/crazyrichla
- X/Twitter: https://x.com/crazyrichla

## License

Copyright © 2025 CrazyRichLA. All rights reserved.