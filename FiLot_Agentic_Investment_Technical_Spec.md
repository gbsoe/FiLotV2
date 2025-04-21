# FiLot Agentic Investment System
## Technical Specification Document

## Overview
This document outlines the technical architecture and implementation details for developing FiLot's core agentic investment system. This system will enable the bot to make autonomous investment decisions based on user preferences and execute transactions with varying levels of user involvement.

## System Architecture

### 1. Core Components

#### 1.1 Data Collection Layer
- **Real-time Pool Data**
  - Raydium API integration (existing)
  - Backup data sources for redundancy
  - Caching system with configurable TTL (Time To Live)
  - Data validation and sanitization

- **Market Sentiment Analysis**
  - Integration with news aggregators
  - Social media sentiment tracking
  - Protocol-specific development activity metrics
  - Whale wallet movement monitoring

- **Token Analytics**
  - Historical price data
  - Volatility metrics
  - Correlation with major assets
  - Liquidity depth analysis

#### 1.2 Analysis Layer
- **Risk Assessment Engine**
  - Pool stability scoring algorithm
  - Impermanent loss prediction model
  - Smart contract risk evaluation
  - Protocol risk assessment

- **Performance Prediction**
  - APR forecasting models
  - Volume prediction
  - Price movement estimation
  - Fee generation projections

- **Strategy Formulation**
  - Investment timing optimization
  - Position sizing recommendations
  - Entry/exit strategy development
  - Diversification planning

#### 1.3 Decision Layer
- **User Profile Matching**
  - Risk tolerance mapping
  - Investment horizon alignment
  - Goal-based filtering
  - Preference learning

- **Recommendation Generation**
  - Multi-criteria ranking algorithm
  - Explanation generation
  - Alternative options development
  - Risk-adjusted return optimization

- **Automation Rules Engine**
  - Conditional logic processor
  - Trigger event monitoring
  - Action execution planning
  - Safety circuit breakers

#### 1.4 Execution Layer
- **Wallet Integration**
  - WalletConnect v2 implementation
  - Direct RPC connection fallback
  - Multi-wallet support
  - Address validation and security

- **Transaction Management**
  - Transaction preparation
  - Gas optimization
  - Signature request handling
  - Transaction monitoring

- **Security Controls**
  - Transaction limits
  - Approval workflows
  - Suspicious transaction detection
  - Emergency stop capabilities

### 2. User Interaction Flow

#### 2.1 Investment Profile Setup
1. User provides risk tolerance (conservative, moderate, aggressive)
2. User specifies investment horizon (short, medium, long-term)
3. User sets investment goals (growth, income, balanced)
4. User defines automation preferences (manual, semi-automatic, automatic)
5. System stores and confirms profile settings

#### 2.2 Investment Recommendation Flow
1. User requests investment options or system detects opportunity
2. System gathers latest pool data and market conditions
3. AI models analyze options based on user profile
4. System ranks potential investments by suitability
5. Recommendations presented with clear rationale
6. User reviews and selects preferred option

#### 2.3 Transaction Execution Flow
1. System prepares transaction details based on selection
2. User receives transaction summary for approval
3. System requests wallet signature via WalletConnect
4. Transaction submitted to blockchain
5. System monitors transaction status
6. User notified of completion or failure
7. Transaction details stored in history

#### 2.4 Automated Investment Flow
1. User sets automation parameters (e.g., "Invest $100 weekly in top-performing stable pools")
2. System schedules regular evaluation of investment targets
3. AI selects optimal investment based on current conditions and user profile
4. System prepares conditional transaction
5. Based on user's automation level:
   - Full Auto: Execute directly (with limits)
   - Semi-Auto: Request approval then execute
   - Manual: Send recommendation for manual execution
6. System logs actions and provides reports

### 3. AI Decision Models

#### 3.1 Pool Ranking Model
- **Inputs**:
  - Pool TVL, volume, and APR data
  - Token price stability metrics
  - Smart contract security assessment
  - User's risk profile
  - Historical performance

- **Processing**:
  - Feature normalization
  - Multi-criteria weighted scoring
  - Risk-adjustment calculations
  - Profile matching algorithm

- **Outputs**:
  - Ranked list of suitable pools
  - Confidence score for each recommendation
  - Risk assessment for each option
  - Expected return projections

#### 3.2 Investment Timing Model
- **Inputs**:
  - Market volatility indicators
  - Historical APR patterns
  - Gas price trends
  - Pool activity metrics
  - User's investment horizon

- **Processing**:
  - Pattern recognition algorithms
  - Seasonal adjustment
  - Trend analysis
  - Opportunity cost calculation

- **Outputs**:
  - Optimal investment timing recommendations
  - Confidence intervals
  - Alternative timing suggestions
  - Reasoning explanation

#### 3.3 Position Sizing Model
- **Inputs**:
  - User's total investment capacity
  - Risk tolerance profile
  - Pool liquidity depth
  - Diversification goals
  - Expected return variance

- **Processing**:
  - Kelly criterion adaptation
  - Modern portfolio theory application
  - Monte Carlo simulations
  - Downside risk assessment

- **Outputs**:
  - Recommended position sizes
  - Diversification strategy
  - Maximum exposure limits
  - Expected portfolio performance

#### 3.4 Autonomous Agent
- **Inputs**:
  - User-defined rules and preferences
  - Market conditions and triggers
  - Portfolio performance metrics
  - Risk parameters and limits

- **Processing**:
  - Rule evaluation engine
  - Decision tree navigation
  - Safety check verification
  - User authorization level checking

- **Outputs**:
  - Investment actions (with appropriate approvals)
  - Strategy adjustments
  - Alert notifications
  - Performance reports

## Technical Implementation

### 1. Database Schema Updates

