import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db

def init_database(app: Flask):
    """Initialize database configuration and setup"""
    
    # Database configuration
    if os.environ.get('DATABASE_URL'):
        # Production database (PostgreSQL on Render/Heroku)
        database_url = os.environ.get('DATABASE_URL')
        # Fix for SQLAlchemy 1.4+ compatibility with Heroku/Render
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Development database (SQLite)
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "crownix.db")}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    return db, migrate

def create_tables(app: Flask):
    """Create all database tables"""
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")

def seed_database(app: Flask):
    """Seed database with initial data if needed"""
    with app.app_context():
        # Add any initial data here if needed
        # For example, create admin user, default settings, etc.
        pass
