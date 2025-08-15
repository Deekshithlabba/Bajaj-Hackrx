#!/usr/bin/env python3
"""
Test script for single document processing with detailed logging
"""

import os
import sys
import requests
import json
import logging

# Enable detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_single_document():
    """Test processing a single document with a single question"""
    
    print("🧪 TESTING SINGLE DOCUMENT PROCESSING")
    print("=" * 50)
    
    # Test payload
    test_data = {
        "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        "questions": [
            "What is the grace period for premium payment?"
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer hackrx_test_token_12345678"
    }
    
    print("📋 Test Configuration:")
    print(f"Document: policy.pdf (from Azure Blob)")
    print(f"Questions: 1 question only")
    print(f"Quota check disabled: {os.getenv('DISABLE_QUOTA_CHECK', 'false')}")
    print()
    
    try:
        print("🚀 Starting API request...")
        response = requests.post(
            "http://localhost:8000/hackrx/run",
            headers=headers,
            json=test_data,
            timeout=300  # 5 minute timeout
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS! Document processed successfully")
            print(f"Processing time: {result.get('processing_stats', {}).get('processing_time', 'unknown')} seconds")
            print(f"Total chunks: {result.get('processing_stats', {}).get('total_chunks', 'unknown')}")
            
            if 'questions' in result and len(result['questions']) > 0:
                answer = result['questions'][0].get('answer', 'No answer')
                confidence = result['questions'][0].get('confidence', 'unknown')
                print(f"Answer: {answer[:200]}...")
                print(f"Confidence: {confidence}")
            
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>5 minutes)")
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error - is the server running?")
        print("Start server with: python main.py")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    # Check if server is running
    try:
        health_check = requests.get("http://localhost:8000/", timeout=5)
        print("✅ Server is running")
    except:
        print("❌ Server not running. Start with: python main.py")
        sys.exit(1)
    
    test_single_document()