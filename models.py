"""
Database models for the Telegram cryptocurrency pool bot
"""

from datetime import datetime
from app import db

class User(db.Model):
    """
    User model for storing Telegram user data
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)  # Telegram user ID
    username = db.Column(db.String(255), nullable=True)  # Telegram username (optional)
    first_name = db.Column(db.String(255), nullable=True)
    last_name = db.Column(db.String(255), nullable=True)
    is_subscribed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    queries = db.relationship('UserQuery', backref='user', lazy=True)
    
    def __repr__(self):
        return f"<User {self.id}: {self.username or 'No Username'}>"

class UserQuery(db.Model):
    """
    Model for tracking user queries and interactions
    """
    __tablename__ = 'user_queries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    command = db.Column(db.String(50))  # The command used (/start, /info, etc.)
    query_text = db.Column(db.Text, nullable=True)  # Full text of the query
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserQuery {self.id}: {self.command}>"

class Pool(db.Model):
    """
    Model for storing cryptocurrency pool data
    """
    __tablename__ = 'pools'
    
    id = db.Column(db.String(255), primary_key=True)  # Raydium pool ID
    token_a_symbol = db.Column(db.String(50))
    token_b_symbol = db.Column(db.String(50))
    apr_24h = db.Column(db.Float)
    apr_7d = db.Column(db.Float)
    apr_30d = db.Column(db.Float)
    tvl = db.Column(db.Float)  # Total Value Locked in USD
    token_a_price = db.Column(db.Float)
    token_b_price = db.Column(db.Float)
    fee = db.Column(db.Float)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Pool {self.id}: {self.token_a_symbol}/{self.token_b_symbol}>"

class BotStatistics(db.Model):
    """
    Model for tracking bot usage statistics
    """
    __tablename__ = 'bot_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    command_count = db.Column(db.Integer, default=0)
    active_user_count = db.Column(db.Integer, default=0)
    subscribed_user_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f"<BotStatistics {self.id}: {self.command_count} commands>"