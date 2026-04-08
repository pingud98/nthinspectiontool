"""
Unit tests for inspection CRUD operations.
"""
import pytest
from datetime import date
from app import db
from app.models import Inspection, ConclusionStatus, ActionRequired, User, Photo


def test_create_inspection(client, test_user, app):
    """Test creating a new inspection."""
    # Print all registered routes for debugging
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    # Login the user manually
    with app.app_context():
        user = User.query.get(test_user)
        login_response = client.post('/auth/login', data={
            'username': user.username,
            'password': 'testpass'
        }, follow_redirects=True)
        print(f"Login response status: {login_response.status_code}")
        print(f"Login response data (first 200 chars): {login_response.data[:200]}")
    
    # Now try to access the new inspection form
    response = client.get('/new')
    print(f"New inspection form status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response data: {response.data[:200]}")  # First 200 chars
    
    # Actually perform the test
    response = client.post('/new', data={
        'installation_name': 'Test Installation',
        'location': 'Test Location',
        'inspection_date': '2026-01-01',
        'reference_number': '54321',
        'observations': 'Test observations',
        'conclusion_text': 'Test conclusion',
        'conclusion_status': ConclusionStatus.OK.value,
        'submit': 'Submit'
    }, follow_redirects=True)
    
    print(f"POST response status: {response.status_code}")
    print(f"POST response data (first 500 chars): {response.data[:500]}")
    
    assert response.status_code == 200
    assert b'Inspection report created successfully' in response.data
    
    # Verify inspection was created in database
    with app.app_context():
        user_obj = User.query.get(test_user)
        inspection = Inspection.query.filter_by(reference_number=54321).first()
        assert inspection is not None
        assert inspection.installation_name == 'Test Installation'
        assert inspection.location == 'Test Location'
        assert inspection.created_by == user_obj.id


def test_view_inspection(auth_client, test_user, app):
    """Test viewing an inspection."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create an inspection first
        inspection = Inspection(
            installation_name='Test Installation',
            location='Test Location',
            inspection_date=date(2026, 1, 1),
            reference_number='99999',
            observations='Test observations',
            conclusion_text='Test conclusion',
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        inspection_id = inspection.id  # Save the ID for later use
    
    # View the inspection
    response = auth_client.get(f'/{inspection_id}')
    assert response.status_code == 200
    assert b'Test Installation' in response.data
    assert b'Test Location' in response.data
    assert b'99999' in response.data


def test_edit_inspection(auth_client, test_user, app):
    """Test editing an inspection."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create an inspection first
        inspection = Inspection(
            installation_name='Original Installation',
            location='Original Location',
            inspection_date=date(2026, 1, 1),
            reference_number='11111',
            observations='Original observations',
            conclusion_text='Original conclusion',
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        inspection_id = inspection.id  # Save the ID for later use
    
    # Edit the inspection
    response = auth_client.post(f'/{inspection_id}/edit', data={
        'installation_name': 'Edited Installation',
        'location': 'Edited Location',
        'inspection_date': '2026-01-02',
        'reference_number': '22222',
        'observations': 'Edited observations',
        'conclusion_text': 'Edited conclusion',
        'conclusion_status': ConclusionStatus.MINOR.value,
        'submit': 'Submit'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Inspection report updated successfully' in response.data
    
    # Verify changes were saved
    with app.app_context():
        inspection = Inspection.query.get(inspection_id)  # Refetch to avoid detachment issues
        assert inspection.installation_name == 'Edited Installation'
        assert inspection.location == 'Edited Location'
        assert inspection.reference_number == 22222
        assert inspection.observations == 'Edited observations'
        assert inspection.conclusion_text == 'Edited conclusion'
        assert inspection.conclusion_status == ConclusionStatus.MINOR
        assert inspection.version == 2  # Version should be incremented


def test_inspection_version_increment(auth_client, test_user, app):
    """Test that inspection version increments on update."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        inspection = Inspection(
            installation_name='Test Installation',
            location='Test Location',
            inspection_date=date(2026, 1, 1),
            reference_number='33333',
            observations='Test observations',
            conclusion_text='Test conclusion',
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        inspection_id = inspection.id  # Save the ID for later use
    
    assert inspection.version == 1
    
    # Update the inspection
    auth_client.post(f'/{inspection_id}/edit', data={
        'installation_name': 'Updated Installation',
        'location': 'Test Location',  # Keep same location
        'inspection_date': '2026-01-01',
        'reference_number': '33333',  # Keep same reference number
        'observations': 'Updated observations',
        'conclusion_text': 'Updated conclusion',
        'conclusion_status': ConclusionStatus.OK.value,
        'submit': 'Submit'
    })
    
    with app.app_context():
        inspection = Inspection.query.get(inspection_id)  # Refetch to avoid detachment issues
        assert inspection.version == 2