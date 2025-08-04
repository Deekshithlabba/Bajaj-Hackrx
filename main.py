"""
FastAPI Backend - Person 4
HackRx 6.0 Universal Document Intelligence System

Author: Person 4 - Backend & API Architect
Purpose: RESTful API wrapper for the complete document intelligence pipeline
"""

import os
import time
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our complete pipeline (Person 1+2+3 work)
from llm_integration import TwoStageLLMPipeline
from document_ingestion import DocumentIngestionPipeline
from vector_database import VectorDatabasePipeline
from models import DocumentRequest, DocumentResponse, HealthResponse, ErrorResponse
from config import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global pipeline instances
llm_pipeline: Optional[TwoStageLLMPipeline] = None
document_pipeline: Optional[DocumentIngestionPipeline] = None
vector_pipeline: Optional[VectorDatabasePipeline] = None

# Simple in-memory cache (production would use Redis)
document_cache: Dict[str, Any] = {}
response_cache: Dict[str, Any] = {}
CACHE_TTL = 3600  # 1 hour

# Authentication
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    global llm_pipeline, document_pipeline, vector_pipeline
    
    logger.info("🚀 Initializing HackRx 6.0 Document Intelligence API")
    
    try:
        # Initialize all pipeline components
        logger.info("📝 Initializing Document Ingestion Pipeline...")
        document_pipeline = DocumentIngestionPipeline(
            openai_api_key=config.OPENAI_API_KEY
        )
        
        logger.info("🔍 Initializing Vector Database Pipeline...")
        vector_pipeline = VectorDatabasePipeline()
        
        logger.info("🧠 Initializing Two-Stage LLM Pipeline...")
        llm_pipeline = TwoStageLLMPipeline()
        
        logger.info("✅ All pipelines initialized successfully!")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipelines: {e}")
        raise
    
    finally:
        logger.info("🔄 Shutting down application...")


