# FiLot Database-Independent Operation Guide

This guide explains how to run the FiLot Telegram bot in database-independent mode when the PostgreSQL database is unavailable.

## Key Components Added

1. **Enhanced Fallback System**: Complete memory-based storage system with disk persistence for critical data
2. **Instance Conflict Resolution**: Prevents multiple bot instances from conflicting with each other
3. **Resilient Bot Runner**: Special launcher that configures the environment for database-independent operation

## How to Run in Database-Independent Mode

When the PostgreSQL database is unavailable, follow these steps:

```bash
# Run the bot with the resilient runner
python run_resilient_bot.py
```

This runner will:
- Terminate any competing bot instances
- Set up memory-based fallback systems
- Configure the environment for resilient operation
- Start the bot with database-independent settings

## Features Available Without Database

The following features will continue to work even when the database is unavailable:

- Menu navigation and all command interfaces
- Pool data viewing with real token information 
- Wallet connection features
- User state and context preservation
- Risk profile and preferences management

## Data Persistence

While operating in database-independent mode, the following data is persisted to disk:

- Pool information in `pool_data_test_results.json`
- Token prices in `token_price_cache.json`
- User profiles in `user_profiles_backup.json`

This ensures that critical data is not lost during database outages and is automatically restored when the bot restarts.

## Monitoring Database Status

The bot will automatically detect when the database becomes available again and will seamlessly transition back to normal operation.

## Troubleshooting

If you encounter issues with the bot:

1. Check if multiple instances are running with `ps aux | grep python`
2. Restart the bot with the resilient runner: `python run_resilient_bot.py`
3. Review the logs for any error messages
4. Ensure the cache files exist and are not corrupted

## Fallback System Architecture

The fallback system uses a multi-layered approach:

- In-memory state tracking for active user sessions
- Disk-based persistence for important user and market data
- Command-specific fallback handlers for specialized functionality

This ensures that the bot remains fully functional during database outages while maintaining data consistency and security.