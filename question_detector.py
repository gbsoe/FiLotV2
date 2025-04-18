"""
Question detection and predefined answer system for the Telegram bot
"""

import re
import logging
from typing import Optional, Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

def get_predefined_responses() -> Dict[str, str]:
    """
    Return a dictionary of detailed predefined responses with canonical keys.
    """
    return {
        # --- Detailed Product Information ---
        "what is filot": (
            "*FiLot* is a next-generation, AI-powered investment assistant that revolutionizes crypto investing. "
            "Currently in its beta phase, FiLot provides advanced market analysis and real-time insights to help you "
            "identify high-yield liquidity pools and make informed decisions.\n\n"
            "Key features include:\n"
            "• *Real-Time Analytics:* Constantly scans liquidity pools using both historical and live data.\n"
            "• *Automated Recommendations:* Offers tailored suggestions for optimal entry and exit points based on market conditions.\n"
            "• *Risk Management:* Evaluates pool stability and potential impermanent loss to help mitigate risks.\n"
            "• *User-Friendly Interface:* Designed for investors of all levels with intuitive commands and clear insights.\n"
            "• *Seamless Wallet Integration:* Easily connect your wallet to monitor and manage investments.\n\n"
            "Looking ahead, when FiLot fully launches, the platform will enable one-click investments via Telegram or through a dedicated FiLot app—making the process simple and hassle-free.\n\n"
            "With FiLot, you can potentially earn much more than by placing your money in a traditional bank."
        ),

        "what is la token": (
            "*LA!* Token is a community-driven meme coin that forms the cornerstone of the FiLot ecosystem. "
            "Inspired by Singapore's vibrant culture and recognized as a symbol of Asia's financial hub, LA! Token is not only a cryptocurrency—it's a token designed "
            "to unlock exclusive benefits within FiLot. A total of 1 billion tokens will be issued.\n\n"
            "*Key attributes include:*\n"
            "• *Token Supply:* Exactly 1 billion tokens will be issued, all allocated directly to the community with no reserved allocations for founders.\n"
            "• *Utility Integration:* Grants access to premium features, lower fees, and special investment opportunities on FiLot.\n"
            "• *Governance Rights:* Enables token holders to vote on key platform decisions and shape the project's future.\n"
            "• *Built on Solana:* Offers fast, secure, and low-cost transactions along with robust security measures.\n\n"
            "LA! Token empowers its holders and fosters a decentralized, community-first ecosystem while embracing the fun, meme-inspired culture.\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "what are la token's use cases": (
            "LA! Token serves several critical roles within the FiLot ecosystem:\n\n"
            "• *Access to Premium Features:* Unlocks advanced market analytics, investment simulations, and priority access to new liquidity pools.\n"
            "• *Staking and Yield Generation:* Earn rewards by staking your tokens, which also help secure the network.\n"
            "• *Governance Participation:* Vote on platform upgrades and strategic initiatives that determine FiLot's direction.\n"
            "• *Incentive Programs:* Benefit from exclusive promotions, bonus rewards, and loyalty incentives that boost community engagement.\n"
            "• *Collateral Use:* Potentially use LA! Token as collateral in DeFi protocols to unlock further investment opportunities.\n\n"
            "These diverse use cases make LA! Token both an investment asset and a key utility that drives the functionality of the FiLot ecosystem.\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "how can i benefit from la token": (
            "Holding LA! Token offers several benefits on the FiLot platform:\n\n"
            "• *Exclusive Access:* Unlock advanced investment tools and premium analytics available exclusively to token holders.\n"
            "• *Reduced Fees:* Enjoy discounted transaction fees and preferential rates on various platform services.\n"
            "• *Staking Rewards:* Earn passive income through staking programs designed for long-term holders.\n"
            "• *Governance Influence:* Participate in community votes to help steer the platform's development.\n"
            "• *Early Adopter Perks:* Receive bonus incentives and early access to future features as the ecosystem expands.\n\n"
            "Overall, LA! Token provides both immediate value and significant long-term growth potential within the FiLot ecosystem.\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "what makes la token unique": (
            "LA! Token is unique due to its community-driven, meme-inspired approach:\n\n"
            "• *True Community Ownership:* Every token is distributed directly to users, with no reserved allocations for insiders.\n"
            "• *Meme Culture & Symbolism:* Inspired by Singapore's vibrant culture and celebrated as a symbol of Asia's financial hub, it combines fun with financial utility.\n"
            "• *Deep Integration with FiLot:* Unlocks premium features and reduces fees within the FiLot investment assistant.\n"
            "• *Robust Security:* Built on the Solana blockchain with audited smart contracts and enforced liquidity locks to safeguard investments.\n"
            "• *Active Governance:* Empowers holders to participate in decisions that shape the platform's future.\n\n"
            "These elements create a digital asset that is both playful and purposeful, offering high utility and growth potential.\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "tell me about la token's launch": (
            "The launch of LA! Token is one of the most anticipated events in the FiLot ecosystem, officially set for March 31, 2025, on Pump.fun.\n\n"
            "*Key Launch Details:*\n\n"
            "*Launch Platform:* LA! Token will launch on Pump.fun.\n\n"
            "*Launch Timing:* March 31, 2025\n\n"
            "*Token Supply:* A total of 1,000,000,000 LA! Tokens will be issued.\n\n"
            "*Community-First Distribution:* 99% of tokens will be allocated directly to the community, ensuring fairness and broad participation.\n\n"
            "*Platform Integration:* The token launch paves the way for the upcoming release of FiLot's AI-powered tools and real-time analytics, scheduled for the end of Q2 2025.\n\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "when does filot launch": (
            "FiLot is currently in beta mode, providing advanced market analysis and investment insights.\n\n"
            "The full launch—which will introduce a one-click investment feature—will be available soon. This feature will be accessible either via Telegram or through a dedicated FiLot app.\n\n"
            "Stay tuned for official announcements regarding the exact launch date and additional functionalities."
        ),

        "what is the roadmap": (
            "The roadmap for FiLot and LA! Token outlines a dynamic plan focused on continuous innovation and community growth.\n\n"
            "*Key phases include:*\n"
            "• Pre-Launch: Final testing, security audits, and early community-building through beta programs and social media engagement.\n"
            "• *LA! Token Launch (31 March 2025):* Official debut of LA! Token with FiLot's (Beta) advanced features and 99% community distribution (with 1 billion tokens issued).\n"
            "• *Post-Launch Enhancements:* Ongoing updates to refine platform functionality, introduce new investment tools, and expand integration with other DeFi protocols.\n"
            "• *Governance Rollout:* Implementation of community voting mechanisms that allow LA! Token holders to influence strategic decisions.\n"
            "• *Ecosystem Expansion:* Formation of strategic partnerships to broaden the platform's reach and enhance its overall value.\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "security and governance": (
            "Security and governance are fundamental to the FiLot and LA! Token ecosystem.\n\n"
            "• *Security Measures:*\n"
            "   - *Blockchain Reliability:* Built on the Solana blockchain for high performance and robust security.\n"
            "   - *Audited Smart Contracts:* All contracts undergo thorough third-party audits to minimize vulnerabilities.\n"
            "   - *Liquidity Locks:* A portion of the liquidity is securely locked to maintain market stability and protect investors.\n"
            "   - *Continuous Monitoring:* Real-time oversight ensures rapid responses to potential risks.\n\n"
            "• *Governance Framework:*\n"
            "   - *Community Voting:* LA! Token holders can participate in key decisions that shape the platform's future.\n"
            "   - *Transparent Communication:* All proposals and governance decisions are shared openly through official channels.\n"
            "   - *Adaptive Policies:* Governance protocols evolve based on user feedback and emerging market trends.\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        "technical innovation": (
            "FiLot and LA! Token are built on a foundation of technical innovation that bridges advanced AI with robust blockchain technology.\n\n"
            "• *AI-Driven Insights:* Machine learning algorithms analyze real-time data to identify high-yield investment opportunities.\n"
            "• *Automated Investment Strategies:* Simplifies the investment process by executing optimal moves automatically based on market conditions.\n"
            "• *Scalable Infrastructure:* Powered by the Solana blockchain, ensuring fast, secure, and cost-effective transactions as the platform scales.\n"
            "• *Integrated Ecosystem:* Seamlessly combines investment tools, governance mechanisms, and staking rewards into one unified platform."
        ),

        # --- Additional Fundamental Market Concepts ---
        "what is liquidity pool": (
            "A *liquidity pool* is a smart contract that holds funds—often in paired cryptocurrencies—to facilitate trading on decentralized exchanges.\n\n"
            "Key aspects include:\n"
            "• *Decentralized Trading:* Traders swap tokens directly against the pool instead of using a central order book.\n"
            "• *Earning Fees:* Liquidity providers earn a share of the trading fees proportional to their contribution.\n"
            "• *Risk Consideration:* Although liquidity pools can yield high returns, they also carry risks such as impermanent loss.\n\n"
            "By providing liquidity through FiLot, users can potentially earn far more than with traditional savings accounts."
        ),

        "impermanent loss": (
            "*Impermanent loss* (IL) occurs when the value of your deposited tokens changes relative to each other, "
            "resulting in a temporary loss compared to simply holding the tokens.\n\n"
            "Key points:\n"
            "• *Price Divergence:* IL happens when the relative prices of tokens in a pool diverge.\n"
            "• *Temporary Impact:* The loss is 'impermanent' because if prices return to their original levels, the loss is reversed.\n"
            "• *Mitigation Strategies:* FiLot's AI selects stable, high-liquidity pools to help minimize the risk of IL."
        ),

        # --- Basic and Mainstream Market Q&A ---
        "how to use filot": (
            "Using FiLot is straightforward:\n\n"
            "1. Start: Type /start to receive a comprehensive introduction to the platform.\n"
            "2. View Opportunities: Use /info to check real-time market data and discover investment opportunities.\n"
            "3. Simulate Earnings: Run /simulate [amount] to see potential returns based on current market conditions.\n"
            "4. Stay Updated: Subscribe with /subscribe to receive regular updates and insights.\n"
            "5. Ask Questions: Use /ask or simply type your question to get detailed answers about crypto investments and the FiLot platform.\n\n"
            "Note: Currently, FiLot is in beta mode—providing analysis and insights only. When the full platform launches, you will be able to invest with one click, either via Telegram or through the dedicated FiLot app. This means you could potentially earn far more than by placing your money in a traditional bank."
        ),

        "what is defi": (
            "*DeFi* stands for Decentralized Finance. It is a suite of financial services built on blockchain technology that operates without centralized intermediaries like banks.\n\n"
            "Through smart contracts, DeFi platforms allow users to lend, borrow, trade, and earn interest—often achieving returns significantly higher than those offered by traditional finance."
        ),

        "what is crypto": (
            "*Crypto* is short for cryptocurrency—a type of digital or virtual currency that uses cryptography for security.\n\n"
            "Cryptocurrencies operate on decentralized networks like blockchains, ensuring secure, transparent, and efficient transactions without the need for central authorities."
        ),

        "what is blockchain": (
            "*Blockchain* is a distributed ledger technology that records transactions across multiple computers in a secure, transparent, and immutable manner.\n\n"
            "It underpins cryptocurrencies and enables decentralized applications by ensuring that once data is recorded, it cannot be altered retroactively without consensus."
        ),

        "what are tokens": (
            "*Tokens* are digital assets created on a blockchain. They can represent various values or utilities—ranging from serving as a currency to granting access rights, rewards, or governance roles within a decentralized ecosystem."
        ),

        "what is ai": (
            "*AI*, or Artificial Intelligence, is a branch of computer science focused on creating systems capable of performing tasks that typically require human-like intelligence, such as decision-making, pattern recognition, and natural language processing."
        ),

        "how do i start investing": (
            "To start investing in crypto, begin by educating yourself on blockchain technology and market trends. With FiLot, type /start for an introduction, check current opportunities with /info, and simulate potential returns with /simulate. Always invest only what you can afford to lose and conduct thorough research before making any decisions."
        ),

        "how to read crypto charts": (
            "Crypto charts display key metrics such as price movements, trading volume, and market trends. Learning basic technical analysis can help you interpret these charts.\n\n"
            "FiLot simplifies this process by providing clear, real-time insights and analytics, making it easier for beginners to understand the market."
        ),

        "what is trading": (
            "*Trading* involves buying and selling assets with the goal of making a profit from price fluctuations.\n\n"
            "In the volatile crypto market, trading can be risky, but platforms like FiLot help by identifying high-yield liquidity pools and optimizing your investment strategy."
        ),

        "what is apr": (
            "*APR* (Annual Percentage Rate) represents the yearly rate of return on an investment without accounting for compounding.\n\n"
            "Traditional banks typically offer around 0.5% to 2% APR, whereas liquidity pools on FiLot can offer APRs ranging from 10% up to 200% or more.\n\n"
            "For example, a $1,000 investment at a 50% APR might yield approximately $500 in one year (before compounding), which is significantly higher than what a conventional bank deposit would earn."
        ),

        "what is apy": (
            "*APY* (Annual Percentage Yield) takes into account the effects of compounding, providing a more comprehensive view of potential earnings over a year.\n\n"
            "While traditional savings accounts might yield an APY of around 1% to 2%, liquidity pools on FiLot can have APYs ranging from 10% to well over 200%, depending on market conditions and the compounding frequency."
        ),

        "compare bank interest": (
            "Traditional bank interest rates typically range from *0.5%* to *2%* per year. In contrast, crypto liquidity pools—especially those identified by FiLot—can offer APRs between *10%* and *200%+*.\n\n"
            "For example, a *$1,000* deposit at a *1%* bank interest rate would earn about *$10* to *$20* in a year, whereas the same *$1,000* investment in a high-yield liquidity pool on FiLot could yield between *$100* and *$500* or more annually. This stark contrast illustrates the potential for significantly higher returns."
        ),

        "what can i ask": (
            "You can ask a wide range of questions about FiLot and the crypto market. For example, you can inquire about:\n\n"
            "• *FiLot Features:* Questions like 'What is FiLot?' or 'How does FiLot work?' to learn about our AI-powered investment insights.\n"
            "• *LA! Token Details:* Ask 'What is LA! Token?' or 'What are LA! Token's use cases?' to understand its role in our ecosystem and its *1 billion* token supply.\n"
            "• *Liquidity Pools and IL:* Inquire about 'What is a liquidity pool?' or 'What is impermanent loss?' to grasp key DeFi concepts.\n"
            "• *Market Comparisons:* Questions such as 'What is APR?' or 'Compare bank interest rates' to see how crypto returns compare to traditional finance.\n\n"
            "Simply type your question, and I'll provide a clear, detailed answer!\n\n"
            "*Token Contract Address (CA):*\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "*Buy LA! Token:*\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),

        # Add the /start command response to handle if users send "start" as text
        "start": (
            "⚠️ Welcome to the FiLot AI-powered Investment Assistant!\n\n"
            "💡 I help you track real-time crypto earnings and updates—think of me as your AI-powered investment assistant for maximizing your returns through FiLot's liquidity pool optimization and LA! Token.\n\n"
            "💰 Why should you care?\n\n"
            "👈 Banks offer just 0.5%-2% a year, but with FiLot, our AI finds the best liquidity pools where you can earn much more (potentially 10-200%+) depending on market conditions—automatically and safely.\n\n"
            "🤔 How does it work?\n\n"
            "👉 FiLot AI scans the market in real time, predicts the best pools, and helps you invest in one click. No complicated DeFi knowledge needed!\n\n"
            "👆 Want to see your potential earnings?\n"
            "Use /simulate [amount] to calculate your potential earnings (default is $1,000). For example, type /simulate 5000 to see how much you could earn by investing $5,000.\n\n"
            "ℹ What's a liquidity pool?\n\n"
            "💡 It's like a community savings pot where people add their crypto. Every time someone trades using that pool, contributors earn a share of the fees. The more you contribute, the more you earn!\n\n"
            "✅ FiLot Makes It Easy & Safe\n\n"
            "🔢 Stay Updated\n\n"
            "Type /subscribe for automatic updates, /info to see today's best earnings, or /help for more details.\n\n"
            "⏰ Have questions? Just ask me directly or use /ask to get product-related answers.\n\n"
            "⚠️ FiLot is launching soon! Get in early and let AI grow your money smarter than a bank!\n\n"
            "Token Contract Address (CA):\n`Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump`\n\n"
            "Buy LA! Token:\nhttps://pump.fun/coin/Bpz8btet2EVDzjjHZAaqwjTzE5p62H9Sb5RuKVNBpump"
        ),
    }


def get_variations() -> Dict[str, List[str]]:
    """
    Return a dictionary mapping canonical queries to their variations.
    Variations are used to match user input to the appropriate response.
    """
    return {
        "what is filot": [
            "what is filot",
            "explain filot",
            "tell me about filot",
            "what does filot do",
            "fi lot platform",
            "about filot",
            "who is filot"
        ],
        "what is la token": [
            "what is la token",
            "what is la",
            "tell me about la",
            "explain la token",
            "la coin",
            "la",
            "what's la token",
            "la token info"
        ],
        "what are la token's use cases": [
            "what are la token's use cases",
            "la token use cases",
            "what can la token be used for",
            "how is la token used",
            "la token purpose",
            "what is la used for"
        ],
        "how can i benefit from la token": [
            "how can i benefit from la token",
            "benefits of la token",
            "why hold la token",
            "advantages of la token",
            "why buy la token",
            "reasons to own la"
        ],
        "what makes la token unique": [
            "what makes la token unique",
            "unique features of la token",
            "what is special about la token",
            "how is la token different",
            "la token uniqueness",
            "what sets la token apart"
        ],
        "tell me about la token's launch": [
            "tell me about la token's launch",
            "la launch",
            "when la launch",
            "when does la launch",
            "la token launch",
            "launch la token",
            "la token release date"
        ],
        "when does filot launch": [
            "when does filot launch",
            "filot launch",
            "when filot launch",
            "filot launching",
            "fi lot launch",
            "when will filot be available",
            "filot release date"
        ],
        "what is the roadmap": [
            "what is the roadmap",
            "roadmap for filot",
            "fi lot roadmap",
            "what is the future plan",
            "development timeline",
            "future of filot",
            "what's coming next"
        ],
        "security and governance": [
            "security and governance",
            "how secure is la token",
            "governance of filot",
            "security measures",
            "how is la token secured",
            "token security",
            "governance structure"
        ],
        "technical innovation": [
            "technical innovation",
            "what are the innovations",
            "technological features of filot",
            "tech behind filot",
            "filot technology",
            "technical features"
        ],
        "how to use filot": [
            "how to use filot",
            "how do i use filot",
            "using filot",
            "filot usage instructions",
            "getting started with filot",
            "filot tutorial"
        ],
        "what is defi": [
            "what is defi",
            "define defi",
            "what does defi mean",
            "explain defi",
            "definition of defi",
            "defi explained"
        ],
        "what is crypto": [
            "what is crypto",
            "explain crypto",
            "what does crypto mean",
            "cryptocurrency explained",
            "definition of cryptocurrency",
            "what are cryptocurrencies"
        ],
        "what is blockchain": [
            "what is blockchain",
            "explain blockchain",
            "what does blockchain mean",
            "blockchain technology",
            "how does blockchain work",
            "blockchain explained"
        ],
        "what are tokens": [
            "what are tokens",
            "explain tokens",
            "what is a token",
            "crypto tokens",
            "digital tokens",
            "tokens explained"
        ],
        "what is ai": [
            "what is ai",
            "explain ai",
            "what does ai mean",
            "artificial intelligence",
            "ai explained",
            "how does ai work"
        ],
        "how do i start investing": [
            "how do i start investing",
            "how to start investing",
            "investment basics",
            "crypto investing start",
            "begin investing",
            "first steps in investing"
        ],
        "how to read crypto charts": [
            "how to read crypto charts",
            "reading crypto charts",
            "understanding crypto charts",
            "crypto chart analysis",
            "interpret crypto charts",
            "crypto technical analysis"
        ],
        "what is trading": [
            "what is trading",
            "explain trading",
            "what does trading mean",
            "how to trade crypto",
            "crypto trading",
            "trading explained"
        ],
        "what is apr": [
            "what is apr",
            "explain apr",
            "annual percentage rate",
            "apr meaning",
            "apr crypto",
            "apr explained"
        ],
        "what is apy": [
            "what is apy",
            "explain apy",
            "annual percentage yield",
            "apy meaning",
            "apy crypto",
            "apy vs apr"
        ],
        "compare bank interest": [
            "compare bank interest",
            "bank interest rates vs crypto",
            "traditional bank interest comparison",
            "crypto vs bank rates",
            "interest rate comparison",
            "bank vs defi interest"
        ],
        "what can i ask": [
            "what can i ask",
            "what questions can i ask",
            "what should i ask",
            "help me ask",
            "what topics can i ask about",
            "what can you answer"
        ],
        "what is liquidity pool": [
            "what is liquidity pool",
            "explain liquidity pool",
            "liquidity pool meaning",
            "how do liquidity pools work",
            "lp in crypto",
            "defi pools"
        ],
        "impermanent loss": [
            "impermanent loss",
            "what is impermanent loss",
            "explain impermanent loss",
            "il in crypto",
            "prevent impermanent loss",
            "how does impermanent loss work"
        ],
        "start": [
            "start",
            "let's start",
            "begin",
            "get started",
            "hello",
            "hi",
            "hey"
        ],
    }


