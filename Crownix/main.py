import os
import json
import uuid
from flask import Blueprint, request, jsonify, render_template, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import logging

from .extensions import db, bcrypt
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
        # File validation
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid or no file selected'}), 400
        
        # File size validation (16MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > 16 * 1024 * 1024:  # 16MB limit
            return jsonify({'error': 'File size exceeds 16MB limit'}), 400
        
        # Secure filename handling
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join('uploads', unique_filename)
        
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)

        extraction_result = doc_processor.extract_enhanced_text(file_path, file_extension)
        if not extraction_result['success']:
            if os.path.exists(file_path):
                os.remove(file_path) # Clean up failed upload
            return jsonify({'error': extraction_result.get('error', 'Failed to process file')}), 500

        document = Document(
            uuid=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=file_size,
            extracted_text=extraction_result['text'],
            doc_metadata=json.dumps(extraction_result.get('metadata', {})),
            upload_timestamp=datetime.utcnow()
        )
        db.session.add(document)
        db.session.commit()

        return jsonify({'success': True, 'document': document.to_dict()})
    except Exception as e:
        logger.error(f"Upload Error: {e}")
        # Clean up file if it was saved
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
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
        
        # Input validation
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data provided.'}), 400
            
        document_uuid = data.get('document_uuid')
        question = data.get('question')
        
        # Validate required fields
        if not document_uuid:
            return jsonify({'error': 'Document UUID is required.'}), 400
        if not question:
            return jsonify({'error': 'Question is required.'}), 400
        
        # Validate input lengths
        if len(question) > 1000:  # Limit question length
            return jsonify({'error': 'Question too long. Maximum 1000 characters allowed.'}), 400
        
        # Sanitize inputs
        document_uuid = document_uuid.strip()
        question = question.strip()
        
        document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
        if not document:
            return jsonify({'error': 'Document not found or access denied.'}), 404
        
        # Check document text length
        if len(document.extracted_text) > 50000:  # Limit document size for AI processing
            return jsonify({'error': 'Document too large for Q&A. Maximum 50,000 characters allowed.'}), 400
        
        answer, job_uuid = doc_processor.answer_question(
            document_text=document.extracted_text, question=question, document_id=document.id, user_id=current_user.id)
        
        if not answer or 'error' in answer.lower():
            return jsonify({'error': answer or 'Failed to generate answer.'}), 500
        
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

# --- ENHANCED DOCUMENT PROCESSING API ---
@main.route('/api/document/enhanced-extract', methods=['POST'])
@login_required
def enhanced_extract():
    """Enhanced document extraction with metadata"""
    try:
        if not doc_processor:
            return jsonify({'error': 'Document processor not initialized.'}), 503
            
        # File validation
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid or no file selected'}), 400
        
        # File size validation (16MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > 16 * 1024 * 1024:  # 16MB limit
            return jsonify({'error': 'File size exceeds 16MB limit'}), 400
        
        # Secure filename handling
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({'error': 'Invalid filename'}), 400
            
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join('uploads', unique_filename)
        
        # Ensure uploads directory exists
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)

        extraction_result = doc_processor.extract_enhanced_text(file_path, file_extension)
        if not extraction_result['success']:
            if os.path.exists(file_path):
                os.remove(file_path)  # Clean up failed upload
            return jsonify({'error': extraction_result.get('error', 'Failed to process file')}), 500

        document = Document(
            uuid=str(uuid.uuid4()),
            user_id=current_user.id,
            filename=filename,
            file_path=file_path,
            file_type=file_extension,
            file_size=file_size,
            extracted_text=extraction_result['text'],
            doc_metadata=json.dumps(extraction_result.get('metadata', {})),
            upload_timestamp=datetime.utcnow()
        )
        db.session.add(document)
        db.session.commit()

        return jsonify({
            'success': True,
            'document_uuid': document.uuid,
            'filename': document.filename,
            'file_type': document.file_type,
            'extraction_result': extraction_result
        })
    except Exception as e:
        logger.error(f"Enhanced Extraction Error: {e}")
        # Clean up file if it was saved
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
        return jsonify({'error': 'An unexpected error occurred during extraction.'}), 500