# Initialize FastAPI app
app = FastAPI(
    title="HackRx 6.0 - Universal Document Intelligence System",
    description="AI-powered document analysis with two-stage reasoning and complete explainability",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication dependency
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Verify Bearer token - now used as OpenAI API key"""
    token = credentials.credentials
    
    # Basic token validation - assuming it's an OpenAI API key
    if not token or len(token) < 10:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token (expected OpenAI API key)",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Additional validation for OpenAI API key format
    if not token.startswith(('sk-', 'sk-proj-')):
        logger.warning(f"Bearer token doesn't look like OpenAI API key: {token[:10]}...")
        # Still allow it - will fallback to env key if this fails
    
    return token


# Cache utilities
def get_cache_key(documents: List[str], questions: List[str]) -> str:
    """Generate cache key from request parameters"""
    import hashlib
    content = f"{sorted(documents)}_{sorted(questions)}"
    return hashlib.md5(content.encode()).hexdigest()


def is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """Check if cache entry is still valid"""
    if not cache_entry:
        return False
    
    timestamp = cache_entry.get("timestamp", 0)
    return (time.time() - timestamp) < CACHE_TTL


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - API health check"""
    return HealthResponse(
        status="healthy",
        message="HackRx 6.0 Document Intelligence API is running",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check endpoint"""
    try:
        # Check pipeline status
        pipeline_status = {
            "document_pipeline": document_pipeline is not None,
            "vector_pipeline": vector_pipeline is not None,
            "llm_pipeline": llm_pipeline is not None
        }
        
        all_healthy = all(pipeline_status.values())
        
        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            message="All systems operational" if all_healthy else "Some systems unavailable",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            details=pipeline_status
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"System error: {str(e)}",
            version="1.0.0",
            timestamp=datetime.now().isoformat()
        )


@app.post("/hackrx/run", response_model=DocumentResponse)
async def process_documents(
    request: DocumentRequest,
    background_tasks: BackgroundTasks,
    openai_api_key: str = Depends(verify_token)
) -> DocumentResponse:
    """
    Main HackRx 6.0 endpoint - Process documents and answer questions
    
    This endpoint implements the complete document intelligence pipeline:
    1. Document ingestion and processing (Person 1)
    2. Vector database indexing and search (Person 2) 
    3. Two-stage LLM reasoning with citations (Person 3)
    4. RESTful API response formatting (Person 4)
    """
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(f"🔍 Processing request {request_id}: {len(request.documents)} docs, {len(request.questions)} questions")
    logger.info(f"🔑 Using OpenAI API key: {openai_api_key[:10]}...")
    
    try:
        # Initialize pipelines with the provided API key (bearer token)
        # Create new instances per request to use the specific API key
        try:
            request_document_pipeline = DocumentIngestionPipeline(openai_api_key=openai_api_key)
            request_llm_pipeline = TwoStageLLMPipeline(openai_api_key=openai_api_key)
            logger.info("✅ Pipelines initialized with provided API key")
        except Exception as api_key_error:
            logger.warning(f"⚠️ Failed to initialize with provided API key: {api_key_error}")
            logger.info("🔄 Falling back to environment API key")
            request_document_pipeline = document_pipeline  # Use global instance
            request_llm_pipeline = llm_pipeline  # Use global instance
        
        # Check cache first
        cache_key = get_cache_key(request.documents, request.questions)
        cached_response = response_cache.get(cache_key)
        
        if cached_response and is_cache_valid(cached_response):
            logger.info(f"📋 Cache hit for request {request_id}")
            return DocumentResponse(**cached_response["data"])
        
        # Initialize response structure
        results = []
        processing_stats = {
            "total_documents": len(request.documents),
            "total_questions": len(request.questions),
            "documents_processed": 0,
            "questions_answered": 0,
            "total_chunks_processed": 0,
            "total_tokens_used": 0,
            "total_cost": 0.0
        }
        
        # Process each document
        all_processed_chunks = []
        
        for doc_url in request.documents:
            try:
                logger.info(f"📄 Processing document: {doc_url}")
                
                # Check document cache
                doc_cache_key = f"doc_{hashlib.md5(str(doc_url).encode()).hexdigest()}"
                cached_chunks = document_cache.get(doc_cache_key)
                
                if cached_chunks and is_cache_valid(cached_chunks):
                    logger.info(f"📋 Using cached chunks for document: {doc_url}")
                    chunks = cached_chunks["data"]
                else:
                    # Process document using Person 1's pipeline with provided API key
                    logger.info(f"🔄 Processing new document: {doc_url}")
                    chunks = request_document_pipeline.process_document_from_url(str(doc_url))
                    optimized_chunks = request_document_pipeline.chunk_document_content(chunks)
                    
                    # Cache the processed chunks
                    document_cache[doc_cache_key] = {
                        "data": optimized_chunks,
                        "timestamp": time.time()
                    }
                    chunks = optimized_chunks
                
                # Index chunks in vector database using Person 2's pipeline
                logger.info(f"🔍 Indexing {len(chunks)} chunks in vector database")
                
                # Convert chunks to the format expected by vector pipeline
                chunk_data = []
                for chunk in chunks:
                    chunk_dict = {
                        "content": chunk.content,
                        "content_type": chunk.content_type,
                        "metadata": chunk.metadata,
                        "page_number": chunk.page_number,
                        "source_url": str(doc_url),
                        "chunk_id": chunk.chunk_id
                    }
                    chunk_data.append(chunk_dict)
                
                # Process through vector pipeline
                vector_records = vector_pipeline.prepare_vector_records(chunk_data)
                vector_pipeline.upsert_vectors(vector_records, namespace="documents")
                
                all_processed_chunks.extend(chunks)
                processing_stats["documents_processed"] += 1
                processing_stats["total_chunks_processed"] += len(chunks)
                
                logger.info(f"✅ Document processed: {len(chunks)} chunks indexed")
                
            except Exception as e:
                logger.error(f"❌ Failed to process document {doc_url}: {e}")
                # Continue with other documents
                continue
        
        # Process each question using Person 3's LLM pipeline
        for question in request.questions:
            try:
                logger.info(f"🤔 Processing question: {question}")
                
                # Use Person 3's complete LLM pipeline with provided API key
                llm_result = request_llm_pipeline.process_query(question)
                
                # Update processing stats
                processing_stats["questions_answered"] += 1
                processing_stats["total_tokens_used"] += llm_result["performance"]["token_usage"]["total_tokens"]
                processing_stats["total_cost"] += llm_result["performance"]["estimated_cost"]
                
                # Format result for API response
                question_result = {
                    "question": question,
                    "answer": llm_result["answer"],
                    "confidence": llm_result["confidence"],
                    "citations": llm_result["citations"],
                    "sections": llm_result.get("sections", []),
                    "methodology": llm_result.get("methodology", "two_stage_hybrid_rag"),
                    "processing_time": llm_result["performance"]["total_processing_time"]
                }
                
                results.append(question_result)
                
                logger.info(f"✅ Question answered: {llm_result['confidence']:.2f} confidence, {len(llm_result['citations'])} citations")
                
            except Exception as e:
                logger.error(f"❌ Failed to process question '{question}': {e}")
                # Add error result
                results.append({
                    "question": question,
                    "answer": f"Error processing question: {str(e)}",
                    "confidence": 0.0,
                    "citations": [],
                    "sections": [],
                    "methodology": "error",
                    "processing_time": 0.0
                })
        
        # Build final response - simple answers array format
        total_processing_time = time.time() - start_time
        
        # Extract just the answers from results
        answers = [result["answer"] for result in results]
        
        response_data = {
            "answers": answers
        }
        
        # Cache the response
        response_cache[cache_key] = {
            "data": response_data,
            "timestamp": time.time()
        }
        
        logger.info(f"🎉 Request {request_id} completed: {total_processing_time:.2f}s, {processing_stats['questions_answered']} questions answered")
        
        return DocumentResponse(**response_data)
        
    except Exception as e:
        logger.error(f"❌ Request {request_id} failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_type="http_error",
            message=exc.detail,
            status_code=exc.status_code,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_type="internal_error",
            message="Internal server error",
            status_code=500,
            timestamp=datetime.now().isoformat(),
            details=str(exc) if config.DEBUG else None
        ).dict()
    )


# Development server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )