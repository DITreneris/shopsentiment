# MongoDB Aggregation Pipeline Optimization Plan

*May 1, 2025*

## Overview

This document outlines the implementation plan for optimizing ShopSentiment's dashboard performance using MongoDB's aggregation framework and precomputed statistics. The goal is to achieve a 75% reduction in dashboard loading time for complex queries.

## Current Performance Analysis

Based on initial testing with production-scale data (100 users, 500 products, 100,000 reviews):

| Query Type | Average Time (ms) | 95th Percentile (ms) | Max Time (ms) |
|------------|-------------------|----------------------|---------------|
| Sentiment Trend | 850 | 1200 | 1800 |
| Rating Distribution | 720 | 980 | 1500 |
| Keyword Sentiment | 1100 | 1450 | 2200 |
| Product Comparison | 1550 | 2100 | 3500 |

Target performance after optimization:

| Query Type | Target Avg Time (ms) | Target 95th (ms) | Reduction |
|------------|----------------------|------------------|-----------|
| Sentiment Trend | 210 | 300 | 75% |
| Rating Distribution | 180 | 245 | 75% |
| Keyword Sentiment | 275 | 360 | 75% |
| Product Comparison | 375 | 525 | 75% |

## Implementation Strategy

### 1. Precomputed Statistics Collection

Create a new MongoDB collection to store precomputed statistics:

```javascript
db.createCollection('precomputed_stats', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['stats_type', 'identifier', 'created_at', 'data'],
      properties: {
        stats_type: { bsonType: 'string' },
        identifier: { bsonType: 'string' },
        created_at: { bsonType: 'date' },
        expires_at: { bsonType: 'date' },
        data: { bsonType: 'object' }
      }
    }
  }
})

// Create indexes
db.precomputed_stats.createIndex({ stats_type: 1, identifier: 1 }, { unique: true })
db.precomputed_stats.createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 })
```

### 2. Aggregation Pipeline Enhancements

Enhance the existing `AggregationPipelines` class with:

1. New methods to store and retrieve precomputed statistics
2. Optimized aggregation pipelines using efficient MongoDB operators
3. Index usage analysis and optimization
4. Memory management improvements for large datasets

### 3. Background Refresh System

Implement a background job system to refresh precomputed statistics:

1. Create a scheduled task to refresh popular statistics during off-peak hours
2. Implement priority-based refresh for frequently accessed statistics
3. Add cache invalidation triggers for data modifications
4. Create a dashboard for monitoring statistics freshness

### 4. Multi-Level Caching Strategy

Implement a multi-level caching strategy:

1. MongoDB precomputed statistics (persistent, shared across instances)
2. Redis caching for faster access (in-memory, supporting high throughput)
3. Application-level caching for session-specific data

## Implementation Plan

### Phase 1: Enhance Aggregation Pipelines (3 days)

1. Refactor `AggregationPipelines` class for better performance:
   - Add early filtering in pipelines
   - Optimize stages to reduce memory usage
   - Use efficient operators ($group, $project, $bucket)
   - Add efficient pagination support
   - Implement index hints

2. Add precomputed statistics methods:
   - `store_precomputed_stats(stats_type, identifier, data, expiration=None)`
   - `get_precomputed_stats(stats_type, identifier, max_age_hours=24)`
   - `invalidate_precomputed_stats(stats_type=None, identifier=None)`

### Phase 2: Dashboard Service Integration (2 days)

1. Enhance `DashboardService` to use precomputed statistics:
   - Update all data retrieval methods to use multi-level caching
   - Implement automatic fallback to direct calculation
   - Add performance monitoring metrics
   - Implement concurrent refresh for multiple statistics

2. Add precomputed stats management:
   - Create an admin interface for managing precomputed statistics
   - Add diagnostics for cache hit/miss ratios
   - Implement manual refresh triggers

### Phase 3: Background Refresh System (2 days)

1. Implement Celery tasks for background refreshes:
   - `refresh_product_stats(product_id)`
   - `refresh_platform_stats(platform)`
   - `refresh_global_stats()`
   - `refresh_user_stats(user_id)`

