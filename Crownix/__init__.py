import os
from flask import Flask
from dotenv import load_dotenv

# Import extensions
from .extensions import db, bcrypt, login_manager

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load environment variables
    load_dotenv()

    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a-default-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///crownix.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = 'uploads'

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Need to import models here for the user_loader and create_all
    from . import models

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    # Import and register blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint, url_prefix='')

    with app.app_context():
        db.create_all()

    return app

