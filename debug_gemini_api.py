#!/usr/bin/env python3
"""
Debug Gemini API Response Issues
Test what the Gemini API is actually returning
"""

import logging
from gemini_api_manager import gemini_api_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_api():
    """Test Gemini API responses"""
    
    logger.info("🧪 Testing Gemini API Responses")
    logger.info("=" * 50)
    
    try:
        # Test simple prompt first
        simple_prompt = """You are a helpful assistant. Respond with valid JSON only.

{
    "test": "success",
    "message": "This is a test response"
}

Respond with valid JSON only."""
        
        logger.info("🔍 Testing simple JSON prompt...")
        response = gemini_api_manager.analyze_task(simple_prompt)
        logger.info(f"📝 Simple response: {response}")
        logger.info(f"📏 Response length: {len(response) if response else 0}")
        logger.info(f"🔤 Response type: {type(response)}")
        
        if response:
            logger.info(f"📋 First 500 chars: {response[:500]}")
        
        logger.info("=" * 50)
        
        # Test simplified domain analysis prompt
        domain_prompt = """Look at this document sample:

DOCUMENT SAMPLE:
- Content Type: text
- Content: This insurance policy covers premium payments and grace periods for medical coverage.

Based on this sample:
1. What domain is this? (insurance, medical, legal, financial, etc.)
2. Create 3 example question-answer pairs that show how to answer questions in this domain

Please respond in JSON format like this:
{
    "domain": "insurance",
    "query_type": "factual",
    "few_shot_prompts": [
        {
            "example_question": "What is a grace period?",
            "example_answer": "A grace period is the time allowed after a premium due date...",
            "pattern_explanation": "Clear definition with context"
        }
    ],
    "confidence": 0.8,
    "reasoning": "Domain analysis based on document content"
}"""
        
        logger.info("🔍 Testing domain analysis prompt...")
        domain_response = gemini_api_manager.analyze_task(domain_prompt)
        logger.info(f"📝 Domain response: {domain_response}")
        
        if domain_response:
            logger.info(f"📋 First 500 chars: {domain_response[:500]}")
            
            # Try to parse as JSON
            import json
            try:
                parsed = json.loads(domain_response)
                logger.info(f"✅ JSON parsing successful: {parsed}")
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed: {e}")
        
        logger.info("=" * 50)
        logger.info("🎉 Gemini API debugging complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Gemini API test failed: {e}")
        return False

def main():
    """Main test function"""
    
    logger.info("🚀 Starting Gemini API Debugging")
    
    success = test_gemini_api()
    
    if success:
        logger.info("✅ Debugging completed. Check the logs above for response details.")
    else:
        logger.error("❌ Debugging failed. Check your API configuration.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)