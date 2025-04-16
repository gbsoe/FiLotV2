#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database migration script to fix schema inconsistencies
"""

import os
import sys
import logging
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import text
from models import db

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)

# Configure the Flask application
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Initialize SQLAlchemy with the Flask application
db.init_app(app)

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    with app.app_context():
        try:
            result = db.session.execute(text(
                f"SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                f"WHERE table_name='{table_name}' AND column_name='{column_name}');"
            )).scalar()
            return result
        except Exception as e:
            logger.error(f"Error checking column {column_name} in {table_name}: {e}")
            return False

def add_missing_columns():
    """Add missing columns to tables."""
    with app.app_context():
        try:
            # Check and add verification_attempts column to users table
            if not check_column_exists('users', 'verification_attempts'):
                logger.info("Adding verification_attempts column to users table")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN verification_attempts INTEGER DEFAULT 0;"
                ))
                db.session.commit()
                logger.info("Added verification_attempts column to users table")

            # Check and fix other missing columns if needed
            # For example, add preferred_pools if missing
            if not check_column_exists('users', 'preferred_pools'):
                logger.info("Adding preferred_pools column to users table")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN preferred_pools JSONB;"
                ))
                db.session.commit()
                logger.info("Added preferred_pools column to users table")

            # Add investment_goals if missing
            if not check_column_exists('users', 'investment_goals'):
                logger.info("Adding investment_goals column to users table")
                db.session.execute(text(
                    "ALTER TABLE users ADD COLUMN investment_goals VARCHAR(255);"
                ))
                db.session.commit()
                logger.info("Added investment_goals column to users table")

            # Fix BigInteger columns that might be Integer in the database
            # This is a bit tricky as it requires data conversion
            # For now, logging the issue - a more comprehensive fix might require 
            # dropping and recreating the table, which could lose data
            logger.warning("Some columns might have wrong type (Integer instead of BigInteger)")
            logger.warning("To fix this properly might require a full table migration")

            # Check if any foreign key constraints need to be fixed
            # This would require more complex migration logic

            logger.info("Database schema check and fixes completed")
        except Exception as e:
            logger.error(f"Error fixing database schema: {e}")
            db.session.rollback()
            return False

        return True

def reset_session_if_needed():
    """Reset the SQLAlchemy session if needed."""
    with app.app_context():
        try:
            # Try a simple query to check if the session is working
            result = db.session.execute(text("SELECT 1")).scalar()
            if result != 1:
                raise Exception("Session test failed")
        except Exception as e:
            logger.warning(f"Session might be in a bad state: {e}")
            db.session.rollback()
            logger.info("Session rolled back")

if __name__ == "__main__":
    logger.info("Starting database schema fix script")
    
    reset_session_if_needed()
    
    if add_missing_columns():
        logger.info("Database schema fixes applied successfully")
    else:
        logger.error("Failed to apply all database schema fixes")
        sys.exit(1)
    
    logger.info("Database schema fix script completed")