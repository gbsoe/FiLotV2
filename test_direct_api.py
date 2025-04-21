"""
Simple script to directly test the API without any other library dependencies
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URLs to test
base_url = "https://raydium-trader-filot.replit.app"
api_key = os.environ.get("RAYDIUM_API_KEY", "raydium_filot_api_key_125fje90")
headers = {
    "x-api-key": api_key,
    "Content-Type": "application/json"
}

endpoints = [
    "/health",
    "/api/pools",
    "/api/pool/3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv",
    "/api/pool/CYbD9RaToYMtWKA7QZyoLahnHdWq553Vm62Lh6qWtuxq",
    "/api/pool/2AXXcN6oN9bBT5owwmTH53C7QHUXvhLeu718Kqt8rvY2"
]

print(f"Testing API endpoints with API key: {api_key}")
for endpoint in endpoints:
    url = f"{base_url}{endpoint}"
    print(f"\nTesting: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Print only first part of the response
        data = response.json()
        print(f"  Status: {response.status_code} - SUCCESS")
        
        # For pool endpoints, show token pair and APR
        if "/api/pool/" in endpoint and "pool" in data:
            pool = data["pool"]
            print(f"  Pool ID: {pool.get('id', 'N/A')}")
            print(f"  Token Pair: {pool.get('tokenPair', 'N/A')}")
            print(f"  APR: {pool.get('apr24h', pool.get('apr', 'N/A'))}%")
            print(f"  TVL: ${pool.get('liquidityUsd', pool.get('liquidity', 'N/A'))}")
        elif "/api/pools" == endpoint:
            # Show counts of pools in each category
            best_performance = data.get("pools", {}).get("bestPerformance", [])
            top_stable = data.get("pools", {}).get("topStable", [])
            print(f"  Best Performance Pools: {len(best_performance)}")
            print(f"  Top Stable Pools: {len(top_stable)}")
            
            # Show first pool of each type if available
            if best_performance:
                pool = best_performance[0]
                print(f"  First Best Performance Pool:")
                print(f"    ID: {pool.get('id', 'N/A')}")
                print(f"    Token Pair: {pool.get('tokenPair', 'N/A')}")
        else:
            # Just print the first few keys
            print(f"  Response keys: {list(data.keys())[:5]}")
    except requests.exceptions.RequestException as e:
        print(f"  ERROR: {e}")