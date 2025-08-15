#!/usr/bin/env python3
"""
Debug script to check current quota usage and test embedding generation
"""

import os
import sys
from datetime import datetime
from gemini_api_manager import GeminiAPIManager
from config import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def check_quota_status():
    """Check current quota status and test basic functionality"""
    print("🔍 QUOTA DEBUG TOOL")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Check:")
    embedding_key = os.getenv("GEMINI_EMBEDDING_API_KEY")
    master_key = os.getenv("GEMINI_API_KEY")
    
    print(f"GEMINI_EMBEDDING_API_KEY: {'✅ Set' if embedding_key else '❌ Missing'}")
    print(f"GEMINI_API_KEY (fallback): {'✅ Set' if master_key else '❌ Missing'}")
    print(f"Using key: {embedding_key[:20] + '...' if embedding_key else master_key[:20] + '...' if master_key else 'None'}")
    print()
    
    # Check configuration
    print("⚙️ Configuration:")
    print(f"Embedding model: {config.EMBEDDING_MODEL}")
    print(f"Daily quota limit: {config.EMBEDDING_DAILY_QUOTA}")
    print(f"Batch size: {config.EMBEDDING_BATCH_SIZE}")
    print()
    
    # Initialize API manager
    print("🚀 Initializing API Manager...")
    try:
        api_manager = GeminiAPIManager()
        print("✅ API Manager initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize API Manager: {e}")
        return False
    
    # Check daily usage
    print("\n📊 Daily Usage Check:")
    used_key = embedding_key or master_key
    if used_key:
        current_usage = api_manager.daily_usage[used_key]
        remaining = config.EMBEDDING_DAILY_QUOTA - current_usage
        
        print(f"Today's usage: {current_usage}/{config.EMBEDDING_DAILY_QUOTA}")
        print(f"Remaining quota: {remaining}")
        print(f"Last reset date: {api_manager.last_reset_date}")
        print(f"Current date: {datetime.now().date()}")
    
    # Test single embedding
    print("\n🧪 Testing Single Embedding:")
    try:
        test_text = "This is a test document for quota checking."
        print(f"Generating embedding for: '{test_text}'")
        
        embeddings = api_manager.generate_embeddings([test_text])
        
        if embeddings and len(embeddings) > 0:
            print(f"✅ Embedding generated successfully!")
            print(f"Embedding dimensions: {len(embeddings[0])}")
            print(f"First few values: {embeddings[0][:5]}")
            
            # Check updated usage
            updated_usage = api_manager.daily_usage[used_key]
            print(f"Updated daily usage: {updated_usage}/{config.EMBEDDING_DAILY_QUOTA}")
            
        else:
            print("❌ No embedding returned")
            
    except Exception as e:
        print(f"❌ Embedding test failed: {e}")
        return False
    
    print("\n✅ All tests completed!")
    return True

if __name__ == "__main__":
    success = check_quota_status()
    sys.exit(0 if success else 1)