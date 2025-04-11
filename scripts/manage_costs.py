#!/usr/bin/env python
"""
Cost Management CLI for ShopSentiment

This script provides a command-line interface for managing and optimizing costs:
- Monitor resource usage
- Implement cost optimization
- Set up usage-based scaling triggers
- Create budget monitoring and alerts
- Run resource cleanup procedures
- Generate cost allocation reports
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.cost_management import ResourceMonitor, CostOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/cost_management.log')
    ]
)
logger = logging.getLogger('cost_management')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='ShopSentiment Cost Management CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor resource usage')
    monitor_parser.add_argument('--config', help='Path to configuration file')
    monitor_parser.add_argument('--output', help='Output file for monitoring results')
    
    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Implement cost optimizations')
    optimize_parser.add_argument('--config', help='Path to configuration file')
    optimize_parser.add_argument('--skip-redis', action='store_true', help='Skip Redis optimizations')
    optimize_parser.add_argument('--skip-mongodb', action='store_true', help='Skip MongoDB optimizations')
    optimize_parser.add_argument('--skip-scaling', action='store_true', help='Skip worker scaling')
    optimize_parser.add_argument('--skip-cleanup', action='store_true', help='Skip resource cleanup')
    
    # Budget command
    budget_parser = subparsers.add_parser('budget', help='Manage budget monitoring and alerts')
    budget_parser.add_argument('--config', help='Path to configuration file')
    budget_parser.add_argument('--set-limit', type=float, help='Set monthly budget limit in USD')
    budget_parser.add_argument('--check', action='store_true', help='Check current budget status')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Run resource cleanup procedures')
    cleanup_parser.add_argument('--config', help='Path to configuration file')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned up without taking action')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate cost allocation reports')
    report_parser.add_argument('--config', help='Path to configuration file')
    report_parser.add_argument('--output', help='Output file for report')
    report_parser.add_argument('--format', choices=['json', 'csv', 'html'], default='json', help='Report format')
    
    return parser.parse_args()

def monitor_resources(args):
    """Monitor resource usage"""
    logger.info("Starting resource monitoring...")
    monitor = ResourceMonitor(args.config)
    
    # Get metrics
    mongodb_metrics = monitor.get_mongodb_metrics()
    redis_metrics = monitor.get_redis_metrics()
    api_metrics = monitor.get_api_metrics()
    
    # Check for warning thresholds
    warnings = []
    if mongodb_metrics.get('exceeds_threshold', False):
        warnings.append(f"MongoDB storage usage exceeds threshold: {mongodb_metrics.get('storage_gb', 0):.2f} GB")
    
    if redis_metrics.get('exceeds_threshold', False):
        warnings.append(f"Redis memory usage exceeds threshold: {redis_metrics.get('memory_mb', 0):.2f} MB")
    
    # Output results
    report = {
        'timestamp': datetime.now().isoformat(),
        'mongodb': mongodb_metrics,
        'redis': redis_metrics,
        'api': api_metrics,
        'warnings': warnings
    }
    
    # Display report
    print("\n=== Resource Monitoring Report ===")
    print(f"Time: {report['timestamp']}")
    print("\nMongoDB:")
    print(f"- Storage: {mongodb_metrics.get('storage_gb', 0):.2f} GB")
    print(f"- Index Size: {mongodb_metrics.get('index_size_mb', 0):.2f} MB")
    
    print("\nRedis:")
    print(f"- Memory: {redis_metrics.get('memory_mb', 0):.2f} MB")
    queue_lengths = redis_metrics.get('queue_lengths', {})
    print(f"- Queue Lengths: {sum(queue_lengths.values())} total tasks")
    
    print("\nAPI:")
    print(f"- Requests/min: {api_metrics.get('requests_per_min', 0)}")
    print(f"- Avg Response Time: {api_metrics.get('avg_response_time_ms', 0)} ms")
    
    if warnings:
        print("\nWARNINGS:")
        for warning in warnings:
            print(f"- {warning}")
    
    # Save report if output file specified
    if args.output:
        try:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
    
    return report

def optimize_costs(args):
    """Implement cost optimizations"""
    logger.info("Starting cost optimization...")
    optimizer = CostOptimizer(args.config)
    
    results = {
        'timestamp': datetime.now().isoformat(),
    }
    
    # MongoDB optimization
    if not args.skip_mongodb:
        logger.info("Optimizing MongoDB...")
        mongodb_results = optimizer.optimize_mongodb_indexes()
        results['mongodb'] = mongodb_results
        
        print("\n=== MongoDB Optimization Results ===")
        if 'error' in mongodb_results:
            print(f"Error: {mongodb_results['error']}")
        else:
            print(f"Collections analyzed: {mongodb_results.get('collections_analyzed', 0)}")
            for coll, stats in mongodb_results.get('results', {}).items():
                if stats.get('unused_indexes'):
                    print(f"- {coll}: {len(stats.get('unused_indexes', []))} potentially unused indexes")
    
    # Redis optimization
    if not args.skip_redis:
        logger.info("Optimizing Redis...")
        redis_results = optimizer.optimize_redis_memory()
        results['redis'] = redis_results
        
        print("\n=== Redis Optimization Results ===")
        if 'error' in redis_results:
            print(f"Error: {redis_results['error']}")
        else:
            before_mb = redis_results.get('before_memory_bytes', 0) / (1024 * 1024)
            after_mb = redis_results.get('after_memory_bytes', 0) / (1024 * 1024)
            print(f"Memory before: {before_mb:.2f} MB")
            print(f"Memory after: {after_mb:.2f} MB")
            print(f"Reduction: {redis_results.get('percent_reduction', 0):.2f}%")
            print(f"Cache keys optimized: {redis_results.get('cache_keys_optimized', 0)}")
    
    # Worker scaling
    if not args.skip_scaling:
        logger.info("Evaluating worker scaling...")
        scaling_results = optimizer.implement_worker_scaling()
        results['scaling'] = scaling_results
        
        print("\n=== Worker Scaling Results ===")
        if 'error' in scaling_results:
            print(f"Error: {scaling_results['error']}")
        else:
            if scaling_results.get('status') == 'no_action':
                print(f"No scaling needed. Current workers: {scaling_results.get('previous_count', 0)}")
            else:
                print(f"Action: {scaling_results.get('action', 'unknown')}")
                print(f"Workers: {scaling_results.get('previous_count', 0)} → {scaling_results.get('target_count', 0)}")
    
    # Resource cleanup
    if not args.skip_cleanup:
        logger.info("Running resource cleanup...")
        cleanup_results = optimizer.monitor.trigger_resource_cleanup()
        results['cleanup'] = cleanup_results
        
        print("\n=== Resource Cleanup Results ===")
        if 'error' in cleanup_results:
            print(f"Error: {cleanup_results['error']}")
        else:
            mongodb = cleanup_results.get('mongodb', {})
            print("MongoDB cleanup:")
            print(f"- Temp data deleted: {mongodb.get('temp_data_deleted', 0)}")
            print(f"- Logs deleted: {mongodb.get('logs_deleted', 0)}")
            print(f"- Backups deleted: {mongodb.get('backups_deleted', 0)}")
            
            filesystem = cleanup_results.get('filesystem', {})
            print("Filesystem cleanup:")
            print(f"- Log files deleted: {filesystem.get('logs_deleted', 0)}")
            print(f"- Temp files deleted: {filesystem.get('temp_files_deleted', 0)}")
    
    return results

def manage_budget(args):
    """Manage budget monitoring and alerts"""
    logger.info("Managing budget...")
    monitor = ResourceMonitor(args.config)
    
    # Set budget limit if specified
    if args.set_limit:
        logger.info(f"Setting budget limit to ${args.set_limit:.2f} USD")
        # In a real app, you would update the configuration file here
        print(f"Budget limit set to ${args.set_limit:.2f} USD")
        
        # This is just a simulation for this example
        config_path = args.config or 'config/cost_management.json'
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                config['budget']['monthly_limit_usd'] = args.set_limit
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                
                print(f"Updated budget limit in {config_path}")
            else:
                print(f"Configuration file {config_path} not found")
        except Exception as e:
            logger.error(f"Error updating budget limit: {e}")
    
    # Check budget status
    if args.check or not args.set_limit:
        budget_status = monitor.check_budget_status()
        
        print("\n=== Budget Status ===")
        if 'error' in budget_status:
            print(f"Error: {budget_status['error']}")
        else:
            print(f"Month: {budget_status.get('month')}")
            print(f"Budget: ${budget_status.get('budget_limit', 0):.2f} USD")
            print(f"Estimated cost: ${budget_status.get('estimated_cost', 0):.2f} USD")
            print(f"Percent used: {budget_status.get('percent_used', 0):.1f}%")
            
            # Show cost breakdown
            breakdown = budget_status.get('breakdown', {})
            print("\nCost Breakdown:")
            for service, cost in breakdown.items():
                print(f"- {service}: ${cost:.2f} USD")
            
            # Show alerts
            alerts = budget_status.get('alerts', [])
            if alerts:
                print("\nBudget Alerts:")
                for alert in alerts:
                    print(f"- [{alert.get('level', 'info').upper()}] {alert.get('message', '')}")
        
        return budget_status

def run_cleanup(args):
    """Run resource cleanup procedures"""
    logger.info("Running resource cleanup...")
    monitor = ResourceMonitor(args.config)
    
    if args.dry_run:
        # In a dry run, we just estimate what would be cleaned up
        print("\n=== Cleanup Dry Run ===")
        print("The following would be cleaned up:")
        
        cleanup_config = monitor.config.get('cleanup', {})
        print(f"- Temporary data older than {cleanup_config.get('temp_data_ttl_days', 7)} days")
        print(f"- Log files older than {cleanup_config.get('log_retention_days', 30)} days")
        print(f"- Backups older than {cleanup_config.get('backup_retention_days', 90)} days")
        
        return {'dry_run': True, 'config': cleanup_config}
    else:
        # Actually run the cleanup
        cleanup_results = monitor.trigger_resource_cleanup()
        
        print("\n=== Resource Cleanup Results ===")
        if 'error' in cleanup_results:
            print(f"Error: {cleanup_results['error']}")
        else:
            mongodb = cleanup_results.get('mongodb', {})
            print("MongoDB cleanup:")
            print(f"- Temp data deleted: {mongodb.get('temp_data_deleted', 0)}")
            print(f"- Logs deleted: {mongodb.get('logs_deleted', 0)}")
            print(f"- Backups deleted: {mongodb.get('backups_deleted', 0)}")
            
            filesystem = cleanup_results.get('filesystem', {})
            print("Filesystem cleanup:")
            print(f"- Log files deleted: {filesystem.get('logs_deleted', 0)}")
            print(f"- Temp files deleted: {filesystem.get('temp_files_deleted', 0)}")
        
        return cleanup_results

def generate_report(args):
    """Generate cost allocation reports"""
    logger.info("Generating cost report...")
    monitor = ResourceMonitor(args.config)
    
    # Generate comprehensive report
    report = monitor.generate_cost_report()
    
    print("\n=== Cost Allocation Report ===")
    if 'error' in report:
        print(f"Error: {report['error']}")
    else:
        print(f"Generated at: {report.get('timestamp')}")
        
        # Show budget status
        budget_status = report.get('budget_status', {})
        print(f"\nBudget: ${budget_status.get('budget_limit', 0):.2f} USD")
        print(f"Estimated cost: ${budget_status.get('estimated_cost', 0):.2f} USD")
        print(f"Percent used: {budget_status.get('percent_used', 0):.1f}%")
        
        # Show cost allocation
        cost_allocation = report.get('cost_allocation', {}).get('by_feature', {})
        print("\nCost Allocation by Feature:")
        for feature, costs in cost_allocation.items():
            print(f"- {feature}: ${costs.get('compute_cost', 0) + costs.get('storage_cost', 0):.2f} USD ({costs.get('percentage', 0)}%)")
        
        # Show recommendations
        recommendations = report.get('optimization_recommendations', [])
        if recommendations:
            print("\nOptimization Recommendations:")
            for rec in recommendations:
                print(f"- [{rec.get('resource')}] {rec.get('issue')}")
                print(f"  Recommendation: {rec.get('recommendation')}")
                print(f"  Estimated savings: {rec.get('estimated_savings')}")
    
    # Save report if output file specified
    if args.output:
        output_format = args.format.lower()
        try:
            if output_format == 'json':
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
            elif output_format == 'csv':
                # Basic CSV export for demonstration
                import csv
                with open(args.output, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Feature', 'Compute Cost', 'Storage Cost', 'Percentage'])
                    for feature, costs in report.get('cost_allocation', {}).get('by_feature', {}).items():
                        writer.writerow([
                            feature, 
                            costs.get('compute_cost', 0),
                            costs.get('storage_cost', 0),
                            costs.get('percentage', 0)
                        ])
            elif output_format == 'html':
                # Basic HTML report for demonstration
                html_content = f"""
                <html>
                <head>
                    <title>Cost Allocation Report</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 40px; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }}
                        th {{ background-color: #f2f2f2; }}
                        .warning {{ color: orange; }}
                        .critical {{ color: red; }}
                    </style>
                </head>
                <body>
                    <h1>Cost Allocation Report</h1>
                    <p>Generated at: {report.get('timestamp')}</p>
                    
                    <h2>Budget Status</h2>
                    <p>Month: {budget_status.get('month')}</p>
                    <p>Budget: ${budget_status.get('budget_limit', 0):.2f} USD</p>
                    <p>Estimated cost: ${budget_status.get('estimated_cost', 0):.2f} USD</p>
                    <p>Percent used: {budget_status.get('percent_used', 0):.1f}%</p>
                    
                    <h2>Cost Allocation by Feature</h2>
                    <table>
                        <tr>
                            <th>Feature</th>
                            <th>Compute Cost</th>
                            <th>Storage Cost</th>
                            <th>Total Cost</th>
                            <th>Percentage</th>
                        </tr>
                """
                
                for feature, costs in report.get('cost_allocation', {}).get('by_feature', {}).items():
                    compute = costs.get('compute_cost', 0)
                    storage = costs.get('storage_cost', 0)
                    total = compute + storage
                    percent = costs.get('percentage', 0)
                    
                    html_content += f"""
                        <tr>
                            <td>{feature}</td>
                            <td>${compute:.2f}</td>
                            <td>${storage:.2f}</td>
                            <td>${total:.2f}</td>
                            <td>{percent}%</td>
                        </tr>
                    """
                
                html_content += """
                    </table>
                    
                    <h2>Optimization Recommendations</h2>
                    <ul>
                """
                
                for rec in report.get('optimization_recommendations', []):
                    html_content += f"""
                        <li>
                            <strong>{rec.get('resource')}:</strong> {rec.get('issue')}<br>
                            Recommendation: {rec.get('recommendation')}<br>
                            Estimated savings: {rec.get('estimated_savings')}
                        </li>
                    """
                
                html_content += """
                    </ul>
                </body>
                </html>
                """
                
                with open(args.output, 'w') as f:
                    f.write(html_content)
            
            logger.info(f"Report saved to {args.output}")
            print(f"\nReport saved to {args.output}")
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            print(f"Error saving report: {e}")
    
    return report

def main():
    """Main entry point"""
    args = parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    try:
        if args.command == 'monitor':
            monitor_resources(args)
        elif args.command == 'optimize':
            optimize_costs(args)
        elif args.command == 'budget':
            manage_budget(args)
        elif args.command == 'cleanup':
            run_cleanup(args)
        elif args.command == 'report':
            generate_report(args)
        else:
            print("Please specify a command. Use --help for available commands.")
    except Exception as e:
        logger.error(f"Error running command {args.command}: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 