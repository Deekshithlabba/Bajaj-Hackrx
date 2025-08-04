"""
Vector Database Integration Pipeline - Person 2
===============================================

Sophisticated vector database integration that stores and retrieves document chunks
from Pinecone with OpenAI embeddings for semantic search.

Features:
- OpenAI text-embedding-3-small integration (cost-effective, 1536 dimensions)
- Pinecone vector database with gRPC for high performance
- Batch processing with smart error handling
- Rich metadata preservation for explainability
- Production-ready with comprehensive logging

Author: Person 2 - HackRx 6.0 Universal Document Intelligence System
"""

import json
import logging
import time
import uuid
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

import numpy as np
from openai import OpenAI
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec

from config import config


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """Represents a vector record for Pinecone"""
    id: str
    values: List[float]
    metadata: Dict[str, Any]


class VectorDatabasePipeline:
    """
    Production-ready vector database pipeline for document chunks.
    
    Integrates with Person 1's document ingestion output and creates
    a searchable vector database using Pinecone and OpenAI embeddings.
    """
    
    def __init__(self, 
                 index_name: Optional[str] = None,
                 auto_generate_index: bool = True):
        """
        Initialize the vector database pipeline.
        
        Args:
            index_name: Name of the Pinecone index (auto-generated if None)
            auto_generate_index: Whether to auto-generate unique index name
        """
        # API Keys
        self.openai_api_key = config.OPENAI_API_KEY
        self.pinecone_api_key = config.PINECONE_API_KEY
        
        # Auto-generate unique index name if needed
        if index_name:
            self.index_name = index_name
        elif auto_generate_index:
            import uuid
            self.index_name = f"hackrx-docs-{uuid.uuid4().hex[:8]}"
        else:
            self.index_name = config.PINECONE_INDEX_NAME
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        if not self.pinecone_api_key:
            raise ValueError("Pinecone API key is required. Set PINECONE_API_KEY environment variable.")
        
        # Initialize clients
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.pinecone_client = Pinecone(api_key=self.pinecone_api_key)
        
        # Configuration
        self.embedding_model = config.EMBEDDING_MODEL
        self.embedding_dimension = config.EMBEDDING_DIMENSION
        self.batch_size = config.BATCH_SIZE
        
        # Pinecone index (initialized lazily)
        self._index = None
        
        logger.info(f"🚀 Vector Database Pipeline initialized")
        logger.info(f"📊 Model: {self.embedding_model} ({self.embedding_dimension}D)")
        logger.info(f"🗂️ Index: {self.index_name}")
    
    @property
    def index(self):
        """Lazy initialization of Pinecone index"""
        if self._index is None:
            self._index = self.pinecone_client.Index(self.index_name)
        return self._index
    
    def create_index(self, force_recreate: bool = False) -> bool:
        """
        Create a Pinecone index with optimal settings.
        
        Args:
            force_recreate: Whether to delete and recreate existing index
            
        Returns:
            True if index was created/already exists, False otherwise
        """
        try:
            # Check if index already exists
            existing_indexes = self.pinecone_client.list_indexes().names()
            
            if self.index_name in existing_indexes:
                if force_recreate:
                    logger.info(f"🗑️ Deleting existing index: {self.index_name}")
                    self.pinecone_client.delete_index(self.index_name)
                    time.sleep(10)  # Wait for deletion to complete
                else:
                    logger.info(f"✅ Index {self.index_name} already exists")
                    return True
            
            # Create new index
            logger.info(f"📝 Creating new index: {self.index_name}")
            
            spec = ServerlessSpec(
                cloud=config.PINECONE_CLOUD,
                region=config.PINECONE_REGION
            )
            
            self.pinecone_client.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric=config.VECTOR_METRIC,
                spec=spec
            )
            
            # Wait for index to be ready
            logger.info("⏳ Waiting for index to be ready...")
            time.sleep(10)  # Typical wait time for serverless index
            
            # Verify index is ready
            index_stats = self.index.describe_index_stats()
            logger.info(f"✅ Index created successfully: {index_stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create index: {e}")
            return False
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts using OpenAI.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            logger.debug(f"🔄 Generating embeddings for {len(texts)} texts")
            
            response = self.openai_client.embeddings.create(
                input=texts,
                model=self.embedding_model
            )
            
            embeddings = [record.embedding for record in response.data]
            logger.debug(f"✅ Generated {len(embeddings)} embeddings")
            
            # Rate limiting: 40-second delay between API calls
            logger.info("⏳ Waiting 40 seconds before next API call to avoid rate limits...")
            time.sleep(3)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ Failed to generate embeddings: {e}")
            raise
    
    def load_chunks_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load document chunks from Person 1's JSON output.
        
        Args:
            json_path: Path to the chunks JSON file
            
        Returns:
            List of chunk dictionaries
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            logger.info(f"📁 Loaded {len(chunks)} chunks from {json_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Failed to load chunks from {json_path}: {e}")
            raise
    
    def prepare_vector_records(self, chunks: List[Dict[str, Any]]) -> List[VectorRecord]:
        """
        Convert document chunks to vector records with embeddings.
        
        Args:
            chunks: List of document chunks from Person 1
            
        Returns:
            List of VectorRecord objects ready for Pinecone
        """
        vector_records = []
        
        # Process chunks in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            
            # Extract texts for embedding
            texts = []
            for chunk in batch:
                content = chunk.get('content', '')
                if not content.strip():
                    continue
                texts.append(content)
            
            if not texts:
                continue
                
            # Generate embeddings for this batch
            try:
                embeddings = self.generate_embeddings(texts)
                
                # Create vector records
                for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                    # Create unique ID
                    chunk_id = chunk.get('chunk_id') or f"chunk_{uuid.uuid4().hex[:12]}"
                    
                    # Prepare metadata (preserve all original metadata)
                    metadata = {
                        "content": chunk.get('content', '')[:1000],  # Truncate content for metadata
                        "content_type": chunk.get('content_type', 'text'),
                        "page_number": chunk.get('page_number', 1),
                        "source_url": chunk.get('source_url', ''),
                        "chunk_id": chunk_id,
                        "word_count": len(chunk.get('content', '').split()),
                        "content_length": len(chunk.get('content', '')),
                        "created_at": chunk.get('metadata', {}).get('created_at', ''),
                        "extraction_method": chunk.get('metadata', {}).get('extraction_method', ''),
                    }
                    
                    # Add any additional metadata from the original chunk
                    if 'metadata' in chunk and isinstance(chunk['metadata'], dict):
                        for key, value in chunk['metadata'].items():
                            if key not in metadata and value is not None:
                                # Only include serializable values
                                if isinstance(value, (str, int, float, bool)):
                                    metadata[f"original_{key}"] = value
                    
                    vector_records.append(VectorRecord(
                        id=chunk_id,
                        values=embedding,
                        metadata=metadata
                    ))
                
                logger.info(f"✅ Processed batch {i//self.batch_size + 1}: {len(embeddings)} vectors")
                
            except Exception as e:
                logger.error(f"❌ Failed to process batch {i//self.batch_size + 1}: {e}")
                continue
        
        logger.info(f"🎯 Prepared {len(vector_records)} vector records")
        return vector_records
    
    def upsert_vectors(self, vector_records: List[VectorRecord], 
                      namespace: str = "default") -> bool:
        """
        Upsert vector records to Pinecone in batches.
        
        Args:
            vector_records: List of VectorRecord objects
            namespace: Pinecone namespace to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            successful_upserts = 0
            
            # Process in batches
            for i in range(0, len(vector_records), self.batch_size):
                batch = vector_records[i:i + self.batch_size]
                
                # Convert to Pinecone format
                vectors_to_upsert = [
                    (record.id, record.values, record.metadata)
                    for record in batch
                ]
                
                try:
                    # Upsert to Pinecone
                    response = self.index.upsert(
                        vectors=vectors_to_upsert,
                        namespace=namespace
                    )
                    
                    successful_upserts += len(batch)
                    logger.info(f"✅ Upserted batch {i//self.batch_size + 1}: {len(batch)} vectors")
                    
                    # Brief pause to avoid rate limits
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to upsert batch {i//self.batch_size + 1}: {e}")
                    continue
            
            logger.info(f"🎯 Successfully upserted {successful_upserts}/{len(vector_records)} vectors")
            
            # Get index statistics
            stats = self.index.describe_index_stats()
            logger.info(f"📊 Index stats: {stats}")
            
            return successful_upserts > 0
            
        except Exception as e:
            logger.error(f"❌ Failed to upsert vectors: {e}")
            return False
    
    def search_similar(self, query: str, top_k: int = 5, 
                      namespace: str = "default",
                      filter_dict: Optional[Dict[str, Any]] = None,
                      hybrid: bool = False,
                      semantic_weight: float = 0.7) -> Dict[str, Any]:
        """
        Search for similar content using semantic search or hybrid search.
        
        Args:
            query: Text query to search for
            top_k: Number of results to return
            namespace: Pinecone namespace to search
            filter_dict: Optional metadata filter
            hybrid: Whether to use hybrid search (semantic + keyword)
            semantic_weight: Weight for semantic search in hybrid mode (0.0-1.0)
            
        Returns:
            Search results with scores and metadata
        """
        try:
            if hybrid:
                return self._hybrid_search(query, top_k, namespace, filter_dict, semantic_weight)
            else:
                return self._semantic_search(query, top_k, namespace, filter_dict)
            
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            raise
    
    def _semantic_search(self, query: str, top_k: int, 
                        namespace: str, filter_dict: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Pure semantic search using embeddings"""
        # Generate embedding for query
        query_embedding = self.generate_embeddings([query])[0]
        
        # Search Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
            include_values=False,
            filter=filter_dict
        )
        
        logger.info(f"🔍 Semantic search: Found {len(results.matches)} results")
        
        return {
            "query": query,
            "search_type": "semantic",
            "results": results.matches,
            "total_found": len(results.matches)
        }
    
    def _hybrid_search(self, query: str, top_k: int, 
                      namespace: str, filter_dict: Optional[Dict[str, Any]],
                      semantic_weight: float = 0.7) -> Dict[str, Any]:
        """
        Hybrid search combining semantic and keyword-based search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            namespace: Pinecone namespace
            filter_dict: Metadata filter
            semantic_weight: Weight for semantic search (0.0-1.0)
        """
        keyword_weight = 1.0 - semantic_weight
        
        # Get more results from semantic search to have pool for reranking
        semantic_k = min(top_k * 3, 50)  # Get 3x more for reranking
        
        # 1. Semantic search
        semantic_results = self._semantic_search(query, semantic_k, namespace, filter_dict)
        
        if not semantic_results["results"]:
            return semantic_results
        
        # 2. Keyword-based scoring
        query_terms = self._extract_keywords(query.lower())
        
        # 3. Combine scores
        hybrid_results = []
        for result in semantic_results["results"]:
            content = result.metadata.get("content", "").lower()
            
            # Calculate keyword relevance score
            keyword_score = self._calculate_keyword_score(query_terms, content)
            
            # Combine semantic and keyword scores
            semantic_score = float(result.score)
            hybrid_score = (semantic_weight * semantic_score) + (keyword_weight * keyword_score)
            
            # Create new result with hybrid score
            hybrid_result = {
                "id": result.id,
                "score": hybrid_score,
                "semantic_score": semantic_score,
                "keyword_score": keyword_score,
                "metadata": result.metadata
            }
            hybrid_results.append(hybrid_result)
        
        # 4. Sort by hybrid score and take top_k
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = hybrid_results[:top_k]
        
        logger.info(f"🔍 Hybrid search: Combined {len(semantic_results['results'])} semantic results")
        logger.info(f"🎯 Hybrid search: Returning top {len(final_results)} hybrid-ranked results")
        
        return {
            "query": query,
            "search_type": "hybrid",
            "semantic_weight": semantic_weight,
            "keyword_weight": keyword_weight,
            "results": final_results,
            "total_found": len(final_results)
        }
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query"""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'about', 'what', 'when', 'where', 'how', 'why', 'which', 'that',
            'this', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might'
        }
        
        # Extract words (alphanumeric sequences)
        words = re.findall(r'\b\w+\b', query.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _calculate_keyword_score(self, query_terms: List[str], content: str) -> float:
        """Calculate keyword relevance score for content"""
        if not query_terms:
            return 0.0
        
        content_words = re.findall(r'\b\w+\b', content.lower())
        content_counter = Counter(content_words)
        
        # Calculate TF-IDF-like score
        total_score = 0.0
        total_terms = len(query_terms)
        
        for term in query_terms:
            # Term frequency in content
            tf = content_counter.get(term, 0)
            
            # Boost for exact matches
            if tf > 0:
                # Normalize by content length and boost frequent terms
                normalized_tf = tf / max(len(content_words), 1)
                total_score += normalized_tf * (1 + np.log(tf))
        
        # Normalize by number of query terms
        final_score = total_score / total_terms if total_terms > 0 else 0.0
        
        return min(final_score, 1.0)  # Cap at 1.0
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get current index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
        except Exception as e:
            logger.error(f"❌ Failed to get index stats: {e}")
            return {}
    
    def process_document_chunks(self, json_path: str, 
                              namespace: str = "default",
                              create_index_if_missing: bool = True) -> bool:
        """
        Complete pipeline: Load chunks, create embeddings, and store in Pinecone.
        
        Args:
            json_path: Path to Person 1's chunk JSON file
            namespace: Pinecone namespace to use
            create_index_if_missing: Whether to create index if it doesn't exist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🚀 Starting vector database pipeline for {json_path}")
            
            # Create index if needed
            if create_index_if_missing:
                if not self.create_index():
                    logger.error("❌ Failed to create/verify index")
                    return False
            
            # Load chunks
            chunks = self.load_chunks_from_json(json_path)
            if not chunks:
                logger.error("❌ No chunks loaded")
                return False
            
            # Prepare vector records
            vector_records = self.prepare_vector_records(chunks)
            if not vector_records:
                logger.error("❌ No vector records prepared")
                return False
            
            # Upsert to Pinecone
            success = self.upsert_vectors(vector_records, namespace)
            
            if success:
                # Display final stats
                stats = self.get_index_stats()
                logger.info(f"🎯 Pipeline completed successfully!")
                logger.info(f"📊 Final stats: {stats}")
                
                # Test search functionality (both semantic and hybrid)
                logger.info("🔍 Testing search functionality...")
                
                # Test semantic search
                semantic_results = self.search_similar("insurance policy", top_k=3, namespace=namespace, hybrid=False)
                logger.info(f"✅ Semantic search test: Found {semantic_results['total_found']} results")
                
                # Test hybrid search
                hybrid_results = self.search_similar("insurance policy coverage", top_k=3, namespace=namespace, hybrid=True)
                logger.info(f"✅ Hybrid search test: Found {hybrid_results['total_found']} results")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return False


def main():
    """Main function for testing the vector database pipeline"""
    
    # Initialize pipeline
    try:
        pipeline = VectorDatabasePipeline()
        
        # Process the chunks from Person 1
        chunks_file = "processed_chunks/chunks_doc_1.json"
        
        if not Path(chunks_file).exists():
            logger.error(f"❌ Chunks file not found: {chunks_file}")
            logger.info("💡 Make sure Person 1's document processing is complete")
            return False
        
        # Run the complete pipeline
        success = pipeline.process_document_chunks(
            json_path=chunks_file,
            namespace="hackrx-docs",
            create_index_if_missing=True
        )
        
        if success:
            logger.info("🎉 Vector database setup complete!")
            logger.info("🔗 Ready for Person 3 (LLM integration)")
        else:
            logger.error("❌ Vector database setup failed")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        return False


if __name__ == "__main__":
    main()