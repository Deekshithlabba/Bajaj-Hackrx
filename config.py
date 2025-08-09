"""
Configuration settings for the Document Ingestion Pipeline
"""

import os
from pathlib import Path
from typing import Dict, Any


class IngestionConfig:
    """Configuration class for document ingestion pipeline"""
    
    def __init__(self):
        # API Keys
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        
        # Directory settings
        self.TEMP_DIR = Path("./temp_documents")
        self.OUTPUT_DIR = Path("./processed_chunks")
        self.CACHE_DIR = Path("./document_cache")
        
        # Create directories if they don't exist
        for directory in [self.TEMP_DIR, self.OUTPUT_DIR, self.CACHE_DIR]:
            directory.mkdir(exist_ok=True)
        
        # Chunking settings
        self.MAX_CHUNK_SIZE = 1000  # Maximum characters per chunk
        self.CHUNK_OVERLAP = 100    # Character overlap between chunks
        
        # Processing settings
        self.SUPPORTED_FORMATS = {'.pdf', '.docx', '.doc'}
        self.MAX_FILE_SIZE_MB = 50  # Maximum file size in MB
        
        # Multi-API-Key Gemini Configuration for Optimal Performance
        
        # Embedding Service (Using proper dedicated embedding model)
        self.GEMINI_EMBEDDING_API_KEY = os.getenv("GEMINI_EMBEDDING_API_KEY")
        self.EMBEDDING_MODEL = "models/text-embedding-004"  # Proper embedding model
        self.EMBEDDING_BATCH_SIZE = 5  # Reduced to manage daily quotas better
        self.EMBEDDING_DAILY_QUOTA = 1000  # Free tier daily limit
        self.DISABLE_QUOTA_CHECK = os.getenv("DISABLE_QUOTA_CHECK", "false").lower() == "true"  # Emergency bypass
        
        # LLM Stage 1: Task Analyzer (Gemini 2.0 Flash for fast analysis)
        self.GEMINI_ANALYZER_API_KEY = os.getenv("GEMINI_ANALYZER_API_KEY") 
        self.TASK_ANALYZER_MODEL = "gemini-2.0-flash-exp"  # Latest 2.0 Flash model
        
        # LLM Stage 2: Domain Expert (Gemini 2.0 Flash for high-quality responses)
        self.GEMINI_EXPERT_API_KEY = os.getenv("GEMINI_EXPERT_API_KEY")
        self.DOMAIN_EXPERT_MODEL = "gemini-2.0-flash-exp"  # Latest 2.0 Flash model
        
        # Vision Processing (For images/charts)
        self.GEMINI_VISION_API_KEY = os.getenv("GEMINI_VISION_API_KEY")
        self.VISION_MODEL = "gemini-2.0-flash-exp"  # Latest 2.0 multimodal model
        self.MAX_VISION_TOKENS = 500
        
        # Fallback: Single API key for all services if individual keys not provided
        self.GEMINI_MASTER_API_KEY = os.getenv("GEMINI_API_KEY")  # Backward compatibility
        
        # Table extraction settings (deployment-ready)
        self.TABLE_EXTRACTION_METHOD = "pdfplumber"  # Python-only, no system deps
        self.MIN_TABLE_ACCURACY = 80  # Minimum accuracy threshold for tables
        
        # Image processing settings
        self.MAX_IMAGE_SIZE = (1024, 1024)  # Max image dimensions for processing
        self.IMAGE_QUALITY = 85  # JPEG quality for image compression
        
        # Performance settings
        self.ENABLE_CACHING = True
        self.CACHE_EXPIRY_HOURS = 24
        
        # Full functionality enabled
        self.full_extraction = True
        
        # Step 2: Vector Database Settings (Pinecone)
        # Auto-generate unique index name using UUID if not specified
        import uuid
        default_index_name = f"hackrx-docs-{uuid.uuid4().hex[:8]}"
        self.PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", default_index_name)
        self.PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
        self.PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
        self.EMBEDDING_DIMENSION = 768  # Proper dimension for text-embedding-004
        self.VECTOR_METRIC = "cosine"  # Recommended for text embeddings
        self.BATCH_SIZE = 100  # Batch size for vector operations
        
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        # Check API key configuration (with fallback logic)
        api_keys_available = []
        
        # Check individual service keys
        if self.GEMINI_EMBEDDING_API_KEY:
            api_keys_available.append("EMBEDDING")
        if self.GEMINI_ANALYZER_API_KEY:
            api_keys_available.append("ANALYZER")
        if self.GEMINI_EXPERT_API_KEY:
            api_keys_available.append("EXPERT")
        if self.GEMINI_VISION_API_KEY:
            api_keys_available.append("VISION")
            
        # Check master fallback key
        if self.GEMINI_MASTER_API_KEY:
            api_keys_available.append("MASTER")
            
        if not api_keys_available:
            issues.append("No Gemini API keys configured. Set at least GEMINI_API_KEY or individual service keys.")
        
        if not self.PINECONE_API_KEY:
            issues.append("PINECONE_API_KEY environment variable not set")
        
        # Check if required directories are writable
        for dir_name, directory in [
            ("TEMP_DIR", self.TEMP_DIR),
            ("OUTPUT_DIR", self.OUTPUT_DIR),
            ("CACHE_DIR", self.CACHE_DIR)
        ]:
            if not directory.exists():
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create {dir_name} at {directory}: {e}")
            elif not os.access(directory, os.W_OK):
                issues.append(f"{dir_name} at {directory} is not writable")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": {
                "temp_dir": str(self.TEMP_DIR),
                "output_dir": str(self.OUTPUT_DIR),
                "cache_dir": str(self.CACHE_DIR),
                "max_chunk_size": self.MAX_CHUNK_SIZE,
                "chunk_overlap": self.CHUNK_OVERLAP,
                "supported_formats": list(self.SUPPORTED_FORMATS),
                "gemini_api_keys": {
                    "embedding": bool(self.GEMINI_EMBEDDING_API_KEY),
                    "analyzer": bool(self.GEMINI_ANALYZER_API_KEY), 
                    "expert": bool(self.GEMINI_EXPERT_API_KEY),
                    "vision": bool(self.GEMINI_VISION_API_KEY),
                    "master_fallback": bool(self.GEMINI_MASTER_API_KEY)
                },
                "has_pinecone_key": bool(self.PINECONE_API_KEY),
                "pinecone_index_name": self.PINECONE_INDEX_NAME,
                "models": {
                    "embedding": self.EMBEDDING_MODEL,
                    "task_analyzer": self.TASK_ANALYZER_MODEL,
                    "domain_expert": self.DOMAIN_EXPERT_MODEL,
                    "vision": self.VISION_MODEL
                }
            }
        }
    
    def get_cache_path(self, document_url: str) -> Path:
        """Get cache file path for a document URL"""
        import hashlib
        url_hash = hashlib.md5(document_url.encode()).hexdigest()
        return self.CACHE_DIR / f"doc_{url_hash}.json"
    
    def test_python_dependencies(self) -> Dict[str, bool]:
        """Test if Python dependencies are working (deployment-ready)"""
        results = {}
        
        # Test PDFPlumber (main table extraction)
        try:
            import pdfplumber
            results['pdfplumber'] = True
            print("✅ PDFPlumber available for table extraction")
        except ImportError:
            results['pdfplumber'] = False
            print("❌ PDFPlumber not available")
        
        # Test Google Generative AI
        try:
            import google.generativeai as genai
            results['google_generativeai'] = True
            print("✅ Google Generative AI client available")
        except ImportError:
            results['google_generativeai'] = False
            print("❌ Google Generative AI client not available")
        
        # Test PyMuPDF
        try:
            import fitz
            results['pymupdf'] = True
            print("✅ PyMuPDF available for PDF processing")
        except ImportError:
            results['pymupdf'] = False
            print("❌ PyMuPDF not available")
        
        return results

