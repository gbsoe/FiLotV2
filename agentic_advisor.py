#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Agentic investment advisor for FiLot Telegram bot
Combines technical pool data with market sentiment to provide intelligent investment recommendations
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

import solpool_api_client as solpool_api
import filotsense_api_client as sentiment_api

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Risk profile definitions
RISK_PROFILES = {
    "conservative": {
        "min_tvl": 2000000,  # $2M minimum TVL for stability
        "max_apr": 30,       # Cap APR to avoid highly speculative pools
        "min_sentiment": -0.1, # Avoid very negative sentiment
        "min_prediction": 60, # Reasonable prediction confidence
        "description": "Prioritizes stable pools with moderate returns and lower risk"
    },
    "moderate": {
        "min_tvl": 1000000,  # $1M minimum TVL
        "max_apr": 50,       # Higher APR tolerance
        "min_sentiment": -0.3, # Can accept some negative sentiment
        "min_prediction": 50, # Average prediction confidence
        "description": "Balanced approach between growth and stability"
    },
    "aggressive": {
        "min_tvl": 500000,   # $500K minimum TVL
        "max_apr": 100,      # High APR tolerance for speculative pools
        "min_sentiment": -0.5, # Can accept more negative sentiment for high returns
        "min_prediction": 40, # Lower prediction confidence threshold
        "description": "Prioritizes high returns with higher risk tolerance"
    }
}