@main.route('/api/document/smart-edit', methods=['POST'])
@login_required
def smart_edit():
    """AI-powered smart editing of document content"""
    try:
        if not doc_processor:
            return jsonify({'error': 'Document processor not initialized.'}), 503
        
        # Input validation
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data provided.'}), 400
            
        document_uuid = data.get('document_uuid')
        edit_instruction = data.get('edit_instruction')
        
        # Validate required fields
        if not document_uuid:
            return jsonify({'error': 'Document UUID is required.'}), 400
        if not edit_instruction:
            return jsonify({'error': 'Edit instruction is required.'}), 400
        
        # Validate input lengths
        if len(edit_instruction) > 1000:  # Limit instruction length
            return jsonify({'error': 'Edit instruction too long. Maximum 1000 characters allowed.'}), 400
        
        # Sanitize inputs
        document_uuid = document_uuid.strip()
        edit_instruction = edit_instruction.strip()
        
        document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
        if not document:
            return jsonify({'error': 'Document not found or access denied.'}), 404
        
        # Check document text length
        if len(document.extracted_text) > 50000:  # Limit document size for AI processing
            return jsonify({'error': 'Document too large for AI processing. Maximum 50,000 characters allowed.'}), 400
        
        edit_result = doc_processor.smart_edit_content(document.extracted_text, edit_instruction)
        if not edit_result['success']:
            return jsonify({'error': edit_result.get('error', 'Failed to edit content')}), 500
        
        # Save processing job
        job = ProcessingJob(
            job_type='edit',
            input_text=document.extracted_text,
            output_text=edit_result['edited_content'],
            document_id=document.id,
            user_id=current_user.id,
            status='completed'
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'edited_content': edit_result['edited_content'],
            'original_content': edit_result['original_content'],
            'edit_instruction': edit_result['edit_instruction'],
            'job_uuid': job.uuid
        })
    except Exception as e:
        logger.error(f"Smart Edit Error: {e}")
        return jsonify({'error': 'An error occurred during smart editing.'}), 500

@main.route('/api/document/convert', methods=['POST'])
@login_required
def convert_document():
    """Convert document to different formats"""
    try:
        if not doc_processor:
            return jsonify({'error': 'Document processor not initialized.'}), 503
        
        # Input validation
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data provided.'}), 400
            
        document_uuid = data.get('document_uuid')
        target_format = data.get('target_format', 'pdf')
        
        # Validate required fields
        if not document_uuid:
            return jsonify({'error': 'Document UUID is required.'}), 400
        
        # Validate and sanitize inputs
        document_uuid = document_uuid.strip()
        target_format = target_format.strip().lower()
        
        # Validate target format
        allowed_formats = ['pdf', 'docx', 'txt', 'html', 'md', 'json']
        if target_format not in allowed_formats:
            return jsonify({'error': f'Invalid target format. Allowed formats: {allowed_formats}'}), 400
        
        document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
        if not document:
            return jsonify({'error': 'Document not found or access denied.'}), 404
        
        # Check document text length
        if len(document.extracted_text) > 50000:  # Limit document size for conversion
            return jsonify({'error': 'Document too large for conversion. Maximum 50,000 characters allowed.'}), 400
        
        conversion_result = doc_processor.convert_document_format(
            document.extracted_text, document.file_type, target_format, 
            json.loads(document.doc_metadata) if document.doc_metadata else None)
        
        if not conversion_result['success']:
            return jsonify({'error': conversion_result.get('error', 'Failed to convert document')}), 500
        
        # Save processing job
        job = ProcessingJob(
            job_type='convert',
            input_text=document.extracted_text,
            output_text=conversion_result.get('file_path', ''),
            document_id=document.id,
            user_id=current_user.id,
            status='completed'
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'download_url': f"/download/{os.path.basename(conversion_result['file_path'])}",
            'target_format': target_format,
            'job_uuid': job.uuid
        })
    except Exception as e:
        logger.error(f"Conversion Error: {e}")
        return jsonify({'error': 'An error occurred during document conversion.'}), 500

@main.route('/api/document/summary', methods=['POST'])
@login_required
def document_summary():
    """Generate AI-powered summary of document content"""
    try:
        if not doc_processor:
            return jsonify({'error': 'Document processor not initialized.'}), 503
        
        # Input validation
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data provided.'}), 400
            
        document_uuid = data.get('document_uuid')
        summary_type = data.get('summary_type', 'brief')
        
        # Validate required fields
        if not document_uuid:
            return jsonify({'error': 'Document UUID is required.'}), 400
        
        # Validate and sanitize inputs
        document_uuid = document_uuid.strip()
        summary_type = summary_type.strip().lower()
        
        # Validate summary type
        allowed_types = ['brief', 'detailed', 'executive', 'key_points']
        if summary_type not in allowed_types:
            return jsonify({'error': f'Invalid summary type. Allowed types: {allowed_types}'}), 400
        
        document = Document.query.filter_by(uuid=document_uuid, user_id=current_user.id).first()
        if not document:
            return jsonify({'error': 'Document not found or access denied.'}), 404
        
        # Check document text length
        if len(document.extracted_text) > 50000:  # Limit document size for AI processing
            return jsonify({'error': 'Document too large for summarization. Maximum 50,000 characters allowed.'}), 400
        
        summary_result = doc_processor.generate_summary(document.extracted_text, summary_type)
        if not summary_result['success']:
            return jsonify({'error': summary_result.get('error', 'Failed to generate summary')}), 500
        
        # Save processing job
        job = ProcessingJob(
            job_type='summary',
            input_text=document.extracted_text,
            output_text=summary_result['summary'],
            document_id=document.id,
            user_id=current_user.id,
            status='completed'
        )
        db.session.add(job)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'summary': summary_result['summary'],
            'summary_type': summary_result['summary_type'],
            'job_uuid': job.uuid
        })
    except Exception as e:
        logger.error(f"Summary Error: {e}")
        return jsonify({'error': 'An error occurred during summary generation.'}), 500

@main.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-doctransform',
        'version': '1.0.0'
    }), 200
