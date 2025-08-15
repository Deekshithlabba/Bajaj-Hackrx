#!/usr/bin/env python3
"""
Quick test for fixed rate limiting
"""
import os
import time
from gemini_api_manager import GeminiAPIManager

def test_fixed_rate_limiting():
    print("🧪 Testing Fixed Rate Limiting")
    print("=" * 40)
    
    # Set quota bypass
    os.environ['DISABLE_QUOTA_CHECK'] = 'true'
    
    api_manager = GeminiAPIManager()
    
    print("Testing 10 quick embedding calls...")
    start_time = time.time()
    
    for i in range(10):
        try:
            print(f"Call {i+1}/10: ", end="", flush=True)
            embedding = api_manager.generate_embeddings([f"Test text {i}"])
            print(f"✅ Success ({len(embedding[0])}D)")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    total_time = time.time() - start_time
    print(f"\n📊 Results:")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Average per call: {total_time/10:.1f} seconds")
    print(f"Expected for 766 chunks: {(total_time/10)*766/60:.1f} minutes")

if __name__ == "__main__":
    test_fixed_rate_limiting()