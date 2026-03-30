# Inspection Reporting and Management Application

A production-ready web application for managing inspection reports, built with Python Flask.

## Features

- User authentication and authorization
- Admin panel for user management
- Inspection creation, editing, and viewing
- Photo uploads with captions and action requirements
- PDF export of inspection reports (A4 format)
- Role-based access control (admin vs regular users)
- Responsive design with Tailwind CSS

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: Flask (with Flask-Login, Flask-WTF, Flask-SQLAlchemy)
- **Database**: SQLite via SQLAlchemy ORM
- **PDF Generation**: WeasyPrint
- **TLS/HTTPS**: Self-signed certificate
- **Frontend**: Jinja2 templates + Tailwind CSS (via CDN) + vanilla JS
- **Authentication**: Bcrypt password hashing, session-based login
- **File Storage**: Local filesystem under `/uploads/`

## Setup
> **Note**: After running the setup script, an admin user is created with username `admin` and password `admin`. You can change these credentials after logging in.

1. Clone the repository
2. Run the setup script:
   ```bash
   python setup.py
   ```
3. The setup script will:
   - Install dependencies
   - Generate SSL certificates
   - Create the database and run migrations
   - Prompt for admin account details
4. Start the application:
   ```bash
   python run.py
   ```
5. Access the application at https://localhost:5000

## Project Structure

```
inspection-app/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── admin.py
│   │   ├── inspections.py
│   │   └── export.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── inspection_form.html
│   │   ├── inspection_view.html
│   │   └── admin/
│   │       ├── users.html
│   │       └── user_form.html
│   ├── utils/
│   │   ├── pdf_generator.py
│   │   └── security.py
│   └── static/
│       ├── css/
│       └── js/
├── uploads/
├── certs/
├── setup.py
├── run.py
├── requirements.txt
└── .gitignore
```

## License

This project is licensed under the MIT License.