```sql
-- New tables for the agentic investment system

-- Automation rules table
CREATE TABLE automation_rules (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- e.g., "periodic", "threshold", "rebalance"
    trigger_conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    max_transaction_amount NUMERIC(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_executed_at TIMESTAMP,
    execution_count INTEGER DEFAULT 0
);

-- Transaction history table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    transaction_hash VARCHAR(255),
    pool_id VARCHAR(255) REFERENCES pools(id),
    transaction_type VARCHAR(50) NOT NULL,  -- e.g., "invest", "withdraw", "claim"
    amount NUMERIC(20, 8) NOT NULL,
    token_symbol VARCHAR(10) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- e.g., "pending", "completed", "failed"
    gas_used NUMERIC(20, 8),
    execution_price NUMERIC(20, 8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    automation_rule_id INTEGER REFERENCES automation_rules(id),
    error_message TEXT
);

-- User portfolio table
CREATE TABLE user_portfolio (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    pool_id VARCHAR(255) REFERENCES pools(id),
    token_a_amount NUMERIC(20, 8) NOT NULL,
    token_b_amount NUMERIC(20, 8) NOT NULL,
    initial_value_usd NUMERIC(20, 2) NOT NULL,
    current_value_usd NUMERIC(20, 2),
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fees_earned_usd NUMERIC(20, 2) DEFAULT 0,
    impermanent_loss_usd NUMERIC(20, 2) DEFAULT 0
);

-- Investment recommendations table
CREATE TABLE investment_recommendations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    recommendation_type VARCHAR(50) NOT NULL,  -- e.g., "new", "rebalance", "exit"
    pool_id VARCHAR(255) REFERENCES pools(id),
    reasoning TEXT NOT NULL,
    confidence_score FLOAT,
    recommended_amount NUMERIC(20, 2),
    expected_apr FLOAT,
    risk_score INTEGER,  -- 1-10 scale
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_executed BOOLEAN DEFAULT false,
    transaction_id INTEGER REFERENCES transactions(id)
);

-- AI model performance tracking
CREATE TABLE model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    prediction_type VARCHAR(50) NOT NULL,  -- e.g., "apr", "risk", "timing"
    predicted_value NUMERIC(20, 8) NOT NULL,
    actual_value NUMERIC(20, 8),
    prediction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluation_time TIMESTAMP,
    accuracy_metric FLOAT,
    context_data JSONB
);
```

### 2. Key Python Modules

#### 2.1 Investment Agent Module
```python
# investment_agent.py
class InvestmentAgent:
    """Main agent responsible for autonomous investment decisions."""
    
    def __init__(self, user_id, risk_profile='moderate', 
                 investment_horizon='medium', automation_level='semi'):
        self.user_id = user_id
        self.risk_profile = risk_profile
        self.investment_horizon = investment_horizon
        self.automation_level = automation_level
        self.models = self._initialize_models()
        
    def _initialize_models(self):
        """Initialize the AI models needed for decision making."""
        return {
            'pool_ranking': PoolRankingModel(),
            'timing': InvestmentTimingModel(),
            'position_sizing': PositionSizingModel()
        }
        
    async def get_recommendations(self, amount=None, token_preference=None):
        """Generate investment recommendations based on user profile."""
        # Fetch latest pool data
        pools = await get_pool_data()
        
        # Get user's portfolio for context
        portfolio = await get_user_portfolio(self.user_id)
        
        # Rank pools according to user profile
        ranked_pools = await self.models['pool_ranking'].rank_pools(
            pools=pools,
            risk_profile=self.risk_profile,
            investment_horizon=self.investment_horizon,
            portfolio=portfolio,
            token_preference=token_preference
        )
        
        # Determine optimal position sizes
        sized_recommendations = await self.models['position_sizing'].calculate_positions(
            ranked_pools=ranked_pools,
            total_amount=amount,
            risk_profile=self.risk_profile,
            portfolio=portfolio
        )
        
        # Assess timing factors
        timed_recommendations = await self.models['timing'].optimize_timing(
            recommendations=sized_recommendations,
            market_conditions=await get_market_conditions()
        )
        
        # Save recommendations to database
        saved_recommendations = await save_recommendations(
            user_id=self.user_id,
            recommendations=timed_recommendations
        )
        
        return saved_recommendations
        
    async def execute_investment(self, recommendation_id, wallet_address=None):
        """Execute an investment based on a recommendation."""
        # Retrieve recommendation
        recommendation = await get_recommendation(recommendation_id)
        
        # Verify user owns this recommendation
        if recommendation.user_id != self.user_id:
            raise PermissionError("Not authorized to execute this recommendation")
            
        # Check if recommendation is still valid
        if recommendation.expires_at < datetime.utcnow():
            raise ValueError("Recommendation has expired")
            
        # Prepare transaction
        transaction = await prepare_transaction(
            recommendation=recommendation,
            wallet_address=wallet_address
        )
        
        # Execute based on automation level
        if self.automation_level == 'full':
            # Verify within safety limits
            await self._verify_safety_limits(transaction)
            # Execute directly
            result = await execute_transaction(transaction)
        elif self.automation_level == 'semi':
            # Queue for approval
            result = await queue_for_approval(transaction)
        else:  # 'manual'
            # Provide instructions for manual execution
            result = await generate_manual_instructions(transaction)
            
        # Update recommendation status
        await update_recommendation_status(
            recommendation_id=recommendation_id,
            status="executed" if result.success else "failed",
            transaction_id=result.transaction_id if result.success else None
        )
        
        return result
        
    async def _verify_safety_limits(self, transaction):
        """Verify transaction is within safety limits."""
        # Check transaction amount limits
        user_limits = await get_user_limits(self.user_id)
        
        if transaction.amount > user_limits.max_transaction:
            raise ValueError(f"Transaction exceeds maximum limit of {user_limits.max_transaction}")
            
        # Check daily volume limits
        daily_volume = await get_user_daily_volume(self.user_id)
        
        if daily_volume + transaction.amount > user_limits.daily_max:
            raise ValueError(f"Transaction would exceed daily limit of {user_limits.daily_max}")
            
        # Verify pool is still safe
        pool_safety = await check_pool_safety(transaction.pool_id)
        
        if pool_safety.risk_level > user_limits.max_risk_level:
            raise ValueError(f"Pool risk level {pool_safety.risk_level} exceeds maximum {user_limits.max_risk_level}")
            
        return True
        
    async def process_automation_rules(self):
        """Process all automation rules for this user."""
        # Get active automation rules
        rules = await get_active_automation_rules(self.user_id)
        
        results = []
        for rule in rules:
            try:
                # Check if rule conditions are met
                should_execute, actions = await evaluate_rule_conditions(rule)
                
                if should_execute:
                    # Execute the rule's actions
                    result = await execute_rule_actions(
                        rule_id=rule.id,
                        actions=actions,
                        automation_level=self.automation_level
                    )
                    results.append(result)
                    
                    # Update rule execution metadata
                    await update_rule_execution(
                        rule_id=rule.id,
                        executed_at=datetime.utcnow(),
                        result=result.success
                    )
            except Exception as e:
                logger.error(f"Error processing rule {rule.id}: {str(e)}")
                results.append({
                    "rule_id": rule.id,
                    "success": False,
                    "error": str(e)
                })
                
        return results
```

