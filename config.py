#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration management for the Telegram cryptocurrency pool bot
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

def load_config():
    """
    Load configuration from config.json file.
    Returns a dictionary with configuration values.
    """
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info("Configuration loaded successfully")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        # Return default configuration
        return {
            "pools": [
                # Default Raydium pools to track
                "58oQChx4yWmvKdwLLZzBi4ChoCc2fqCUWBkwMihLYQo2", # SOL-USDC
                "AVs9TA4nWDzfPJE9gGVNJMVhcQy3V9PGazuz33BfG2RA", # SOL-USDT
                "6UmmUiYoBjSrhakAobJw8BvkmJtDVxaeBtbt7rxWo1mg", # RAY-USDC
                "AVoHTGKPFP6irad4cr5ML5YbRzAZsZLnLES3CJLXaP8K", # RAY-SOL
                "2QXXnRnSBi4QY8Pe9VMXVJpE2RfpPaP4RLKjAHD99JYy", # RAY-USDT
            ],
            "api": {
                "raydium_base_url": "https://api.raydium.io/v2",
                # Set default rate limits
                "rate_limit": {
                    "calls_per_minute": 60,
                    "retry_after": 60
                },
                # Set default cache settings
                "cache": {
                    "pool_data_ttl": 300,  # 5 minutes
                    "simulation_ttl": 600  # 10 minutes
                }
            }
        }
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in configuration file: {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}
