#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database utilities for the Telegram cryptocurrency pool bot
"""

import os
import json
import time
import logging
import datetime
import shutil
from functools import wraps
from typing import Dict, Any, List, Optional, Union, Callable
from sqlalchemy.exc import SQLAlchemyError

from models import (
    User, UserQuery, Pool, BotStatistics, UserActivityLog,
    SystemBackup, ErrorLog, SuspiciousURL
)
from app import db

# Configure logging
logger = logging.getLogger(__name__)

def handle_db_error(func):
    """Decorator to handle database errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            # Log the error to the database if possible
            try:
                error_log = ErrorLog(
                    error_type="Database Error",
                    error_message=str(e),
                    module=f"db_utils.{func.__name__}",
                    user_id=kwargs.get('user_id')
                )
                db.session.add(error_log)
                db.session.commit()
            except Exception:
                # If we can't log to DB, at least we logged to the file
                pass
            return None
    return wrapper

# User Management Functions

@handle_db_error
def get_or_create_user(user_id: int, username: str = None, first_name: str = None, 
                     last_name: str = None) -> User:
    """
    Get a user from the database or create a new one if not exists.
    
    Args:
        user_id: Telegram user ID
        username: Telegram username (optional)
        first_name: User's first name (optional)
        last_name: User's last name (optional)
        
    Returns:
        User object
    """
    user = User.query.get(user_id)
    
    if not user:
        # Create new user
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        db.session.add(user)
        db.session.commit()
        
        # Log user creation
        log_user_activity(user_id, "account_created", "New user created")
    else:
        # Update user info in case it has changed
        if username is not None and username != user.username:
            user.username = username
        if first_name is not None and first_name != user.first_name:
            user.first_name = first_name
        if last_name is not None and last_name != user.last_name:
            user.last_name = last_name
            
        # Update last active time
        user.last_active = datetime.datetime.utcnow()
        db.session.commit()
    
    return user

@handle_db_error
def block_user(user_id: int, reason: str = None) -> bool:
    """
    Block a user.
    
    Args:
        user_id: Telegram user ID
        reason: Reason for blocking (optional)
        
    Returns:
        True if successful, False otherwise
    """
    user = User.query.get(user_id)
    
    if not user:
        return False
    
    user.is_blocked = True
    db.session.commit()
    
    # Log user blocking
    log_user_activity(user_id, "user_blocked", f"User blocked: {reason}")
    
    # Update statistics
    update_bot_statistics()
    
    return True

@handle_db_error
def unblock_user(user_id: int) -> bool:
    """
    Unblock a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    user = User.query.get(user_id)
    
    if not user:
        return False
    
    user.is_blocked = False
    db.session.commit()
    
    # Log user unblocking
    log_user_activity(user_id, "user_unblocked", "User unblocked")
    
    # Update statistics
    update_bot_statistics()
    
    return True

@handle_db_error
def subscribe_user(user_id: int) -> bool:
    """
    Subscribe a user to updates.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    user = User.query.get(user_id)
    
    if not user:
        return False
    
    user.is_subscribed = True
    db.session.commit()
    
    # Log subscription
    log_user_activity(user_id, "user_subscribed", "User subscribed to updates")
    
    # Update statistics
    update_bot_statistics()
    
    return True

@handle_db_error
def unsubscribe_user(user_id: int) -> bool:
    """
    Unsubscribe a user from updates.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        True if successful, False otherwise
    """
    user = User.query.get(user_id)
    
    if not user:
        return False
    
    user.is_subscribed = False
    db.session.commit()
    
    # Log unsubscription
    log_user_activity(user_id, "user_unsubscribed", "User unsubscribed from updates")
    
    # Update statistics
    update_bot_statistics()
    
    return True

@handle_db_error
def get_subscribed_users() -> List[User]:
    """
    Get all subscribed users.
    
    Returns:
        List of User objects who are subscribed to updates
    """
    return User.query.filter_by(is_subscribed=True, is_blocked=False).all()

