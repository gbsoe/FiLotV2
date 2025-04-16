#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Security safeguards for the Telegram cryptocurrency pool bot
"""

import re
import time
import random
import logging
import datetime
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes
import db_utils

# Configure logging
logger = logging.getLogger(__name__)

# Constants for rate limiting
MAX_MESSAGES_PER_MINUTE = 20
MAX_COMMANDS_PER_MINUTE = 10
RATE_LIMIT_RESET_TIME = 60  # seconds

# Constants for spam detection
SPAM_SCORE_THRESHOLD = 10
SPAM_RESET_INTERVAL = 3600  # 1 hour in seconds
SPAM_TRIGGERS = [
    (r'(https?://\S+)', 2),  # URLs
    (r'(@\w+)', 1),  # Mentions
    (r'(/\w+)', 0.5),  # Commands
    (r'[A-Z]{10,}', 3),  # ALL CAPS text
    (r'(.)\1{5,}', 2),  # Repeated characters
    (r'\b(crypto|token|coin|ico|airdrop|free|money|profit|invest|earn|mining)\b', 0.5),  # Common crypto spam words
]

# URL blocklist patterns
SUSPICIOUS_URL_PATTERNS = [
    r'bit\.ly',
    r'tinyurl\.com',
    r'goo\.gl',
    r't\.co',
    r'crypto[a-z]*\.io',
    r'airdrop',
    r'free.*token',
    r'ico.*sale',
    r'mining.*profit',
]

class RateLimiter:
    """Rate limiter for messages and commands."""
    
    def __init__(self):
        self.user_message_counts: Dict[int, List[float]] = {}  # user_id -> list of message timestamps
        self.user_command_counts: Dict[int, List[float]] = {}  # user_id -> list of command timestamps
    
    def check_rate_limit(self, user_id: int, is_command: bool = False) -> bool:
        """
        Check if a user has exceeded their rate limit.
        
        Args:
            user_id: Telegram user ID
            is_command: Whether this is a command
            
        Returns:
            True if user is within rate limit, False if exceeded
        """
        current_time = time.time()
        
        if is_command:
            # Handle command rate limiting
            if user_id not in self.user_command_counts:
                self.user_command_counts[user_id] = []
            
            # Remove timestamps older than the reset time
            self.user_command_counts[user_id] = [
                t for t in self.user_command_counts[user_id]
                if current_time - t < RATE_LIMIT_RESET_TIME
            ]
            
            # Check if command count exceeds limit
            if len(self.user_command_counts[user_id]) >= MAX_COMMANDS_PER_MINUTE:
                return False
            
            # Add current timestamp
            self.user_command_counts[user_id].append(current_time)
        else:
            # Handle message rate limiting
            if user_id not in self.user_message_counts:
                self.user_message_counts[user_id] = []
            
            # Remove timestamps older than the reset time
            self.user_message_counts[user_id] = [
                t for t in self.user_message_counts[user_id]
                if current_time - t < RATE_LIMIT_RESET_TIME
            ]
            
            # Check if message count exceeds limit
            if len(self.user_message_counts[user_id]) >= MAX_MESSAGES_PER_MINUTE:
                return False
            
            # Add current timestamp
            self.user_message_counts[user_id].append(current_time)
        
        return True

class SpamDetector:
    """Detector for spam messages."""
    
    def __init__(self):
        self.user_spam_scores: Dict[int, Dict[str, Any]] = {}  # user_id -> {score, last_reset}
        
        # Compile regex patterns for performance
        self.patterns = [(re.compile(pattern, re.IGNORECASE), score) for pattern, score in SPAM_TRIGGERS]
    
    def check_message(self, user_id: int, message_text: str) -> Tuple[bool, float]:
        """
        Check if a message is spam.
        
        Args:
            user_id: Telegram user ID
            message_text: Message text to check
            
        Returns:
            Tuple of (is_spam, spam_score)
        """
        current_time = time.time()
        
        # Initialize or reset user's spam score if needed
        if user_id not in self.user_spam_scores:
            self.user_spam_scores[user_id] = {
                'score': 0.0,
                'last_reset': current_time
            }
        elif current_time - self.user_spam_scores[user_id]['last_reset'] > SPAM_RESET_INTERVAL:
            # Reset spam score after the reset interval
            self.user_spam_scores[user_id] = {
                'score': 0.0,
                'last_reset': current_time
            }
        
        # Calculate message spam score
        message_score = 0.0
        
        # Check message against regex patterns
        for pattern, score in self.patterns:
            matches = pattern.findall(message_text)
            if matches:
                message_score += score * len(matches)
        
        # Check message length
        if len(message_text) > 500:
            message_score += 2.0
        
        # Update user's spam score
        self.user_spam_scores[user_id]['score'] += message_score
        
        # Check if user's spam score exceeds threshold
        is_spam = self.user_spam_scores[user_id]['score'] >= SPAM_SCORE_THRESHOLD
        
        # Update user's spam score in the database
        try:
            user = db_utils.get_or_create_user(user_id)
            user.spam_score = self.user_spam_scores[user_id]['score']
            db_utils.db.session.commit()
        except Exception as e:
            logger.error(f"Error updating user spam score: {e}")
        
        return is_spam, message_score

class URLScanner:
    """Scanner for suspicious or malicious URLs."""
    
    def __init__(self):
        # Compile regex patterns for performance
        self.url_pattern = re.compile(r'(https?://\S+)', re.IGNORECASE)
        self.suspicious_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in SUSPICIOUS_URL_PATTERNS]
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from a text.
        
        Args:
            text: Text to extract URLs from
            
        Returns:
            List of extracted URLs
        """
        return self.url_pattern.findall(text)
    
    def check_urls(self, text: str) -> List[Dict[str, Any]]:
        """
        Check all URLs in a text for safety.
        
        Args:
            text: Text to check URLs in
            
        Returns:
            List of dictionaries with URL safety information
        """
        urls = self.extract_urls(text)
        results = []
        
        for url in urls:
            # Check against suspicious patterns
            is_suspicious = any(pattern.search(url) for pattern in self.suspicious_patterns)
            
            if is_suspicious:
                # Mark as suspicious in the database
                db_utils.mark_url_suspicious(url, category="pattern_match")
                
                results.append({
                    'url': url,
                    'is_safe': False,
                    'reason': "Matches suspicious pattern"
                })
            else:
                # Check against the database
                safety_info = db_utils.check_url_safety(url)
                results.append({
                    'url': url,
                    'is_safe': safety_info['is_safe'],
                    'reason': safety_info.get('category', "Not in database")
                })
        
        return results

