"""
WalletConnect utilities for the Telegram cryptocurrency pool bot
Integrates with the Solana wallet service for improved wallet connectivity and transaction handling.
"""

import os
import json
import logging
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, Union, Tuple
import urllib.parse  # Standard library for URL encoding
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import SolanaWalletService
try:
    from solana_wallet_service import get_wallet_service
    SOLANA_SERVICE_AVAILABLE = True
    logger.info("Solana wallet service is available")
except ImportError:
    logger.warning("Solana wallet service not available, will use legacy implementation")
    SOLANA_SERVICE_AVAILABLE = False

# Try to import optional dependencies with fallbacks
try:
    import psycopg2
    from psycopg2.extras import Json
    PSYCOPG2_AVAILABLE = True
except ImportError:
    logger.warning("psycopg2 not available, will use mock database functionality")
    PSYCOPG2_AVAILABLE = False
    # Define a mock Json class
    class Json:
        def __init__(self, data):
            self.data = data

try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not available, will use environment variables directly")

# Check for WalletConnect Project ID
WALLETCONNECT_PROJECT_ID = os.environ.get("WALLETCONNECT_PROJECT_ID")
if not WALLETCONNECT_PROJECT_ID:
    logger.warning("WALLETCONNECT_PROJECT_ID not found in environment variables")

# Check for Solana RPC URL
SOLANA_RPC_URL = os.environ.get("SOLANA_RPC_URL")
if not SOLANA_RPC_URL:
    logger.warning("SOLANA_RPC_URL not found in environment variables, will use public endpoint")

# Database connection string
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL and PSYCOPG2_AVAILABLE:
    logger.warning("DATABASE_URL not found in environment variables, database features will be limited")

#########################
# Database Setup
#########################

def get_db_connection():
    """Create a database connection."""
    # Skip if psycopg2 is not available or DATABASE_URL is not set
    if not PSYCOPG2_AVAILABLE or not DATABASE_URL:
        logger.warning("Database connection not available - psycopg2 or DATABASE_URL missing")
        return None
        
    try:
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize the database tables needed for WalletConnect sessions."""
    # Import app at function level to avoid circular imports
    from app import app
    
    # Skip if database connection not available
    if not PSYCOPG2_AVAILABLE or not DATABASE_URL:
        logger.warning("Skipping database initialization - database not available")
        return False
    
    try:
        # Use app context for database operations
        with app.app_context():
            conn = get_db_connection()
            if not conn:
                logger.warning("Could not connect to database - skipping initialization")
                return False
                
            cursor = conn.cursor()
            
            # Create wallet_sessions table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wallet_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    session_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    telegram_user_id BIGINT,
                    status VARCHAR(50) DEFAULT 'pending',
                    wallet_address TEXT,
                    expires_at TIMESTAMP
                )
            """)
            
            cursor.close()
            conn.close()
            logger.info("Database initialized successfully")
            return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        return False

#########################
# WalletConnect Integration
#########################

