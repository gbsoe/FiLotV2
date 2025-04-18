#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for bot's pool data retrieval
"""

import asyncio
from response_data import get_pool_data
import bot

async def test_bot_pool_data():
    print("Testing Bot's pool data retrieval...")
    try:
        # Test the bot's pool data retrieval
        pools = await bot.get_pool_data()
        if pools:
            print(f"✅ Bot retrieved {len(pools)} pools")
            print(f"First pool: {pools[0].token_a_symbol}/{pools[0].token_b_symbol} with APR: {pools[0].apr_24h}%")
        else:
            print("❌ No pools returned")
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test the direct fallback data
    try:
        data = get_pool_data()
        print(f"✅ Direct fallback data contains {len(data.get('topAPR', []))} top APR pools")
        print(f"First pool: {data['topAPR'][0]['pairName']} with APR: {data['topAPR'][0]['apr']}%")
    except Exception as e:
        print(f"❌ Error getting fallback data: {e}")

if __name__ == "__main__":
    asyncio.run(test_bot_pool_data())