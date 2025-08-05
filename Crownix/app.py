import os
import json
import base64
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import pdfplumber
from docx import Document
import pytesseract
from PIL import Image
import io
from datetime import datetime
import uuid

# Database imports
from models import db, User, Document as DocumentModel, ProcessingJob, APIUsage
from database import init_database, create_tables

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Initialize database
db_instance, migrate = init_database(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF using pdfplumber with enhanced accuracy"""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                # Try multiple extraction methods for better accuracy
                page_text = page.extract_text()
                
                # If standard extraction fails, try with different settings
                if not page_text or len(page_text.strip()) < 10:
                    # Try with different extraction settings
                    page_text = page.extract_text(
                        x_tolerance=3,
                        y_tolerance=3,
                        layout=True,
                        x_density=7.25,
                        y_density=13
                    )
                
                # If still no text, try extracting from tables
                if not page_text or len(page_text.strip()) < 10:
                    tables = page.extract_tables()
                    if tables:
                        table_text = ""
                        for table in tables:
                            for row in table:
                                if row:
                                    table_text += " ".join([cell or "" for cell in row]) + "\n"
                        page_text = table_text
                
                if page_text:
                    # Clean and normalize the text
                    page_text = clean_extracted_text(page_text)
                    text += f"\n--- Page {page_num} ---\n{page_text}\n"
        
        return text.strip() if text.strip() else "No text could be extracted from this PDF."
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"

def extract_text_from_docx(file_path):
    """Extract text from DOCX using python-docx"""
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text from DOCX: {str(e)}"

def extract_text_from_image(file_path):
    """Extract text from image using pytesseract"""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        return f"Error extracting text from image: {str(e)}"

def extract_text_from_file(file_path, file_extension):
    """Extract text based on file type"""
    if file_extension.lower() == 'pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension.lower() in ['docx', 'doc']:
        return extract_text_from_docx(file_path)
    elif file_extension.lower() in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
        return extract_text_from_image(file_path)
    else:
        return "Unsupported file format"

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get all documents with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        documents = DocumentModel.query.order_by(DocumentModel.upload_time.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': documents.total,
                'pages': documents.pages
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch documents: {str(e)}'}), 500

@app.route('/api/documents/<document_uuid>', methods=['GET'])
def get_document(document_uuid):
    """Get a specific document by UUID"""
    try:
        document = DocumentModel.query.filter_by(uuid=document_uuid).first()
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify({
            'success': True,
            'document': document.to_dict(),
            'extracted_text': document.extracted_text
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch document: {str(e)}'}), 500

@app.route('/api/processing-jobs', methods=['GET'])
def get_processing_jobs():
    """Get processing jobs with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')  # Optional status filter
        
        query = ProcessingJob.query
        if status:
            query = query.filter_by(status=status)
        
        jobs = query.order_by(ProcessingJob.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': jobs.total,
                'pages': jobs.pages
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch processing jobs: {str(e)}'}), 500

@app.route('/api/processing-jobs/<job_uuid>', methods=['GET'])
def get_processing_job(job_uuid):
    """Get a specific processing job by UUID"""
    try:
        job = ProcessingJob.query.filter_by(uuid=job_uuid).first()
        if not job:
            return jsonify({'error': 'Processing job not found'}), 404
        
        return jsonify({
            'success': True,
            'job': job.to_dict(),
            'input_text': job.input_text,
            'output_text': job.output_text
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch processing job: {str(e)}'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get application statistics"""
    try:
        total_documents = DocumentModel.query.count()
        total_jobs = ProcessingJob.query.count()
        completed_jobs = ProcessingJob.query.filter_by(status='completed').count()
        failed_jobs = ProcessingJob.query.filter_by(status='failed').count()
        
        # Get recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_documents = DocumentModel.query.filter(DocumentModel.upload_time >= week_ago).count()
        recent_jobs = ProcessingJob.query.filter(ProcessingJob.created_at >= week_ago).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_documents': total_documents,
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'success_rate': (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                'recent_documents': recent_documents,
                'recent_jobs': recent_jobs
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch stats: {str(e)}'}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and text extraction"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        file_extension = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Extract text
        extracted_text = extract_text_from_file(file_path, file_extension)
        
        # Create document record in database
        document = DocumentModel(
            original_filename=filename,
            unique_filename=unique_filename,
            file_path=file_path,
            file_extension=file_extension,
            file_size=file_size,
            mime_type=file.content_type,
            extracted_text=extracted_text,
            extraction_status='completed' if extracted_text else 'failed',
            processed_at=datetime.utcnow()
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Return response with document info
        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'document': document.to_dict(),
            'extracted_text': extracted_text
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle AI processing requests"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    user_query = data.get('query', '')
    document_text = data.get('document_text', '')
    document_id = data.get('document_id')  # Optional document ID
    job_type = data.get('job_type', 'general_query')  # Type of processing
    
    if not user_query or not document_text:
        return jsonify({'error': 'Both query and document_text are required'}), 400
    
    # Create processing job record
    processing_job = ProcessingJob(
        job_type=job_type,
        input_text=f"Query: {user_query}\n\nDocument: {document_text[:1000]}...",  # Truncate for storage
        document_id=document_id,
        started_at=datetime.utcnow()
    )
    
    db.session.add(processing_job)
    db.session.commit()
    
    # Prepare the prompt for Gemini
    system_prompt = "You are an AI document assistant. You can: Summarize documents, suggest edits and improvements, convert content to different formats, and answer questions about the document content. Please provide your response in the following JSON format: {\"Summary\": \"Brief summary of the document or response to query\", \"EditsApplied\": [\"List of suggested edits or improvements\"], \"ConvertedFileLink\": \"If applicable, describe the converted format\", \"Answer\": \"Detailed answer to the user's query\"}"
    
    user_prompt = f"Document Content:\n{document_text}\n\nUser Query: {user_query}\n\nPlease analyze the document and respond to the user's query."
    
    payload = {
        "contents": [
            {"parts": [{"text": system_prompt + "\n" + user_prompt}]}
        ]
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "key": GEMINI_API_KEY
    }
    
    try:
        start_time = datetime.utcnow()
        gemini_response = requests.post(GEMINI_API_URL, params=params, headers=headers, data=json.dumps(payload))
        gemini_response.raise_for_status()
        result = gemini_response.json()
        ai_response = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        # Try to parse as JSON, if not, format it
        try:
            parsed_response = json.loads(ai_response)
        except Exception:
            parsed_response = {
                "Summary": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
                "EditsApplied": [],
                "ConvertedFileLink": "",
                "Answer": ai_response
            }
        
        # Update processing job with results
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        processing_job.status = 'completed'
        processing_job.output_text = ai_response
        processing_job.completed_at = end_time
        processing_job.processing_time = processing_time
        
        # Track API usage
        api_usage = APIUsage(
            processing_job_id=processing_job.id,
            api_provider='gemini',
            api_model='gemini-pro',
            input_tokens=len(user_prompt.split()),  # Rough estimate
            output_tokens=len(ai_response.split()),  # Rough estimate
            total_tokens=len(user_prompt.split()) + len(ai_response.split()),
            timestamp=end_time,
            response_time=processing_time
        )
        
        db.session.add(api_usage)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'response': parsed_response,
            'raw_ai_response': ai_response,
            'processing_job_id': processing_job.uuid
        })
    except Exception as e:
        # Update processing job with error
        processing_job.status = 'failed'
        processing_job.error_message = str(e)
        processing_job.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'error': f'Gemini API request failed: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download processed files"""
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    except Exception as e:
        return jsonify({'error': f'Download failed: {str(e)}'}), 404

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Placeholder login route
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Placeholder signup route
    return render_template('signup.html')

@app.route('/logout')
def logout():
    # Placeholder logout route
    return render_template('index.html')

if __name__ == '__main__':
    # Initialize database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully!")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