async def create_walletconnect_session(telegram_user_id: int) -> Dict[str, Any]:
    """
    Create a new WalletConnect session using WalletConnect protocol with enhanced security.
    
    Args:
        telegram_user_id: Telegram user ID to associate with the session
        
    Returns:
        Dictionary with session details including URI
    """
    # Import app at function level to avoid circular imports
    from app import app
    
    # If Solana wallet service is available, use it instead of the legacy implementation
    if SOLANA_SERVICE_AVAILABLE:
        try:
            # Get wallet service
            wallet_service = get_wallet_service()
            
            # Create session
            result = await wallet_service.create_session(telegram_user_id)
            
            # Save to database if successful and database is available
            if result["success"] and PSYCOPG2_AVAILABLE and DATABASE_URL:
                try:
                    with app.app_context():
                        conn = get_db_connection()
                        if conn:
                            cursor = conn.cursor()
                            
                            # Convert to ISO format if datetime objects
                            expires_at = result.get("expires_at")
                            if isinstance(expires_at, str):
                                # Already in correct format
                                pass
                            elif hasattr(expires_at, "isoformat"):
                                # Convert datetime to string
                                expires_at = expires_at.isoformat()
                            else:
                                # Use default expiration if not available
                                expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
                            
                            session_data = {
                                "uri": result.get("uri", ""),
                                "qr_uri": result.get("qr_uri", ""),
                                "created": int(time.time()),
                                "session_id": result["session_id"],
                                "security_level": result.get("security_level", "read_only"),
                                "expires_at": expires_at,
                            }
                            
                            cursor.execute(
                                """
                                INSERT INTO wallet_sessions 
                                (session_id, session_data, telegram_user_id, status, wallet_address, expires_at) 
                                VALUES (%s, %s, %s, %s, %s, %s)
                                """, 
                                (
                                    result["session_id"], 
                                    Json(session_data), 
                                    telegram_user_id, 
                                    result.get("status", "pending"),
                                    result.get("wallet_address", None),
                                    expires_at
                                )
                            )
                            
                            cursor.close()
                            conn.close()
                            logger.info(f"Saved WalletConnect session to database")
                except Exception as db_error:
                    logger.warning(f"Could not save WalletConnect session to database: {db_error}")
            
            # Return the result from the wallet service
            return result
            
        except Exception as e:
            logger.error(f"Error creating session with Solana wallet service: {e}")
            logger.info("Falling back to legacy implementation")
            # Fall through to legacy implementation
    
    # Legacy implementation
    logger.info("Using legacy WalletConnect implementation")
    if not WALLETCONNECT_PROJECT_ID:
        logger.warning("WalletConnect Project ID not configured, using basic URI format")
    
    try:
        # Generate a unique session ID with stronger randomness
        session_id = str(uuid.uuid4())
        
        # Log session creation attempt with security audit
        logger.info(f"Secure wallet connection requested for user {telegram_user_id}")
        
        # Generate a WalletConnect URI
        try:
            logger.info(f"Creating WalletConnect connection for user {telegram_user_id}")
            
            # Generate required components
            topic = uuid.uuid4().hex
            # Secure random key for encryption
            sym_key = uuid.uuid4().hex + uuid.uuid4().hex[:32]  # Make sure it's not too long
            # Current relay server
            relay_url = "wss://relay.walletconnect.org"
            
            # Standard WalletConnect v2 format
            wc_uri = f"wc:{topic}@2?relay-protocol=irn&relay-url={relay_url}&symKey={sym_key}"
            
            # Include project ID in the WalletConnect URI if available
            if WALLETCONNECT_PROJECT_ID:
                wc_uri = f"{wc_uri}&projectId={WALLETCONNECT_PROJECT_ID}"
            
            # URL encode for compatibility with different wallet apps
            uri_encoded = urllib.parse.quote(wc_uri)
            
            # Use standard format that works with most wallets
            deep_link_uri = f"https://walletconnect.com/wc?uri={uri_encoded}"
            
            # Create the data structure with all necessary information
            data = {
                "uri": deep_link_uri,
                "raw_wc_uri": wc_uri,  # Store the raw wc: URI for display to users
                "id": topic,  # Use the topic as the ID
                "relay": relay_url,
                "symKey": sym_key,
                "version": "2"
            }
            
            logger.info(f"Generated WalletConnect URI successfully")
            
        except Exception as wc_error:
            logger.error(f"Error creating WalletConnect URI: {wc_error}", exc_info=True)
            # Fallback to a simpler URI format if there was an error
            topic = uuid.uuid4().hex[:10]  # Shorter for simplicity
            wc_uri = f"wc:{topic}@2"
            data = {
                "uri": f"https://walletconnect.com/wc?uri={urllib.parse.quote(wc_uri)}",
                "raw_wc_uri": wc_uri,
                "id": topic
            }
            logger.info(f"Generated fallback WalletConnect URI")
        
        # Try to save to database if available, but continue even if it fails
        try:
            if PSYCOPG2_AVAILABLE and DATABASE_URL:
                # Use app context for database operations
                with app.app_context():
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        
                        expires_at = datetime.now() + timedelta(hours=1)
                        
                        session_data = {
                            "uri": data["uri"],
                            "raw_wc_uri": data.get("raw_wc_uri", ""),
                            "created": int(time.time()),
                            "session_id": data.get("id", ""),
                            "security_level": "read_only",
                            "expires_at": expires_at.isoformat(),
                        }
                        
                        cursor.execute(
                            """
                            INSERT INTO wallet_sessions 
                            (session_id, session_data, telegram_user_id, status, expires_at) 
                            VALUES (%s, %s, %s, %s, %s)
                            """, 
                            (session_id, Json(session_data), telegram_user_id, "pending", expires_at)
                        )
                        
                        cursor.close()
                        conn.close()
                        logger.info(f"Saved WalletConnect session to database")
        except Exception as db_error:
            # Just log the error but continue - we don't need the database for the core functionality
            logger.warning(f"Could not save WalletConnect session to database: {db_error}")
        
        # Return the successful result regardless of database status
        return {
            "success": True,
            "session_id": session_id,
            "uri": data["uri"],
            "raw_wc_uri": data.get("raw_wc_uri", ""),
            "telegram_user_id": telegram_user_id,
            "security_level": "read_only",
            "expires_in_seconds": 3600
        }
            
    except Exception as e:
        logger.error(f"Error creating WalletConnect session: {e}")
        return {
            "success": False, 
            "error": f"Error creating WalletConnect session: {e}"
        }

async def check_walletconnect_session(session_id: str) -> Dict[str, Any]:
    """
    Check the status of a WalletConnect session with enhanced security checks.
    
    Args:
        session_id: The session ID to check
        
    Returns:
        Dictionary with session status and security information
    """
    # Import app at function level to avoid circular imports
    from app import app
    
    # If Solana wallet service is available, use it instead of the legacy implementation
    if SOLANA_SERVICE_AVAILABLE:
        try:
            # Get wallet service
            wallet_service = get_wallet_service()
            
            # Check session
            result = await wallet_service.check_session(session_id)
            
            # Return the result from the wallet service
            return result
            
        except Exception as e:
            logger.error(f"Error checking session with Solana wallet service: {e}")
            logger.info("Falling back to legacy implementation")
            # Fall through to legacy implementation
    
    # Legacy implementation
    logger.info("Using legacy session check implementation")
    
    # If the database is not available, provide some basic info
    if not PSYCOPG2_AVAILABLE or not DATABASE_URL:
        logger.warning("Database not available for session check, providing default response")
        return {
            "success": True,
            "session_id": session_id,
            "status": "unknown",
            "message": "Session status cannot be determined without database access",
            "security_level": "unknown"
        }
    
    try:
        # Use app context for database operations
        with app.app_context():
            conn = get_db_connection()
            if not conn:
                logger.warning("Could not connect to database for session check")
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": "unknown",
                    "message": "Database connection failed, session status unknown",
                    "security_level": "unknown"
                }
                
            cursor = conn.cursor()
            
            try:
                cursor.execute(
                    "SELECT session_data, status, telegram_user_id, created_at FROM wallet_sessions WHERE session_id = %s",
                    (session_id,)
                )
                
                result = cursor.fetchone()
                
                if not result:
                    cursor.close()
                    conn.close()
                    return {"success": False, "error": "Session not found"}
                    
                session_data, status, telegram_user_id, created_at = result
                
                # Check if session has expired (default: 1 hour timeout)
                current_time = int(time.time())
                expires_at = session_data.get("expires_at", 0)
                
                if expires_at > 0 and current_time > expires_at:
                    # Session has expired, mark it as expired and return error
                    logger.info(f"Session {session_id} has expired")
                    
                    try:
                        # Update session status in database
                        cursor.execute(
                            "UPDATE wallet_sessions SET status = 'expired' WHERE session_id = %s",
                            (session_id,)
                        )
                    except Exception as update_error:
                        logger.warning(f"Could not update session status: {update_error}")
                    
                    cursor.close()
                    conn.close()
                    
                    return {
                        "success": False,
                        "error": "Session has expired. Please create a new wallet connection.",
                        "session_id": session_id,
                        "expired": True
                    }
                
                # Add security level information to the response
                security_level = session_data.get("security_level", "unknown")
                permissions = session_data.get("permissions_requested", [])
                
                cursor.close()
                conn.close()
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "status": status,
                    "telegram_user_id": telegram_user_id,
                    "session_data": session_data,
                    "security_level": security_level,
                    "permissions": permissions,
                    "created_at": created_at.isoformat() if created_at else None,
                    "expires_at": expires_at if expires_at > 0 else None,
                    "expires_in_seconds": max(0, expires_at - current_time) if expires_at > 0 else None
                }
                
            except Exception as db_error:
                if cursor:
                    cursor.close()
                if conn and conn.closed == 0:
                    conn.close()
                raise db_error
            
    except Exception as e:
        logger.error(f"Error checking WalletConnect session: {e}", exc_info=True)
        return {
            "success": False, 
            "error": f"Error checking WalletConnect session: {e}"
        }

