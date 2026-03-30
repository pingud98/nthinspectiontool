"""
Unit tests for database models.
"""
import pytest
from datetime import date
from app import db
from app.models import User, Inspection, Photo, ConclusionStatus, ActionRequired


def test_user_creation(app, test_user):
    """Test creating a user."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"
        assert user.is_active == True
        assert user.is_admin == False
        assert user.check_password("testpass") == True
        assert user.check_password("wrongpass") == False


def test_admin_creation(app, test_admin):
    """Test creating an admin user."""
    with app.app_context():
        # Get the admin object from the ID
        admin = User.query.get(test_admin)
        assert admin.username == "admin"
        assert admin.is_admin == True
        assert admin.check_password("adminpass") == True


def test_inspection_creation(app, test_user):
    """Test creating an inspection."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        inspection = Inspection(
            installation_name="Test Installation",
            location="Test Location",
            inspection_date=date(2026, 1, 1),
            reference_number=12345,
            observations="Test observations",
            conclusion_text="Test conclusion",
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        
        assert inspection.id is not None
        assert inspection.installation_name == "Test Installation"
        assert inspection.location == "Test Location"
        assert inspection.reference_number == 12345
        assert inspection.version == 1
        assert inspection.observations == "Test observations"
        assert inspection.conclusion_text == "Test conclusion"
        assert inspection.conclusion_status == ConclusionStatus.OK
        assert inspection.created_by == user.id


def test_photo_creation(app, test_user):
    """Test creating a photo associated with an inspection."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # First create an inspection
        inspection = Inspection(
            installation_name="Test Installation",
            location="Test Location",
            inspection_date=date(2026, 1, 1),
            reference_number=12345,
            observations="Test observations",
            conclusion_text="Test conclusion",
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        
        # Then create a photo
        photo = Photo(
            inspection_id=inspection.id,
            filename="test.jpg",
            caption="Test caption",
            action_required=ActionRequired.URGENT
        )
        db.session.add(photo)
        db.session.commit()
        
        assert photo.id is not None
        assert photo.inspection_id == inspection.id
        assert photo.filename == "test.jpg"
        assert photo.caption == "Test caption"
        assert photo.action_required == ActionRequired.URGENT


def test_inspection_relationships(app, test_user):
    """Test relationships between inspection and related models."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create inspection
        inspection = Inspection(
            installation_name="Test Installation",
            location="Test Location",
            inspection_date=date(2026, 1, 1),
            reference_number=12345,
            observations="Test observations",
            conclusion_text="Test conclusion",
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        
        # Create photo
        photo = Photo(
            inspection_id=inspection.id,
            filename="test.jpg",
            caption="Test photo"
        )
        db.session.add(photo)
        
        # Create inspector association
        from app.models import InspectionInspector
        inspector = InspectionInspector(
            inspection_id=inspection.id,
            user_id=user.id
        )
        db.session.add(inspector)
        
        db.session.commit()
        
        # Test relationships
        assert len(inspection.photos) == 1
        assert inspection.photos[0].filename == "test.jpg"
        assert len(inspection.inspectors) == 1
        assert inspection.inspectors[0].user_id == user.id
        assert inspection.creator.username == user.username


def test_unique_reference_number_constraint(app, test_user):
    """Test that reference numbers must be unique."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create first inspection
        inspection1 = Inspection(
            installation_name="Test Installation 1",
            location="Test Location 1",
            inspection_date=date(2026, 1, 1),
            reference_number=1000,
            observations="Test observations 1",
            conclusion_text="Test conclusion 1",
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection1)
        db.session.commit()
        
        # Try to create second inspection with same reference number
        inspection2 = Inspection(
            installation_name="Test Installation 2",
            location="Test Location 2",
            inspection_date=date(2026, 1, 2),
            reference_number=1000,  # Same reference number
            observations="Test observations 2",
            conclusion_text="Test conclusion 2",
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection2)
        
        # This should raise an integrity error
        with pytest.raises(Exception):
            db.session.commit()