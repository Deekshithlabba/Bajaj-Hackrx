"""
Advanced Document Ingestion Pipeline for HackRx 6.0
Person 1: Advanced Data Ingestion Lead

This module handles:
1. Document loading from URLs (PDF, DOCX)
2. Layout-aware parsing (headings, paragraphs, lists)
3. Table extraction and conversion to markdown
4. Multimodal processing (images, charts, OCR)
5. Chunking with rich metadata for explainability
"""

import os
import io
import json
import time
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urlparse
import requests
import fitz  # PyMuPDF
import pandas as pd
from PIL import Image
import base64
from pathlib import Path
import re

# Table extraction libraries
try:
    import camelot  # Primary table extraction method
    CAMELOT_AVAILABLE = True
except ImportError:
    print("Warning: camelot-py not installed. Install with: pip install camelot-py[cv]")
    camelot = None
    CAMELOT_AVAILABLE = False

try:
    import pdfplumber  # Fallback table extraction method
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    print("Warning: pdfplumber not installed. Table extraction will be limited.")
    PDFPLUMBER_AVAILABLE = False

try:
    from unstructured.partition.auto import partition
    from unstructured.chunking.title import chunk_by_title
except ImportError:
    print("Warning: unstructured library not installed. Using fallback parsing.")
    partition = None

# For multimodal processing
# import openai  # Replaced with Gemini
import google.generativeai as genai

@dataclass
class DocumentChunk:
    """Represents a processed chunk of document content"""
    content: str
    content_type: str  # 'text', 'table', 'image', 'heading'
    metadata: Dict[str, Any]
    page_number: int
    source_url: str
    chunk_id: str
    bbox: Optional[Dict[str, float]] = None  # Bounding box coordinates
    