@handle_db_error
def verify_user(user_id: int, code: str) -> bool:
    """
    Verify a user with the provided code.
    
    Args:
        user_id: Telegram user ID
        code: Verification code
        
    Returns:
        True if verification successful, False otherwise
    """
    user = User.query.get(user_id)
    
    if not user or not user.verification_code:
        return False
    
    if user.verification_code == code:
        user.is_verified = True
        user.verification_code = None  # Clear the code after verification
        db.session.commit()
        
        # Log verification
        log_user_activity(user_id, "user_verified", "User verified their account")
        return True
    
    return False

@handle_db_error
def generate_verification_code(user_id: int) -> Optional[str]:
    """
    Generate a verification code for a user.
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Verification code string or None if failed
    """
    import random
    import string
    
    user = User.query.get(user_id)
    
    if not user:
        return None
    
    # Generate a random 6-character alphanumeric code
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    user.verification_code = verification_code
    db.session.commit()
    
    # Log code generation
    log_user_activity(user_id, "verification_code_generated", "Verification code generated")
    
    return verification_code

# Query and Log Functions

@handle_db_error
def log_user_query(user_id: int, command: str, query_text: str = None, 
                 response_text: str = None, processing_time: float = None) -> UserQuery:
    """
    Log a user query to the database.
    
    Args:
        user_id: Telegram user ID
        command: Command used
        query_text: Full text of the query (optional)
        response_text: Bot's response (optional)
        processing_time: Time taken to process in ms (optional)
        
    Returns:
        UserQuery object
    """
    query = UserQuery(
        user_id=user_id,
        command=command,
        query_text=query_text,
        response_text=response_text,
        processing_time=processing_time
    )
    db.session.add(query)
    
    # Increment message count for rate limiting
    user = User.query.get(user_id)
    if user:
        user.message_count += 1
        user.last_message_time = datetime.datetime.utcnow()
    
    db.session.commit()
    
    # Update bot statistics
    update_bot_statistics()
    
    return query

