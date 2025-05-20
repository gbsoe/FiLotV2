# FiLot Telegram Bot Reference

**Bot Name:** FiLot - Your Agentic Financial Assistant  
**Generation Date:** May 20, 2025

This document provides a comprehensive reference of all user-facing commands and interactive buttons in the FiLot Telegram bot.

## Slash Commands

### /faq
**Handler:** `faq_command`  
**Description:** Display frequently asked questions about cryptocurrency pools and investment concepts.

### /help
**Handler:** `help_command`  
**Description:** Send a help message showing available commands and display the help menu.

### /info
**Handler:** `info_command`  
**Description:** Show information about cryptocurrency pools, including APR, volume, and liquidity data.

### /profile
**Handler:** `profile_command`  
**Description:** Set user investment preferences such as risk profile and investment horizon.

### /simulate
**Handler:** `simulate_command`  
**Description:** Calculate potential investment returns based on an amount and time period.

### /social
**Handler:** `social_command`  
**Description:** Display social media links related to FiLot.

### /start
**Handler:** `start_command`  
**Description:** Send a welcome message and initialize the bot for a new user.

### /status
**Handler:** `status_command`  
**Description:** Check the current status of the bot and associated services.

### /subscribe
**Handler:** `subscribe_command`  
**Description:** Subscribe to daily updates about cryptocurrency pools.

### /unsubscribe
**Handler:** `unsubscribe_command`  
**Description:** Unsubscribe from daily updates.

### /verify
**Handler:** `verify_command`  
**Description:** Verify the user's identity with a verification code.

### /wallet
**Handler:** `wallet_command`  
**Description:** Manage wallet connections and view wallet information.

### /walletconnect
**Handler:** `walletconnect_command`  
**Description:** Connect wallet using WalletConnect protocol and QR code.

## Button Callbacks

### Main Navigation

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 💰 Invest | `invest` | `handle_invest` | Display investment options menu. |
| 🧭 Explore Pools | `explore_pools` | `handle_explore_pools` | Show pool exploration options. |
| 👤 My Account | `account` | `handle_account` | Display user account information and settings. |
| ℹ️ Help | `help` | `handle_help` | Show help menu with support options. |
| ⬅️ Back to Main Menu | `back_to_main` | `handle_back_to_main` | Return to the main menu from any submenu. |

### Investment Options

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 🧠 Smart Invest | `smart_invest` | `handle_investment_selection` | Start AI-powered investment recommendation flow. |
| 📈 High APR Pools | `high_apr` | `handle_high_apr_pools` | Display pools with highest yields. |
| ⭐ Top Pools | `top_pools` | `handle_pool_info` | Show most popular liquidity pools. |
| 💼 My Investments | `my_investments` | `handle_my_investments` | Track existing investments and positions. |

### Pool Exploration

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 📊 View All Pools | `pools` | `handle_pool_info` | Display all available liquidity pools. |
| 📈 High APR Pools | `high_apr` | `handle_high_apr_pools` | Show pools with highest yields. |
| 🔍 Search by Token | `token_search` | `handle_token_search` | Find pools containing a specific token. |
| 🔮 View Predictions | `predictions` | `handle_predictions` | Show AI predictions for pool performance. |

### Account & Profile Options

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 💳 Wallet Settings | `wallet_settings` | `handle_wallet_settings` | Manage wallet connections and settings. |
| ⚙️ Update Profile | `update_profile` | `handle_update_profile` | Update investment preferences and profile settings. |
| 🔔 Subscription Settings | `subscription_settings` | `handle_subscription_settings` | Manage notification preferences. |
| 📝 Enter Address Manually | `enter_address` | `handle_callback_query` | Manually enter wallet address. |
| 🔄 Refresh Wallet Data | `refresh_wallet` | `handle_callback_query` | Refresh data from connected wallet. |
| 🎯 Update Risk Profile | `update_risk` | `handle_callback_query` | Update user's risk tolerance setting. |
| ⏱️ Update Investment Horizon | `update_horizon` | `handle_callback_query` | Update user's investment timeframe preference. |
| 🏆 Update Investment Goals | `update_goals` | `handle_callback_query` | Update user's investment goals. |

### Help & FAQ

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 📚 Getting Started | `help_getting_started` | `handle_callback_query` | Show getting started guide. |
| 🔡 Command List | `help_commands` | `handle_callback_query` | Display list of all available commands. |
| ❓ FAQ | `faq` | `handle_faq` | Show frequently asked questions. |

### WalletConnect Actions

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 🔌 Connect Wallet | `walletconnect` | `handle_callback_query` | Start WalletConnect session with QR code. |
| Check Connection | `check_wc_<session_id>` | `handle_callback_query` | Check status of WalletConnect session. |
| Cancel Connection | `cancel_wc_<session_id>` | `handle_callback_query` | Cancel an active WalletConnect session. |

### Token Search

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| SOL | `search_token_SOL` | `handle_callback_query` | Search for pools containing SOL token. |
| USDC | `search_token_USDC` | `handle_callback_query` | Search for pools containing USDC token. |
| ETH | `search_token_ETH` | `handle_callback_query` | Search for pools containing ETH token. |
| USDT | `search_token_USDT` | `handle_callback_query` | Search for pools containing USDT token. |
| BTC | `search_token_BTC` | `handle_callback_query` | Search for pools containing BTC token. |
| BONK | `search_token_BONK` | `handle_callback_query` | Search for pools containing BONK token. |
| 🔍 Custom Token Search | `custom_token_search` | `handle_callback_query` | Search for pools containing any token. |

### Predictions & Analytics

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 📈 Rising Pools | `rising_pools` | `handle_callback_query` | Show pools predicted to increase in value. |
| 📉 Declining Pools | `declining_pools` | `handle_callback_query` | Show pools predicted to decrease in value. |
| 🎯 Most Stable | `stable_pools` | `handle_stable_pools` | Show pools with most stable performance. |

### Notifications & Subscriptions

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 🔔 Enable Notifications | `enable_notifications` | `handle_callback_query` | Subscribe to notifications and updates. |
| 🔕 Disable Notifications | `disable_notifications` | `handle_callback_query` | Unsubscribe from notifications. |
| 📋 Notification Preferences | `notification_preferences` | `handle_callback_query` | Customize notification settings. |

### My Investments

| Button Label | Callback Data | Handler | Description |
|-------------|--------------|---------|-------------|
| 📊 Performance Overview | `investment_performance` | `handle_callback_query` | View investment performance metrics. |
| 📋 Active Positions | `active_positions` | `handle_callback_query` | Show current active investment positions. |
| 📜 Transaction History | `transaction_history` | `handle_callback_query` | Display history of transactions. |

## Pattern-Based Callbacks

The bot also uses several pattern-based callback handlers for dynamic content:

- `pool:<pool_id>`: Display information about a specific pool
- `POOL_PREFIX + <data>`: Various pool-related operations
- `APR_POOLS_PREFIX + <page>`: Pagination for high APR pools list
- `STABLE_POOLS_PREFIX + <page>`: Pagination for stable pools list
- `PROFILE_PREFIX + <action>`: Profile management actions
- `FAQ_PREFIX + <topic>`: Display specific FAQ topic
- `BACK_PREFIX + <destination>`: Navigation to specific pages
- `PAGE_PREFIX + <page_info>`: Pagination control
- `PREFIX_MENU + <menu_type>`: Switch between menu types