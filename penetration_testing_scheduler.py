#!/usr/bin/env python
import schedule
import time
import subprocess
import logging
import os
import json
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('penetration_testing.log')
    ]
)
logger = logging.getLogger(__name__)

class PenetrationTestingScheduler:
    """Manages the scheduling and execution of penetration testing."""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', ''),
            'to_email': os.getenv('TO_EMAIL', '')
        }
        
        self.pentest_schedule = {
            'quarterly': {
                'description': 'Full system penetration test covering all components',
                'last_run': None,
                'next_run': self._get_next_quarter_date(),
                'duration': '2 weeks',
                'assigned_team': 'External Security Firm',
                'scope': 'All production systems including API endpoints, frontend, database, and infrastructure',
                'priority': 'Critical'
            },
            'monthly': {
                'description': 'Targeted penetration testing of critical API endpoints',
                'last_run': None,
                'next_run': self._get_next_month_date(),
                'duration': '3 days',
                'assigned_team': 'Internal Security Team',
                'scope': 'API endpoints, authentication services, and data access points',
                'priority': 'High'
            },
            'bi-weekly': {
                'description': 'Automated penetration testing of recent changes',
                'last_run': None,
                'next_run': self._get_next_biweekly_date(),
                'duration': '1 day',
                'assigned_team': 'DevOps',
                'scope': 'Recently modified components and endpoints',
                'priority': 'Medium'
            }
        }
        
        self.pentest_history = []
        self.load_pentest_history()

    def _get_next_quarter_date(self) -> str:
        """Calculate the start date of the next quarter."""
        today = datetime.now()
        month = today.month
        year = today.year
        
        # Determine the next quarter start
        if month < 4:  # Q1
            next_quarter = datetime(year, 4, 1)
        elif month < 7:  # Q2
            next_quarter = datetime(year, 7, 1)
        elif month < 10:  # Q3
            next_quarter = datetime(year, 10, 1)
        else:  # Q4
            next_quarter = datetime(year + 1, 1, 1)
        
        return next_quarter.isoformat()

    def _get_next_month_date(self) -> str:
        """Calculate the start date of the next month."""
        today = datetime.now()
        month = today.month
        year = today.year
        
        # Move to the first day of next month
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        return next_month.isoformat()

    def _get_next_biweekly_date(self) -> str:
        """Calculate the date two weeks from now."""
        today = datetime.now()
        next_biweekly = today + timedelta(days=14)
        return next_biweekly.isoformat()

    def load_pentest_history(self):
        """Load penetration testing history from file."""
        try:
            if os.path.exists('pentest_history.json'):
                with open('pentest_history.json', 'r') as f:
                    self.pentest_history = json.load(f)
        except Exception as e:
            logger.error(f"Error loading penetration testing history: {e}")

    def save_pentest_history(self):
        """Save penetration testing history to file."""
        try:
            with open('pentest_history.json', 'w') as f:
                json.dump(self.pentest_history, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving penetration testing history: {e}")

    def save_pentest_schedule(self):
        """Save penetration testing schedule to file."""
        try:
            with open('pentest_schedule.json', 'w') as f:
                json.dump(self.pentest_schedule, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving penetration testing schedule: {e}")

    def schedule_penetration_test(self, test_type: str):
        """Schedule a penetration test and notify the team."""
        if test_type not in self.pentest_schedule:
            logger.error(f"Unknown test type: {test_type}")
            return
        
        test_info = self.pentest_schedule[test_type]
        logger.info(f"Scheduling {test_type} penetration test")
        
        # Record that we're scheduling this test
        now = datetime.now().isoformat()
        test_info['last_scheduled'] = now
        
        # Add to history
        test_record = {
            'type': test_type,
            'scheduled_at': now,
            'planned_start_date': test_info['next_run'],
            'status': 'scheduled',
            'assigned_team': test_info['assigned_team'],
            'scope': test_info['scope']
        }
        self.pentest_history.append(test_record)
        
        # Save updated state
        self.save_pentest_history()
        self.save_pentest_schedule()
        
        # Send notification
        self.send_schedule_notification(test_type, test_info)
        
        logger.info(f"{test_type.capitalize()} penetration test scheduled for {test_info['next_run']}")

    def send_schedule_notification(self, test_type: str, test_info: Dict[str, Any]):
        """Send email notification about upcoming penetration test."""
        subject = f"Upcoming {test_type.capitalize()} Penetration Test - {test_info['priority']} Priority"
        
        body = f"""
        Penetration Testing Schedule Notification
        =========================================
        
        A {test_type} penetration test has been scheduled:
        
        Test Description: {test_info['description']}
        Start Date: {test_info['next_run']}
        Duration: {test_info['duration']}
        Assigned Team: {test_info['assigned_team']}
        Scope: {test_info['scope']}
        Priority: {test_info['priority']}
        
        Please prepare all necessary resources and access for the penetration testing team.
        """
        
        self.send_email(subject, body)

    def send_email(self, subject: str, body: str):
        """Send email using configured SMTP settings."""
        if not all([self.email_config['username'], self.email_config['password']]):
            logger.warning("Email configuration not set. Skipping notification.")
            return
        
        msg = MIMEMultipart()
        msg['From'] = self.email_config['from_email']
        msg['To'] = self.email_config['to_email']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            logger.info("Notification email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def generate_pentest_report(self) -> str:
        """Generate a report of penetration testing schedule and history."""
        if not self.pentest_history:
            return "No penetration testing history available."
        
        report = ["Penetration Testing Schedule and History", "=" * 40 + "\n"]
        
        # Add schedule information
        report.append("Scheduled Tests:")
        for test_type, info in self.pentest_schedule.items():
            report.append(f"\n{test_type.capitalize()} Test:")
            report.append(f"  Description: {info['description']}")
            report.append(f"  Next Run: {info['next_run']}")
            report.append(f"  Last Run: {info['last_run'] or 'Never'}")
            report.append(f"  Duration: {info['duration']}")
            report.append(f"  Team: {info['assigned_team']}")
            report.append(f"  Priority: {info['priority']}")
        
        # Add history information
        report.append("\n\nRecent Test History:")
        for test in self.pentest_history[-5:]:  # Show last 5 tests
            report.append(f"\n{test['type'].capitalize()} Test:")
            report.append(f"  Scheduled: {test['scheduled_at']}")
            report.append(f"  Planned Start: {test['planned_start_date']}")
            report.append(f"  Status: {test['status']}")
            report.append(f"  Team: {test['assigned_team']}")
        
        return "\n".join(report)

def check_and_schedule_tests():
    """Check if it's time to schedule any penetration tests."""
    scheduler = PenetrationTestingScheduler()
    
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    
    # Check if it's time for quarterly test
    next_quarter = datetime.fromisoformat(scheduler.pentest_schedule['quarterly']['next_run'])
    if (next_quarter - today).days <= 14:  # Schedule 2 weeks in advance
        scheduler.schedule_penetration_test('quarterly')
        
        # Update next run date
        if next_quarter.month == 1:  # Q1
            next_quarter = datetime(next_quarter.year, 4, 1)
        elif next_quarter.month == 4:  # Q2
            next_quarter = datetime(next_quarter.year, 7, 1)
        elif next_quarter.month == 7:  # Q3
            next_quarter = datetime(next_quarter.year, 10, 1)
        else:  # Q4
            next_quarter = datetime(next_quarter.year + 1, 1, 1)
        
        scheduler.pentest_schedule['quarterly']['next_run'] = next_quarter.isoformat()
        scheduler.save_pentest_schedule()
    
    # Check if it's time for monthly test
    next_month = datetime.fromisoformat(scheduler.pentest_schedule['monthly']['next_run'])
    if (next_month - today).days <= 7:  # Schedule 1 week in advance
        scheduler.schedule_penetration_test('monthly')
        
        # Update next run date
        month = next_month.month
        year = next_month.year
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        scheduler.pentest_schedule['monthly']['next_run'] = next_month.isoformat()
        scheduler.save_pentest_schedule()
    
    # Check if it's time for bi-weekly test
    next_biweekly = datetime.fromisoformat(scheduler.pentest_schedule['bi-weekly']['next_run'])
    if (next_biweekly - today).days <= 3:  # Schedule 3 days in advance
        scheduler.schedule_penetration_test('bi-weekly')
        
        # Update next run date
        next_biweekly = next_biweekly + timedelta(days=14)
        scheduler.pentest_schedule['bi-weekly']['next_run'] = next_biweekly.isoformat()
        scheduler.save_pentest_schedule()

def main():
    """Main function to start the penetration testing scheduler."""
    # Initial setup
    scheduler = PenetrationTestingScheduler()
    
    # Schedule daily check
    schedule.every().day.at("09:00").do(check_and_schedule_tests)
    
    logger.info("Penetration testing scheduler started")
    
    # Run first check immediately
    check_and_schedule_tests()
    
    # Generate and display initial report
    print("\nPenetration Testing Schedule Report:")
    print(scheduler.generate_pentest_report())
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main() 