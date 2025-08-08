"""API endpoints for insurance policy processing."""

from flask import Blueprint, request, jsonify, current_app
from Crownix.insurance_processor import InsurancePolicyProcessor
import logging

logger = logging.getLogger(__name__)

# Create blueprint
insurance_bp = Blueprint('insurance', __name__, url_prefix='/api/insurance')

@insurance_bp.route('/process', methods=['POST'])
def process_policy():
    """Process an insurance policy document and return structured data."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing document text'}), 400
            
        document_text = data['text']
        
        # Process the document
        processor = InsurancePolicyProcessor(document_text)
        structured_data = processor.get_structured_data()
        
        return jsonify({
            'success': True,
            'data': structured_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing insurance policy: {str(e)}")
        return jsonify({'error': 'Failed to process document', 'details': str(e)}), 500

@insurance_bp.route('/ask', methods=['POST'])
def ask_policy_question():
    """Answer questions about an insurance policy document."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data or 'question' not in data:
            return jsonify({'error': 'Missing document text or question'}), 400
            
        document_text = data['text']
        question = data['question']
        
        # Process the document and answer question
        processor = InsurancePolicyProcessor(document_text)
        answer = processor.answer_question(question)
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        }), 200
        
    except Exception as e:
        logger.error(f"Error answering insurance policy question: {str(e)}")
        return jsonify({'error': 'Failed to answer question', 'details': str(e)}), 500

@insurance_bp.route('/extract-sections', methods=['POST'])
def extract_policy_sections():
    """Extract sections from an insurance policy document."""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing document text'}), 400
            
        document_text = data['text']
        
        # Process the document
        processor = InsurancePolicyProcessor(document_text)
        sections = processor.sections
        
        return jsonify({
            'success': True,
            'sections': list(sections.keys()),
            'section_contents': sections
        }), 200
        
    except Exception as e:
        logger.error(f"Error extracting policy sections: {str(e)}")
        return jsonify({'error': 'Failed to extract sections', 'details': str(e)}), 500
