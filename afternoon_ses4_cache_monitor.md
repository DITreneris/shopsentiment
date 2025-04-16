# Cache Hit/Miss Monitoring Implementation Plan

## Overview
This document outlines the detailed implementation plan for adding cache hit/miss monitoring to the ShopSentiment application, as identified in our roadmap. This feature will help us track cache performance, optimize resource usage, and identify opportunities for further improvements.

## Implementation Steps

### 1. Cache Configuration Setup

```python
# config/cache.py
CACHE_TYPE = "RedisCache"
CACHE_REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
CACHE_REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
CACHE_REDIS_DB = int(os.environ.get("REDIS_CACHE_DB", 0))
CACHE_DEFAULT_TIMEOUT = 300
CACHE_KEY_PREFIX = "shopsentiment_"
CACHE_REDIS_URL = os.environ.get("REDIS_URL")
```

### 2. Cache Monitoring Class

```python
# utils/cache_monitor.py
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from flask_caching import Cache
from flask import current_app

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """Store cache statistics."""
    hits: int = 0
    misses: int = 0
    keys: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # key -> (hits, misses)
    
    @property
    def total(self) -> int:
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.hits / self.total
    
    def top_hit_keys(self, limit: int = 10) -> List[Tuple[str, int]]:
        return sorted(
            [(k, v[0]) for k, v in self.keys.items()], 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]
    
    def top_miss_keys(self, limit: int = 10) -> List[Tuple[str, int]]:
        return sorted(
            [(k, v[1]) for k, v in self.keys.items()], 
            key=lambda x: x[1], 
            reverse=True
        )[:limit]

class CacheMonitor:
    """Monitor cache hits and misses."""
    
    def __init__(self, cache: Cache):
        self.cache = cache
        self.stats = CacheStats()
        self.start_time = time.time()
        
    def _get_original_methods(self):
        """Store original cache methods."""
        self._original_get = self.cache.get
        self._original_set = self.cache.set
        
    def register(self):
        """Register the monitor by patching cache methods."""
        self._get_original_methods()
        
        def monitored_get(key, *args, **kwargs):
            result = self._original_get(key, *args, **kwargs)
            
            # Track the hit/miss
            if result is None:
                self.stats.misses += 1
                if key in self.stats.keys:
                    self.stats.keys[key] = (self.stats.keys[key][0], self.stats.keys[key][1] + 1)
                else:
                    self.stats.keys[key] = (0, 1)
                logger.debug(f"Cache MISS: {key}")
            else:
                self.stats.hits += 1
                if key in self.stats.keys:
                    self.stats.keys[key] = (self.stats.keys[key][0] + 1, self.stats.keys[key][1])
                else:
                    self.stats.keys[key] = (1, 0)
                logger.debug(f"Cache HIT: {key}")
                
            return result
        
        # Replace the original methods with monitored versions
        self.cache.get = monitored_get
        
        logger.info("Cache monitoring activated")
        return self
        
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "hits": self.stats.hits,
            "misses": self.stats.misses,
            "total": self.stats.total,
            "hit_rate": self.stats.hit_rate,
            "top_hit_keys": self.stats.top_hit_keys(),
            "top_miss_keys": self.stats.top_miss_keys(),
            "uptime_seconds": time.time() - self.start_time,
        }
```

### 3. Integrate with Application

```python
# app.py
from utils.cache_monitor import CacheMonitor
from flask_caching import Cache

def create_app():
    # ...existing code...
    
    # Configure caching
    app.config.from_object('config.cache')
    cache = Cache(app)
    
    # Setup cache monitoring
    cache_monitor = CacheMonitor(cache).register()
    app.cache_monitor = cache_monitor
    
    # ...existing code...
    
    # Add cache stats endpoint
    @app.route('/api/v1/admin/cache-stats')
    @admin_required  # Ensure only admins can access
    def cache_stats():
        """Return cache statistics."""
        return jsonify(app.cache_monitor.get_stats())
    
    return app
```

### 4. Add Cache Decorators to API Endpoints

```python
# Example of adding caching to API endpoints
@app.route('/api/v1/products')
@cache.cached(timeout=300, key_prefix='all_products')
def get_products():
    """API endpoint to get all products with sentiment data."""
    try:
        logger.info('API request for products')
        # Database query here
        return jsonify({'products': products, 'count': len(products)})
    except Exception as e:
        logger.error(f'Error in API products route: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
```

### 5. Create Admin Dashboard for Cache Monitoring

