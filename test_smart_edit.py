"""Test script for smart_edit_content method"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from Crownix.document_processor import DocumentProcessor
import os

def test_smart_edit():
    # Get the Gemini API key from environment variables or use a placeholder for testing
    gemini_api_key = os.getenv('GEMINI_API_KEY', 'placeholder-key-for-testing')
    if not gemini_api_key or gemini_api_key == 'placeholder-key-for-testing':
        print("Warning: Using placeholder API key for testing")
    
    # Create a document processor instance
    processor = DocumentProcessor(gemini_api_key)
    
    # Test document text
    document_text = """This is a sample document for testing the smart edit functionality. 
    It contains several sentences that we can use to verify the editing capabilities.
    The document should be edited according to the instructions provided."""
    
    # Test edit instruction
    edit_instruction = "Make the language more formal and professional"
    
    # Test the smart_edit_content method
    result = processor.smart_edit_content(document_text, edit_instruction)
    
    # Print the result
    print("Smart Edit Result:")
    print(f"Success: {result.get('success', False)}")
    if result.get('success'):
        print(f"Edited Content: {result.get('edited_content', '')}")
        print(f"Changes Made: {result.get('changes_made', [])}")
        print(f"Confidence: {result.get('confidence', 0)}")
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")
        # Print more details about the error
        if 'suggested_next_steps' in result:
            print("Suggested next steps:")
            for step in result['suggested_next_steps']:
                print(f"  - {step}")

if __name__ == "__main__":
    test_smart_edit()
