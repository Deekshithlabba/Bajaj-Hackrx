# Document Ingestion Pipeline - Person 1

> **Advanced Data Ingestion Lead for HackRx 6.0 Universal Document Intelligence System**

This module implements a sophisticated document ingestion pipeline that transforms complex, multi-format documents into structured, searchable knowledge chunks with rich metadata for explainability.

## 🚀 Features - PRODUCTION READY

### for the example pdf url
✅ **Successfully extracting 802 chunks from test documents**  
✅ **83 tables extracted reliably via PDFPlumber**  
✅ **453 headings + 265 text chunks processed**  
✅ **Clean, professional output with rich metadata**  

### Core Capabilities
- **Multi-format Support**: PDF, DOCX, DOC documents
- **Layout-Aware Parsing**: Preserves document structure (headings, paragraphs, lists)
- **Dual Table Extraction**: PDFPlumber (primary) + Camelot (optional enhancement)
- **Multimodal Processing**: AI-powered image description with GPT-4o
- **Smart Chunking**: Optimized chunk sizes with metadata for retrieval
- **Rich Metadata**: Every chunk tagged with source, page, and processing details

### Key Features
- **🔄 Caching System**: Avoid reprocessing identical documents
- **⚡ Performance Optimization**: Streaming, parallel processing
- **🛡️ Error Handling**: Graceful degradation and detailed error reporting
- **🔍 Explainability**: Complete traceability from answer back to source
- **☁️ Deployment Ready**: Pure Python fallbacks for cloud environments

## 📦 Installation - TESTED & WORKING

### Quick Setup (Recommended)
```bash
# 1. Create and activate virtual environment
python -m venv person1
source person1/bin/activate  # On Windows: person1\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements_ingestion.txt

# 3. Set up environment variables
cp environment_template.txt .env
# Edit .env and set: OPENAI_API_KEY=your_key_here

# 4. Test the pipeline
python test_ingestion.py
```

### Optional: Enhanced Table Extraction
```bash
# For best table extraction quality (optional)
# macOS:
brew install ghostscript poppler

# Ubuntu/Debian:
sudo apt-get install ghostscript poppler-utils

# Windows: Download and install manually, add to PATH
```

**Note**: The pipeline works perfectly without Ghostscript using PDFPlumber as the primary table extractor. Ghostscript installation only provides optional enhancement via Camelot.

## 🔧 Usage

### Basic Usage
```python
from document_ingestion import DocumentIngestionPipeline

# Initialize pipeline
pipeline = DocumentIngestionPipeline(openai_api_key="your_key")

# Process a document
chunks = pipeline.process_document_from_url("https://example.com/doc.pdf")

# Optimize chunk sizes
optimized_chunks = pipeline.chunk_document_content(chunks)

# Export results
pipeline.export_chunks_to_json(optimized_chunks, "output.json")
```

### Advanced Usage
```python
from document_ingestion import DocumentIngestionPipeline
from config import config

# Initialize with custom settings
pipeline = DocumentIngestionPipeline(
    openai_api_key=config.OPENAI_API_KEY,
    temp_dir="./custom_temp"
)

# Process with custom chunking
chunks = pipeline.process_document_from_url(document_url)
optimized_chunks = pipeline.chunk_document_content(
    chunks,
    max_chunk_size=1500,  # Custom chunk size
    overlap_size=150      # Custom overlap
)

# Analyze results
for chunk in optimized_chunks:
    print(f"Type: {chunk.content_type}")
    print(f"Page: {chunk.page_number}")
    print(f"Content: {chunk.content[:100]}...")
    print(f"Metadata: {chunk.metadata}")
```

## 📊 Output Format

Each document is processed into `DocumentChunk` objects with the following structure:

```python
@dataclass
class DocumentChunk:
    content: str              # The actual text/table/image description
    content_type: str         # 'text', 'table', 'image', 'heading'
    metadata: Dict[str, Any]  # Rich metadata for explainability
    page_number: int          # Source page (1-indexed)
    source_url: str          # Original document URL
    chunk_id: str            # Unique identifier
    bbox: Optional[Dict]     # Bounding box coordinates (if available)
```

### Content Types
- **text**: Regular paragraphs and content
- **heading**: Document headings and titles
- **table**: Tables converted to markdown format
- **image**: AI-generated descriptions of images/charts

### Metadata Examples
```json
{
  "content_length": 1247,
  "word_count": 183,
  "created_at": "2024-01-15T10:30:00",
  "table_index": 0,
  "accuracy": 95.6,
  "image_format": "png",
  "width": 800,
  "height": 600
}
```

## 🔍 Testing

### Run Tests
```bash
# Test with sample documents
python test_ingestion.py

# Test configuration
python config.py

# Test specific document
python -c "
from document_ingestion import DocumentIngestionPipeline
pipeline = DocumentIngestionPipeline('your_api_key')
chunks = pipeline.process_document_from_url('your_url')
print(f'Processed {len(chunks)} chunks')
"
```

### Sample Test Documents
Add your HackRx sample document URLs to `test_ingestion.py`:
```python
sample_documents = [
    "https://your-hackrx-sample-1.pdf",
    "https://your-hackrx-sample-2.docx",
    # Add more sample URLs here
]
```

## 🏗️ Architecture

```
Document URL
     ↓
📥 Document Loader
     ↓
📄 Layout-Aware Parser
     ├── Text & Headings
     ├── Tables → Markdown
     └── Images → AI Descriptions
     ↓
🔤 Chunking & Metadata
     ↓
💾 Structured Output
```

### Processing Pipeline (CURRENT)
1. **Download**: Fetch document from URL
2. **Parse**: Extract content with layout preservation using PyMuPDF
3. **Tables**: Convert to markdown using PDFPlumber (primary) + Camelot (optional)
4. **Images**: Generate descriptions using GPT-4o (OpenAI)
5. **Chunk**: Optimize for embedding and retrieval
6. **Metadata**: Tag with rich context for explainability

### Table Extraction Strategy
- **Primary**: PDFPlumber (pure Python, always works)
- **Enhancement**: Camelot (better quality, requires Ghostscript)
- **Smart Validation**: Filters out false table detections
- **Graceful Fallback**: No errors if system dependencies missing

## ⚙️ Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional
TEMP_DIR=./temp_documents
OUTPUT_DIR=./processed_chunks
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=100
```

### Supported Document Types
- **PDF**: Full support with tables and images
- **DOCX**: Text and basic table extraction
- **DOC**: Limited support (converted via unstructured)

### Performance Settings
- **Max File Size**: 50MB default
- **Chunk Size**: 1000 characters default
- **Chunk Overlap**: 100 characters default
- **Caching**: 24-hour default expiry

## 🔧 Integration with Other Components

### With Vector Database (Person 2)
```python
# Person 1: Generate chunks
chunks = pipeline.process_document_from_url(url)
optimized_chunks = pipeline.chunk_document_content(chunks)

# Person 2: Index in vector database
for chunk in optimized_chunks:
    embedding = generate_embedding(chunk.content)
    vector_db.upsert(
        id=chunk.chunk_id,
        values=embedding,
        metadata={
            "content": chunk.content,
            "content_type": chunk.content_type,
            "page_number": chunk.page_number,
            "source_url": chunk.source_url,
            **chunk.metadata
        }
    )
```

### With LLM Pipeline (Person 3)
```python
# Retrieve relevant chunks
relevant_chunks = vector_db.query(user_query)

# Use chunk metadata for citations
for chunk in relevant_chunks:
    citation = f"{chunk.source_url}, Page {chunk.page_number}"
    # Include in LLM prompt for explainability
```

## 🚨 Troubleshooting - CURRENT SOLUTIONS

### ✅ SOLVED: Common Issues

#### Virtual Environment Setup
```bash
# IMPORTANT: Always use the person1 virtual environment
source person1/bin/activate  # Make sure this shows (person1) in prompt
pip install -r requirements_ingestion.txt
```

#### API Configuration
```bash
# 1. Create .env file from template
cp environment_template.txt .env

# 2. Edit .env file and add your OpenAI API key
# OPENAI_API_KEY=your_key_here

# 3. Test configuration
python config.py
```

#### Table Extraction (WORKING SOLUTION)
```python
# ✅ CURRENT STATUS: Working perfectly!
# - PDFPlumber extracts tables reliably (83 tables from test doc)
# - Camelot runs silently (no error messages if Ghostscript unavailable)
# - Smart validation prevents false table detections

# Expected output:
# "✅ Extracted 802 chunks"
# "Content types found: text: 265, heading: 453, table: 83, image: 1"
```

#### Image Processing
```python
# OpenAI API quota issues:
# - Get a valid API key with available quota
# - Images show as "[Image content - API error: RateLimitError]" (expected)
# - Core pipeline still works without image descriptions
```

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test individual components
pipeline._extract_tables_from_page(pdf_path, 0, url)
pipeline._describe_image(image_data)
```

## 📈 Performance Optimization

### Tips for Production
1. **Caching**: Enable document caching for repeated processing
2. **Parallel Processing**: Process multiple documents concurrently
3. **Chunk Size**: Optimize based on your embedding model
4. **Image Processing**: Batch image descriptions for efficiency
5. **Error Handling**: Implement retry logic for API calls

### Monitoring
- Track processing time per document
- Monitor API usage and costs
- Log failed extractions for improvement
- Measure chunk quality and relevance

## 🚀 Usage

### Basic Usage
```python
from document_ingestion import DocumentIngestionPipeline

# Initialize pipeline
pipeline = DocumentIngestionPipeline(openai_api_key="your_key")

# Process a document
chunks = pipeline.process_document_from_url("https://example.com/doc.pdf")

# Optimize chunks
optimized_chunks = pipeline.chunk_document_content(chunks)

# Export results
pipeline.export_chunks_to_json(optimized_chunks, "output.json")
```

## 🎯 INTEGRATION STATUS

### ✅ Person 1 Status: COMPLETE
**Successfully extracting 802 chunks with professional output**

### ✅ Person 2 Status: COMPLETE  
**Successfully integrated with Pinecone vector database with hybrid search**

