"""
Enhanced FastAPI Backend with RAG Evaluation Metrics
Integration of comprehensive evaluation metrics into the main application

This enhanced version of main.py includes real-time metrics collection
and periodic evaluation reporting for production monitoring.
"""

import os
import time
import uuid
import hashlib
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import existing components
from llm_integration import TwoStageLLMPipeline
from document_ingestion import DocumentIngestionPipeline
from vector_database import VectorDatabasePipeline
from models import DocumentRequest, DocumentResponse, HealthResponse, ErrorResponse
from config import config

# Import new evaluation system
from rag_evaluation_metrics import RAGEvaluationSystem

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
evaluation_system: Optional[RAGEvaluationSystem] = None

# Enhanced metrics tracking
real_time_metrics = {
    'requests_processed': 0,
    'total_latency': 0.0,
    'total_api_calls': 0,
    'total_tokens': 0,
    'total_cost': 0.0,
    'cache_hits': 0,
    'cache_misses': 0,
    'error_count': 0,
    'last_reset': datetime.now()
}

# Request-level detailed tracking
request_history = []
MAX_HISTORY_SIZE = 1000

# Simple in-memory cache (production would use Redis)
document_cache: Dict[str, Any] = {}
response_cache: Dict[str, Any] = {}
CACHE_TTL = 3600  # 1 hour

# Authentication
security = HTTPBearer()


class MetricsCollector:
    """Real-time metrics collection for RAG evaluation"""
    
    def __init__(self):
        self.session_start = datetime.now()
        self.retrieval_metrics = defaultdict(list)
        self.generation_metrics = defaultdict(list)
        self.performance_metrics = defaultdict(list)
        
    def record_request(self, request_data: Dict[str, Any]):
        """Record metrics for a single request"""
        global real_time_metrics, request_history
        
        # Update real-time counters
        real_time_metrics['requests_processed'] += 1
        real_time_metrics['total_latency'] += request_data.get('processing_time', 0.0)
        real_time_metrics['total_api_calls'] += request_data.get('api_calls', 0)
        real_time_metrics['total_tokens'] += request_data.get('tokens_used', 0)
        real_time_metrics['total_cost'] += request_data.get('estimated_cost', 0.0)
        
        if request_data.get('cache_hit'):
            real_time_metrics['cache_hits'] += 1
        else:
            real_time_metrics['cache_misses'] += 1
            
        if request_data.get('error'):
            real_time_metrics['error_count'] += 1
        
        # Store detailed history
        request_history.append({
            'timestamp': datetime.now().isoformat(),
            'request_id': request_data.get('request_id'),
            'processing_time': request_data.get('processing_time', 0.0),
            'api_calls': request_data.get('api_calls', 0),
            'tokens_used': request_data.get('tokens_used', 0),
            'cost': request_data.get('estimated_cost', 0.0),
            'cache_hit': request_data.get('cache_hit', False),
            'error': request_data.get('error', False),
            'confidence': request_data.get('confidence', 0.0),
            'citations_count': request_data.get('citations_count', 0)
        })
        
        # Trim history if too large
        if len(request_history) > MAX_HISTORY_SIZE:
            request_history = request_history[-MAX_HISTORY_SIZE:]
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        if real_time_metrics['requests_processed'] == 0:
            return {
                'avg_latency': 0.0,
                'avg_cost_per_query': 0.0,
                'avg_api_calls': 0.0,
                'cache_hit_rate': 0.0,
                'error_rate': 0.0,
                'throughput': 0.0
            }
        
        session_duration = (datetime.now() - self.session_start).total_seconds()
        processed = real_time_metrics['requests_processed']
        
        return {
            'avg_latency': real_time_metrics['total_latency'] / processed,
            'avg_cost_per_query': real_time_metrics['total_cost'] / processed,
            'avg_api_calls': real_time_metrics['total_api_calls'] / processed,
            'cache_hit_rate': real_time_metrics['cache_hits'] / (real_time_metrics['cache_hits'] + real_time_metrics['cache_misses']),
            'error_rate': real_time_metrics['error_count'] / processed,
            'throughput': processed / max(1, session_duration),
            'total_requests': processed,
            'session_duration': session_duration
        }
    
    def check_performance_targets(self) -> Dict[str, bool]:
        """Check if current performance meets targets"""
        metrics = self.get_current_metrics()
        
        return {
            'latency_target': metrics['avg_latency'] < 30.0,  # <30s
            'cost_target': metrics['avg_cost_per_query'] < 0.50,  # <$0.50
            'api_calls_target': metrics['avg_api_calls'] < 20,  # <20 API calls
            'cache_hit_target': metrics['cache_hit_rate'] > 0.5,  # >50%
            'error_rate_target': metrics['error_rate'] < 0.05  # <5%
        }


