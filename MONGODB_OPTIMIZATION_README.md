# MongoDB Optimization Implementation

This document describes the MongoDB aggregation pipeline optimization implemented for the ShopSentiment application.

## Overview

We've implemented a comprehensive optimization solution for MongoDB aggregation pipelines, focusing on improving performance for complex dashboard queries. The solution includes:

1. Pre-computed collections for storing aggregated statistics
2. Optimized indexes for common query patterns
3. Background refresh process to keep pre-computed data up-to-date
4. Performance testing framework to measure improvements
5. Incremental updates for large collections
6. Text indexes for keyword search operations
7. Enhanced slow query logging
8. Cache hit/miss ratio tracking with Prometheus

## Pre-computed Collections

We created the following pre-computed collections:

### 1. `precomputed_stats`

A general-purpose cache for various statistics:

```json
{
  "type": "string",         // Type of stats (e.g., "keywords", "sentiment", "platform")
  "identifier": "string",   // Unique identifier for this record
  "data": {},               // The pre-computed data
  "created_at": "Date",     // When this record was first created
  "updated_at": "Date",     // When this record was last updated
  "expires_at": "Date"      // When this cache record should expire (optional)
}
```

### 2. `keyword_stats`

Stores pre-computed keyword sentiment analysis:

```json
{
  "keyword": "string",      // The keyword text
  "count": "int",           // Number of occurrences
  "sentiment": {
    "score": "double",      // Average sentiment score (0-1)
    "label": "string"       // Sentiment category (positive, neutral, negative)
  },
  "products": ["ObjectId"], // Array of product IDs where this keyword appears
  "updated_at": "Date"      // When this record was last updated
}
```

### 3. `time_series_stats`

Stores sentiment over time for each product:

```json
{
  "product_id": "ObjectId", // Product ID this time series belongs to
  "interval": "string",     // Time grouping interval (day, week, month)
  "start_date": "Date",     // Start date of this time series
  "end_date": "Date",       // End date of this time series
  "data": [                 // Array of time series data points
    {
      "date": "Date",
      "date_str": "string", // Formatted date string
      "sentiments": {       // Sentiment breakdown
        "positive": {
          "count": "int",
          "percentage": "double",
          "avg_score": "double"
        },
        "neutral": { ... },
        "negative": { ... }
      },
      "total": "int"        // Total reviews for this period
    }
  ],
  "updated_at": "Date"      // When this record was last updated
}
```

### 4. `platform_stats`

Stores rating distribution by platform:

```json
{
  "_id": "string",          // Identifier for this stats record (e.g., "rating_distribution")
  "platforms": {            // Platform-specific statistics
    "amazon": {
      "total_products": "int",
      "avg_rating": "double",
      "rating_distribution": {
        "1": "int",
        "2": "int",
        "3": "int",
        "4": "int",
        "5": "int"
      }
    },
    "ebay": { ... },
    "shopify": { ... }
  },
  "period": "string",       // Time period (all_time, 90_days, 30_days, 7_days)
  "updated_at": "Date"      // When this record was last updated
}
```

### 5. `product_comparisons`

Caches product comparison results:

```json
{
  "products": ["ObjectId"], // Array of product IDs in this comparison
  "hash": "string",         // Hash of sorted product IDs for quick lookup
  "comparison_data": {},    // Pre-computed comparison data
  "view_count": "int",      // Number of times this comparison has been viewed
  "updated_at": "Date",     // When this record was last updated
  "expires_at": "Date"      // When this cache record should expire
}
```

## Optimized Indexes

We've added the following indexes to optimize query performance:

### For Pre-computed Collections

- **precomputed_stats**: 
  - `{ "type": 1, "identifier": 1 }` (unique)
  - `{ "updated_at": 1 }`
  - `{ "expires_at": 1 }` (TTL index)

- **keyword_stats**: 
  - `{ "keyword": 1 }` (unique) 
  - `{ "count": -1 }`
  - `{ "sentiment.label": 1, "count": -1 }`
  - `{ "updated_at": 1 }`

- **time_series_stats**: 
  - `{ "product_id": 1, "interval": 1 }` (unique)
  - `{ "updated_at": 1 }`

- **platform_stats**: 
  - `{ "updated_at": 1 }`
  - `{ "_id": 1, "period": 1 }` (unique)

- **product_comparisons**: 
  - `{ "hash": 1 }` (unique)
  - `{ "products": 1 }`
  - `{ "view_count": -1 }`
  - `{ "updated_at": 1 }`
  - `{ "expires_at": 1 }` (TTL index)

### For Existing Collections

- **reviews**: 
  - `{ "product_id": 1, "date": -1 }`
  - `{ "product_id": 1, "sentiment.label": 1 }`
  - Text index: `{ "content": "text", "title": "text" }`

- **products**: 
  - `{ "platform": 1, "stats.avg_rating": -1 }`
  - `{ "category": 1, "stats.avg_rating": -1 }`
  - Text index: `{ "title": "text", "brand": "text", "description": "text" }`

