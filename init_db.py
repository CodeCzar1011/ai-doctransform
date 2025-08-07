#!/usr/bin/env python3
"""
Database initialization script for AI DocTransform application
This script is designed to work with Render deployment
"""

import os
import sys

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def init_database():
    """Initialize the database using the main application factory"""
    try:
        # Import the application factory from Crownix package
        from Crownix import create_app
        
        # Create the Flask app
        app = create_app()
        
        with app.app_context():
            # Import database instance
            from Crownix.extensions import db
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully!")
            
            # Import models to ensure they're registered
            from Crownix.models import User, Document, ProcessingJob, APIUsage
            print("✅ All models imported and registered!")
            
            return True
            
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🚀 Initializing AI DocTransform database...")
    
    if len(sys.argv) > 1 and sys.argv[1] == 'init':
        success = init_database()
        if success:
            print("✅ Database initialization completed successfully!")
            sys.exit(0)
        else:
            print("❌ Database initialization failed!")
            sys.exit(1)
    else:
        print("Usage: python init_db.py init")
        sys.exit(1)

if __name__ == "__main__":
    main()
