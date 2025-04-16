#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Anthropic Claude AI integration for specialized financial advice
"""

import os
import logging
import aiohttp
import json
from typing import Optional, Dict, List, Any, Tuple
import anthropic
from anthropic import Anthropic

# Configure logging
logger = logging.getLogger(__name__)

class AnthropicAI:
    """Client for interacting with Anthropic Claude API for financial advice."""
    
    def __init__(self, api_key: str):
        """
        Initialize the Anthropic Claude AI client.
        
        Args:
            api_key: API key for Anthropic API
        """
        self.api_key = api_key
        # Note that the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        self.model = "claude-3-5-sonnet-20241022"  
        self.client = None if not api_key else Anthropic(api_key=api_key)
        
    async def get_financial_advice(self, 
                                  user_query: str, 
                                  pool_data: Optional[List[Dict[str, Any]]] = None,
                                  risk_profile: str = "moderate",
                                  investment_horizon: str = "medium") -> str:
        """
        Generate specialized financial advice using Anthropic Claude.
        
        Args:
            user_query: User's financial question
            pool_data: Optional cryptocurrency pool data for context
            risk_profile: User's risk tolerance (conservative, moderate, aggressive)
            investment_horizon: User's investment timeframe (short, medium, long)
            
        Returns:
            AI-generated financial advice as a string
        """
        if not self.api_key or not self.client:
            return "Financial advice features are currently unavailable."
            
        try:
            # Prepare pool data context if available
            pool_context = ""
            if pool_data and len(pool_data) > 0:
                pool_context = "\\nCurrent pool data available:\\n"
                for i, pool in enumerate(pool_data[:5], 1):  # Limit to 5 pools for context
                    pair = f"{pool.get('token_a_symbol')}-{pool.get('token_b_symbol')}"
                    apr = pool.get('apr_24h', 0)
                    tvl = pool.get('tvl', 0)
                    pool_context += f"{i}. {pair}: APR {apr:.2f}%, TVL ${tvl:,.2f}\\n"
            
            # Create system prompt with financial expertise
            system_prompt = f"""
            You are a sophisticated cryptocurrency and DeFi financial advisor with expertise in liquidity pools, yield farming, and investment strategies.
            
            Current context:
            - User's risk profile: {risk_profile}
            - Investment horizon: {investment_horizon}
            {pool_context}
            
            Guidelines for providing financial advice:
            1. Analyze questions thoroughly and provide detailed, actionable financial insights
            2. Balance educational content with practical advice
            3. Always consider risk management and diversification principles
            4. Explain the concept of impermanent loss when discussing liquidity pools
            5. Structure your answers with clear sections and bullet points where appropriate
            6. Always include a brief disclaimer about cryptocurrency investment risks
            7. When recommending strategies, consider the user's risk profile and time horizon
            8. Use professional financial terminology but explain complex concepts
            9. Keep responses concise and focused on the specific question
            10. Avoid making specific price predictions or guarantees of returns
            
            Respond directly to the user's query without repeating the query or saying "as a financial advisor" or similar phrases.
            """
            
            # Generate the response
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                max_tokens=1024,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": user_query}
                ]
            )
            
            # Extract and return the advice
            financial_advice = response.content[0].text if response.content else "I couldn't generate financial advice at this time."
            return financial_advice
                
        except Exception as e:
            logger.error(f"Error generating financial advice: {e}")
            return "Sorry, an error occurred while generating financial advice. Please try again later."
            
    async def assess_investment_risk(self, pool_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the risk level of a specific liquidity pool investment.
        
        Args:
            pool_data: Data about the pool to assess
            
        Returns:
            Dictionary with risk assessment and explanations
        """
        if not self.api_key or not self.client:
            return {"risk_level": "unknown", "explanation": "Risk assessment is currently unavailable."}
            
        try:
            # Prepare pool context as a string
            pair = f"{pool_data.get('token_a_symbol')}-{pool_data.get('token_b_symbol')}"
            apr = pool_data.get('apr_24h', 0)
            apr_7d = pool_data.get('apr_7d', 0)
            apr_30d = pool_data.get('apr_30d', 0)
            tvl = pool_data.get('tvl', 0)
            fee = pool_data.get('fee', 0)
            volume_24h = pool_data.get('volume_24h', 0)
            
            # Create the prompt
            risk_assessment_prompt = f"""
            Analyze the risk profile of this cryptocurrency liquidity pool and provide a detailed assessment:
            
            Pool Pair: {pair}
            Current APR (24h): {apr:.2f}%
            7-Day APR: {apr_7d:.2f}%
            30-Day APR: {apr_30d:.2f}%
            Total Value Locked: ${tvl:,.2f}
            Fee Rate: {fee:.2f}%
            24h Trading Volume: ${volume_24h:,.2f}
            
            Provide a risk assessment with:
            1. Overall risk level (Low, Medium, High, Very High)
            2. Key risk factors specific to this pool
            3. Potential impermanent loss considerations
            4. Volatility assessment of the token pair
            5. Liquidity concerns
            
            Format the response as JSON with fields: risk_level, key_factors, impermanent_loss, volatility, liquidity, explanation
            """
            
            # Generate the assessment
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.3,  # Lower temperature for more consistent analysis
                messages=[
                    {"role": "user", "content": risk_assessment_prompt}
                ]
            )
            
            # Parse the JSON response
            response_text = response.content[0].text if response.content else ""
            
            # Try to extract JSON from the response text
            try:
                # Find JSON block in the text if it's wrapped in backticks
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    assessment = json.loads(json_str)
                    
                    # Ensure all expected fields are present
                    required_fields = ["risk_level", "key_factors", "impermanent_loss", 
                                      "volatility", "liquidity", "explanation"]
                    
                    for field in required_fields:
                        if field not in assessment:
                            assessment[field] = "Not provided"
                            
                    return assessment
                else:
                    return {
                        "risk_level": "medium",
                        "explanation": "Could not generate detailed risk assessment.",
                        "key_factors": "N/A",
                        "impermanent_loss": "N/A",
                        "volatility": "N/A",
                        "liquidity": "N/A"
                    }
            except json.JSONDecodeError:
                logger.error("Failed to parse risk assessment JSON response")
                return {
                    "risk_level": "medium",
                    "explanation": "Could not generate detailed risk assessment.",
                    "key_factors": "N/A",
                    "impermanent_loss": "N/A",
                    "volatility": "N/A",
                    "liquidity": "N/A"
                }
                
        except Exception as e:
            logger.error(f"Error assessing investment risk: {e}")
            return {
                "risk_level": "unknown",
                "explanation": "An error occurred during risk assessment.",
                "key_factors": "N/A",
                "impermanent_loss": "N/A",
                "volatility": "N/A",
                "liquidity": "N/A"
            }
    
    async def generate_investment_strategy(self, 
                                         investment_amount: float,
                                         risk_profile: str = "moderate",
                                         investment_horizon: str = "medium",
                                         pool_data: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Generate a personalized investment strategy based on user parameters.
        
        Args:
            investment_amount: Amount to invest in USD
            risk_profile: User's risk tolerance (conservative, moderate, aggressive)
            investment_horizon: User's investment timeframe (short, medium, long)
            pool_data: Optional cryptocurrency pool data for context
            
        Returns:
            Detailed investment strategy as a string
        """
        if not self.api_key or not self.client:
            return "Investment strategy generation is currently unavailable."
            
        try:
            # Prepare pool data context if available
            pool_context = ""
            if pool_data and len(pool_data) > 0:
                pool_context = "\\nAvailable liquidity pools:\\n"
                for i, pool in enumerate(pool_data[:7], 1):  # Use up to 7 pools
                    pair = f"{pool.get('token_a_symbol')}-{pool.get('token_b_symbol')}"
                    apr = pool.get('apr_24h', 0)
                    tvl = pool.get('tvl', 0)
                    fee = pool.get('fee', 0)
                    pool_context += f"{i}. {pair}: APR {apr:.2f}%, TVL ${tvl:,.2f}, Fee {fee:.2f}%\\n"
            
            # Define strategy parameters based on risk profile
            parameters = {
                "conservative": {
                    "stable_allocation": "60-70%",
                    "high_yield_allocation": "10-20%",
                    "experimental_allocation": "0-5%",
                    "pool_preference": "Stable pairs (USDC-USDT, ETH-stETH)"
                },
                "moderate": {
                    "stable_allocation": "40-50%",
                    "high_yield_allocation": "30-40%",
                    "experimental_allocation": "10-20%",
                    "pool_preference": "Balanced mix of stable and higher APR pools"
                },
                "aggressive": {
                    "stable_allocation": "20-30%",
                    "high_yield_allocation": "40-50%",
                    "experimental_allocation": "20-30%",
                    "pool_preference": "Higher APR pools with greater risk tolerance"
                }
            }
            
            # Get parameters for the selected risk profile
            risk_params = parameters.get(risk_profile.lower(), parameters["moderate"])
            
            # Create the strategy prompt
            strategy_prompt = f"""
            Generate a detailed cryptocurrency liquidity pool investment strategy with these parameters:
            
            Investment Amount: ${investment_amount:,.2f}
            Risk Profile: {risk_profile}
            Investment Horizon: {investment_horizon}
            
            Strategy Parameters:
            - Stable allocation: {risk_params["stable_allocation"]}
            - High-yield allocation: {risk_params["high_yield_allocation"]}
            - Experimental allocation: {risk_params["experimental_allocation"]}
            - Pool preference: {risk_params["pool_preference"]}
            
            {pool_context}
            
            Provide:
            1. A detailed allocation strategy with specific percentages
            2. Recommended entry strategy (DCA vs. lump sum)
            3. Risk management approaches
            4. How to monitor and when to adjust the strategy
            5. Impermanent loss considerations
            6. Tax implications to be aware of
            
            Structure this as a professional investment strategy document with clear sections and actionable advice.
            Include a brief risk disclaimer at the end.
            """
            
            # Generate the strategy
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1536,  # Longer response for detailed strategy
                temperature=0.7,
                messages=[
                    {"role": "user", "content": strategy_prompt}
                ]
            )
            
            # Extract and return the strategy
            strategy = response.content[0].text if response.content else "I couldn't generate an investment strategy at this time."
            return strategy
                
        except Exception as e:
            logger.error(f"Error generating investment strategy: {e}")
            return "Sorry, an error occurred while generating your investment strategy. Please try again later."
            
    async def explain_financial_concept(self, concept: str) -> str:
        """
        Provide detailed explanation of a DeFi or crypto financial concept.
        
        Args:
            concept: The financial concept to explain
            
        Returns:
            Detailed explanation as a string
        """
        if not self.api_key or not self.client:
            return "Financial concept explanations are currently unavailable."
            
        try:
            # Create the explanation prompt
            explanation_prompt = f"""
            Provide a comprehensive explanation of the DeFi/cryptocurrency concept: {concept}
            
            Include:
            1. Clear definition and core principles
            2. How it works in practical terms
            3. Main advantages and disadvantages
            4. Real-world applications in DeFi
            5. Compare to traditional finance equivalents if applicable
            6. Key risks or considerations
            
            Use simple language where possible but include necessary technical terms with explanations.
            Format with clear headings and bullet points where appropriate.
            Keep the explanation educational and actionable for cryptocurrency investors.
            """
            
            # Generate the explanation
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0.5,
                messages=[
                    {"role": "user", "content": explanation_prompt}
                ]
            )
            
            # Extract and return the explanation
            explanation = response.content[0].text if response.content else "I couldn't generate an explanation at this time."
            return explanation
                
        except Exception as e:
            logger.error(f"Error explaining financial concept: {e}")
            return "Sorry, an error occurred while generating the explanation. Please try again later."

    async def classify_financial_question(self, question: str) -> str:
        """
        Classify a financial question to determine the best response approach.
        
        Args:
            question: User's financial question
            
        Returns:
            Classification category (e.g., "pool_advice", "general_question", etc.)
        """
        if not self.api_key or not self.client:
            return "general"
            
        try:
            # Create the classification prompt
            classification_prompt = """
            Classify the following cryptocurrency/DeFi question into exactly ONE of these categories:
            
            1. pool_advice - Questions about specific liquidity pools or farming strategies
            2. token_question - Questions about specific tokens or cryptocurrencies
            3. risk_assessment - Questions about risks, security, or safety
            4. strategy_help - Questions about investment strategies or approaches
            5. defi_explanation - Questions seeking explanation of DeFi concepts
            6. market_prediction - Questions about price movements or market trends
            7. tax_question - Questions about taxes or regulatory issues
            8. platform_question - Questions about specific DeFi platforms
            9. general - General questions that don't fit other categories
            
            Respond with ONLY the category name, nothing else.
            
            Question: 
            """
            
            # Generate the classification
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,  # Very short response needed
                temperature=0.2,  # Low temperature for consistent results
                messages=[
                    {"role": "user", "content": classification_prompt + question}
                ]
            )
            
            # Extract and clean the classification
            classification = response.content[0].text.strip().lower() if response.content else "general"
            
            # Normalize to known categories
            known_categories = [
                "pool_advice", "token_question", "risk_assessment", "strategy_help",
                "defi_explanation", "market_prediction", "tax_question", "platform_question", "general"
            ]
            
            if classification in known_categories:
                return classification
            else:
                return "general"
                
        except Exception as e:
            logger.error(f"Error classifying financial question: {e}")
            return "general"