#### 2.2 Wallet Integration Module
```python
# wallet_service.py
class WalletService:
    """Service for wallet integration and transaction handling."""
    
    def __init__(self):
        self.rpc_client = RpcClient()
        self.walletconnect_client = WalletConnectClient()
        
    async def connect_wallet(self, user_id, connection_type='walletconnect'):
        """Connect a user's wallet using specified method."""
        if connection_type == 'walletconnect':
            # Create WalletConnect session
            session = await self.walletconnect_client.create_session(user_id)
            return {
                'success': True,
                'connection_type': 'walletconnect',
                'session_id': session.id,
                'uri': session.uri,
                'expires_at': session.expires_at
            }
        elif connection_type == 'direct':
            # Return instructions for direct connection
            return {
                'success': True,
                'connection_type': 'direct',
                'instructions': 'Please provide your wallet address'
            }
        else:
            raise ValueError(f"Unsupported connection type: {connection_type}")
            
    async def prepare_transaction(self, pool_id, amount, user_id, transaction_type='invest'):
        """Prepare a transaction for the specified pool and amount."""
        # Get pool details
        pool = await get_pool_by_id(pool_id)
        
        # Get user's wallet
        wallet = await get_user_wallet(user_id)
        
        # Calculate token amounts based on pool ratio
        token_amounts = await calculate_token_amounts(pool, amount)
        
        # Calculate estimated gas
        estimated_gas = await estimate_transaction_gas(
            transaction_type=transaction_type,
            pool=pool,
            token_amounts=token_amounts
        )
        
        # Create transaction object
        transaction = {
            'user_id': user_id,
            'pool_id': pool_id,
            'transaction_type': transaction_type,
            'amount': amount,
            'token_a_symbol': pool.token_a_symbol,
            'token_a_amount': token_amounts['token_a'],
            'token_b_symbol': pool.token_b_symbol,
            'token_b_amount': token_amounts['token_b'],
            'estimated_gas': estimated_gas,
            'wallet_address': wallet.address if wallet else None,
            'created_at': datetime.utcnow(),
            'status': 'prepared'
        }
        
        # Save transaction to database
        saved_transaction = await save_transaction(transaction)
        
        return saved_transaction
        
    async def execute_transaction(self, transaction_id, wallet_address=None, signed_tx=None):
        """Execute a prepared transaction."""
        # Get transaction details
        transaction = await get_transaction(transaction_id)
        
        # Verify transaction is in prepared state
        if transaction.status != 'prepared':
            raise ValueError(f"Transaction is in {transaction.status} state, not prepared")
            
        # Update wallet address if provided
        if wallet_address and not transaction.wallet_address:
            transaction.wallet_address = wallet_address
            await update_transaction(transaction)
            
        # If we have a signed transaction, submit it
        if signed_tx:
            result = await self.rpc_client.submit_transaction(signed_tx)
            
            # Update transaction with result
            transaction.status = 'completed' if result.success else 'failed'
            transaction.transaction_hash = result.tx_hash if result.success else None
            transaction.completed_at = datetime.utcnow() if result.success else None
            transaction.error_message = result.error if not result.success else None
            
            await update_transaction(transaction)
            
            # If successful, update user portfolio
            if result.success:
                await update_user_portfolio(
                    user_id=transaction.user_id,
                    transaction=transaction
                )
                
            return {
                'success': result.success,
                'transaction_id': transaction.id,
                'transaction_hash': result.tx_hash if result.success else None,
                'status': transaction.status,
                'error': result.error if not result.success else None
            }
            
        # Otherwise, create a transaction for signing
        else:
            # Get pool contract ABI
            pool_abi = await get_pool_abi(transaction.pool_id)
            
            # Build unsigned transaction
            unsigned_tx = await build_transaction(
                pool_abi=pool_abi,
                wallet_address=transaction.wallet_address,
                token_a_amount=transaction.token_a_amount,
                token_b_amount=transaction.token_b_amount,
                transaction_type=transaction.transaction_type
            )
            
            # If using WalletConnect, send for signing
            if transaction.wallet_connect_session_id:
                signing_request = await self.walletconnect_client.request_signature(
                    session_id=transaction.wallet_connect_session_id,
                    transaction=unsigned_tx
                )
                
                # Update transaction with signing request
                transaction.status = 'awaiting_signature'
                transaction.signing_request_id = signing_request.id
                await update_transaction(transaction)
                
                return {
                    'success': True,
                    'transaction_id': transaction.id,
                    'status': 'awaiting_signature',
                    'signing_request_id': signing_request.id
                }
                
            # Otherwise return unsigned transaction for manual signing
            else:
                # Update transaction status
                transaction.status = 'needs_signature'
                await update_transaction(transaction)
                
                return {
                    'success': True,
                    'transaction_id': transaction.id,
                    'status': 'needs_signature',
                    'unsigned_transaction': unsigned_tx
                }
                
    async def check_transaction_status(self, transaction_id):
        """Check the status of a transaction."""
        transaction = await get_transaction(transaction_id)
        
        # If transaction is completed or failed, just return current status
        if transaction.status in ['completed', 'failed']:
            return {
                'transaction_id': transaction.id,
                'status': transaction.status,
                'transaction_hash': transaction.transaction_hash,
                'completed_at': transaction.completed_at,
                'error_message': transaction.error_message
            }
            
        # If transaction is on-chain, check status
        if transaction.transaction_hash:
            tx_status = await self.rpc_client.check_transaction(transaction.transaction_hash)
            
            # Update transaction status if needed
            if tx_status.finalized and transaction.status != 'completed':
                transaction.status = 'completed'
                transaction.completed_at = datetime.utcnow()
                await update_transaction(transaction)
                
                # Update user portfolio
                await update_user_portfolio(
                    user_id=transaction.user_id,
                    transaction=transaction
                )
            elif tx_status.failed and transaction.status != 'failed':
                transaction.status = 'failed'
                transaction.error_message = tx_status.error or "Transaction failed on-chain"
                await update_transaction(transaction)
                
            return {
                'transaction_id': transaction.id,
                'status': transaction.status,
                'transaction_hash': transaction.transaction_hash,
                'blockchain_status': tx_status.status,
                'completed_at': transaction.completed_at,
                'error_message': transaction.error_message
            }
            
        # If transaction is awaiting signature, check WalletConnect status
        if transaction.status == 'awaiting_signature' and transaction.signing_request_id:
            signing_status = await self.walletconnect_client.check_signing_request(
                signing_request_id=transaction.signing_request_id
            )
            
            # If signed, submit transaction
            if signing_status.signed:
                submit_result = await self.execute_transaction(
                    transaction_id=transaction.id,
                    signed_tx=signing_status.signed_transaction
                )
                return submit_result
                
            # If rejected, update status
            elif signing_status.rejected:
                transaction.status = 'signature_rejected'
                transaction.error_message = "User rejected signature request"
                await update_transaction(transaction)
                
            return {
                'transaction_id': transaction.id,
                'status': transaction.status,
                'signing_status': signing_status.status
            }
            
        # Otherwise just return current status
        return {
            'transaction_id': transaction.id,
            'status': transaction.status
        }
        
    async def get_wallet_balance(self, wallet_address):
        """Get the balance of tokens in a wallet."""
        try:
            # Get SOL balance
            sol_balance = await self.rpc_client.get_sol_balance(wallet_address)
            
            # Get token balances
            token_balances = await self.rpc_client.get_token_balances(wallet_address)
            
            # Combine balances
            balances = {
                'SOL': sol_balance,
                **token_balances
            }
            
            return balances
        except Exception as e:
            logger.error(f"Error getting wallet balance: {str(e)}")
            raise
```

