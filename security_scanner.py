#!/usr/bin/env python
import subprocess
import json
import sys
import os
from datetime import datetime
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('security_scan.log')
    ]
)
logger = logging.getLogger(__name__)

class SecurityScanner:
    def __init__(self):
        self.scan_results = {
            'timestamp': datetime.now().isoformat(),
            'vulnerability_scan': None,
            'dependency_check': None,
            'security_headers': None,
            'total_vulnerabilities': 0,
            'risk_level': 'LOW'
        }
    
    def run_safety_check(self) -> Dict[str, Any]:
        """Run safety check on Python dependencies."""
        try:
            logger.info("Running safety check on dependencies...")
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True
            )
            
            try:
                output = json.loads(result.stdout)
                if isinstance(output, list):
                    count = len(output)
                    logger.warning(f"Found {count} vulnerabilities in dependencies")
                    return {'vulnerabilities': output, 'count': count}
                else:
                    logger.info("No known vulnerabilities found in dependencies")
                    return {'vulnerabilities': [], 'count': 0}
            except json.JSONDecodeError:
                # If JSON parsing fails, check if it's because there are no vulnerabilities
                if "No known security vulnerabilities found" in result.stdout:
                    logger.info("No known vulnerabilities found in dependencies")
                    return {'vulnerabilities': [], 'count': 0}
                else:
                    logger.error(f"Error parsing safety check output: {result.stdout}")
                    return {'error': 'Failed to parse safety check output', 'count': 0}
            
        except Exception as e:
            logger.error(f"Error running safety check: {e}")
            return {'error': str(e), 'count': 0}

    def check_security_headers(self) -> Dict[str, Any]:
        """Check security headers in Flask application."""
        headers_to_check = {
            'Content-Security-Policy': False,
            'X-Frame-Options': False,
            'X-Content-Type-Options': False,
            'X-XSS-Protection': False,
            'Strict-Transport-Security': False,
            'Referrer-Policy': False,
            'Cross-Origin-Opener-Policy': False,
            'Cross-Origin-Embedder-Policy': False,
            'Cross-Origin-Resource-Policy': False,
            'X-Permitted-Cross-Domain-Policies': False
        }
        
        try:
            with open('app/__init__.py', 'r') as f:
                content = f.read()
            
            # Check Talisman configuration
            if 'talisman = Talisman(' in content:
                headers_to_check['Content-Security-Policy'] = 'content_security_policy=csp' in content
                headers_to_check['X-Frame-Options'] = 'frame_options=' in content
                headers_to_check['X-Content-Type-Options'] = 'x_content_type_options=' in content
                headers_to_check['X-XSS-Protection'] = 'x_xss_protection=' in content
                headers_to_check['Strict-Transport-Security'] = 'strict_transport_security=' in content
                headers_to_check['Referrer-Policy'] = 'referrer_policy=' in content
            
            # Check additional headers in after_request
            if '@app.after_request' in content:
                headers_to_check['Cross-Origin-Opener-Policy'] = 'Cross-Origin-Opener-Policy' in content
                headers_to_check['Cross-Origin-Embedder-Policy'] = 'Cross-Origin-Embedder-Policy' in content
                headers_to_check['Cross-Origin-Resource-Policy'] = 'Cross-Origin-Resource-Policy' in content
                headers_to_check['X-Permitted-Cross-Domain-Policies'] = 'X-Permitted-Cross-Domain-Policies' in content
            
            missing_headers = [h for h, present in headers_to_check.items() if not present]
            score = (sum(headers_to_check.values()) / len(headers_to_check)) * 100
            
            return {
                'checked_headers': headers_to_check,
                'missing_headers': missing_headers,
                'score': score,
                'details': {
                    'talisman_configured': 'talisman = Talisman(' in content,
                    'after_request_configured': '@app.after_request' in content
                }
            }
            
        except Exception as e:
            logger.error(f"Error checking security headers: {e}")
            return {'error': str(e)}

    def check_dependencies(self) -> Dict[str, Any]:
        """Check for outdated dependencies."""
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                outdated = json.loads(result.stdout)
                return {
                    'outdated_packages': outdated,
                    'count': len(outdated)
                }
            return {'error': 'Failed to check dependencies', 'count': 0}
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return {'error': str(e), 'count': 0}

    def calculate_risk_level(self) -> str:
        """Calculate overall risk level based on scan results."""
        vulnerability_count = self.scan_results['vulnerability_scan']['count']
        header_score = self.scan_results['security_headers']['score']
        
        if vulnerability_count > 5 or header_score < 50:
            return 'HIGH'
        elif vulnerability_count > 0 or header_score < 80:
            return 'MEDIUM'
        return 'LOW'

    def run_full_scan(self) -> Dict[str, Any]:
        """Run all security checks and return results."""
        logger.info("Starting full security scan...")
        
        # Run vulnerability scan
        self.scan_results['vulnerability_scan'] = self.run_safety_check()
        
        # Check security headers
        self.scan_results['security_headers'] = self.check_security_headers()
        
        # Check dependencies
        self.scan_results['dependency_check'] = self.check_dependencies()
        
        # Calculate total vulnerabilities
        self.scan_results['total_vulnerabilities'] = (
            self.scan_results['vulnerability_scan']['count']
        )
        
        # Calculate risk level
        self.scan_results['risk_level'] = self.calculate_risk_level()
        
        # Save results to file
        self.save_results()
        
        logger.info(f"Scan completed. Risk Level: {self.scan_results['risk_level']}")
        return self.scan_results

    def save_results(self) -> None:
        """Save scan results to a JSON file."""
        filename = f"security_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w') as f:
                json.dump(self.scan_results, f, indent=2)
            logger.info(f"Scan results saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving scan results: {e}")

def main():
    scanner = SecurityScanner()
    results = scanner.run_full_scan()
    
    # Print summary to console
    print("\n=== Security Scan Summary ===")
    print(f"Risk Level: {results['risk_level']}")
    print(f"Total Vulnerabilities: {results['total_vulnerabilities']}")
    print(f"Security Headers Score: {results['security_headers']['score']}%")
    print("\nDetailed results have been saved to a JSON file.")
    
    # Exit with status code based on risk level
    if results['risk_level'] == 'HIGH':
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main() 