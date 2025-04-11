#!/usr/bin/env python3
"""
Python 3.10 Migration Script for ShopSentiment

This script performs several actions to assist with migrating from Python 3.7 to Python 3.10:
1. Creates a new virtual environment with Python 3.10
2. Installs dependencies from requirements-py310.txt
3. Runs compatibility checks
4. Updates type hints to use the new syntax
5. Runs tests to ensure everything works correctly

Usage:
    python migrate_to_python310.py [--check-only]
    
Options:
    --check-only: Only check for compatibility issues without making changes
"""

import os
import sys
import re
import subprocess
import shutil
import argparse
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('python310_migration.log')
    ]
)

logger = logging.getLogger('py310_migration')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Migrate ShopSentiment to Python 3.10')
    parser.add_argument('--check-only', action='store_true', help='Only check for compatibility issues without making changes')
    parser.add_argument('--venv-path', default='.venv310', help='Path to create the Python 3.10 virtual environment')
    return parser.parse_args()

def check_python_version():
    """Check if Python 3.10+ is available on the system."""
    try:
        # Try to find Python 3.10 or higher
        result = subprocess.run(['python3.10', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"Found Python 3.10: {result.stdout.strip()}")
            return 'python3.10'
    except FileNotFoundError:
        pass
    
    try:
        # Check if the default python command is Python 3.10+
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_match = re.search(r'Python (\d+\.\d+\.\d+)', result.stdout)
            if version_match:
                version = version_match.group(1)
                major, minor, _ = map(int, version.split('.'))
                if major == 3 and minor >= 10:
                    logger.info(f"Found Python {version}")
                    return 'python'
    except FileNotFoundError:
        pass
    
    logger.error("Python 3.10 or higher is required for this migration.")
    return None

def create_virtual_environment(python_cmd, venv_path):
    """Create a new virtual environment with Python 3.10."""
    logger.info(f"Creating virtual environment at {venv_path} using {python_cmd}")
    
    try:
        subprocess.run([python_cmd, '-m', 'venv', venv_path], check=True)
        logger.info(f"Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create virtual environment: {e}")
        return False

def install_dependencies(venv_path):
    """Install dependencies from requirements-py310.txt."""
    if sys.platform == 'win32':
        pip_path = os.path.join(venv_path, 'Scripts', 'pip')
    else:
        pip_path = os.path.join(venv_path, 'bin', 'pip')
    
    logger.info("Installing dependencies from requirements-py310.txt")
    
    try:
        subprocess.run([pip_path, 'install', '-r', 'requirements-py310.txt'], check=True)
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def update_type_hints(file_path):
    """Update type hints in a Python file to use the new Python 3.10 syntax."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match type hints using Union
    union_pattern = r'Union\[([\w\s,\.]+?)\]'
    # Pattern to match type hints using Optional
    optional_pattern = r'Optional\[([\w\s,\.]+?)\]'
    
    # Replace Union[X, Y] with X | Y
    def union_replacement(match):
        types = [t.strip() for t in match.group(1).split(',')]
        return ' | '.join(types)
    
    # Replace Optional[X] with X | None
    def optional_replacement(match):
        return f"{match.group(1)} | None"
    
    # Apply replacements
    content = re.sub(union_pattern, union_replacement, content)
    content = re.sub(optional_pattern, optional_replacement, content)
    
    # Write back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return file_path

def find_python_files(root_dir='.'):
    """Find all Python files in the project."""
    python_files = []
    for root, _, files in os.walk(root_dir):
        if '.venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def update_all_type_hints():
    """Update type hints in all Python files to use the new Python 3.10 syntax."""
    logger.info("Updating type hints to use Python 3.10 syntax")
    
    python_files = find_python_files()
    updated_files = []
    
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_file = {executor.submit(update_type_hints, file): file for file in python_files}
        for future in future_to_file:
            try:
                file = future.result()
                updated_files.append(file)
            except Exception as e:
                logger.error(f"Error updating {future_to_file[future]}: {e}")
    
    logger.info(f"Updated type hints in {len(updated_files)} files")
    return updated_files

def run_tests(venv_path):
    """Run tests to ensure everything works correctly with Python 3.10."""
    if sys.platform == 'win32':
        python_path = os.path.join(venv_path, 'Scripts', 'python')
    else:
        python_path = os.path.join(venv_path, 'bin', 'python')
    
    logger.info("Running tests with Python 3.10")
    
    try:
        subprocess.run([python_path, '-m', 'pytest'], check=True)
        logger.info("All tests passed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Tests failed: {e}")
        return False

def check_compatibility():
    """Run compatibility checks for Python 3.10."""
    logger.info("Running compatibility checks for Python 3.10")
    
    # Use the existing compatibility checker script
    try:
        result = subprocess.run(['python', 'scripts/upgrade_python.py', '--format', 'text'], 
                                capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Compatibility check completed")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Compatibility check failed: {result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run compatibility check: {e}")
        return False

def main():
    """Main function to orchestrate the migration process."""
    args = parse_arguments()
    
    logger.info("Starting Python 3.10 migration process")
    
    # Check if Python 3.10 is available
    python_cmd = check_python_version()
    if not python_cmd:
        logger.error("Migration aborted: Python 3.10 or higher is required")
        return False
    
    # Run compatibility checks
    if not check_compatibility():
        logger.warning("Compatibility issues detected. Please review the log file.")
        if args.check_only:
            return False
    elif args.check_only:
        logger.info("Check-only mode: Compatibility check completed")
        return True
    
    # Create virtual environment
    if not create_virtual_environment(python_cmd, args.venv_path):
        logger.error("Migration aborted: Failed to create virtual environment")
        return False
    
    # Install dependencies
    if not install_dependencies(args.venv_path):
        logger.error("Migration aborted: Failed to install dependencies")
        return False
    
    # Update type hints
    updated_files = update_all_type_hints()
    if not updated_files:
        logger.warning("No files were updated for type hints")
    
    # Run tests
    if not run_tests(args.venv_path):
        logger.warning("Some tests failed with Python 3.10. Manual intervention may be required.")
    
    logger.info(f"""
Migration to Python 3.10 completed. Next steps:

1. Review the log file 'python310_migration.log' for any warnings or errors
2. Activate the new virtual environment:
   - On Windows: {args.venv_path}\\Scripts\\activate
   - On Unix/Mac: source {args.venv_path}/bin/activate
3. Run the application with Python 3.10
4. Update your deployment scripts to use Python 3.10

If you encounter any issues, refer to the documentation or revert back to Python 3.7.
    """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 