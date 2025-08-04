from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import shutil
import os

app = FastAPI(title="AI DocTransform Webhook")

# Enable CORS for frontend access (React or HTML)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Limit this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def root():
    return {"message": "Welcome to AI DocTransform Webhook – Basic Version"}

@app.post("/webhook/document")
async def upload_and_process_document(
    file: UploadFile = File(...),
    query: str = Form(...)
):
    """
    Accepts:
    - file: a document (PDF, DOCX, or image)
    - query: user instruction ("Summarize", "Convert", etc.)

    Returns:
    - Simulated JSON response for demo
    """

    # Save uploaded file
    file_id = str(uuid.uuid4())
    file_name = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🔧 TODO (for backend dev):
    # Integrate:
    # - OpenAI/Gemini for queries
    # - pdfplumber / python-docx for file reading
    # - Tesseract for image OCR
    # - Conversion using pdfkit / pandoc

    # Simulated response for demo/submission
    return JSONResponse(content={
        "Summary": "This document describes AI-based document interaction.",
        "EditsApplied": ["Changed tone to formal", "Grammar corrected"],
        "ConvertedFileLink": f"https://yourdomain.com/files/{file_name}"
    })
