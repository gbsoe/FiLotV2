#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for the Raydium API client
"""

from raydium_client import RaydiumClient

def test_api_health():
    """Test the API health endpoint"""
    client = RaydiumClient()
    print("🔍 Raydium API Health Check:")
    try:
        health = client.check_health()
        print(f"✅ Health Status: {health}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_api_pools():
    """Test the API pools endpoint"""
    client = RaydiumClient()
    print("\n🔍 Raydium API Pools Check:")
    try:
        pools = client.get_pools()
        if pools:
            print(f"✅ Successfully retrieved pools data")
            print(f"Categories: {', '.join(pools.keys())}")
            for category, pool_list in pools.items():
                print(f"  - {category}: {len(pool_list)} pools")
            
            # Print first pool from first category if available
            first_category = list(pools.keys())[0]
            if pools[first_category]:
                print(f"\nSample pool from {first_category}:")
                for key, value in pools[first_category][0].items():
                    print(f"  {key}: {value}")
        else:
            print("❌ No pools data returned (empty response)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_health()
    test_api_pools()