"""
Cache Monitoring Module - Simplified version for testing

This module provides functionality for monitoring cache performance.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class CacheMetrics:
    """Data class for cache metrics."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.total_hit_time = 0.0
        self.total_miss_time = 0.0
    
    @property
    def total_operations(self):
        """Total number of operations."""
        return self.hits + self.misses
    
    @property
    def hit_ratio(self):
        """Hit ratio calculation."""
        if self.total_operations == 0:
            return 0.0
        return self.hits / self.total_operations
    
    @property
    def avg_hit_time(self):
        """Average hit time in milliseconds."""
        if self.hits == 0:
            return 0.0
        return self.total_hit_time / self.hits * 1000
    
    @property
    def avg_miss_time(self):
        """Average miss time in milliseconds."""
        if self.misses == 0:
            return 0.0
        return self.total_miss_time / self.misses * 1000
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio": self.hit_ratio,
            "avg_hit_time_ms": self.avg_hit_time,
            "avg_miss_time_ms": self.avg_miss_time,
            "total_operations": self.total_operations
        }

class CacheMonitor:
    """Cache monitoring singleton."""
    
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize monitor."""
        self._metrics = {}
        self._global_metrics = CacheMetrics()
        self._lock = threading.Lock()
    
    def record_hit(self, key, duration):
        """Record a cache hit."""
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = CacheMetrics()
            
            self._metrics[key].hits += 1
            self._metrics[key].total_hit_time += duration
            self._global_metrics.hits += 1
            self._global_metrics.total_hit_time += duration
    
    def record_miss(self, key, duration):
        """Record a cache miss."""
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = CacheMetrics()
            
            self._metrics[key].misses += 1
            self._metrics[key].total_miss_time += duration
            self._global_metrics.misses += 1
            self._global_metrics.total_miss_time += duration
    
    def get_metrics(self):
        """Get all metrics."""
        with self._lock:
            return {
                "global": self._global_metrics.to_dict(),
                "keys": {k: v.to_dict() for k, v in self._metrics.items()}
            }
    
    def get_top_keys(self, n=10, sort_by="hits"):
        """Get top N keys sorted by specified metric."""
        with self._lock:
            if not self._metrics:
                return []
            
            if sort_by == "hits":
                sort_key = lambda x: x[1].hits
            elif sort_by == "misses":
                sort_key = lambda x: x[1].misses
            elif sort_by == "hit_ratio":
                sort_key = lambda x: x[1].hit_ratio
            else:
                sort_key = lambda x: x[1].total_operations
            
            sorted_items = sorted(
                self._metrics.items(),
                key=sort_key,
                reverse=True
            )
            
            return [(k, v.to_dict()) for k, v in sorted_items[:n]]
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._global_metrics = CacheMetrics() 