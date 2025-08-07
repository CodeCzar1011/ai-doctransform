import os
import json
import uuid
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from . import db, bcrypt
from .models import User, Document, ChatMessage
from .document_processor import DocumentProcessor

main = Blueprint('main', __name__)

# Initialize enhanced document processor
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
doc_processor = DocumentProcessor(GEMINI_API_KEY) if GEMINI_API_KEY else None

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

logger = logging.getLogger(__name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

# --- AUTHENTICATION ROUTES ---
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'success': True, 'message': 'Already logged in.'})
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user and user.check_password(data.get('password')):
            login_user(user, remember=True)
            return jsonify({'success': True, 'message': 'Logged in successfully.'})
        return jsonify({'success': False, 'error': 'Invalid email or password.'}), 401
    return render_template('login.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return jsonify({'success': True, 'message': 'Already logged in.'})
    if request.method == 'POST':
        data = request.get_json()
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'success': False, 'error': 'Email is already registered.'}), 400
        new_user = User(username=data.get('username'), email=data.get('email'))
        new_user.set_password(data.get('password'))
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        return jsonify({'success': True, 'message': 'Signup successful. You are now logged in.'})
    return render_template('signup.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'You have been logged out.'})

# --- DOCUMENT & FILE ROUTES ---
@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload and text extraction"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid or no file selected'}), 400

        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join('uploads', unique_filename)
        file.save(file_path)

        extraction_result = doc_processor.extract_enhanced_text(file_path, file_extension)
        if not extraction_result['success']:
            os.remove(file_path) # Clean up failed upload
            return jsonify({'error': extraction_result.get('error', 'Failed to process file')}), 500

        document = Document(
            uuid=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=os.path.getsize(file_path),
            extracted_text=extraction_result['text'],
            metadata=json.dumps(extraction_result.get('metadata', {})),
            upload_timestamp=datetime.utcnow()
        )
        db.session.add(document)
        db.session.commit()

        return jsonify({'success': True, 'document': document.to_dict()})
    except Exception as e:
        logger.error(f"Upload Error: {e}")
        return jsonify({'error': 'An unexpected error occurred during upload.'}), 500

@main.route('/download/<filename>')
@login_required
def download_file(filename):
    """Download processed files"""
    return send_from_directory('uploads', filename, as_attachment=True)

# --- AI & DOCUMENT PROCESSING API ---
@main.route('/api/document/qa', methods=['POST'])
@login_required
def document_qa():
    """AI-powered Q&A on document content"""
    try:
        if not doc_processor:
            return jsonify({'error': 'Document processor not initialized.'}), 503
        data = request.get_json()
        document_uuid = data.get('document_uuid')
        question = data.get('question')
        document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
        if not document:
            return jsonify({'error': 'Document not found or access denied.'}), 404
        answer, job_uuid = doc_processor.answer_question(
            document_text=document.extracted_text, question=question, document_id=document.id, user_id=current_user.id)
        return jsonify({'success': True, 'answer': answer, 'job_uuid': job_uuid})
    except Exception as e:
        logger.error(f"Q&A Error: {e}")
        return jsonify({'error': 'An error occurred during Q&A.'}), 500

# --- CHAT HISTORY API ---
@main.route('/api/document/<string:document_uuid>/chat', methods=['GET'])
@login_required
def get_chat_history(document_uuid):
    document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
    if not document:
        return jsonify({'success': False, 'error': 'Document not found or access denied.'}), 404
    messages = ChatMessage.query.filter_by(document_id=document.id).order_by(ChatMessage.timestamp.asc()).all()
    return jsonify({'success': True, 'messages': [m.to_dict() for m in messages]})

@main.route('/api/document/<string:document_uuid>/chat', methods=['POST'])
@login_required
def post_chat_message(document_uuid):
    data = request.get_json()
    document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
    if not document:
        return jsonify({'success': False, 'error': 'Document not found or access denied.'}), 404
    
    chat_msg = ChatMessage(
        user_id=current_user.id,
        document_id=document.id,
        message_type=data.get('message_type', 'user'),
        content=data.get('content')
    )
    db.session.add(chat_msg)
    db.session.commit()
    return jsonify({'success': True, 'message': chat_msg.to_dict()})
