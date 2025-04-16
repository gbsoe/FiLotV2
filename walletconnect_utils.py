"""
WalletConnect utilities for the Telegram cryptocurrency pool bot
"""

import os
import json
import logging
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, Union, Tuple
import aiohttp
import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Check for WalletConnect Project ID
WALLETCONNECT_PROJECT_ID = os.environ.get("WALLETCONNECT_PROJECT_ID")
if not WALLETCONNECT_PROJECT_ID:
    logger.warning("WALLETCONNECT_PROJECT_ID not found in environment variables")

# Database connection string
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment variables")

#########################
# Database Setup
#########################

def get_db_connection():
    """Create a database connection."""
    try:
        connection = psycopg2.connect(DATABASE_URL)
        connection.autocommit = True
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise e

def init_db():
    """Initialize the database tables needed for WalletConnect sessions."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create wallet_sessions table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                session_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                telegram_user_id BIGINT,
                status VARCHAR(50) DEFAULT 'pending'
            )
        """)
        
        cursor.close()
        conn.close()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

#########################
# WalletConnect Integration
#########################

async def create_walletconnect_session(telegram_user_id: int) -> Dict[str, Any]:
    """
    Create a new WalletConnect session using Reown API.
    
    Args:
        telegram_user_id: Telegram user ID to associate with the session
        
    Returns:
        Dictionary with session details including URI
    """
    if not WALLETCONNECT_PROJECT_ID:
        return {
            "success": False, 
            "error": "WalletConnect Project ID not configured"
        }
    
    try:
        # Generate a unique session ID
        session_id = str(uuid.uuid4())
        
        # Create a WalletConnect session using Reown API
        async with aiohttp.ClientSession() as session:
            url = "https://api.reown.com/v1/walletconnect/session"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {WALLETCONNECT_PROJECT_ID}"
            }
            payload = {
                "requiredNamespaces": {
                    "solana": {
                        "methods": ["solana_signTransaction", "solana_signMessage"],
                        "chains": ["solana:mainnet"],
                        "events": ["connect", "disconnect"]
                    }
                },
                "metadata": {
                    "name": "FiLot Investment Advisor",
                    "description": "AI Investment Advisor for DeFi",
                    "url": "https://filot.app",
                    "icons": ["https://filot.app/icon.png"]
                }
            }
            
            response = await session.post(url, headers=headers, json=payload)
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"Error from Reown API: {error_text}")
                return {
                    "success": False, 
                    "error": f"Error creating WalletConnect session: {error_text}"
                }
                
            data = await response.json()
            
            if "uri" not in data:
                return {
                    "success": False, 
                    "error": "Failed to generate connection URI"
                }
            
            # Save session details to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            session_data = {
                "uri": data["uri"],
                "created": int(time.time()),
                "reown_session_id": data.get("id", "")
            }
            
            cursor.execute(
                """
                INSERT INTO wallet_sessions 
                (session_id, session_data, telegram_user_id, status) 
                VALUES (%s, %s, %s, %s)
                """, 
                (session_id, Json(session_data), telegram_user_id, "pending")
            )
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "session_id": session_id,
                "uri": data["uri"],
                "telegram_user_id": telegram_user_id
            }
            
    except Exception as e:
        logger.error(f"Error creating WalletConnect session: {e}")
        return {
            "success": False, 
            "error": f"Error creating WalletConnect session: {e}"
        }

async def check_walletconnect_session(session_id: str) -> Dict[str, Any]:
    """
    Check the status of a WalletConnect session.
    
    Args:
        session_id: The session ID to check
        
    Returns:
        Dictionary with session status
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT session_data, status, telegram_user_id FROM wallet_sessions WHERE session_id = %s",
            (session_id,)
        )
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return {"success": False, "error": "Session not found"}
            
        session_data, status, telegram_user_id = result
        
        # If using Reown API, we'd check the session status here
        
        return {
            "success": True,
            "session_id": session_id,
            "status": status,
            "telegram_user_id": telegram_user_id,
            "session_data": session_data
        }
        
    except Exception as e:
        logger.error(f"Error checking WalletConnect session: {e}")
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
    try:
        # Get session data first
        session_info = await check_walletconnect_session(session_id)
        
        if not session_info["success"]:
            return session_info
            
        # If using Reown API, we'd send a disconnect request here
        
        # Delete the session from database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM wallet_sessions WHERE session_id = %s",
            (session_id,)
        )
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": "Session terminated successfully"
        }
        
    except Exception as e:
        logger.error(f"Error killing WalletConnect session: {e}")
        return {
            "success": False, 
            "error": f"Error killing WalletConnect session: {e}"
        }

async def get_user_walletconnect_sessions(telegram_user_id: int) -> Dict[str, Any]:
    """
    Get all WalletConnect sessions for a user.
    
    Args:
        telegram_user_id: Telegram user ID
        
    Returns:
        Dictionary with list of sessions
    """
    try:
        conn = get_db_connection()
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
                "created_at": created_at.isoformat(),
                "uri": session_data.get("uri", ""),
                # Additional fields as needed
            })
        
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "telegram_user_id": telegram_user_id,
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error getting user WalletConnect sessions: {e}")
        return {
            "success": False, 
            "error": f"Error getting user WalletConnect sessions: {e}"
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