#### 2.3 AI Models Module
```python
# ai_models.py
class PoolRankingModel:
    """Model for ranking pools based on user profile and preferences."""
    
    async def rank_pools(self, pools, risk_profile, investment_horizon, portfolio=None, token_preference=None):
        """Rank pools according to user preferences."""
        # Convert risk profile to numerical values
        risk_weights = {
            'conservative': {'stability': 0.5, 'apr': 0.2, 'liquidity': 0.3},
            'moderate': {'stability': 0.3, 'apr': 0.4, 'liquidity': 0.3},
            'aggressive': {'stability': 0.1, 'apr': 0.7, 'liquidity': 0.2}
        }
        
        # Get weights for this risk profile
        weights = risk_weights.get(risk_profile, risk_weights['moderate'])
        
        # Apply time horizon factor
        horizon_factor = {
            'short': {'recent_weight': 0.8, 'historical_weight': 0.2},
            'medium': {'recent_weight': 0.5, 'historical_weight': 0.5},
            'long': {'recent_weight': 0.2, 'historical_weight': 0.8}
        }
        
        time_weights = horizon_factor.get(investment_horizon, horizon_factor['medium'])
        
        # Calculate scores for each pool
        scored_pools = []
        for pool in pools:
            # Skip pools with tokens that don't match preference (if specified)
            if token_preference and token_preference not in [pool.token_a_symbol, pool.token_b_symbol]:
                continue
                
            # Calculate APR score using time-weighted average
            apr_score = (
                pool.apr_24h * time_weights['recent_weight'] +
                (pool.apr_7d or pool.apr_24h) * time_weights['historical_weight']
            ) / 100  # Normalize to 0-1 scale
            
            # Calculate stability score (inverse of volatility)
            if pool.apr_7d and pool.apr_30d:
                volatility = std_dev([pool.apr_24h, pool.apr_7d, pool.apr_30d]) / max(pool.apr_24h, pool.apr_7d, pool.apr_30d)
                stability_score = 1 - min(volatility, 1)  # Normalize to 0-1 scale
            else:
                stability_score = 0.5  # Default for pools without historical data
                
            # Calculate liquidity score based on TVL
            # Normalize on log scale: 0.2 for $10k, 0.5 for $100k, 0.8 for $1M+
            liquidity_score = min(0.8, max(0.2, 0.2 + 0.3 * math.log10(max(10000, pool.tvl) / 10000)))
            
            # Calculate combined score
            combined_score = (
                apr_score * weights['apr'] +
                stability_score * weights['stability'] +
                liquidity_score * weights['liquidity']
            )
            
            # Apply diversification bonus if portfolio exists and doesn't contain this pool
            if portfolio and not any(p.pool_id == pool.id for p in portfolio):
                combined_score *= 1.1  # 10% bonus for diversification
                
            scored_pools.append({
                'pool': pool,
                'score': combined_score,
                'apr_score': apr_score,
                'stability_score': stability_score,
                'liquidity_score': liquidity_score
            })
            
        # Sort pools by score (descending)
        sorted_pools = sorted(scored_pools, key=lambda x: x['score'], reverse=True)
        
        return sorted_pools


class InvestmentTimingModel:
    """Model for optimizing investment timing."""
    
    async def optimize_timing(self, recommendations, market_conditions):
        """Optimize timing for investment recommendations."""
        # Apply timing factors to each recommendation
        timed_recommendations = []
        
        for rec in recommendations:
            pool = rec['pool']
            
            # Calculate gas price factor (0-1, higher is better timing)
            gas_factor = 1 - min(1, market_conditions['gas_price'] / 100)  # Normalize to 0-1
            
            # Calculate volatility factor
            market_volatility = market_conditions.get('volatility', 0.5)
            volatility_factor = 1 - market_volatility  # Lower volatility is better timing
            
            # Calculate momentum factor based on APR trend
            if pool.apr_7d and pool.apr_24h:
                momentum = (pool.apr_24h - pool.apr_7d) / max(pool.apr_7d, 1)  # Normalized change
                momentum_factor = 0.5 + min(0.5, max(-0.5, momentum * 5))  # Scale to 0-1
            else:
                momentum_factor = 0.5  # Neutral if no trend data
                
            # Combine factors with recommendation score
            timing_score = (
                rec['score'] * 0.6 +  # Base recommendation score
                gas_factor * 0.1 +    # Gas price impact
                volatility_factor * 0.1 + # Market volatility impact
                momentum_factor * 0.2  # Trend momentum impact
            )
            
            # Determine timing recommendation
            if timing_score > 0.8:
                timing_recommendation = "optimal"
            elif timing_score > 0.6:
                timing_recommendation = "good"
            elif timing_score > 0.4:
                timing_recommendation = "neutral"
            else:
                timing_recommendation = "suboptimal"
                
            # Add timing data to recommendation
            timed_rec = {
                **rec,
                'timing_score': timing_score,
                'timing_recommendation': timing_recommendation,
                'timing_factors': {
                    'gas_factor': gas_factor,
                    'volatility_factor': volatility_factor,
                    'momentum_factor': momentum_factor
                }
            }
            
            timed_recommendations.append(timed_rec)
            
        # Resort based on combined score and timing
        sorted_recommendations = sorted(timed_recommendations, 
                                       key=lambda x: x['score'] * 0.7 + x['timing_score'] * 0.3, 
                                       reverse=True)
        
        return sorted_recommendations


class PositionSizingModel:
    """Model for calculating optimal position sizes."""
    
    async def calculate_positions(self, ranked_pools, total_amount=None, risk_profile='moderate', portfolio=None):
        """Calculate optimal position sizes for recommended pools."""
        # If no amount specified, return pools with recommendation to size manually
        if not total_amount:
            return [{**pool, 'position_size': None} for pool in ranked_pools]
            
        # Determine number of positions based on risk profile
        max_positions = {
            'conservative': 5,  # More diversification
            'moderate': 3,
            'aggressive': 2     # More concentration
        }.get(risk_profile, 3)
        
        # Limit to top pools
        top_pools = ranked_pools[:max_positions]
        
        # Calculate allocation weights based on scores
        total_score = sum(pool['score'] for pool in top_pools)
        
        if total_score == 0:
            # Equal weighting if all scores are 0
            weights = [1/len(top_pools)] * len(top_pools)
        else:
            weights = [pool['score'] / total_score for pool in top_pools]
            
        # Apply risk profile adjustments to weights
        if risk_profile == 'conservative':
            # More equal weighting for conservative
            weights = [0.5 * w + 0.5 * (1/len(weights)) for w in weights]
        elif risk_profile == 'aggressive':
            # More concentrated for aggressive
            weights = [w ** 1.5 for w in weights]
            weights = [w / sum(weights) for w in weights]  # Renormalize
            
        # Calculate position sizes
        sized_pools = []
        for i, pool in enumerate(top_pools):
            position_size = total_amount * weights[i]
            
            # Enforce minimum meaningful position size (1% of total)
            if position_size < (total_amount * 0.01):
                continue
                
            # Round to appropriate precision
            position_size = round(position_size, 2)
            
            sized_pools.append({
                **pool,
                'position_size': position_size,
                'allocation_weight': weights[i]
            })
            
        return sized_pools
```