def get_investment_recommendation(
    investment_amount: float,
    risk_profile: str = "moderate",
    token_preference: Optional[str] = None,
    max_suggestions: int = 3
) -> Dict[str, Any]:
    """
    Generate an intelligent investment recommendation based on multiple data sources
    
    Args:
        investment_amount: Amount to invest (USD)
        risk_profile: User's risk tolerance ("conservative", "moderate", "aggressive")
        token_preference: Optional token to prioritize in recommendations
        max_suggestions: Maximum number of pool suggestions to return
        
    Returns:
        Dictionary with recommendations, explanations, and data sources
    """
    try:
        # Validate risk profile
        if risk_profile not in RISK_PROFILES:
            risk_profile = "moderate"  # Default to moderate if invalid
        
        profile_config = RISK_PROFILES[risk_profile]
        logger.info(f"Generating recommendation for {risk_profile} profile with ${investment_amount} investment amount")
        
        # Initialize result structure
        result = {
            "status": "success",
            "investment_amount": investment_amount,
            "risk_profile": risk_profile,
            "token_preference": token_preference,
            "suggestions": [],
            "market_sentiment": {},
            "explanation": "",
            "fallback_used": False,
            "action": "invest"  # Default recommendation action
        }
        
        # Get potential pools based on risk profile
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
        
        # Get predictions if available
        predicted_pools = solpool_api.get_predictions(min_score=profile_config["min_prediction"], limit=10)
        if predicted_pools and len(predicted_pools) > 0:
            # Convert predictions to pool format for scoring
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
        
        # Get market sentiment for common tokens
        common_tokens = ["SOL", "USDC", "BTC", "ETH", "BONK", "JTO"]
        sentiment_data = {}
        
        try:
            all_sentiment = sentiment_api.get_sentiment_data()
            if all_sentiment.get("status") == "success" and all_sentiment.get("sentiment"):
                for token in common_tokens:
                    if token in all_sentiment["sentiment"]:
                        sentiment_data[token] = {
                            "score": all_sentiment["sentiment"][token].get("score", 0),
                            "timestamp": all_sentiment["sentiment"][token].get("timestamp", "")
                        }
            
            # If token preference specified, prioritize that sentiment
            if token_preference and token_preference.upper() in sentiment_data:
                result["market_sentiment"]["token_preference"] = sentiment_data[token_preference.upper()]
            
            # Add overall market sentiment (average of BTC and ETH as indicators)
            if "BTC" in sentiment_data and "ETH" in sentiment_data:
                overall_score = (sentiment_data["BTC"]["score"] + sentiment_data["ETH"]["score"]) / 2
                result["market_sentiment"]["overall"] = {"score": overall_score}
            
            # Add Solana ecosystem sentiment
            if "SOL" in sentiment_data:
                result["market_sentiment"]["solana"] = sentiment_data["SOL"]
            
            logger.info(f"Retrieved sentiment data for {len(sentiment_data)} tokens")
        except Exception as e:
            logger.error(f"Error getting sentiment data: {e}")
            # Proceed without sentiment data
        
        # No candidate pools found, use fallback recommendation
        if not candidate_pools:
            result["fallback_used"] = True
            result["status"] = "partial"
            result["explanation"] = "Unable to retrieve real-time pool data. Using default recommendations."
            
            # Create fallback suggestions based on risk profile
            if risk_profile == "conservative":
                result["suggestions"] = [
                    {"pair": "SOL-USDC", "apr": 8.5, "tvl": 4500000, "description": "Major pair with stable returns"},
                    {"pair": "ETH-USDC", "apr": 6.2, "tvl": 3800000, "description": "Established pair with low volatility"}
                ]
            elif risk_profile == "aggressive":
                result["suggestions"] = [
                    {"pair": "BONK-SOL", "apr": 35.8, "tvl": 780000, "description": "High volatility meme token pair"},
                    {"pair": "JTO-SOL", "apr": 28.4, "tvl": 950000, "description": "New token with growth potential"}
                ]
            else:  # moderate
                result["suggestions"] = [
                    {"pair": "SOL-USDT", "apr": 12.5, "tvl": 2800000, "description": "Balanced risk-reward ratio"},
                    {"pair": "RAY-SOL", "apr": 18.7, "tvl": 1200000, "description": "DEX token with solid fundamentals"}
                ]
            
            return result
        
        # Score and rank candidate pools
        scored_pools = []
        
        for pool in candidate_pools:
            # Skip duplicates by ID
            if any(p.get("pool_id") == pool.get("id") for p in scored_pools):
                continue
                
            # Get token symbols
            token_a = pool.get("token_a_symbol", "")
            token_b = pool.get("token_b_symbol", "")
            
            if not token_a or not token_b:
                continue
            
            # Apply risk profile filters
            tvl = pool.get("tvl", 0)
            apr = pool.get("apr_24h", 0)
            
            # Skip pools that don't meet TVL minimum
            if tvl < profile_config["min_tvl"]:
                continue
                
            # Skip pools with APR beyond max for risk profile
            if apr > profile_config["max_apr"]:
                continue
                
            # Initialize score components
            pool_score = 0
            score_reasons = []
            
            # Get sentiment score for tokens in pool (if available)
            token_a_sentiment = 0
            token_b_sentiment = 0
            
            if token_a in sentiment_data:
                token_a_sentiment = sentiment_data[token_a]["score"]
            if token_b in sentiment_data:
                token_b_sentiment = sentiment_data[token_b]["score"]
                
            # Calculate average sentiment score for the pool
            avg_sentiment = 0
            if token_a_sentiment or token_b_sentiment:
                avg_sentiment = (token_a_sentiment + token_b_sentiment) / 2 if token_a_sentiment and token_b_sentiment else token_a_sentiment or token_b_sentiment
                
            # Skip pools with very negative sentiment based on risk profile
            if avg_sentiment < profile_config["min_sentiment"]:
                continue
                
            # 1. Base scoring: APR (30% weight)
            # Higher APR is better, but with diminishing returns
            apr_score = min(10, apr / 5)  # Cap at 10 points
            pool_score += apr_score * 0.3
            
            if apr > 20:
                score_reasons.append(f"High APR at {apr:.1f}%")
                
            # 2. TVL scoring (20% weight)
            # Higher TVL means more stability
            tvl_score = min(10, tvl / 500000)  # Cap at 10 points
            pool_score += tvl_score * 0.2
            
            if tvl > 2000000:
                score_reasons.append("Strong liquidity depth")
                
            # 3. Prediction score if available (25% weight)
            prediction_score = pool.get("prediction_score", 0)
            if prediction_score > 0:
                pred_score = min(10, prediction_score / 10)  # Cap at 10 points
                pool_score += pred_score * 0.25
                
                if prediction_score > 70:
                    score_reasons.append("High prediction confidence")
                
            # 4. Sentiment analysis scoring (25% weight)
            if avg_sentiment:
                # Map sentiment (-1 to 1) to 0-10 scale
                sentiment_score = (avg_sentiment + 1) * 5
                pool_score += sentiment_score * 0.25
                
                if avg_sentiment > 0.3:
                    score_reasons.append("Positive market sentiment")
                elif avg_sentiment < -0.3:
                    score_reasons.append("Caution: Negative sentiment")
                    
            # 5. Token preference bonus (if applicable)
            if token_preference and (token_preference.upper() == token_a or token_preference.upper() == token_b):
                pool_score += 2  # Bonus points for matching token preference
                score_reasons.append(f"Includes preferred {token_preference} token")
                
            # Prepare detailed pool data for scoring
            scored_pool = {
                "pool_id": pool.get("id", ""),
                "pair": f"{token_a}/{token_b}",
                "apr": apr,
                "tvl": tvl,
                "score": pool_score,
                "prediction_score": prediction_score,
                "sentiment_score": avg_sentiment,
                "reasons": score_reasons,
                "raw_data": pool  # Include raw data for further processing
            }
            
            scored_pools.append(scored_pool)
            
        # Sort scored pools by score descending
        scored_pools = sorted(scored_pools, key=lambda x: x["score"], reverse=True)
        
        # Take top suggestions based on max_suggestions parameter
        top_pools = scored_pools[:max_suggestions]
        
        # Fill in result suggestions from top pools
        for pool in top_pools:
            result["suggestions"].append({
                "pool_id": pool["pool_id"],
                "pair": pool["pair"],
                "apr": pool["apr"],
                "tvl": pool["tvl"],
                "score": pool["score"],
                "prediction_score": pool.get("prediction_score", 0),
                "sentiment_score": pool.get("sentiment_score", 0),
                "reasons": pool.get("reasons", [])
            })
        
        # Generate overall explanation based on market conditions and top pool
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
            top_reasons = ", ".join(top_pool.get("reasons", ["Good balance of risk and reward"]))
            
            # Combine into comprehensive explanation
            result["explanation"] = f"{market_conditions}{solana_conditions} Based on your {risk_profile} risk profile and our analysis, "
            result["explanation"] += f"the {top_pool['pair']} pool at {top_pool['apr']:.1f}% APR offers the best opportunity because: {top_reasons}."
        
        return result
            
    except Exception as e:
        logger.error(f"Error generating investment recommendation: {e}")
        # Provide fallback response
        return {
            "status": "error",
            "investment_amount": investment_amount,
            "risk_profile": risk_profile,
            "suggestions": [
                {"pair": "SOL-USDC", "apr": 10.5, "tvl": 3000000, "description": "Default stable recommendation"}
            ],
            "explanation": "Unable to generate personalized recommendations at this time. Here's a generally stable option.",
            "fallback_used": True
        }

