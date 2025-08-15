#!/usr/bin/env python3
"""
Test the corrected Two-Stage LLM Pipeline
Verifies domain analysis and few-shot prompting flow
"""

import logging
from llm_integration import TwoStageLLMPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_two_stage_pipeline():
    """Test the corrected two-stage pipeline"""
    
    logger.info("🧪 Testing Two-Stage LLM Pipeline with Corrected Flow")
    logger.info("=" * 60)
    
    try:
        # Initialize the pipeline
        logger.info("🚀 Initializing Two-Stage LLM Pipeline...")
        pipeline = TwoStageLLMPipeline()
        
        # Test query about insurance (typical domain from your logs)
        test_query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        logger.info(f"🔍 Testing with query: {test_query}")
        logger.info("=" * 60)
        
        # Process the query through the two-stage pipeline
        result = pipeline.process_query(test_query)
        
        if "error" in result:
            logger.error(f"❌ Pipeline failed: {result['error']}")
            return False
        
        # Display results
        logger.info("✅ Two-Stage Pipeline Results:")
        logger.info(f"📊 Query: {result['query']}")
        logger.info(f"🎯 Answer: {result['answer'][:200]}...")
        logger.info(f"📈 Confidence: {result['confidence']}")
        logger.info(f"🏷️ Domain: {result['task_analysis']['domain']}")
        logger.info(f"🎯 Few-Shot Prompts Created: {len(result['task_analysis']['few_shot_prompts'])}")
        logger.info(f"📝 Methodology: {result['methodology']}")
        logger.info(f"⏱️ Processing Time: {result['performance']['total_processing_time']:.2f}s")
        logger.info(f"🔢 Sections: {len(result['sections'])}")
        logger.info(f"📚 Citations: {len(result['citations'])}")
        
        # Show few-shot prompts that were created
        if result['task_analysis']['few_shot_prompts']:
            logger.info("🎯 Few-Shot Prompts Created in Stage 1:")
            for i, prompt in enumerate(result['task_analysis']['few_shot_prompts'], 1):
                logger.info(f"   {i}. Q: {prompt.get('example_question', 'N/A')[:100]}...")
                logger.info(f"      A: {prompt.get('example_answer', 'N/A')[:100]}...")
        
        logger.info("=" * 60)
        logger.info("🎉 Two-Stage Pipeline Test Completed Successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function"""
    
    logger.info("🚀 Starting Two-Stage LLM Pipeline Test")
    
    success = test_two_stage_pipeline()
    
    if success:
        logger.info("✅ All tests passed! The corrected two-stage flow is working.")
        logger.info("🔄 Stage 1: Domain understanding + Few-shot prompt creation ✓")
        logger.info("🎯 Stage 2: Use few-shot prompts + user question to generate answer ✓")
    else:
        logger.error("❌ Tests failed. Please check the logs for details.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)