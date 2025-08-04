"""
Test Vector Database Integration - Person 2
==========================================

Comprehensive testing for the vector database pipeline.
Tests embedding generation, Pinecone integration, and search functionality.

Usage:
    python test_vector_database.py

Requirements:
    - OPENAI_API_KEY in environment
    - PINECONE_API_KEY in environment
    - Processed chunks from Person 1 (processed_chunks/chunks_doc_1.json)
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
sys.path.append('.')

try:
    from vector_database import VectorDatabasePipeline
    from config import config
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    logger.error("Make sure vector_database.py and config.py are in the current directory")
    sys.exit(1)


class VectorDatabaseTester:
    """Comprehensive test suite for vector database integration"""
    
    def __init__(self):
        self.pipeline = None
        self.test_results = {
            "config_validation": False,
            "pipeline_initialization": False,
            "embedding_generation": False,
            "index_creation": False,
            "data_loading": False,
            "vector_preparation": False,
            "pinecone_upsert": False,
            "search_functionality": False,
            "full_pipeline": False
        }
    
    def test_configuration(self) -> bool:
        """Test configuration and environment setup"""
        logger.info("🔧 Testing configuration...")
        
        try:
            # Test configuration validation
            validation = config.validate_config()
            
            if not validation["valid"]:
                logger.error("❌ Configuration validation failed:")
                for issue in validation["issues"]:
                    logger.error(f"   - {issue}")
                return False
            
            # Check required settings
            required_settings = [
                ("OpenAI API Key", config.OPENAI_API_KEY),
                ("Pinecone API Key", config.PINECONE_API_KEY),
                ("Index Name", config.PINECONE_INDEX_NAME),
                ("Embedding Model", config.EMBEDDING_MODEL)
            ]
            
            for name, value in required_settings:
                if not value:
                    logger.error(f"❌ Missing {name}")
                    return False
                logger.info(f"✅ {name}: {'*' * min(8, len(str(value)))}")
            
            logger.info(f"✅ Configuration valid")
            return True
            
        except Exception as e:
            logger.error(f"❌ Configuration test failed: {e}")
            return False
    
    def test_pipeline_initialization(self) -> bool:
        """Test pipeline initialization"""
        logger.info("🚀 Testing pipeline initialization...")
        
        try:
            self.pipeline = VectorDatabasePipeline()
            logger.info(f"✅ Pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Pipeline initialization failed: {e}")
            return False
    
    def test_embedding_generation(self) -> bool:
        """Test OpenAI embedding generation"""
        logger.info("🧠 Testing embedding generation...")
        
        try:
            # Test with sample texts
            test_texts = [
                "This is a test document about insurance policies.",
                "Machine learning models require vector embeddings.",
                "Pinecone is a vector database for AI applications."
            ]
            
            embeddings = self.pipeline.generate_embeddings(test_texts)
            
            # Validate embeddings
            if len(embeddings) != len(test_texts):
                logger.error(f"❌ Expected {len(test_texts)} embeddings, got {len(embeddings)}")
                return False
            
            for i, embedding in enumerate(embeddings):
                if len(embedding) != config.EMBEDDING_DIMENSION:
                    logger.error(f"❌ Embedding {i} has wrong dimension: {len(embedding)}")
                    return False
            
            logger.info(f"✅ Generated {len(embeddings)} embeddings ({config.EMBEDDING_DIMENSION}D)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {e}")
            return False
    
    def test_index_creation(self) -> bool:
        """Test Pinecone index creation"""
        logger.info("📝 Testing index creation...")
        
        try:
            # Use a test index name to avoid conflicts
            test_index_name = f"{config.PINECONE_INDEX_NAME}-test"
            self.pipeline.index_name = test_index_name
            
            # Create index
            success = self.pipeline.create_index(force_recreate=True)
            
            if not success:
                logger.error("❌ Index creation failed")
                return False
            
            # Test index accessibility
            stats = self.pipeline.get_index_stats()
            logger.info(f"✅ Index created: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Index creation test failed: {e}")
            return False
    
    def test_data_loading(self) -> bool:
        """Test loading chunks from Person 1's output"""
        logger.info("📁 Testing data loading...")
        
        try:
            chunks_file = "processed_chunks/chunks_doc_1.json"
            
            if not Path(chunks_file).exists():
                logger.error(f"❌ Chunks file not found: {chunks_file}")
                logger.info("💡 Run Person 1's document processing first")
                return False
            
            chunks = self.pipeline.load_chunks_from_json(chunks_file)
            
            if not chunks:
                logger.error("❌ No chunks loaded")
                return False
            
            # Analyze chunk structure
            sample_chunk = chunks[0]
            required_fields = ['content', 'content_type', 'page_number']
            
            for field in required_fields:
                if field not in sample_chunk:
                    logger.warning(f"⚠️ Missing field in chunk: {field}")
            
            logger.info(f"✅ Loaded {len(chunks)} chunks")
            logger.info(f"📊 Sample chunk keys: {list(sample_chunk.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data loading test failed: {e}")
            return False
    
    def test_vector_preparation(self) -> bool:
        """Test vector record preparation"""
        logger.info("🔄 Testing vector preparation...")
        
        try:
            # Load a small sample
            chunks_file = "processed_chunks/chunks_doc_1.json"
            all_chunks = self.pipeline.load_chunks_from_json(chunks_file)
            
            # Take first 10 chunks for testing
            test_chunks = all_chunks[:10]
            
            vector_records = self.pipeline.prepare_vector_records(test_chunks)
            
            if not vector_records:
                logger.error("❌ No vector records prepared")
                return False
            
            # Validate vector records
            sample_record = vector_records[0]
            
            # Check required fields
            if not hasattr(sample_record, 'id') or not sample_record.id:
                logger.error("❌ Vector record missing ID")
                return False
            
            if not hasattr(sample_record, 'values') or len(sample_record.values) != config.EMBEDDING_DIMENSION:
                logger.error("❌ Vector record has invalid embedding")
                return False
            
            if not hasattr(sample_record, 'metadata') or not sample_record.metadata:
                logger.error("❌ Vector record missing metadata")
                return False
            
            logger.info(f"✅ Prepared {len(vector_records)} vector records")
            logger.info(f"📊 Sample metadata keys: {list(sample_record.metadata.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector preparation test failed: {e}")
            return False
    
    def test_pinecone_upsert(self) -> bool:
        """Test upserting vectors to Pinecone"""
        logger.info("⬆️ Testing Pinecone upsert...")
        
        try:
            # Load a small sample
            chunks_file = "processed_chunks/chunks_doc_1.json"
            all_chunks = self.pipeline.load_chunks_from_json(chunks_file)
            
            # Take first 5 chunks for testing
            test_chunks = all_chunks[:5]
            vector_records = self.pipeline.prepare_vector_records(test_chunks)
            
            # Upsert to test namespace
            success = self.pipeline.upsert_vectors(vector_records, namespace="test")
            
            if not success:
                logger.error("❌ Pinecone upsert failed")
                return False
            
            # Verify upsert
            stats = self.pipeline.get_index_stats()
            logger.info(f"✅ Upserted {len(vector_records)} vectors")
            logger.info(f"📊 Index stats: {stats}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pinecone upsert test failed: {e}")
            return False
    
    def test_search_functionality(self) -> bool:
        """Test semantic search functionality"""
        logger.info("🔍 Testing search functionality...")
        
        try:
            # Test queries for both semantic and hybrid search
            test_queries = [
                "insurance policy",
                "medical coverage",
                "premium payment",
                "claim process"
            ]
            
            for query in test_queries:
                # Test semantic search
                semantic_results = self.pipeline.search_similar(
                    query=query,
                    top_k=3,
                    namespace="test",
                    hybrid=False
                )
                
                # Test hybrid search
                hybrid_results = self.pipeline.search_similar(
                    query=query,
                    top_k=3,
                    namespace="test",
                    hybrid=True,
                    semantic_weight=0.7
                )
                
                if not semantic_results["results"] and not hybrid_results["results"]:
                    logger.warning(f"⚠️ No results for query: '{query}'")
                    continue
                
                logger.info(f"✅ Query '{query}':")
                logger.info(f"   Semantic: {len(semantic_results['results'])} results")
                logger.info(f"   Hybrid: {len(hybrid_results['results'])} results")
                
                # Check result structure for semantic search
                if semantic_results["results"]:
                    top_result = semantic_results["results"][0]
                    if not hasattr(top_result, 'score') or not hasattr(top_result, 'metadata'):
                        logger.error("❌ Invalid semantic search result structure")
                        return False
                    logger.info(f"   Semantic top score: {top_result.score:.3f}")
                
                # Check result structure for hybrid search
                if hybrid_results["results"]:
                    top_hybrid = hybrid_results["results"][0]
                    if not isinstance(top_hybrid, dict) or 'score' not in top_hybrid:
                        logger.error("❌ Invalid hybrid search result structure")
                        return False
                    logger.info(f"   Hybrid top score: {top_hybrid['score']:.3f}")
                    logger.info(f"   Semantic component: {top_hybrid.get('semantic_score', 0):.3f}")
                    logger.info(f"   Keyword component: {top_hybrid.get('keyword_score', 0):.3f}")
            
            logger.info("✅ Search functionality working (semantic + hybrid)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Search test failed: {e}")
            return False
    
    def test_full_pipeline(self) -> bool:
        """Test the complete pipeline"""
        logger.info("🎯 Testing full pipeline...")
        
        try:
            chunks_file = "processed_chunks/chunks_doc_1.json"
            
            # Run the complete pipeline with a subset
            success = self.pipeline.process_document_chunks(
                json_path=chunks_file,
                namespace="full-test",
                create_index_if_missing=True
            )
            
            if not success:
                logger.error("❌ Full pipeline test failed")
                return False
            
            logger.info("✅ Full pipeline test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Full pipeline test failed: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        logger.info("🧪 Starting Vector Database Test Suite")
        logger.info("=" * 50)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("Pipeline Initialization", self.test_pipeline_initialization),
            ("Embedding Generation", self.test_embedding_generation),
            ("Index Creation", self.test_index_creation),
            ("Data Loading", self.test_data_loading),
            ("Vector Preparation", self.test_vector_preparation),
            ("Pinecone Upsert", self.test_pinecone_upsert),
            ("Search Functionality", self.test_search_functionality),
            ("Full Pipeline", self.test_full_pipeline)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n--- {test_name} ---")
            try:
                result = test_func()
                self.test_results[test_name.lower().replace(" ", "_")] = result
                if result:
                    passed += 1
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    logger.error(f"❌ {test_name}: FAILED")
            except Exception as e:
                logger.error(f"❌ {test_name}: ERROR - {e}")
                self.test_results[test_name.lower().replace(" ", "_")] = False
        
        # Summary
        logger.info("\n" + "=" * 50)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 50)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed! Vector database is ready!")
            logger.info("🔗 Ready for Person 3 (LLM integration)")
        else:
            logger.error("⚠️ Some tests failed. Check configuration and dependencies.")
        
        return passed == total


def main():
    """Main test execution"""
    print("🚀 Vector Database Test Suite - Person 2")
    print("=" * 50)
    
    # Check if chunks file exists
    chunks_file = Path("processed_chunks/chunks_doc_1.json")
    if not chunks_file.exists():
        print("❌ Error: processed_chunks/chunks_doc_1.json not found")
        print("💡 Please run Person 1's document processing first:")
        print("   python test_ingestion.py")
        return False
    
    # Run tests
    tester = VectorDatabaseTester()
    success = tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)