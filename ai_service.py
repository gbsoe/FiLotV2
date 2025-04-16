#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DeepSeek AI integration for the Telegram cryptocurrency pool bot
"""

import os
import logging
import aiohttp
import json
from typing import Optional

logger = logging.getLogger(__name__)

class DeepSeekAI:
    """Client for interacting with DeepSeek AI API."""
    
    def __init__(self, api_key: str):
        """
        Initialize the DeepSeek AI client.
        
        Args:
            api_key: API key for DeepSeek AI
        """
        self.api_key = api_key
        self.api_url = "https://api.deepseek.com/v1"  # Update with actual DeepSeek API URL
        self.session = None
        
    async def _ensure_session(self):
        """Ensure that the aiohttp session is created."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            
    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            
    async def check_status(self) -> bool:
        """
        Check if the DeepSeek AI API is available.
        
        Returns:
            bool: True if the API is available, False otherwise
        """
        if not self.api_key:
            return False
            
        try:
            await self._ensure_session()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Simple endpoint check (this would need to be updated with actual DeepSeek API endpoints)
            async with self.session.get(
                f"{self.api_url}/models", 
                headers=headers
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Error checking DeepSeek AI API status: {e}")
            return False
            
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response using DeepSeek AI.
        
        Args:
            prompt: User's prompt/question
            
        Returns:
            AI-generated response as a string
        """
        if not self.api_key:
            return "AI features are currently unavailable."
            
        try:
            await self._ensure_session()
            
            # Enhance the prompt with context
            enhanced_prompt = (
                "You are a helpful assistant specializing in cryptocurrency and DeFi. "
                "Provide accurate, educational information about crypto pools, liquidity providing, "
                "yield farming, and investment strategies. Keep answers concise and informative. "
                f"User question: {prompt}"
            )
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Payload for DeepSeek API (adjust as needed for actual API)
            payload = {
                "model": "deepseek-chat",  # Update with actual model name
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant specializing in cryptocurrency."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            async with self.session.post(
                f"{self.api_url}/chat/completions", 
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to generate AI response: {response.status}")
                    error_text = await response.text()
                    logger.error(f"API error: {error_text}")
                    return "Sorry, I encountered an error while processing your request."
                
                response_data = await response.json()
                
                # Extract the generated text (adjust based on actual API response format)
                response_text = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                if not response_text:
                    return "Sorry, I couldn't generate a response."
                    
                return response_text
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "Sorry, an error occurred while processing your request."
            
    async def classify_message(self, message: str) -> str:
        """
        Classify a user message to determine intent.
        
        Args:
            message: User's message text
            
        Returns:
            Classification result (e.g., "pool_inquiry", "price_question", etc.)
        """
        if not self.api_key:
            return "unknown"
            
        try:
            await self._ensure_session()
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",  # Update with actual model name
                "messages": [
                    {"role": "system", "content": "Classify the following message into one of these categories: pool_inquiry, price_question, investment_advice, general_crypto, other. Respond with only the category name."},
                    {"role": "user", "content": message}
                ],
                "temperature": 0.3,
                "max_tokens": 20
            }
            
            async with self.session.post(
                f"{self.api_url}/chat/completions", 
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to classify message: {response.status}")
                    return "unknown"
                
                response_data = await response.json()
                
                # Extract the classification (adjust based on actual API response format)
                classification = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Normalize and clean the classification
                classification = classification.strip().lower()
                
                # Map to known categories
                known_categories = [
                    "pool_inquiry", "price_question", "investment_advice", 
                    "general_crypto", "other"
                ]
                
                if classification in known_categories:
                    return classification
                else:
                    return "unknown"
                
        except Exception as e:
            logger.error(f"Error classifying message: {e}")
            return "unknown"
