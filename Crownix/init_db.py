#!/usr/bin/env python3
"""
Database management script for Crownix application.

This script provides command-line utilities for managing the database:
- Initialize database tables
- Reset the database
- Seed sample data
- Run migrations
"""

import os
import sys
import click
from flask import current_app
from flask.cli import with_appcontext

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(current_dir))  # Add project root to path

def register_commands(app):
    """Register database commands with the Flask app."""
    app.cli.add_command(init_db_command)
    app.cli.add_command(reset_db_command)
    app.cli.add_command(seed_db_command)

@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database."""
    from .extensions import db
    
    try:
        # Create all database tables
        db.create_all()
        click.echo('Initialized the database.')
    except Exception as e:
        click.echo(f'Error initializing database: {str(e)}', err=True)
        sys.exit(1)

@click.command('reset-db')
@with_appcontext
def reset_db_command():
    """Drop and recreate all database tables."""
    from .extensions import db
    
    if click.confirm('Are you sure you want to drop all tables and recreate them? This will delete all data!'):
        try:
            # Drop all tables
            db.drop_all()
            click.echo('Dropped all tables.')
            
            # Recreate all tables
            db.create_all()
            click.echo('Recreated all tables.')
            
            # Ensure upload directory exists
            upload_dir = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            click.echo(f'Ensured upload directory exists at: {upload_dir}')
            
        except Exception as e:
            click.echo(f'Error resetting database: {str(e)}', err=True)
            sys.exit(1)
    else:
        click.echo('Database reset cancelled.')

@click.command('seed-db')
@with_appcontext
def seed_db_command():
    """Seed the database with sample data."""
    from .extensions import db
    from .models import User, Document, ProcessingJob
    from datetime import datetime, timedelta
    import uuid
    
    try:
        # Check if we already have users
        if User.query.first() is not None:
            if not click.confirm('Database already has data. Continue seeding anyway?'):
                return
        
        # Create sample user
        user = User(
            username='demo',
            email='demo@example.com',
            is_active=True
        )
        user.set_password('demo123')
        db.session.add(user)
        
        # Create sample document
        doc = Document(
            user=user,
            filename='sample_document.pdf',
            filepath='uploads/sample_document.pdf',
            file_type='application/pdf',
            file_size=1024 * 50  # 50KB
        )
        db.session.add(doc)
        
        # Create sample processing job
        job = ProcessingJob(
            document=doc,
            user=user,
            job_type='summary',
            input_data='{"summary_type": "brief"}',
            status='completed',
            result='{"summary": "This is a sample summary of the document."}',
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow()
        )
        db.session.add(job)
        
        # Commit all changes
        db.session.commit()
        click.echo('Successfully seeded database with sample data.')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error seeding database: {str(e)}', err=True)
        sys.exit(1)
    except ImportError as e:
        click.echo(f'Error importing models: {str(e)}', err=True)
        sys.exit(1)

def main():
    """Run the database management commands."""
    # Import the create_app function from the main package
    from . import create_app
    
    # Create the Flask application
    app = create_app()
    
    # Register the database commands
    register_commands(app)
    
    # Run the CLI
    app.cli.main()

if __name__ == "__main__":
    main()
