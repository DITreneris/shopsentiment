#!/usr/bin/env python
import subprocess
import json
import sys
import logging
from typing import List, Dict, Any
import pkg_resources
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dependency_update.log')
    ]
)
logger = logging.getLogger(__name__)

class DependencyUpdater:
    def __init__(self):
        self.requirements_file = 'requirements.txt'
        self.backup_file = 'requirements.backup.txt'
        self.current_deps = {}
        self.outdated_deps = {}
        
    def get_current_dependencies(self) -> Dict[str, str]:
        """Get current dependencies from requirements.txt."""
        try:
            with open(self.requirements_file, 'r') as f:
                requirements = f.readlines()
            
            deps = {}
            for req in requirements:
                req = req.strip()
                if req and not req.startswith('#'):
                    # Handle different requirement formats
                    if '==' in req:
                        name, version = req.split('==')
                        deps[name] = version
                    elif '>=' in req:
                        name, version = req.split('>=')
                        deps[name] = f">={version}"
                    else:
                        deps[req] = 'latest'
            
            return deps
        except FileNotFoundError:
            logger.error(f"Requirements file {self.requirements_file} not found")
            return {}

    def get_outdated_packages(self) -> List[Dict[str, str]]:
        """Get list of outdated packages."""
        try:
            result = subprocess.run(
                ['pip', 'list', '--outdated', '--format=json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            return []
            
        except Exception as e:
            logger.error(f"Error checking outdated packages: {e}")
            return []

    def backup_requirements(self):
        """Create a backup of the current requirements file."""
        try:
            with open(self.requirements_file, 'r') as src, open(self.backup_file, 'w') as dst:
                dst.write(src.read())
            logger.info(f"Created backup of requirements file: {self.backup_file}")
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise

    def update_requirements(self, outdated: List[Dict[str, str]]):
        """Update requirements.txt with new versions."""
        try:
            current_deps = self.get_current_dependencies()
            
            # Create updated requirements content
            new_requirements = []
            with open(self.requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        new_requirements.append(line)
                        continue
                    
                    # Extract package name
                    package_name = line.split('==')[0].split('>=')[0].strip()
                    
                    # Find if package is in outdated list
                    update_info = next(
                        (pkg for pkg in outdated if pkg['name'] == package_name),
                        None
                    )
                    
                    if update_info:
                        # Preserve version constraint style (== or >=)
                        if '>=' in line:
                            new_requirements.append(f"{package_name}>={update_info['latest_version']}")
                        else:
                            new_requirements.append(f"{package_name}=={update_info['latest_version']}")
                        logger.info(f"Updating {package_name} to version {update_info['latest_version']}")
                    else:
                        new_requirements.append(line)
            
            # Write updated requirements
            with open(self.requirements_file, 'w') as f:
                f.write('\n'.join(new_requirements) + '\n')
            
            logger.info("Requirements file updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating requirements: {e}")
            raise

    def verify_updates(self) -> bool:
        """Verify that updates haven't broken dependencies."""
        try:
            result = subprocess.run(
                ['pip', 'check'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error("Dependency conflicts found after update")
                logger.error(result.stdout)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying updates: {e}")
            return False

    def rollback_updates(self):
        """Rollback to backup requirements file if verification fails."""
        try:
            with open(self.backup_file, 'r') as src, open(self.requirements_file, 'w') as dst:
                dst.write(src.read())
            logger.info("Successfully rolled back to previous requirements")
        except Exception as e:
            logger.error(f"Error rolling back updates: {e}")
            raise

    def run_update(self):
        """Run the complete update process."""
        try:
            # Get outdated packages
            outdated = self.get_outdated_packages()
            if not outdated:
                logger.info("No outdated packages found")
                return True
            
            logger.info(f"Found {len(outdated)} outdated packages")
            
            # Create backup
            self.backup_requirements()
            
            # Update requirements file
            self.update_requirements(outdated)
            
            # Verify updates
            if not self.verify_updates():
                logger.warning("Update verification failed, rolling back changes")
                self.rollback_updates()
                return False
            
            logger.info("Successfully updated all dependencies")
            return True
            
        except Exception as e:
            logger.error(f"Error during update process: {e}")
            return False

def main():
    updater = DependencyUpdater()
    success = updater.run_update()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 