def is_question(text: str) -> bool:
    """
    Determine if text is likely a question based on various patterns.
    
    Args:
        text: The message text to analyze
        
    Returns:
        True if the text is likely a question, False otherwise
    """
    # Clean the text
    text = text.strip().lower()
    
    # Empty text is not a question
    if not text:
        return False
    
    # Check if ends with a question mark
    if text.endswith('?'):
        return True
    
    # Check for question words at the beginning
    question_starters = ['what', 'how', 'why', 'when', 'where', 'which', 'who', 'is', 'are', 'can', 
                          'could', 'will', 'would', 'should', 'do', 'does', 'did', 'tell me about']
    
    for starter in question_starters:
        if text.startswith(starter + ' '):
            return True
            
    # Check for inverted question structure
    inverted_patterns = [
        r'(is|are|was|were|do|does|did|have|has|had|can|could|should|would|will) ([\w\s]+)\?*$',
        r'(is|are|was|were|do|does|did|have|has|had|can|could|should|would|will) (it|there|they|he|she|we|you|i) ([\w\s]+)\?*$'
    ]
    
    for pattern in inverted_patterns:
        if re.match(pattern, text):
            return True
    
    # Check for additional question patterns
    question_expressions = [
        "explain", "tell me about", "what about", "i want to know", "can you", "i need info", 
        "information on", "details about", "describe", "elaborate on", "need help with"
    ]
    
    for expression in question_expressions:
        if expression in text:
            return True
    
    return False