#### 2.4 Blockchain Integration Module
```python
# blockchain_service.py
class RpcClient:
    """Client for interacting with blockchain via RPC."""
    
    def __init__(self):
        """Initialize the RPC client."""
        # Get RPC endpoint from environment variables
        self.rpc_url = os.environ.get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
        self.commitment = "confirmed"
        
        # Initialize web3 connection
        # This is a simplified example - actual implementation would use appropriate
        # Solana or EVM based libraries depending on the blockchain
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
    async def get_sol_balance(self, wallet_address):
        """Get SOL balance for a wallet."""
        try:
            response = await self._make_rpc_call("getBalance", [wallet_address])
            balance = response.get("result", {}).get("value", 0) / 10**9  # Convert lamports to SOL
            return balance
        except Exception as e:
            logger.error(f"Error getting SOL balance: {str(e)}")
            raise
            
    async def get_token_balances(self, wallet_address):
        """Get SPL token balances for a wallet."""
        try:
            response = await self._make_rpc_call("getTokenAccountsByOwner", [
                wallet_address,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},  # SPL Token program ID
                {"encoding": "jsonParsed"}
            ])
            
            token_balances = {}
            for account in response.get("result", {}).get("value", []):
                token_data = account.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                
                token_address = token_data.get("mint")
                if not token_address:
                    continue
                    
                # Get token info
                token_info = await self._get_token_info(token_address)
                
                # Calculate actual balance with decimals
                raw_balance = int(token_data.get("tokenAmount", {}).get("amount", 0))
                decimals = int(token_data.get("tokenAmount", {}).get("decimals", 0))
                balance = raw_balance / (10 ** decimals)
                
                if token_info and token_info.get("symbol"):
                    token_balances[token_info["symbol"]] = balance
                    
            return token_balances
        except Exception as e:
            logger.error(f"Error getting token balances: {str(e)}")
            raise
            
    async def _get_token_info(self, token_address):
        """Get information about a token."""
        # This would typically query a token registry or on-chain metadata
        # Simplified implementation for demonstration
        token_registry = {
            "So11111111111111111111111111111111111111112": {"symbol": "SOL", "decimals": 9},
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {"symbol": "USDC", "decimals": 6},
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {"symbol": "USDT", "decimals": 6}
            # Add more tokens as needed
        }
        
        return token_registry.get(token_address, {"symbol": token_address[:5], "decimals": 9})
        
    async def estimate_transaction_gas(self, transaction_type, pool, token_amounts):
        """Estimate gas fees for a transaction."""
        # This would calculate actual gas estimates based on the transaction type
        # Simplified implementation for demonstration
        base_fee = 0.000005  # Base fee in SOL
        
        # Adjust based on transaction type
        if transaction_type == "invest":
            fee_multiplier = 2.0
        elif transaction_type == "withdraw":
            fee_multiplier = 1.5
        else:
            fee_multiplier = 1.0
            
        # Estimate fee
        estimated_fee = base_fee * fee_multiplier
        
        return estimated_fee
        
    async def submit_transaction(self, signed_transaction):
        """Submit a signed transaction to the blockchain."""
        try:
            response = await self._make_rpc_call("sendTransaction", [
                signed_transaction,
                {"encoding": "base64", "commitment": self.commitment}
            ])
            
            tx_hash = response.get("result")
            
            if tx_hash:
                return {
                    "success": True,
                    "tx_hash": tx_hash
                }
            else:
                error = response.get("error", {}).get("message", "Unknown error")
                return {
                    "success": False,
                    "error": error
                }
        except Exception as e:
            logger.error(f"Error submitting transaction: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def check_transaction(self, tx_hash):
        """Check the status of a transaction."""
        try:
            response = await self._make_rpc_call("getSignatureStatuses", [[tx_hash]])
            
            status_info = response.get("result", {}).get("value", [None])[0]
            
            if not status_info:
                return {
                    "status": "pending",
                    "finalized": False,
                    "failed": False
                }
                
            confirmations = status_info.get("confirmations")
            is_finalized = confirmations is None and status_info.get("confirmationStatus") == "finalized"
            
            return {
                "status": status_info.get("confirmationStatus", "unknown"),
                "confirmations": confirmations,
                "finalized": is_finalized,
                "failed": status_info.get("err") is not None,
                "error": status_info.get("err")
            }
        except Exception as e:
            logger.error(f"Error checking transaction: {str(e)}")
            raise
            
    async def _make_rpc_call(self, method, params=None):
        """Make a JSON-RPC call."""
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params or []
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.rpc_url, headers=headers, json=data) as response:
                response_data = await response.json()
                
                if "error" in response_data:
                    logger.error(f"RPC error: {response_data['error']}")
                    
                return response_data
```

