from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    documents = db.relationship('Document', backref='user', lazy=True, cascade='all, delete-orphan')
    processing_jobs = db.relationship('ProcessingJob', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    """Document model for storing uploaded files and their metadata"""
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    original_filename = db.Column(db.String(255), nullable=False)
    unique_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_extension = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    mime_type = db.Column(db.String(100))
    
    # Text extraction
    extracted_text = db.Column(db.Text)
    extraction_status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    extraction_error = db.Column(db.Text)
    
    # Metadata
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # nullable for anonymous uploads
    
    # Relationships
    processing_jobs = db.relationship('ProcessingJob', backref='document', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'
    
    def to_dict(self):
        """Convert document to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'original_filename': self.original_filename,
            'file_extension': self.file_extension,
            'file_size': self.file_size,
            'extraction_status': self.extraction_status,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class ProcessingJob(db.Model):
    """Model for tracking AI processing jobs and their results"""
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    
    # Job details
    job_type = db.Column(db.String(50), nullable=False)  # 'summarize', 'translate', 'analyze', etc.
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    
    # Input and output
    input_text = db.Column(db.Text)
    output_text = db.Column(db.Text)
    ai_model = db.Column(db.String(50), default='gemini-pro')
    
    # Processing metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    processing_time = db.Column(db.Float)  # in seconds
    
    # Error handling
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    
    # Relationships
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def __repr__(self):
        return f'<ProcessingJob {self.job_type} - {self.status}>'
    
    def to_dict(self):
        """Convert processing job to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'uuid': self.uuid,
            'job_type': self.job_type,
            'status': self.status,
            'ai_model': self.ai_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'processing_time': self.processing_time
        }

class APIUsage(db.Model):
    """Model for tracking API usage and costs"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    processing_job_id = db.Column(db.Integer, db.ForeignKey('processing_jobs.id'), nullable=True)
    
    # API details
    api_provider = db.Column(db.String(50), nullable=False)  # 'gemini', 'openai', etc.
    api_model = db.Column(db.String(50), nullable=False)
    
    # Usage metrics
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    total_tokens = db.Column(db.Integer)
    estimated_cost = db.Column(db.Float)  # in USD
    
    # Timing
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)  # in seconds
    
    def __repr__(self):
        return f'<APIUsage {self.api_provider} - {self.total_tokens} tokens>'
