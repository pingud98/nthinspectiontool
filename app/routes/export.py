"""
Export routes for generating PDF reports.
"""
from flask import Blueprint, send_file, make_response, current_app, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Inspection
from app.utils.pdf_generator import generate_pdf
import io

export = Blueprint('export', __name__)

@export.route('/<int:id>/pdf')
@login_required
def export_pdf(id):
    """Generate and serve PDF report for an inspection."""
    inspection = Inspection.query.get_or_404(id)
    # Check if user has permission to view this inspection (simple check: creator or admin)
    if inspection.created_by != current_user.id and not current_user.is_admin:
        # For simplicity, we'll allow if they are an inspector? But we'll just check creator/admin for now.
        # In a full implementation, we'd check if the user is in the inspectors list.
        flash('You do not have permission to export this inspection.', 'error')
        return redirect(url_for('inspections.dashboard'))
    
    # Generate PDF
    pdf_bytes = generate_pdf(id)
    
    # Create a file-like object from the PDF bytes
    pdf_file = io.BytesIO(pdf_bytes)
    
    # Generate filename
    filename = f"inspection_report_{inspection.reference_number}_v{inspection.version}.pdf"
    
    # Return PDF as download
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )