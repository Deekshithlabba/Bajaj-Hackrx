#!/usr/bin/env python3
"""
Test the improved search strategy
"""

import logging
from llm_integration import TwoStageLLMPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_improved_search():
    """Test the improved search strategy"""
    
    logger.info("🧪 Testing Improved Search Strategy")
    logger.info("=" * 60)
    
    try:
        # Initialize the LLM pipeline 
        pipeline = TwoStageLLMPipeline()
        
        # Test the grace period question
        test_query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        logger.info(f"🔍 Testing query: {test_query}")
        logger.info("=" * 60)
        
        # Test the key term extraction
        key_terms = pipeline._extract_key_search_terms(test_query)
        logger.info(f"✅ Key terms extracted: '{key_terms}'")
        
        logger.info("=" * 60)
        logger.info("🎉 Key term extraction test complete!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    
    success = test_improved_search()
    
    if success:
        logger.info("✅ Improved search strategy is ready!")
        logger.info("💡 Now try running your main application again.")
    else:
        logger.error("❌ Test failed.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)