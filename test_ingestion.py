"""
Sample usage script for the Document Ingestion Pipeline
This demonstrates how to use the ingestion pipeline with your sample datasets
"""

import os
import json
from pathlib import Path
from document_ingestion import DocumentIngestionPipeline
from config import setup_environment, config

def test_with_sample_documents():
    """Test the ingestion pipeline with sample documents"""
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed. Please check configuration.")
        return
    
    # Initialize the pipeline
    try:
        pipeline = DocumentIngestionPipeline(
            openai_api_key=config.OPENAI_API_KEY,
            temp_dir=str(config.TEMP_DIR)
        )
        print("✅ Pipeline initialized successfully!")
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        return
    
    # Sample document URLs (replace these with your actual sample datasets)
    sample_documents = [
        # Add your sample document URLs here
        "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D",
        # "https://example.com/sample_legal_contract.pdf",
        # "https://example.com/sample_hr_handbook.docx",
    ]
    
    # If no URLs provided, create a test with local files
    if not sample_documents:
        print("📝 No sample URLs provided. Looking for local test files...")
        test_files = list(Path(".").glob("*.pdf")) + list(Path(".").glob("*.docx"))
        
        if test_files:
            print(f"Found {len(test_files)} local files to test:")
            for file in test_files:
                print(f"   - {file}")
            
            # Test with first local file
            test_file = test_files[0]
            test_local_file(pipeline, test_file)
        else:
            print("⚠️  No test documents found. Please either:")
            print("   1. Add URLs to the sample_documents list in this script")
            print("   2. Place some PDF or DOCX files in this directory")
            print("   3. Use the pipeline directly with: pipeline.process_document_from_url(url)")
        return
    
    # Process each sample document
    for i, doc_url in enumerate(sample_documents, 1):
        print(f"\n🔄 Processing document {i}/{len(sample_documents)}: {doc_url}")
        
        try:
            # Process the document
            chunks = pipeline.process_document_from_url(doc_url)
            print(f"✅ Extracted {len(chunks)} initial chunks")
            
            # Optimize chunk sizes
            optimized_chunks = pipeline.chunk_document_content(
                chunks,
                max_chunk_size=config.MAX_CHUNK_SIZE,
                overlap_size=config.CHUNK_OVERLAP
            )
            print(f"✅ Optimized to {len(optimized_chunks)} chunks")
            
            # Show sample of extracted content
            show_sample_chunks(optimized_chunks, doc_url)
            
            # Export results
            output_file = config.OUTPUT_DIR / f"chunks_doc_{i}.json"
            pipeline.export_chunks_to_json(optimized_chunks, str(output_file))
            print(f"💾 Results saved to: {output_file}")
            
            # Generate summary report
            generate_processing_report(optimized_chunks, output_file.with_suffix('.txt'))
            
        except Exception as e:
            print(f"❌ Error processing {doc_url}: {str(e)}")
            continue

def test_local_file(pipeline, file_path: Path):
    """Test processing with a local file"""
    print(f"\n🔄 Testing with local file: {file_path}")
    
    # For local files, we need to create a file:// URL or use the file directly
    # This is a simplified version - in production you'd upload to a URL
    try:
        # Convert to absolute path URL
        file_url = file_path.absolute().as_uri()
        
        # Process the document
        chunks = pipeline.process_document_from_url(file_url)
        print(f"✅ Extracted {len(chunks)} initial chunks")
        
        # Optimize chunk sizes
        optimized_chunks = pipeline.chunk_document_content(chunks)
        print(f"✅ Optimized to {len(optimized_chunks)} chunks")
        
        # Show sample content
        show_sample_chunks(optimized_chunks, str(file_path))
        
        # Export results
        output_file = config.OUTPUT_DIR / f"test_{file_path.stem}_chunks.json"
        pipeline.export_chunks_to_json(optimized_chunks, str(output_file))
        print(f"💾 Results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing local file: {str(e)}")

def show_sample_chunks(chunks, source):
    """Display sample chunks for inspection"""
    print(f"\n📋 Sample chunks from {Path(source).name}:")
    
    # Group chunks by type
    chunk_types = {}
    for chunk in chunks:
        chunk_type = chunk.content_type
        if chunk_type not in chunk_types:
            chunk_types[chunk_type] = []
        chunk_types[chunk_type].append(chunk)
    
    # Show summary
    print(f"   Content types found:")
    for chunk_type, type_chunks in chunk_types.items():
        print(f"   - {chunk_type}: {len(type_chunks)} chunks")
    
    # Show sample from each type
    for chunk_type, type_chunks in chunk_types.items():
        sample_chunk = type_chunks[0]
        print(f"\n   📄 Sample {chunk_type} chunk:")
        print(f"      Page: {sample_chunk.page_number}")
        print(f"      Content: {sample_chunk.content[:150]}...")
        if sample_chunk.metadata:
            print(f"      Metadata: {sample_chunk.metadata}")

def generate_processing_report(chunks, output_path):
    """Generate a human-readable processing report"""
    report_lines = []
    report_lines.append("DOCUMENT PROCESSING REPORT")
    report_lines.append("=" * 50)
    report_lines.append(f"Total chunks: {len(chunks)}")
    report_lines.append(f"Generated at: {config.OUTPUT_DIR}")
    report_lines.append("")
    
    # Analyze content types
    content_types = {}
    total_content_length = 0
    pages = set()
    
    for chunk in chunks:
        content_type = chunk.content_type
        content_types[content_type] = content_types.get(content_type, 0) + 1
        total_content_length += len(chunk.content)
        pages.add(chunk.page_number)
    
    report_lines.append("CONTENT ANALYSIS:")
    report_lines.append(f"- Total pages processed: {len(pages)}")
    report_lines.append(f"- Total content length: {total_content_length:,} characters")
    report_lines.append(f"- Average chunk size: {total_content_length // len(chunks):,} characters")
    report_lines.append("")
    
    report_lines.append("CONTENT TYPES:")
    for content_type, count in content_types.items():
        percentage = (count / len(chunks)) * 100
        report_lines.append(f"- {content_type}: {count} chunks ({percentage:.1f}%)")
    
    report_lines.append("")
    report_lines.append("SAMPLE CHUNKS:")
    report_lines.append("-" * 30)
    
    # Show sample chunks
    for i, chunk in enumerate(chunks[:5]):  # Show first 5 chunks
        report_lines.append(f"\nChunk {i+1} ({chunk.content_type}):")
        report_lines.append(f"Page: {chunk.page_number}")
        report_lines.append(f"ID: {chunk.chunk_id}")
        report_lines.append(f"Content: {chunk.content[:200]}...")
        report_lines.append("")
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"📊 Processing report saved to: {output_path}")

def demo_chunk_analysis():
    """Demonstrate different types of content analysis"""
    print("\n🔍 ANALYSIS CAPABILITIES:")
    print("The ingestion pipeline can extract and process:")
    print("✅ Text content with layout preservation")
    print("✅ Tables converted to markdown format")
    print("✅ Images with AI-generated descriptions")
    print("✅ Headings and document structure")
    print("✅ Rich metadata for explainability")
    print("\n📊 Each chunk includes:")
    print("- Content type (text, table, image, heading)")
    print("- Page number and source URL")
    print("- Bounding box coordinates (when available)")
    print("- Processing metadata (word count, accuracy, etc.)")
    print("- Unique chunk ID for reference")

if __name__ == "__main__":
    print("🚀 Document Ingestion Pipeline Test")
    print("=" * 50)
    
    # Show capabilities
    demo_chunk_analysis()
    
    # Run tests
    test_with_sample_documents()
    
    print("\n✨ Test completed!")
    print(f"📁 Check the '{config.OUTPUT_DIR}' directory for results")
    print("\n💡 Next steps:")
    print("1. Review the generated JSON files to see extracted chunks")
    print("2. Check the processing reports for analysis summaries")
    print("3. Integrate this pipeline with Person 2's vector database code")
    print("4. Test with your actual HackRx sample documents")