# Initialize metrics collector
metrics_collector = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources with metrics"""
    global llm_pipeline, document_pipeline, vector_pipeline, evaluation_system
    
    logger.info("🚀 Initializing Enhanced HackRx 6.0 API with Evaluation Metrics")
    
    try:
        # Initialize existing pipelines
        logger.info("📝 Initializing Document Ingestion Pipeline...")
        document_pipeline = DocumentIngestionPipeline()
        
        logger.info("🔍 Initializing Vector Database Pipeline...")
        vector_pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        
        logger.info("🧠 Initializing Two-Stage LLM Pipeline...")
        llm_pipeline = TwoStageLLMPipeline()
        
        # Initialize evaluation system
        logger.info("🔬 Initializing RAG Evaluation System...")
        evaluation_system = RAGEvaluationSystem(vector_pipeline, llm_pipeline)
        
        # Create sample evaluation dataset for monitoring
        evaluation_system.create_sample_dataset("./evaluation_datasets/monitoring_dataset.json")
        evaluation_system.load_evaluation_dataset("./evaluation_datasets/monitoring_dataset.json", "monitoring")
        
        logger.info("✅ All systems initialized with evaluation metrics!")
        
        # Start background metrics reporting
        asyncio.create_task(periodic_evaluation_report())
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize enhanced system: {e}")
        raise
    
    finally:
        logger.info("🔄 Shutting down enhanced application...")


async def periodic_evaluation_report():
    """Background task to generate periodic evaluation reports"""
    while True:
        try:
            await asyncio.sleep(3600)  # Every hour
            
            logger.info("📊 Generating periodic evaluation report...")
            
            # Get current metrics
            current_metrics = metrics_collector.get_current_metrics()
            targets_met = metrics_collector.check_performance_targets()
            
            # Log performance summary
            logger.info(f"📈 Hourly Performance Summary:")
            logger.info(f"   Requests Processed: {current_metrics['total_requests']}")
            logger.info(f"   Avg Latency: {current_metrics['avg_latency']:.2f}s {'✅' if targets_met['latency_target'] else '❌'}")
            logger.info(f"   Cache Hit Rate: {current_metrics['cache_hit_rate']:.1%} {'✅' if targets_met['cache_hit_target'] else '❌'}")
            logger.info(f"   Error Rate: {current_metrics['error_rate']:.1%} {'✅' if targets_met['error_rate_target'] else '❌'}")
            
            # Run evaluation if we have enough data
            if current_metrics['total_requests'] >= 5:
                try:
                    report = evaluation_system.run_comprehensive_evaluation("monitoring")
                    logger.info(f"🔬 Evaluation Report Generated: Hit Rate {report.retrieval_metrics.hit_rate:.1%}")
                except Exception as e:
                    logger.warning(f"⚠️ Evaluation failed: {e}")
            
        except Exception as e:
            logger.error(f"❌ Periodic evaluation error: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying


# Initialize enhanced FastAPI app
app = FastAPI(
    title="HackRx 6.0 - Enhanced Universal Document Intelligence with Metrics",
    description="AI-powered document analysis with comprehensive evaluation metrics and monitoring",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify Bearer token for authentication"""
    token = credentials.credentials
    
    if not token or len(token) < 16:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    logger.info(f"✅ Valid bearer token received: {token[:8]}...")
    return True


def get_cache_key(documents: str, questions: List[str]) -> str:
    """Generate cache key from request parameters"""
    content = f"{documents}_{sorted(questions)}"
    return hashlib.md5(content.encode()).hexdigest()


