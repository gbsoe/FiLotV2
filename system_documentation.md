# FiLot - Cryptocurrency Investment Bot System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Database Schema](#database-schema)
5. [API Integrations](#api-integrations)
6. [Bot Commands](#bot-commands)
7. [Web Interface](#web-interface)
8. [Environment Variables](#environment-variables)
9. [Development Workflow](#development-workflow)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

## System Overview

FiLot is a cutting-edge Telegram bot designed to revolutionize cryptocurrency investment experiences through intelligent, user-friendly technologies. The system helps users make informed investment decisions, manage portfolios, and automate cryptocurrency investments on the Solana blockchain.

### Key Features

- Real-time cryptocurrency pool information
- AI-driven investment recommendations
- Investment simulation tools
- Wallet integration via WalletConnect v2
- Portfolio tracking and management
- Automated investment strategies
- Natural language query processing

## Architecture

The system is designed with a multi-layer architecture:

### 1. Data Collection Layer
- **Real-time Pool Data**: Integration with Raydium API
- **Market Sentiment Analysis**: News aggregators and social media tracking
- **Token Analytics**: Historical price data and volatility metrics

### 2. Analysis Layer
- **Risk Assessment Engine**: Pool stability scoring and impermanent loss prediction
- **Performance Prediction**: APR forecasting models
- **Strategy Formulation**: Investment timing and position sizing recommendations

### 3. Decision Layer
- **User Profile Matching**: Risk tolerance mapping and preference learning
- **Recommendation Generation**: Multi-criteria ranking algorithms
- **Automation Rules Engine**: Conditional logic processor and trigger event monitoring

### 4. Execution Layer
- **Wallet Integration**: WalletConnect v2 implementation
- **Transaction Management**: Transaction preparation and monitoring
- **Security Controls**: Transaction limits and approval workflows

## Core Components

### 1. Main Application (app.py)
The Flask web application that serves as the web interface for the bot, providing:
- Health check endpoint
- Admin dashboard
- User statistics
- System status monitoring

### 2. Telegram Bot (bot.py)
The core bot functionality handling:
- Command processing
- User interactions
- Message parsing
- Callback query handling

### 3. WSGI Entry Point (wsgi.py)
Entry point for the Flask web application and Telegram bot, responsible for:
- Starting both Flask and bot applications
- Configuration loading
- Thread management

### 4. Database Utilities (db_utils.py)
Utilities for database operations including:
- Session management
- Backup and restore functionality
- Schema migrations
- Query optimization

### 5. WalletConnect Integration (walletconnect_utils.py)
Utilities for integrating with WalletConnect protocol:
- Session creation and management
- Wallet connection verification
- Transaction signing

### 6. Raydium Client (raydium_client.py)
Client for interacting with the Raydium API:
- Pool data retrieval
- Transaction preparation
- Market data analysis

### 7. Anthropic AI Service (anthropic_service.py)
Integration with Claude AI for:
- Advanced query processing
- Investment recommendations
- Natural language interactions

## Database Schema

The system uses PostgreSQL for data storage with the following key models:

### User Model
```python
class User(db.Model):
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_subscribed = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    message_count = Column(Integer, default=0)
    spam_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_active = Column(DateTime, nullable=True)
```

### Pool Model
```python
class Pool(db.Model):
    id = Column(String(255), primary_key=True)
    token_a_symbol = Column(String(20), nullable=False)
    token_b_symbol = Column(String(20), nullable=False)
    apr_24h = Column(Float, nullable=True)
    apr_7d = Column(Float, nullable=True)
    apr_30d = Column(Float, nullable=True)
    tvl = Column(Float, nullable=True)
    token_a_price = Column(Float, nullable=True)
    token_b_price = Column(Float, nullable=True)
    fee = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    tx_count_24h = Column(Integer, nullable=True)
    last_updated = Column(DateTime, nullable=True)
```

### BotStatistics Model
```python
class BotStatistics(db.Model):
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, unique=True)
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    commands_used = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    subscription_rate = Column(Float, default=0.0)
```

### Transaction Tables
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(255) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    wallet_address VARCHAR(255) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    amount NUMERIC(20, 8) NOT NULL,
    token_symbol VARCHAR(50) NOT NULL,
    target_symbol VARCHAR(50),
    pool_id VARCHAR(255),
    simulation_result JSONB,
    transaction_data JSONB,
    transaction_signature VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
)
```

### Automation Rules Table
```sql
CREATE TABLE automation_rules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    trigger_conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    max_transaction_amount NUMERIC(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_executed_at TIMESTAMP,
    execution_count INTEGER DEFAULT 0
)
```

## API Integrations

### 1. Raydium API
- **Base URL**: https://raydium-trader-filot.replit.app
- **Authentication**: API key in x-api-key header
- **Main Endpoints**:
  - `/health` - Check API health
  - `/api/pools` - Get all pools
  - `/api/pool/{pool_id}` - Get specific pool details
  - `/api/pools/filter` - Filter pools by criteria

### 2. Anthropic Claude API
- Used for advanced AI-driven financial advice
- Requires ANTHROPIC_API_KEY environment variable
- Handles complex user queries and generates investment recommendations

### 3. Solana RPC API
- Used for blockchain interactions
- Requires SOLANA_RPC_URL environment variable
- Handles wallet balance checking and transaction submissions

### 4. WalletConnect API
- Used for wallet integration
- Requires WALLETCONNECT_PROJECT_ID environment variable
- Handles session creation and transaction signing

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize the bot and see welcome message |
| `/help` | Display help information and available commands |
| `/info` | Get information about a specific cryptocurrency or pool |
| `/simulate` | Simulate an investment strategy |
| `/subscribe` | Subscribe to daily updates |
| `/unsubscribe` | Unsubscribe from daily updates |
| `/status` | Check the status of the system |
| `/verify` | Verify user identity |
| `/wallet` | Manage connected wallets |

## Web Interface

The web interface provides:
- Health check endpoint (`/health`)
- Admin dashboard for monitoring
- User statistics visualization
- System status overview

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_TOKEN` | Telegram Bot API token | Yes |
| `DATABASE_URL` | PostgreSQL database connection string | Yes |
| `SESSION_SECRET` | Secret key for session encryption | Yes |
| `ANTHROPIC_API_KEY` | API key for Claude AI service | Yes |
| `WALLETCONNECT_PROJECT_ID` | Project ID for WalletConnect | Yes |
| `SOLANA_RPC_URL` | RPC URL for Solana blockchain interaction | Yes |
| `RAYDIUM_API_URL` | URL for Raydium API service | Yes |
| `RAYDIUM_API_KEY` | API key for Raydium service | Yes |

## Development Workflow

1. **Local Setup**
   - Clone the repository
   - Install dependencies
   - Set up environment variables
   - Initialize the database

2. **Development Process**
   - Make changes to code
   - Run tests
   - Verify with local Telegram bot instance
   - Submit changes for review

3. **Database Migration**
   - Use `fix_database.py` script for schema updates
   - Test migrations in development environment before deploying

## Deployment

The system is deployed on Replit with:
- Flask application running on gunicorn
- Telegram bot running in a separate thread
- PostgreSQL database for data storage
- Environment variables configured in Replit Secrets

## Troubleshooting

### Common Issues

1. **Bot Not Responding**
   - Check if the Telegram token is valid
   - Verify bot process is running
   - Check for errors in logs

2. **Database Connection Issues**
   - Verify DATABASE_URL is correct
   - Check PostgreSQL service is running
   - Try resetting the connection pool

3. **API Integration Issues**
   - Verify API keys are valid
   - Check network connectivity
   - Inspect response data for errors

### Debug Tools

1. **debug_bot.py**
   - Runs bot with enhanced logging
   - Exposes web interface for log inspection

2. **debug_remote.py**
   - Provides system diagnostics
   - Collects logs and environment information
   - Checks connectivity to external services

---

*Last Updated: May 12, 2025*