```python
# templates/admin/cache_stats.html
{% extends 'admin/base.html' %}

{% block title %}Cache Statistics{% endblock %}

{% block content %}
<div class="container">
    <div class="card">
        <div class="card-header">
            <h2>Cache Statistics</h2>
            <p>Monitoring period: <span id="uptime"></span></p>
        </div>
        <div class="card-body">
            <div class="row">
                <div class="col-md-4">
                    <div class="metric-card">
                        <h3>Hit Rate</h3>
                        <div class="metric-value" id="hit-rate">-</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card">
                        <h3>Total Hits</h3>
                        <div class="metric-value" id="hits">-</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card">
                        <h3>Total Misses</h3>
                        <div class="metric-value" id="misses">-</div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <h3>Top Cache Hits</h3>
                    <table class="table" id="top-hits">
                        <thead>
                            <tr>
                                <th>Key</th>
                                <th>Hits</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
                <div class="col-md-6">
                    <h3>Top Cache Misses</h3>
                    <table class="table" id="top-misses">
                        <thead>
                            <tr>
                                <th>Key</th>
                                <th>Misses</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Fetch cache stats
    fetchCacheStats();
    // Refresh every 30 seconds
    setInterval(fetchCacheStats, 30000);
    
    function fetchCacheStats() {
        fetch('/api/v1/admin/cache-stats')
            .then(response => response.json())
            .then(data => {
                // Update metrics
                document.getElementById('hit-rate').textContent = 
                    (data.hit_rate * 100).toFixed(2) + '%';
                document.getElementById('hits').textContent = data.hits;
                document.getElementById('misses').textContent = data.misses;
                
                // Format uptime
                const uptime = formatUptime(data.uptime_seconds);
                document.getElementById('uptime').textContent = uptime;
                
                // Update tables
                updateTable('top-hits', data.top_hit_keys);
                updateTable('top-misses', data.top_miss_keys);
            })
            .catch(error => {
                console.error('Error fetching cache stats:', error);
            });
    }
    
    function updateTable(tableId, data) {
        const tbody = document.querySelector(`#${tableId} tbody`);
        tbody.innerHTML = '';
        
        data.forEach(([key, count]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${key}</td>
                <td>${count}</td>
            `;
            tbody.appendChild(row);
        });
    }
    
    function formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        
        let result = '';
        if (days > 0) result += `${days}d `;
        if (hours > 0) result += `${hours}h `;
        if (minutes > 0) result += `${minutes}m `;
        result += `${remainingSeconds}s`;
        
        return result;
    }
});
</script>
{% endblock %}
```

## 6. Redis Connection Health Check

```python
# utils/cache_health.py
import redis
from typing import Dict
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def check_redis_health() -> Dict:
    """Check Redis connection health."""
    redis_url = current_app.config.get('CACHE_REDIS_URL')
    if not redis_url:
        host = current_app.config.get('CACHE_REDIS_HOST', 'localhost')
        port = current_app.config.get('CACHE_REDIS_PORT', 6379)
        db = current_app.config.get('CACHE_REDIS_DB', 0)
    else:
        # Parse from URL if provided
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        host = parsed.hostname
        port = parsed.port or 6379
        path = parsed.path or ''
        db = int(path[1:]) if path and len(path) > 1 else 0
    
    try:
        client = redis.Redis(host=host, port=port, db=db)
        info = client.info()
        
        memory_used = info.get('used_memory_human', 'N/A')
        total_keys = sum(
            client.dbsize() for db in range(16) 
            if client.exists(f'db{db}')
        ) if db == 0 else client.dbsize()
        
        return {
            'status': 'healthy',
            'version': info.get('redis_version', 'N/A'),
            'memory_used': memory_used,
            'total_keys': total_keys,
            'uptime_seconds': info.get('uptime_in_seconds', 0)
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
```

## Testing Plan

1. **Unit Tests**:
   - Test CacheStats class functionality
   - Test CacheMonitor with a mock cache
   - Test Redis health check with a mock Redis client

2. **Integration Tests**:
   - Test actual caching of API responses
   - Verify hit/miss tracking accuracy
   - Test cache invalidation

3. **Performance Tests**:
   - Measure response time improvements with caching
   - Analyze hit rate under different load scenarios
   - Test memory usage impact

## Monitoring & Alerting

1. **Set up alerts for**:
   - Low hit rates (below 70%)
   - High miss rates on common endpoints
   - Redis memory usage above 80%
   - Redis connection issues

2. **Dashboard metrics**:
   - Hit rate trends over time
   - Cache size growth
   - Top missed and hit keys
   - Average response time improvement

## Documentation

1. **Developer Documentation**:
   - Cache key naming conventions
   - How to add caching to new endpoints
   - How to view and interpret cache statistics

2. **Operations Documentation**:
   - Redis setup and configuration
   - Scaling Redis for higher loads
   - Troubleshooting common issues 