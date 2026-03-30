"""
Inspection routes for creating, viewing, editing, and listing inspections.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Inspection, InspectionInspector, Photo, ConclusionStatus, ActionRequired, User
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, DateField, SelectField, FieldList, FormField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

inspections = Blueprint('inspections', __name__)

# Forms
class InspectorForm(FlaskForm):
    user_id = SelectField('Registered User', coerce=int, validators=[Optional()])
    free_text_name = StringField('Free-text Name', validators=[Optional(), Length(max=128)])
    # We'll use a custom validator to ensure at least one is set

class PhotoForm(FlaskForm):
    caption = StringField('Caption', validators=[Optional(), Length(max=255)])
    action_required = SelectField('Action Required', choices=[
        (ActionRequired.NONE.value, 'No action required'),
        (ActionRequired.URGENT.value, 'Urgent action required'),
        (ActionRequired.BEFORE_NEXT.value, 'Action required before next inspection')
    ], validators=[DataRequired()])
    # File field will be handled in the view, not in the form for multiple uploads

class InspectionForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        self.inspection_id = kwargs.pop('inspection_id', None)
        super(InspectionForm, self).__init__(*args, **kwargs)
        
    installation_name = StringField('Installation Name', validators=[DataRequired(), Length(max=255)])
    location = StringField('Location', validators=[DataRequired(), Length(max=255)])
    inspection_date = DateField('Date of Inspection', validators=[DataRequired()], format='%Y-%m-%d')
    reference_number = IntegerField('Reference Number', validators=[DataRequired(), NumberRange(min=1)])
    observations = TextAreaField('Observations', validators=[Optional()])
    conclusion_text = TextAreaField('Conclusion Comments', validators=[Optional()])
    conclusion_status = SelectField('Conclusion Status', choices=[
        (ConclusionStatus.OK.value, 'OK for operation in current state'),
        (ConclusionStatus.MINOR.value, 'Minor comments — Remedial actions required for continued operation'),
        (ConclusionStatus.MAJOR.value, 'Major comments — Operation suspended until resolution and satisfactory follow-up inspection')
    ], validators=[DataRequired()])
    inspectors = FieldList(FormField(InspectorForm), min_entries=1)
    photos = FieldList(FormField(PhotoForm), min_entries=0)
    submit = SubmitField('Submit')

    def validate_reference_number(self, field):
        # Check if reference number already exists (excluding current inspection if editing)
        if self.inspection_id:
            # Editing existing inspection
            existing = Inspection.query.filter(
                Inspection.reference_number == field.data,
                Inspection.id != self.inspection_id
            ).first()
        else:
            # Creating new inspection
            existing = Inspection.query.filter_by(reference_number=field.data).first()
        
        if existing:
            raise ValidationError('Reference number already exists. Please use a unique reference number.')

# Helper function to save uploaded photos
def save_photo(file):
    if file and file.filename:
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return None
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return unique_filename
    return None

# Routes
@inspections.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve uploaded files."""
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)


@inspections.route('/')
@login_required
def dashboard():
    # Show inspections that the user has access to (created by them or they are an inspector)
    # For simplicity, we'll show all inspections for now
    inspections = Inspection.query.order_by(Inspection.created_at.desc()).all()
    return render_template('dashboard.html', inspections=inspections)

@inspections.route('/new', methods=['GET', 'POST'])
@login_required
def new_inspection():
    form = InspectionForm()
    # Populate the user dropdown for inspectors
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    # Access the SelectField correctly through the FormField's form attribute
    if len(form.inspectors) > 0:
        form.inspectors[0].form.user_id.choices = [(0, '-- Select User --')] + [(u.id, u.full_name) for u in users]
    # Pre-fill the first inspector with the current user
    if request.method == 'GET':
        form.inspectors[0].user_id.data = current_user.id
        form.inspectors[0].free_text_name.data = ''
        # Set default date to today
        form.inspection_date.data = datetime.today().date()
    if form.validate_on_submit():
        # Create inspection
        inspection = Inspection(
            installation_name=form.installation_name.data,
            location=form.location.data,
            inspection_date=form.inspection_date.data,
            reference_number=form.reference_number.data,
            observations=form.observations.data,
            conclusion_text=form.conclusion_text.data,
            conclusion_status=ConclusionStatus(form.conclusion_status.data),
            created_by=current_user.id
        )
        db.session.add(inspection)
        db.session.flush()  # Get the ID for foreign keys
        
        # Add inspectors
        for inspector_form in form.inspectors:
            if inspector_form.user_id.data and inspector_form.user_id.data != 0:
                inspector = InspectionInspector(
                    inspection_id=inspection.id,
                    user_id=inspector_form.user_id.data
                )
            elif inspector_form.free_text_name.data:
                inspector = InspectionInspector(
                    inspection_id=inspection.id,
                    free_text_name=inspector_form.free_text_name.data
                )
            else:
                continue  # Skip if neither is set
            db.session.add(inspector)
        
        # Handle photo uploads
        # Process uploaded photos from the form
        for idx, photo_form in enumerate(form.photos):
            # Check if a file was uploaded for this photo entry
            file_key = f'photos-{idx}-file'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    # Save the photo
                    filename = save_photo(file)
                    if filename:
                        # Create photo record
                        photo = Photo(
                            inspection_id=inspection.id,
                            filename=filename,
                            caption=photo_form.caption.data,
                            action_required=ActionRequired(photo_form.action_required.data)
                        )
                        db.session.add(photo)
                    else:
                        flash('Invalid file type. Only JPG, JPEG, PNG, GIF, and WEBP are allowed.', 'warning')
        
        db.session.commit()
        flash('Inspection report created successfully.', 'success')
        return redirect(url_for('inspections.view_inspection', id=inspection.id))
    
    # Pass users to template for JavaScript functionality
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    return render_template('inspection_form.html', form=form, title='New Inspection', users=users)

