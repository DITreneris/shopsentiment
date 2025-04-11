#!/usr/bin/env python
import subprocess
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('critical_updates.log')
    ]
)
logger = logging.getLogger(__name__)

# Critical security-related packages to update
CRITICAL_PACKAGES = [
    'urllib3',
    'cryptography',
    'requests',
    'flask',
    'werkzeug',
    'pymongo',
    'dnspython',
    'pycryptodome',
    'pyOpenSSL',
    'Django>=3.2.21,<4.0'  # Django 3.2.x LTS is compatible with Python 3.7 and has security fixes
]

def update_package(package_name):
    """Update a single package to its latest version."""
    try:
        logger.info(f"Updating {package_name}...")
        result = subprocess.run(
            ['pip', 'install', '--upgrade', package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully updated {package_name}")
            return True
        else:
            logger.error(f"Failed to update {package_name}: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating {package_name}: {e}")
        return False

def verify_package(package_name):
    """Verify that a package is installed and working."""
    try:
        # Extract the base package name without version specifiers
        base_package_name = package_name.split('>=')[0].split('==')[0].split('<')[0].strip()
        
        result = subprocess.run(
            ['pip', 'show', base_package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"Package {base_package_name} verified successfully")
            return True
        else:
            logger.error(f"Package {base_package_name} verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying {package_name}: {e}")
        return False

def main():
    success_count = 0
    failure_count = 0
    
    logger.info("Starting critical security package updates...")
    
    for package in CRITICAL_PACKAGES:
        if update_package(package) and verify_package(package):
            success_count += 1
        else:
            failure_count += 1
    
    logger.info(f"Update complete. Successful updates: {success_count}, Failed updates: {failure_count}")
    
    # Update requirements.txt with new versions
    try:
        # Use a more reliable method to update requirements.txt
        result = subprocess.run(
            ['pip', 'freeze'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            with open('requirements.txt', 'w') as f:
                f.write(result.stdout)
            logger.info("Updated requirements.txt with new package versions")
        else:
            logger.error("Failed to generate requirements.txt")
    except Exception as e:
        logger.error(f"Failed to update requirements.txt: {e}")
    
    return 0 if failure_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main()) 