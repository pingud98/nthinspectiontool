"""
Application factory and initialization module.
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import datetime
from flask_wtf import CSRFProtect
from flask_migrate import Migrate
import os
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory function."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from app.routes.inspections import inspections as inspections_blueprint
    app.register_blueprint(inspections_blueprint)
    
    from app.routes.export import export as export_blueprint
    app.register_blueprint(export_blueprint)
    
    # Initialize configuration
    Config.init_app(app)
    
    # Shell context for flask cli
    @app.shell_context_processor
    def make_shell_context():
        from app.models import User, Inspection, ConclusionStatus, ActionRequired
        return {'db': db, 'User': User, 'Inspection': Inspection, 
                'ConclusionStatus': ConclusionStatus, 'ActionRequired': ActionRequired}
    
    @app.context_processor
    def inject_now():
        from app.models import ConclusionStatus, ActionRequired
        return {"now": lambda: datetime.now(), 
                "ConclusionStatus": ConclusionStatus, 
                "ActionRequired": ActionRequired}
    return app

# Import models to ensure they are registered with SQLAlchemy before app creation
# This is done inside create_app to avoid circular imports, but we need to import here for migrations
# Actually, we'll import models in the routes or where needed to avoid circular imports.
# We'll import User and Inspection here for shell context, but we need to avoid circular imports.
# Let's import them inside the shell_context_processor function as shown above.