#!/usr/bin/env python3
"""
Make all Python scripts executable in the shop-sentiment project.

This script:
1. Finds all Python scripts in the project
2. Adds the shebang line if missing
3. Makes the files executable

Usage:
    python scripts/make_scripts_executable.py
"""

import os
import stat
import sys
from pathlib import Path

# List of scripts that should be executable
EXECUTABLE_SCRIPTS = [
    "scripts/initialize_mongodb.py",
    "scripts/test_mongodb_connection.py",
    "scripts/add_sample_product.py",
    "scripts/list_mongodb_data.py",
    "scripts/check_mongodb.py",
    "scripts/run_load_test.py",
    "scripts/load_test_data_generator.py",
    "scripts/run_mongodb_performance_test.py", 
    "scripts/migrate_to_mongodb.py",
    "scripts/test_migration.py",
    "scripts/upgrade_python.py",
    "scripts/enable_dashboard.py",
    "scripts/migrate_to_python310.py"
]

# Shebang line to add at the top of script files
SHEBANG = "#!/usr/bin/env python3"

def make_executable(file_path):
    """
    Make a file executable by adding executable permission.
    
    Args:
        file_path: Path to the file
    """
    # Get current permissions
    current_permissions = os.stat(file_path).st_mode
    
    # Add executable permission for user, group, and others (similar to chmod +x)
    executable_permissions = current_permissions | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    
    # Set new permissions
    os.chmod(file_path, executable_permissions)
    
    print(f"Made executable: {file_path}")

def ensure_shebang(file_path):
    """
    Ensure the file has a proper shebang line at the top.
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if shebang was added, False if it already existed
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if the file already starts with the shebang
    if content.startswith(SHEBANG):
        return False
    
    # Add shebang at the top
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"{SHEBANG}\n{content}")
    
    return True

def process_script(script_path):
    """
    Process a script by ensuring it has a shebang and making it executable.
    
    Args:
        script_path: Path to the script
    """
    # Convert to absolute path
    abs_path = os.path.abspath(script_path)
    
    # Ensure the file exists
    if not os.path.isfile(abs_path):
        print(f"Warning: Script not found: {abs_path}")
        return
    
    # Add shebang if needed
    added_shebang = ensure_shebang(abs_path)
    if added_shebang:
        print(f"Added shebang to: {script_path}")
    
    # Make executable
    make_executable(abs_path)

def main():
    """Main function to process all scripts."""
    print("Making scripts executable...")
    
    # Get the project root directory
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle
        script_dir = os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Project root is the parent of the scripts directory
    project_root = os.path.abspath(os.path.join(script_dir, '..'))
    
    # Process each script
    for script_relative_path in EXECUTABLE_SCRIPTS:
        script_path = os.path.join(project_root, script_relative_path)
        process_script(script_path)
    
    print("\nAll scripts processed successfully!")
    print("\nYou can now run scripts directly on Unix/Linux/Mac:")
    for script in EXECUTABLE_SCRIPTS:
        print(f"  ./{script}")
    
    print("\nOn Windows, you still need to use:")
    for script in EXECUTABLE_SCRIPTS:
        print(f"  python {script}")

if __name__ == "__main__":
    main() 