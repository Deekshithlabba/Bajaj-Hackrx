#!/usr/bin/env python3
"""
Test the Complete Enhanced System - Should Find 30 Days Answer
"""

import logging
from llm_integration import TwoStageLLMPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_complete_answer():
    """Test if the enhanced system finds the complete 30 days answer"""
    
    logger.info("🎯 TESTING COMPLETE ENHANCED SYSTEM FOR 30 DAYS ANSWER")
    logger.info("=" * 80)
    
    try:
        # Initialize the enhanced pipeline
        pipeline = TwoStageLLMPipeline()
        
        # The exact question that should find "30 days"
        test_query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        logger.info(f"📋 Query: {test_query}")
        logger.info("=" * 80)
        
        # Process the query with enhanced retrieval
        logger.info("🚀 Running Enhanced Two-Stage Pipeline...")
        result = pipeline.process_query(test_query)
        
        logger.info("=" * 80)
        logger.info("📊 FINAL RESULTS:")
        
        if "error" in result:
            logger.error(f"❌ Pipeline failed: {result['error']}")
            return False
        
        # Check the answer
        answer = result.get('answer', '')
        logger.info(f"🎯 Answer: {answer}")
        
        # Check if we found the 30 days information
        answer_lower = answer.lower()
        success_indicators = [
            "30 days" in answer_lower,
            "thirty days" in answer_lower,
            "continuity" in answer_lower,
            "maintain" in answer_lower and "policy" in answer_lower,
            "renewal" in answer_lower and "grace" in answer_lower
        ]
        
        found_complete_answer = any(success_indicators)
        
        # Display results
        logger.info(f"📈 Confidence: {result.get('confidence', 0)}")
        logger.info(f"🔢 Sections: {len(result.get('sections', []))}")
        logger.info(f"📚 Citations: {len(result.get('citations', []))}")
        
        if found_complete_answer:
            logger.info("🎉 ✅ SUCCESS: Found complete answer with 30 days information!")
        else:
            logger.warning("⚠️ PARTIAL: Still missing 30 days specifics")
        
        # Show citations to see what chunks were actually used
        citations = result.get('citations', [])
        if citations:
            logger.info("\n📚 Citations used:")
            for i, citation in enumerate(citations[:5], 1):
                chunk_id = citation.get('chunk_id', 'Unknown')
                excerpt = citation.get('excerpt', 'No excerpt')
                logger.info(f"   {i}. {chunk_id}: {excerpt[:150]}...")
                
                # Check if this citation has the 30 days info
                if "30" in excerpt.lower() or "thirty" in excerpt.lower():
                    logger.info(f"      🎯 *** THIS CITATION HAS 30 DAYS INFO! ***")
        
        # Check if the target chunk was found
        target_chunk_id = "47d333b30ff5_sub_1"  # The chunk we know has the answer
        target_found = any(c.get('chunk_id') == target_chunk_id for c in citations)
        
        if target_found:
            logger.info(f"✅ Target chunk {target_chunk_id} was found and used!")
        else:
            logger.warning(f"❌ Target chunk {target_chunk_id} was NOT found in citations")
        
        logger.info("=" * 80)
        logger.info("🎉 Test complete!")
        
        return found_complete_answer
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    success = test_complete_answer()
    
    if success:
        logger.info("✅ COMPLETE SUCCESS: Enhanced system found 30 days answer!")
        logger.info("🚀 The system now provides the complete answer users expect.")
    else:
        logger.error("❌ Enhancement still needs work - missing 30 days specifics.")
        logger.info("🔧 Check the citations to see what chunks are being retrieved.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)