# FiLot: Agentic AI Investment Advisor

FiLot is a cutting-edge Telegram bot designed to revolutionize cryptocurrency investment experiences through intelligent, user-friendly technologies. FiLot serves as an agentic AI-powered system that analyzes liquidity pools, recommends optimal investments, and can execute trades securely with varying levels of automation.

With our new simplified One-Command interface and persistent navigation buttons, investing in cryptocurrency has never been more accessible. FiLot specializes in providing access to Raydium liquidity pools on the Solana blockchain, offering institutional-grade investment opportunities with advanced security features and AI-driven recommendations.

## Core Features

- **Data-Driven Insights**: Real-time data ingestion from Raydium and external sources
- **Advanced AI Models**: Financial analysis and personalized recommendations
- **One-Command Interface**: Simplified, button-driven navigation for enhanced user experience
- **Persistent Button Navigation**: Consistent and reliable button functionality throughout the app
- **Secure Wallet Integration**: WalletConnect protocol support for safe transactions
- **Personalized Risk Management**: Customized strategies based on user profiles
- **Enterprise Security**: Institutional-grade security standards and comprehensive safeguards

## Project Structure

### Main Components

- **Telegram Bot**: Core user interface via Telegram messaging platform
- **Flask Web Server**: Administrative interface and background services
- **AI Services**: Integrated AI models for financial advice and reinforcement learning-based investment recommendations
- **Database**: PostgreSQL database for storing user profiles, transactions, and market data
- **Blockchain Integration**: Services for interacting with Solana blockchain and liquidity pools

### Key Files

**Core Infrastructure:**
- `main.py`: Application entry point and initialization
- `bot.py`: Telegram bot command handlers and core logic
- `app.py`: Flask web application for admin interface
- `models.py`: SQLAlchemy database models for data persistence

**Navigation System:**
- `menus.py`: Persistent menu system for One-Command interface
- `keyboard_utils.py`: Button generation and navigation handlers
- `callback_handler.py`: Callback processing for button interactions
- `anti_loop.py`: Prevention of message and button loop issues

**API Integration:**
- `raydium_client.py`: Integration with Raydium API for pool data
- `solpool_client.py`: Solana pool interaction and monitoring
- `filotsense_client.py`: Market sentiment and analytics
- `coingecko_utils.py`: Token price retrieval utilities

**AI Services:**
- `ai_service.py`: DeepSeek AI integration for analysis
- `anthropic_service.py`: Anthropic Claude AI for financial advice
- `intent_detector.py`: User message intent classification
- `recommendation_agent.py`: Investment recommendation engine
- `rl_integration.py`: Reinforcement learning system for optimized investment decisions
- `rl_agent.py`: Deep Q-Network implementation for investment strategy learning
- `rl_environment.py`: Simulated environment for training investment agents

## Installation and Setup

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Telegram Bot Token
- DeepSeek API Key (optional)
- Anthropic API Key (optional)
- WalletConnect Project ID (optional)
- Solana RPC URL (optional)

### Environment Variables

Create a `.env` file with the following variables:

```
DATABASE_URL=postgresql://username:password@localhost:5432/filot
TELEGRAM_TOKEN=your_telegram_bot_token
DEEPSEEK_API_KEY=your_deepseek_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
WALLETCONNECT_PROJECT_ID=your_walletconnect_project_id
SOLANA_RPC_URL=your_solana_rpc_url
```

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up the database:
   ```
   python setup_database.py
   ```
4. Start the application:
   ```
   python main.py
   ```

## One-Command Interface

FiLot features a simplified One-Command interface with persistent buttons for easier navigation:

### Primary Commands
- `/start`: Introduction to the bot and main navigation menu
- `/help`: List available commands and buttons
- `/explore`: Access pool information, simulations, and FAQ
- `/account`: Manage wallet, profile settings, and subscriptions
- `/invest`: View recommended pools and investment opportunities
- `/smart_invest`: Get AI-powered investment recommendations using reinforcement learning

### Navigation Features
- **Persistent Buttons**: Consistent navigation throughout the experience
- **Back Navigation**: Easy return to previous menus
- **Context-Aware Options**: Relevant buttons based on current position
- **Simplified Flows**: Streamlined investment process with fewer steps

