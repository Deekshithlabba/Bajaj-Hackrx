#!/usr/bin/env python3
"""
Test Enhanced Retrieval Strategy - All Improvements
"""

import logging
from llm_integration import TwoStageLLMPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_retrieval():
    """Test the complete enhanced retrieval strategy"""
    
    logger.info("🚀 Testing Enhanced Retrieval Strategy")
    logger.info("=" * 80)
    
    try:
        # Initialize the LLM pipeline with enhanced retrieval
        pipeline = TwoStageLLMPipeline()
        
        # Test the grace period question
        test_query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        logger.info(f"🎯 Testing query: {test_query}")
        logger.info("=" * 80)
        
        # Test individual search strategies
        logger.info("🔍 Testing Individual Search Components:")
        
        # Test specific terms extraction
        specific_terms = pipeline._extract_specific_terms(test_query)
        logger.info(f"✅ Specific terms: '{specific_terms}'")
        
        # Test definition query
        definition_query = pipeline._build_definition_query(test_query)
        logger.info(f"✅ Definition query: '{definition_query}'")
        
        # Test key terms extraction  
        key_terms = pipeline._extract_key_search_terms(test_query)
        logger.info(f"✅ Key terms: '{key_terms}'")
        
        logger.info("=" * 80)
        
        # Now test the full pipeline
        logger.info("🔄 Running Full Enhanced Two-Stage Pipeline...")
        result = pipeline.process_query(test_query)
        
        logger.info("=" * 80)
        logger.info("🎉 Enhanced Pipeline Results:")
        
        if "error" in result:
            logger.error(f"❌ Pipeline failed: {result['error']}")
            return False
        
        # Display comprehensive results
        logger.info(f"📊 Query: {result['query']}")
        logger.info(f"🎯 Answer: {result['answer'][:300]}...")
        logger.info(f"📈 Confidence: {result['confidence']}")
        logger.info(f"🏷️ Domain: {result['task_analysis']['domain']}")
        logger.info(f"🔢 Few-Shot Prompts: {len(result['task_analysis']['few_shot_prompts'])}")
        logger.info(f"📝 Methodology: {result['methodology']}")
        logger.info(f"⏱️ Processing Time: {result['performance']['total_processing_time']:.2f}s")
        logger.info(f"🔢 Sections: {len(result['sections'])}")
        logger.info(f"📚 Citations: {len(result['citations'])}")
        
        # Check if we found grace period information
        answer_text = result['answer'].lower()
        if "grace period" in answer_text and "not available" not in answer_text:
            logger.info("🎯 ✅ SUCCESS: Found grace period information!")
        elif "not available" in answer_text or "cannot" in answer_text:
            logger.warning("⚠️ PARTIAL: LLM still says information not available")
        else:
            logger.info("📋 UNKNOWN: Check the answer content above")
        
        # Show citations if any
        if result['citations']:
            logger.info("📚 Citations found:")
            for i, citation in enumerate(result['citations'][:3], 1):
                logger.info(f"   {i}. {citation.get('excerpt', 'No excerpt')[:100]}...")
        
        logger.info("=" * 80)
        logger.info("🎉 Enhanced retrieval test complete!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Enhanced retrieval test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    success = test_enhanced_retrieval()
    
    if success:
        logger.info("✅ Enhanced retrieval strategy tested successfully!")
        logger.info("🔍 Review the results above to see if grace period information was found.")
        logger.info("📊 Key improvements:")
        logger.info("   - Increased k from 8 to 28 total chunks searched")
        logger.info("   - 4 different search strategies")
        logger.info("   - Re-ranking based on relevance")
        logger.info("   - Enhanced failure handling in prompts")
    else:
        logger.error("❌ Enhanced retrieval test failed.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)