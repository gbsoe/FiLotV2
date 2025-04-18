#!/usr/bin/env python3
import sys
import os
sys.path.append(os.getcwd())

# Create a simple Pool class for testing
class MockPool:
    def __init__(self, id, token_a_symbol, token_b_symbol, apr_24h, apr_7d, apr_30d, tvl, token_a_price):
        self.id = id
        self.token_a_symbol = token_a_symbol
        self.token_b_symbol = token_b_symbol
        self.apr_24h = apr_24h
        self.apr_7d = apr_7d
        self.apr_30d = apr_30d
        self.tvl = tvl
        self.token_a_price = token_a_price
        self.fee = 0.003  # 0.3%

# Create mock pools for testing
def create_mock_pools():
    pools = [
        MockPool(
            "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv", 
            "SOL", "USDC", 
            134.00, 68.51, 95.68, 
            9051107.35, 131.7
        ),
        MockPool(
            "2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2", 
            "SOL", "RAY", 
            74.95, 36.56, 49.97, 
            3641303.90, 131.7
        ),
        MockPool(
            "CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq", 
            "SOL", "USDC", 
            49.48, 27.10, 33.08, 
            2045186.01, 131.7
        ),
        MockPool(
            "Ar1owSzR5L6LXBYm7kJsEU9vHzCpexGZY6nqfuh1WjG5", 
            "ETH", "USDC", 
            23.25, 15.63, 18.41, 
            5829123.45, 3045.2
        ),
        MockPool(
            "HQ8oeaHofBJyM8DMhCD5YasRXjqT3cGjcCHcVNnYEGS1", 
            "SOL", "USDT", 
            42.19, 32.64, 36.75, 
            1876502.34, 131.7
        ),
    ]
    return pools

# Import the formatting functions
from utils import format_pool_info, format_simulation_results

# Test the formatting functions
def test_format_pool_info():
    pools = create_mock_pools()
    formatted = format_pool_info(pools)
    print("===== /info Command Output =====")
    print(formatted)
    print("\n")

def test_format_simulation_results():
    pools = create_mock_pools()
    amount = 1000.0
    formatted = format_simulation_results(pools, amount)
    print("===== /simulate Command Output =====")
    print(formatted)
    print("\n")

if __name__ == "__main__":
    test_format_pool_info()
    test_format_simulation_results()
