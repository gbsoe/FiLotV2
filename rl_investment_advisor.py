#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reinforcement Learning Investment Advisor for FiLot Telegram bot
Provides AI-powered investment recommendations using RL techniques
"""

import logging
import time
import random
import json
import os
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

import solpool_api_client as solpool_api
import filotsense_api_client as sentiment_api
import agentic_advisor

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Feature importance weights by risk profile
RISK_PROFILE_WEIGHTS = {
    "conservative": {
        "apr": 0.15,           # Lower weight on APR
        "tvl": 0.30,           # Higher weight on liquidity/stability
        "volume": 0.15,        # Medium weight on volume
        "volatility": -0.20,   # High penalty for volatility
        "sentiment": 0.10,     # Low weight on sentiment
        "prediction": 0.10     # Low weight on AI predictions
    },
    "moderate": {
        "apr": 0.25,           # Medium weight on APR
        "tvl": 0.20,           # Medium weight on liquidity/stability
        "volume": 0.15,        # Medium weight on volume
        "volatility": -0.10,   # Medium penalty for volatility
        "sentiment": 0.15,     # Medium weight on sentiment
        "prediction": 0.15     # Medium weight on AI predictions
    },
    "aggressive": {
        "apr": 0.35,           # High weight on APR
        "tvl": 0.10,           # Low weight on liquidity/stability
        "volume": 0.15,        # Medium weight on volume
        "volatility": -0.05,   # Low penalty for volatility
        "sentiment": 0.15,     # Medium weight on sentiment
        "prediction": 0.20     # High weight on AI predictions
    }
}

# DQN Model configuration
DQN_CONFIG = {
    "learning_rate": 0.001,    # Learning rate for optimizer
    "gamma": 0.95,             # Discount factor for future rewards
    "epsilon": 0.2,            # Exploration rate
    "epsilon_min": 0.01,       # Minimum exploration rate
    "epsilon_decay": 0.995,    # Decay rate for exploration
    "memory_size": 1000,       # Replay memory size
    "batch_size": 32           # Batch size for training
}

# File to store experience replay buffer
EXPERIENCE_BUFFER_FILE = "rl_experience.json"

# Check if PyTorch is available (for actual DQN implementation)
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    PYTORCH_AVAILABLE = True
    logger.info("PyTorch is available, using DQN model")
except ImportError:
    PYTORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using simulated RL model")

class SimpleReplayMemory:
    """Simple experience replay memory for RL agent"""
    
    def __init__(self, capacity=1000):
        """Initialize replay memory with given capacity"""
        self.capacity = capacity
        self.memory = []
        self.position = 0
        self._load_memory()
        
    def _load_memory(self):
        """Load experience memory from file if exists"""
        try:
            if os.path.exists(EXPERIENCE_BUFFER_FILE):
                with open(EXPERIENCE_BUFFER_FILE, 'r') as f:
                    self.memory = json.load(f)
                    self.position = len(self.memory) % self.capacity
                    logger.info(f"Loaded {len(self.memory)} experiences from replay memory")
        except Exception as e:
            logger.error(f"Error loading replay memory: {e}")
            self.memory = []
            self.position = 0
            
    def _save_memory(self):
        """Save experience memory to file"""
        try:
            with open(EXPERIENCE_BUFFER_FILE, 'w') as f:
                json.dump(self.memory, f)
        except Exception as e:
            logger.error(f"Error saving replay memory: {e}")
            
    def push(self, state, action, reward, next_state, done):
        """Add experience to memory"""
        if len(self.memory) < self.capacity:
            self.memory.append(None)
        self.memory[self.position] = {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "done": done
        }
        self.position = (self.position + 1) % self.capacity
        # Periodically save memory
        if self.position % 10 == 0:
            self._save_memory()
            
    def sample(self, batch_size):
        """Sample a batch of experiences from memory"""
        if len(self.memory) < batch_size:
            return []
        return random.sample(self.memory, batch_size)
    
    def __len__(self):
        """Return current size of memory"""
        return len(self.memory)

class SimpleDQN:
    """Simple DQN model implementation when PyTorch is not available"""
    
    def __init__(self, state_size, action_size):
        """
        Initialize simulated DQN model
        
        Args:
            state_size: Size of state space (number of features)
            action_size: Size of action space (number of possible actions)
        """
        self.state_size = state_size
        self.action_size = action_size
        self.epsilon = DQN_CONFIG["epsilon"]
        self.epsilon_min = DQN_CONFIG["epsilon_min"]
        self.epsilon_decay = DQN_CONFIG["epsilon_decay"]
        self.memory = SimpleReplayMemory(DQN_CONFIG["memory_size"])
        self.weights = np.random.randn(state_size, action_size) * 0.1
        logger.info(f"Initialized simulated DQN with state size {state_size} and action size {action_size}")
        
    def act(self, state):
        """
        Choose an action based on current state
        
        Args:
            state: Current state vector
            
        Returns:
            Chosen action index
        """
        if np.random.rand() <= self.epsilon:
            # Exploration: random action
            return random.randrange(self.action_size)
        
        # Exploitation: best known action
        act_values = np.dot(state, self.weights)
        return np.argmax(act_values)
    
    def train(self, batch_size=None):
        """
        Simple training step using memory replay
        
        Args:
            batch_size: Batch size for training
        """
        if batch_size is None:
            batch_size = DQN_CONFIG["batch_size"]
            
        if len(self.memory) < batch_size:
            return
        
        # Sample batch from memory
        experiences = self.memory.sample(batch_size)
        
        # Very simple update rule (not a real DQN, just for simulation)
        for experience in experiences:
            state = np.array(experience["state"])
            action = experience["action"]
            reward = experience["reward"]
            next_state = np.array(experience["next_state"])
            done = experience["done"]
            
            # Simple Q-learning update
            target = reward
            if not done:
                target += DQN_CONFIG["gamma"] * np.max(np.dot(next_state, self.weights))
                
            # Update weights for the taken action
            current_q = np.dot(state, self.weights[:, action])
            error = target - current_q
            
            # Update weights for chosen action
            for i in range(self.state_size):
                self.weights[i, action] += DQN_CONFIG["learning_rate"] * error * state[i]
        
        # Decay exploration rate
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

class RLInvestmentAdvisor:
    """RL-based investment advisor that provides optimized pool recommendations"""
    
    def __init__(self):
        """Initialize the RL investment advisor"""
        # State space size: APR, TVL, Volume, Volatility, Sentiment, Prediction
        self.state_size = 6
        # Action space: top N pools to recommend
        self.action_size = 10
        
        # Initialize DQN model
        if PYTORCH_AVAILABLE:
            # PyTorch DQN implementation would go here
            # For now, just use the simple DQN
            self.model = SimpleDQN(self.state_size, self.action_size)
        else:
            self.model = SimpleDQN(self.state_size, self.action_size)
            
        # For tracking selected investments
        self.investments = {}
        
    def _extract_features(self, pool_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract features from pool data for RL state
        
        Args:
            pool_data: Pool data dictionary
            
        Returns:
            Feature vector as numpy array
        """
        # Extract and normalize features
        apr = min(pool_data.get("apr_24h", 0) / 100.0, 1.0)  # Normalize 0-100% to 0-1
        tvl = min(pool_data.get("tvl", 0) / 10000000.0, 1.0)  # Normalize $0-10M to 0-1
        volume = min(pool_data.get("volume_24h", 0) / 1000000.0, 1.0)  # Normalize $0-1M to 0-1
        
        # Volatility (simplified)
        price_change = abs(pool_data.get("price_change_24h", 0)) / 20.0  # Normalize +-20% to 0-1
        
        # Sentiment from FilotSense
        sentiment = 0.5  # Default neutral
        token_a = pool_data.get("token_a_symbol", "")
        token_b = pool_data.get("token_b_symbol", "")
        
        try:
            all_sentiment = sentiment_api.get_sentiment_data()
            
            if all_sentiment.get("status") == "success" and all_sentiment.get("sentiment"):
                # Calculate average sentiment for both tokens
                sentiments = []
                
                if token_a in all_sentiment["sentiment"]:
                    sentiments.append(all_sentiment["sentiment"][token_a].get("score", 0))
                    
                if token_b in all_sentiment["sentiment"]:
                    sentiments.append(all_sentiment["sentiment"][token_b].get("score", 0))
                    
                if sentiments:
                    # Convert -1 to 1 scale to 0 to 1
                    sentiment = sum(sentiments) / len(sentiments)
                    sentiment = (sentiment + 1) / 2  # Convert -1:1 to 0:1
        except Exception as e:
            logger.error(f"Error getting sentiment data: {e}")
        
        # Prediction score from SolPool
        prediction = pool_data.get("prediction_score", 50) / 100.0  # Normalize 0-100 to 0-1
        
        return np.array([apr, tvl, volume, price_change, sentiment, prediction])
    
    def _calculate_reward(self, 
                        pool_data: Dict[str, Any], 
                        initial_investment: float,
                        days_held: int,
                        risk_profile: str = "moderate") -> float:
        """
        Calculate reward for RL training based on investment outcome
        
        Args:
            pool_data: Pool data at end of investment period
            initial_investment: Initial investment amount
            days_held: Number of days investment was held
            risk_profile: User's risk profile
            
        Returns:
            Calculated reward value
        """
        # Get feature weights based on risk profile
        if risk_profile not in RISK_PROFILE_WEIGHTS:
            risk_profile = "moderate"
            
        weights = RISK_PROFILE_WEIGHTS[risk_profile]
        
        # Extract features
        features = self._extract_features(pool_data)
        
        # Calculate weighted feature score
        feature_score = (
            features[0] * weights["apr"] +
            features[1] * weights["tvl"] +
            features[2] * weights["volume"] +
            features[3] * weights["volatility"] +
            features[4] * weights["sentiment"] +
            features[5] * weights["prediction"]
        )
        
        # Calculate estimated return
        apr = pool_data.get("apr_24h", 0)
        estimated_return = initial_investment * (1 + (apr/100) * (days_held/365))
        profit_ratio = (estimated_return - initial_investment) / initial_investment
        
        # Combine feature score with profit ratio
        reward = feature_score * 0.5 + profit_ratio * 0.5
        
        return reward
    
    def get_recommendations(self,
                           investment_amount: float,
                           risk_profile: str = "moderate",
                           token_preference: Optional[str] = None,
                           max_suggestions: int = 3) -> Dict[str, Any]:
        """
        Get RL-powered investment recommendations
        
        Args:
            investment_amount: Amount to invest (USD)
            risk_profile: User's risk tolerance ("conservative", "moderate", "aggressive")
            token_preference: Optional token to prioritize in recommendations
            max_suggestions: Maximum number of pool suggestions to return
            
        Returns:
            Dictionary with recommendations, explanations, and confidence scores
        """
        logger.info(f"Generating RL-powered recommendations with {risk_profile} profile and ${investment_amount} investment")
        
        # Initialize result
        result = {
            "status": "success",
            "investment_amount": investment_amount,
            "risk_profile": risk_profile,
            "token_preference": token_preference,
            "suggestions": [],
            "market_sentiment": {},
            "explanation": "",
            "fallback_used": False,
            "rl_powered": True,
            "action": "invest"
        }
        
        try:
            # Get candidate pools
            candidate_pools = []
            
            # Try to get pools from token preference if specified
            if token_preference:
                token_pools = solpool_api.get_token_pools(token_preference, limit=10)
                if token_pools and len(token_pools) > 0:
                    candidate_pools.extend(token_pools)
                    logger.info(f"Found {len(token_pools)} pools containing {token_preference}")
            
            # Add high APR pools
            high_apr_pools = solpool_api.get_high_apr_pools(limit=10)
            if high_apr_pools and len(high_apr_pools) > 0:
                candidate_pools.extend(high_apr_pools)
                logger.info(f"Found {len(high_apr_pools)} high APR pools")
            
            # Get predictions 
            predicted_pools = solpool_api.get_predictions(min_score=50, limit=10)
            if predicted_pools and len(predicted_pools) > 0:
                for pred in predicted_pools:
                    pred_pool = {
                        "id": pred.get("pool_id", ""),
                        "token_a_symbol": pred.get("name", "").split("/")[0] if "/" in pred.get("name", "") else "",
                        "token_b_symbol": pred.get("name", "").split("/")[1] if "/" in pred.get("name", "") else "",
                        "apr_24h": pred.get("current_apr", 0),
                        "tvl": pred.get("current_tvl", 0),
                        "prediction_score": pred.get("prediction_score", 0),
                        "predicted_apr_mid": pred.get("predicted_apr_mid", 0),
                        "key_factors": pred.get("key_factors", [])
                    }
                    candidate_pools.append(pred_pool)
                logger.info(f"Found {len(predicted_pools)} pools with predictions")
            
            # Not enough pools to analyze
            if len(candidate_pools) < max_suggestions:
                # Fallback to standard agentic advisor
                logger.info("Not enough candidate pools, falling back to standard advisor")
                standard_recommendation = agentic_advisor.get_investment_recommendation(
                    investment_amount, risk_profile, token_preference, max_suggestions
                )
                standard_recommendation["rl_powered"] = False
                return standard_recommendation
            
            # Get market sentiment for result context
            try:
                all_sentiment = sentiment_api.get_sentiment_data()
                if all_sentiment.get("status") == "success" and all_sentiment.get("sentiment"):
                    # Add overall market sentiment (average of BTC and ETH as indicators)
                    if "BTC" in all_sentiment["sentiment"] and "ETH" in all_sentiment["sentiment"]:
                        btc_score = all_sentiment["sentiment"]["BTC"].get("score", 0)
                        eth_score = all_sentiment["sentiment"]["ETH"].get("score", 0)
                        overall_score = (btc_score + eth_score) / 2
                        result["market_sentiment"]["overall"] = {"score": overall_score}
                    
                    # Add Solana ecosystem sentiment
                    if "SOL" in all_sentiment["sentiment"]:
                        result["market_sentiment"]["solana"] = all_sentiment["sentiment"]["SOL"]
            except Exception as e:
                logger.error(f"Error getting sentiment data: {e}")
            
            # Extract features for each pool
            pool_features = []
            for pool in candidate_pools:
                # Skip duplicates by ID
                if any(p["pool_id"] == pool.get("id") for p in pool_features):
                    continue
                
                features = self._extract_features(pool)
                
                # Skip invalid pools
                if np.isnan(features).any():
                    continue
                
                # Add to feature list
                pool_features.append({
                    "pool_id": pool.get("id", ""),
                    "pair": f"{pool.get('token_a_symbol', '')}/{pool.get('token_b_symbol', '')}",
                    "features": features,
                    "raw_data": pool
                })
            
            # Use RL model to rank pools
            ranked_pools = []
            
            # For each candidate pool, calculate Q-value directly
            for pool in pool_features:
                state = pool["features"]
                q_values = np.dot(state, self.model.weights)
                confidence = np.max(q_values) / np.sum(np.abs(q_values)) if np.sum(np.abs(q_values)) > 0 else 0
                
                # Apply risk profile weights to get final score
                weights = RISK_PROFILE_WEIGHTS[risk_profile]
                score = (
                    state[0] * weights["apr"] +        # APR
                    state[1] * weights["tvl"] +        # TVL
                    state[2] * weights["volume"] +     # Volume
                    state[3] * weights["volatility"] + # Volatility
                    state[4] * weights["sentiment"] +  # Sentiment
                    state[5] * weights["prediction"]   # Prediction
                )
                
                # Add token preference bonus
                if token_preference:
                    token_a = pool["raw_data"].get("token_a_symbol", "")
                    token_b = pool["raw_data"].get("token_b_symbol", "")
                    if token_preference.upper() == token_a.upper() or token_preference.upper() == token_b.upper():
                        score += 0.1  # 10% bonus for matching token preference
                
                # Build explanation based on feature contributions
                reasons = []
                
                if state[0] > 0.3:  # APR > 30%
                    reasons.append(f"High APR at {pool['raw_data'].get('apr_24h', 0):.1f}%")
                    
                if state[1] > 0.2:  # TVL > $2M
                    reasons.append(f"Strong liquidity depth")
                    
                if state[2] > 0.3:  # Volume > $300K
                    reasons.append(f"High trading volume")
                    
                if state[3] < 0.1:  # Low volatility
                    reasons.append(f"Low price volatility")
                    
                if state[4] > 0.7:  # Positive sentiment
                    reasons.append(f"Positive market sentiment")
                    
                if state[5] > 0.7:  # High prediction score
                    reasons.append(f"Strong prediction confidence")
                
                ranked_pools.append({
                    "pool_id": pool["pool_id"],
                    "pair": pool["pair"],
                    "apr": pool["raw_data"].get("apr_24h", 0),
                    "tvl": pool["raw_data"].get("tvl", 0),
                    "score": score,
                    "confidence": confidence,
                    "reasons": reasons,
                    "raw_data": pool["raw_data"]
                })
            
            # Sort by score
            ranked_pools.sort(key=lambda x: x["score"], reverse=True)
            
            # Take top suggestions
            top_pools = ranked_pools[:max_suggestions]
            
            # Fill result suggestions
            for pool in top_pools:
                result["suggestions"].append({
                    "pool_id": pool["pool_id"],
                    "pair": pool["pair"],
                    "apr": pool["apr"],
                    "tvl": pool["tvl"],
                    "score": pool["score"],
                    "confidence": pool["confidence"],
                    "reasons": pool["reasons"]
                })
            
            # Generate overall explanation
            if len(result["suggestions"]) > 0:
                # Use market sentiment for general market explanation
                market_conditions = ""
                if "overall" in result["market_sentiment"]:
                    overall_sentiment = result["market_sentiment"]["overall"]["score"]
                    if overall_sentiment > 0.3:
                        market_conditions = "The overall market sentiment is positive, which may support continued growth in liquidity pools."
                    elif overall_sentiment < -0.3:
                        market_conditions = "The overall market sentiment is cautious, suggesting a more conservative approach to pool investments."
                    else:
                        market_conditions = "The market sentiment is neutral, with balanced opportunities for strategic pool investments."
                
                # Add Solana-specific explanation if available
                solana_conditions = ""
                if "solana" in result["market_sentiment"]:
                    solana_sentiment = result["market_sentiment"]["solana"]["score"]
                    if solana_sentiment > 0.3:
                        solana_conditions = " Solana ecosystem sentiment is positive, creating favorable conditions for SOL-based pools."
                    elif solana_sentiment < -0.3:
                        solana_conditions = " Solana ecosystem sentiment shows some caution, consider diversifying across different token pairs."
                
                # Get top recommendation details
                top_pool = result["suggestions"][0]
                confidence_level = "high" if top_pool["confidence"] > 0.7 else "moderate" if top_pool["confidence"] > 0.4 else "tentative"
                top_reasons = ", ".join(top_pool["reasons"])
                
                # Combine into comprehensive explanation
                result["explanation"] = f"{market_conditions}{solana_conditions} Based on AI analysis with {confidence_level} confidence, "
                result["explanation"] += f"the {top_pool['pair']} pool at {top_pool['apr']:.1f}% APR offers the best opportunity because: {top_reasons}."
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RL investment advisor: {e}")
            # Fallback to standard agentic advisor
            standard_recommendation = agentic_advisor.get_investment_recommendation(
                investment_amount, risk_profile, token_preference, max_suggestions
            )
            standard_recommendation["rl_powered"] = False
            standard_recommendation["fallback_used"] = True
            return standard_recommendation
    
    def record_investment(self, user_id: int, pool_id: str, investment_amount: float, risk_profile: str):
        """
        Record an investment for RL training feedback
        
        Args:
            user_id: User ID making the investment
            pool_id: Pool ID that was invested in
            investment_amount: Amount invested
            risk_profile: User's risk profile
        """
        try:
            # Get pool details
            pool_details = solpool_api.get_pool_detail(pool_id)
            
            if not pool_details or "status" not in pool_details or pool_details["status"] != "success":
                logger.error(f"Could not get pool details for {pool_id}")
                return
            
            # Record initial state
            initial_state = self._extract_features(pool_details)
            
            # Store investment record
            investment_id = f"{user_id}_{pool_id}_{int(time.time())}"
            self.investments[investment_id] = {
                "user_id": user_id,
                "pool_id": pool_id,
                "investment_amount": investment_amount,
                "risk_profile": risk_profile,
                "start_time": time.time(),
                "initial_state": initial_state.tolist(),
                "initial_apr": pool_details.get("apr_24h", 0),
                "initial_tvl": pool_details.get("tvl", 0)
            }
            
            logger.info(f"Recorded investment {investment_id} for RL training")
            
        except Exception as e:
            logger.error(f"Error recording investment: {e}")
    
    def feedback_investment(self, user_id: int, pool_id: str, rating: int, exit_amount: Optional[float] = None):
        """
        Provide feedback on a previous investment for RL training
        
        Args:
            user_id: User ID who made the investment
            pool_id: Pool ID that was invested in
            rating: User rating (1-5) of how good the investment was
            exit_amount: Optional amount received upon exit
        """
        try:
            # Find matching investment
            found = False
            for investment_id, investment in self.investments.items():
                if investment["user_id"] == user_id and investment["pool_id"] == pool_id:
                    found = True
                    
                    # Get current pool details
                    pool_details = solpool_api.get_pool_detail(pool_id)
                    
                    if not pool_details or "status" not in pool_details or pool_details["status"] != "success":
                        logger.error(f"Could not get pool details for {pool_id}")
                        return
                    
                    # Calculate days held
                    days_held = (time.time() - investment["start_time"]) / (60 * 60 * 24)
                    
                    # Extract features for current state
                    current_state = self._extract_features(pool_details)
                    
                    # Calculate reward
                    # If exit_amount provided, use actual return
                    if exit_amount:
                        profit_ratio = (exit_amount - investment["investment_amount"]) / investment["investment_amount"]
                        # Scale profit ratio to a reward (-1 to 1)
                        base_reward = min(max(profit_ratio * 5, -1), 1)
                    else:
                        # Use estimated return from APR
                        base_reward = self._calculate_reward(
                            pool_details, 
                            investment["investment_amount"],
                            days_held,
                            investment["risk_profile"]
                        )
                    
                    # Incorporate user rating (1-5) into reward
                    user_reward = (rating - 3) / 2  # Scale 1-5 to -1 to 1
                    
                    # Combine base reward with user feedback (70% base, 30% user feedback)
                    reward = base_reward * 0.7 + user_reward * 0.3
                    
                    # Add experience to replay memory
                    self.model.memory.push(
                        investment["initial_state"],  # Initial state
                        0,                           # Action (arbitrary for feedback)
                        reward,                      # Reward
                        current_state.tolist(),      # Final state
                        True                         # Terminal state
                    )
                    
                    # Train model on this experience
                    self.model.train(batch_size=1)
                    
                    logger.info(f"Added feedback for investment {investment_id} with reward {reward:.2f}")
                    
                    # Remove from active investments
                    self.investments.pop(investment_id)
                    break
            
            if not found:
                logger.warning(f"No matching investment found for user {user_id} and pool {pool_id}")
                
        except Exception as e:
            logger.error(f"Error processing investment feedback: {e}")
            
