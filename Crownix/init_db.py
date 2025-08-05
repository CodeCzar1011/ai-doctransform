#!/usr/bin/env python3
"""
Database initialization script for Crownix application
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def create_app():
    """Create Flask app for database initialization"""
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_migrate import Migrate
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    app = Flask(__name__)
    
    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Database configuration
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Production database (PostgreSQL)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Development database (SQLite)
        db_path = os.path.join(current_dir, 'crownix.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db = SQLAlchemy()
    migrate = Migrate()
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models to register them
    with app.app_context():
        from models import User, DocumentModel, ProcessingJob, APIUsage
    
    return app, db

def init_database_tables():
    """Initialize all database tables"""
    app, db = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Print table information
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📊 Created {len(tables)} tables:")
            for table in tables:
                print(f"   - {table}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False

def seed_sample_data():
    """Add some sample data for testing (optional)"""
    app, db = create_app()
    
    with app.app_context():
        try:
            from models import DocumentModel
            
            # Check if data already exists
            if DocumentModel.query.first():
                print("📝 Sample data already exists, skipping seed...")
                return True
            
            # Add sample document (for testing)
            sample_doc = DocumentModel(
                original_filename="sample_document.txt",
                unique_filename="sample_123_document.txt",
                file_path="uploads/sample_123_document.txt",
                file_extension="txt",
                file_size=1386,
                mime_type="text/plain",
                extracted_text="This is a sample document for testing the Crownix application database functionality.",
                extraction_status="completed"
            )
            
            db.session.add(sample_doc)
            db.session.commit()
            
            print("✅ Sample data seeded successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error seeding sample data: {e}")
            return False

def reset_database():
    """Reset database (drop and recreate all tables)"""
    app, db = create_app()
    
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            print("🗑️  Dropped all existing tables")
            
            # Recreate tables
            db.create_all()
            print("✅ Database reset successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            print("🚀 Initializing Crownix database...")
            success = init_database_tables()
            sys.exit(0 if success else 1)
            
        elif command == "seed":
            print("🌱 Seeding sample data...")
            init_success = init_database_tables()
            if init_success:
                seed_success = seed_sample_data()
                sys.exit(0 if seed_success else 1)
            else:
                sys.exit(1)
                
        elif command == "reset":
            print("⚠️  Resetting database (this will delete all data)...")
            confirm = input("Are you sure? Type 'yes' to continue: ")
            if confirm.lower() == 'yes':
                success = reset_database()
                sys.exit(0 if success else 1)
            else:
                print("❌ Database reset cancelled")
                sys.exit(1)
                
        else:
            print(f"❌ Unknown command: {command}")
            print_usage()
            sys.exit(1)
    else:
        print_usage()

def print_usage():
    """Print usage information"""
    print("""
🏗️  Crownix Database Initialization Script

Usage:
    python init_db.py <command>

Commands:
    init    - Initialize database tables
    seed    - Initialize tables and add sample data
    reset   - Reset database (WARNING: deletes all data)

Examples:
    python init_db.py init
    python init_db.py seed
    python init_db.py reset
    """)

if __name__ == "__main__":
    main()
