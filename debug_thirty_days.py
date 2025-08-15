#!/usr/bin/env python3
"""
Debug: Find the "thirty days" grace period information
"""

import logging
from vector_database import VectorDatabasePipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_thirty_days_info():
    """Find where the 'thirty days' grace period information is stored"""
    
    logger.info("🔍 SEARCHING FOR 'THIRTY DAYS' GRACE PERIOD INFORMATION")
    logger.info("=" * 80)
    
    try:
        # Initialize vector pipeline
        pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        
        # Search queries to find the thirty days information
        search_queries = [
            "thirty days grace period",
            "30 days grace period", 
            "grace period thirty days premium payment",
            "thirty days provided premium payment",
            "grace period days premium due date",
            "thirty days renew continue policy",
            "30 days provided for premium",
            "grace period without losing continuity"
        ]
        
        all_found_chunks = {}
        
        for i, query in enumerate(search_queries, 1):
            logger.info(f"\n🔍 Search {i}: '{query}'")
            
            results = pipeline.search_similar(
                query=query,
                top_k=10,
                hybrid=True,
                semantic_weight=0.6,
                namespace="documents"
            )
            
            if results and "results" in results:
                logger.info(f"   Found {len(results['results'])} results")
                
                for j, result in enumerate(results['results'][:3], 1):
                    metadata = result['metadata']
                    content = metadata['content']
                    chunk_id = metadata.get('chunk_id', 'Unknown')
                    
                    # Check if this chunk contains "thirty" or "30"
                    if "thirty" in content.lower() or "30" in content.lower() or "days" in content.lower():
                        logger.info(f"\n   🎯 MATCH {j} (Score: {result['score']:.4f})")
                        logger.info(f"   Chunk ID: {chunk_id}")
                        logger.info(f"   Content: {content}")
                        
                        # Store this chunk
                        all_found_chunks[chunk_id] = {
                            'content': content,
                            'score': result['score'],
                            'query': query,
                            'metadata': metadata
                        }
                        
                        # Check if this is the exact answer
                        if "thirty days" in content.lower() and "grace period" in content.lower():
                            logger.info(f"   *** THIS IS THE COMPLETE ANSWER! ***")
                    else:
                        logger.info(f"   Result {j}: {content[:100]}... (Score: {result['score']:.4f})")
            else:
                logger.info("   No results found")
        
        logger.info("\n" + "=" * 80)
        logger.info("📊 SUMMARY OF FOUND CHUNKS WITH 'THIRTY DAYS' OR '30'")
        logger.info("=" * 80)
        
        if all_found_chunks:
            for chunk_id, info in all_found_chunks.items():
                logger.info(f"\nChunk ID: {chunk_id}")
                logger.info(f"Best Score: {info['score']:.4f}")
                logger.info(f"Found via: '{info['query']}'")
                logger.info(f"Source: {info['metadata'].get('source_url', 'Unknown')}")
                logger.info(f"Page: {info['metadata'].get('page_number', 'Unknown')}")
                logger.info(f"Content: {info['content']}")
                logger.info("-" * 60)
        else:
            logger.warning("❌ No chunks found with 'thirty days' or '30' information!")
        
        # Test if the original enhanced search finds these chunks
        logger.info("\n🧪 TESTING: Does enhanced search find these chunks?")
        original_query = "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?"
        
        enhanced_results = pipeline.search_similar(
            query=original_query,
            top_k=15,
            hybrid=True,
            semantic_weight=0.9,
            namespace="documents"
        )
        
        found_in_enhanced = []
        if enhanced_results and "results" in enhanced_results:
            for result in enhanced_results['results']:
                chunk_id = result['metadata'].get('chunk_id', 'Unknown')
                if chunk_id in all_found_chunks:
                    found_in_enhanced.append({
                        'chunk_id': chunk_id,
                        'rank': enhanced_results['results'].index(result) + 1,
                        'score': result['score']
                    })
        
        if found_in_enhanced:
            logger.info("✅ Enhanced search DOES find the thirty days chunks:")
            for item in found_in_enhanced:
                logger.info(f"   Rank {item['rank']}: {item['chunk_id']} (Score: {item['score']:.4f})")
        else:
            logger.warning("❌ Enhanced search does NOT find the thirty days chunks!")
            logger.info("   This explains why the LLM doesn't see the complete answer.")
        
        return all_found_chunks
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return {}

def main():
    """Main function"""
    
    found_chunks = find_thirty_days_info()
    
    if found_chunks:
        logger.info(f"\n✅ Found {len(found_chunks)} chunks with thirty days information!")
        logger.info("💡 The complete answer exists - we need to improve chunk retrieval ranking.")
    else:
        logger.error("❌ Could not find thirty days information.")
        logger.info("💡 The information might be chunked differently or need different search terms.")
    
    return len(found_chunks) > 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)