### 🔄 Person 3 Status: READY TO START
**Two-Stage LLM Integration (Task Analyzer + Domain Expert)**

### 🔗 Handoff to Person 3 (LLM Integration)

1. **Integration Ready**: Use the JSON output from `processed_chunks/`
2. **Chunk Structure**: Each chunk has `content`, `content_type`, `metadata`, `page_number`, `source_url`, `chunk_id`
3. **Testing Data**: Sample chunks available in `processed_chunks/chunks_doc_1.json`
4. **Metadata Rich**: Full traceability for citations and explainability

### 📄 Ready for Person 3: Two-Stage RAG Pipeline

**PERSON 3 STARTS HERE** - Complete retrieval foundation ready:

#### **Stage 1: Task Analyzer (Person 3 Implementation)**
```python
from vector_database import VectorDatabasePipeline

# Initialize the completed vector database (Person 1 + 2 work)
pipeline = VectorDatabasePipeline()

# Task Analyzer retrieval (broad context)
task_context = pipeline.search_similar(
    query=user_question,
    top_k=8,  # More context for task analysis
    hybrid=True,
    semantic_weight=0.8,  # Emphasize semantic understanding
    namespace="documents"
)

# Person 3: Build Task Analyzer LLM
# - Analyze user intent
# - Determine response structure
# - Generate dynamic prompts for Domain Expert
```

#### **Stage 2: Domain Expert (Person 3 Implementation)**
```python
# Domain Expert retrieval (focused expertise) 
expert_context = pipeline.search_similar(
    query=refined_expert_query,  # From Task Analyzer
    top_k=5,  # Focused, high-quality results
    hybrid=True,
    semantic_weight=0.9,  # Heavy semantic focus
    filter_dict={"content_type": "text"},  # Domain filtering
    namespace="documents"
)

# Person 3: Build Domain Expert LLM
# - Deep domain reasoning
# - Generate final structured answer
# - Include citations with metadata
```

#### **Available Search Results Format:**
```python
search_results = {
    "query": "user question about insurance",
    "search_type": "hybrid",  # semantic + keyword
    "semantic_weight": 0.8,
    "results": [
        {
            "score": 0.89,
            "semantic_score": 0.92,  # For analysis
            "keyword_score": 0.78,   # For analysis
            "metadata": {
                "content": "National Insurance Co. Ltd...",
                "content_type": "text",
                "page_number": 1,
                "source_url": "policy.pdf", 
                "chunk_id": "doc_1_chunk_001",
                "word_count": 15,
                "content_length": 95,
                "extraction_method": "pdfplumber"
            }
        }
    ],
    "total_found": 5
}
```

## 📝 Core Files (STEP 1 + 2 COMPLETE)

### **✅ Person 1 Files (Document Ingestion - COMPLETE)**
- ✅ `document_ingestion.py` - Main pipeline (WORKING)
- ✅ `test_ingestion.py` - Testing script (WORKING)
- ✅ `processed_chunks/chunks_doc_1.json` - 802 chunks ready (2.25MB)

### **✅ Person 2 Files (Vector Database - COMPLETE)**
- ✅ `vector_database.py` - Hybrid search pipeline (WORKING)
- ✅ `test_vector_database.py` - Comprehensive testing (WORKING)
- ✅ `test_vector_database_mock.py` - No-API testing (WORKING)
- ✅ `demo_complete_pipeline.py` - Full integration demo (WORKING)

### **📚 Documentation (COMPLETE)**
- ✅ `README_Ingestion.md` - Person 1 documentation
- ✅ `README_VectorDB.md` - Person 2 documentation  
- ✅ `README_LLM_Integration.md` - **Person 3 starting guide**

### **⚙️ Configuration (COMPLETE)**
- ✅ `config.py` - Configuration management (WORKING)
- ✅ `requirements_ingestion.txt` - All dependencies (VERIFIED)
- ✅ `environment_template.txt` - Environment template

## 🤝 Integration Status

### **✅ COMPLETED COMPONENTS:**
- **✅ Person 1**: Document Ingestion (802 chunks extracted and processed)
- **✅ Person 2**: Vector Database with Hybrid Search (Pinecone + OpenAI embeddings)

### **🔄 NEXT COMPONENT:**
- **🚀 Person 3**: Two-Stage LLM Integration (Task Analyzer + Domain Expert)
  - **📖 Start Here**: `README_LLM_Integration.md`
  - **🔧 Foundation Ready**: Use `VectorDatabasePipeline()` for retrieval
  - **🎯 Goal**: Build RAG completion layer on solid retrieval foundation

### **⏳ PENDING COMPONENTS:**
- **Person 4**: Backend API integration
- **Person 5**: Frontend explainability display

---

## 🎉 **STEP 2 COMPLETE - RAG RETRIEVAL FOUNDATION READY!**

**Person 3: Your advanced retrieval system is ready!** 

Check `README_LLM_Integration.md` for your comprehensive starting guide with code examples, architecture details, and integration points.

> **Next Step**: `python -c "from vector_database import VectorDatabasePipeline; print('✅ Ready for Person 3!')"` 🚀