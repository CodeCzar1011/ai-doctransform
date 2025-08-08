import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Import extensions
from .extensions import db, bcrypt, login_manager, migrate

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-default-secret-key')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///crownix.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Configure SQLite for better concurrency
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'connect_args': {'check_same_thread': False}
        }

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Enable CORS for all routes
    CORS(app, resources={
        r"/*": {
            "origins": [
                "https://ai-doctransform.onrender.com",
                "http://localhost:5000",
                "http://127.0.0.1:5000",
                "file://"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })

    # Import models here for the user_loader and create_all
    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Import and register blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='')
    
    from .api.insurance_endpoints import insurance_bp
    app.register_blueprint(insurance_bp)

    # Register database commands
    from .init_db import register_commands
    register_commands(app)
    
    # Initialize database within app context
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Create uploads directory if it doesn't exist
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app

