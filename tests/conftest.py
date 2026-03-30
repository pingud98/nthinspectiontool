"""
Test configuration and fixtures for the inspection application.
"""
import pytest
from app import create_app, db
from app.models import User, Inspection, Photo


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
        "UPLOAD_FOLDER": "/tmp/test_uploads",
    })

    # Create tables and upload directory
    with app.app_context():
        db.create_all()
        import os
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    yield app

    # Clean up
    with app.app_context():
        db.session.remove()
        db.drop_all()
        import os
        import shutil
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            shutil.rmtree(app.config['UPLOAD_FOLDER'])


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user and return its ID."""
    with app.app_context():
        user = User(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            is_active=True
        )
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()
        return user.id  # Return ID instead of object


@pytest.fixture
def test_admin(app):
    """Create a test admin user and return its ID."""
    with app.app_context():
        admin = User(
            username="admin",
            full_name="Admin User",
            email="admin@example.com",
            is_admin=True,
            is_active=True
        )
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
        return admin.id  # Return ID instead of object


@pytest.fixture
def auth_client(client, test_user, app):
    """An authenticated test client."""
    with app.app_context():
        # Login the test user by ID
        user = User.query.get(test_user)
        client.post('/auth/login', data={
            'username': user.username,
            'password': 'testpass'
        })
    return client


@pytest.fixture
def admin_client(client, test_admin, app):
    """An admin authenticated test client."""
    with app.app_context():
        # Login the admin user by ID
        admin = User.query.get(test_admin)
        client.post('/auth/login', data={
            'username': admin.username,
            'password': 'adminpass'
        })
    return client