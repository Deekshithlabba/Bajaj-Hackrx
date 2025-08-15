#!/usr/bin/env python3
"""
Debug Search and Retrieval for Grace Period Query
Test what chunks are being retrieved for the grace period question
"""

import logging
from vector_database import VectorDatabasePipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_search_for_grace_period():
    """Test search retrieval for grace period question"""
    
    logger.info("🔍 Testing Search Retrieval for Grace Period Query")
    logger.info("=" * 60)
    
    try:
        # Initialize vector pipeline with consistent index name
        pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        
        # Test the exact query from your logs
        query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        logger.info(f"🔍 Testing query: {query}")
        logger.info("=" * 60)
        
        # Test semantic search
        logger.info("📋 Testing Semantic Search...")
        semantic_results = pipeline.search_similar(
            query=query,
            top_k=8,
            hybrid=False,
            namespace="documents"
        )
        
        if semantic_results and "results" in semantic_results:
            logger.info(f"✅ Found {len(semantic_results['results'])} semantic results")
            for i, result in enumerate(semantic_results['results'][:3], 1):
                metadata = result['metadata']
                content_preview = metadata['content'][:300]
                logger.info(f"   {i}. Score: {result['score']:.3f}")
                logger.info(f"      Source: {metadata['source_url']}")
                logger.info(f"      Type: {metadata['content_type']}")
                logger.info(f"      Content: {content_preview}...")
                logger.info(f"      ---")
        else:
            logger.warning("❌ No semantic results found")
        
        logger.info("=" * 60)
        
        # Test hybrid search
        logger.info("📋 Testing Hybrid Search...")
        hybrid_results = pipeline.search_similar(
            query=query,
            top_k=8,
            hybrid=True,
            semantic_weight=0.9,
            namespace="documents"
        )
        
        if hybrid_results and "results" in hybrid_results:
            logger.info(f"✅ Found {len(hybrid_results['results'])} hybrid results")
            for i, result in enumerate(hybrid_results['results'][:3], 1):
                metadata = result['metadata']
                content_preview = metadata['content'][:300]
                logger.info(f"   {i}. Score: {result['score']:.3f}")
                logger.info(f"      Source: {metadata['source_url']}")
                logger.info(f"      Type: {metadata['content_type']}")
                logger.info(f"      Content: {content_preview}...")
                logger.info(f"      ---")
        else:
            logger.warning("❌ No hybrid results found")
        
        logger.info("=" * 60)
        
        # Test different search terms
        alternative_queries = [
            "grace period premium payment",
            "National Parivar Mediclaim grace period", 
            "premium payment deadline",
            "late premium payment",
            "payment grace time",
            "mediclaim premium grace"
        ]
        
        logger.info("🔍 Testing Alternative Search Terms...")
        for alt_query in alternative_queries:
            logger.info(f"Testing: '{alt_query}'")
            alt_results = pipeline.search_similar(
                query=alt_query,
                top_k=3,
                hybrid=True,
                namespace="documents"
            )
            
            if alt_results and "results" in alt_results and len(alt_results['results']) > 0:
                best_result = alt_results['results'][0]
                content_preview = best_result['metadata']['content'][:200]
                logger.info(f"   ✅ Best match (Score: {best_result['score']:.3f}): {content_preview}...")
            else:
                logger.info(f"   ❌ No results")
            logger.info("")
        
        logger.info("=" * 60)
        logger.info("🎉 Search debugging complete!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Search debugging failed: {e}")
        return False

def main():
    """Main debug function"""
    
    logger.info("🚀 Starting Search Retrieval Debugging")
    
    success = test_search_for_grace_period()
    
    if success:
        logger.info("✅ Debugging completed. Check the results above.")
        logger.info("💡 If no relevant results found, the documents might not contain grace period information.")
        logger.info("💡 Or try different search terms that might be in your specific documents.")
    else:
        logger.error("❌ Debugging failed. Check your vector database setup.")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)