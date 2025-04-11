"""
Cost Management Utilities for ShopSentiment

This module provides functionality for:
1. Cloud resource cost optimization
2. Usage-based scaling triggers
3. Budget monitoring and alerts
4. Resource cleanup procedures
5. Cost allocation tracking
"""

import os
import json
import logging
import datetime
import requests
from typing import Dict, List, Optional, Tuple
import pymongo
import redis
from app.celery import celery_app

# Configure logging
logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Monitor resource usage and costs across the application"""
    
    def __init__(self, config_path: str = None):
        """Initialize the resource monitor with optional configuration path"""
        self.config = self._load_config(config_path)
        self.thresholds = self.config.get('thresholds', {})
        self.current_usage = {}
        self.budget_data = self.config.get('budget', {})
        self.alert_endpoints = self.config.get('alert_endpoints', {})
    
    def _load_config(self, config_path: str = None) -> Dict:
        """Load configuration from file or use defaults"""
        default_config = {
            'thresholds': {
                'mongodb_storage_gb': 10,
                'redis_memory_mb': 500,
                'api_requests_per_min': 1000,
                'worker_queue_length': 100
            },
            'budget': {
                'monthly_limit_usd': 500,
                'alert_thresholds': [0.5, 0.75, 0.9]
            },
            'alert_endpoints': {
                'email': os.environ.get('COST_ALERT_EMAIL'),
                'webhook': os.environ.get('COST_ALERT_WEBHOOK')
            },
            'scaling': {
                'enabled': True,
                'worker_ratio': 1.5,  # Scale workers when queue length is 1.5x worker count
                'max_workers': 10,
                'min_workers': 2
            },
            'cleanup': {
                'temp_data_ttl_days': 7,
                'log_retention_days': 30,
                'backup_retention_days': 90
            }
        }
        
        if not config_path:
            return default_config
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            if subkey not in config[key]:
                                config[key][subkey] = subvalue
                return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Error loading config from {config_path}: {e}. Using defaults.")
            return default_config

    def get_mongodb_metrics(self, uri: str = None) -> Dict:
        """Get MongoDB usage metrics"""
        try:
            uri = uri or os.environ.get('MONGODB_URI')
            db_name = os.environ.get('MONGODB_DB_NAME', 'shopsentiment')
            client = pymongo.MongoClient(uri)
            db = client[db_name]
            
            # Get database stats
            db_stats = db.command('dbStats')
            storage_size = db_stats.get('storageSize', 0) / (1024 * 1024 * 1024)  # Convert to GB
            
            # Get collection stats
            collections = db.list_collection_names()
            collection_stats = {}
            for coll in collections:
                stats = db.command('collStats', coll)
                collection_stats[coll] = {
                    'size_mb': stats.get('size', 0) / (1024 * 1024),
                    'count': stats.get('count', 0)
                }
            
            # Get index stats
            index_size_mb = sum(
                stats.get('totalIndexSize', 0) for stats in 
                [db.command('collStats', coll) for coll in collections]
            ) / (1024 * 1024)
            
            metrics = {
                'storage_gb': storage_size,
                'collections': collection_stats,
                'index_size_mb': index_size_mb,
                'exceeds_threshold': storage_size > self.thresholds.get('mongodb_storage_gb', 10)
            }
            
            self.current_usage['mongodb'] = metrics
            return metrics
        except Exception as e:
            logger.error(f"Error getting MongoDB metrics: {e}")
            return {'error': str(e)}

    def get_redis_metrics(self, redis_url: str = None) -> Dict:
        """Get Redis usage metrics"""
        try:
            redis_url = redis_url or os.environ.get('REDIS_URL')
            r = redis.from_url(redis_url)
            
            # Get Redis info
            info = r.info()
            used_memory_mb = info.get('used_memory', 0) / (1024 * 1024)
            
            # Get Celery queue lengths
            queues = ['celery', 'celery.priority', 'celery.scheduled']
            queue_lengths = {}
            for queue in queues:
                queue_lengths[queue] = r.llen(queue)
            
            # Get Redis key count
            key_count = info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)
            
            metrics = {
                'memory_mb': used_memory_mb,
                'queue_lengths': queue_lengths,
                'connected_clients': info.get('connected_clients', 0),
                'key_count': key_count,
                'exceeds_threshold': used_memory_mb > self.thresholds.get('redis_memory_mb', 500)
            }
            
            self.current_usage['redis'] = metrics
            return metrics
        except Exception as e:
            logger.error(f"Error getting Redis metrics: {e}")
            return {'error': str(e)}

    def get_api_metrics(self) -> Dict:
        """Get API usage metrics from logs or monitoring systems"""
        try:
            # This would typically connect to your API gateway, load balancer metrics
            # or parse application logs
            # For example purposes, we're creating sample data
            metrics = {
                'requests_per_min': 800,  # Sample data
                'avg_response_time_ms': 150,
                'error_rate': 0.02,
                'exceeds_threshold': 800 > self.thresholds.get('api_requests_per_min', 1000)
            }
            
            self.current_usage['api'] = metrics
            return metrics
        except Exception as e:
            logger.error(f"Error getting API metrics: {e}")
            return {'error': str(e)}

    def check_budget_status(self) -> Dict:
        """Check the budget status and evaluate if we need to trigger alerts"""
        try:
            # Get the current date and determine the month
            now = datetime.datetime.now()
            current_month = now.strftime('%Y-%m')
            
            # Sample budget calculation - in a real app this would fetch from your cloud provider's API
            # Example for AWS using boto3, or GCP using google-cloud-billing
            monthly_limit = self.budget_data.get('monthly_limit_usd', 500)
            
            # For demo purposes - estimated costs based on resource usage
            est_mongodb_cost = self.current_usage.get('mongodb', {}).get('storage_gb', 0) * 0.25
            est_redis_cost = self.current_usage.get('redis', {}).get('memory_mb', 0) * 0.001
            est_compute_cost = 100  # Sample fixed compute cost
            
            # Total estimated cost
            estimated_cost = est_mongodb_cost + est_redis_cost + est_compute_cost
            budget_percent_used = (estimated_cost / monthly_limit) if monthly_limit > 0 else 0
            
            # Check for threshold alerts
            alerts = []
            for threshold in self.budget_data.get('alert_thresholds', [0.5, 0.75, 0.9]):
                if budget_percent_used >= threshold:
                    alerts.append({
                        'level': 'warning' if threshold < 0.9 else 'critical',
                        'message': f"Budget alert: {threshold*100:.0f}% of monthly budget used ({estimated_cost:.2f} / {monthly_limit:.2f} USD)"
                    })
            
            budget_status = {
                'month': current_month,
                'estimated_cost': estimated_cost,
                'budget_limit': monthly_limit,
                'percent_used': budget_percent_used * 100,
                'alerts': alerts,
                'breakdown': {
                    'mongodb': est_mongodb_cost,
                    'redis': est_redis_cost,
                    'compute': est_compute_cost
                }
            }
            
            # Send alerts if needed
            if alerts:
                self.send_budget_alerts(alerts, budget_status)
            
            return budget_status
        except Exception as e:
            logger.error(f"Error checking budget status: {e}")
            return {'error': str(e)}

    def send_budget_alerts(self, alerts: List[Dict], budget_status: Dict) -> bool:
        """Send budget alerts via configured channels"""
        try:
            for alert in alerts:
                # Email alert
                if self.alert_endpoints.get('email'):
                    # In a real app, you would implement email sending here
                    logger.info(f"Would send email alert to {self.alert_endpoints['email']}: {alert['message']}")
                
                # Webhook alert
                if self.alert_endpoints.get('webhook'):
                    try:
                        requests.post(
                            self.alert_endpoints['webhook'],
                            json={
                                'alert': alert,
                                'budget_status': budget_status,
                                'timestamp': datetime.datetime.now().isoformat()
                            },
                            timeout=5
                        )
                    except requests.RequestException as e:
                        logger.error(f"Failed to send webhook alert: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending budget alerts: {e}")
            return False

    def evaluate_scaling_needs(self) -> Dict:
        """Evaluate if we need to scale resources up or down based on usage"""
        try:
            if not self.config.get('scaling', {}).get('enabled', False):
                return {'scaling_enabled': False}
            
            scaling_config = self.config.get('scaling', {})
            
            # Get current worker count
            worker_stats = celery_app.control.inspect().stats() or {}
            current_worker_count = len(worker_stats)
            
            # Get queue length
            redis_metrics = self.current_usage.get('redis', {})
            queue_length = sum(redis_metrics.get('queue_lengths', {}).values())
            
            # Calculate if we need to scale up or down
            worker_ratio = scaling_config.get('worker_ratio', 1.5)
            max_workers = scaling_config.get('max_workers', 10)
            min_workers = scaling_config.get('min_workers', 2)
            
            if queue_length > current_worker_count * worker_ratio and current_worker_count < max_workers:
                # Need to scale up
                target_workers = min(current_worker_count + 1, max_workers)
                scaling_action = 'scale_up'
            elif queue_length < current_worker_count * 0.5 and current_worker_count > min_workers:
                # Can scale down
                target_workers = max(current_worker_count - 1, min_workers)
                scaling_action = 'scale_down'
            else:
                # No scaling needed
                target_workers = current_worker_count
                scaling_action = 'none'
            
            return {
                'scaling_enabled': True,
                'current_workers': current_worker_count,
                'queue_length': queue_length,
                'action': scaling_action,
                'target_workers': target_workers,
                'worker_ratio': worker_ratio
            }
        except Exception as e:
            logger.error(f"Error evaluating scaling needs: {e}")
            return {'error': str(e)}

    def trigger_resource_cleanup(self) -> Dict:
        """Trigger cleanup of temporary resources and unused data"""
        try:
            cleanup_config = self.config.get('cleanup', {})
            
            now = datetime.datetime.now()
            temp_data_cutoff = now - datetime.timedelta(days=cleanup_config.get('temp_data_ttl_days', 7))
            log_cutoff = now - datetime.timedelta(days=cleanup_config.get('log_retention_days', 30))
            backup_cutoff = now - datetime.timedelta(days=cleanup_config.get('backup_retention_days', 90))
            
            # MongoDB cleanup
            try:
                uri = os.environ.get('MONGODB_URI')
                db_name = os.environ.get('MONGODB_DB_NAME', 'shopsentiment')
                client = pymongo.MongoClient(uri)
                db = client[db_name]
                
                # Clean up temp collections
                temp_deleted = db.temp_data.delete_many({'created_at': {'$lt': temp_data_cutoff}}).deleted_count
                
                # Clean up old logs
                log_deleted = db.application_logs.delete_many({'timestamp': {'$lt': log_cutoff}}).deleted_count
                
                # Clean up old backups
                backup_deleted = db.database_backups.delete_many({'created_at': {'$lt': backup_cutoff}}).deleted_count
                
                mongodb_cleanup = {
                    'temp_data_deleted': temp_deleted,
                    'logs_deleted': log_deleted,
                    'backups_deleted': backup_deleted
                }
            except Exception as e:
                logger.error(f"Error cleaning up MongoDB: {e}")
                mongodb_cleanup = {'error': str(e)}
            
            # File system cleanup (logs, temporary files)
            file_cleanup = {
                'logs_deleted': 0,
                'temp_files_deleted': 0
            }
            
            # Example: clean up log files
            log_dir = 'logs'
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log'):
                        file_path = os.path.join(log_dir, filename)
                        try:
                            file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_time < log_cutoff:
                                os.remove(file_path)
                                file_cleanup['logs_deleted'] += 1
                        except OSError as e:
                            logger.error(f"Error deleting log file {file_path}: {e}")
            
            # Example: clean up temp files
            temp_dir = 'temp'
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
                        if file_time < temp_data_cutoff:
                            os.remove(file_path)
                            file_cleanup['temp_files_deleted'] += 1
                    except OSError as e:
                        logger.error(f"Error deleting temp file {file_path}: {e}")
            
            return {
                'mongodb': mongodb_cleanup,
                'filesystem': file_cleanup,
                'cleanup_time': now.isoformat()
            }
        except Exception as e:
            logger.error(f"Error triggering resource cleanup: {e}")
            return {'error': str(e)}

    def track_cost_allocation(self) -> Dict:
        """Track cost allocation per feature, team, or project"""
        # This would typically connect to your cloud provider's tagging/cost allocation API
        # For example, using AWS Cost Explorer or Google Cloud Billing
        # For sample implementation, we'll create some mock data
        
        try:
            features = {
                'core_api': {'compute_cost': 150, 'storage_cost': 50, 'percentage': 40},
                'sentiment_analysis': {'compute_cost': 100, 'storage_cost': 30, 'percentage': 26},
                'recommendation_engine': {'compute_cost': 80, 'storage_cost': 20, 'percentage': 20},
                'mobile_api': {'compute_cost': 40, 'storage_cost': 10, 'percentage': 10},
                'admin_dashboard': {'compute_cost': 10, 'storage_cost': 10, 'percentage': 4}
            }
            
            return {
                'by_feature': features,
                'timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error tracking cost allocation: {e}")
            return {'error': str(e)}

    def generate_cost_report(self) -> Dict:
        """Generate a comprehensive cost report with recommendations"""
        try:
            # Gather all metrics
            mongodb_metrics = self.get_mongodb_metrics()
            redis_metrics = self.get_redis_metrics()
            api_metrics = self.get_api_metrics()
            budget_status = self.check_budget_status()
            scaling_needs = self.evaluate_scaling_needs()
            cost_allocation = self.track_cost_allocation()
            
            # Generate optimization recommendations
            recommendations = []
            
            # MongoDB recommendations
            if mongodb_metrics.get('exceeds_threshold', False):
                recommendations.append({
                    'resource': 'mongodb',
                    'issue': 'High storage usage',
                    'recommendation': 'Consider implementing data archiving or TTL indexes',
                    'estimated_savings': '15-25%'
                })
            
            # Check for large collections that might need optimization
            large_collections = [
                (name, stats) for name, stats in mongodb_metrics.get('collections', {}).items()
                if stats.get('size_mb', 0) > 500
            ]
            for name, stats in large_collections:
                recommendations.append({
                    'resource': 'mongodb',
                    'issue': f'Large collection: {name} ({stats["size_mb"]:.2f} MB)',
                    'recommendation': 'Review indexing strategy and implement data archiving',
                    'estimated_savings': '10-20%'
                })
            
            # Redis recommendations
            if redis_metrics.get('exceeds_threshold', False):
                recommendations.append({
                    'resource': 'redis',
                    'issue': 'High memory usage',
                    'recommendation': 'Implement key expiration or reduce cache TTLs',
                    'estimated_savings': '10-30%'
                })
            
            # Scaling recommendations
            if scaling_needs.get('action') == 'scale_down':
                recommendations.append({
                    'resource': 'worker',
                    'issue': 'Worker over-provisioning',
                    'recommendation': f'Scale down from {scaling_needs["current_workers"]} to {scaling_needs["target_workers"]} workers',
                    'estimated_savings': f'{((scaling_needs["current_workers"] - scaling_needs["target_workers"]) / scaling_needs["current_workers"] * 100):.1f}%'
                })
            
            report = {
                'timestamp': datetime.datetime.now().isoformat(),
                'budget_status': budget_status,
                'resource_metrics': {
                    'mongodb': mongodb_metrics,
                    'redis': redis_metrics,
                    'api': api_metrics
                },
                'scaling_needs': scaling_needs,
                'cost_allocation': cost_allocation,
                'optimization_recommendations': recommendations
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating cost report: {e}")
            return {'error': str(e)}

# Class for direct cost optimization actions
class CostOptimizer:
    """Implement cost optimization strategies for ShopSentiment"""
    
    def __init__(self, config_path: str = None):
        """Initialize the cost optimizer with optional configuration path"""
        self.monitor = ResourceMonitor(config_path)
        self.config = self.monitor.config
    
    def optimize_mongodb_indexes(self, uri: str = None, db_name: str = None) -> Dict:
        """Optimize MongoDB indexes to reduce storage costs"""
        try:
            uri = uri or os.environ.get('MONGODB_URI')
            db_name = db_name or os.environ.get('MONGODB_DB_NAME', 'shopsentiment')
            client = pymongo.MongoClient(uri)
            db = client[db_name]
            
            # Get collections and their indexes
            collections = db.list_collection_names()
            results = {}
            
            for coll_name in collections:
                coll = db[coll_name]
                # Get current indexes
                current_indexes = list(coll.list_indexes())
                unused_indexes = []
                
                # Analyze index usage (in a real app, you would use index stats)
                # For this example, we're just using a simple heuristic
                for idx in current_indexes:
                    # Skip the _id index as it's required
                    if idx['name'] == '_id_':
                        continue
                    
                    # Check if this is potentially an unused index
                    # In a real app, you would check the index usage stats
                    if 'unused' in idx.get('name', ''):
                        unused_indexes.append(idx['name'])
                
                # Store results for this collection
                results[coll_name] = {
                    'total_indexes': len(current_indexes),
                    'unused_indexes': unused_indexes
                }
                
                # Don't actually drop indexes in this example
                # In a real app, you might drop them after careful analysis
                # for idx_name in unused_indexes:
                #     coll.drop_index(idx_name)
            
            return {
                'analysis_complete': True,
                'collections_analyzed': len(collections),
                'results': results
            }
        except Exception as e:
            logger.error(f"Error optimizing MongoDB indexes: {e}")
            return {'error': str(e)}
    
    def optimize_redis_memory(self, redis_url: str = None) -> Dict:
        """Optimize Redis memory usage by setting appropriate TTLs"""
        try:
            redis_url = redis_url or os.environ.get('REDIS_URL')
            r = redis.from_url(redis_url)
            
            # Memory usage before optimization
            before_memory = r.info()['used_memory']
            
            # Get all keys (WARNING: don't use in production without limiting scan)
            all_keys = []
            cursor = '0'
            while cursor != 0:
                cursor, keys = r.scan(cursor=cursor, count=100)
                all_keys.extend(keys)
                if not cursor:
                    break
            
            # Sample optimization strategy: set TTL on cache keys
            cache_keys = [k for k in all_keys if k.startswith(b'cache:')]
            for key in cache_keys:
                # Only set TTL if key doesn't already have one
                if r.ttl(key) == -1:  # -1 means no TTL set
                    r.expire(key, 86400)  # 1 day TTL
            
            # Memory usage after optimization
            after_memory = r.info()['used_memory']
            
            return {
                'before_memory_bytes': before_memory,
                'after_memory_bytes': after_memory,
                'memory_difference_bytes': before_memory - after_memory,
                'percent_reduction': ((before_memory - after_memory) / before_memory * 100) if before_memory > 0 else 0,
                'cache_keys_optimized': len(cache_keys)
            }
        except Exception as e:
            logger.error(f"Error optimizing Redis memory: {e}")
            return {'error': str(e)}
    
    def implement_worker_scaling(self, target_count: int = None) -> Dict:
        """Implement Celery worker scaling based on demand"""
        try:
            # This would typically be implemented using your cloud provider's APIs
            # or container orchestration platform like Kubernetes
            current_metrics = self.monitor.evaluate_scaling_needs()
            
            target_count = target_count or current_metrics.get('target_workers')
            current_count = current_metrics.get('current_workers', 0)
            
            if target_count is None:
                return {'error': 'Could not determine target worker count'}
            
            if target_count == current_count:
                return {
                    'status': 'no_action',
                    'message': f'Worker count already at optimal level ({current_count})'
                }
            
            # In a real app, you would implement actual scaling here
            # For example, with Kubernetes:
            # kubectl scale deployment/celery-workers --replicas=target_count
            
            return {
                'status': 'success',
                'action': 'scale_up' if target_count > current_count else 'scale_down',
                'previous_count': current_count,
                'target_count': target_count,
                'implementation': 'simulated'  # This would be 'kubernetes', 'docker', etc. in a real app
            }
        except Exception as e:
            logger.error(f"Error implementing worker scaling: {e}")
            return {'error': str(e)}
    
    def implement_all_optimizations(self) -> Dict:
        """Implement all cost optimization strategies"""
        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'mongodb_optimization': self.optimize_mongodb_indexes(),
            'redis_optimization': self.optimize_redis_memory(),
            'worker_scaling': self.implement_worker_scaling(),
            'cleanup': self.monitor.trigger_resource_cleanup()
        }
        
        # Check for any errors
        has_errors = any('error' in result for result in results.values() if isinstance(result, dict))
        
        results['status'] = 'partial_success' if has_errors else 'success'
        return results 