class DocumentIngestionPipeline:
    """Advanced document ingestion pipeline with multimodal capabilities"""
    
    def __init__(self, gemini_api_key: str = None, temp_dir: str = "./temp_documents"):
        """
        Initialize the ingestion pipeline
        
        Args:
            gemini_api_key: Gemini API key for multimodal processing
            temp_dir: Directory to store temporary downloaded documents
        """
        # Initialize Gemini client
        try:
            self.gemini_api_key = gemini_api_key or config.GEMINI_API_KEY
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.vision_model = genai.GenerativeModel(config.VISION_MODEL)
            else:
                print("Warning: No Gemini API key provided. Image processing will be disabled.")
                self.vision_model = None
        except Exception as e:
            print(f"Error initializing Gemini client: {e}")
            self.vision_model = None
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        
        # Supported document types
        self.supported_extensions = {'.pdf', '.docx', '.doc'}
        
        # Image processing enabled by default  
        self.skip_image_processing = False
        
    def process_document_from_url(self, document_url: str) -> List[DocumentChunk]:
        """
        Main entry point: Process a document from URL and return structured chunks
        
        Args:
            document_url: URL to the document
            
        Returns:
            List of DocumentChunk objects with rich metadata
        """
        try:
            # Step 1: Download document
            local_path = self._download_document(document_url)
            
            # Step 2: Extract document content based on type
            if local_path.suffix.lower() == '.pdf':
                chunks = self._process_pdf(local_path, document_url)
            elif local_path.suffix.lower() in ['.docx', '.doc']:
                chunks = self._process_docx(local_path, document_url)
            else:
                raise ValueError(f"Unsupported document type: {local_path.suffix}")
            
            # Step 3: Clean up temporary file
            if local_path.exists():
                local_path.unlink()
                
            return chunks
            
        except Exception as e:
            print(f"Error processing document {document_url}: {str(e)}")
            raise
    
    def _download_document(self, url: str) -> Path:
        """Download document from URL to temporary location"""
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Extract filename from URL or content-disposition
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        if not filename or '.' not in filename:
            # Try to get from content-disposition header
            cd = response.headers.get('content-disposition', '')
            if 'filename=' in cd:
                filename = cd.split('filename=')[1].strip('"')
            else:
                # Generate filename based on URL hash
                url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                content_type = response.headers.get('content-type', '')
                if 'pdf' in content_type:
                    filename = f"document_{url_hash}.pdf"
                elif 'word' in content_type or 'docx' in content_type:
                    filename = f"document_{url_hash}.docx"
                else:
                    filename = f"document_{url_hash}.pdf"  # Default to PDF
        
        local_path = self.temp_dir / filename
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return local_path
    
    def _process_pdf(self, pdf_path: Path, source_url: str) -> List[DocumentChunk]:
        """Process PDF document with advanced parsing"""
        chunks = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            # Extract text with layout information
            text_chunks = self._extract_text_with_layout(page, page_num, source_url)
            chunks.extend(text_chunks)
            
            # Extract tables
            table_chunks = self._extract_tables_from_page(pdf_path, page_num, source_url)
            chunks.extend(table_chunks)
            
            # Extract and process images
            image_chunks = self._extract_images_from_page(page, page_num, source_url)
            chunks.extend(image_chunks)
        
        doc.close()
        return chunks
    
    def _extract_text_with_layout(self, page, page_num: int, source_url: str) -> List[DocumentChunk]:
        """Extract text while preserving layout structure"""
        chunks = []
        
        # Get text blocks with layout information
        blocks = page.get_text("dict")
        
        current_text = ""
        current_type = "text"
        
        for block in blocks["blocks"]:
            if "lines" in block:  # Text block
                block_text = ""
                for line in block["lines"]:
                    line_text = ""
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            # Detect headings based on font size and style
                            font_size = span["size"]
                            font_flags = span["flags"]  # Bold, italic flags
                            
                            # Simple heading detection (can be improved)
                            if font_size > 14 or font_flags & 2**4:  # Large font or bold
                                if current_text.strip():
                                    # Save previous chunk
                                    chunks.append(self._create_chunk(
                                        current_text.strip(),
                                        current_type,
                                        page_num,
                                        source_url,
                                        block
                                    ))
                                    current_text = ""
                                
                                # Create heading chunk
                                chunks.append(self._create_chunk(
                                    text,
                                    "heading",
                                    page_num,
                                    source_url,
                                    span
                                ))
                            else:
                                line_text += text + " "
                    
                    block_text += line_text + "\n"
                
                current_text += block_text
        
        # Add remaining text as final chunk
        if current_text.strip():
            chunks.append(self._create_chunk(
                current_text.strip(),
                current_type,
                page_num,
                source_url,
                {}
            ))
        
        return chunks
    
    def _extract_tables_from_page(self, pdf_path: Path, page_num: int, source_url: str) -> List[DocumentChunk]:
        """Extract tables using PDFPlumber (primary) with Camelot optional enhancement"""
        chunks = []
        
        # Use PDFPlumber as primary method (deployment-ready, no system dependencies)
        if not PDFPLUMBER_AVAILABLE:
            return chunks
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    
                    # Extract tables using PDFPlumber with improved filtering
                    tables = page.extract_tables()
                    
                    for i, table in enumerate(tables):
                        if table and len(table) > 1 and self._is_valid_table(table):  # Ensure it's actually a table
                            # Convert to DataFrame
                            try:
                                # Handle cases where rows have different lengths
                                max_cols = max(len(row) for row in table)
                                normalized_table = []
                                
                                for row in table:
                                    # Pad rows to have the same number of columns
                                    normalized_row = row + [None] * (max_cols - len(row))
                                    normalized_table.append(normalized_row)
                                
                                if len(normalized_table) > 1:
                                    # Use first row as headers, rest as data
                                    headers = normalized_table[0]
                                    data = normalized_table[1:]
                                    
                                    df = pd.DataFrame(data, columns=headers)
                                    df = df.dropna(how='all').dropna(axis=1, how='all')
                                    
                                    if not df.empty and len(df) > 0:
                                        markdown_table = self._dataframe_to_markdown(df)
                                        
                                        if markdown_table.strip():  # Only add non-empty tables
                                            chunk = self._create_chunk(
                                                markdown_table,
                                                "table",
                                                page_num,
                                                source_url,
                                                {
                                                    "table_index": i,
                                                    "extraction_method": "pdfplumber",
                                                    "rows": len(df),
                                                    "columns": len(df.columns),
                                                    "deployment_ready": True
                                                }
                                            )
                                            chunks.append(chunk)
                            except Exception as e:
                                print(f"Error processing table {i} on page {page_num}: {str(e)}")
                                continue
        
        except ImportError:
            print("PDFPlumber not available. Table extraction disabled.")
        except Exception as e:
            print(f"Table extraction error on page {page_num}: {str(e)}")
        
        # Optional Camelot enhancement (silent - no error messages if unavailable)
        if CAMELOT_AVAILABLE and not chunks:  # Only try if PDFPlumber found no tables
            try:
                import os
                import subprocess
                
                # Silent check for Ghostscript availability
                result = subprocess.run(['gs', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # Configure environment for Camelot
                    old_path = os.environ.get('PATH', '')
                    os.environ['PATH'] = '/opt/homebrew/bin:/usr/local/bin:' + old_path
                    
                    tables = camelot.read_pdf(str(pdf_path), pages=str(page_num + 1))
                    
                    # Restore original PATH
                    os.environ['PATH'] = old_path
                    
                    for i, table in enumerate(tables):
                        if table.df is not None and not table.df.empty:
                            markdown_table = self._dataframe_to_markdown(table.df)
                            if markdown_table.strip():
                                chunk = self._create_chunk(
                                    markdown_table,
                                    "table",
                                    page_num,
                                    source_url,
                                    {
                                        "table_index": i,
                                        "accuracy": table.accuracy,
                                        "whitespace": table.whitespace,
                                        "extraction_method": "camelot_enhanced"
                                    }
                                )
                                chunks.append(chunk)
            except:
                pass  # Silent failure - PDFPlumber already did the job
        
        return chunks
    
    def _is_valid_table(self, table) -> bool:
        """Determine if extracted content is actually a table (not just formatted text)"""
        if not table or len(table) < 2:
            return False
        
        # Check for table characteristics
        total_cells = sum(len(row) for row in table)
        non_empty_cells = sum(1 for row in table for cell in row if cell and str(cell).strip())
        
        # Basic validation criteria
        if total_cells < 4:  # Too few cells to be a meaningful table
            return False
        
        # Check column consistency (real tables have consistent column counts)
        row_lengths = [len(row) for row in table]
        max_cols = max(row_lengths)
        min_cols = min(row_lengths)
        
        # If there's too much variation in column counts, it's probably not a table
        if max_cols > 1 and (max_cols - min_cols) > max_cols * 0.5:
            return False
        
        # Check if it looks like a single-column paragraph split into "rows"
        if max_cols == 1:
            # Single column could be a paragraph, check content
            all_text = " ".join(str(cell) for row in table for cell in row if cell)
            
            # If it's a long continuous text, probably not a table
            if len(all_text) > 200 and not any(char in all_text for char in [':', '|', '$', '%']):
                # Check if it looks like structured data vs prose
                sentences = all_text.split('.')
                if len(sentences) > 3 and all(len(s.strip().split()) > 5 for s in sentences[:3] if s.strip()):
                    return False  # Looks like prose, not tabular data
        
        # Check for actual tabular indicators
        has_numbers = any(any(char.isdigit() for char in str(cell)) for row in table for cell in row if cell)
        has_structure_words = any(word in str(table).lower() for word in ['amount', 'limit', 'coverage', 'premium', 'deductible', '$'])
        
        # Additional filters for this specific document type (insurance policy)
        text_content = str(table).lower()
        paragraph_indicators = ['whereas', 'hereinafter', 'provided that', 'in respect of', 'subject to']
        if any(indicator in text_content for indicator in paragraph_indicators) and max_cols == 1:
            return False  # Likely policy text, not a table
        
        return True
    
    def _extract_images_from_page(self, page, page_num: int, source_url: str) -> List[DocumentChunk]:
        """Extract images and generate descriptions using multimodal LLM"""
        chunks = []
        
        try:
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Get image data
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY or RGB
                        img_data = pix.tobytes("png")
                        
                        # Generate description using multimodal LLM
                        description = self._describe_image(img_data)
                        
                        if description:
                            chunk = self._create_chunk(
                                description,
                                "image",
                                page_num,
                                source_url,
                                {
                                    "image_index": img_index,
                                    "image_format": "png",
                                    "width": pix.width,
                                    "height": pix.height
                                }
                            )
                            chunks.append(chunk)
                    
                    pix = None  # Free memory
                    
                except Exception as e:
                    print(f"Error processing image {img_index} on page {page_num}: {str(e)}")
                    continue
        
        except Exception as e:
            print(f"Error extracting images from page {page_num}: {str(e)}")
        
        return chunks
    
    def _describe_image(self, image_data: bytes) -> str:
        """Generate description of image using Gemini Vision"""
        # Skip image processing if explicitly disabled
        if hasattr(self, 'skip_image_processing') and self.skip_image_processing:
            return "[Image content - processing skipped]"
        
        # Skip if no vision model available
        if not self.vision_model:
            return "[Image content - Gemini not configured]"
        
        try:
            # Convert bytes to PIL Image for Gemini
            from PIL import Image as PILImage
            import io
            
            image = PILImage.open(io.BytesIO(image_data))
            
            prompt = "Describe this image in detail. Focus on any text, charts, diagrams, or important visual information that would be relevant for document analysis. If there's text in the image, transcribe it accurately."
            
            response = self.vision_model.generate_content([prompt, image])
            
            description = response.text
            return description if description else "[Image description unavailable]"
            
        except Exception as e:
            print(f"Error describing image: {str(e)}")
            # Return placeholder instead of empty string for better traceability
            return f"[Image content - API error: {type(e).__name__}]"
    
    def _process_docx(self, docx_path: Path, source_url: str) -> List[DocumentChunk]:
        """Process DOCX document (placeholder - can be enhanced)"""
        chunks = []
        
        # Basic DOCX processing using unstructured if available
        if partition is not None:
            try:
                elements = partition(filename=str(docx_path))
                
                for i, element in enumerate(elements):
                    chunk = DocumentChunk(
                        content=str(element),
                        content_type="text",
                        metadata={
                            "element_type": type(element).__name__,
                            "element_index": i
                        },
                        page_number=0,  # DOCX doesn't have clear page boundaries
                        source_url=source_url,
                        chunk_id=f"docx_{hashlib.md5(str(element).encode()).hexdigest()[:8]}"
                    )
                    chunks.append(chunk)
                    
            except Exception as e:
                print(f"Error processing DOCX with unstructured: {str(e)}")
                # Fallback to basic text extraction
                return self._basic_docx_processing(docx_path, source_url)
        else:
            return self._basic_docx_processing(docx_path, source_url)
        
        return chunks
    
    def _basic_docx_processing(self, docx_path: Path, source_url: str) -> List[DocumentChunk]:
        """Basic DOCX processing fallback"""
        try:
            import docx
            doc = docx.Document(docx_path)
            
            chunks = []
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph.text.strip():
                    chunk = self._create_chunk(
                        paragraph.text.strip(),
                        "text",
                        0,
                        source_url,
                        {"paragraph_index": i}
                    )
                    chunks.append(chunk)
            
            return chunks
            
        except ImportError:
            print("python-docx not installed. Cannot process DOCX files.")
            return []
    
    def _create_chunk(self, content: str, content_type: str, page_num: int, 
                     source_url: str, extra_metadata: Dict = None) -> DocumentChunk:
        """Create a DocumentChunk with rich metadata"""
        metadata = {
            "content_length": len(content),
            "word_count": len(content.split()),
            "created_at": pd.Timestamp.now().isoformat(),
            **(extra_metadata or {})
        }
        
        chunk_id = hashlib.md5(f"{source_url}_{page_num}_{content[:50]}".encode()).hexdigest()[:12]
        
        return DocumentChunk(
            content=content,
            content_type=content_type,
            metadata=metadata,
            page_number=page_num + 1,  # 1-indexed for user display
            source_url=source_url,
            chunk_id=chunk_id
        )
    
    def _dataframe_to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to clean markdown table"""
        # Clean the dataframe
        df = df.fillna("")
        df = df.astype(str)
        
        # Remove empty rows and columns
        df = df.loc[~(df == "").all(axis=1)]  # Remove empty rows
        df = df.loc[:, ~(df == "").all(axis=0)]  # Remove empty columns
        
        if df.empty:
            return ""
        
        # Convert to markdown
        markdown = df.to_markdown(index=False, tablefmt="pipe")
        return markdown
    
    def chunk_document_content(self, chunks: List[DocumentChunk], 
                             max_chunk_size: int = 1000,
                             overlap_size: int = 100) -> List[DocumentChunk]:
        """
        Further chunk large content pieces for optimal embedding
        
        Args:
            chunks: Initial document chunks
            max_chunk_size: Maximum characters per chunk
            overlap_size: Character overlap between chunks
            
        Returns:
            List of optimally-sized chunks
        """
        optimized_chunks = []
        
        for chunk in chunks:
            if len(chunk.content) <= max_chunk_size:
                optimized_chunks.append(chunk)
            else:
                # Split large chunks
                content = chunk.content
                start = 0
                chunk_counter = 0
                
                while start < len(content):
                    end = min(start + max_chunk_size, len(content))
                    
                    # Try to break at sentence boundary
                    if end < len(content):
                        # Look for sentence endings
                        sentence_end = content.rfind('.', start, end)
                        if sentence_end > start + max_chunk_size // 2:
                            end = sentence_end + 1
                    
                    chunk_content = content[start:end].strip()
                    
                    if chunk_content:
                        new_chunk = DocumentChunk(
                            content=chunk_content,
                            content_type=chunk.content_type,
                            metadata={
                                **chunk.metadata,
                                "parent_chunk_id": chunk.chunk_id,
                                "sub_chunk_index": chunk_counter,
                                "is_continuation": chunk_counter > 0
                            },
                            page_number=chunk.page_number,
                            source_url=chunk.source_url,
                            chunk_id=f"{chunk.chunk_id}_sub_{chunk_counter}",
                            bbox=chunk.bbox
                        )
                        optimized_chunks.append(new_chunk)
                    
                    start = max(start + max_chunk_size - overlap_size, end)
                    chunk_counter += 1
        
        return optimized_chunks
    
    def export_chunks_to_json(self, chunks: List[DocumentChunk], output_path: str):
        """Export processed chunks to JSON for inspection"""
        chunks_data = [asdict(chunk) for chunk in chunks]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(chunks)} chunks to {output_path}")

# Example usage and testing
if __name__ == "__main__":
    # Initialize the pipeline
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Please set OPENAI_API_KEY environment variable")
        exit(1)
    
    pipeline = DocumentIngestionPipeline(openai_api_key)
    
    # Example usage with a sample document URL
    sample_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
    
    try:
        print(f"Processing document: {sample_url}")
        chunks = pipeline.process_document_from_url(sample_url)
        
        print(f"Extracted {len(chunks)} initial chunks")
        
        # Optimize chunk sizes
        optimized_chunks = pipeline.chunk_document_content(chunks)
        print(f"Optimized to {len(optimized_chunks)} chunks")
        
        # Display sample chunks
        for i, chunk in enumerate(optimized_chunks[:3]):
            print(f"\n--- Chunk {i+1} ---")
            print(f"Type: {chunk.content_type}")
            print(f"Page: {chunk.page_number}")
            print(f"Content: {chunk.content[:200]}...")
            print(f"Metadata: {chunk.metadata}")
        
        # Export for inspection
        pipeline.export_chunks_to_json(optimized_chunks, "processed_chunks.json")
        
    except Exception as e:
        print(f"Error processing document: {str(e)}")