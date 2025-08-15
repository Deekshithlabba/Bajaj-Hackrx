#!/usr/bin/env python3
"""
Isolate and Test the Retriever - Step 1
See exactly what chunks the retriever is finding for the grace period query
"""

import logging
from vector_database import VectorDatabasePipeline
from llm_integration import TwoStageLLMPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_retriever_isolation():
    """Test what the retriever actually finds for the grace period query"""
    
    logger.info("🔍 STEP 1: Isolating and Testing the Retriever")
    logger.info("=" * 80)
    
    try:
        # Initialize vector pipeline
        pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        
        # The exact query from your test
        query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        logger.info(f"🎯 Query: {query}")
        logger.info("=" * 80)
        
        # Test 1: Direct search with current strategy
        logger.info("📋 TEST 1: Current Search Strategy (k=8)")
        current_results = pipeline.search_similar(
            query=query,
            top_k=8,
            hybrid=True,
            semantic_weight=0.9,
            namespace="documents"
        )
        
        if current_results and "results" in current_results:
            logger.info(f"✅ Found {len(current_results['results'])} results")
            for i, result in enumerate(current_results['results'], 1):
                metadata = result['metadata']
                content = metadata['content']
                logger.info(f"\n--- CHUNK {i} ---")
                logger.info(f"Score: {result['score']:.4f}")
                logger.info(f"Source: {metadata.get('source_url', 'Unknown')}")
                logger.info(f"Page: {metadata.get('page_number', 'Unknown')}")
                logger.info(f"Type: {metadata.get('content_type', 'Unknown')}")
                logger.info(f"Chunk ID: {metadata.get('chunk_id', 'Unknown')}")
                logger.info(f"Content: {content[:500]}...")
                if len(content) > 500:
                    logger.info(f"[Content truncated - full length: {len(content)} chars]")
                logger.info("=" * 60)
        else:
            logger.error("❌ No results found with current strategy")
        
        # Test 2: Increase k to 15
        logger.info("\n📋 TEST 2: Increased Retrieval (k=15)")
        extended_results = pipeline.search_similar(
            query=query,
            top_k=15,
            hybrid=True,
            semantic_weight=0.7,
            namespace="documents"
        )
        
        if extended_results and "results" in extended_results:
            logger.info(f"✅ Found {len(extended_results['results'])} results with k=15")
            # Show chunks 9-15 (the additional ones)
            for i, result in enumerate(extended_results['results'][8:], 9):
                metadata = result['metadata']
                content = metadata['content']
                logger.info(f"\n--- ADDITIONAL CHUNK {i} ---")
                logger.info(f"Score: {result['score']:.4f}")
                logger.info(f"Content: {content[:300]}...")
                
                # Check if this chunk contains grace period info
                if "grace" in content.lower() or "payment" in content.lower():
                    logger.info("🎯 ** POTENTIALLY RELEVANT - Contains 'grace' or 'payment' **")
                logger.info("=" * 40)
        
        # Test 3: Try different search terms
        alternative_terms = [
            "grace period premium payment",
            "grace period",
            "premium payment deadline",
            "National Parivar Mediclaim grace",
            "payment grace period mediclaim"
        ]
        
        logger.info("\n📋 TEST 3: Alternative Search Terms")
        for term in alternative_terms:
            logger.info(f"\n🔍 Testing: '{term}'")
            alt_results = pipeline.search_similar(
                query=term,
                top_k=5,
                hybrid=True,
                semantic_weight=0.6,
                namespace="documents"
            )
            
            if alt_results and "results" in alt_results and len(alt_results['results']) > 0:
                best_result = alt_results['results'][0]
                content = best_result['metadata']['content']
                logger.info(f"   Best match (Score: {best_result['score']:.4f}):")
                logger.info(f"   Content: {content[:200]}...")
                
                # Check for grace period content
                if "grace" in content.lower():
                    logger.info("   🎯 ** CONTAINS GRACE PERIOD INFO **")
                    logger.info(f"   Full content: {content}")
            else:
                logger.info("   ❌ No results")
        
        # Test 4: Test the improved LLM pipeline search strategy
        logger.info("\n📋 TEST 4: Improved LLM Pipeline Search Strategy")
        llm_pipeline = TwoStageLLMPipeline()
        key_terms = llm_pipeline._extract_key_search_terms(query)
        logger.info(f"Extracted key terms: '{key_terms}'")
        
        # Test key terms search
        key_results = pipeline.search_similar(
            query=key_terms,
            top_k=10,
            hybrid=True,
            semantic_weight=0.7,
            namespace="documents"
        )
        
        if key_results and "results" in key_results:
            logger.info(f"✅ Key terms search found {len(key_results['results'])} results")
            for i, result in enumerate(key_results['results'][:3], 1):
                metadata = result['metadata']
                content = metadata['content']
                logger.info(f"\n--- KEY TERMS RESULT {i} ---")
                logger.info(f"Score: {result['score']:.4f}")
                logger.info(f"Content: {content[:300]}...")
                if "grace" in content.lower():
                    logger.info("🎯 ** CONTAINS GRACE PERIOD INFO **")
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 Retriever isolation test complete!")
        logger.info("📊 Analysis:")
        logger.info("   - Check if any chunks contain grace period information")
        logger.info("   - Look for chunks with low scores that might be relevant")
        logger.info("   - See if alternative search terms find better results")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Retriever test failed: {e}")
        return False

def main():
    """Main test function"""
    
    success = test_retriever_isolation()
    
    if success:
        logger.info("✅ Retriever isolation completed.")
        logger.info("💡 Review the chunks above to see what the retriever is finding.")
        logger.info("💡 Look for grace period information in any of the results.")
    else:
        logger.error("❌ Test failed.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)