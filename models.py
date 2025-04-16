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
    is_blocked = db.Column(db.Boolean, default=False)  # For blocking users who violate rules
    is_verified = db.Column(db.Boolean, default=False)  # For user verification system
    verification_code = db.Column(db.String(20), nullable=True)  # For verification process
    message_count = db.Column(db.Integer, default=0)  # Track message count for rate limiting
    last_message_time = db.Column(db.DateTime, nullable=True)  # For rate limiting
    spam_score = db.Column(db.Integer, default=0)  # For spam detection
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    queries = db.relationship('UserQuery', backref='user', lazy=True)
    activity_logs = db.relationship('UserActivityLog', backref='user', lazy=True)
    
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
    response_text = db.Column(db.Text, nullable=True)  # Bot's response
    processing_time = db.Column(db.Float, nullable=True)  # Time taken to process in ms
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
    volume_24h = db.Column(db.Float, nullable=True)  # 24-hour volume
    tx_count_24h = db.Column(db.Integer, nullable=True)  # 24-hour transaction count
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
    blocked_user_count = db.Column(db.Integer, default=0)
    spam_detected_count = db.Column(db.Integer, default=0)
    average_response_time = db.Column(db.Float, default=0)  # Average response time in ms
    uptime_percentage = db.Column(db.Float, default=100.0)  # Percentage of time bot was available
    error_count = db.Column(db.Integer, default=0)  # Count of errors encountered
    
    def __repr__(self):
        return f"<BotStatistics {self.id}: {self.command_count} commands>"

class UserActivityLog(db.Model):
    """
    Model for monitoring user activity in detail
    """
    __tablename__ = 'user_activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50))  # Type of activity (login, message, command, etc.)
    details = db.Column(db.Text, nullable=True)  # Additional details about the activity
    ip_address = db.Column(db.String(50), nullable=True)  # User's IP address if available
    user_agent = db.Column(db.String(255), nullable=True)  # User's client info if available
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<UserActivityLog {self.id}: {self.activity_type}>"

class SystemBackup(db.Model):
    """
    Model for tracking database backups
    """
    __tablename__ = 'system_backups'
    
    id = db.Column(db.Integer, primary_key=True)
    backup_path = db.Column(db.String(255))  # Path to the backup file
    backup_size = db.Column(db.Integer)  # Size of the backup in bytes
    record_count = db.Column(db.Integer)  # Number of records backed up
    is_complete = db.Column(db.Boolean, default=True)  # Whether the backup completed successfully
    notes = db.Column(db.Text, nullable=True)  # Any notes about the backup
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemBackup {self.id}: {self.created_at.strftime('%Y-%m-%d %H:%M')}>"

class ErrorLog(db.Model):
    """
    Model for tracking system errors
    """
    __tablename__ = 'error_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    error_type = db.Column(db.String(100))  # Type of error
    error_message = db.Column(db.Text)  # Full error message
    traceback = db.Column(db.Text, nullable=True)  # Stack trace
    module = db.Column(db.String(100))  # Module where error occurred
    user_id = db.Column(db.Integer, nullable=True)  # User ID if error related to a user
    resolved = db.Column(db.Boolean, default=False)  # Whether the error has been resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ErrorLog {self.id}: {self.error_type}>"

class SuspiciousURL(db.Model):
    """
    Model for tracking and blocking suspicious URLs
    """
    __tablename__ = 'suspicious_urls'
    
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255))  # The suspicious URL
    domain = db.Column(db.String(100))  # Domain extracted from URL
    category = db.Column(db.String(50))  # Category of threat (phishing, malware, spam, etc.)
    detection_count = db.Column(db.Integer, default=1)  # Number of times detected
    is_blocked = db.Column(db.Boolean, default=True)  # Whether the URL is blocked
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_detected = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<SuspiciousURL {self.id}: {self.url}>"