#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
One-time script to fix the wallet_sessions table if it's missing the user_id column
"""

import os
import sys
import traceback
import time
from app import app, db
from sqlalchemy import text

def fix_wallet_sessions_table():
    """
    Fix the wallet_sessions table by adding the user_id column if it's missing
    """
    print("Checking and fixing wallet_sessions table...")
    
    try:
        with app.app_context():
            # Check if the column exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name='wallet_sessions' AND column_name='user_id'
                );
            """)
            result = db.session.execute(check_query).scalar()
            
            if not result:
                print("user_id column is missing from wallet_sessions table. Adding it...")
                
                # Add the user_id column
                add_column_query = text("""
                    ALTER TABLE wallet_sessions 
                    ADD COLUMN user_id BIGINT REFERENCES users(id);
                """)
                db.session.execute(add_column_query)
                db.session.commit()
                
                print("Successfully added user_id column to wallet_sessions table.")
            else:
                print("user_id column already exists in wallet_sessions table.")
            
            # Print the current table structure for verification
            desc_query = text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'wallet_sessions';")
            columns = db.session.execute(desc_query).fetchall()
            
            print("\nCurrent wallet_sessions table structure:")
            for column in columns:
                print(f"  - {column[0]}: {column[1]}")
                
            print("\nTable fix completed successfully!")
            
    except Exception as e:
        print(f"Error fixing wallet_sessions table: {e}")
        print(traceback.format_exc())
        return False
        
    return True

def recreate_wallet_sessions_table():
    """
    Drop and recreate the wallet_sessions table if fixing it doesn't work
    WARNING: This will lose all existing wallet session data
    """
    print("Recreating wallet_sessions table from scratch...")
    
    try:
        with app.app_context():
            # Drop the table if it exists
            drop_query = text("DROP TABLE IF EXISTS wallet_sessions;")
            db.session.execute(drop_query)
            db.session.commit()
            
            # Let SQLAlchemy recreate the table with the correct schema
            from models import WalletSession
            db.create_all()
            
            print("Successfully recreated wallet_sessions table!")
    except Exception as e:
        print(f"Error recreating wallet_sessions table: {e}")
        print(traceback.format_exc())
        return False
        
    return True

if __name__ == "__main__":
    # Try to fix the table first
    if not fix_wallet_sessions_table():
        print("\nFix failed. Attempting to recreate the table...")
        if recreate_wallet_sessions_table():
            print("\nRecreation successful!")
        else:
            print("\nBoth fix and recreation failed. Please check the database manually.")
            sys.exit(1)
            
    print("\nScript completed successfully!")