### 3. Added Telegram Bot Commands and Handlers

#### 3.1 New Bot Commands
```python
async def invest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Start the investment process when the command /invest is issued.
    
    Parameters:
        amount (optional): Amount to invest, e.g. /invest 100
    """
    try:
        user = update.effective_user
        
        # Extract amount if provided
        amount = None
        if context.args and len(context.args) > 0:
            try:
                amount = float(context.args[0])
                if amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError:
                await update.message.reply_text(
                    "Please provide a valid positive amount. Example: /invest 100"
                )
                return
        
        # If no amount provided, ask user
        if not amount:
            await update.message.reply_text(
                "How much would you like to invest? Please reply with a number (e.g. 100)."
            )
            # Set conversation state to expect amount
            context.user_data["expecting_invest_amount"] = True
            return
        
        # Start investment process
        await update.message.reply_text(f"Starting investment process for ${amount:.2f}...")
        
        # Get user's profile
        from app import app
        with app.app_context():
            db_user = db_utils.get_or_create_user(user.id)
            risk_profile = db_user.risk_profile
            investment_horizon = db_user.investment_horizon
        
        # Create investment agent
        agent = InvestmentAgent(
            user_id=user.id,
            risk_profile=risk_profile,
            investment_horizon=investment_horizon
        )
        
        # Get recommendations
        recommendations = await agent.get_recommendations(amount=amount)
        
        if not recommendations or len(recommendations) == 0:
            await update.message.reply_text(
                "No suitable investment opportunities found at this time. Please try again later."
            )
            return
        
        # Format recommendations
        formatted_recommendations = format_investment_recommendations(recommendations)
        
        # Create buttons for each recommendation
        keyboard = []
        for rec in recommendations[:3]:  # Limit to top 3
            keyboard.append([
                InlineKeyboardButton(
                    f"{rec.pool.token_a_symbol}-{rec.pool.token_b_symbol} (${rec.recommended_amount:.2f})",
                    callback_data=f"invest_{rec.id}"
                )
            ])
        
        # Add button to see more recommendations
        if len(recommendations) > 3:
            keyboard.append([
                InlineKeyboardButton("See More Options", callback_data="more_investments")
            ])
        
        # Add button to customize amount
        keyboard.append([
            InlineKeyboardButton("Customize Amount", callback_data="customize_investment")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_markdown(
            f"*Investment Recommendations*\n\n{formatted_recommendations}\n\n"
            f"Please select a pool to invest in:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Error in invest command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your investment. Please try again later."
        )


async def auto_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Configure automation rules when the command /auto is issued.
    
    Examples:
        /auto list - List current automation rules
        /auto create - Start creating a new rule
        /auto delete 1 - Delete rule with ID 1
    """
    try:
        user = update.effective_user
        
        # Get subcommand
        if not context.args or len(context.args) == 0:
            # Default to showing help if no subcommand
            await update.message.reply_markdown(
                "*Automation Commands*\n\n"
                "• `/auto list` - List your current automation rules\n"
                "• `/auto create` - Create a new automation rule\n"
                "• `/auto delete [ID]` - Delete a rule (e.g. `/auto delete 1`)\n"
                "• `/auto toggle [ID]` - Enable/disable a rule\n\n"
                "Automation allows FiLot to manage your investments based on your preferences."
            )
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == "list":
            # List existing automation rules
            from app import app
            with app.app_context():
                rules = await get_automation_rules(user.id)
            
            if not rules or len(rules) == 0:
                await update.message.reply_markdown(
                    "You don't have any automation rules set up yet.\n\n"
                    "Use `/auto create` to set up your first rule."
                )
                return
            
            # Format rules for display
            rules_text = "*Your Automation Rules*\n\n"
            
            for rule in rules:
                status = "✅ Active" if rule.is_active else "❌ Disabled"
                rules_text += f"*Rule {rule.id}: {rule.rule_name}* - {status}\n"
                rules_text += f"Type: {rule.rule_type.capitalize()}\n"
                
                # Format trigger conditions
                if rule.rule_type == "periodic":
                    interval = rule.trigger_conditions.get("interval", "daily")
                    rules_text += f"Frequency: Every {interval}\n"
                elif rule.rule_type == "threshold":
                    metric = rule.trigger_conditions.get("metric", "apr")
                    threshold = rule.trigger_conditions.get("threshold", 0)
                    operator = rule.trigger_conditions.get("operator", ">")
                    rules_text += f"Trigger: When {metric} {operator} {threshold}\n"
                
                # Format actions
                action = rule.actions.get("action", "notify")
                if action == "invest":
                    amount = rule.actions.get("amount", 0)
                    rules_text += f"Action: Invest ${amount:.2f}\n"
                elif action == "rebalance":
                    rules_text += "Action: Rebalance portfolio\n"
                
                # Add rule limits
                if rule.max_transaction_amount:
                    rules_text += f"Maximum transaction: ${rule.max_transaction_amount:.2f}\n"
                
                rules_text += "\n"
            
            # Add button to create new rule
            keyboard = [[InlineKeyboardButton("Create New Rule", callback_data="auto_create")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_markdown(rules_text, reply_markup=reply_markup)
            
        elif subcommand == "create":
            # Start rule creation wizard
            keyboard = [
                [InlineKeyboardButton("Periodic Investment", callback_data="auto_create_periodic")],
                [InlineKeyboardButton("Threshold-Based", callback_data="auto_create_threshold")],
                [InlineKeyboardButton("Portfolio Rebalancing", callback_data="auto_create_rebalance")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_markdown(
                "*Create Automation Rule*\n\n"
                "Please select the type of automation rule you want to create:",
                reply_markup=reply_markup
            )
            
        elif subcommand == "delete":
            # Delete a rule
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Please specify which rule to delete. Example: /auto delete 1"
                )
                return
            
            try:
                rule_id = int(context.args[1])
                
                # Verify rule exists and belongs to user
                from app import app
                with app.app_context():
                    rule = await get_automation_rule(rule_id)
                    
                    if not rule or rule.user_id != user.id:
                        await update.message.reply_text(
                            "Rule not found. Please check the ID and try again."
                        )
                        return
                    
                    # Confirm deletion
                    keyboard = [
                        [InlineKeyboardButton("Yes, Delete Rule", callback_data=f"confirm_delete_rule_{rule_id}")],
                        [InlineKeyboardButton("No, Keep Rule", callback_data="cancel_delete_rule")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_markdown(
                        f"*Confirm Rule Deletion*\n\n"
                        f"Are you sure you want to delete rule #{rule_id}: {rule.rule_name}?\n\n"
                        f"This action cannot be undone.",
                        reply_markup=reply_markup
                    )
            except ValueError:
                await update.message.reply_text(
                    "Invalid rule ID. Please provide a number."
                )
            
        elif subcommand == "toggle":
            # Enable or disable a rule
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Please specify which rule to toggle. Example: /auto toggle 1"
                )
                return
            
            try:
                rule_id = int(context.args[1])
                
                # Toggle rule status
                from app import app
                with app.app_context():
                    result = await toggle_automation_rule(rule_id, user.id)
                    
                    if result["success"]:
                        status = "enabled" if result["is_active"] else "disabled"
                        await update.message.reply_markdown(
                            f"✅ Rule #{rule_id} has been {status}.\n\n"
                            f"Use `/auto list` to see all your rules."
                        )
                    else:
                        await update.message.reply_text(
                            f"Error: {result['error']}"
                        )
            except ValueError:
                await update.message.reply_text(
                    "Invalid rule ID. Please provide a number."
                )
            
        else:
            # Unknown subcommand
            await update.message.reply_markdown(
                "Unknown command. Available options:\n\n"
                "• `/auto list` - List your current automation rules\n"
                "• `/auto create` - Create a new automation rule\n"
                "• `/auto delete [ID]` - Delete a rule\n"
                "• `/auto toggle [ID]` - Enable/disable a rule"
            )
        
    except Exception as e:
        logger.error(f"Error in auto command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while processing your automation request. Please try again later."
        )


async def portfolio_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show user's investment portfolio when the command /portfolio is issued.
    """
    try:
        user = update.effective_user
        
        # Get user's portfolio
        from app import app
        with app.app_context():
            db_utils.log_user_activity(user.id, "portfolio_command")
            portfolio = await get_user_portfolio(user.id)
        
        if not portfolio or len(portfolio) == 0:
            await update.message.reply_markdown(
                "📊 *Your Investment Portfolio*\n\n"
                "You don't have any active investments yet.\n\n"
                "Use the `/invest` command to start investing in liquidity pools."
            )
            return
        
        # Calculate portfolio metrics
        total_invested = sum(item.initial_value_usd for item in portfolio)
        current_value = sum(item.current_value_usd for item in portfolio)
        total_return = current_value - total_invested
        return_percentage = (total_return / total_invested) * 100 if total_invested > 0 else 0
        total_fees = sum(item.fees_earned_usd for item in portfolio)
        
        # Format portfolio summary
        summary = (
            "📊 *Your Investment Portfolio*\n\n"
            f"Total Invested: *${total_invested:.2f}*\n"
            f"Current Value: *${current_value:.2f}*\n"
            f"Total Return: *${total_return:.2f}* ({return_percentage:.2f}%)\n"
            f"Fees Earned: *${total_fees:.2f}*\n\n"
            "*Active Investments:*\n\n"
        )
        
        # Format individual investments
        for item in portfolio:
            pool = await get_pool_by_id(item.pool_id)
            
            if not pool:
                continue
                
            item_return = item.current_value_usd - item.initial_value_usd
            item_return_pct = (item_return / item.initial_value_usd) * 100 if item.initial_value_usd > 0 else 0
            
            # Format with emojis based on performance
            performance_emoji = "🟢" if item_return > 0 else "🔴" if item_return < 0 else "⚪"
            
            # Add to summary
            summary += (
                f"{performance_emoji} *{pool.token_a_symbol}-{pool.token_b_symbol}*\n"
                f"Invested: ${item.initial_value_usd:.2f} on {item.entry_date.strftime('%Y-%m-%d')}\n"
                f"Current: ${item.current_value_usd:.2f} ({item_return_pct:.2f}%)\n"
                f"Fee Income: ${item.fees_earned_usd:.2f}\n"
                f"Current APR: {pool.apr_24h:.2f}%\n\n"
            )
        
        # Add portfolio management buttons
        keyboard = [
            [InlineKeyboardButton("Add to Portfolio", callback_data="invest")],
            [InlineKeyboardButton("Rebalance Portfolio", callback_data="rebalance_portfolio")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_markdown(summary, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error in portfolio command: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred while retrieving your portfolio. Please try again later."
        )
```

