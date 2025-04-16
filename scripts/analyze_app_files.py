#!/usr/bin/env python3
"""
Migration script to help transition from old application files to the new structure.
This script scans old app files for routes and functionality that might need to be migrated.
"""
import os
import re
import sys
from collections import defaultdict

# Files to analyze
APP_FILES = ['app.py', 'simple.py', 'simple_app.py', 'minimal.py']

def extract_routes(content):
    """Extract route definitions from file content."""
    # Look for both app.route and blueprint route patterns
    route_patterns = [
        r'@app\.route\([\'"](.+?)[\'"](.*?)\)',
        r'@\w+_bp\.route\([\'"](.+?)[\'"](.*?)\)'
    ]
    
    routes = []
    for pattern in route_patterns:
        routes.extend(re.findall(pattern, content, re.DOTALL))
    
    return routes

def extract_functions(content):
    """Extract function definitions from file content."""
    func_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    return re.findall(func_pattern, content)

def main():
    routes_by_file = defaultdict(list)
    functions_by_file = defaultdict(list)
    
    print("Analyzing application files for migration...")
    
    # Filter to only existing files
    existing_files = [f for f in APP_FILES if os.path.exists(f)]
    if not existing_files:
        print("No application files found!")
        return
    
    for file in existing_files:
        with open(file, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
            except UnicodeDecodeError:
                print(f"Error reading {file}: UnicodeDecodeError. Skipping...")
                continue
            
        routes = extract_routes(content)
        functions = extract_functions(content)
        
        routes_by_file[file] = routes
        functions_by_file[file] = functions
        
        print(f"\nAnalyzing {file}:")
        print(f"  Found {len(routes)} routes:")
        for route_info in routes:
            route_path = route_info[0]
            route_methods = route_info[1] if route_info[1].strip() else "GET (default)"
            print(f"    - {route_path} {route_methods}")
        
        print(f"  Found {len(functions)} functions:")
        for func in functions:
            print(f"    - {func}()")
        
    # Find duplicate routes
    all_routes = []
    for file, routes in routes_by_file.items():
        for route in routes:
            all_routes.append((route[0], file))
    
    route_paths = [r[0] for r in all_routes]
    duplicates = set([r for r in route_paths if route_paths.count(r) > 1])
    
    if duplicates:
        print("\nWarning! Duplicate routes found:")
        for route in duplicates:
            files = [f for r, f in all_routes if r == route]
            print(f"  Route '{route}' is defined in: {', '.join(files)}")
    
    # Generate migration plan
    print("\nMigration plan:")
    print("1. Keep the new src/__init__.py application factory as the primary entry point")
    print("2. For each route, ensure it exists in the new structure in src/api/v1/")
    print("3. Check for unique functionality in each file not covered by routes")
    print("4. After migration is complete, remove old application files")
    
    # Export routes and functions to a file for reference
    with open('migration_reference.txt', 'w') as f:
        f.write("Migration Reference\n")
        f.write("=================\n\n")
        
        for file in existing_files:
            if file not in routes_by_file:
                continue
                
            f.write(f"File: {file}\n")
            f.write("-" * (len(file) + 6) + "\n\n")
            
            f.write("Routes:\n")
            for route_info in routes_by_file[file]:
                route_path = route_info[0]
                route_methods = route_info[1] if route_info[1].strip() else "GET (default)"
                f.write(f"  - {route_path} {route_methods}\n")
            
            f.write("\nFunctions:\n")
            for func in functions_by_file[file]:
                f.write(f"  - {func}()\n")
            
            f.write("\n\n")
    
    print("\nMigration reference exported to migration_reference.txt")

if __name__ == "__main__":
    main() 