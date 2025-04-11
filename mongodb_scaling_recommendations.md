# MongoDB Scaling Recommendations for ShopSentiment

## Current Performance Analysis

Our performance analysis identified the following bottlenecks:

- **Keyword Sentiment Analysis**: 1472.23ms -> 33.91075134277344ms after optimization
- **Rating Distribution by Platform**: 456.82ms -> 39.87765312194824ms after optimization

## Implemented Optimizations

To address these bottlenecks, we have implemented:

1. **Optimized Indexes**
   - Compound indexes for time-series queries
   - Text indexes for keyword searches
   - Indexes optimized for platform-based analytics

2. **Precomputed Collections**
   - Keyword statistics collection
   - Time-series data collection
   - Platform statistics collection

3. **Caching Strategy**
   - Scheduled refreshes of precomputed data
   - Incremental updates for frequently changing data

## Scaling Recommendations

As the application scales to handle production workloads, we recommend the following:

### 1. MongoDB Infrastructure

**Current Needs (Up to 1M reviews)**
- MongoDB Atlas M10 cluster (or equivalent)
- 2 nodes minimum (primary + secondary)
- 2 vCPUs per node
- 4GB RAM per node
- General purpose SSD storage

**Scaling to 10M+ reviews**
- Upgrade to MongoDB Atlas M30 cluster 
- 3+ nodes for high availability
- 8 vCPUs per node
- 16GB RAM per node
- Low-latency SSD storage
- Consider sharding when approaching 50M+ reviews

### 2. Sharding Strategy

When sharding becomes necessary:

- **Shard Key Selection**: 
  - For `products` collection: Use compound key of (`platform` + `_id`)
  - For `reviews` collection: Use compound key of (`product_id` + `date`)

- **Chunk Distribution**:
  - Configure chunk size to 64MB
  - Monitor chunk migrations to avoid hotspots

### 3. Indexing Strategy

- **Index Memory Budget**: 
  - Keep total index size under 50% of available RAM
  - Monitor working set size to ensure it fits in RAM

- **Background Indexing**:
  - Always build new indexes in background on production
  - Schedule index builds during low-traffic periods

### 4. Connection Pooling

- **Connection Management**:
  - Set minimum pool size to 5
  - Set maximum pool size to (100 × number of application servers)
  - Configure connection timeout to 30s

### 5. Read Scaling

- **Read Preference**:
  - Use `secondaryPreferred` for dashboard and analytics
  - Use `primary` for critical write operations
  - Set up read-only analytics users

### 6. Write Scaling

- **Write Concerns**:
  - Use `w: majority` for critical operations
  - Use `w: 1` for high-volume, less-critical writes

- **Bulk Operations**:
  - Use bulk writes for batch operations
  - Use `ordered: false` for parallel processing

### 7. Monitoring and Alerts

- Set up alerts for:
  - Queries exceeding 500ms
  - Index cache eviction rate > 10%
  - Connection pool saturation > 80%
  - Oplog window falling below 24 hours

## Implementation Timeline

1. **Immediate**: Apply all optimization strategies in this document
2. **1-3 months**: Implement monitoring and alerting
3. **3-6 months**: Evaluate need for vertical scaling
4. **6-12 months**: Prepare sharding strategy if growth trends continue

## Cost Considerations

- MongoDB Atlas M10 -> ~$150/month
- MongoDB Atlas M30 -> ~$600/month
- Consider reserved instances for ~30% cost savings
- Implement TTL indexes for data archiving to control storage costs

This scaling plan should accommodate 10x growth in data volume while maintaining sub-200ms response times for all queries.
