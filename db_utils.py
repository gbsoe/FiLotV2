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
import psycopg2
from functools import wraps
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from sqlalchemy.exc import SQLAlchemyError

from models import (
    User, UserQuery, Pool, BotStatistics, UserActivityLog,
    SystemBackup, ErrorLog, SuspiciousURL, MoodEntry
)
from app import db

# Configure logging
logger = logging.getLogger(__name__)

def ping_database() -> Tuple[bool, Any]:
    """
    Ping the database to keep connections alive and verify connectivity.
    
    Returns:
        Tuple of (success, result)
    """
    try:
        conn, cursor = get_db_connection()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        return True, result
    except Exception as e:
        logger.error(f"Database ping failed: {e}")
        return False, str(e)

def get_db_connection() -> Tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor]:
    """
    Get a connection to the PostgreSQL database.
    
    Returns:
        Tuple of connection and cursor objects
    """
    try:
        # Get database URL from environment variable
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            logger.error("DATABASE_URL environment variable not found")
            raise ValueError("DATABASE_URL environment variable not found")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        logger.debug("Connected to PostgreSQL database")
        return conn, cursor
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def handle_db_error(func):
    """Decorator to handle database errors and use fallback when needed."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {str(e)}")
            
            # Try to use fallback if this function is related to menu state
            user_id = kwargs.get('user_id')
            if user_id and 'menu' in func.__name__.lower():
                # Import here to avoid circular imports
                import db_fallback
                
                # Log to fallback system
                db_fallback.log_user_activity(
                    user_id, 
                    "db_error", 
                    {"function": func.__name__, "error": str(e)}
                )
                logger.info(f"Used fallback logging for user {user_id} in {func.__name__}")
            
            # Try to log the error to the database if possible
            try:
                error_log = ErrorLog(
                    error_type="Database Error",
                    error_message=str(e),
                    module=f"db_utils.{func.__name__}",
                    user_id=user_id
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
    # In our database, the id column IS the telegram_id
    logger.info(f"Looking for user with id={user_id}")

    # Try to find the user by ID
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logger.error(f"Error querying user by primary key: {e}")
        user = None

    if not user:
        logger.info(f"User {user_id} not found, creating new user")
        # Create new user with the Telegram ID as the primary key
        try:
            user = User(
                id=user_id,  # Set the primary key directly to the Telegram ID
                username=username,
                first_name=first_name,
                last_name=last_name,
                created_at=datetime.datetime.utcnow(),
                last_active=datetime.datetime.utcnow()
            )
            db.session.add(user)
            db.session.flush()  # Try to flush first to catch errors early

            logger.info(f"Created new user with id={user_id}")

            # Commit changes
            db.session.commit()

            # Don't log activity yet as it might fail if user isn't properly created
            try:
                # Now it's safe to log activity since the user exists
                activity = UserActivityLog(
                    user_id=user_id,
                    activity_type="account_created",
                    details="New user created",
                    timestamp=datetime.datetime.utcnow()
                )
                db.session.add(activity)
                db.session.commit()
                logger.info(f"Logged creation activity for user {user_id}")
            except Exception as e:
                # Non-critical error, just log it
                logger.error(f"Error logging user creation activity: {e}")
                db.session.rollback()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {e}")
            # Re-raise only if it's a critical error
            if "duplicate key" not in str(e).lower():
                raise
            # If it's a duplicate key, try fetching again as another process might have created it
            user = User.query.get(user_id)
            if not user:
                raise  # If still not found, there's a serious issue
    else:
        logger.info(f"User {user_id} found, updating if needed")
        # Update user info in case it has changed
        changed = False
        if username is not None and username != user.username:
            user.username = username
            changed = True
        if first_name is not None and first_name != user.first_name:
            user.first_name = first_name
            changed = True
        if last_name is not None and last_name != user.last_name:
            user.last_name = last_name
            changed = True

        # Update last active timestamp
        user.last_active = datetime.datetime.utcnow()
        changed = True

        if changed:
            try:
                db.session.commit()
                logger.info(f"Updated user {user_id}")
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating user info: {e}")

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
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user:
        logger.warning(f"Cannot block user {user_id}: user not found")
        return False

    user.is_blocked = True
    user.block_reason = reason
    db.session.commit()

    # Log user blocking
    log_user_activity(user_id, "user_blocked", f"User blocked: {reason}")

    # Update statistics
    update_bot_statistics()

    logger.info(f"User {user_id} blocked successfully")
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
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user:
        logger.warning(f"Cannot unblock user {user_id}: user not found")
        return False

    user.is_blocked = False
    db.session.commit()

    # Log user unblocking
    log_user_activity(user_id, "user_unblocked", "User unblocked")

    # Update statistics
    update_bot_statistics()

    logger.info(f"User {user_id} unblocked successfully")
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
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user:
        logger.warning(f"Cannot subscribe user {user_id}: user not found")
        return False

    user.is_subscribed = True
    db.session.commit()

    # Log subscription
    log_user_activity(user_id, "user_subscribed", "User subscribed to updates")

    # Update statistics
    update_bot_statistics()

    logger.info(f"User {user_id} subscribed successfully")
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
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user:
        logger.warning(f"Cannot unsubscribe user {user_id}: user not found")
        return False

    user.is_subscribed = False
    db.session.commit()

    # Log unsubscription
    log_user_activity(user_id, "user_unsubscribed", "User unsubscribed from updates")

    # Update statistics
    update_bot_statistics()

    logger.info(f"User {user_id} unsubscribed successfully")
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
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user or not user.verification_code:
        logger.warning(f"Cannot verify user {user_id}: user not found or no verification code")
        return False

    if user.verification_code == code:
        user.is_verified = True
        user.verification_code = None  # Clear the code after verification
        db.session.commit()

        # Log verification
        log_user_activity(user_id, "user_verified", "User verified their account")
        logger.info(f"User {user_id} verified successfully")
        return True

    logger.warning(f"User {user_id} provided invalid verification code")
    return False

@handle_db_error
def update_user_profile(user_id: int, field: str, value: Any) -> bool:
    """
    Update a user's investment profile settings.

    Args:
        user_id: Telegram user ID
        field: Field name to update (risk_profile, investment_horizon, investment_goals, etc.)
        value: New value for the field

    Returns:
        True if update successful, False otherwise
    """
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user:
        logger.warning(f"Cannot update profile for user {user_id}: user not found")
        return False

    try:
        # Update the specified field
        if hasattr(user, field):
            setattr(user, field, value)
            db.session.commit()

            # Log profile update
            log_user_activity(
                user_id, 
                "profile_updated", 
                f"User profile updated: {field}={value}"
            )
            logger.info(f"User {user_id} profile updated: {field}={value}")
            return True
        else:
            logger.error(f"Field {field} does not exist in User model")
            return False
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        db.session.rollback()
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

    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)

    if not user:
        logger.warning(f"Cannot generate verification code for user {user_id}: user not found")
        return None

    # Generate a random 6-character alphanumeric code
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    user.verification_code = verification_code
    db.session.commit()

    # Log code generation
    log_user_activity(user_id, "verification_code_generated", "Verification code generated")

    logger.info(f"Verification code generated for user {user_id}")
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
    # Direct primary key lookup since id IS the Telegram ID
    user = User.query.get(user_id)
    if user:
        user.message_count = user.message_count + 1 if hasattr(user, 'message_count') else 1
        user.last_active = datetime.datetime.utcnow()
        logger.debug(f"Updated message count for user {user_id} to {user.message_count}")
    else:
        logger.warning(f"Cannot update message count for user {user_id}: user not found")

    try:
        db.session.commit()
        logger.debug(f"Logged query from user {user_id}, command: {command}")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error logging user query: {e}")
        raise

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
    try:
        # Check if user_id fits in the database column (BigInteger)
        if user_id > 9223372036854775807:  # Max value for a signed 64-bit integer
            logger.warning(f"User ID {user_id} is too large for the database, cannot log activity")
            return None

        # Based on our database schema query, these columns exist
        activity = UserActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.datetime.utcnow()
        )
        db.session.add(activity)
        db.session.commit()

        return activity
    except Exception as e:
        logger.error(f"Error logging user activity: {e}")
        db.session.rollback()
        return None

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
    try:
        # Check if user_id fits in the database column (BigInteger)
        if user_id and user_id > 9223372036854775807:  # Max value for a signed 64-bit integer
            logger.warning(f"User ID {user_id} is too large for the database, logging error without user_id")
            user_id = None

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
    except Exception as e:
        logger.error(f"Error logging error to database: {e}")
        db.session.rollback()
        # At least log to file since we can't log to the database
        logger.error(f"Original error: {error_type} - {error_message}")
        return None

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
    from sqlalchemy import create_engine
    from sqlalchemy.orm import scoped_session, sessionmaker

    try:
        if not hasattr(db, 'session') or db.session.is_active == False:
            engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
            db.session = scoped_session(sessionmaker(bind=engine))

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
    except Exception as e:
        logger.error(f"Error updating bot statistics: {e}")
        if hasattr(db, 'session'):
            db.session.rollback()
        return None


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