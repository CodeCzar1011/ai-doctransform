"""
Advanced Document Processing Service
Handles AI-powered Q&A, smart editing, format conversion, and structured JSON output
"""

import os
import json
import io
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

# File processing imports
import pdfplumber
from docx import Document as DocxDocument
from docx.shared import Inches
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import pandas as pd
from openpyxl import Workbook
import csv

# Format conversion imports
import markdown
import html2text
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from fpdf import FPDF
import weasyprint

# AI and web imports
import requests
from bs4 import BeautifulSoup

# Database imports
from models import db, DocumentModel, ProcessingJob

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Advanced document processing with AI capabilities"""
    
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        
    def extract_enhanced_text(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """Enhanced text extraction with metadata"""
        try:
            result = {
                'text': '',
                'metadata': {},
                'structure': {},
                'success': True,
                'error': None
            }
            
            if file_type.lower() == 'pdf':
                result = self._extract_pdf_enhanced(file_path)
            elif file_type.lower() in ['docx', 'doc']:
                result = self._extract_docx_enhanced(file_path)
            elif file_type.lower() in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']:
                result = self._extract_image_enhanced(file_path)
            else:
                result['success'] = False
                result['error'] = f"Unsupported file type: {file_type}"
                
            return result
            
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return {
                'text': '',
                'metadata': {},
                'structure': {},
                'success': False,
                'error': str(e)
            }
    
    def _extract_pdf_enhanced(self, file_path: str) -> Dict[str, Any]:
        """Enhanced PDF extraction with structure analysis"""
        text = ""
        metadata = {}
        structure = {'pages': [], 'tables': [], 'images': []}
        
        # Using PyMuPDF for enhanced extraction
        doc = fitz.open(file_path)
        metadata = {
            'page_count': doc.page_count,
            'title': doc.metadata.get('title', ''),
            'author': doc.metadata.get('author', ''),
            'subject': doc.metadata.get('subject', ''),
            'creator': doc.metadata.get('creator', ''),
            'creation_date': doc.metadata.get('creationDate', ''),
            'modification_date': doc.metadata.get('modDate', '')
        }
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text()
            text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            # Extract page structure
            page_info = {
                'page_number': page_num + 1,
                'text_length': len(page_text),
                'has_images': len(page.get_images()) > 0,
                'image_count': len(page.get_images())
            }
            structure['pages'].append(page_info)
            
            # Extract images info
            for img_index, img in enumerate(page.get_images()):
                structure['images'].append({
                    'page': page_num + 1,
                    'index': img_index,
                    'xref': img[0]
                })
        
        doc.close()
        
        # Also try pdfplumber for table extraction
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    if tables:
                        for table_index, table in enumerate(tables):
                            structure['tables'].append({
                                'page': page_num + 1,
                                'table_index': table_index,
                                'rows': len(table),
                                'columns': len(table[0]) if table else 0
                            })
        except Exception as e:
            logger.warning(f"Table extraction failed: {str(e)}")
        
        return {
            'text': text,
            'metadata': metadata,
            'structure': structure,
            'success': True,
            'error': None
        }
    
    def _extract_docx_enhanced(self, file_path: str) -> Dict[str, Any]:
        """Enhanced DOCX extraction with structure analysis"""
        doc = DocxDocument(file_path)
        text = ""
        structure = {'paragraphs': [], 'tables': [], 'images': []}
        
        # Extract paragraphs with style info
        for para_index, paragraph in enumerate(doc.paragraphs):
            para_text = paragraph.text
            text += para_text + "\n"
            
            structure['paragraphs'].append({
                'index': para_index,
                'text_length': len(para_text),
                'style': paragraph.style.name if paragraph.style else 'Normal'
            })
        
        # Extract tables
        for table_index, table in enumerate(doc.tables):
            structure['tables'].append({
                'index': table_index,
                'rows': len(table.rows),
                'columns': len(table.columns)
            })
            
            # Add table text to main text
            text += f"\n--- Table {table_index + 1} ---\n"
            for row in table.rows:
                row_text = " | ".join([cell.text for cell in row.cells])
                text += row_text + "\n"
        
        # Basic metadata
        metadata = {
            'paragraph_count': len(doc.paragraphs),
            'table_count': len(doc.tables),
            'title': doc.core_properties.title or '',
            'author': doc.core_properties.author or '',
            'subject': doc.core_properties.subject or '',
            'created': str(doc.core_properties.created) if doc.core_properties.created else '',
            'modified': str(doc.core_properties.modified) if doc.core_properties.modified else ''
        }
        
        return {
            'text': text,
            'metadata': metadata,
            'structure': structure,
            'success': True,
            'error': None
        }
    
    def _extract_image_enhanced(self, file_path: str) -> Dict[str, Any]:
        """Enhanced image OCR with metadata"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            
            metadata = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height
            }
            
            # Get OCR confidence data
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidence_scores = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            structure = {
                'ocr_confidence': avg_confidence,
                'word_count': len([word for word in ocr_data['text'] if word.strip()]),
                'detected_languages': 'eng'  # Default, could be enhanced
            }
            
            return {
                'text': text,
                'metadata': metadata,
                'structure': structure,
                'success': True,
                'error': None
            }
            
        except Exception as e:
            return {
                'text': '',
                'metadata': {},
                'structure': {},
                'success': False,
                'error': str(e)
            }
    
    def ai_question_answer(self, document_text: str, question: str, context: Dict = None) -> Dict[str, Any]:
        """AI-powered Q&A on document content"""
        try:
            # Prepare the prompt
            system_prompt = """You are an AI assistant specialized in analyzing and answering questions about document content. 
            Provide accurate, helpful, and contextual answers based on the document provided. 
            If the answer cannot be found in the document, clearly state that."""
            
            user_prompt = f"""Document Content:
{document_text[:8000]}  # Limit for API

Question: {question}

Please provide a comprehensive answer based on the document content above."""
            
            # Call Gemini API
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"{system_prompt}\n\n{user_prompt}"
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.gemini_api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['candidates'][0]['content']['parts'][0]['text']
                
                return {
                    'success': True,
                    'answer': answer,
                    'question': question,
                    'confidence': 'high',  # Could be enhanced with confidence scoring
                    'sources': 'document_content',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}",
                    'question': question
                }
                
        except Exception as e:
            logger.error(f"Error in AI Q&A: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'question': question
            }
    
    def smart_edit_content(self, document_text: str, edit_instruction: str) -> Dict[str, Any]:
        """AI-powered smart editing (rephrase, summarize, change tone, etc.)"""
        try:
            system_prompt = """You are an expert content editor. You can rephrase, summarize, change tone, 
            fix grammar, restructure, and perform various editing tasks on documents. 
            Always maintain the core meaning while applying the requested changes."""
            
            user_prompt = f"""Original Content:
{document_text[:6000]}  # Limit for API

Edit Instruction: {edit_instruction}

Please apply the requested editing changes and return the modified content."""
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"{system_prompt}\n\n{user_prompt}"
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.gemini_api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                edited_content = result['candidates'][0]['content']['parts'][0]['text']
                
                return {
                    'success': True,
                    'original_content': document_text,
                    'edited_content': edited_content,
                    'edit_instruction': edit_instruction,
                    'changes_made': 'AI-powered editing applied',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}",
                    'edit_instruction': edit_instruction
                }
                
        except Exception as e:
            logger.error(f"Error in smart editing: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'edit_instruction': edit_instruction
            }
    
    def convert_document_format(self, content: str, source_format: str, target_format: str, 
                              metadata: Dict = None) -> Dict[str, Any]:
        """Convert document to different formats"""
        try:
            if target_format.lower() == 'json':
                return self._convert_to_json(content, metadata)
            elif target_format.lower() == 'pdf':
                return self._convert_to_pdf(content)
            elif target_format.lower() == 'docx':
                return self._convert_to_docx(content)
            elif target_format.lower() == 'markdown':
                return self._convert_to_markdown(content)
            elif target_format.lower() == 'html':
                return self._convert_to_html(content)
            elif target_format.lower() == 'txt':
                return self._convert_to_txt(content)
            else:
                return {
                    'success': False,
                    'error': f"Unsupported target format: {target_format}"
                }
                
        except Exception as e:
            logger.error(f"Error converting to {target_format}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _convert_to_json(self, content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Convert content to structured JSON"""
        # Parse content into structured format
        lines = content.split('\n')
        paragraphs = [line.strip() for line in lines if line.strip()]
        
        structured_data = {
            'document_info': {
                'total_characters': len(content),
                'total_words': len(content.split()),
                'total_paragraphs': len(paragraphs),
                'extraction_timestamp': datetime.utcnow().isoformat()
            },
            'metadata': metadata or {},
            'content': {
                'full_text': content,
                'paragraphs': paragraphs,
                'summary': content[:500] + '...' if len(content) > 500 else content
            }
        }
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(structured_data, temp_file, indent=2, ensure_ascii=False)
        temp_file.close()
        
        return {
            'success': True,
            'file_path': temp_file.name,
            'format': 'json',
            'data': structured_data
        }
    
    def _convert_to_pdf(self, content: str) -> Dict[str, Any]:
        """Convert content to PDF"""
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.close()
        
        # Create PDF using ReportLab
        doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                p = Paragraph(para.strip(), styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 12))
        
        doc.build(story)
        
        return {
            'success': True,
            'file_path': temp_file.name,
            'format': 'pdf'
        }
    
    def _convert_to_docx(self, content: str) -> Dict[str, Any]:
        """Convert content to DOCX"""
        doc = DocxDocument()
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                doc.add_paragraph(para.strip())
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.docx', delete=False)
        doc.save(temp_file.name)
        temp_file.close()
        
        return {
            'success': True,
            'file_path': temp_file.name,
            'format': 'docx'
        }
    
    def _convert_to_markdown(self, content: str) -> Dict[str, Any]:
        """Convert content to Markdown"""
        # Basic conversion - could be enhanced with structure detection
        markdown_content = content
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        temp_file.write(markdown_content)
        temp_file.close()
        
        return {
            'success': True,
            'file_path': temp_file.name,
            'format': 'markdown'
        }
    
    def _convert_to_html(self, content: str) -> Dict[str, Any]:
        """Convert content to HTML"""
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Converted Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        p {{ margin-bottom: 16px; }}
    </style>
