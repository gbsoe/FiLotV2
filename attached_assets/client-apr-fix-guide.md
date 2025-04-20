# Raydium API Client Integration Fix Guide

## Issue Summary

We've identified a discrepancy between the APR values displayed on your client implementation and the actual values from Raydium. After thorough investigation, we've confirmed that our API server is correctly receiving and processing the data from the Raydium SDK, but your client-side implementation may not be correctly displaying or refreshing this data.

### Observed Discrepancies for Pool ID: 3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv

| APR Period | Current Client Display | Raydium Website | Raydium SDK (Direct) |
|------------|------------------------|-----------------|----------------------|
| 24h APR    | 48.67%                 | 49.47%          | 49.67%               |
| 7d APR     | 47.46%                 | 58.97%          | 58.99%               |
| 30d APR    | 45.25%                 | 95.41%          | 95.52%               |

As you can see, the values from the Raydium SDK closely match what's displayed on the Raydium website, but your client is displaying significantly different values, especially for 7d and 30d APRs.

## Root Causes & Solutions

### 1. API Response Caching

**Issue**: Browsers and HTTP clients often cache API responses by default, which can cause outdated data to be displayed.

**Solutions**:
- Add a cache-busting parameter to your API requests:
  ```javascript
  const timestamp = new Date().getTime();
  const response = await api.get(`/api/pool/${poolId}?_t=${timestamp}`);
  ```
- Add appropriate cache control headers to your requests:
  ```javascript
  const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'x-api-key': API_KEY
    }
  });
  ```

### 2. Infrequent Data Refresh

**Issue**: If your client only fetches data once or infrequently, it won't reflect real-time changes in pool metrics.

**Solutions**:
- Implement a periodic refresh mechanism:
  ```javascript
  // Refresh data every 60 seconds
  setInterval(async () => {
    await refreshPoolData();
  }, 60000);
  ```
- Add a manual refresh button for users:
  ```javascript
  <button onClick={refreshPoolData}>Refresh Data</button>
  ```

### 3. Incorrect Value Parsing

**Issue**: String to number conversions can sometimes lead to precision or rounding issues.

**Solutions**:
- Ensure consistent parsing throughout your application:
  ```javascript
  // Always use parseFloat for APR values from the API
  const apr24h = parseFloat(poolData.apr24h);
  ```
- Use toFixed(2) for display, but not for calculations:
  ```javascript
  // For display only
  displayValue = `${parseFloat(aprValue).toFixed(2)}%`;
  ```

### 4. Middleware or Transform Issues

**Issue**: If you're transforming API responses before displaying them, there might be bugs in the transformation logic.

**Solutions**:
- Log the raw API response to verify what's being received:
  ```javascript
  console.log('Raw pool data:', response.data);
  ```
- Check any middleware or interceptors that might be modifying the response:
  ```javascript
  // Remove any response transformers that might be modifying the data
  const api = axios.create({
    transformResponse: [], // Disable default transformations
    // ... other config
  });
  ```

## Example Implementation

Here's a complete example of a correctly implemented client function for fetching and displaying pool data:

```javascript
// Pool fetch with proper error handling and cache busting
async function getPoolData(poolId) {
  try {
    const timestamp = new Date().getTime();
    const response = await api.get(`/api/pool/${poolId}?_t=${timestamp}`);
    
    if (!response.data || !response.data.pool) {
      console.error('Invalid response format');
      return null;
    }
    
    return response.data.pool;
  } catch (error) {
    console.error('Error fetching pool data:', error);
    return null;
  }
}

// Display function with proper parsing and formatting
function displayPoolData(poolData) {
  if (!poolData) return 'No data available';
  
  return `• Pool ID: 📋 ${poolData.id}
  Token Pair: ${poolData.tokenPair}
  24h APR: ${parseFloat(poolData.apr24h).toFixed(2)}%
  7d APR: ${parseFloat(poolData.apr7d).toFixed(2)}%
  30d APR: ${parseFloat(poolData.apr30d).toFixed(2)}%
  TVL (USD): $${parseFloat(poolData.liquidityUsd).toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })}
  Current Price (USD): $${parseFloat(poolData.price).toFixed(2)} per ${poolData.tokenPair.split('/')[0]}`;
}

// Implementing periodic refresh
let refreshInterval;

function startAutoRefresh(poolId, displayElementId) {
  // Clear any existing interval
  if (refreshInterval) clearInterval(refreshInterval);
  
  // Initial load
  updatePoolDisplay(poolId, displayElementId);
  
  // Set up refresh interval (every 60 seconds)
  refreshInterval = setInterval(() => {
    updatePoolDisplay(poolId, displayElementId);
  }, 60000);
}

async function updatePoolDisplay(poolId, elementId) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  element.innerHTML = 'Loading...';
  
  const poolData = await getPoolData(poolId);
  if (poolData) {
    element.innerHTML = displayPoolData(poolData);
  } else {
    element.innerHTML = 'Failed to load pool data';
  }
}
```

## Testing Your Fix

After implementing these fixes, verify that:

1. The displayed APR values match those on the Raydium website
2. The data refreshes periodically
3. Manual refresh works correctly
4. Error handling gracefully manages API failures

We recommend implementing these fixes as soon as possible to ensure your users have access to the most accurate and up-to-date pool data.

## API Response Format Reference

For your reference, here's what the pool data from our API should look like:

```json
{
  "id": "3ucNos4NbumPLZNWztqGHNFFgkHeRMBQAVemeeomsUxv",
  "tokenPair": "SOL/USDC",
  "baseMint": "So11111111111111111111111111111111111111112",
  "quoteMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
  "apr24h": "49.67",
  "apr7d": "58.99",
  "apr30d": "95.52",
  "liquidityUsd": "9337025.91",
  "price": "136.79",
  "volume24h": "30996598.11",
  "volume7d": "449622307.18"
}
```

Make sure your client is correctly accessing and displaying these specific fields.

If you have any questions or need further assistance, please don't hesitate to contact our API support team.