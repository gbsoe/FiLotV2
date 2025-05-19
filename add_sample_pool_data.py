#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to add sample pool data to the database for testing interactive buttons
"""

import datetime
import logging
from app import app
from models import db, Pool

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sample pool data
sample_pools = [
    {
        "id": "SOL-USDC-V4",
        "token_a_symbol": "SOL",
        "token_b_symbol": "USDC",
        "token_a_price": 150.25,
        "token_b_price": 1.0,
        "apr_24h": 12.5,
        "apr_7d": 11.8,
        "apr_30d": 10.9,
        "tvl": 5420000.0,
        "fee": 0.0025,  # 0.25%
        "volume_24h": 1250000.0,
        "tx_count_24h": 2150
    },
    {
        "id": "BONK-USDC-V4",
        "token_a_symbol": "BONK",
        "token_b_symbol": "USDC",
        "token_a_price": 0.000015,
        "token_b_price": 1.0,
        "apr_24h": 45.2,
        "apr_7d": 42.5,
        "apr_30d": 38.7,
        "tvl": 1250000.0,
        "fee": 0.003,  # 0.3%
        "volume_24h": 850000.0,
        "tx_count_24h": 3250
    },
    {
        "id": "PYTH-SOL-V4",
        "token_a_symbol": "PYTH",
        "token_b_symbol": "SOL",
        "token_a_price": 0.75,
        "token_b_price": 150.25,
        "apr_24h": 28.7,
        "apr_7d": 26.2,
        "apr_30d": 24.5,
        "tvl": 2150000.0,
        "fee": 0.002,  # 0.2%
        "volume_24h": 920000.0,
        "tx_count_24h": 1850
    },
    {
        "id": "JTO-USDC-V4",
        "token_a_symbol": "JTO",
        "token_b_symbol": "USDC",
        "token_a_price": 2.15,
        "token_b_price": 1.0,
        "apr_24h": 32.8,
        "apr_7d": 31.5,
        "apr_30d": 29.2,
        "tvl": 1850000.0,
        "fee": 0.0025,  # 0.25%
        "volume_24h": 750000.0,
        "tx_count_24h": 1650
    },
    {
        "id": "RAY-SOL-V4",
        "token_a_symbol": "RAY",
        "token_b_symbol": "SOL",
        "token_a_price": 0.95,
        "token_b_price": 150.25,
        "apr_24h": 18.5,
        "apr_7d": 17.8,
        "apr_30d": 16.9,
        "tvl": 3250000.0,
        "fee": 0.0025,  # 0.25%
        "volume_24h": 1050000.0,
        "tx_count_24h": 1950
    }
]

def add_sample_pool_data():
    """Add sample pool data to the database."""
    with app.app_context():
        try:
            # Check if we already have pool data
            existing_count = Pool.query.count()
            
            if existing_count > 0:
                logger.info(f"Database already contains {existing_count} pools. Skipping sample data insertion.")
                return
            
            # Add sample pool data
            for pool_data in sample_pools:
                pool = Pool(
                    id=pool_data["id"],
                    token_a_symbol=pool_data["token_a_symbol"],
                    token_b_symbol=pool_data["token_b_symbol"],
                    token_a_price=pool_data["token_a_price"],
                    token_b_price=pool_data["token_b_price"],
                    apr_24h=pool_data["apr_24h"],
                    apr_7d=pool_data["apr_7d"],
                    apr_30d=pool_data["apr_30d"],
                    tvl=pool_data["tvl"],
                    fee=pool_data["fee"],
                    volume_24h=pool_data["volume_24h"],
                    tx_count_24h=pool_data["tx_count_24h"],
                    last_updated=datetime.datetime.utcnow()
                )
                db.session.add(pool)
            
            db.session.commit()
            logger.info(f"Added {len(sample_pools)} sample pools to the database")
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding sample pool data: {e}")

if __name__ == "__main__":
    add_sample_pool_data()