@inspections.route('/<int:id>')
@login_required
def view_inspection(id):
    inspection = Inspection.query.get_or_404(id)
    return render_template('inspection_view.html', inspection=inspection)

@inspections.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_inspection(id):
    inspection = Inspection.query.get_or_404(id)
    # Check if user has permission to edit (creator or admin?)
    if inspection.created_by != current_user.id and not current_user.is_admin:
        flash('You do not have permission to edit this inspection.', 'error')
        return redirect(url_for('inspections.dashboard'))
    
    form = InspectionForm(obj=inspection, inspection_id=inspection.id)
    # Populate user dropdown
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    for inspector_form in form.inspectors:
        inspector_form.user_id.choices = [(0, '-- Select User --')] + [(u.id, u.full_name) for u in users]
    
    if request.method == 'GET':
        # Populate inspectors
        # Clear existing entries
        while len(form.inspectors) > 0:
            form.inspectors.pop_entry()
        for inspector in inspection.inspectors:
            if inspector.user_id:
                form.inspectors.append_entry({
                    'user_id': inspector.user_id,
                    'free_text_name': ''
                })
            else:
                form.inspectors.append_entry({
                    'user_id': 0,
                    'free_text_name': inspector.free_text_name
                })
        # Ensure at least one entry
        if len(form.inspectors) == 0:
            form.inspectors.append_entry()
        
        # Populate photos
        # Clear existing entries
        while len(form.photos) > 0:
            form.photos.pop_entry()
        for photo in inspection.photos:
            form.photos.append_entry({
                'caption': photo.caption,
                'action_required': photo.action_required.value
            })
    
    if form.validate_on_submit():
        # Update inspection fields
        inspection.installation_name = form.installation_name.data
        inspection.location = form.location.data
        inspection.inspection_date = form.inspection_date.data
        inspection.reference_number = form.reference_number.data
        inspection.observations = form.observations.data
        inspection.conclusion_text = form.conclusion_text.data
        inspection.conclusion_status = ConclusionStatus(form.conclusion_status.data)
        inspection.updated_at = datetime.utcnow()
        
        # Update inspectors: remove existing and add new
        InspectionInspector.query.filter_by(inspection_id=inspection.id).delete()
        for inspector_form in form.inspectors:
            if inspector_form.user_id.data and inspector_form.user_id.data != 0:
                inspector = InspectionInspector(
                    inspection_id=inspection.id,
                    user_id=inspector_form.user_id.data
                )
            elif inspector_form.free_text_name.data:
                inspector = InspectionInspector(
                    inspection_id=inspection.id,
                    free_text_name=inspector_form.free_text_name.data
                )
            else:
                continue
            db.session.add(inspector)
        
        # Handle photo updates
        # Remove existing photos
        Photo.query.filter_by(inspection_id=inspection.id).delete()
        
        # Process uploaded photos from the form
        for idx, photo_form in enumerate(form.photos):
            # Check if a file was uploaded for this photo entry
            file_key = f'photos-{idx}-file'
            if file_key in request.files:
                file = request.files[file_key]
                if file and file.filename:
                    # Save the photo
                    filename = save_photo(file)
                    if filename:
                        # Create photo record
                        photo = Photo(
                            inspection_id=inspection.id,
                            filename=filename,
                            caption=photo_form.caption.data,
                            action_required=ActionRequired(photo_form.action_required.data)
                        )
                        db.session.add(photo)
                    else:
                        flash('Invalid file type. Only JPG, JPEG, PNG, GIF, and WEBP are allowed.', 'warning')
                # If no file uploaded but we have caption/action data, keep existing photo?
                # For simplicity, we only process when a file is uploaded
        
        # Increment version
        inspection.version += 1
        
        db.session.commit()
        flash('Inspection report updated successfully.', 'success')
        return redirect(url_for('inspections.view_inspection', id=inspection.id))
    
    # Pass users to template for JavaScript functionality
    users = User.query.filter_by(is_active=True).order_by(User.full_name).all()
    return render_template('inspection_form.html', form=form, title='Edit Inspection', inspection=inspection, users=users)