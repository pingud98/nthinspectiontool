"""
Unit tests for authentication functionality.
"""
import pytest
from app import db
from app.models import User


def test_login_logout(client, test_user, app):
    """Test user login and logout."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
    
    # Test login page access
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data
    
    # Test login
    response = client.post('/auth/login', data={
        'username': user.username,
        'password': 'testpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Dashboard' in response.data  # Should redirect to dashboard
    
    # Test logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'Login' in response.data  # Should redirect to login page


def test_login_failure(client, test_user, app):
    """Test login with invalid credentials."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
    
    response = client.post('/auth/login', data={
        'username': user.username,
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_access_protected_route_without_login(client):
    """Test that protected routes redirect to login when not authenticated."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302  # Redirect
    assert '/auth/login' in response.location