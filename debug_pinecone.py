#!/usr/bin/env python3
"""
Pinecone Debug Script
Test Pinecone connection and index operations
"""

import os
import logging
from config import IngestionConfig
from vector_database import VectorDatabasePipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pinecone_connection():
    """Test basic Pinecone connection and operations"""
    
    logger.info("🔍 Testing Pinecone Connection and Index Operations")
    
    try:
        # Initialize config
        config = IngestionConfig()
        
        # Check environment variables
        logger.info("📋 Checking environment variables...")
        if not config.PINECONE_API_KEY:
            logger.error("❌ PINECONE_API_KEY not set")
            return False
        
        logger.info(f"✅ PINECONE_API_KEY: {'*' * 8 + config.PINECONE_API_KEY[-4:]}")
        logger.info(f"✅ PINECONE_CLOUD: {config.PINECONE_CLOUD}")
        logger.info(f"✅ PINECONE_REGION: {config.PINECONE_REGION}")
        
        # Initialize vector pipeline with fixed name
        logger.info("🚀 Initializing Vector Database Pipeline...")
        pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-test", 
            auto_generate_index=False
        )
        
        # Test listing indexes
        logger.info("📝 Testing Pinecone connection by listing indexes...")
        try:
            existing_indexes = pipeline.pinecone_client.list_indexes().names()
            logger.info(f"✅ Connection successful! Found {len(existing_indexes)} existing indexes:")
            for idx in existing_indexes:
                logger.info(f"   - {idx}")
        except Exception as e:
            logger.error(f"❌ Failed to list indexes: {e}")
            return False
        
        # Test index creation
        logger.info("🔨 Testing index creation...")
        try:
            success = pipeline.create_index(force_recreate=True)
            if success:
                logger.info("✅ Index created successfully!")
                
                # Test index stats
                stats = pipeline.get_index_stats()
                logger.info(f"📊 Index stats: {stats}")
                
                # Cleanup test index
                logger.info("🧹 Cleaning up test index...")
                pipeline.pinecone_client.delete_index("hackrx-docs-test")
                logger.info("✅ Test index deleted")
                
            else:
                logger.error("❌ Index creation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
            return False
        
        logger.info("🎉 All Pinecone tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinecone test failed: {e}")
        return False

def check_environment():
    """Check all required environment variables"""
    
    logger.info("🔍 Checking Environment Variables")
    
    required_vars = [
        "PINECONE_API_KEY",
        "GEMINI_API_KEY"
    ]
    
    optional_vars = [
        "PINECONE_CLOUD",
        "PINECONE_REGION",
        "PINECONE_INDEX_NAME"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * 8 + value[-4:] if len(value) > 8 else '*' * len(value)}")
        else:
            logger.error(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.info(f"⚠️  {var}: Not set (using default)")
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    logger.info("✅ All required environment variables are set!")
    return True

def main():
    """Main diagnostic function"""
    
    logger.info("🚀 Starting Pinecone Diagnostic")
    logger.info("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return False
    
    logger.info("=" * 50)
    
    # Test Pinecone
    if not test_pinecone_connection():
        logger.error("❌ Pinecone test failed")
        return False
    
    logger.info("=" * 50)
    logger.info("🎉 All diagnostics passed! Your Pinecone setup is working correctly.")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)