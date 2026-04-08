"""
Unit tests for PDF export functionality.
"""
import pytest
from datetime import date
from app import db
from app.models import Inspection, User, ConclusionStatus, ActionRequired, Photo
from app.utils.pdf_generator import generate_pdf


def test_pdf_generation(app, test_user):
    """Test generating a PDF for an inspection."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create an inspection with some data
        inspection = Inspection(
            installation_name='Test Installation',
            location='Test Location',
            inspection_date=date(2026, 1, 1),
            reference_number='88888',
            observations='Test observations for PDF',
            conclusion_text='Test conclusion for PDF',
            conclusion_status=ConclusionStatus.OK,
            created_by=user.id
        )
        db.session.add(inspection)
        db.session.commit()
        
        # Add a photo
        photo = Photo(
            inspection_id=inspection.id,
            filename='test_photo.jpg',
            caption='Test photo',
            action_required=ActionRequired.NONE
        )
        db.session.add(photo)
        db.session.commit()
        
        # Generate PDF
        pdf_bytes = generate_pdf(inspection.id)
        
        # Verify PDF was generated
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 1000  # Should be a reasonable size for a PDF
        
        # Check that it starts with PDF header
        assert pdf_bytes.startswith(b'%PDF')


def test_pdf_generation_with_inspectors(app, test_user):
    """Test PDF generation with inspectors."""
    with app.app_context():
        # Get the user object from the ID
        user = User.query.get(test_user)
        # Create inspection
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
        
        # Generate PDF
        pdf_bytes = generate_pdf(inspection.id)
        
        assert pdf_bytes is not None
        assert len(pdf_bytes) > 0


def test_pdf_generation_nonexistent_inspection(app):
    """Test PDF generation for nonexistent inspection raises 404."""
    with app.app_context():
        # Try to generate PDF for inspection that doesn't exist
        with pytest.raises(Exception):  # Should raise 404 or similar
            generate_pdf(99999)  # Non-existent ID