"""
Fallback responses for button commands when database is unavailable
"""

def get_faq_responses():
    """
    Return predefined responses for FAQ sections when database access is unavailable
    """
    return {
        "about_liquidity_pools": (
            "*Liquidity Pools Explained*\n\n"
            "A liquidity pool is a collection of funds locked in a smart contract that facilitates trading on decentralized exchanges.\n\n"
            "Key features:\n"
            "• Allows for automated trading without traditional order books\n"
            "• Creates market liquidity for token pairs\n"
            "• Generates fees for liquidity providers\n"
            "• Enables opportunities for passive income\n\n"
            "When you provide liquidity, you deposit equal values of two tokens. In return, you receive LP tokens representing your share of the pool, and earn fees from trades."
        ),
        
        "about_apr": (
            "*Understanding APR in Crypto*\n\n"
            "APR (Annual Percentage Rate) represents the yearly return on your investment in a liquidity pool.\n\n"
            "Important aspects:\n"
            "• Calculated based on trading fees and token rewards\n"
            "• Typically higher than traditional finance returns\n"
            "• Fluctuates based on trading volume and market conditions\n"
            "• Does not account for compounding (unlike APY)\n\n"
            "For example, a 50% APR means your investment would theoretically increase by 50% over a year if rates remained constant."
        ),
        
        "about_impermanent_loss": (
            "*Impermanent Loss Explained*\n\n"
            "Impermanent loss occurs when the price ratio of tokens in a liquidity pool changes compared to when you deposited them.\n\n"
            "Key points:\n"
            "• Happens when one token's price changes significantly relative to the other\n"
            "• Called 'impermanent' because it can reverse if prices return to original ratio\n"
            "• Becomes permanent only when you withdraw your funds\n"
            "• Often offset by trading fees and rewards\n\n"
            "Higher volatility between paired tokens typically leads to greater impermanent loss risk."
        ),
        
        "about_defi": (
            "*DeFi (Decentralized Finance) Overview*\n\n"
            "DeFi refers to financial services built on blockchain technology that operate without central authorities.\n\n"
            "Key components:\n"
            "• Lending and borrowing platforms\n"
            "• Decentralized exchanges (DEXs)\n"
            "• Yield farming opportunities\n"
            "• Automated market makers (AMMs)\n"
            "• Staking and liquidity provision\n\n"
            "DeFi aims to create an open, permissionless financial system accessible to anyone with an internet connection and a crypto wallet."
        ),
        
        "about_tokens": (
            "*Cryptocurrency Tokens Explained*\n\n"
            "Tokens are digital assets built on existing blockchain platforms, unlike coins which have their own blockchains.\n\n"
            "Token types:\n"
            "• Utility tokens: Provide access to a product or service\n"
            "• Security tokens: Represent ownership in an asset\n"
            "• Governance tokens: Allow voting on protocol decisions\n"
            "• Stablecoins: Pegged to maintain consistent value\n\n"
            "For liquidity pools, tokens are typically paired together to create trading pairs that users can swap between."
        ),
        
        "about_wallets": (
            "*Crypto Wallets Explained*\n\n"
            "Crypto wallets are applications that store your private keys, allowing you to interact with blockchains.\n\n"
            "Popular wallet types:\n"
            "• Hardware wallets: Physical devices offering highest security (Ledger, Trezor)\n"
            "• Software wallets: Desktop/mobile apps for convenience (Phantom, Solflare)\n"
            "• Web wallets: Browser-based access (Phantom extension)\n"
            "• Paper wallets: Offline storage method\n\n"
            "FiLot integrates with wallets via WalletConnect protocol for secure, non-custodial control of your assets."
        ),
        
        "about_risks": (
            "*Understanding DeFi Risks*\n\n"
            "DeFi investments come with several important risk factors:\n\n"
            "• Smart contract vulnerabilities\n"
            "• Impermanent loss in liquidity pools\n"
            "• Market volatility and price risk\n"
            "• Protocol governance changes\n"
            "• Regulatory uncertainty\n"
            "• Liquidation risk in lending protocols\n\n"
            "FiLot helps mitigate these risks through careful analysis and monitoring, but all crypto investments contain inherent risk. Always invest responsibly."
        )
    }

