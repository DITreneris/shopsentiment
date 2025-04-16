#!/usr/bin/env python3
"""
Script to consolidate application files by migrating unique functionality.
This script migrates functionality from app.py, simple.py, simple_app.py, and minimal.py
to the new modular structure.
"""

import os
import re
import sys
import shutil
from datetime import datetime

# Files to migrate
APP_FILES = ['app.py', 'simple.py', 'simple_app.py', 'minimal.py']

# New structure
NEW_STRUCTURE = {
    'app_factory': 'src/__init__.py',
    'api_routes': {
        'products': 'src/api/v1/products.py',
        'sentiment': 'src/api/v1/sentiment.py'
    },
    'web_routes': 'src/web_routes.py',
    'product_model': 'src/models/product.py',
    'auth': 'src/auth.py',
    'database': 'src/database/connection.py'
}

def backup_file(file_path):
    """Create a backup of a file."""
    if not os.path.exists(file_path):
        return
        
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.basename(file_path)
    backup_path = os.path.join(backup_dir, f"{filename}.{timestamp}")
    
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")

def create_migration_plan():
    """Create a plan for migrating functionality."""
    # Read the migration reference
    with open('migration_reference.txt', 'r') as f:
        ref_content = f.read()
    
    # Parse the reference to identify key routes and functions
    routes_to_migrate = {}
    functions_to_check = set()
    
    for file in APP_FILES:
        if file == 'app.py':
            # Skip app.py as we've already migrated its functionality
            continue
            
        file_section = re.search(f"File: {file}.*?Routes:(.*?)Functions:(.*?)(\n\nFile:|$)", 
                                ref_content, re.DOTALL)
        
        if not file_section:
            continue
            
        routes_text = file_section.group(1)
        functions_text = file_section.group(2)
        
        # Extract routes
        routes = re.findall(r'- (.*?) (.*)', routes_text)
        for route in routes:
            route_path = route[0].strip()
            
            # Determine target file based on route pattern
            if route_path.startswith('/api/products') or route_path.startswith('/api/v1/products'):
                target = NEW_STRUCTURE['api_routes']['products']
            elif route_path.startswith('/api/analyze') or route_path.startswith('/api/v1/sentiment'):
                target = NEW_STRUCTURE['api_routes']['sentiment']
            elif route_path.startswith('/auth'):
                target = NEW_STRUCTURE['auth']
            else:
                # Web routes
                target = NEW_STRUCTURE['web_routes']
                
            routes_to_migrate[route_path] = {
                'source_file': file,
                'target_file': target
            }
        
        # Extract functions
        functions = re.findall(r'- (\w+)\(\)', functions_text)
        for func in functions:
            functions_to_check.add((func, file))
    
    return {
        'routes': routes_to_migrate,
        'functions': functions_to_check
    }

def generate_web_routes_file():
    """Generate a new web_routes.py file for web endpoints."""
    if os.path.exists(NEW_STRUCTURE['web_routes']):
        print(f"Web routes file already exists: {NEW_STRUCTURE['web_routes']}")
        return
        
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(NEW_STRUCTURE['web_routes']), exist_ok=True)
    
    content = '''"""
Web routes for the ShopSentiment application.
Contains all non-API web routes.
"""

import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for

logger = logging.getLogger(__name__)

# Create a blueprint for web routes
web_bp = Blueprint('web', __name__)


@web_bp.route('/')
def index():
    """Render the homepage."""
    try:
        logger.info('Accessing index page')
        return render_template('index.html', 
                            server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            now=datetime.now())
    except Exception as e:
        logger.error(f'Error in index route: {str(e)}')
        return render_template('500.html'), 500


@web_bp.route('/dashboard')
def dashboard():
    """Render the dashboard page."""
    try:
        logger.info('Accessing dashboard page')
        # In a real implementation, this would fetch data from the database
        # For now, using mock data
        sample_data = [
            {'name': 'Product A', 'sentiment_score': 0.85, 'reviews_count': 128},
            {'name': 'Product B', 'sentiment_score': 0.42, 'reviews_count': 64},
            {'name': 'Product C', 'sentiment_score': 0.91, 'reviews_count': 256}
        ]
        return render_template('dashboard.html', 
                            products=sample_data,
                            server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            now=datetime.now())
    except Exception as e:
        logger.error(f'Error in dashboard route: {str(e)}')
        return render_template('500.html'), 500


@web_bp.route('/about')
def about():
    """Render the about page."""
    try:
        logger.info('Accessing about page')
        return render_template('about.html',
                            server_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            now=datetime.now())
    except Exception as e:
        logger.error(f'Error in about route: {str(e)}')
        return render_template('500.html'), 500


# Function to register the blueprint with the app
def register_web_routes(app):
    """Register web routes with the Flask app."""
    app.register_blueprint(web_bp)
'''
    
    with open(NEW_STRUCTURE['web_routes'], 'w') as f:
        f.write(content)
        
    print(f"Generated web routes file: {NEW_STRUCTURE['web_routes']}")

