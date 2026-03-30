#!/usr/bin/env python3
"""
Entry point for the Inspection Reporting and Management application.
"""
import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Run the application with SSL context for HTTPS
    cert_path = 'certs/cert.pem'
    key_path = 'certs/key.pem'
    if os.path.exists(cert_path) and os.path.exists(key_path):
        app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=(cert_path, key_path))
    else:
        print("SSL certificates not found. Please run setup.py first.")
        print("Running in HTTP mode for development (not recommended for production).")
        app.run(host='0.0.0.0', port=5000, debug=True)