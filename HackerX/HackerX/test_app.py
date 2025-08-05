#!/usr/bin/env python3
"""
Test script for AI DocTransform application
"""

import requests
import json
import os
import sys

BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_webhook():
    """Test webhook endpoint with sample data"""
    print("\nTesting webhook endpoint...")
    
    sample_data = {
        "query": "Summarize this document in 2 sentences",
        "document_text": "This is a sample document for testing purposes. It contains some text that can be analyzed by the AI assistant. The document discusses various topics and provides information for processing."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhook",
            headers={"Content-Type": "application/json"},
            data=json.dumps(sample_data)
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Webhook test passed")
                print(f"Response: {json.dumps(data['response'], indent=2)}")
                return True
            else:
                print(f"❌ Webhook failed: {data.get('error')}")
                return False
        else:
            print(f"❌ Webhook HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return False

def test_upload_without_file():
    """Test upload endpoint without file (should fail)"""
    print("\nTesting upload endpoint without file...")
    
    try:
        response = requests.post(f"{BASE_URL}/upload")
        if response.status_code == 400:
            data = response.json()
            if "No file provided" in data.get('error', ''):
                print("✅ Upload validation working correctly")
                return True
            else:
                print(f"❌ Unexpected error: {data.get('error')}")
                return False
        else:
            print(f"❌ Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Upload test error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing AI DocTransform Application")
    print("=" * 50)
    
    # Check if server is running
    if not test_health():
        print("\n❌ Server is not running. Please start the Flask app first:")
        print("   python app.py")
        sys.exit(1)
    
    # Test webhook
    webhook_success = test_webhook()
    
    # Test upload validation
    upload_success = test_upload_without_file()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"Health Check: ✅")
    print(f"Webhook Test: {'✅' if webhook_success else '❌'}")
    print(f"Upload Validation: {'✅' if upload_success else '❌'}")
    
    if webhook_success and upload_success:
        print("\n🎉 All tests passed! Your application is working correctly.")
        print("\nNext steps:")
        print("1. Open http://localhost:5000 in your browser")
        print("2. Upload a document and test the full workflow")
        print("3. Use ngrok to expose your app: ngrok http 5000")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        if not webhook_success:
            print("   - Make sure OPENAI_API_KEY is set")
        sys.exit(1)

if __name__ == "__main__":
    main() 