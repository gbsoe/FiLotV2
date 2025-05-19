#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Menu system for FiLot Telegram bot
Defines the structure and configuration for the One-Command interface with persistent buttons
"""

from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum


class MenuType(Enum):
    """Enum representing different types of menus in the bot"""
    MAIN = "main"
    EXPLORE = "explore"
    ACCOUNT = "account"
    INVEST = "invest"
    SETTINGS = "settings"
    HELP = "help"
    POOL_INFO = "pool_info"
    WALLET = "wallet"
    SIMULATE = "simulate"
    FAQ = "faq"
    PROFILE = "profile"
    SUBSCRIBE = "subscribe"
    BACK = "back"


class MenuConfig:
    """Configuration for a menu in the bot"""
    
    def __init__(
        self,
        menu_type: MenuType,
        title: str,
        buttons: List[List[str]],
        help_text: str,
        parent_menu: Optional['MenuType'] = None,
        callback_data: Optional[Dict[str, str]] = None,
        requires_auth: bool = False,
        requires_wallet: bool = False
    ):
        """
        Initialize a menu configuration.
        
        Args:
            menu_type: Type of the menu
            title: Title text to display at the top of the menu
            buttons: List of button rows, each row being a list of button labels
            help_text: Help text to show with the menu
            parent_menu: Parent menu to go back to (if any)
            callback_data: Optional custom callback data for buttons
            requires_auth: Whether this menu requires user authentication
            requires_wallet: Whether this menu requires a connected wallet
        """
        self.menu_type = menu_type
        self.title = title
        self.buttons = buttons
        self.help_text = help_text
        self.parent_menu = parent_menu
        self.callback_data = callback_data or {}
        self.requires_auth = requires_auth
        self.requires_wallet = requires_wallet


# Define the menu structure
MENUS: Dict[MenuType, MenuConfig] = {
    # Main menu - entry point
    MenuType.MAIN: MenuConfig(
        menu_type=MenuType.MAIN,
        title="🚀 FiLot - Main Menu",
        buttons=[
            ["💰 Explore Pools", "👤 My Account"],
            ["💹 Invest", "ℹ️ Help"]
        ],
        help_text="Welcome to FiLot! Use the buttons below to navigate."
    ),
    
    # Explore menu - for exploring pools and information
    MenuType.EXPLORE: MenuConfig(
        menu_type=MenuType.EXPLORE,
        title="💰 Explore Pools",
        buttons=[
            ["📊 Pool Information", "🔮 Simulate Investment"],
            ["❓ FAQ", "⬅️ Back to Main Menu"]
        ],
        help_text="Explore liquidity pools and learn more about investments.",
        parent_menu=MenuType.MAIN
    ),
    
    # Account menu - for user account management
    MenuType.ACCOUNT: MenuConfig(
        menu_type=MenuType.ACCOUNT,
        title="👤 My Account",
        buttons=[
            ["👛 Wallet", "📋 Profile"],
            ["🔔 Subscriptions", "⬅️ Back to Main Menu"]
        ],
        help_text="Manage your account settings and wallet connection.",
        parent_menu=MenuType.MAIN
    ),
    
    # Invest menu - for investment options
    MenuType.INVEST: MenuConfig(
        menu_type=MenuType.INVEST,
        title="💹 Investment Options",
        buttons=[
            ["🧠 Smart Invest", "⭐ Top Pools"],
            ["💼 My Investments", "⬅️ Back to Main Menu"]
        ],
        help_text="Discover investment opportunities and manage your portfolio.",
        parent_menu=MenuType.MAIN,
        requires_wallet=True
    ),
    
    # Help menu - for assistance
    MenuType.HELP: MenuConfig(
        menu_type=MenuType.HELP,
        title="ℹ️ Help & Support",
        buttons=[
            ["📚 Commands", "📱 Contact"],
            ["🔗 Links", "⬅️ Back to Main Menu"]
        ],
        help_text="Get help with using the bot and find resources.",
        parent_menu=MenuType.MAIN
    ),
    
    # Pool info menu - for detailed pool information
    MenuType.POOL_INFO: MenuConfig(
        menu_type=MenuType.POOL_INFO,
        title="📊 Pool Information",
        buttons=[
            ["📈 High APR Pools", "💵 Stable Pools"],
            ["🔍 Search Pool", "📊 All Pools"],
            ["⬅️ Back to Explore"]
        ],
        help_text="View detailed information about liquidity pools. Select a category or search for specific pools.",
        parent_menu=MenuType.EXPLORE
    ),
    
    # Wallet menu - for wallet management
    MenuType.WALLET: MenuConfig(
        menu_type=MenuType.WALLET,
        title="👛 Wallet Management",
        buttons=[
            ["🔌 Connect Wallet", "💰 Check Balance"],
            ["📝 Transactions", "⬅️ Back to Account"]
        ],
        help_text="Connect and manage your cryptocurrency wallet.",
        parent_menu=MenuType.ACCOUNT
    ),
    
    # Simulate menu - for investment simulation
    MenuType.SIMULATE: MenuConfig(
        menu_type=MenuType.SIMULATE,
        title="🔮 Investment Simulation",
        buttons=[
            ["💲 Quick Simulate", "📊 Custom Simulation"],
            ["📑 Simulation History", "⬅️ Back to Explore"]
        ],
        help_text="Simulate potential returns on different investment scenarios.",
        parent_menu=MenuType.EXPLORE
    ),
    
    # FAQ menu - for frequently asked questions
    MenuType.FAQ: MenuConfig(
        menu_type=MenuType.FAQ,
        title="❓ Frequently Asked Questions",
        buttons=[
            ["💡 About Liquidity Pools", "💱 About APR"],
            ["🛡️ About Risks", "⬅️ Back to Explore"]
        ],
        help_text="Find answers to common questions about crypto investments.",
        parent_menu=MenuType.EXPLORE
    ),
    
    # Profile menu - for user profile management
    MenuType.PROFILE: MenuConfig(
        menu_type=MenuType.PROFILE,
        title="📋 Investment Profile",
        buttons=[
            ["🎯 Risk Tolerance", "⏱️ Investment Horizon"],
            ["🎲 Investment Goals", "⬅️ Back to Account"]
        ],
        help_text="Configure your investment preferences and risk profile.",
        parent_menu=MenuType.ACCOUNT
    ),
    
    # Subscribe menu - for notification management
    MenuType.SUBSCRIBE: MenuConfig(
        menu_type=MenuType.SUBSCRIBE,
        title="🔔 Subscription Settings",
        buttons=[
            ["📊 Daily Updates", "🚨 Price Alerts"],
            ["📈 Performance Reports", "⬅️ Back to Account"]
        ],
        help_text="Manage your notification preferences and subscriptions.",
        parent_menu=MenuType.ACCOUNT
    )
}


def get_menu_config(menu_type: MenuType) -> MenuConfig:
    """
    Get a menu configuration by its type.
    
    Args:
        menu_type: The type of menu to retrieve
        
    Returns:
        MenuConfig object for the specified menu type
    
    Raises:
        KeyError: If the menu type is not found
    """
    return MENUS[menu_type]


def get_menu_by_button_text(button_text: str) -> Optional[MenuType]:
    """
    Find a menu type based on button text.
    
    Args:
        button_text: The button text to search for
        
    Returns:
        Corresponding MenuType or None if not found
    """
    button_text = button_text.strip()
    button_to_menu = {
        "💰 Explore Pools": MenuType.EXPLORE,
        "👤 My Account": MenuType.ACCOUNT,
        "💹 Invest": MenuType.INVEST,
        "ℹ️ Help": MenuType.HELP,
        "📊 Pool Information": MenuType.POOL_INFO,
        "🔮 Simulate Investment": MenuType.SIMULATE,
        "❓ FAQ": MenuType.FAQ,
        "👛 Wallet": MenuType.WALLET,
        "📋 Profile": MenuType.PROFILE,
        "🔔 Subscriptions": MenuType.SUBSCRIBE,
    }
    
    # Handle "Back to X" buttons
    if button_text.startswith("⬅️ Back to"):
        for menu_type, config in MENUS.items():
            back_text = f"⬅️ Back to {config.title.split('-')[0].strip()}"
            if button_text == back_text:
                return menu_type
        
        # Generic back button handling
        if "Main Menu" in button_text:
            return MenuType.MAIN
        
    return button_to_menu.get(button_text)