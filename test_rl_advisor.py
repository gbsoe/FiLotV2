#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the RL Investment Advisor using real API data
"""

import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Import the RL advisor to test
from rl_investment_advisor import get_rl_recommendations

def test_investment_recommendations():
    """Test investment recommendations with different risk profiles"""
    
    # Parameters to test
    investment_amount = 1000.0  # $1000 investment
    risk_profiles = ["conservative", "moderate", "aggressive"]
    token_preferences = [None, "SOL", "USDC"]
    
    results = {}
    
    # Test each risk profile
    for risk in risk_profiles:
        results[risk] = {}
        
        # Test with different token preferences
        for token in token_preferences:
            test_name = f"{risk}_{'any' if token is None else token}"
            print(f"\n=== Testing {risk.upper()} risk profile with {token or 'no'} token preference ===")
            
            try:
                # Get recommendations using the RL advisor
                recommendations = get_rl_recommendations(
                    investment_amount=investment_amount,
                    risk_profile=risk,
                    token_preference=token,
                    max_suggestions=3
                )
                
                # Save results for reporting
                results[risk][token or "any"] = recommendations
                
                # Print summary of recommendations
                print(f"Status: {recommendations.get('status', 'unknown')}")
                print(f"RL-powered: {recommendations.get('rl_powered', False)}")
                print(f"Fallback used: {recommendations.get('fallback_used', False)}")
                
                # Display suggested pools
                suggestions = recommendations.get("suggestions", [])
                if suggestions:
                    print(f"\nTop {len(suggestions)} recommended pools:")
                    for i, suggestion in enumerate(suggestions):
                        print(f"{i+1}. {suggestion.get('pair')} - APR: {suggestion.get('apr', 0):.2f}% - Score: {suggestion.get('score', 0):.4f}")
                        reasons = suggestion.get('reasons', [])
                        if reasons:
                            print(f"   Reasons: {', '.join(reasons)}")
                else:
                    print("No pool suggestions found.")
                
                # Display explanation
                explanation = recommendations.get("explanation", "")
                if explanation:
                    print(f"\nExplanation: {explanation}")
                    
                # Display market sentiment data
                market_sentiment = recommendations.get("market_sentiment", {})
                if market_sentiment:
                    print("\nMarket Sentiment Data:")
                    if "overall" in market_sentiment:
                        print(f"Overall: {market_sentiment['overall'].get('score', 0):.2f}")
                    if "solana" in market_sentiment:
                        print(f"Solana: {market_sentiment['solana'].get('score', 0):.2f}")
                        
            except Exception as e:
                logger.error(f"Error testing {test_name}: {str(e)}")
                results[risk][token or "any"] = {"error": str(e)}
    
    # Save all results to a file for analysis
    with open("rl_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("\nTest results saved to rl_test_results.json")
    return results

def main():
    """Main test function"""
    print("Testing RL Investment Advisor with Real API Data")
    test_investment_recommendations()

if __name__ == "__main__":
    main()