def get_commands_list():
    """
    Return a formatted list of available commands
    """
    return (
        "*Available Commands*\n\n"
        "/start - Initialize the bot and see the welcome message\n"
        "/help - Display this help message with all available commands\n"
        "/info - View information about top-performing liquidity pools\n"
        "/simulate [amount] - Simulate investment returns (e.g., /simulate 1000)\n"
        "/wallet [address] - Connect your wallet address for monitoring\n"
        "/walletconnect - Connect via WalletConnect protocol\n"
        "/profile - Set your investment preferences and risk profile\n"
        "/subscribe - Subscribe to daily updates and alerts\n"
        "/unsubscribe - Unsubscribe from updates\n"
        "/status - Check the current status of your investments\n"
        "/faq - View frequently asked questions\n"
        "/contact - Get contact information for support\n"
        "/feedback - Send feedback about the bot\n\n"
        "You can also use the menu buttons below for easy navigation."
    )

def get_contact_info():
    """
    Return contact information
    """
    return (
        "*Contact Information*\n\n"
        "For support or inquiries, please reach out through one of these channels:\n\n"
        "• *Telegram Group*: @FiLotCommunity\n"
        "• *Twitter*: @FiLot_Official\n"
        "• *Email*: support@filot.io\n"
        "• *Discord*: discord.gg/filot\n\n"
        "Our support team typically responds within 24 hours. For urgent matters, please use Telegram for fastest assistance."
    )

def get_links_info():
    """
    Return useful links
    """
    return (
        "*Useful Links*\n\n"
        "• *Official Website*: https://filot.io\n"
        "• *Documentation*: https://docs.filot.io\n"
        "• *Blog*: https://blog.filot.io\n"
        "• *GitHub*: https://github.com/filot-project\n"
        "• *Twitter*: https://twitter.com/FiLot_Official\n"
        "• *Telegram Group*: https://t.me/FiLotCommunity\n"
        "• *Discord*: https://discord.gg/filot\n\n"
        "For the latest updates and announcements, follow us on Twitter and join our Telegram group."
    )

def get_investment_options():
    """
    Return investment options
    """
    return (
        "*Investment Options*\n\n"
        "FiLot offers various investment opportunities tailored to your preferences:\n\n"
        "• *Smart Invest*: AI-powered investment recommendations based on your risk profile\n"
        "• *Top Pools*: View and invest in the highest-performing liquidity pools\n"
        "• *Stable Pools*: Lower-risk options focusing on stablecoin pairs\n"
        "• *Custom Strategy*: Create personalized investment strategies\n\n"
        "Use the buttons below to explore these options. For personalized recommendations, make sure to set up your risk profile using the /profile command."
    )

def get_my_investments():
    """
    Return my investments info
    """
    return (
        "*Your Investment Portfolio*\n\n"
        "To view your active investments, please connect your wallet using the /wallet or /walletconnect commands.\n\n"
        "Once connected, you'll be able to see:\n"
        "• Your current portfolio value\n"
        "• Active liquidity positions\n"
        "• Historical performance\n"
        "• Earned fees and rewards\n"
        "• Recommended adjustments\n\n"
        "FiLot uses read-only access to your wallet to provide these insights while keeping your funds secure."
    )

def get_subscription_settings():
    """
    Return subscription settings info
    """
    return (
        "*Subscription Settings*\n\n"
        "Manage your notification preferences:\n\n"
        "• *Daily Updates*: Receive a daily summary of your portfolio performance\n"
        "• *Price Alerts*: Get notified when tokens reach your target prices\n"
        "• *APR Changes*: Be informed when pool APRs significantly change\n"
        "• *Security Alerts*: Receive notifications about important security updates\n\n"
        "Use /subscribe to enable notifications and /unsubscribe to disable them. You can customize your preferences by replying with specific options after subscribing."
    )

def handle_button_command(command):
    """
    Process button commands and return appropriate responses when database is unavailable
    
    Args:
        command: The command to process
        
    Returns:
        Response text for the command
    """
    # FAQ responses
    faq_responses = get_faq_responses()
    
    # Map button commands to responses
    button_map = {
        "about_liquidity_pools": faq_responses.get("about_liquidity_pools"),
        "about_apr": faq_responses.get("about_apr"),
        "about_impermanent_loss": faq_responses.get("about_impermanent_loss"),
        "about_defi": faq_responses.get("about_defi"),
        "about_tokens": faq_responses.get("about_tokens"),
        "about_wallets": faq_responses.get("about_wallets"),
        "about_risks": faq_responses.get("about_risks"),
        "commands": get_commands_list(),
        "contact": get_contact_info(),
        "links": get_links_info(),
        "investment_options": get_investment_options(),
        "my_investments": get_my_investments(),
        "subscription_settings": get_subscription_settings()
    }
    
    # Return the response for the command, or a fallback message
    return button_map.get(command, "Sorry, that feature is currently unavailable. Please try again later.")