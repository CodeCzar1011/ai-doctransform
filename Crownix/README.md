# AI DocTransform - Document AI Assistant

A full-stack web application that allows users to upload documents (PDF, DOCX, images), extract content, and get AI-powered insights using OpenAI's GPT models.

## Features

- **Document Upload**: Support for PDF, DOCX, DOC, and various image formats (PNG, JPG, JPEG, GIF, BMP, TIFF)
- **Text Extraction**: Automatic text extraction using specialized libraries (pdfplumber, python-docx, pytesseract)
- **AI Processing**: OpenAI GPT integration for document analysis, summarization, and editing suggestions
- **Modern UI**: Clean, responsive interface built with Bootstrap
- **Real-time Processing**: Immediate feedback and loading states

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Document Processing**: pdfplumber, python-docx, pytesseract, Pillow
- **AI**: OpenAI GPT-3.5-turbo
- **File Handling**: Werkzeug

## Installation & Setup

### 1. Prerequisites

- Python 3.8 or higher
- Tesseract OCR (for image text extraction)
- OpenAI API key

### 2. Install Tesseract OCR

**Windows:**
```bash
# Download and install from: https://github.com/UB-Mannheim/tesseract/wiki
# Add to PATH: C:\Program Files\Tesseract-OCR
```

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Setup Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure OpenAI API

Set your OpenAI API key as an environment variable:

**Windows:**
```bash
set OPENAI_API_KEY=your-api-key-here
```

**macOS/Linux:**
```bash
export OPENAI_API_KEY=your-api-key-here
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## API Endpoints

### 1. File Upload (`POST /upload`)

Upload a document and extract its text content.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: File in `file` field

**Response:**
```json
{
  "success": true,
  "message": "File uploaded and processed successfully",
  "file_info": {
    "filename": "document.pdf",
    "unique_filename": "uuid_document.pdf",
    "file_path": "uploads/uuid_document.pdf",
    "file_extension": "pdf",
    "extracted_text": "Extracted text content...",
    "upload_time": "2024-01-01T12:00:00"
  }
}
```

### 2. AI Processing (`POST /webhook`)

Send a query about the document content.

**Request:**
```json
{
  "query": "Summarize this document",
  "document_text": "Document content here..."
}
```

**Response:**
```json
{
  "success": true,
  "response": {
    "Summary": "Brief summary of the document",
    "EditsApplied": ["Suggested edit 1", "Suggested edit 2"],
    "ConvertedFileLink": "Description of converted format",
    "Answer": "Detailed answer to the query"
  },
  "raw_ai_response": "Raw AI response text"
}
```

### 3. Health Check (`GET /health`)

Check application status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00"
}
```

## Testing the Application

### 1. Using the Web Interface

1. Open `http://localhost:5000` in your browser
2. Upload a document (PDF, DOCX, or image)
3. View the extracted text
4. Enter a query about the document
5. Get AI-powered response

### 2. Testing with cURL

**Upload a file:**
```bash
curl -X POST -F "file=@sample.pdf" http://localhost:5000/upload
```

**Send a query:**
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize this document",
    "document_text": "Your document text here..."
  }' \
  http://localhost:5000/webhook
```

**Health check:**
```bash
curl http://localhost:5000/health
```

### 3. Testing with Postman

1. **Upload File:**
   - Method: `POST`
   - URL: `http://localhost:5000/upload`
   - Body: `form-data`
   - Key: `file` (Type: File)
   - Value: Select your document

2. **Send Query:**
   - Method: `POST`
   - URL: `http://localhost:5000/webhook`
   - Headers: `Content-Type: application/json`
   - Body: `raw` (JSON)
   ```json
   {
     "query": "Summarize this document",
     "document_text": "Your document text here..."
   }
   ```

## Exposing Locally with ngrok (for HackRx)

### 1. Install ngrok

Download from: https://ngrok.com/download

### 2. Start your Flask application

```bash
python app.py
```

### 3. Expose with ngrok

```bash
ngrok http 5000
```

### 4. Use the ngrok URL

ngrok will provide a public URL like: `https://abc123.ngrok.io`

### 5. Test the public endpoint

```bash
# Test health endpoint
curl https://abc123.ngrok.io/health

# Test upload (replace with your ngrok URL)
curl -X POST -F "file=@sample.pdf" https://abc123.ngrok.io/upload
```

## Sample Queries

Here are some example queries you can try:

1. **Summarization:**
   - "Summarize this document in 3 bullet points"
   - "Provide a brief overview of the main topics"

2. **Format Conversion:**
   - "Convert this content into a professional email format"
   - "Transform this into bullet points"

3. **Editing Suggestions:**
   - "Identify and suggest improvements for grammar and clarity"
   - "Find any spelling errors and suggest corrections"

4. **Content Analysis:**
   - "Extract key points and create a table of contents"
   - "What are the main arguments presented in this document?"

## File Structure

```
HackerX/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main web interface
├── static/               # Static assets (CSS, JS, images)
├── uploads/              # Uploaded files (created automatically)
└── utiles/               # Utility functions
```

## Troubleshooting

### Common Issues

1. **Tesseract not found:**
   - Ensure Tesseract is installed and in your PATH
   - Windows: Add `C:\Program Files\Tesseract-OCR` to PATH

2. **OpenAI API errors:**
   - Verify your API key is set correctly
   - Check your OpenAI account has sufficient credits

3. **File upload errors:**
   - Ensure file size is under 16MB
   - Check file format is supported

4. **Port already in use:**
   - Change port in `app.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`

### Error Messages

- `"No file provided"`: No file was selected for upload
- `"File type not allowed"`: Unsupported file format
- `"OpenAI API key not configured"`: Set OPENAI_API_KEY environment variable
- `"Upload failed"`: Check file size and format

## Future Enhancements

- [ ] Download button for AI-edited or converted files
- [ ] Hindi/regional language support
- [ ] Memory of previous queries
- [ ] PDF to DOCX conversion using pandoc
- [ ] Batch file processing
- [ ] User authentication
- [ ] File storage in cloud (AWS S3, Google Cloud Storage)

## License

This project is created for HackRx submission and educational purposes.

## Support

For issues and questions, please check the troubleshooting section or create an issue in the repository. 