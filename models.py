#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database models for the Telegram cryptocurrency pool bot
"""

import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

# Initialize the database
db = SQLAlchemy()

class User(db.Model):
    """User model representing a Telegram user."""
    __tablename__ = "users"
    
    # In the database, the 'id' column stores the Telegram user ID directly
    # We use BigInteger to support large Telegram IDs
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_blocked = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_subscribed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    # The column name in the database is 'last_active'
    last_active = Column(DateTime, default=datetime.datetime.utcnow)
    verification_code = Column(String(8), nullable=True)
    verification_attempts = Column(Integer, default=0)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    block_reason = Column(String(255), nullable=True)
    message_count = Column(Integer, default=0)
    spam_score = Column(Integer, default=0)
    
    # Financial profile settings
    risk_profile = Column(String(20), default="moderate")  # conservative, moderate, aggressive
    investment_horizon = Column(String(20), default="medium")  # short, medium, long
    preferred_pools = Column(JSON, nullable=True)  # User's favorite or preferred pool types
    investment_goals = Column(String(255), nullable=True)  # User's financial goals
    
    # Wallet connection settings
    wallet_address = Column(String(255), nullable=True)  # Solana wallet public address
    wallet_connected_at = Column(DateTime, nullable=True)  # When wallet was connected
    connection_status = Column(String(20), default="disconnected")  # disconnected, connecting, connected, failed
    wallet_session_id = Column(String(100), nullable=True)  # For WalletConnect session tracking
    last_tx_id = Column(String(100), nullable=True)  # Last transaction signature
    
    # Notification preferences
    notif_market = Column(Boolean, default=False)  # Market summary notifications
    notif_apr = Column(Boolean, default=False)  # APR change notifications
    notif_price = Column(Boolean, default=False)  # Price change notifications
    notif_prediction = Column(Boolean, default=False)  # AI prediction notifications
    
    # Relationships
    queries = relationship("UserQuery", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user", cascade="all, delete-orphan")
    investments = relationship("InvestmentLog", back_populates="user", cascade="all, delete-orphan")
    
    # Property to maintain backward compatibility
    @property
    def telegram_id(self):
        return self.id
    
    # Properties to maintain compatibility with code that uses last_active_at
    @property
    def last_active_at(self):
        return self.last_active
    
    @last_active_at.setter
    def last_active_at(self, value):
        self.last_active = value
    
    def __repr__(self):
        return f"<User id={self.id}, username={self.username}>"

class UserQuery(db.Model):
    """UserQuery model representing a query made by a user."""
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    command = Column(String(50), nullable=True)
    query_text = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)
    processing_time = Column(Float, nullable=True)  # In milliseconds
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="queries")
    
    def __repr__(self):
        return f"<UserQuery id={self.id}, user_id={self.user_id}, command={self.command}>"

class Pool(db.Model):
    """Pool model representing a cryptocurrency pool."""
    __tablename__ = "pools"
    
    id = Column(String(255), primary_key=True)  # This is actually the pool_id
    token_a_symbol = Column(String(10), nullable=False)
    token_b_symbol = Column(String(10), nullable=False)
    token_a_price = Column(Float, nullable=False)
    token_b_price = Column(Float, nullable=False)
    apr_24h = Column(Float, nullable=False)
    apr_7d = Column(Float, nullable=True)
    apr_30d = Column(Float, nullable=True)
    tvl = Column(Float, nullable=False)
    fee = Column(Float, nullable=False)
    volume_24h = Column(Float, nullable=True)
    tx_count_24h = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Properties to maintain compatibility with application code
    @property
    def pool_id(self):
        return self.id
        
    @property
    def updated_at(self):
        return self.last_updated
    
    def __repr__(self):
        return f"<Pool id={self.id}, token_a={self.token_a_symbol}, token_b={self.token_b_symbol}, apr_24h={self.apr_24h}>"

class UserActivityLog(db.Model):
    """UserActivityLog model representing user activity."""
    __tablename__ = "user_activity_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    def __repr__(self):
        return f"<UserActivityLog id={self.id}, user_id={self.user_id}, activity_type={self.activity_type}>"

class ErrorLog(db.Model):
    """ErrorLog model representing system errors."""
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True)
    error_type = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    module = Column(String(100), nullable=True)
    user_id = Column(BigInteger, nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Properties to maintain compatibility with application code
    @property
    def timestamp(self):
        return self.created_at
    
    def __repr__(self):
        return f"<ErrorLog id={self.id}, error_type={self.error_type}>"

class BotStatistics(db.Model):
    """BotStatistics model representing bot statistics."""
    __tablename__ = "bot_statistics"
    
    id = Column(Integer, primary_key=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    command_count = Column(Integer, default=0)
    active_user_count = Column(Integer, default=0)
    subscribed_user_count = Column(Integer, default=0)
    blocked_user_count = Column(Integer, default=0)
    spam_detected_count = Column(Integer, default=0)
    average_response_time = Column(Float, default=0.0)  # In milliseconds
    uptime_percentage = Column(Float, default=0.0)  # Percentage
    error_count = Column(Integer, default=0)
    
    # Properties to maintain compatibility with application code
    @property
    def total_users(self):
        return self.active_user_count
        
    @property
    def active_users_24h(self):
        return self.active_user_count
        
    @property
    def active_users_7d(self):
        return self.active_user_count
        
    @property
    def subscribed_users(self):
        return self.subscribed_user_count
        
    @property
    def total_messages(self):
        return self.command_count * 2  # Estimate
        
    @property
    def total_commands(self):
        return self.command_count
        
    @property
    def response_time_avg(self):
        return self.average_response_time
        
    @property
    def uptime(self):
        # Convert percentage to seconds (assuming 100% = 30 days)
        return int(self.uptime_percentage * 30 * 24 * 60 * 60 / 100)
        
    @property
    def updated_at(self):
        return self.start_time
    
    def __repr__(self):
        return f"<BotStatistics id={self.id}, active_users={self.active_user_count}, commands={self.command_count}>"

class SystemBackup(db.Model):
    """SystemBackup model representing system backups."""
    __tablename__ = "system_backups"
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)  # In bytes
    backup_type = Column(String(50), default="full")
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemBackup id={self.id}, filename={self.filename}, created_at={self.created_at}>"

class SuspiciousURL(db.Model):
    """SuspiciousURL model representing suspicious URLs detected by the bot."""
    __tablename__ = "suspicious_urls"
    
    id = Column(Integer, primary_key=True)
    url = Column(String(2000), nullable=False)
    category = Column(String(50), default="unknown")
    detected_in_message_id = Column(BigInteger, nullable=True)
    detected_from_user_id = Column(BigInteger, nullable=True)
    is_verified_threat = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<SuspiciousURL id={self.id}, url={self.url}, category={self.category}>"

class MoodEntry(db.Model):
    """MoodEntry model for tracking user emotional states related to investments."""
    __tablename__ = "mood_entries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    mood = Column(String(20), nullable=False)  # very_happy, happy, neutral, sad, anxious, angry, confused
    mood_emoji = Column(String(10), nullable=False)  # The emoji representation
    context = Column(String(50), nullable=False)  # before_investment, after_investment, market_up, etc.
    notes = Column(Text, nullable=True)  # Optional user notes
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="mood_entries")
    
    def __repr__(self):
        return f"<MoodEntry id={self.id}, user_id={self.user_id}, mood={self.mood}, context={self.context}>"

class InvestmentLog(db.Model):
    """InvestmentLog model for tracking user investments in liquidity pools."""
    __tablename__ = "investment_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    pool_id = Column(String(255), ForeignKey("pools.id"), nullable=False)
    amount = Column(Float, nullable=False)  # Amount in USD
    tx_hash = Column(String(100), nullable=False)  # Transaction signature/hash
    status = Column(String(20), nullable=False)  # confirming, confirmed, failed, etc.
    token_a_amount = Column(Float, nullable=True)  # Amount of token A invested
    token_b_amount = Column(Float, nullable=True)  # Amount of token B invested
    apr_at_entry = Column(Float, nullable=True)  # APR at time of investment
    notes = Column(Text, nullable=True)  # Optional notes or error messages
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="investments")
    pool = relationship("Pool", backref="investments")
    
    def __repr__(self):
        return f"<InvestmentLog id={self.id}, user_id={self.user_id}, pool_id={self.pool_id}, amount=${self.amount}, status={self.status}>"