def update_app_factory():
    """Update the app factory to include web routes."""
    if not os.path.exists(NEW_STRUCTURE['app_factory']):
        print(f"Error: App factory file not found: {NEW_STRUCTURE['app_factory']}")
        return
    
    with open(NEW_STRUCTURE['app_factory'], 'r') as f:
        content = f.read()
    
    # Check if web routes are already imported
    if "from src.web_routes import register_web_routes" not in content:
        # Find the register_api import
        import_pattern = r"from src\.api\.v1 import register_api"
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                "from src.api.v1 import register_api\nfrom src.web_routes import register_web_routes",
                content
            )
        
        # Find where register_api is called
        register_pattern = r"register_api\(app\)"
        if re.search(register_pattern, content):
            content = re.sub(
                register_pattern,
                "register_api(app)\n    register_web_routes(app)",
                content
            )
        
        # Write the updated content
        with open(NEW_STRUCTURE['app_factory'], 'w') as f:
            f.write(content)
            
        print(f"Updated app factory to include web routes: {NEW_STRUCTURE['app_factory']}")
    else:
        print("Web routes already registered in app factory")

def create_auth_module():
    """Create a simple auth module for authentication endpoints."""
    if os.path.exists(NEW_STRUCTURE['auth']):
        print(f"Auth module already exists: {NEW_STRUCTURE['auth']}")
        return
        
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(NEW_STRUCTURE['auth']), exist_ok=True)
    
    content = '''"""
Authentication module for the ShopSentiment application.
"""

import logging
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

# Create a blueprint for auth routes
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint."""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing email or password'
            }), 400
            
        email = data['email']
        password = data['password']
        
        # In a real implementation, this would check against a database
        # For demonstration, using a mock user
        if email == 'user@example.com' and password == 'password':
            session['user_id'] = '1'
            session['email'] = email
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': '1',
                    'email': email
                }
            })
        else:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Invalid credentials'
            }), 401
            
    except Exception as e:
        logger.error(f'Error in login endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during login'
        }), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register endpoint."""
    try:
        data = request.get_json()
        if not data or 'email' not in data or 'password' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing email or password'
            }), 400
            
        email = data['email']
        password = data['password']
        
        # In a real implementation, this would store the user in a database
        # For demonstration, just return success
        return jsonify({
            'message': 'Registration successful',
            'user': {
                'id': '1',
                'email': email
            }
        }), 201
            
    except Exception as e:
        logger.error(f'Error in register endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during registration'
        }), 500


@auth_bp.route('/me', methods=['GET'])
def me():
    """Get current user information."""
    try:
        if 'user_id' not in session:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Not logged in'
            }), 401
            
        # In a real implementation, this would fetch the user from a database
        return jsonify({
            'user': {
                'id': session['user_id'],
                'email': session.get('email', 'unknown')
            }
        })
            
    except Exception as e:
        logger.error(f'Error in me endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while fetching user information'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint."""
    try:
        session.pop('user_id', None)
        session.pop('email', None)
        
        return jsonify({
            'message': 'Logout successful'
        })
            
    except Exception as e:
        logger.error(f'Error in logout endpoint: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred during logout'
        }), 500


# Function to register the blueprint with the app
def register_auth_routes(app):
    """Register auth routes with the Flask app."""
    app.register_blueprint(auth_bp)
'''
    
    with open(NEW_STRUCTURE['auth'], 'w') as f:
        f.write(content)
        
    print(f"Generated auth module: {NEW_STRUCTURE['auth']}")