def should_exit_position(
    pool_id: str,
    entry_apr: float,
    entry_time_days: int,
    risk_profile: str = "moderate"
) -> Dict[str, Any]:
    """
    Determine if a user should exit a position based on current conditions
    
    Args:
        pool_id: Pool identifier
        entry_apr: APR at time of entry
        entry_time_days: Days since position was entered
        risk_profile: User's risk profile
        
    Returns:
        Dictionary with exit recommendation and explanation
    """
    try:
        # Initialize result
        result = {
            "status": "success",
            "pool_id": pool_id,
            "entry_apr": entry_apr,
            "current_apr": 0,
            "apr_change": 0,
            "apr_change_pct": 0,
            "entry_time_days": entry_time_days,
            "action": "hold",  # Default action
            "explanation": "",
            "risk_profile": risk_profile,
            "market_conditions": {}
        }
        
        # Get current pool details
        pool_details = solpool_api.get_pool_detail(pool_id)
        
        # If we can't get pool details, recommend holding
        if not pool_details or pool_details.get("status") != "success":
            result["status"] = "partial"
            result["action"] = "hold"
            result["explanation"] = "Unable to retrieve current pool data. Recommend holding position until data is available."
            return result
            
        # Get current APR and calculate change
        current_apr = pool_details.get("apr_24h", 0)
        result["current_apr"] = current_apr
        
        apr_change = current_apr - entry_apr
        result["apr_change"] = apr_change
        
        # Calculate percentage change
        if entry_apr > 0:
            apr_change_pct = (apr_change / entry_apr) * 100
            result["apr_change_pct"] = apr_change_pct
        else:
            apr_change_pct = 0
            
        # Get market sentiment data
        try:
            # Get token pair from pool details
            token_a = pool_details.get("token_a_symbol", "")
            token_b = pool_details.get("token_b_symbol", "")
            
            # Get sentiment for these tokens if available
            all_sentiment = sentiment_api.get_sentiment_data()
            
            if all_sentiment.get("status") == "success" and all_sentiment.get("sentiment"):
                # Add token-specific sentiment
                if token_a and token_a in all_sentiment["sentiment"]:
                    result["market_conditions"][token_a] = all_sentiment["sentiment"][token_a]
                    
                if token_b and token_b in all_sentiment["sentiment"]:
                    result["market_conditions"][token_b] = all_sentiment["sentiment"][token_b]
                    
                # Add overall market sentiment (average of BTC and ETH)
                if "BTC" in all_sentiment["sentiment"] and "ETH" in all_sentiment["sentiment"]:
                    btc_score = all_sentiment["sentiment"]["BTC"].get("score", 0)
                    eth_score = all_sentiment["sentiment"]["ETH"].get("score", 0)
                    overall_score = (btc_score + eth_score) / 2
                    
                    result["market_conditions"]["overall"] = {
                        "score": overall_score,
                        "description": "Overall market sentiment"
                    }
        except Exception as e:
            logger.error(f"Error getting sentiment data for exit recommendation: {e}")
            # Proceed without sentiment data
        
        # Make decision logic based on risk profile
        # 1. Conservative investors prioritize protecting capital
        # 2. Moderate investors balance risks and rewards
        # 3. Aggressive investors willing to hold through volatility for better returns
        
        # Decision factors based on risk profile
        exit_thresholds = {
            "conservative": {
                "apr_drop_pct": -15,      # Exit if APR drops by 15%
                "min_hold_days": 5,       # Minimum days to hold before considering exit
                "sentiment_threshold": -0.2 # Exit if sentiment becomes negative
            },
            "moderate": {
                "apr_drop_pct": -30,      # Exit if APR drops by 30%
                "min_hold_days": 3,       # Minimum days to hold before considering exit
                "sentiment_threshold": -0.4 # More tolerance for negative sentiment
            },
            "aggressive": {
                "apr_drop_pct": -50,      # Exit if APR drops by 50%
                "min_hold_days": 1,       # Minimum days to hold before considering exit
                "sentiment_threshold": -0.6 # High tolerance for negative sentiment
            }
        }
        
        # Default to moderate if invalid risk profile
        if risk_profile not in exit_thresholds:
            risk_profile = "moderate"
            
        threshold = exit_thresholds[risk_profile]
        
        # Check exit conditions and build explanation
        exit_reasons = []
        hold_reasons = []
        
        # Check APR change
        if apr_change_pct <= threshold["apr_drop_pct"]:
            exit_reasons.append(f"APR has dropped significantly ({apr_change_pct:.1f}%)")
        else:
            if apr_change > 0:
                hold_reasons.append(f"APR has increased by {apr_change_pct:.1f}%")
            else:
                hold_reasons.append(f"APR change ({apr_change_pct:.1f}%) is within acceptable range")
                
        # Check sentiment if available
        token_sentiment = 0
        if token_a in result["market_conditions"]:
            token_sentiment += result["market_conditions"][token_a].get("score", 0)
            
        if token_b in result["market_conditions"]:
            token_sentiment += result["market_conditions"][token_b].get("score", 0)
            
        # Average sentiment if we have data for both tokens
        if token_a in result["market_conditions"] and token_b in result["market_conditions"]:
            token_sentiment /= 2
            
        if token_sentiment < threshold["sentiment_threshold"]:
            exit_reasons.append(f"Market sentiment for this pool is negative")
        elif token_sentiment > 0.3:
            hold_reasons.append(f"Positive market sentiment for this pool")
            
        # Check minimum hold time
        if entry_time_days < threshold["min_hold_days"]:
            hold_reasons.append(f"Position recently entered, minimum hold time ({threshold['min_hold_days']} days) not yet reached")
            
        # Make final decision 
        if len(exit_reasons) > 0 and entry_time_days >= threshold["min_hold_days"]:
            result["action"] = "exit"
            reason_text = ", ".join(exit_reasons)
            result["explanation"] = f"Recommend exiting position because: {reason_text}."
        else:
            result["action"] = "hold"
            reason_text = ", ".join(hold_reasons) if hold_reasons else "Current conditions favorable for continued holding"
            result["explanation"] = f"Recommend holding position because: {reason_text}."
            
        return result
        
    except Exception as e:
        logger.error(f"Error generating exit recommendation: {e}")
        # Fallback to conservative recommendation - hold
        return {
            "status": "error",
            "pool_id": pool_id,
            "entry_apr": entry_apr,
            "current_apr": 0,
            "apr_change": 0,
            "apr_change_pct": 0,
            "entry_time_days": entry_time_days,
            "action": "hold",
            "explanation": "Unable to analyze current pool conditions. Recommend holding position until analysis is available.",
            "risk_profile": risk_profile,
            "market_conditions": {}
        }