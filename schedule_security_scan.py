#!/usr/bin/env python
import schedule
import time
import subprocess
import logging
import os
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('security_scan_scheduler.log')
    ]
)
logger = logging.getLogger(__name__)

class SecurityScanScheduler:
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME', ''),
            'password': os.getenv('SMTP_PASSWORD', ''),
            'from_email': os.getenv('FROM_EMAIL', ''),
            'to_email': os.getenv('TO_EMAIL', '')
        }

    def run_security_scan(self):
        """Run the security scanner and process results."""
        logger.info("Starting scheduled security scan...")
        
        try:
            # Run the security scanner
            result = subprocess.run(
                ['python', 'security_scanner.py'],
                capture_output=True,
                text=True
            )
            
            # Get the latest scan results file
            scan_files = [f for f in os.listdir('.') if f.startswith('security_scan_') and f.endswith('.json')]
            if not scan_files:
                logger.error("No scan results file found")
                return
            
            latest_scan = max(scan_files)
            with open(latest_scan, 'r') as f:
                scan_results = json.load(f)
            
            # Send email notification if there are issues
            if scan_results['risk_level'] != 'LOW':
                self.send_notification(scan_results)
            
            logger.info(f"Security scan completed. Risk Level: {scan_results['risk_level']}")
            
        except Exception as e:
            logger.error(f"Error running security scan: {e}")
            self.send_error_notification(str(e))

    def send_notification(self, scan_results):
        """Send email notification with scan results."""
        if not all([self.email_config['username'], self.email_config['password']]):
            logger.warning("Email configuration not set. Skipping notification.")
            return
        
        try:
            subject = f"Security Scan Alert - Risk Level: {scan_results['risk_level']}"
            
            # Create message body
            body = f"""
            Security Scan Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            Risk Level: {scan_results['risk_level']}
            Total Vulnerabilities: {scan_results['total_vulnerabilities']}
            Security Headers Score: {scan_results['security_headers']['score']}%
            
            Vulnerability Details:
            {json.dumps(scan_results['vulnerability_scan'], indent=2)}
            
            Missing Security Headers:
            {json.dumps(scan_results['security_headers']['missing_headers'], indent=2)}
            
            Please review the full scan results for more details.
            """
            
            self.send_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def send_error_notification(self, error_message):
        """Send notification about scan execution error."""
        subject = "Security Scan Error Alert"
        body = f"""
        Error occurred during security scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Error details:
        {error_message}
        
        Please check the security scan logs for more information.
        """
        
        self.send_email(subject, body)

    def send_email(self, subject, body):
        """Send email using configured SMTP settings."""
        if not all([self.email_config['username'], self.email_config['password']]):
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

def main():
    scheduler = SecurityScanScheduler()
    
    # Schedule daily scan
    schedule.every().day.at("00:00").do(scheduler.run_security_scan)
    
    # Schedule weekly full scan
    schedule.every().monday.at("02:00").do(scheduler.run_security_scan)
    
    logger.info("Security scan scheduler started")
    
    # Run first scan immediately
    scheduler.run_security_scan()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main() 