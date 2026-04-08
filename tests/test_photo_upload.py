"""
Unit tests for photo upload functionality.
"""
import pytest
import io
from datetime import date
from app import db
from app.models import Photo, Inspection, User, ConclusionStatus, ActionRequired
from unittest.mock import Mock


def test_save_photo_function(app):
    """Test the save_photo helper function."""
    from app.routes.inspections import save_photo
    
    # Create a mock file object
    test_file = Mock()
    test_file.filename = "test.jpg"
    test_file.save = Mock()
    
    # Test saving the photo
    with app.app_context():
        filename = save_photo(test_file)
        assert filename is not None
        assert filename.endswith(".jpg")
        assert len(filename) > 10  # UUID prefix + original filename
        
        # Verify save was called
        test_file.save.assert_called_once()
        
        # Check that the file path would be correct
        import os
        expected_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        test_file.save.assert_called_with(expected_filepath)


def test_save_photo_invalid_extension(app):
    """Test that invalid file extensions are rejected."""
    from app.routes.inspections import save_photo
    
    # Test with invalid extension
    test_file = Mock()
    test_file.filename = "test.exe"
    
    with app.app_context():
        filename = save_photo(test_file)
        assert filename is None  # Should return None for invalid extension
    
    # Test with no extension
    test_file = Mock()
    test_file.filename = "test"
    
    with app.app_context():
        filename = save_photo(test_file)
        assert filename is None  # Should return None for no extension


def test_photo_upload_in_inspection_creation(auth_client, test_user, app):
    """Test accessing the inspection creation form (file upload testing done in end-to-end tests)."""
    # Login the user
    with app.app_context():
        user = User.query.get(test_user)
    
    # Test that we can access the new inspection form
    response = auth_client.get('/new')
    assert response.status_code == 200
    assert b'New Inspection' in response.data
    
    # Test that we can submit the form without files (should work)
    response = auth_client.post('/new', data={
        'installation_name': 'Test Installation',
        'location': 'Test Location',
        'inspection_date': '2026-01-01',
        'reference_number': '54321',
        'observations': 'Test observations',
        'conclusion_text': 'Test conclusion',
        'conclusion_status': ConclusionStatus.OK.value,
        'submit': 'Submit'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Inspection report created successfully' in response.data
    
    # Verify inspection was created in database
    with app.app_context():
        inspection = Inspection.query.filter_by(reference_number=54321).first()
        assert inspection is not None
        assert inspection.installation_name == 'Test Installation'
        assert inspection.location == 'Test Location'


def test_photo_model_creation(app, test_user):
    """Test creating a photo record in the database."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create inspection first
        inspection = Inspection(
            installation_name='Test Installation',
            location='Test Location',
            inspection_date=date(2026, 1, 1),
            reference_number='77777',
            observations='Test observations',
            conclusion_text='Test conclusion',
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        
        # Create photo
        photo = Photo(
            inspection_id=inspection.id,
            filename='test_upload.jpg',
            caption='Test photo caption',
            action_required=ActionRequired.URGENT
        )
        db.session.add(photo)
        db.session.commit()
        
        assert photo.id is not None
        assert photo.inspection_id == inspection.id
        assert photo.filename == 'test_upload.jpg'
        assert photo.caption == 'Test photo caption'
        assert photo.action_required == ActionRequired.URGENT
        
        # Test relationship
        assert len(inspection.photos) == 1
        assert inspection.photos[0] == photo