class UserVerification:
    """System for verifying users."""
    
    def __init__(self):
        self.pending_verifications: Dict[int, Dict[str, Any]] = {}  # user_id -> {code, expiry}
    
    def generate_verification_code(self, user_id: int) -> str:
        """
        Generate a verification code for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            Verification code string
        """
        # Generate code in the database
        code = db_utils.generate_verification_code(user_id)
        
        # Also store locally with expiry
        expiry = time.time() + 3600  # 1 hour expiry
        self.pending_verifications[user_id] = {
            'code': code,
            'expiry': expiry
        }
        
        return code
    
    def verify_code(self, user_id: int, code: str) -> bool:
        """
        Verify a user's verification code.
        
        Args:
            user_id: Telegram user ID
            code: Verification code to verify
            
        Returns:
            True if verification successful, False otherwise
        """
        # Check if code is valid and not expired
        if user_id in self.pending_verifications:
            if time.time() > self.pending_verifications[user_id]['expiry']:
                # Code has expired
                del self.pending_verifications[user_id]
                return False
            
            if self.pending_verifications[user_id]['code'] == code:
                # Code is valid
                result = db_utils.verify_user(user_id, code)
                if result:
                    # Verification successful, remove from pending
                    del self.pending_verifications[user_id]
                return result
        
        # Fallback to database check
        return db_utils.verify_user(user_id, code)

# Initialize security components
rate_limiter = RateLimiter()
spam_detector = SpamDetector()
url_scanner = URLScanner()
user_verification = UserVerification()

# Security wrapper functions

def check_user_blocked(func):
    """Decorator to check if a user is blocked."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Get or create user in database
        user = db_utils.get_or_create_user(
            user_id,
            update.effective_user.username,
            update.effective_user.first_name,
            update.effective_user.last_name
        )
        
        if user and user.is_blocked:
            # User is blocked, silently ignore
            logger.info(f"Blocked user {user_id} attempted to use the bot")
            return None
        
        # User is not blocked, proceed
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def check_rate_limit(func):
    """Decorator to check rate limits."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        is_command = bool(update.message and update.message.text and update.message.text.startswith('/'))
        
        if not rate_limiter.check_rate_limit(user_id, is_command):
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for user {user_id}")
            
            # Log the rate limit in the database
            db_utils.log_user_activity(user_id, "rate_limit_exceeded", 
                                    f"{'Command' if is_command else 'Message'} rate limit exceeded")
            
            if is_command:
                # Only notify the user for command rate limiting
                await update.message.reply_text(
                    "⚠️ You are sending commands too quickly. Please wait a moment before trying again."
                )
            
            return None
        
        # Rate limit not exceeded, proceed
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def check_spam(func):
    """Decorator to check for spam."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.message and update.message.text:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            is_spam, spam_score = spam_detector.check_message(user_id, message_text)
            
            if is_spam:
                # Message is spam
                logger.warning(f"Spam detected from user {user_id}: {message_text[:50]}...")
                
                # Log the spam in the database
                db_utils.log_user_activity(user_id, "spam_detected", 
                                        f"Spam score: {spam_score}, Message: {message_text[:100]}")
                
                # Block user if spam score is very high
                if spam_score >= SPAM_SCORE_THRESHOLD * 2:
                    db_utils.block_user(user_id, "Excessive spam")
                    await update.message.reply_text(
                        "🚫 Your account has been blocked for sending spam. "
                        "If you believe this is a mistake, please contact support."
                    )
                    return None
                
                await update.message.reply_text(
                    "⚠️ Your message has been flagged as potential spam. "
                    "Please avoid sending similar messages."
                )
                return None
        
        # Not spam, proceed
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def check_urls(func):
    """Decorator to check URLs in messages for safety."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.message and update.message.text:
            user_id = update.effective_user.id
            message_text = update.message.text
            
            # Check for URLs
            url_results = url_scanner.check_urls(message_text)
            
            # If there are unsafe URLs, block the message
            unsafe_urls = [result for result in url_results if not result['is_safe']]
            
            if unsafe_urls:
                # Unsafe URLs detected
                logger.warning(f"Unsafe URLs detected from user {user_id}: {unsafe_urls}")
                
                # Log the unsafe URLs in the database
                for url_result in unsafe_urls:
                    db_utils.log_user_activity(user_id, "unsafe_url_detected", 
                                           f"URL: {url_result['url']}, Reason: {url_result['reason']}")
                
                await update.message.reply_text(
                    "⚠️ Your message contains suspicious or unsafe URLs. "
                    "For security reasons, this message will not be processed."
                )
                return None
        
        # No unsafe URLs, proceed
        return await func(update, context, *args, **kwargs)
    
    return wrapper

def apply_all_safeguards(func):
    """Apply all safeguards at once."""
    @check_user_blocked
    @check_rate_limit
    @check_spam
    @check_urls
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        return await func(update, context, *args, **kwargs)
    
    return wrapper