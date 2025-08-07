# AI DocTransform

AI DocTransform is a smart document converter and query assistant that leverages AI to understand, edit, and convert documents (PDF, DOCX, images, etc.).

## Features

- Multi-format document upload (PDF, DOCX, images)
- AI-powered question answering about document content
- Chat-based document editing
- Document format conversion
- Structured JSON output
- Multilingual support

## Tech Stack

- Frontend: HTML/CSS/JS with Bootstrap
- Backend: Python with Flask
- AI: OpenAI/Gemini Pro
- File Processing: PyMuPDF, pdfplumber, python-docx, Tesseract OCR
- Conversion: Pandoc, PDFKit

## Recent Improvements

- Enhanced AI accuracy and performance for document analysis and Q&A
- Fixed dependency version compatibility issues (pandas, pandoc, lxml, PyMuPDF)
- Resolved import structure issues for proper deployment
- Updated project structure for better maintainability

## Deployment

The application is deployed on Render.com and is accessible at: https://ai-doctransform.onrender.com

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run the application: `python app.py`