@handle_db_error
def log_user_activity(user_id: int, activity_type: str, details: str = None,
                    ip_address: str = None, user_agent: str = None) -> UserActivityLog:
    """
    Log user activity.
    
    Args:
        user_id: Telegram user ID
        activity_type: Type of activity
        details: Additional details (optional)
        ip_address: User's IP address (optional)
        user_agent: User's client info (optional)
        
    Returns:
        UserActivityLog object
    """
    activity = UserActivityLog(
        user_id=user_id,
        activity_type=activity_type,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.session.add(activity)
    db.session.commit()
    
    return activity

@handle_db_error
def log_error(error_type: str, error_message: str, traceback: str = None,
            module: str = None, user_id: int = None) -> ErrorLog:
    """
    Log an error to the database.
    
    Args:
        error_type: Type of error
        error_message: Error message
        traceback: Stack trace (optional)
        module: Module where error occurred (optional)
        user_id: User ID if error related to a user (optional)
        
    Returns:
        ErrorLog object
    """
    error = ErrorLog(
        error_type=error_type,
        error_message=error_message,
        traceback=traceback,
        module=module,
        user_id=user_id
    )
    db.session.add(error)
    db.session.commit()
    
    # Update bot statistics
    stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
    if stats:
        stats.error_count += 1
        db.session.commit()
    
    return error

# Pool Data Functions

@handle_db_error
def save_pool_data(pool_data: List[Dict[str, Any]]) -> bool:
    """
    Save pool data to the database.
    
    Args:
        pool_data: List of pool data dictionaries
        
    Returns:
        True if successful, False otherwise
    """
    try:
        for pool_item in pool_data:
            pool_id = pool_item.get('id')
            
            if not pool_id:
                continue
            
            # Check if pool exists
            pool = Pool.query.get(pool_id)
            
            if not pool:
                # Create new pool
                pool = Pool(
                    id=pool_id,
                    token_a_symbol=pool_item.get('token_a', {}).get('symbol', 'Unknown'),
                    token_b_symbol=pool_item.get('token_b', {}).get('symbol', 'Unknown'),
                    apr_24h=float(pool_item.get('apr_24h', pool_item.get('apr', 0))),
                    apr_7d=float(pool_item.get('apr_7d', 0)),
                    apr_30d=float(pool_item.get('apr_30d', 0)),
                    tvl=float(pool_item.get('tvl', 0)),
                    token_a_price=float(pool_item.get('token_a', {}).get('price', 0)),
                    token_b_price=float(pool_item.get('token_b', {}).get('price', 0)),
                    fee=float(pool_item.get('fee', 0.003)),
                    volume_24h=float(pool_item.get('volume_24h', 0)),
                    tx_count_24h=int(pool_item.get('tx_count_24h', 0)),
                )
                db.session.add(pool)
            else:
                # Update existing pool
                pool.token_a_symbol = pool_item.get('token_a', {}).get('symbol', pool.token_a_symbol)
                pool.token_b_symbol = pool_item.get('token_b', {}).get('symbol', pool.token_b_symbol)
                pool.apr_24h = float(pool_item.get('apr_24h', pool_item.get('apr', pool.apr_24h)))
                pool.apr_7d = float(pool_item.get('apr_7d', pool.apr_7d))
                pool.apr_30d = float(pool_item.get('apr_30d', pool.apr_30d))
                pool.tvl = float(pool_item.get('tvl', pool.tvl))
                pool.token_a_price = float(pool_item.get('token_a', {}).get('price', pool.token_a_price))
                pool.token_b_price = float(pool_item.get('token_b', {}).get('price', pool.token_b_price))
                pool.fee = float(pool_item.get('fee', pool.fee))
                pool.volume_24h = float(pool_item.get('volume_24h', pool.volume_24h))
                pool.tx_count_24h = int(pool_item.get('tx_count_24h', pool.tx_count_24h))
                pool.last_updated = datetime.datetime.utcnow()
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving pool data: {e}")
        return False

@handle_db_error
def get_all_pools() -> List[Pool]:
    """
    Get all pools from the database.
    
    Returns:
        List of Pool objects
    """
    return Pool.query.order_by(Pool.apr_24h.desc()).all()

@handle_db_error
def get_high_apr_pools(limit: int = 5) -> List[Pool]:
    """
    Get pools with highest APR.
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of Pool objects with highest APR
    """
    return Pool.query.order_by(Pool.apr_24h.desc()).limit(limit).all()

@handle_db_error
def get_stable_pools(limit: int = 5) -> List[Pool]:
    """
    Get stable pools (those containing USDC/USDT).
    
    Args:
        limit: Maximum number of pools to return
        
    Returns:
        List of stable Pool objects
    """
    # Search for pools with USDC or USDT in either token
    pools = Pool.query.filter(
        ((Pool.token_a_symbol.contains('USDC')) | (Pool.token_a_symbol.contains('USDT')) |
         (Pool.token_b_symbol.contains('USDC')) | (Pool.token_b_symbol.contains('USDT')))
    ).order_by(Pool.tvl.desc()).limit(limit).all()
    
    return pools

# Statistics and Monitoring Functions

@handle_db_error
def update_bot_statistics() -> BotStatistics:
    """
    Update or create bot statistics.
    
    Returns:
        BotStatistics object
    """
    # Get current stats or create new
    stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
    
    if not stats:
        # Create new stats object if none exists
        stats = BotStatistics(start_time=datetime.datetime.utcnow())
        db.session.add(stats)
    
    # Update statistics
    stats.command_count = UserQuery.query.count()
    stats.active_user_count = User.query.filter(
        User.last_active > (datetime.datetime.utcnow() - datetime.timedelta(days=1)),
        User.is_blocked == False
    ).count()
    stats.subscribed_user_count = User.query.filter_by(is_subscribed=True).count()
    stats.blocked_user_count = User.query.filter_by(is_blocked=True).count()
    
    # Calculate average response time
    response_times = db.session.query(UserQuery.processing_time).filter(UserQuery.processing_time != None).all()
    if response_times:
        avg_time = sum(rt[0] for rt in response_times) / len(response_times)
        stats.average_response_time = avg_time
    
    db.session.commit()
    return stats

@handle_db_error
def create_database_backup() -> Optional[SystemBackup]:
    """
    Create a backup of the database.
    
    Returns:
        SystemBackup object or None if failed
    """
    try:
        # Create backup directory if it doesn't exist
        backup_dir = os.path.join(os.getcwd(), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"db_backup_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # Initialize record counts
        record_counts = {
            'users': User.query.count(),
            'queries': UserQuery.query.count(),
            'pools': Pool.query.count(),
            'activities': UserActivityLog.query.count(),
            'errors': ErrorLog.query.count(),
            'urls': SuspiciousURL.query.count()
        }
        total_records = sum(record_counts.values())
        
        # Export all tables to a JSON file
        data = {
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_subscribed': user.is_subscribed,
                    'is_blocked': user.is_blocked,
                    'is_verified': user.is_verified,
                    'message_count': user.message_count,
                    'spam_score': user.spam_score,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_active': user.last_active.isoformat() if user.last_active else None
                }
                for user in User.query.all()
            ],
            'pools': [
                {
                    'id': pool.id,
                    'token_a_symbol': pool.token_a_symbol,
                    'token_b_symbol': pool.token_b_symbol,
                    'apr_24h': pool.apr_24h,
                    'apr_7d': pool.apr_7d,
                    'apr_30d': pool.apr_30d,
                    'tvl': pool.tvl,
                    'token_a_price': pool.token_a_price,
                    'token_b_price': pool.token_b_price,
                    'fee': pool.fee,
                    'volume_24h': pool.volume_24h,
                    'tx_count_24h': pool.tx_count_24h,
                    'last_updated': pool.last_updated.isoformat() if pool.last_updated else None
                }
                for pool in Pool.query.all()
            ],
            'metadata': {
                'created_at': datetime.datetime.now().isoformat(),
                'record_counts': record_counts,
                'total_records': total_records
            }
        }
        
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Get file size
        backup_size = os.path.getsize(backup_path)
        
        # Create backup record
        backup = SystemBackup(
            backup_path=backup_path,
            backup_size=backup_size,
            record_count=total_records,
            notes=f"Automatic backup, tables: {', '.join(record_counts.keys())}"
        )
        db.session.add(backup)
        db.session.commit()
        
        logger.info(f"Database backup created: {backup_path}")
        return backup
    except Exception as e:
        logger.error(f"Error creating database backup: {e}")
        
        # Try to log the error
        try:
            log_error("Backup Error", str(e), module="db_utils.create_database_backup")
        except:
            pass
        
        return None