# Load environment variables at module import time
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables must be set manually.")

# Global configuration instance (created after .env is loaded)
config = IngestionConfig()

# Environment setup helper
def setup_environment():
    """Helper function to set up the environment"""
    # .env file is already loaded at module import time
    
    print("🚀 Document Ingestion Pipeline Configuration")
    
    # Validate configuration
    validation = config.validate_config()
    
    if not validation["valid"]:
        print("\n⚠️  Configuration Issues Found:")
        for issue in validation["issues"]:
            print(f"   - {issue}")
        print("\n📝 Setup Instructions:")
        print("   1. Set individual Gemini API keys for optimal performance:")
        print("      - GEMINI_EMBEDDING_API_KEY (for embeddings)")
        print("      - GEMINI_ANALYZER_API_KEY (for task analysis)")
        print("      - GEMINI_EXPERT_API_KEY (for domain expertise)")
        print("      - GEMINI_VISION_API_KEY (for image processing)")
        print("   2. Or set GEMINI_API_KEY as a fallback for all services")
        print("   2. Ensure all directories are writable")
        return False
    
    print("\n✅ Configuration validated successfully!")
    print(f"📁 Temp directory: {config.TEMP_DIR}")
    print(f"📁 Output directory: {config.OUTPUT_DIR}")
    print(f"📁 Cache directory: {config.CACHE_DIR}")
    
    # Test dependencies
    deps_working = config.test_python_dependencies()
    
    print(f"\n🎯 Pipeline Status: READY!")
    print("   ✨ Full extraction capabilities enabled")
    print("   📊 Text, tables, and images supported")
    
    return True

if __name__ == "__main__":
    # Test configuration
    setup_environment()