#!/usr/bin/env python
"""
Cost Management Cron Script for ShopSentiment

This script is intended to be run as a scheduled task (cron job) to:
1. Monitor resource usage
2. Implement automatic cost optimizations
3. Trigger usage-based scaling
4. Generate budget alerts
5. Run resource cleanup procedures
6. Generate periodic cost reports
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import subprocess

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.utils.cost_management import ResourceMonitor, CostOptimizer

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'cost_management_cron.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger('cost_management_cron')

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='ShopSentiment Cost Management Cron Script')
    parser.add_argument('--config', default='config/cost_management.json', help='Path to configuration file')
    parser.add_argument('--daily', action='store_true', help='Run daily tasks only')
    parser.add_argument('--weekly', action='store_true', help='Run weekly tasks only')
    parser.add_argument('--monthly', action='store_true', help='Run monthly tasks only')
    parser.add_argument('--no-optimize', action='store_true', help='Skip optimization tasks')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip cleanup tasks')
    parser.add_argument('--report-dir', default='reports/cost', help='Directory to store reports')
    return parser.parse_args()

def run_daily_tasks(args):
    """Run daily cost management tasks"""
    logger.info("Starting daily cost management tasks")
    
    # Create monitor and optimizer instances
    monitor = ResourceMonitor(args.config)
    optimizer = CostOptimizer(args.config)
    
    # 1. Monitor resources
    logger.info("Monitoring resources")
    mongodb_metrics = monitor.get_mongodb_metrics()
    redis_metrics = monitor.get_redis_metrics()
    api_metrics = monitor.get_api_metrics()
    
    # Check budget status
    budget_status = monitor.check_budget_status()
    
    # Check if we need to scale resources
    scaling_needs = monitor.evaluate_scaling_needs()
    
    # 2. Implement automatic optimizations if needed
    if not args.no_optimize:
        logger.info("Running automatic optimizations")
        
        # Only perform Redis optimizations if memory usage is high
        if redis_metrics.get('exceeds_threshold', False):
            logger.info("Redis memory usage is high, optimizing")
            optimizer.optimize_redis_memory()
        
        # Scale workers if needed
        if scaling_needs.get('action') != 'none':
            logger.info(f"Worker scaling needed: {scaling_needs.get('action')}")
            optimizer.implement_worker_scaling()
    
    # 3. Save daily monitoring report
    os.makedirs(args.report_dir, exist_ok=True)
    report_file = os.path.join(args.report_dir, f'daily_cost_report_{datetime.now().strftime("%Y%m%d")}.json')
    
    daily_report = {
        'timestamp': datetime.now().isoformat(),
        'resource_metrics': {
            'mongodb': mongodb_metrics,
            'redis': redis_metrics,
            'api': api_metrics
        },
        'budget_status': budget_status,
        'scaling_needs': scaling_needs
    }
    
    try:
        with open(report_file, 'w') as f:
            json.dump(daily_report, f, indent=2)
        logger.info(f"Daily report saved to {report_file}")
    except Exception as e:
        logger.error(f"Error saving daily report: {e}")
    
    return daily_report

def run_weekly_tasks(args):
    """Run weekly cost management tasks"""
    logger.info("Starting weekly cost management tasks")
    
    # Create monitor and optimizer instances
    monitor = ResourceMonitor(args.config)
    optimizer = CostOptimizer(args.config)
    
    # 1. Run comprehensive optimizations
    if not args.no_optimize:
        logger.info("Running comprehensive optimizations")
        # This includes MongoDB index optimization which can be more intensive
        optimization_results = optimizer.optimize_mongodb_indexes()
        logger.info(f"MongoDB optimization analyzed {optimization_results.get('collections_analyzed', 0)} collections")
    
    # 2. Run cleanup procedures
    if not args.no_cleanup:
        logger.info("Running resource cleanup")
        cleanup_results = monitor.trigger_resource_cleanup()
        # Log cleanup results
        mongodb_results = cleanup_results.get('mongodb', {})
        logger.info(f"MongoDB cleanup: {mongodb_results.get('temp_data_deleted', 0)} temp records, {mongodb_results.get('logs_deleted', 0)} logs removed")
    
    # 3. Generate weekly report with cost allocation
    logger.info("Generating weekly cost report")
    cost_report = monitor.generate_cost_report()
    
    # Save weekly report
    os.makedirs(args.report_dir, exist_ok=True)
    report_file = os.path.join(args.report_dir, f'weekly_cost_report_{datetime.now().strftime("%Y%m%d")}.json')
    
    try:
        with open(report_file, 'w') as f:
            json.dump(cost_report, f, indent=2)
        logger.info(f"Weekly report saved to {report_file}")
    except Exception as e:
        logger.error(f"Error saving weekly report: {e}")
    
    # Also generate HTML report for easier reading
    html_report_file = os.path.join(args.report_dir, f'weekly_cost_report_{datetime.now().strftime("%Y%m%d")}.html')
    
    try:
        # Call the manage_costs.py script to generate an HTML report
        cmd = [
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'manage_costs.py'),
            'report',
            '--config', args.config,
            '--output', html_report_file,
            '--format', 'html'
        ]
        subprocess.run(cmd, check=True)
        logger.info(f"HTML weekly report saved to {html_report_file}")
    except Exception as e:
        logger.error(f"Error generating HTML weekly report: {e}")
    
    return cost_report

def run_monthly_tasks(args):
    """Run monthly cost management tasks"""
    logger.info("Starting monthly cost management tasks")
    
    # Create monitor and optimizer instances
    monitor = ResourceMonitor(args.config)
    
    # 1. Generate comprehensive monthly cost report
    logger.info("Generating monthly cost report")
    cost_report = monitor.generate_cost_report()
    
    # 2. Track cost allocation
    cost_allocation = monitor.track_cost_allocation()
    
    # 3. Create monthly budget projection
    # This would typically connect to your cloud provider's billing API
    # For this example, we're using the current cost estimate as a baseline
    budget_status = monitor.check_budget_status()
    current_cost = budget_status.get('estimated_cost', 0)
    budget_limit = budget_status.get('budget_limit', 500)
    
    monthly_projection = {
        'current_cost': current_cost,
        'budget_limit': budget_limit,
        'percent_used': (current_cost / budget_limit * 100) if budget_limit > 0 else 0,
        'projected_end_month_cost': current_cost * 1.1,  # Simple projection with 10% growth
        'within_budget': (current_cost * 1.1) <= budget_limit
    }
    
    # Save monthly report
    os.makedirs(args.report_dir, exist_ok=True)
    report_file = os.path.join(args.report_dir, f'monthly_cost_report_{datetime.now().strftime("%Y%m")}.json')
    
    monthly_report = {
        'timestamp': datetime.now().isoformat(),
        'cost_report': cost_report,
        'cost_allocation': cost_allocation,
        'budget_projection': monthly_projection
    }
    
    try:
        with open(report_file, 'w') as f:
            json.dump(monthly_report, f, indent=2)
        logger.info(f"Monthly report saved to {report_file}")
    except Exception as e:
        logger.error(f"Error saving monthly report: {e}")
    
    # Also generate HTML report for easier reading
    html_report_file = os.path.join(args.report_dir, f'monthly_cost_report_{datetime.now().strftime("%Y%m")}.html')
    
    try:
        # Call the manage_costs.py script to generate an HTML report
        cmd = [
            sys.executable, 
            os.path.join(os.path.dirname(__file__), 'manage_costs.py'),
            'report',
            '--config', args.config,
            '--output', html_report_file,
            '--format', 'html'
        ]
        subprocess.run(cmd, check=True)
        logger.info(f"HTML monthly report saved to {html_report_file}")
    except Exception as e:
        logger.error(f"Error generating HTML monthly report: {e}")
    
    return monthly_report

def main():
    """Main entry point"""
    args = parse_args()
    
    try:
        # Create report directory if it doesn't exist
        os.makedirs(args.report_dir, exist_ok=True)
        
        # Determine which tasks to run
        if args.daily:
            run_daily_tasks(args)
        elif args.weekly:
            run_weekly_tasks(args)
        elif args.monthly:
            run_monthly_tasks(args)
        else:
            # If no specific task type is specified, run based on day of month/week
            now = datetime.now()
            day_of_month = now.day
            day_of_week = now.weekday()  # 0 = Monday, 6 = Sunday
            
            # Always run daily tasks
            run_daily_tasks(args)
            
            # Run weekly tasks on Monday (day_of_week = 0)
            if day_of_week == 0:
                run_weekly_tasks(args)
            
            # Run monthly tasks on the 1st of the month
            if day_of_month == 1:
                run_monthly_tasks(args)
    
    except Exception as e:
        logger.error(f"Error running cost management cron: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 