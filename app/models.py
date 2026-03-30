"""
Database models for the Inspection Reporting and Management application.
"""
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

# Enums for conclusion status and action required
class ConclusionStatus(enum.Enum):
    OK = 'ok'
    MINOR = 'minor'
    MAJOR = 'major'

class ActionRequired(enum.Enum):
    NONE = 'none'
    URGENT = 'urgent'
    BEFORE_NEXT = 'before_next'

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    inspections_created = db.relationship('Inspection', backref='creator', lazy=True, foreign_keys='Inspection.created_by')
    inspections_as_inspector = db.relationship('InspectionInspector', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Inspection(db.Model):
    """Inspection model representing a single inspection report."""
    __tablename__ = 'inspections'
    
    id = db.Column(db.Integer, primary_key=True)
    installation_name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    inspection_date = db.Column(db.Date, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    reference_number = db.Column(db.Integer, nullable=False, unique=True)
    observations = db.Column(db.Text)
    conclusion_text = db.Column(db.Text)
    conclusion_status = db.Column(db.Enum(ConclusionStatus), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    inspectors = db.relationship('InspectionInspector', backref='inspection', lazy=True, cascade='all, delete-orphan')
    photos = db.relationship('Photo', backref='inspection', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Inspection {self.reference_number} v{self.version}>'

class InspectionInspector(db.Model):
    """Association model for inspectors on an inspection (supports users and free-text names)."""
    __tablename__ = 'inspection_inspectors'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspections.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    free_text_name = db.Column(db.String(128), nullable=True)
    
    # Ensure either user_id or free_text_name is set
    __table_args__ = (
        db.CheckConstraint('(user_id IS NOT NULL) OR (free_text_name IS NOT NULL AND free_text_name != \'\')'),
    )
    
    def __repr__(self):
        if self.user_id:
            return f'<InspectionInspector User:{self.user_id}>'
        return f'<InspectionInspector FreeText:{self.free_text_name}>'

class Photo(db.Model):
    """Photo model for images attached to inspections."""
    __tablename__ = 'photos'
    
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey('inspections.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    action_required = db.Column(db.Enum(ActionRequired), default=ActionRequired.NONE, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Photo {self.filename}>'