</head>
<body>
"""
        
        # Convert paragraphs to HTML
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                html_content += f"    <p>{para.strip()}</p>\n"
        
        html_content += """</body>
</html>"""
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8')
        temp_file.write(html_content)
        temp_file.close()
        
        return {
            'success': True,
            'file_path': temp_file.name,
            'format': 'html'
        }
    
    def _convert_to_txt(self, content: str) -> Dict[str, Any]:
        """Convert content to plain text"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
        
        return {
            'success': True,
            'file_path': temp_file.name,
            'format': 'txt'
        }
    
    def generate_summary(self, content: str, summary_type: str = 'brief') -> Dict[str, Any]:
        """Generate AI-powered summary of document content"""
        try:
            if summary_type == 'brief':
                instruction = "Provide a brief summary (2-3 sentences) of the main points."
            elif summary_type == 'detailed':
                instruction = "Provide a detailed summary covering all major points and key details."
            elif summary_type == 'bullet':
                instruction = "Provide a bullet-point summary of the key points."
            else:
                instruction = "Provide a comprehensive summary of the content."
            
            system_prompt = f"""You are an expert at summarizing documents. {instruction}
            Focus on the most important information and maintain accuracy."""
            
            user_prompt = f"""Content to summarize:
{content[:7000]}  # Limit for API

Please provide the requested summary."""
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": f"{system_prompt}\n\n{user_prompt}"
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.gemini_api_url}?key={self.gemini_api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result['candidates'][0]['content']['parts'][0]['text']
                
                return {
                    'success': True,
                    'summary': summary,
                    'summary_type': summary_type,
                    'original_length': len(content),
                    'summary_length': len(summary),
                    'compression_ratio': len(summary) / len(content) if content else 0,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}",
                    'summary_type': summary_type
                }
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'summary_type': summary_type
            }
