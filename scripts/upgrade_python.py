#!/usr/bin/env python
"""
Python 3.10 Upgrade Helper
Scans the codebase for Python 3.7 deprecation warnings and patterns
that might need to be updated for Python 3.10+ compatibility
"""

import os
import sys
import re
import ast
import logging
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('python_upgrade_report.log')
    ]
)
logger = logging.getLogger(__name__)

# Patterns to look for in Python files
PATTERNS = [
    {
        'name': 'from collections import abc import',
        'pattern': r'from\s+collections\s+import\s+(\w+(?:\s*,\s*\w+)*)',
        'description': 'Collection ABCs moved from collections to collections.abc in Python 3.10',
        'suggestion': 'Change to "from collections.abc import ..."',
        'collections_abc': ['Mapping', 'MutableMapping', 'Sequence', 'MutableSequence', 
                           'Set', 'MutableSet', 'Container', 'Iterable', 'Iterator', 
                           'Hashable', 'Sized', 'Callable', 'Collection']
    },
    {
        'name': 'distutils usage',
        'pattern': r'(?:from|import)\s+distutils',
        'description': 'distutils is deprecated in Python 3.10, removed in Python 3.12',
        'suggestion': 'Use setuptools instead or packaging if appropriate'
    },
    {
        'name': 'Abstract Base Classes',
        'pattern': r'(?:from|import)\s+abc',
        'description': 'Abstract Base Classes API changes in Python 3.10',
        'suggestion': 'Check @abstractproperty usage, it was removed in 3.8, use @property @abstractmethod instead'
    },
    {
        'name': 'typing Union',
        'pattern': r'from\s+typing\s+import.*Union',
        'description': 'Union types can use X | Y syntax in Python 3.10+',
        'suggestion': 'Consider using X | Y syntax instead of Union[X, Y]'
    },
    {
        'name': 'typing Optional',
        'pattern': r'from\s+typing\s+import.*Optional',
        'description': 'Optional[X] can use X | None syntax in Python 3.10+',
        'suggestion': 'Consider using X | None syntax instead of Optional[X]'
    },
    {
        'name': 'legacy string formatting',
        'pattern': r'%[sdiouxXeEfFgGcrs]',
        'description': 'Legacy % string formatting found',
        'suggestion': 'Use f-strings or str.format() instead'
    },
    {
        'name': 'imp module usage',
        'pattern': r'(?:from|import)\s+imp\b',
        'description': 'imp module is deprecated and was removed in Python 3.12',
        'suggestion': 'Use importlib instead'
    },
    {
        'name': 'parser module usage',
        'pattern': r'(?:from|import)\s+parser\b',
        'description': 'parser module is deprecated and was removed in Python 3.10',
        'suggestion': 'Use ast module instead'
    },
    {
        'name': 'asyncio.coroutine usage',
        'pattern': r'asyncio\.coroutine',
        'description': 'asyncio.coroutine() is deprecated in Python 3.8+',
        'suggestion': 'Use async/await syntax instead'
    },
    {
        'name': 'use of assert',
        'pattern': r'\bassert\b',
        'description': 'Assert statements are used, might behave differently in 3.10+ debug vs. optimized mode',
        'suggestion': 'Ensure assertions are not being used for input validation'
    }
]

# Files and directories to exclude
EXCLUDE_PATTERNS = [
    r'\.git',
    r'\.pytest_cache',
    r'__pycache__',
    r'\.venv',
    r'venv',
    r'env',
    r'node_modules',
    r'\.eggs',
    r'\.tox',
    r'build',
    r'dist',
    r'migrations',
]

class CompatibilityIssue:
    """Represents a compatibility issue found in the code"""
    def __init__(self, file_path, line_num, line, pattern_name, description, suggestion):
        self.file_path = file_path
        self.line_num = line_num
        self.line = line.strip()
        self.pattern_name = pattern_name
        self.description = description
        self.suggestion = suggestion
    
    def __str__(self):
        return f"{self.file_path}:{self.line_num} - {self.pattern_name}\n  {self.line}\n  {self.description}\n  Suggestion: {self.suggestion}"

def find_python_files(base_dir, exclude_patterns=None):
    """Find all Python files in the directory recursively, respecting excludes"""
    if exclude_patterns is None:
        exclude_patterns = EXCLUDE_PATTERNS
    
    exclude_regex = re.compile('|'.join(exclude_patterns))
    python_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not exclude_regex.search(d)]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not exclude_regex.search(file_path):
                    python_files.append(file_path)
    
    return python_files

