# MongoDB Aggregation Pipeline Optimization Plan

## 1. Performance Analysis Results

Based on our performance testing with ~100K reviews and 1K products, we've identified the following performance bottlenecks:

| Query | Average Time (ms) | Observations |
|-------|-------------------|--------------|
| Keyword Sentiment Analysis | 1,472 ms | Extremely slow. Requires keyword unwinding and multiple calculations. |
| Rating Distribution by Platform | 457 ms | Slow due to complex $lookup operation and calculations. |
| Product Comparison | 57 ms | Acceptable but could be improved. Uses $lookup between collections. |
| Sentiment Over Time (90 days) | 39 ms | Good performance. Simple aggregation with date grouping. |
| Sentiment Over Time (30 days) | 35 ms | Good performance. Efficient date range filtering. |

## 2. Identified Issues

### 2.1. Major Bottlenecks

1. **Keyword Processing Operations**
   - Unwinding arrays of keywords is CPU intensive
   - Grouping by keyword across large datasets is slow
   - Sentiment calculation per keyword requires multiple passes

2. **Cross-Collection Lookups**
   - Joining products and reviews collections is expensive
   - $lookup operations don't utilize indexes efficiently
   - Results in large in-memory data processing

3. **Complex Date Manipulations**
   - Date grouping and formatting adds processing overhead
   - Calculations across date ranges are memory intensive

### 2.2. Index Usage Analysis

- **Missing Indexes**: No compound indexes for complex queries
- **Index Types**: Basic single-field indexes only
- **Collection Structure**: No pre-computed statistics collections

## 3. Optimization Plan

### 3.1. Pre-computed Collections Strategy

1. **Create Dedicated Stats Collections**
   - **Time-Series Collection**: Store pre-calculated sentiment over time
   - **Keywords Collection**: Store pre-aggregated keyword statistics
   - **Platform Stats Collection**: Store rating distributions by platform

2. **Scheduled Update Process**
   - Implement a background process to update pre-computed collections
   - Update on write operations or schedule periodic refresh
   - Implement proper TTL (Time-To-Live) for cached data

### 3.2. Index Optimization

1. **Reviews Collection**
   - Add compound index: `{ product_id: 1, date: -1 }`
   - Add index for sentiment filtering: `{ product_id: 1, "sentiment.label": 1 }`
   - Add text index for keyword search: `{ keywords: "text" }`

2. **Products Collection**
   - Add compound index: `{ platform: 1, "stats.avg_rating": -1 }`
   - Add index for category filtering: `{ category: 1, "stats.avg_rating": -1 }`

3. **Pre-computed Collections**
   - Add TTL index on cache collections: `{ updated_at: 1 }, { expireAfterSeconds: 86400 }`

### 3.3. Pipeline Optimization

1. **Keyword Analysis Pipeline**
   - Move to materialized view updated daily
   - Implement schema:
     ```
     {
       _id: "keyword",
       count: 100,
       avg_sentiment: 0.75,
       sentiment_label: "positive",
       products: [ObjectId1, ObjectId2, ...],
       updated_at: ISODate()
     }
     ```

2. **Rating Distribution Pipeline**
   - Create scheduled aggregation job
   - Store results in dedicated collection:
     ```
     {
       _id: "platform_ratings",
       platforms: {
         amazon: { "1": 100, "2": 200, ... },
         ebay: { "1": 50, "2": 150, ... }
       },
       updated_at: ISODate()
     }
     ```

3. **Product Comparison Optimization**
   - Denormalize key metrics in product documents
   - Cache frequent comparison results
   - Implement partial results for faster initial loading

## 4. Implementation Priority

1. **High Priority (Immediate)**
   - Create pre-computed stats collection structure
   - Add compound indexes for common query patterns
   - Implement keyword stats materialized view

2. **Medium Priority (Next Week)**
   - Implement scheduled update process for stats
   - Modify API endpoints to use pre-computed data
   - Add fallback to direct calculation when cache misses

3. **Low Priority (Later Phase)**
   - Implement TTL for cache expiration 
   - Add monitoring for aggregation performance
   - Optimize background refresh process

## 5. Estimated Performance Improvements

| Query | Current (ms) | Expected (ms) | Improvement |
|-------|--------------|---------------|-------------|
| Keyword Analysis | 1,472 | < 50 | 97% reduction |
| Rating Distribution | 457 | < 30 | 93% reduction |
| Product Comparison | 57 | < 20 | 65% reduction |
| Sentiment Over Time | 39 | < 20 | 49% reduction |

## 6. Monitoring Strategy

- Implement slow query logging for operations > 100ms
- Track cache hit/miss ratio for pre-computed data
- Monitor MongoDB CPU and memory during aggregation operations
- Set up alerts for queries exceeding performance thresholds 