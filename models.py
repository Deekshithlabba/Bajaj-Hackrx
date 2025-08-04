"""
Pydantic Models - Person 4
Request/Response models for HackRx 6.0 API

Author: Person 4 - Backend & API Architect
Purpose: Type-safe API models with validation
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator


class DocumentRequest(BaseModel):
    """
    Request model for /hackrx/run endpoint
    Matches HackRx 6.0 competition specifications
    """
    documents: List[HttpUrl] = Field(
        ...,
        description="List of document URLs to process",
        example=[
            "https://example.com/policy.pdf",
            "https://example.com/claims.docx"
        ]
    )
    
    questions: List[str] = Field(
        ...,
        min_items=1,
        max_items=10,
        description="List of questions to answer from the documents",
        example=[
            "What are the premium calculation methods?",
            "What medical conditions are excluded from coverage?"
        ]
    )
    
    @validator('documents')
    def validate_documents(cls, v):
        if not v:
            raise ValueError('At least one document URL is required')
        if len(v) > 5:
            raise ValueError('Maximum 5 documents allowed per request')
        return v
    
    @validator('questions')
    def validate_questions(cls, v):
        if not v:
            raise ValueError('At least one question is required')
        for question in v:
            if len(question.strip()) < 5:
                raise ValueError('Questions must be at least 5 characters long')
            if len(question) > 500:
                raise ValueError('Questions must be less than 500 characters')
        return v

    class Config:
        schema_extra = {
            "example": {
                "documents": [
                    "https://example.com/insurance-policy.pdf"
                ],
                "questions": [
                    "What are the premium calculation methods?",
                    "What medical conditions are excluded from coverage?"
                ]
            }
        }


class Citation(BaseModel):
    """Citation model with source traceability"""
    source: str = Field(..., description="Source document URL or filename")
    page: int = Field(..., description="Page number in the source document")
    chunk_id: str = Field(..., description="Unique identifier for the text chunk")
    excerpt: str = Field(..., description="Relevant excerpt from the source")
    relevance_score: float = Field(..., description="Relevance score (0.0 to 1.0)")
    content_type: str = Field(..., description="Type of content (text, table, image)")
    section: Optional[str] = Field(None, description="Section title where citation was used")

    class Config:
        schema_extra = {
            "example": {
                "source": "policy.pdf",
                "page": 15,
                "chunk_id": "doc_1_chunk_042",
                "excerpt": "Premium is calculated based on age, health status, and coverage amount...",
                "relevance_score": 0.94,
                "content_type": "text",
                "section": "Premium Calculation Methods"
            }
        }


class ResponseSection(BaseModel):
    """Structured response section with citations"""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    citations: List[Citation] = Field(default=[], description="Citations supporting this section")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for this section")

    class Config:
        schema_extra = {
            "example": {
                "title": "Premium Calculation Methods",
                "content": "Based on the policy documents, premium calculations use multiple factors...",
                "citations": [
                    {
                        "source": "policy.pdf",
                        "page": 15,
                        "chunk_id": "doc_1_chunk_042",
                        "excerpt": "Premium is calculated based on...",
                        "relevance_score": 0.94,
                        "content_type": "text"
                    }
                ],
                "confidence": 0.92
            }
        }


class QuestionResult(BaseModel):
    """Result for a single question"""
    question: str = Field(..., description="The original question")
    answer: str = Field(..., description="Comprehensive answer based on documents")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in the answer")
    citations: List[Citation] = Field(default=[], description="All citations supporting the answer")
    sections: List[ResponseSection] = Field(default=[], description="Structured sections of the response")
    methodology: str = Field(..., description="Analysis methodology used")
    processing_time: float = Field(..., description="Time taken to process this question (seconds)")

    class Config:
        schema_extra = {
            "example": {
                "question": "What are the premium calculation methods?",
                "answer": "Based on the policy documents, premium calculations use multiple factors including age, health status, coverage amount, and risk assessment...",
                "confidence": 0.92,
                "citations": [
                    {
                        "source": "policy.pdf",
                        "page": 15,
                        "chunk_id": "doc_1_chunk_042",
                        "excerpt": "Premium is calculated based on...",
                        "relevance_score": 0.94,
                        "content_type": "text"
                    }
                ],
                "sections": [
                    {
                        "title": "Calculation Factors",
                        "content": "The main factors include...",
                        "citations": [],
                        "confidence": 0.90
                    }
                ],
                "methodology": "two_stage_hybrid_rag",
                "processing_time": 12.5
            }
        }


class ProcessingStats(BaseModel):
    """Processing statistics for the request"""
    total_documents: int = Field(..., description="Total number of documents in request")
    total_questions: int = Field(..., description="Total number of questions in request")
    documents_processed: int = Field(..., description="Number of documents successfully processed")
    questions_answered: int = Field(..., description="Number of questions successfully answered")
    total_chunks_processed: int = Field(..., description="Total number of document chunks processed")
    total_tokens_used: int = Field(..., description="Total LLM tokens used")
    total_cost: float = Field(..., description="Estimated total cost in USD")

    class Config:
        schema_extra = {
            "example": {
                "total_documents": 2,
                "total_questions": 3,
                "documents_processed": 2,
                "questions_answered": 3,
                "total_chunks_processed": 847,
                "total_tokens_used": 12450,
                "total_cost": 0.189
            }
        }


class PerformanceMetrics(BaseModel):
    """Performance metrics for the request"""
    total_processing_time: float = Field(..., description="Total processing time in seconds")
    average_time_per_question: float = Field(..., description="Average processing time per question")
    total_tokens_used: int = Field(..., description="Total tokens used across all LLM calls")
    estimated_total_cost: float = Field(..., description="Estimated total cost in USD")

    class Config:
        schema_extra = {
            "example": {
                "total_processing_time": 45.2,
                "average_time_per_question": 15.1,
                "total_tokens_used": 12450,
                "estimated_total_cost": 0.189
            }
        }


class ResponseMetadata(BaseModel):
    """Response metadata"""
    api_version: str = Field(..., description="API version")
    pipeline_version: str = Field(..., description="Pipeline version identifier")
    timestamp: str = Field(..., description="Response timestamp (ISO format)")
    cached: bool = Field(default=False, description="Whether response was served from cache")

    class Config:
        schema_extra = {
            "example": {
                "api_version": "1.0.0",
                "pipeline_version": "person_1_2_3_complete",
                "timestamp": "2024-01-15T10:30:00.123456",
                "cached": False
            }
        }


class DocumentResponse(BaseModel):
    """
    Response model for /hackrx/run endpoint
    Simple array of answers format
    """
    answers: List[str] = Field(..., description="Array of answers corresponding to the input questions")

    class Config:
        schema_extra = {
            "example": {
                "answers": [
                    "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
                    "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.",
                    "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy."
                ]
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="System status", example="healthy")
    message: str = Field(..., description="Status message", example="All systems operational")
    version: str = Field(..., description="API version", example="1.0.0")
    timestamp: str = Field(..., description="Check timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional status details")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "message": "All systems operational",
                "version": "1.0.0",
                "timestamp": "2024-01-15T10:30:00.123456",
                "details": {
                    "document_pipeline": True,
                    "vector_pipeline": True,
                    "llm_pipeline": True
                }
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp")
    details: Optional[str] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request ID if available")

    class Config:
        schema_extra = {
            "example": {
                "error_type": "validation_error",
                "message": "Invalid request format",
                "status_code": 400,
                "timestamp": "2024-01-15T10:30:00.123456",
                "details": "Questions must be at least 5 characters long",
                "request_id": "req_abc123def456"
            }
        }


# Rate limiting models
class RateLimitInfo(BaseModel):
    """Rate limiting information"""
    requests_remaining: int = Field(..., description="Requests remaining in current window")
    reset_time: str = Field(..., description="When the rate limit resets")
    window_size: int = Field(..., description="Rate limit window size in seconds")
    max_requests: int = Field(..., description="Maximum requests per window")

    class Config:
        schema_extra = {
            "example": {
                "requests_remaining": 95,
                "reset_time": "2024-01-15T11:00:00.000000",
                "window_size": 3600,
                "max_requests": 100
            }
        }