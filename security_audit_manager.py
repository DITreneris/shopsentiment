#!/usr/bin/env python
import json
import os
import logging
import schedule
import time
from datetime import datetime, timedelta
import subprocess
from typing import Dict, List, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('security_audit.log')
    ]
)
logger = logging.getLogger(__name__)

class SecurityAuditManager:
    def __init__(self):
        self.audit_schedule = {
            'daily': {
                'tasks': [
                    'Run automated vulnerability scan',
                    'Check security logs for suspicious activities',
                    'Monitor system resources and performance'
                ],
                'last_run': None
            },
            'weekly': {
                'tasks': [
                    'Review security incident reports',
                    'Check for outdated dependencies',
                    'Review access logs and user permissions',
                    'Scan for exposed sensitive information'
                ],
                'last_run': None
            },
            'monthly': {
                'tasks': [
                    'Comprehensive security audit',
                    'Penetration testing',
                    'Review and update security policies',
                    'Backup verification and recovery testing'
                ],
                'last_run': None
            }
        }
        
        self.audit_history = []
        self.load_audit_history()

    def load_audit_history(self):
        """Load audit history from file."""
        try:
            if os.path.exists('audit_history.json'):
                with open('audit_history.json', 'r') as f:
                    self.audit_history = json.load(f)
        except Exception as e:
            logger.error(f"Error loading audit history: {e}")

    def save_audit_history(self):
        """Save audit history to file."""
        try:
            with open('audit_history.json', 'w') as f:
                json.dump(self.audit_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving audit history: {e}")

    def run_security_scan(self) -> Dict[str, Any]:
        """Run security scanner and return results."""
        try:
            result = subprocess.run(
                ['python', 'security_scanner.py'],
                capture_output=True,
                text=True
            )
            
            # Get the latest scan results file
            scan_files = [f for f in os.listdir('.') if f.startswith('security_scan_') and f.endswith('.json')]
            if not scan_files:
                return {'error': 'No scan results found'}
            
            latest_scan = max(scan_files)
            with open(latest_scan, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error running security scan: {e}")
            return {'error': str(e)}

    def run_dependency_check(self) -> Dict[str, Any]:
        """Check for outdated dependencies."""
        try:
            result = subprocess.run(
                ['python', 'update_critical_deps.py'],
                capture_output=True,
                text=True
            )
            return {
                'status': 'success' if result.returncode == 0 else 'failure',
                'output': result.stdout
            }
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return {'error': str(e)}

    def perform_daily_audit(self):
        """Perform daily security audit tasks."""
        logger.info("Starting daily security audit...")
        
        # Run security scan
        scan_results = self.run_security_scan()
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'daily',
            'tasks_completed': self.audit_schedule['daily']['tasks'],
            'scan_results': scan_results,
            'issues_found': []
        }
        
        if scan_results.get('risk_level') != 'LOW':
            audit_entry['issues_found'].append(f"Security risk level: {scan_results.get('risk_level')}")
        
        self.audit_history.append(audit_entry)
        self.audit_schedule['daily']['last_run'] = datetime.now().isoformat()
        self.save_audit_history()
        
        logger.info("Daily security audit completed")

    def perform_weekly_audit(self):
        """Perform weekly security audit tasks."""
        logger.info("Starting weekly security audit...")
        
        # Run dependency check
        dep_check = self.run_dependency_check()
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'weekly',
            'tasks_completed': self.audit_schedule['weekly']['tasks'],
            'dependency_check': dep_check,
            'issues_found': []
        }
        
        if dep_check.get('status') == 'failure':
            audit_entry['issues_found'].append("Dependency update failed")
        
        self.audit_history.append(audit_entry)
        self.audit_schedule['weekly']['last_run'] = datetime.now().isoformat()
        self.save_audit_history()
        
        logger.info("Weekly security audit completed")

    def perform_monthly_audit(self):
        """Perform monthly security audit tasks."""
        logger.info("Starting monthly security audit...")
        
        # Run comprehensive security checks
        scan_results = self.run_security_scan()
        dep_check = self.run_dependency_check()
        
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'monthly',
            'tasks_completed': self.audit_schedule['monthly']['tasks'],
            'scan_results': scan_results,
            'dependency_check': dep_check,
            'issues_found': []
        }
        
        self.audit_history.append(audit_entry)
        self.audit_schedule['monthly']['last_run'] = datetime.now().isoformat()
        self.save_audit_history()
        
        logger.info("Monthly security audit completed")

    def generate_audit_report(self, audit_type: str = None) -> str:
        """Generate a report of audit findings."""
        if not self.audit_history:
            return "No audit history available."
        
        if audit_type:
            relevant_audits = [a for a in self.audit_history if a['type'] == audit_type]
        else:
            relevant_audits = self.audit_history
        
        report = ["Security Audit Report", "=" * 20 + "\n"]
        
        for audit in relevant_audits[-5:]:  # Show last 5 audits
            report.append(f"Audit Type: {audit['type']}")
            report.append(f"Timestamp: {audit['timestamp']}")
            report.append("Tasks Completed:")
            for task in audit['tasks_completed']:
                report.append(f"  - {task}")
            
            if audit.get('issues_found'):
                report.append("\nIssues Found:")
                for issue in audit['issues_found']:
                    report.append(f"  - {issue}")
            
            report.append("\n" + "-" * 40 + "\n")
        
        return "\n".join(report)

def main():
    audit_manager = SecurityAuditManager()
    
    # Schedule daily audit at midnight
    schedule.every().day.at("00:00").do(audit_manager.perform_daily_audit)
    
    # Schedule weekly audit on Monday at 1 AM
    schedule.every().monday.at("01:00").do(audit_manager.perform_weekly_audit)
    
    # Schedule monthly audit on the 1st at 2 AM
    schedule.every().day.at("02:00").do(
        lambda: audit_manager.perform_monthly_audit() 
        if datetime.now().day == 1 else None
    )
    
    # Run initial audit
    logger.info("Running initial security audit...")
    audit_manager.perform_daily_audit()
    
    # Generate and display initial report
    print("\nInitial Audit Report:")
    print(audit_manager.generate_audit_report())
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main() 