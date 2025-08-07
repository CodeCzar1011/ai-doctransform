#!/bin/bash

# Render build script for AI DocTransform
echo "Starting build process..."

# Install Python dependencies
pip install -r requirements.txt

# Run database initialization and migration
echo "Initializing database..."
python init_db.py

echo "Build completed successfully!"