async def kill_walletconnect_session(session_id: str) -> Dict[str, Any]:
    """
    Kill a WalletConnect session.
    
    Args:
        session_id: The session ID to kill
        
    Returns:
        Dictionary with operation result
    """
    # Import app at function level to avoid circular imports
    from app import app
    
    # If Solana wallet service is available, use it instead of the legacy implementation
    if SOLANA_SERVICE_AVAILABLE:
        try:
            # Get wallet service
            wallet_service = get_wallet_service()
            
            # Disconnect wallet
            result = await wallet_service.disconnect_wallet(session_id)
            
            # Return the result from the wallet service
            return result
            
        except Exception as e:
            logger.error(f"Error disconnecting wallet with Solana wallet service: {e}")
            logger.info("Falling back to legacy implementation")
            # Fall through to legacy implementation
    
    # Legacy implementation
    logger.info("Using legacy session deletion implementation")
    
    # If the database is not available, just return success
    if not PSYCOPG2_AVAILABLE or not DATABASE_URL:
        logger.warning("Database not available for session deletion, skipping")
        return {
            "success": True,
            "message": "Session terminated (database unavailable)",
            "warning": "Database operations skipped - database unavailable"
        }
    
    try:
        # Use app context for database operations
        with app.app_context():
            # Skip database check if not available
            conn = get_db_connection()
            if not conn:
                logger.warning("Could not connect to database for session deletion")
                return {
                    "success": True,
                    "message": "Session considered terminated (database unreachable)",
                    "warning": "Database operations skipped - could not connect"
                }
                
            try:
                cursor = conn.cursor()
                
                # Simple deletion without checking first
                cursor.execute(
                    "DELETE FROM wallet_sessions WHERE session_id = %s",
                    (session_id,)
                )
                
                cursor.close()
                conn.close()
                
            except Exception as db_error:
                logger.error(f"Database error while killing session: {db_error}", exc_info=True)
                if conn and conn.closed == 0:
                    conn.close()
                return {
                    "success": True,
                    "message": "Session considered terminated (database error)",
                    "warning": f"Database error: {str(db_error)}"
                }
        
        return {
            "success": True,
            "message": "Session terminated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error killing WalletConnect session: {e}", exc_info=True)
        return {
            "success": True,  # Return success anyway to avoid blocking the UI
            "message": "Session considered terminated (error occurred)",
            "warning": f"Error occurred: {str(e)}"
        }

async def get_user_walletconnect_sessions(telegram_user_id: int) -> Dict[str, Any]:
    """
    Get all WalletConnect sessions for a user.
    
    Args:
        telegram_user_id: Telegram user ID
        
    Returns:
        Dictionary with list of sessions
    """
    # Import app at function level to avoid circular imports
    from app import app
    
    # If database not available, return empty list
    if not PSYCOPG2_AVAILABLE or not DATABASE_URL:
        logger.warning("Database not available for getting user sessions, returning empty list")
        return {
            "success": True,
            "telegram_user_id": telegram_user_id,
            "sessions": [],
            "warning": "Database unavailable - cannot retrieve actual sessions"
        }
    
    try:
        # Use app context for database operations
        with app.app_context():
            conn = get_db_connection()
            if not conn:
                logger.warning("Could not connect to database for getting user sessions")
                return {
                    "success": True,
                    "telegram_user_id": telegram_user_id,
                    "sessions": [],
                    "warning": "Database connection failed - cannot retrieve sessions"
                }
                
            try:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT session_id, session_data, status, created_at 
                    FROM wallet_sessions 
                    WHERE telegram_user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (telegram_user_id,)
                )
                
                sessions = []
                for row in cursor.fetchall():
                    session_id, session_data, status, created_at = row
                    sessions.append({
                        "session_id": session_id,
                        "status": status,
                        "created_at": created_at.isoformat() if created_at else None,
                        "uri": session_data.get("uri", "") if session_data else "",
                    })
                
                cursor.close()
                conn.close()
                
                return {
                    "success": True,
                    "telegram_user_id": telegram_user_id,
                    "sessions": sessions
                }
                
            except Exception as db_error:
                logger.error(f"Database error while getting user sessions: {db_error}", exc_info=True)
                if conn and conn.closed == 0:
                    conn.close()
                return {
                    "success": True,
                    "telegram_user_id": telegram_user_id,
                    "sessions": [],
                    "warning": f"Database error: {str(db_error)}"
                }
            
    except Exception as e:
        logger.error(f"Error getting user WalletConnect sessions: {e}", exc_info=True)
        return {
            "success": True,  # Return success with empty list to avoid blocking the UI
            "telegram_user_id": telegram_user_id,
            "sessions": [],
            "warning": f"Error occurred: {str(e)}"
        }

# Initialize database on module load
init_db()

# Example usage (for testing purposes)
if __name__ == "__main__":
    async def test():
        print("Creating WalletConnect session...")
        result = await create_walletconnect_session(12345)
        print(f"Session creation result: {result}")
        
        if result["success"]:
            session_id = result["session_id"]
            
            print("\nChecking session status...")
            status = await check_walletconnect_session(session_id)
            print(f"Session status: {status}")
            
            print("\nGetting user sessions...")
            user_sessions = await get_user_walletconnect_sessions(12345)
            print(f"User sessions: {user_sessions}")
            
            print("\nKilling session...")
            kill_result = await kill_walletconnect_session(session_id)
            print(f"Session kill result: {kill_result}")
    
    asyncio.run(test())