def is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """Check if cache entry is still valid"""
    if not cache_entry:
        return False
    timestamp = cache_entry.get("timestamp", 0)
    return (time.time() - timestamp) < CACHE_TTL


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with enhanced health info"""
    current_metrics = metrics_collector.get_current_metrics()
    
    return HealthResponse(
        status="healthy",
        message=f"Enhanced HackRx 6.0 API - {current_metrics['total_requests']} requests processed",
        version="1.1.0",
        timestamp=datetime.now().isoformat(),
        details={
            'avg_latency': current_metrics['avg_latency'],
            'cache_hit_rate': current_metrics['cache_hit_rate'],
            'throughput': current_metrics['throughput']
        }
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with performance metrics"""
    try:
        # Check pipeline status
        pipeline_status = {
            "document_pipeline": document_pipeline is not None,
            "vector_pipeline": vector_pipeline is not None,
            "llm_pipeline": llm_pipeline is not None,
            "evaluation_system": evaluation_system is not None
        }
        
        # Get current performance metrics
        current_metrics = metrics_collector.get_current_metrics()
        targets_met = metrics_collector.check_performance_targets()
        
        all_healthy = all(pipeline_status.values())
        performance_healthy = all(targets_met.values())
        
        overall_status = "healthy" if (all_healthy and performance_healthy) else "degraded"
        
        return HealthResponse(
            status=overall_status,
            message="All systems operational with performance monitoring" if all_healthy else "Some systems degraded",
            version="1.1.0",
            timestamp=datetime.now().isoformat(),
            details={
                **pipeline_status,
                "performance_metrics": current_metrics,
                "targets_met": targets_met
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            message=f"System error: {str(e)}",
            version="1.1.0",
            timestamp=datetime.now().isoformat()
        )


@app.get("/metrics")
async def get_metrics(authenticated: bool = Depends(verify_token)):
    """Get detailed performance metrics"""
    current_metrics = metrics_collector.get_current_metrics()
    targets_met = metrics_collector.check_performance_targets()
    
    # Calculate additional metrics from history
    recent_requests = [r for r in request_history if 
                      datetime.fromisoformat(r['timestamp']) > datetime.now() - timedelta(hours=1)]
    
    return {
        "current_metrics": current_metrics,
        "targets_met": targets_met,
        "recent_performance": {
            "requests_last_hour": len(recent_requests),
            "avg_confidence": sum(r.get('confidence', 0.0) for r in recent_requests) / max(1, len(recent_requests)),
            "avg_citations": sum(r.get('citations_count', 0) for r in recent_requests) / max(1, len(recent_requests))
        },
        "evaluation_status": {
            "system_initialized": evaluation_system is not None,
            "last_evaluation": "Available on demand",
            "datasets_loaded": list(evaluation_system.test_datasets.keys()) if evaluation_system else []
        }
    }


@app.post("/evaluate")
async def run_evaluation(authenticated: bool = Depends(verify_token)):
    """Run comprehensive RAG evaluation on demand"""
    if not evaluation_system:
        raise HTTPException(status_code=500, detail="Evaluation system not initialized")
    
    try:
        logger.info("🔬 Running on-demand evaluation...")
        report = evaluation_system.run_comprehensive_evaluation("monitoring")
        
        return {
            "evaluation_completed": True,
            "timestamp": report.timestamp,
            "retrieval_metrics": {
                "hit_rate": report.retrieval_metrics.hit_rate,
                "mrr": report.retrieval_metrics.mean_reciprocal_rank,
                "precision_at_5": report.retrieval_metrics.precision_at_k.get(5, 0.0)
            },
            "generation_metrics": {
                "faithfulness": report.generation_metrics.faithfulness,
                "citation_accuracy": report.generation_metrics.citation_accuracy,
                "relevance": report.generation_metrics.relevance
            },
            "performance_metrics": {
                "avg_latency": report.performance_metrics.end_to_end_latency,
                "total_api_calls": report.performance_metrics.total_api_calls,
                "cost_per_query": report.performance_metrics.cost_per_query
            },
            "targets_met": {
                "hit_rate_target": report.retrieval_metrics.hit_rate > 0.95,
                "citation_accuracy_target": report.generation_metrics.citation_accuracy > 0.95,
                "latency_target": report.performance_metrics.end_to_end_latency < 30.0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/hackrx/run", response_model=DocumentResponse)
async def process_documents_with_metrics(
    request: DocumentRequest,
    background_tasks: BackgroundTasks,
    authenticated: bool = Depends(verify_token)
) -> DocumentResponse:
    """
    Enhanced main endpoint with comprehensive metrics collection
    """
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Initialize request tracking
    request_metrics = {
        'request_id': request_id,
        'processing_time': 0.0,
        'api_calls': 0,
        'tokens_used': 0,
        'estimated_cost': 0.0,
        'cache_hit': False,
        'error': False,
        'confidence': 0.0,
        'citations_count': 0
    }
    
    logger.info(f"🔍 Processing request {request_id} with metrics tracking")
    
    try:
        # Check cache first
        cache_key = get_cache_key(str(request.documents), request.questions)
        cached_response = response_cache.get(cache_key)
        
        if cached_response and is_cache_valid(cached_response):
            logger.info(f"📋 Cache hit for request {request_id}")
            request_metrics['cache_hit'] = True
            request_metrics['processing_time'] = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_request(request_metrics)
            
            return DocumentResponse(**cached_response["data"])
        
        # Process document using existing pipeline
        doc_url = request.documents
        logger.info(f"📄 Processing document: {doc_url}")
        
        # Document processing with metrics
        doc_start_time = time.time()
        chunks = document_pipeline.process_document_from_url(str(doc_url))
        optimized_chunks = document_pipeline.chunk_document_content(chunks)
        doc_processing_time = time.time() - doc_start_time
        
        # Vector indexing with metrics
        vector_start_time = time.time()
        chunk_data = []
        for chunk in optimized_chunks:
            chunk_dict = {
                "content": chunk.content,
                "content_type": chunk.content_type,
                "metadata": chunk.metadata,
                "page_number": chunk.page_number,
                "source_url": str(doc_url),
                "chunk_id": chunk.chunk_id
            }
            chunk_data.append(chunk_dict)
        
        if not vector_pipeline.create_index():
            raise Exception("Failed to create Pinecone index")
        
        vector_records = vector_pipeline.prepare_vector_records(chunk_data)
        vector_pipeline.upsert_vectors(vector_records, namespace="documents")
        vector_processing_time = time.time() - vector_start_time
        
        # Process questions with enhanced metrics
        results = []
        total_confidence = 0.0
        total_citations = 0
        
        for question in request.questions:
            question_start_time = time.time()
            
            logger.info(f"🤔 Processing question: {question}")
            llm_result = llm_pipeline.process_query(question)
            
            question_processing_time = time.time() - question_start_time
            
            # Extract metrics from LLM result
            performance = llm_result.get("performance", {})
            token_usage = performance.get("token_usage", {})
            
            request_metrics['api_calls'] += performance.get("api_calls", 0)
            request_metrics['tokens_used'] += token_usage.get("total_tokens", 0)
            request_metrics['estimated_cost'] += performance.get("estimated_cost", 0.0)
            
            # Track answer quality metrics
            confidence = llm_result.get("confidence", 0.0)
            citations = llm_result.get("citations", [])
            
            total_confidence += confidence
            total_citations += len(citations)
            
            result = {
                "question": question,
                "answer": llm_result["answer"],
                "confidence": confidence,
                "citations": citations,
                "sections": llm_result.get("sections", []),
                "methodology": llm_result.get("methodology", "two_stage_hybrid_rag"),
                "processing_time": question_processing_time
            }
            
            results.append(result)
            logger.info(f"✅ Question answered: {confidence:.2f} confidence, {len(citations)} citations")
        
        # Calculate final metrics
        total_processing_time = time.time() - start_time
        request_metrics['processing_time'] = total_processing_time
        request_metrics['confidence'] = total_confidence / len(request.questions) if request.questions else 0.0
        request_metrics['citations_count'] = total_citations
        
        # Build response
        answers = [result["answer"] for result in results]
        response_data = {"answers": answers}
        
        # Cache the response
        response_cache[cache_key] = {
            "data": response_data,
            "timestamp": time.time()
        }
        
        # Record comprehensive metrics
        metrics_collector.record_request(request_metrics)
        
        logger.info(f"🎉 Request {request_id} completed with metrics:")
        logger.info(f"   Processing Time: {total_processing_time:.2f}s")
        logger.info(f"   API Calls: {request_metrics['api_calls']}")
        logger.info(f"   Tokens Used: {request_metrics['tokens_used']}")
        logger.info(f"   Estimated Cost: ${request_metrics['estimated_cost']:.4f}")
        logger.info(f"   Avg Confidence: {request_metrics['confidence']:.2f}")
        logger.info(f"   Total Citations: {request_metrics['citations_count']}")
        
        return DocumentResponse(**response_data)
        
    except Exception as e:
        request_metrics['error'] = True
        request_metrics['processing_time'] = time.time() - start_time
        metrics_collector.record_request(request_metrics)
        
        logger.error(f"❌ Request {request_id} failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Development server
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "enhanced_main_with_metrics:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )


