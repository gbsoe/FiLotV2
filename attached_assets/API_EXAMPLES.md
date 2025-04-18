# Raydium API Service - Example API Requests

This document provides example API requests using curl to test the Raydium API service.

## Deployment URL

The API service is available at: https://raydium-trader-filot.replit.app

## Setup

Set up your API key in an environment variable for easier testing:

```bash
# API key for authentication
export RAYDIUM_API_KEY="9feae0d0af47e4948e061f2d7820461e374e040c21cf65c087166d7ed18f5ed6"

# Deployed API URL
export API_URL="https://raydium-trader-filot.replit.app"
```

## API Requests

### Root Endpoint

Get overview of available endpoints:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" $API_URL/
```

### Health Check

Check if the API is running properly:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" $API_URL/health
```

### Service Metadata

Get detailed information about the service:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" $API_URL/metadata
```

### Get Pools

Retrieve all categorized pools:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" $API_URL/pools
```

### Filter Pools

#### Filter by Token Symbol

Get pools containing SOL:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?tokenSymbol=SOL&limit=5"
```

Get pools containing USDC:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?tokenSymbol=USDC"
```

#### Filter by APR Range

Get pools with APR between 10% and 20%:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?minApr=10&maxApr=20"
```

Get pools with minimum APR of 15%:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?minApr=15"
```

#### Filter by Token Address

Get pools containing a specific token address:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?tokenAddress=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
```

#### Combined Filters

Get SOL pools with APR higher than 15%:

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?tokenSymbol=SOL&minApr=15"
```

### Cache Management

#### Get Cache Statistics

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" $API_URL/cache/stats
```

#### Clear Cache

```bash
curl -X POST -H "x-api-key: $RAYDIUM_API_KEY" $API_URL/cache/clear
```

## Error Cases

### Missing API Key

```bash
curl $API_URL/health
```

### Invalid API Key

```bash
curl -H "x-api-key: invalid_key" $API_URL/health
```

### Invalid Filter Parameters

```bash
curl -H "x-api-key: $RAYDIUM_API_KEY" "$API_URL/pools/filter?minApr=-5"
```