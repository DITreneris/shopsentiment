"""
Dashboard routes for the ShopSentiment application
Provides endpoints for the interactive dashboard using precomputed stats
"""

import json
import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from bson import ObjectId

from app.services.dashboard_service import dashboard_service
from app.utils.redis_cache import cache_dashboard_stats
from app.utils.mongodb_aggregations import AggregationPipelines

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    """Main dashboard view"""
    return render_template('dashboard/index.html')

@dashboard_bp.route('/api/dashboard/sentiment-trend/<product_id>')
@login_required
@cache_dashboard_stats(timeout=60*60) # 1 hour cache
def sentiment_trend_api(product_id):
    """API endpoint for sentiment trend data"""
    try:
        # Get query parameters with defaults
        days = int(request.args.get('days', 30))
        interval = request.args.get('interval', 'day')
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Validate parameters
        if interval not in ['day', 'week', 'month']:
            return jsonify({'error': 'Invalid interval parameter'}), 400
        
        if days <= 0 or days > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        # Get data from dashboard service
        trend_data = dashboard_service.get_sentiment_trend(
            product_id=product_id,
            days=days,
            interval=interval,
            force_refresh=force_refresh
        )
        
        return jsonify({
            'status': 'success',
            'data': trend_data
        })
        
    except Exception as e:
        logger.error(f"Error in sentiment trend API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/rating-distribution')
@login_required
@cache_dashboard_stats(timeout=60*60) # 1 hour cache
def rating_distribution_api():
    """API endpoint for rating distribution data"""
    try:
        # Get query parameters
        platform = request.args.get('platform', None)
        days = int(request.args.get('days', 90))
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Validate parameters
        if days <= 0 or days > 365:
            return jsonify({'error': 'Days parameter must be between 1 and 365'}), 400
        
        # Get data from dashboard service
        distribution_data = dashboard_service.get_rating_distribution(
            platform=platform,
            days=days,
            force_refresh=force_refresh
        )
        
        return jsonify({
            'status': 'success',
            'data': distribution_data
        })
        
    except Exception as e:
        logger.error(f"Error in rating distribution API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/keyword-sentiment')
@login_required
@cache_dashboard_stats(timeout=60*60*3) # 3 hour cache
def keyword_sentiment_api():
    """API endpoint for keyword sentiment analysis data"""
    try:
        # Get query parameters
        min_count = int(request.args.get('min_count', 10))
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Validate parameters
        if min_count <= 0:
            return jsonify({'error': 'Min count parameter must be positive'}), 400
        
        # Get data from dashboard service
        keyword_data = dashboard_service.get_keyword_sentiment(
            min_count=min_count,
            force_refresh=force_refresh
        )
        
        return jsonify({
            'status': 'success',
            'data': keyword_data
        })
        
    except Exception as e:
        logger.error(f"Error in keyword sentiment API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/product-comparison')
@login_required
@cache_dashboard_stats(timeout=60*60*2) # 2 hour cache
def product_comparison_api():
    """API endpoint for product comparison data"""
    try:
        # Get query parameters - comma-separated list of product IDs
        product_ids_param = request.args.get('product_ids', '')
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if not product_ids_param:
            return jsonify({'error': 'Product IDs parameter is required'}), 400
            
        # Parse and validate product IDs
        try:
            product_ids = [ObjectId(pid.strip()) for pid in product_ids_param.split(',')]
        except Exception:
            return jsonify({'error': 'Invalid product ID format'}), 400
            
        if len(product_ids) < 1 or len(product_ids) > 5:
            return jsonify({'error': 'Number of products must be between 1 and 5'}), 400
        
        # Get data from dashboard service
        comparison_data = dashboard_service.get_product_comparison(
            product_ids=product_ids,
            force_refresh=force_refresh
        )
        
        return jsonify({
            'status': 'success',
            'data': comparison_data
        })
        
    except Exception as e:
        logger.error(f"Error in product comparison API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/refresh-stats', methods=['POST'])
@login_required
def refresh_stats_api():
    """API endpoint to manually trigger stats refresh"""
    try:
        # Check if user has admin privileges
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get parameters from JSON body
        data = request.get_json() or {}
        stat_type = data.get('type')
        target_id = data.get('target_id')
        
        # Validate parameters
        if not stat_type:
            return jsonify({'error': 'Stat type parameter is required'}), 400
            
        # Refresh appropriate stats
        if stat_type == 'sentiment_trend':
            if not target_id:
                return jsonify({'error': 'Target ID is required for sentiment trend'}), 400
                
            dashboard_service.get_sentiment_trend(
                product_id=target_id,
                force_refresh=True
            )
            
        elif stat_type == 'rating_distribution':
            dashboard_service.get_rating_distribution(
                platform=target_id,  # Optional
                force_refresh=True
            )
            
        elif stat_type == 'keyword_sentiment':
            dashboard_service.get_keyword_sentiment(
                force_refresh=True
            )
            
        elif stat_type == 'product_comparison':
            if not target_id:
                return jsonify({'error': 'Target IDs are required for product comparison'}), 400
                
            # Parse comma-separated product IDs
            try:
                product_ids = [ObjectId(pid.strip()) for pid in target_id.split(',')]
            except Exception:
                return jsonify({'error': 'Invalid product ID format'}), 400
                
            dashboard_service.get_product_comparison(
                product_ids=product_ids,
                force_refresh=True
            )
            
        else:
            return jsonify({'error': 'Unknown stat type'}), 400
            
        return jsonify({
            'status': 'success',
            'message': f'Successfully refreshed {stat_type} stats'
        })
        
    except Exception as e:
        logger.error(f"Error in refresh stats API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dashboard/performance')
@login_required
def performance_dashboard():
    """Performance monitoring dashboard for MongoDB optimizations"""
    # Check if user has admin privileges
    if not getattr(current_user, 'is_admin', False):
        return render_template('errors/403.html'), 403
        
    return render_template('dashboard/performance.html')

@dashboard_bp.route('/api/dashboard/stats-freshness')
@login_required
def stats_freshness_api():
    """API endpoint to get precomputed stats freshness information"""
    try:
        # Check if user has admin privileges
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Create aggregation pipelines instance
        pipelines = AggregationPipelines()
        
        # Get freshness data for all stats types
        freshness_data = pipelines.get_stats_freshness()
        
        # Get performance metrics if available
        metrics = {}
        if hasattr(current_app, 'metrics'):
            metrics = {
                'sentiment_trend': current_app.metrics.get_average('dashboard_query.get_sentiment_trend'),
                'rating_distribution': current_app.metrics.get_average('dashboard_query.get_rating_distribution'),
                'keyword_sentiment': current_app.metrics.get_average('dashboard_query.get_keyword_sentiment'),
                'product_comparison': current_app.metrics.get_average('dashboard_query.get_product_comparison')
            }
        
        # List available stats types
        stats_types = pipelines.list_precomputed_stats_types()
        
        return jsonify({
            'status': 'success',
            'freshness': freshness_data,
            'metrics': metrics,
            'stats_types': stats_types
        })
        
    except Exception as e:
        logger.error(f"Error in stats freshness API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/job-stats')
@login_required
def job_stats_api():
    """API endpoint to get background job statistics"""
    try:
        # Check if user has admin privileges
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get job statistics from Celery if available
        job_stats = []
        
        if hasattr(current_app, 'celery'):
            # This implementation depends on how Celery is configured
            # and what monitoring tools are in place
            try:
                from app.tasks.dashboard_tasks import get_task_stats
                job_stats = get_task_stats()
            except Exception as e:
                logger.warning(f"Failed to get Celery task stats: {e}")
                
        # If we couldn't get the stats, return a placeholder
        if not job_stats:
            job_stats = [
                {
                    'type': 'refresh_popular_products',
                    'last_run': 'Unknown',
                    'duration': 'Unknown',
                    'status': 'Unknown'
                },
                {
                    'type': 'refresh_platform_stats',
                    'last_run': 'Unknown',
                    'duration': 'Unknown',
                    'status': 'Unknown'
                }
            ]
        
        return jsonify({
            'status': 'success',
            'job_stats': job_stats
        })
        
    except Exception as e:
        logger.error(f"Error in job stats API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/run-job', methods=['POST'])
@login_required
def run_job_api():
    """API endpoint to manually trigger a background job"""
    try:
        # Check if user has admin privileges
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'error': 'Unauthorized'}), 403
            
        # Get job type from request
        data = request.get_json() or {}
        job_type = data.get('job_type')
        
        if not job_type:
            return jsonify({'error': 'Job type is required'}), 400
            
        # Trigger the appropriate job
        result = None
        if hasattr(current_app, 'celery'):
            if job_type == 'refresh_popular_products':
                from app.tasks.dashboard_tasks import refresh_popular_product_stats
                result = refresh_popular_product_stats.delay()
                
            elif job_type == 'refresh_platform_stats':
                from app.tasks.dashboard_tasks import refresh_platform_stats
                result = refresh_platform_stats.delay()
                
            elif job_type == 'refresh_comparison_stats':
                from app.tasks.dashboard_tasks import refresh_comparison_stats
                result = refresh_comparison_stats.delay()
                
            elif job_type == 'refresh_all_dashboard_stats':
                from app.tasks.dashboard_tasks import refresh_all_dashboard_stats
                result = refresh_all_dashboard_stats.delay()
                
            elif job_type == 'prune_stale_stats':
                from app.tasks.dashboard_tasks import prune_stale_stats
                result = prune_stale_stats.delay()
                
            else:
                return jsonify({'error': f'Unknown job type: {job_type}'}), 400
                
            return jsonify({
                'status': 'success',
                'message': f'Successfully triggered {job_type}',
                'task_id': str(result) if result else None
            })
        else:
            return jsonify({'error': 'Celery not configured'}), 500
            
    except Exception as e:
        logger.error(f"Error triggering job: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/api/dashboard/redis-fallback-metrics')
@login_required
def redis_fallback_metrics_api():
    """API endpoint to get Redis fallback metrics for monitoring system resilience"""
    try:
        # Check if user has admin privileges
        if not getattr(current_user, 'is_admin', False):
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get metrics from dashboard service
        metrics = dashboard_service.get_cache_metrics()
        
        return jsonify({
            'status': 'success',
            'data': metrics
        })
        
    except Exception as e:
        logger.error(f"Error in Redis fallback metrics API: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500 