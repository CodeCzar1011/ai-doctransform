from datetime import datetime
import uuid
from flask_login import UserMixin
from . import db, bcrypt

class User(db.Model, UserMixin):
    """User model for authentication and user management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    documents = db.relationship('Document', backref='user', lazy=True, cascade='all, delete-orphan')
    processing_jobs = db.relationship('ProcessingJob', backref='user', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', back_populates='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Document(db.Model):
    """Document model for storing uploaded files and their metadata"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.Integer)  # in bytes
    extracted_text = db.Column(db.Text)
    metadata = db.Column(db.Text) # For storing JSON as a string
    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    processing_jobs = db.relationship('ProcessingJob', backref='document', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', back_populates='document', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Document {self.filename}>'

    def to_dict(self):
        """Convert document to dictionary for JSON serialization"""
        import json
        return {
            'uuid': self.uuid,
            'user_id': self.user_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'upload_timestamp': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'metadata': json.loads(self.metadata) if self.metadata else {}
        }

class ProcessingJob(db.Model):
    """Model for tracking AI processing jobs and their results"""
    __tablename__ = 'processing_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    job_type = db.Column(db.String(50), nullable=False)  # 'summarize', 'translate', 'analyze', etc.
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    input_text = db.Column(db.Text)
    output_text = db.Column(db.Text)
    ai_model = db.Column(db.String(50), default='gemini-pro')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    processing_time = db.Column(db.Float)  # in seconds
    error_message = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
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

class ChatMessage(db.Model):
    """Model for storing chat history for persistent AI chat per document and user"""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    message_type = db.Column(db.String(10), nullable=False)  # 'user' or 'ai'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='chat_messages', lazy=True)
    document = db.relationship('Document', back_populates='chat_messages', lazy=True)

    def __repr__(self):
        return f'<ChatMessage {self.message_type} - {self.timestamp}>'

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'user_id': self.user_id,
            'document_id': self.document_id,
            'message_type': self.message_type,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class APIUsage(db.Model):
    """Model for tracking API usage and costs"""
    __tablename__ = 'api_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    processing_job_id = db.Column(db.Integer, db.ForeignKey('processing_jobs.id'), nullable=True)
    api_provider = db.Column(db.String(50), nullable=False)  # 'gemini', 'openai', etc.
    api_model = db.Column(db.String(50), nullable=False)
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    total_tokens = db.Column(db.Integer)
    estimated_cost = db.Column(db.Float)  # in USD
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_time = db.Column(db.Float)  # in seconds
    
    def __repr__(self):
        return f'<APIUsage {self.api_provider} - {self.total_tokens} tokens>'


