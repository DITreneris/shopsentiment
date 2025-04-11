import pytest
import os
import tempfile
import json

from app import app as flask_app
from app import init_db

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # Create a testing configuration
    flask_app.config.update({
        'TESTING': True,
        'DATABASE': db_path,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SECRET_KEY': 'test-key',
        'SERVER_NAME': 'localhost.localdomain'
    })

    # Create the database and load test data
    with flask_app.app_context():
        init_db()
        
    # Create a temporary directory for user data
    users_dir = tempfile.mkdtemp()
    users_file = os.path.join(users_dir, 'users.json')
    with open(users_file, 'w') as f:
        json.dump([
            {
                'id': 1,
                'username': 'testuser',
                'email': 'test@example.com',
                'password_hash': 'pbkdf2:sha256:150000$IYt9r7SJ$8eb2b29b98f876e9a28edc57d82f79427f0b1686c2bed25f7c8b1e6c995a046e',  # password: 'testpassword'
                'created_at': '2023-01-01T00:00:00',
                'last_login': None
            }
        ], f)
    
    # Override the users file path
    flask_app.config['USERS_FILE'] = users_file

    yield flask_app

    # Close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)
    
    # Clean up the temporary users file
    os.unlink(users_file)
    os.rmdir(users_dir)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

# Fixtures for authenticated sessions
@pytest.fixture
def auth(client):
    """Authentication helper fixture."""
    class AuthActions:
        def __init__(self, client):
            self._client = client

        def login(self, email='test@example.com', password='testpassword'):
            return self._client.post(
                '/auth/login',
                data={'email': email, 'password': password}
            )

        def logout(self):
            return self._client.get('/auth/logout')

    return AuthActions(client) 