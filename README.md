# AI DocTransform Webhook (FastAPI)

This is the basic webhook for the AI DocTransform project.  
It handles document upload, user queries, and returns a simulated AI response.

## 🔧 Tech Stack
- Python (FastAPI)
- File Upload & Save
- Mock JSON output (for HackRx submission)

## ✅ Features
- Accepts file + query
- Saves file to `/uploads/`
- Returns JSON with mock summary and edit info

---

## 🚀 Endpoint
### `POST /webhook/document`
**Parameters:**
- `file`: UploadFile (PDF, DOCX, JPG, PNG)
- `query`: Form input (string)

**Response:**
```json
{
  "Summary": "...",
  "EditsApplied": ["..."],
  "ConvertedFileLink": "..."
}
