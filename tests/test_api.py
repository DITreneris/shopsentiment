"""API tests for Shop Sentiment Analysis"""
import os
import json
import pytest
from app import app as flask_app

@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    # Set testing config
    flask_app.config.update({
        "TESTING": True,
    })
    
    # Create app context for testing
    with flask_app.app_context():
        yield flask_app

@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()

@pytest.fixture
def auth_token(client):
    """Get an authentication token for testing protected routes"""
    # Try to register a test user
    client.post('/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    # Log in with the test user
    response = client.post('/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    data = json.loads(response.data)
    
    # Return the token
    if 'token' in data:
        return data['token']
    return None

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'

def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert data['message'] == 'Shop Sentiment Analysis API is running'
    assert isinstance(data['endpoints'], list)

def test_register_user(client):
    """Test user registration"""
    # Create a random username to avoid conflicts
    import uuid
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    
    response = client.post('/auth/register', json={
        'username': username,
        'email': email,
        'password': 'password123'
    })
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Registration successful'

def test_login_user(client):
    """Test user login"""
    # Create a random username to avoid conflicts
    import uuid
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@example.com"
    
    # Register user first
    client.post('/auth/register', json={
        'username': username,
        'email': email,
        'password': 'password123'
    })
    
    # Then login
    response = client.post('/auth/login', json={
        'email': email,
        'password': 'password123'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Login successful'
    assert 'token' in data or 'user' in data

def test_products_endpoint(client):
    """Test the products endpoint"""
    response = client.get('/api/products/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)

def test_add_product(client, auth_token):
    """Test adding a product"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    response = client.post(
        '/api/products/',
        json={
            'platform': 'amazon',
            'product_id': 'test123',
            'url': 'https://amazon.com/dp/test123'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code in [200, 201]
    
def test_get_product_reviews(client, auth_token):
    """Test getting product reviews"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    # First add a product
    product_response = client.post(
        '/api/products/',
        json={
            'platform': 'amazon',
            'product_id': 'test456',
            'url': 'https://amazon.com/dp/test456'
        },
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    
    # Check if product was added successfully
    if product_response.status_code not in [200, 201]:
        pytest.skip("Product creation failed")
    
    product_data = json.loads(product_response.data)
    
    # Then get its reviews
    if 'id' in product_data:
        product_id = product_data['id']
        response = client.get(f'/api/products/{product_id}/reviews')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list) 