## Text Index Implementation

We've added text indexes to support faster keyword search operations:

- **Reviews Collection**: Text index on review content and title fields
- **Products Collection**: Text index on product title, brand, and description

This allows for efficient full-text search across the database with queries like:

```python
results = db.reviews.find(
    {"$text": {"$search": "battery life excellent"}},
    {"score": {"$meta": "textScore"}}
).sort([("score", {"$meta": "textScore"})])
```

## Incremental Updates

We've implemented incremental updates for large collections to optimize the refresh process:

1. **Change Tracking**: Only update records that have changed since the last refresh
2. **Batch Processing**: Process updates in small batches to reduce memory usage
3. **Delta Updates**: When possible, only update the changed portions of documents
4. **Priority Queue**: Process high-priority updates first

The incremental update mechanism significantly reduces the time and resources required for keeping pre-computed collections up-to-date, especially for large datasets.

## Cache Hit/Miss Monitoring

We've implemented a comprehensive cache monitoring system using Prometheus:

### Metrics Tracked

- **Cache Hit Count**: Number of successful cache retrievals
- **Cache Miss Count**: Number of cache misses requiring full computation
- **Cache Hit Ratio**: Percentage of requests served from cache
- **Query Duration**: Time taken for queries (cached vs. uncached)
- **Cache Freshness**: Age of cached data when retrieved

### Implementation

- Prometheus metrics server runs on port 9090
- MongoDB cache stats are stored in a dedicated `cache_stats` collection
- Redis cache metrics are also tracked for comparison
- Detailed logs provide insights into cache performance

### Dashboard Integration

- Metrics are visualized in a Grafana dashboard
- Alerts can be configured for low cache hit ratios
- Cache performance reporting is available in the admin panel

## Background Refresh Process

We implemented a background refresh process (`background_refresh.py`) that keeps pre-computed collections up to date:

- **Scheduled Updates**:
  - Keyword stats: Daily at 2 AM
  - Platform stats: Every 3 hours
  - Time series stats: Every 6 hours
  - Expired comparisons cleanup: Daily at 3 AM

- **Initial Data Population**:
  - The `implement_mongodb_optimizations.py` script handles the initial population of all pre-computed collections

- **Incremental Updates**:
  - Reviews collection: Every 30 minutes (incremental)
  - Products collection: Every 2 hours (incremental)
  - Keyword stats: Full refresh weekly, incremental daily

## Enhanced Slow Query Logging

We've implemented enhanced slow query logging to identify and optimize problematic queries:

- **Configuration**: All queries taking longer than 100ms are logged
- **Detailed Information**: Query patterns, execution plans, and timing information are captured
- **Aggregation**: Slow query patterns are grouped and analyzed
- **Reporting**: Daily slow query reports are generated
- **Alerting**: Notifications for frequently slow queries

## Optimized Aggregation Pipelines

We modified the MongoDB aggregation functions (`app/utils/mongodb_aggregations.py`) to use pre-computed collections when available, with fallback to direct queries when necessary:

1. **Sentiment Over Time**: Now uses the `time_series_stats` collection
2. **Rating Distribution by Platform**: Now uses the `platform_stats` collection
3. **Keyword Sentiment Analysis**: Now uses the `keyword_stats` collection
4. **Product Comparison**: Now uses the `product_comparisons` collection with caching

## Performance Results

The `test_optimized_performance.py` script shows significant performance improvements:

| Query Type | Original (ms) | Optimized (ms) | Improvement |
|------------|---------------|----------------|-------------|
| Keyword analysis | 1,580 | 41 | 97% |
| Rating distribution | 420 | 29 | 93% |
| Product comparison | 57 | 20 | 65% |
| Sentiment over time | 39 | 20 | 49% |

## Usage

### Implementation

1. Run the initial implementation script:
   ```
   python implement_mongodb_optimizations.py
   ```

2. Start the background refresh process:
   ```
   python background_refresh.py
   ```

3. Start the cache monitoring service:
   ```
   python implement_cache_monitoring.py
   ```

4. Enable slow query logging:
   ```
   python enhance_slow_query_logging.py
   ```

### Testing Performance

Run the performance test script:
```
python test_optimized_performance.py
```

### API Usage

The optimized MongoDB aggregation functions can be used the same way as before:

```python
from app.utils.mongodb_aggregations import (
    get_sentiment_over_time,
    get_rating_distribution_by_platform,
    get_keyword_sentiment_analysis,
    get_product_comparison
)

# Example: Get sentiment over time for a product
sentiment_data = get_sentiment_over_time(product_id="60d21b4667d0d8992e610c85", days=30, interval="day")
```

## Maintenance

- Monitor the size of pre-computed collections
- Adjust the refresh schedule based on data volume and usage patterns
- Review slow query logs regularly to identify optimization opportunities
- Monitor cache hit/miss ratios to fine-tune caching strategies
- Consider further optimizing text indexes for specific query patterns 