#### 3.2 Message Handler Updates
```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle user messages that are not commands.
    Intelligently detects questions and provides predefined answers or 
    routes to AI for specialized financial advice.
    Updated to handle investment amount input.
    """
    try:
        user = update.effective_user
        message_text = update.message.text
        
        # Check if we're expecting investment amount
        if context.user_data.get("expecting_invest_amount", False):
            try:
                # Parse amount
                amount = float(message_text.strip())
                if amount <= 0:
                    raise ValueError("Amount must be positive")
                
                # Clear expectation
                context.user_data["expecting_invest_amount"] = False
                
                # Forward to invest command
                context.args = [str(amount)]
                return await invest_command(update, context)
            except ValueError:
                await update.message.reply_text(
                    "Please provide a valid positive amount (e.g. 100)."
                )
                return
        
        # Check if we're in rule creation flow
        if "auto_rule_creation" in context.user_data:
            return await handle_rule_creation_input(update, context)
        
        # Continue with regular message handling
        # (existing code for handling questions and AI responses)
        # ...
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        await update.message.reply_text(
            "Sorry, an error occurred. Please try again later."
        )
```

#### 3.3 Callback Handler Updates
```python
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries from inline keyboards.
    Updated to support investment and automation workflows.
    """
    try:
        query = update.callback_query
        user = query.from_user
        data = query.data
        
        # Acknowledge the callback
        await query.answer()
        
        # Handle investment selections
        if data.startswith("invest_"):
            recommendation_id = int(data.split("_")[1])
            await handle_investment_selection(update, context, recommendation_id)
            return
            
        # Handle automation rule creation
        if data.startswith("auto_create"):
            rule_type = data.split("_")[-1] if len(data.split("_")) > 2 else None
            await handle_automation_rule_creation(update, context, rule_type)
            return
            
        # Handle rule deletion
        if data.startswith("confirm_delete_rule_"):
            rule_id = int(data.split("_")[-1])
            
            from app import app
            with app.app_context():
                result = await delete_automation_rule(rule_id, user.id)
                
                if result["success"]:
                    await query.edit_message_text(
                        f"✅ Rule #{rule_id} has been deleted successfully."
                    )
                else:
                    await query.edit_message_text(
                        f"Error: {result['error']}"
                    )
            return
            
        # Handle other callback types
        # (existing code for handling other callbacks)
        # ...
    except Exception as e:
        logger.error(f"Error handling callback query: {e}", exc_info=True)
        try:
            await query.edit_message_text(
                "Sorry, an error occurred. Please try again later."
            )
        except Exception:
            pass
```

