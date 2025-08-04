#!/usr/bin/env python3
"""
Local API Testing Script for HackRx 6.0 Document Intelligence System

This script provides easy testing of the API with different scenarios.
Run this after starting the server with: python main.py
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_DOCUMENTS = [
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    "https://www.orimi.com/pdf-test.pdf"
]

def test_health_check():
    """Test basic health endpoints"""
    print("🏥 Testing Health Endpoints")
    print("-" * 40)
    
    # Root endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
    
    # Health endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        print(f"✅ Health endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
    
    print()

def test_api_with_key(api_key: str, test_name: str) -> Dict[str, Any]:
    """Test API with specific OpenAI API key"""
    print(f"🔑 Testing: {test_name}")
    print("-" * 40)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "documents": [TEST_DOCUMENTS[0]],  # Use first test document
        "questions": [
            "What is this document about?",
            "How many pages does it have?"
        ]
    }
    
    try:
        print(f"📤 Sending request with API key: {api_key[:15]}...")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/hackrx/run",
            headers=headers,
            json=payload,
            timeout=120  # 2 minutes timeout
        )
        end_time = time.time()
        
        print(f"⏱️  Request completed in: {end_time - start_time:.2f} seconds")
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Success!")
            print(f"   Request ID: {result.get('request_id', 'N/A')}")
            print(f"   Questions processed: {len(result.get('results', []))}")
            
            if result.get('results'):
                for i, res in enumerate(result['results']):
                    print(f"   Q{i+1}: {res.get('question', 'N/A')}")
                    print(f"       Answer: {res.get('answer', 'N/A')[:100]}...")
                    print(f"       Confidence: {res.get('confidence', 0):.2f}")
                    print(f"       Citations: {len(res.get('citations', []))}")
            
            if result.get('performance'):
                perf = result['performance']
                print(f"   Performance:")
                print(f"       Total time: {perf.get('total_processing_time', 0):.2f}s")
                print(f"       Tokens used: {perf.get('total_tokens_used', 0)}")
                print(f"       Estimated cost: ${perf.get('estimated_total_cost', 0):.3f}")
            
            return result
            
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error: {error_detail}")
            except:
                print(f"   Error: {response.text}")
            return {}
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>2 minutes)")
        return {}
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {}
    
    finally:
        print()

def test_authentication_scenarios():
    """Test different authentication scenarios"""
    print("🔐 Testing Authentication Scenarios")
    print("=" * 50)
    
    # Get OpenAI API key from user
    openai_key = input("Enter your OpenAI API key (or press Enter to skip): ").strip()
    
    if openai_key:
        # Test 1: Valid OpenAI API key
        test_api_with_key(openai_key, "Valid OpenAI API Key")
        
        # Wait a bit between requests
        time.sleep(2)
    
    # Test 2: Invalid API key (should fallback)
    test_api_with_key("invalid-key-12345-should-fallback", "Invalid Key (Fallback Test)")
    
    # Test 3: No authorization header
    print("🚫 Testing: No Authorization Header")
    print("-" * 40)
    try:
        response = requests.post(
            f"{API_BASE_URL}/hackrx/run",
            headers={"Content-Type": "application/json"},
            json={
                "documents": [TEST_DOCUMENTS[0]],
                "questions": ["What is this about?"]
            }
        )
        print(f"📊 Status Code: {response.status_code}")
        if response.status_code == 401:
            print("✅ Correctly rejected unauthorized request")
        else:
            print("❌ Should have returned 401 Unauthorized")
        print()
    except Exception as e:
        print(f"❌ Request failed: {e}")
        print()

def test_multiple_documents():
    """Test with multiple documents"""
    print("📚 Testing Multiple Documents")
    print("=" * 50)
    
    openai_key = input("Enter your OpenAI API key for multi-document test: ").strip()
    if not openai_key:
        print("⏭️  Skipping multi-document test (no API key provided)")
        return
    
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "documents": TEST_DOCUMENTS[:2],  # Use first two documents
        "questions": [
            "What are the main topics across these documents?",
            "How many total pages are there?",
            "What types of content are included?"
        ]
    }
    
    try:
        print("📤 Sending multi-document request...")
        start_time = time.time()
        
        response = requests.post(
            f"{API_BASE_URL}/hackrx/run",
            headers=headers,
            json=payload,
            timeout=300  # 5 minutes for multiple documents
        )
        
        end_time = time.time()
        print(f"⏱️  Multi-document request completed in: {end_time - start_time:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Multi-document processing successful!")
            print(f"   Documents processed: {len(payload['documents'])}")
            print(f"   Questions answered: {len(result.get('results', []))}")
            
            if result.get('processing_stats'):
                stats = result['processing_stats']
                print(f"   Processing stats:")
                print(f"       Documents processed: {stats.get('documents_processed', 0)}")
                print(f"       Total chunks: {stats.get('total_chunks_processed', 0)}")
                print(f"       Total tokens: {stats.get('total_tokens_used', 0)}")
        else:
            print(f"❌ Multi-document test failed: {response.status_code}")
            print(f"   Error: {response.text}")
    
    except Exception as e:
        print(f"❌ Multi-document test failed: {e}")
    
    print()

def main():
    """Run all tests"""
    print("🚀 HackRx 6.0 Document Intelligence API - Local Testing")
    print("=" * 60)
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Test Documents: {len(TEST_DOCUMENTS)} available")
    print()
    
    # Check if server is running
    try:
        response = requests.get(API_BASE_URL, timeout=5)
        print("✅ Server is running!")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")
        print("Please start the server with: python main.py")
        sys.exit(1)
    
    print()
    
    # Run tests
    test_health_check()
    test_authentication_scenarios()
    
    # Ask if user wants to test multiple documents
    if input("Test multiple documents? (y/n): ").lower().startswith('y'):
        test_multiple_documents()
    
    print("🎉 Testing completed!")
    print("\nNext steps:")
    print("1. Review the results above")
    print("2. Check server logs for detailed processing info")
    print("3. Test with your own documents and questions")
    print("4. Deploy to production when ready!")

if __name__ == "__main__":
    main()