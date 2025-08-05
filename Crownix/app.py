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

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'

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
    """Extract text from PDF using pdfplumber"""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
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
        
        # Extract text
        extracted_text = extract_text_from_file(file_path, file_extension)
        
        # Store file info in session or return with response
        file_info = {
            'filename': filename,
            'unique_filename': unique_filename,
            'file_path': file_path,
            'file_extension': file_extension,
            'extracted_text': extracted_text,
            'upload_time': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'file_info': file_info
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
    
    if not user_query or not document_text:
        return jsonify({'error': 'Both query and document_text are required'}), 400
    
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
        
        return jsonify({
            'success': True,
            'response': parsed_response,
            'raw_ai_response': ai_response
        })
    except Exception as e:
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
    app.run(debug=True, host='0.0.0.0', port=5000)
