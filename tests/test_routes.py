import pytest
import json
from flask import session, g, url_for
from app import app

def test_index_shows_form(client):
    """Test that the index page shows the analysis form."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<form action="/analyze"' in response.data
    assert b'method="post"' in response.data
    assert b'csrf_token' in response.data

def test_analyze_requires_login(client):
    """Test that the analyze endpoint requires login."""
    response = client.post('/analyze', data={
        'platform': 'amazon',
        'product_id': 'B01LYCLS24'
    })
    # Should redirect to login
    assert response.status_code == 302
    assert '/auth/login' in response.headers.get('Location', '')

def test_analyze_with_auth(client, auth):
    """Test that an authenticated user can access the analyze endpoint."""
    auth.login()
    response = client.get('/analyze')
    assert response.status_code == 200
    assert b'Analyze a Product' in response.data

    # Test form submission
    response = client.post('/analyze', data={
        'platform': 'amazon',
        'product_id': 'B01LYCLS24'
    })
    # Should redirect to dashboard
    assert response.status_code == 302
    assert '/dashboard/' in response.headers.get('Location', '')

def test_filter_reviews(client, auth):
    """Test filtering reviews."""
    # First create a product with reviews
    auth.login()
    response = client.post('/analyze', data={
        'platform': 'amazon',
        'product_id': 'B01LYCLS24'
    })
    
    # Get product ID from redirect URL
    product_url = response.headers.get('Location', '')
    product_id = product_url.split('/')[-1]
    
    # Test filtering
    response = client.post(f'/filter/{product_id}', data={
        'min_rating': '4',
        'max_rating': '5',
        'sentiment': 'positive'
    })
    
    assert response.status_code == 200
    assert b'Filtered Reviews' in response.data
    assert b'Applied Filters' in response.data

def test_export_csv(client, auth):
    """Test CSV export."""
    # First create a product with reviews
    auth.login()
    response = client.post('/analyze', data={
        'platform': 'amazon',
        'product_id': 'B01LYCLS24'
    })
    
    # Get product ID from redirect URL
    product_url = response.headers.get('Location', '')
    product_id = product_url.split('/')[-1]
    
    # Test export
    response = client.get(f'/export/csv/{product_id}?include_sentiment=true&include_product_info=true')
    
    assert response.status_code == 200
    assert response.mimetype == 'text/csv'
    assert 'attachment' in response.headers.get('Content-Disposition', '')

def test_export_json(client, auth):
    """Test JSON export."""
    # First create a product with reviews
    auth.login()
    response = client.post('/analyze', data={
        'platform': 'amazon',
        'product_id': 'B01LYCLS24'
    })
    
    # Get product ID from redirect URL
    product_url = response.headers.get('Location', '')
    product_id = product_url.split('/')[-1]
    
    # Test export
    response = client.get(f'/export/json/{product_id}?include_sentiment=true&include_product_info=true')
    
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    assert 'attachment' in response.headers.get('Content-Disposition', '')

def test_auth_routes(client):
    """Test authentication routes with forms."""
    # Test login page
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'<form' in response.data
    assert b'method="post"' in response.data
    assert b'csrf_token' in response.data
    
    # Test login form submission
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpassword'
    })
    assert response.status_code == 302  # Redirect on success
    
    # Test registration page
    response = client.get('/auth/register')
    assert response.status_code == 200
    assert b'<form' in response.data
    assert b'method="post"' in response.data
    assert b'csrf_token' in response.data
    
    # Test registration form submission
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@example.com',
        'password': 'newpassword',
        'confirm_password': 'newpassword'
    })
    assert response.status_code == 302  # Redirect on success

def test_rate_limits(client):
    """Test that rate limits are applied."""
    # Attempt to login multiple times with incorrect password
    for i in range(15):  # Should hit the rate limit after 10 attempts
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        if i >= 10:
            # After 10 attempts, should be rate limited
            assert response.status_code == 429
            break
        else:
            assert response.status_code != 429
            
    # If we didn't break out of the loop, the test failed
    assert i >= 10, "Rate limit was not applied" 