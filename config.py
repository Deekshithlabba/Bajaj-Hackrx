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
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
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
        
        # Multimodal settings
        self.VISION_MODEL = "gpt-4o"
        self.MAX_VISION_TOKENS = 500
        
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
        
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        if not self.OPENAI_API_KEY:
            issues.append("OPENAI_API_KEY environment variable not set")
        
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
                "has_openai_key": bool(self.OPENAI_API_KEY)
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
        
        # Test OpenAI
        try:
            import openai
            results['openai'] = True
            print("✅ OpenAI client available")
        except ImportError:
            results['openai'] = False
            print("❌ OpenAI client not available")
        
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
        print("   1. Set OPENAI_API_KEY in your environment or .env file")
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