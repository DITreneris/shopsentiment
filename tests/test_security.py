import pytest

def test_csrf_protection(client):
    """Test that CSRF protection is enabled."""
    # Try to post to a form endpoint without CSRF token
    response = client.post('/analyze', data={
        'platform': 'amazon',
        'product_id': 'B01LYCLS24'
    })
    # Should fail with a 400 Bad Request (CSRF validation error)
    assert response.status_code == 400

def test_security_headers(client):
    """Test that security headers are set."""
    response = client.get('/')
    
    # Check for Content-Security-Policy header
    assert 'Content-Security-Policy' in response.headers
    
    # Check for X-Frame-Options header
    assert 'X-Frame-Options' in response.headers
    assert response.headers['X-Frame-Options'] == 'DENY'
    
    # Check for X-Content-Type-Options header
    assert 'X-Content-Type-Options' in response.headers
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    
    # Check for X-XSS-Protection header (may be provided by Talisman)
    if 'X-XSS-Protection' in response.headers:
        assert response.headers['X-XSS-Protection'] == '1; mode=block'

def test_csrf_token_in_forms(client):
    """Test that CSRF tokens are included in all forms."""
    # Check login form
    response = client.get('/auth/login')
    assert b'<input id="csrf_token" name="csrf_token"' in response.data
    
    # Check registration form
    response = client.get('/auth/register')
    assert b'<input id="csrf_token" name="csrf_token"' in response.data
    
    # Check analyze form
    response = client.get('/analyze')
    assert b'<input id="csrf_token" name="csrf_token"' in response.data
    
    # Check main page form
    response = client.get('/')
    assert b'<input id="csrf_token" name="csrf_token"' in response.data

def test_no_csrf_on_get(client):
    """Test that GET requests without CSRF tokens still work."""
    response = client.get('/')
    assert response.status_code == 200
    
    response = client.get('/auth/login')
    assert response.status_code == 200
    
    response = client.get('/auth/register')
    assert response.status_code == 200 