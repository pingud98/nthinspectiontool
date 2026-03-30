"""
Admin routes for user management.
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from functools import wraps
from app.routes.auth import admin_required

admin = Blueprint('admin', __name__)

# Forms
class UserForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        super(UserForm, self).__init__(*args, **kwargs)
        
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=8, max=128)])
    password_confirm = PasswordField('Confirm Password', validators=[EqualTo('password')])
    is_admin = BooleanField('Admin Privileges')
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.user_id:
            raise ValidationError('Username already in use. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.user_id:
            raise ValidationError('Email already in use. Please choose a different one.')

# Routes
@admin.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.username).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users)

@admin.route('/user/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = UserForm(user_id=None)
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            full_name=form.full_name.data,
            email=form.email.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data
        )
        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Set a random unusable password if none provided? Or require password?
            # For simplicity, we'll require password on creation.
            flash('Password is required for new users.', 'error')
            return render_template('admin/user_form.html', form=form, title='Create User')
        db.session.add(user)
        db.session.commit()
        flash('User created successfully.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', form=form, title='Create User')

@admin.route('/user/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(user_id=user.id)
    if form.validate_on_submit():
        user.username = form.username.data
        user.full_name = form.full_name.data
        user.email = form.email.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin.users'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.full_name.data = user.full_name
        form.email.data = user.email
        form.is_admin.data = user.is_admin
        form.is_active.data = user.is_active
    return render_template('admin/user_form.html', form=form, title='Edit User')

@admin.route('/user/<int:id>/toggle_active', methods=['POST'])
@login_required
@admin_required
def toggle_active(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
        return redirect(url_for('admin.users'))
    user.is_active = not user.is_active
    db.session.commit()
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully.', 'success')
    return redirect(url_for('admin.users'))