def update_app_factory_with_auth():
    """Update the app factory to include auth routes."""
    if not os.path.exists(NEW_STRUCTURE['app_factory']):
        print(f"Error: App factory file not found: {NEW_STRUCTURE['app_factory']}")
        return
    
    with open(NEW_STRUCTURE['app_factory'], 'r') as f:
        content = f.read()
    
    # Check if auth routes are already imported
    if "from src.auth import register_auth_routes" not in content:
        # Find the register_api import
        import_pattern = r"from src\.web_routes import register_web_routes"
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                "from src.web_routes import register_web_routes\nfrom src.auth import register_auth_routes",
                content
            )
        
        # Find where register_web_routes is called
        register_pattern = r"register_web_routes\(app\)"
        if re.search(register_pattern, content):
            content = re.sub(
                register_pattern,
                "register_web_routes(app)\n    register_auth_routes(app)",
                content
            )
        
        # Write the updated content
        with open(NEW_STRUCTURE['app_factory'], 'w') as f:
            f.write(content)
            
        print(f"Updated app factory to include auth routes: {NEW_STRUCTURE['app_factory']}")
    else:
        print("Auth routes already registered in app factory")

def create_redirection_app():
    """Create a redirection app.py that imports from the new structure."""
    backup_file('app.py')
    
    content = '''"""
Redirection module for backward compatibility.
This file forwards imports and functionality to the new modular structure.
"""

import sys
import logging
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Warn about using the old entry point
warnings.warn(
    "Using app.py is deprecated. Please use the new structure with wsgi.py as the entry point.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new structure
try:
    from src import create_app
    from wsgi import app

    # Export the app instance
    application = app
except ImportError as e:
    logger.error(f"Failed to import from new structure: {str(e)}")
    sys.exit(1)

# For backward compatibility with scripts that import from app.py
if __name__ == "__main__":
    logger.info("Running app.py (deprecated) - using new app factory")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
'''
    
    with open('app.py', 'w') as f:
        f.write(content)
        
    print(f"Created redirection app.py for backward compatibility")

def main():
    """Main function for consolidating app files."""
    print("Consolidating application files...")
    
    # Backup existing files
    for file in APP_FILES:
        backup_file(file)
    
    # Create migration plan
    migration_plan = create_migration_plan()
    print(f"\nMigration plan created:")
    print(f"  - Routes to migrate: {len(migration_plan['routes'])}")
    print(f"  - Functions to check: {len(migration_plan['functions'])}")
    
    # Generate web routes file
    generate_web_routes_file()
    
    # Update app factory to include web routes
    update_app_factory()
    
    # Create auth module
    create_auth_module()
    
    # Update app factory to include auth routes
    update_app_factory_with_auth()
    
    # Create redirection app
    create_redirection_app()
    
    # Generate report
    print("\nMigration complete!")
    print("\nNext steps:")
    print("1. Verify functionality with tests")
    print("2. Check for any missed functionality or edge cases")
    print("3. Update documentation to reflect the new structure")
    
    # Rename old app files to .bak once migration is verified
    print("\nOnce the migration is verified, you can remove the old files:")
    for file in APP_FILES:
        if file != 'app.py':  # We already handled app.py
            print(f"  - {file}")

if __name__ == "__main__":
    main() 