@handle_db_error
def restore_database_from_backup(backup_id: int) -> bool:
    """
    Restore database from a backup.
    
    Args:
        backup_id: ID of the backup to restore
        
    Returns:
        True if successful, False otherwise
    """
    # This is a simplified example - in a production environment,
    # you would need a more sophisticated approach
    try:
        backup = SystemBackup.query.get(backup_id)
        
        if not backup or not os.path.exists(backup.backup_path):
            logger.error(f"Backup {backup_id} not found or file missing")
            return False
        
        # Load data from backup
        with open(backup.backup_path, 'r') as f:
            data = json.load(f)
        
        # Begin transaction
        db.session.begin_nested()
        
        # Restore users
        if 'users' in data:
            # Clear existing users (be careful with this in production!)
            User.query.delete()
            
            for user_data in data['users']:
                user = User(
                    id=user_data['id'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    is_subscribed=user_data['is_subscribed'],
                    is_blocked=user_data['is_blocked'],
                    is_verified=user_data['is_verified'],
                    message_count=user_data['message_count'],
                    spam_score=user_data['spam_score']
                )
                
                if user_data['created_at']:
                    user.created_at = datetime.datetime.fromisoformat(user_data['created_at'])
                
                if user_data['last_active']:
                    user.last_active = datetime.datetime.fromisoformat(user_data['last_active'])
                
                db.session.add(user)
        
        # Restore pools
        if 'pools' in data:
            # Clear existing pools
            Pool.query.delete()
            
            for pool_data in data['pools']:
                pool = Pool(
                    id=pool_data['id'],
                    token_a_symbol=pool_data['token_a_symbol'],
                    token_b_symbol=pool_data['token_b_symbol'],
                    apr_24h=pool_data['apr_24h'],
                    apr_7d=pool_data['apr_7d'],
                    apr_30d=pool_data['apr_30d'],
                    tvl=pool_data['tvl'],
                    token_a_price=pool_data['token_a_price'],
                    token_b_price=pool_data['token_b_price'],
                    fee=pool_data['fee'],
                    volume_24h=pool_data['volume_24h'],
                    tx_count_24h=pool_data['tx_count_24h']
                )
                
                if pool_data['last_updated']:
                    pool.last_updated = datetime.datetime.fromisoformat(pool_data['last_updated'])
                
                db.session.add(pool)
        
        db.session.commit()
        logger.info(f"Database restored from backup {backup_id}")
        
        # Log restoration
        log_error("System Action", f"Database restored from backup {backup_id}", 
                module="db_utils.restore_database_from_backup")
        
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error restoring database from backup: {e}")
        
        # Try to log the error
        try:
            log_error("Restore Error", str(e), module="db_utils.restore_database_from_backup")
        except:
            pass
        
        return False

# URL Safety Functions

@handle_db_error
def check_url_safety(url: str) -> Dict[str, Any]:
    """
    Check if a URL is safe or suspicious.
    
    Args:
        url: URL to check
        
    Returns:
        Dictionary with safety information
    """
    from urllib.parse import urlparse
    
    # Parse URL to get domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # Check if the URL or domain is in our database
    suspicious_url = SuspiciousURL.query.filter(
        (SuspiciousURL.url == url) | (SuspiciousURL.domain == domain)
    ).first()
    
    if suspicious_url:
        # Increment detection count
        suspicious_url.detection_count += 1
        suspicious_url.last_detected = datetime.datetime.utcnow()
        db.session.commit()
        
        return {
            'is_safe': False,
            'category': suspicious_url.category,
            'domain': domain,
            'detection_count': suspicious_url.detection_count,
            'first_detected': suspicious_url.created_at.isoformat()
        }
    
    # Implement additional checks here (API calls to URL scanning services, etc.)
    # For now, we'll assume it's safe if not in our database
    
    return {
        'is_safe': True,
        'domain': domain
    }

@handle_db_error
def mark_url_suspicious(url: str, category: str = "unknown") -> SuspiciousURL:
    """
    Mark a URL as suspicious.
    
    Args:
        url: URL to mark as suspicious
        category: Category of threat (phishing, malware, spam, etc.)
        
    Returns:
        SuspiciousURL object
    """
    from urllib.parse import urlparse
    
    # Parse URL to get domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    # Check if the URL is already in the database
    suspicious_url = SuspiciousURL.query.filter_by(url=url).first()
    
    if suspicious_url:
        # Update existing record
        suspicious_url.detection_count += 1
        suspicious_url.category = category
        suspicious_url.last_detected = datetime.datetime.utcnow()
    else:
        # Create new record
        suspicious_url = SuspiciousURL(
            url=url,
            domain=domain,
            category=category
        )
        db.session.add(suspicious_url)
    
    db.session.commit()
    
    # Update statistics
    stats = BotStatistics.query.order_by(BotStatistics.id.desc()).first()
    if stats:
        stats.spam_detected_count += 1
        db.session.commit()
    
    return suspicious_url