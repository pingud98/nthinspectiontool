#!/usr/bin/env python3
"""
Setup script for the Inspection Reporting and Management application.
"""
import subprocess
import sys
import os
from datetime import datetime

def run_command(command, description=None):
    """Run a shell command and handle errors."""
    if description:
        print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stdout)
        print(e.stderr)
        return False

def main():
    print("=== Inspection Reporting and Management Application Setup ===\n")
    
    # Step 1: Install dependencies
    if not run_command(f"{sys.executable} -m pip install --upgrade -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Step 2: Generate self-signed TLS certificate
    print("\nGenerating self-signed TLS certificate...")
    cert_dir = "certs"
    os.makedirs(cert_dir, exist_ok=True)
    
    # Check if we have mkcert or trustme, otherwise use OpenSSL
    # We'll use OpenSSL for compatibility
    cert_file = os.path.join(cert_dir, "cert.pem")
    key_file = os.path.join(cert_dir, "key.pem")
    
    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        # Generate self-signed certificate using OpenSSL
        openssl_cmd = f'openssl req -x509 -newkey rsa:4096 -keyout {key_file} -out {cert_file} -days 365 -nodes -subj "/CN=localhost"'
        if not run_command(openssl_cmd, "Generating TLS certificate"):
            sys.exit(1)
        print(f"Certificate saved to {cert_file}")
        print(f"Key saved to {key_file}")
    else:
        print("Certificate already exists, skipping generation.")
    
    # Step 3: Create database and run migrations
    # We'll use Flask-Migrate to handle migrations
    # First, we need to create the app and initialize the database
    # We'll do this by running a Python script that initializes the db
    print("\nSetting up database...")
    setup_db_script = """
import os
from app import create_app, db
from app.models import User, Inspection, InspectionInspector, Photo
from flask_migrate import Migrate, init, migrate, upgrade
from flask import Flask

# Create app
app = create_app()
app.app_context().push()

# Initialize migrations if not already done
if not os.path.exists('migrations'):
    init()
    
# Create migration script if there are changes
migrate(message="Initial migration")

# Apply migrations
upgrade()
print("Database initialized and migrations applied.")
"""
    with open('temp_setup_db.py', 'w') as f:
        f.write(setup_db_script)
    
    if not run_command(f"{sys.executable} temp_setup_db.py", "Creating database and running migrations"):
        sys.exit(1)
    
    os.remove('temp_setup_db.py')
    
    # Step 4: Prompt for admin details
    print("\n=== Admin Account Setup ===")
    username = input("Enter admin username: ").strip()
    while not username:
        username = input("Username cannot be empty. Enter admin username: ").strip()
    
    full_name = input("Enter admin full name: ").strip()
    while not full_name:
        full_name = input("Full name cannot be empty. Enter admin full name: ").strip()
    
    email = input("Enter admin email: ").strip()
    while not email:
        email = input("Email cannot be empty. Enter admin email: ").strip()
    
    password = input("Enter admin password: ").strip()
    while not password:
        password = input("Password cannot be empty. Enter admin password: ").strip()
    
    password_confirm = input("Confirm admin password: ").strip()
    while password_confirm != password:
        password_confirm = input("Passwords do not match. Confirm admin password: ").strip()
    
    # Step 5: Create admin account
    print("\nCreating admin account...")
    create_admin_script = f"""
from app import create_app, db
from app.models import User

app = create_app()
app.app_context().push()

# Check if admin already exists
admin = User.query.filter_by(username='{username}').first()
if admin:
    print("Admin user already exists. Updating details...")
else:
    admin = User(username='{username}', full_name='{full_name}', email='{email}', is_admin=True)
    db.session.add(admin)
    
admin.set_password('{password}')
db.session.commit()
print("Admin account created successfully.")
"""
    with open('temp_create_admin.py', 'w') as f:
        f.write(create_admin_script)
    
    if not run_command(f"{sys.executable} temp_create_admin.py", "Creating admin account"):
        sys.exit(1)
    
    os.remove('temp_create_admin.py')
    
    # Step 6: Print success message
    print("\n=== Setup Complete ===")
    print("Application has been successfully set up!")
    print(f"Admin username: {username}")
    print(f"To start the application, run: python run.py")
    print(f"Access the application at: https://localhost:5000")
    print("\nNote: The first time you access the site, your browser may warn about the self-signed certificate.")
    print("You will need to accept the warning to proceed.")

if __name__ == '__main__':
    main()