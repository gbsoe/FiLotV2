#!/usr/bin/env python3
"""
Test script to verify the simulate command formatting
"""

import logging
import sys
import os

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add current directory to sys.path to allow imports
sys.path.append(os.getcwd())

# Import the necessary modules
from response_data import get_pool_data
from utils import format_simulation_results

def test_simulation(amount=1000.0):
    """Test the simulate command output with a specific amount."""
    logger.info(f"Testing simulation with amount: ${amount}")
    
    # Get pool data
    pool_data = get_pool_data()
    logger.info(f"Got {len(pool_data.get('topAPR', []))} pools in topAPR category")
    
    # Test the simulation results formatting
    formatted = format_simulation_results(pool_data.get('topAPR', []), amount)
    print("\n" + "="*50)
    print("SIMULATE COMMAND OUTPUT:")
    print(formatted)
    print("="*50)

if __name__ == "__main__":
    # Test with default amount
    test_simulation(1000.0)
    
    # Test with a larger amount
    test_simulation(10000.0)