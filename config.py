import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max upload
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    # WeasyPrint settings
    WEASYPRINT_BASE_URL = os.environ.get('WEASYPRINT_BASE_URL') or 'file://' + os.path.abspath(os.path.dirname(__file__))
    # PDF settings
    PDF_DOWNLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'pdfs')
    # Ensure upload and pdf directories exist
    @staticmethod
    def init_app(app):
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.PDF_DOWNLOAD_FOLDER, exist_ok=True)