def get_predefined_response(query: str) -> Optional[str]:
    """
    Retrieve a predefined response based on the user's query using enhanced matching.
    The matching logic checks for direct keys, variations, and keyword combinations.
    
    Args:
        query: User's message text
        
    Returns:
        Predefined response or None if no match is found
    """
    if not query:
        return None
        
    # Clean the query
    query_lower = query.lower().strip("?!.,")
    
    # Get responses and variations
    responses = get_predefined_responses()
    variations = get_variations()
    
    # Check if it's likely a question
    if not is_question(query) and not any(keyword in query_lower for keyword in ['hi', 'hello', 'hey', 'start']):
        # If it doesn't seem like a question and doesn't contain greeting keywords, skip matching
        logger.debug(f"Message '{query_lower}' doesn't seem like a question, skipping predefined matching")
        return None
    
    # Log that we're processing a potential question
    logger.info(f"Processing potential question: '{query_lower}'")
    
    # Check for single-word queries using key terms
    key_terms = {
        'la': 'what is la token',
        'filot': 'what is filot',
        'token': 'what is la token',
        'roadmap': 'what is the roadmap',
    }
    if query_lower in key_terms:
        logger.info(f"Matched key term: {query_lower} → {key_terms[query_lower]}")
        return responses.get(key_terms[query_lower])
    
    # Check for exact matches
    if query_lower in responses:
        logger.info(f"Matched exact query: {query_lower}")
        return responses[query_lower]
    
    # Check in variations (exact match or substring match)
    for canonical, variant_list in variations.items():
        if query_lower in variant_list:
            logger.info(f"Matched variation: {query_lower} → {canonical}")
            return responses.get(canonical)
        
        # Look for substring matches
        for variant in variant_list:
            if variant in query_lower:
                logger.info(f"Matched substring: '{variant}' in '{query_lower}' → {canonical}")
                return responses.get(canonical)
    
    # Check for keyword combinations
    keyword_combinations = {
        ('how', 'start'): 'how to use filot',
        ('what', 'pool'): 'what is liquidity pool',
        ('what', 'apr'): 'what is apr',
        ('impermanent', 'loss'): 'impermanent loss',
        ('who', 'you'): 'what is filot',
        ('what', 'ask'): 'what can i ask',
        ('apy', 'mean'): 'what is apy',
        ('bank', 'interest'): 'compare bank interest',
        ('difference', 'apr', 'apy'): 'what is apy'
    }
    for keywords, response_key in keyword_combinations.items():
        if all(keyword in query_lower for keyword in keywords):
            logger.info(f"Matched keyword combination: {keywords} → {response_key}")
            return responses.get(response_key)
    
    # Semantic matching for more complex questions
    # This section tries to match questions that might be phrased differently
    # but are looking for the same information
    
    # Topics and their related keywords
    topics = {
        "what is filot": ["platform", "service", "purpose", "about", "project", "tool", "app", "application"],
        "what is la token": ["cryptocurrency", "coin", "utility", "token", "tokenomics"],
        "what is the roadmap": ["plan", "timeline", "future", "development", "coming", "next"],
        "how to use filot": ["instructions", "guide", "manual", "tutorial", "user", "help", "use"],
        "what is liquidity pool": ["provide liquidity", "lp", "pooling", "amm", "pool"],
        "impermanent loss": ["risk", "loss", "divergence", "price change"],
        "what is apr": ["interest", "return", "yield", "earn", "profit", "reward"],
        "compare bank interest": ["savings", "traditional", "bank", "investment", "return"]
    }
    
    for topic, keywords in topics.items():
        if any(keyword in query_lower for keyword in keywords):
            topic_words = set(topic.split())
            query_words = set(query_lower.split())
            # If query contains at least one topic word and one keyword
            if topic_words.intersection(query_words) and any(keyword in query_lower for keyword in keywords):
                logger.info(f"Matched semantic topic: {topic} with keywords {[k for k in keywords if k in query_lower]}")
                return responses.get(topic)
    
    # No match found
    logger.info(f"No predefined response match for: {query_lower}")
    return None


# For testing purposes
if __name__ == "__main__":
    # Configure basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Test questions
    test_questions = [
        "What is FiLot?",
        "Tell me about LA!",
        "How do I start investing?",
        "Explain impermanent loss",
        "What's the difference between APR and APY?",
        "How much can I earn compared to a bank?",
        "Is LA token on Solana?",
        "What's the contract address for LA?",
        "When does the project launch?",
        "Help me understand liquidity pools",
        "Who created FiLot?",
        "I want to know more about LA token",
        "Hi there",
        "This is not a question just a statement",
        "Just random words without any meaning"
    ]
    
    for q in test_questions:
        print(f"\nQuery: {q}")
        response = get_predefined_response(q)
        print(f"Is question: {is_question(q)}")
        if response:
            print(f"Response: {response[:100]}... (truncated)")
        else:
            print("No predefined response found")
        print("-" * 50)