## Implementation Schedule

1. **Database Schema Updates - Week 1**
   - Create new tables for automation, transactions, portfolio tracking
   - Add indexes for performance optimization
   - Implement migration script for existing database

2. **Core Investment Agent - Weeks 2-3**
   - Develop pool ranking algorithms
   - Implement recommendation generation
   - Create investment sizing strategies
   - Build safety verification systems

3. **Wallet Integration - Weeks 4-5**
   - Enhance WalletConnect implementation
   - Develop transaction signing workflow
   - Implement balance checking features
   - Create transaction history tracking

4. **Blockchain Interface - Weeks 6-7**
   - Build Solana RPC client
   - Implement token balance retrieval
   - Create transaction submission system
   - Develop transaction verification system

5. **Bot Command Updates - Week 8**
   - Add investment command
   - Implement automation commands
   - Create portfolio management interface
   - Enhance message handlers for new flows

6. **Testing & Deployment - Weeks 9-10**
   - Comprehensive testing with test wallets
   - Security audit of transaction handling
   - Performance optimization
   - Phased rollout to users

## Security Considerations

1. **Transaction Safety**
   - Mandatory transaction limits for all users
   - Graduated permissions based on verification level
   - Multiple confirmation steps for large transactions
   - Continuous monitoring for suspicious activity

2. **Wallet Protection**
   - No storage of private keys
   - Read-only connections by default
   - Detailed permission explanations
   - Automatic session timeouts

3. **Data Protection**
   - Encryption of sensitive user data
   - Database access controls
   - Regular security audits
   - Compliance with regulatory requirements

4. **Risk Management**
   - Continuous pool risk assessment
   - Automatic suspension of risky pools
   - Diversification requirements
   - Clear risk communication to users

## Monitoring & Maintenance

1. **Performance Monitoring**
   - Track recommendation accuracy
   - Monitor transaction success rates
   - Measure portfolio performance
   - Log system response times

2. **Error Tracking**
   - Centralized error logging
   - Automatic alerts for critical errors
   - Daily error review process
   - User-reported issues tracking

3. **Model Updates**
   - Weekly model retraining
   - Performance evaluation metrics
   - A/B testing of algorithm improvements
   - User feedback incorporation

4. **System Maintenance**
   - Regular database optimization
   - Cache management
   - API usage monitoring
   - Load balancing as needed

## Conclusion

This technical specification outlines the implementation details for transforming FiLot from an informational bot into a fully agentic investment advisor. The architecture provides a scalable, secure framework for autonomous investment decisions while maintaining appropriate user controls and oversight.

The next phase of development will focus on building these core components, with emphasis on security, reliability, and user experience. This system will enable FiLot to deliver on its promise of simplifying DeFi investments through intelligent automation.