2. Create scheduling logic:
   - Configure periodic tasks for different statistics types
   - Implement access-based refresh prioritization
   - Add retry mechanisms for failed refreshes

### Phase 4: Time-Series Analytics Optimization (3 days)

1. Implement specialized time-series aggregations:
   - Daily/weekly/monthly trend calculations
   - Moving averages and trend indicators
   - Anomaly detection for unusual patterns
   - Seasonal adjustments for cyclical data

2. Add statistical measures:
   - Confidence intervals for predictions
   - Statistical significance indicators
   - Correlation metrics between different data points

## Implementation Details

### Precomputed Stats Storage

```python
def store_precomputed_stats(stats_type, identifier, data, expiration=None):
    """
    Store precomputed statistics in MongoDB
    
    Args:
        stats_type: Type of statistic (e.g., 'sentiment_trend:30:day')
        identifier: Object identifier (e.g., product_id)
        data: The precomputed data to store
        expiration: Optional expiration time in hours (default: 7 days)
    """
    db = get_db()
    if not db:
        return False
        
    # Default expiration: 7 days
    if expiration is None:
        expiration = 7 * 24  # hours
        
    # Calculate expiration date
    expires_at = datetime.now() + timedelta(hours=expiration)
    
    try:
        # Upsert the data
        db.precomputed_stats.update_one(
            {"stats_type": stats_type, "identifier": identifier},
            {"$set": {
                "data": data,
                "created_at": datetime.now(),
                "expires_at": expires_at
            }},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error storing precomputed stats: {e}")
        return False
```

### Background Refresh Task

```python
@celery.task
def refresh_product_stats(product_id):
    """
    Background task to refresh all statistics for a product
    
    Args:
        product_id: MongoDB ObjectId for the product (string)
    """
    logger.info(f"Refreshing stats for product {product_id}")
    
    # Get pipeline instance
    pipeline = AggregationPipelines()
    
    # Calculate and store sentiment trends (last 30/90/365 days)
    for days in [30, 90, 365]:
        for interval in ['day', 'week', 'month']:
            stats_type = f"sentiment_trend:{days}:{interval}"
            data = pipeline.sentiment_over_time(product_id, days, interval)
            pipeline.store_precomputed_stats(stats_type, product_id, data)
    
    # Calculate and store keyword sentiment
    stats_type = "keyword_sentiment"
    data = pipeline.keyword_sentiment_analysis(product_id)
    pipeline.store_precomputed_stats(stats_type, product_id, data)
    
    # Calculate additional product-specific statistics
    # ...
    
    logger.info(f"Completed stats refresh for product {product_id}")
```

### Scheduling Configuration

```python
# Schedule configuration
CELERYBEAT_SCHEDULE = {
    'refresh-popular-products': {
        'task': 'app.tasks.refresh_popular_products',
        'schedule': timedelta(hours=6),  # Every 6 hours
    },
    'refresh-platform-stats': {
        'task': 'app.tasks.refresh_platform_stats',
        'schedule': timedelta(hours=12),  # Every 12 hours
    },
    'refresh-global-stats': {
        'task': 'app.tasks.refresh_global_stats',
        'schedule': timedelta(days=1),  # Daily
    },
}
```

## Performance Monitoring

To ensure optimization goals are met, we will:

1. Implement detailed query timing logs
2. Create dashboard for viewing statistics freshness
3. Set up alerts for slow-performing queries
4. Conduct regular performance reviews

## Migration Strategy

1. Deploy precomputed statistics collection and indexes
2. Roll out enhanced aggregation pipelines
3. Initialize with first round of precomputed statistics
4. Enable background refresh system
5. Monitor and fine-tune for optimal performance

## Success Criteria

1. 75% reduction in dashboard loading time for complex queries
2. No query taking longer than 500ms for 95th percentile
3. Background refresh system keeping statistics fresh within 24 hours
4. Cache hit ratio >80% for popular products

## Rollback Plan

If performance issues arise:

1. Disable background refresh system
2. Revert to direct aggregation pipelines
3. Scale MongoDB resources if necessary
4. Re-evaluate optimization strategy 