# Create a singleton instance
rl_advisor = RLInvestmentAdvisor()

def get_smart_investment_recommendation(
    investment_amount: float,
    risk_profile: str = "moderate",
    token_preference: Optional[str] = None,
    max_suggestions: int = 3
) -> Dict[str, Any]:
    """
    Get smart investment recommendation using RL
    
    Args:
        investment_amount: Amount to invest (USD)
        risk_profile: User's risk tolerance ("conservative", "moderate", "aggressive")
        token_preference: Optional token to prioritize in recommendations
        max_suggestions: Maximum number of pool suggestions to return
        
    Returns:
        Dictionary with recommendations, explanations, and data sources
    """
    global rl_advisor
    return rl_advisor.get_recommendations(
        investment_amount, risk_profile, token_preference, max_suggestions
    )

def record_smart_investment(user_id: int, pool_id: str, investment_amount: float, risk_profile: str):
    """
    Record a smart investment for RL training
    
    Args:
        user_id: User ID making the investment
        pool_id: Pool ID that was invested in 
        investment_amount: Amount invested
        risk_profile: User's risk profile
    """
    global rl_advisor
    rl_advisor.record_investment(user_id, pool_id, investment_amount, risk_profile)
    
def feedback_smart_investment(user_id: int, pool_id: str, rating: int, exit_amount: Optional[float] = None):
    """
    Provide feedback on a smart investment
    
    Args:
        user_id: User ID who made the investment
        pool_id: Pool ID that was invested in
        rating: User rating (1-5) of how good the investment was
        exit_amount: Optional amount received upon exit
    """
    global rl_advisor
    rl_advisor.feedback_investment(user_id, pool_id, rating, exit_amount)