def check_file_for_patterns(file_path, patterns):
    """Check a file for all patterns"""
    issues = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for pattern_info in patterns:
                pattern = pattern_info['pattern']
                pattern_name = pattern_info['name']
                description = pattern_info['description']
                suggestion = pattern_info['suggestion']
                
                # Check for pattern in each line
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # Special handling for collections.abc imports
                        if pattern_name == 'from collections import abc import' and 'collections_abc' in pattern_info:
                            match = re.search(r'from\s+collections\s+import\s+(\w+(?:\s*,\s*\w+)*)', line)
                            if match:
                                imported_names = [name.strip() for name in match.group(1).split(',')]
                                for name in imported_names:
                                    if name in pattern_info['collections_abc']:
                                        issues.append(CompatibilityIssue(
                                            file_path, i+1, line, pattern_name, 
                                            f"'{name}' should be imported from collections.abc in Python 3.10+",
                                            f"Change to 'from collections.abc import {name}'"
                                        ))
                        else:
                            issues.append(CompatibilityIssue(
                                file_path, i+1, line, pattern_name, description, suggestion
                            ))
            
            # Use AST to check for more complex patterns
            try:
                tree = ast.parse(content)
                ast_checker = AstPatternChecker(file_path, lines)
                ast.walk(tree)
                issues.extend(ast_checker.issues)
            except SyntaxError as e:
                logger.warning(f"Syntax error in {file_path}: {e}")
            
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")
    
    return issues

class AstPatternChecker(ast.NodeVisitor):
    """AST visitor to check for more complex patterns"""
    def __init__(self, file_path, lines):
        self.file_path = file_path
        self.lines = lines
        self.issues = []
    
    def visit_Try(self, node):
        """Check for bare except clauses which capture BaseException"""
        for handler in node.handlers:
            if handler.type is None:
                line_num = handler.lineno
                line = self.lines[line_num-1]
                self.issues.append(CompatibilityIssue(
                    self.file_path, line_num, line,
                    'bare except clause',
                    'Bare except clauses catch BaseException, including KeyboardInterrupt and SystemExit',
                    'Use "except Exception:" to only catch exceptions derived from Exception'
                ))
        self.generic_visit(node)
    
    def visit_TryExcept(self, node):
        """Check for bare except clauses in Python 3.7 AST"""
        for handler in node.handlers:
            if handler.type is None:
                line_num = handler.lineno
                line = self.lines[line_num-1]
                self.issues.append(CompatibilityIssue(
                    self.file_path, line_num, line,
                    'bare except clause',
                    'Bare except clauses catch BaseException, including KeyboardInterrupt and SystemExit',
                    'Use "except Exception:" to only catch exceptions derived from Exception'
                ))
        self.generic_visit(node)

