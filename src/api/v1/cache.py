"""
Cache Monitoring API

This module provides API endpoints for cache monitoring in the ShopSentiment application.
Implements the cache hit/miss monitoring API endpoints from the roadmap.
"""

import logging
from flask import Blueprint, jsonify, request, current_app
from src.utils.cache_monitor import get_cache_stats, get_cache_key_stats, reset_cache_stats, export_cache_metrics

logger = logging.getLogger(__name__)

# Create Blueprint
cache_bp = Blueprint('cache_api', __name__)


@cache_bp.route('/stats', methods=['GET'])
def get_stats():
    """
    Get cache statistics.
    
    Returns:
        JSON response with cache statistics
    """
    try:
        stats = get_cache_stats()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_bp.route('/key-stats', methods=['GET'])
def get_key_stats():
    """
    Get statistics for specific keys or all keys.
    
    Returns:
        JSON response with key-specific cache statistics
    """
    try:
        key = request.args.get('key')
        stats = get_cache_key_stats(key)
        return jsonify({
            'success': True,
            'data': stats,
            'key': key
        })
    except Exception as e:
        logger.error(f"Error getting cache key stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_bp.route('/reset', methods=['POST'])
def reset_stats():
    """
    Reset cache statistics.
    
    Returns:
        JSON response confirming reset
    """
    try:
        # Check if this is allowed in the current environment
        if current_app.config.get('ENV') != 'development' and not request.args.get('force'):
            return jsonify({
                'success': False,
                'error': 'Cache stats reset is only allowed in development environment unless force=true'
            }), 403
            
        reset_cache_stats()
        return jsonify({
            'success': True,
            'message': 'Cache statistics reset successfully'
        })
    except Exception as e:
        logger.error(f"Error resetting cache stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@cache_bp.route('/export', methods=['GET'])
def export_metrics():
    """
    Export cache metrics for monitoring systems.
    
    Returns:
        JSON response with all cache metrics
    """
    try:
        metrics = export_cache_metrics()
        format_type = request.args.get('format', 'json')
        
        if format_type == 'prometheus':
            # Generate Prometheus-compatible metrics
            prom_metrics = []
            overall = metrics['overall']
            
            # Add overall metrics
            prom_metrics.append(f'# HELP cache_hits_total Total number of cache hits')
            prom_metrics.append(f'# TYPE cache_hits_total counter')
            prom_metrics.append(f'cache_hits_total {overall["hits"]}')
            
            prom_metrics.append(f'# HELP cache_misses_total Total number of cache misses')
            prom_metrics.append(f'# TYPE cache_misses_total counter')
            prom_metrics.append(f'cache_misses_total {overall["misses"]}')
            
            prom_metrics.append(f'# HELP cache_hit_ratio Cache hit ratio')
            prom_metrics.append(f'# TYPE cache_hit_ratio gauge')
            prom_metrics.append(f'cache_hit_ratio {overall["hit_ratio"]}')
            
            prom_metrics.append(f'# HELP cache_avg_hit_time_ms Average cache hit time in milliseconds')
            prom_metrics.append(f'# TYPE cache_avg_hit_time_ms gauge')
            prom_metrics.append(f'cache_avg_hit_time_ms {overall["avg_hit_time"]}')
            
            prom_metrics.append(f'# HELP cache_avg_miss_time_ms Average cache miss time in milliseconds')
            prom_metrics.append(f'# TYPE cache_avg_miss_time_ms gauge')
            prom_metrics.append(f'cache_avg_miss_time_ms {overall["avg_miss_time"]}')
            
            # Add key-specific metrics
            for key, stats in metrics['keys'].items():
                safe_key = key.replace('.', '_').replace('-', '_').replace(':', '_')
                prom_metrics.append(f'# HELP cache_key_hits_total{{key="{key}"}} Total hits for cache key')
                prom_metrics.append(f'# TYPE cache_key_hits_total counter')
                prom_metrics.append(f'cache_key_hits_total{{key="{key}"}} {stats["hits"]}')
                
                prom_metrics.append(f'# HELP cache_key_misses_total{{key="{key}"}} Total misses for cache key')
                prom_metrics.append(f'# TYPE cache_key_misses_total counter')
                prom_metrics.append(f'cache_key_misses_total{{key="{key}"}} {stats["misses"]}')
            
            return '\n'.join(prom_metrics), 200, {'Content-Type': 'text/plain'}
        else:
            # Default JSON format
            return jsonify(metrics)
            
    except Exception as e:
        logger.error(f"Error exporting cache metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def register_cache_api(app):
    """
    Register cache API endpoints with the application.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(cache_bp, url_prefix='/api/v1/cache') 