### User Experience Improvements
- **Reduced Command Complexity**: No need to remember specific commands or syntax
- **Error Prevention**: Guided navigation eliminates common input errors
- **Consistent UI**: Uniform button layout and standardized responses
- **Progressive Disclosure**: Information presented in manageable, sequential steps
- **Mobile-Optimized**: Designed specifically for comfortable mobile device usage

Commands can also be entered manually, but the button-based interface provides a more intuitive experience.

## Reinforcement Learning Investment System

FiLot features an advanced AI-powered investment recommendation system using reinforcement learning (RL) techniques:

### Key Features

- **Smart Investment Commands**: Get optimized recommendations with the `/smart_invest` command
- **Risk-Profile Adaptation**: Investment recommendations tailored to conservative, moderate, or aggressive profiles
- **Market Timing Analysis**: AI-driven insights about when to enter or exit positions
- **Confidence Ratings**: Transparency about the AI's confidence level in each recommendation
- **Comprehensive Metrics**: Balances APR, TVL, impermanent loss risk, and market volatility
- **Explanation System**: Clear reasoning for why each pool is recommended

### How It Works

1. The RL system analyzes multiple factors including APR, liquidity, token volatility, and market conditions
2. It learns from historical performance data to optimize investment returns
3. Recommendations are balanced based on your risk profile
4. The system continuously improves as it gathers more data

### Benefits Over Traditional Approaches

- **More Balanced Recommendations**: Better risk-adjusted returns compared to simply chasing the highest APR
- **Impermanent Loss Protection**: Considers correlation between tokens to minimize impermanent loss risk
- **Dynamic Adaptation**: Adjusts to changing market conditions rather than using static rules
- **Personalized Strategies**: Tailored to your specific investment goals and risk tolerance

## Understanding Liquidity Pools

Liquidity pools are a simple way to earn rewards from your cryptocurrency holdings. Here's how they work:

- **What is a Liquidity Pool?** A shared collection of funds that allows traders to buy and sell cryptocurrencies more efficiently.

- **How Do You Benefit?** By adding your tokens to these pools, you earn fees generated when others trade using the pool.

- **Why Raydium Pools?** Raydium is a leading platform on the Solana blockchain known for its speed, low fees, and security.

- **Risk Management:** FiLot helps you understand the risks and rewards of each pool before investing.

- **You Maintain Control:** Your tokens remain in your control at all times. FiLot never takes custody of your assets.

## Development Roadmap

See the [Development Roadmap](FiLot_Development_Roadmap.md) for detailed information on project phases and progress.

## Technical Documentation

- [Project Summary](FiLot_Project_Summary.md): Overview of current status and next steps
- [Agentic Investment Technical Specification](FiLot_Agentic_Investment_Technical_Spec.md): Technical details of the agentic investment system
- [Implementation Plan](FiLot_Implementation_Plan.md): Phased approach to implementing agentic capabilities

## Security, Privacy, and Regulatory Compliance

FiLot implements comprehensive security and privacy measures:

### Security Features
- **Institutional-Grade Trust**: Enterprise security standards with rigorous protocols and safeguards
- **Non-custodial Architecture**: Users maintain complete control of their funds at all times
- **WalletConnect Integration**: Secure wallet connectivity without exposing private keys
- **Read-only Access Mode**: Default conservative approach to wallet connections
- **Transaction Limits**: Customizable limits with verification requirements
- **Comprehensive Monitoring**: Advanced logging and real-time monitoring
- **Transparent Operations**: Clear view of all transactions and investment activities

### Privacy Protection
- **Minimal Data Collection**: We only collect essential information needed for service operation
- **No Personal Information**: No requirement for government IDs or sensitive personal information
- **Transparent Data Usage**: Clear information about how user data is used
- **Data Encryption**: All user data is encrypted at rest and in transit
- **Right to Be Forgotten**: Users can request complete removal of their data

## Contact Information

- Product Owner: george@justhodl.la
- Telegram Bot: https://t.me/Fi_lotbot
- Telegram Channel: https://t.me/CrazyRichLAToken
- X/Twitter: https://x.com/crazyrichla
- Instagram: https://www.instagram.com/crazyrichla
- Email Support: support@filot.finance

## License

Copyright © 2025 CrazyRichLA. All rights reserved.