def check_requirements_file(file_path):
    """Check requirements.txt for version constraints that might conflict with Python 3.10"""
    issues = []
    problem_packages = {
        'python-dateutil': ('< 2.8.0', 'Upgrade to 2.8.2 or later for Python 3.10 compatibility'),
        'werkzeug': ('< 2.0.0', 'Upgrade to 2.0.0 or later for Python 3.10 compatibility'),
        'flask': ('< 2.0.0', 'Upgrade to 2.0.0 or later for Python 3.10 compatibility'),
        'jinja2': ('< 3.0.0', 'Upgrade to 3.0.0 or later for Python 3.10 compatibility'),
        'itsdangerous': ('< 2.0.0', 'Upgrade to 2.0.0 or later for Python 3.10 compatibility'),
        'click': ('< 8.0.0', 'Upgrade to 8.0.0 or later for Python 3.10 compatibility'),
        'markupsafe': ('< 2.0.0', 'Upgrade to 2.0.0 or later for Python 3.10 compatibility'),
        'sqlalchemy': ('< 1.4.0', 'Upgrade to 1.4.0 or later for Python 3.10 compatibility'),
        'cryptography': ('< 3.4.0', 'Upgrade to 3.4.0 or later for Python 3.10 compatibility'),
        'numpy': ('< 1.21.0', 'Upgrade to 1.21.0 or later for Python 3.10 compatibility'),
        'pandas': ('< 1.3.0', 'Upgrade to 1.3.0 or later for Python 3.10 compatibility'),
        'pillow': ('< 9.0.0', 'Upgrade to 9.0.0 or later for Python 3.10 compatibility'),
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Check each problematic package
                for package, (version_constraint, suggestion) in problem_packages.items():
                    if line.lower().startswith(package.lower()):
                        # Check if version constraint is specified
                        match = re.search(r'[=<>~!]', line)
                        if match:
                            version_spec = line[match.start():]
                            issues.append(CompatibilityIssue(
                                file_path, i+1, line,
                                'problematic dependency version',
                                f"Package {package} with constraint {version_spec} might have issues with Python 3.10",
                                suggestion
                            ))
                        else:
                            # No version constraint, may be resolved at install time
                            issues.append(CompatibilityIssue(
                                file_path, i+1, line,
                                'dependency without version constraint',
                                f"Package {package} without version constraint might resolve to an incompatible version",
                                f"Consider pinning to a compatible version: {suggestion}"
                            ))
    except Exception as e:
        logger.error(f"Error checking requirements file {file_path}: {e}")
    
    return issues

def generate_report(issues, base_dir, output_format='text'):
    """Generate a report of compatibility issues"""
    if not issues:
        logger.info("No compatibility issues found.")
        return "No compatibility issues found."
    
    logger.info(f"Found {len(issues)} potential compatibility issues.")
    
    # Group issues by file
    issues_by_file = defaultdict(list)
    for issue in issues:
        issues_by_file[issue.file_path].append(issue)
    
    if output_format == 'text':
        report = ["Python 3.10+ Compatibility Report", "=" * 35, ""]
        report.append(f"Found {len(issues)} potential compatibility issues across {len(issues_by_file)} files.")
        report.append("")
        
        # Summary by issue type
        issue_types = defaultdict(int)
        for issue in issues:
            issue_types[issue.pattern_name] += 1
        
        report.append("Summary by issue type:")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {issue_type}: {count} occurrences")
        
        report.append("\nDetailed findings:")
        for file_path, file_issues in sorted(issues_by_file.items()):
            rel_path = os.path.relpath(file_path, base_dir)
            report.append(f"\n{rel_path}:")
            for issue in sorted(file_issues, key=lambda x: x.line_num):
                report.append(f"  Line {issue.line_num}: {issue.pattern_name}")
                report.append(f"    {issue.line}")
                report.append(f"    {issue.description}")
                report.append(f"    Suggestion: {issue.suggestion}")
        
        report.append("\nNext steps:")
        report.append("1. Review each issue and determine if changes are needed")
        report.append("2. Run unit tests after each change to ensure functionality is preserved")
        report.append("3. Update requirement versions to ensure compatibility with Python 3.10+")
        
        return "\n".join(report)
    
    elif output_format == 'markdown':
        report = ["# Python 3.10+ Compatibility Report", ""]
        report.append(f"Found **{len(issues)}** potential compatibility issues across **{len(issues_by_file)}** files.")
        report.append("")
        
        # Summary by issue type
        issue_types = defaultdict(int)
        for issue in issues:
            issue_types[issue.pattern_name] += 1
        
        report.append("## Summary by issue type")
        for issue_type, count in sorted(issue_types.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{issue_type}**: {count} occurrences")
        
        report.append("\n## Detailed findings")
        for file_path, file_issues in sorted(issues_by_file.items()):
            rel_path = os.path.relpath(file_path, base_dir)
            report.append(f"\n### {rel_path}")
            for issue in sorted(file_issues, key=lambda x: x.line_num):
                report.append(f"- **Line {issue.line_num}**: {issue.pattern_name}")
                report.append(f"  - Code: `{issue.line}`")
                report.append(f"  - Description: {issue.description}")
                report.append(f"  - Suggestion: {issue.suggestion}")
        
        report.append("\n## Next steps")
        report.append("1. Review each issue and determine if changes are needed")
        report.append("2. Run unit tests after each change to ensure functionality is preserved")
        report.append("3. Update requirement versions to ensure compatibility with Python 3.10+")
        
        return "\n".join(report)
    
    else:
        return "Unsupported output format"

def main():
    parser = argparse.ArgumentParser(description='Check Python code for 3.7 to 3.10 upgrade compatibility issues')
    parser.add_argument('--base-dir', type=str, default='.', help='Base directory to scan (default: current directory)')
    parser.add_argument('--output', type=str, default='python_310_compatibility_report.txt', help='Output report file')
    parser.add_argument('--format', type=str, choices=['text', 'markdown'], default='text', help='Output format')
    parser.add_argument('--max-workers', type=int, default=4, help='Maximum number of worker threads')
    
    args = parser.parse_args()
    
    logger.info(f"Scanning directory: {args.base_dir}")
    python_files = find_python_files(args.base_dir)
    logger.info(f"Found {len(python_files)} Python files to check")
    
    all_issues = []
    
    # Use ThreadPoolExecutor to parallelize file processing
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        file_results = list(executor.map(lambda file: check_file_for_patterns(file, PATTERNS), python_files))
        for issues in file_results:
            all_issues.extend(issues)
    
    # Check requirements files
    for path in ['requirements.txt', 'dev-requirements.txt', 'requirements-dev.txt']:
        req_path = os.path.join(args.base_dir, path)
        if os.path.exists(req_path):
            logger.info(f"Checking requirements file: {req_path}")
            requirements_issues = check_requirements_file(req_path)
            all_issues.extend(requirements_issues)
    
    # Generate and save report
    report = generate_report(all_issues, args.base_dir, args.format)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report written to {args.output}")
    print(f"Found {len(all_issues)} potential compatibility issues. See {args.output} for details.")

if __name__ == '__main__':
    main() 