"""
Unit tests for admin user management functionality.
"""
import pytest
from app import db
from app.models import User


def test_create_user(admin_client, app):
    """Test creating a new user via admin interface."""
    response = admin_client.post('/admin/user/create', data={
            'username': 'newuser',
            'full_name': 'New User',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'is_active': 'y',
            'submit': 'Save'
        }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'User created successfully' in response.data
    
    # Verify user was created
    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.full_name == 'New User'
        assert user.email == 'newuser@example.com'
        assert user.is_active == True
        assert user.is_admin == False


def test_create_user_duplicate_username(admin_client, app):
    """Test creating a user with duplicate username fails."""
    with app.app_context():
        # Create first user
        user1 = User(username='duplicate', full_name='User One', email='one@example.com')
        user1.set_password('pass1')
        db.session.add(user1)
        db.session.commit()
    
    # Try to create user with same username
    response = admin_client.post('/admin/user/create', data={
            'username': 'duplicate',
            'full_name': 'User Two',
            'email': 'two@example.com',
            'password': 'pass2',
            'password_confirm': 'pass2',
            'submit': 'Save'
        }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Username already in use' in response.data


def test_create_user_duplicate_email(admin_client, app):
    """Test creating a user with duplicate email fails."""
    with app.app_context():
        # Create first user
        user1 = User(username='userone', full_name='User One', email='same@example.com')
        user1.set_password('pass1')
        db.session.add(user1)
        db.session.commit()
    
   # Try to create user with same email
    response = admin_client.post('/admin/user/create', data={
            'username': 'usertwo',
            'full_name': 'User Two',
            'email': 'same@example.com',
            'password': 'pass2',
            'password_confirm': 'pass2',
            'submit': 'Save'
        }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Email already in use' in response.data


def test_edit_user(admin_client, test_user, app):
    """Test editing a user via admin interface."""
    with app.app_context():
        # Get the user object from the ID
        user_obj = User.query.get(test_user)
        # First create a user to edit
        user = User(
            username='edituser',
            full_name='Edit User',
            email='edit@example.com',
            is_admin=False,
            is_active=True
        )
        user.set_password('editpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id  # Store ID while still in session
    
  # Edit the user
    response = admin_client.post(f'/admin/user/{user_id}/edit', data={
            'username': 'editeduser',
            'full_name': 'Edited User',
            'email': 'edited@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'is_admin': 'y',
            'submit': 'Save'
        }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'User updated successfully' in response.data
    
    # Verify changes were saved
    with app.app_context():
        user = User.query.get(user_id)  # Refetch to avoid detachment issues
        assert user.username == 'editeduser'
        assert user.full_name == 'Edited User'
        assert user.email == 'edited@example.com'
        assert user.is_admin == True
        assert user.is_active == False


def test_toggle_user_status(admin_client, test_user, app):
    """Test activating/deactivating a user."""
    with app.app_context():
        # Get the user object from the ID
        user_obj = User.query.get(test_user)
        # Create a user to toggle
        user = User(
            username='togletest',
            full_name='Toggle Test',
            email='toggle@example.com',
            is_admin=False,
            is_active=True
        )
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        user_id = user.id  # Store ID while still in session
    
    # Deactivate user
    response = admin_client.post(f'/admin/user/{user_id}/toggle_active', follow_redirects=True)
    assert response.status_code == 200
    assert b'deactivated' in response.data
    
    with app.app_context():
        user = User.query.get(user_id)  # Refetch to avoid detachment issues
        assert user.is_active == False
    
    # Activate user again
    response = admin_client.post(f'/admin/user/{user_id}/toggle_active', follow_redirects=True)
    assert response.status_code == 200
    assert b'activated' in response.data
    
    with app.app_context():
        user = User.query.get(user_id)  # Refetch to avoid detachment issues
        assert user.is_active == True


def test_admin_access_control(client, test_user, app):
    """Test that non-admin users cannot access admin routes."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
    
    # Login as regular user
    client.post('/auth/login', data={
        'username': user.username,
        'password': 'testpass'
    })
    
    # Try to access admin users page
    response = client.get('/admin/users', follow_redirects=True)
    assert response.status_code == 200
    # Should show error message or redirect
    assert b'You do not have permission' in response.data or b'Login' in response.data