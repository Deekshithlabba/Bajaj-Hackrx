"""
LLM Integration Pipeline - Person 3
Two-Stage RAG with Task Analyzer and Domain Expert

Author: Person 3 - LLM Orchestration & Prompt Engineering Lead
Purpose: Complete the RAG pipeline with intelligent reasoning layer
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
# import tiktoken  # Commented out to avoid Rust compilation issues

import google.generativeai as genai
from vector_database import VectorDatabasePipeline
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskAnalysis:
    """Structured output from Stage 1 - Task Analyzer"""
    query_type: str
    domain: str
    required_sections: List[str]
    search_strategy: Dict[str, Any]
    response_structure: Dict[str, Any]
    confidence: float
    reasoning: str


@dataclass
class Citation:
    """Individual citation with rich metadata"""
    source: str
    page: int
    chunk_id: str
    excerpt: str
    relevance_score: float
    content_type: str


@dataclass
class ResponseSection:
    """Structured response section with citations"""
    title: str
    content: str
    citations: List[Citation]
    confidence: float


@dataclass
class ExpertResponse:
    """Structured output from Stage 2 - Domain Expert"""
    answer: str
    confidence: float
    sections: List[ResponseSection]
    methodology: str
    token_usage: Dict[str, int]
    processing_time: float


class TwoStageLLMPipeline:
    """
    Complete two-stage LLM pipeline for document intelligence
    
    Stage 1: Task Analyzer - Analyzes queries and determines strategy
    Stage 2: Domain Expert - Generates detailed responses with citations
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the two-stage pipeline"""
        # Store API key for potential fallback
        self.primary_api_key = gemini_api_key
        self.fallback_api_key = config.GEMINI_API_KEY
        
        # Try to initialize with provided key, fallback to env key
        try:
            genai.configure(api_key=gemini_api_key or config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(config.LLM_MODEL)
            self.current_api_key = gemini_api_key or config.GEMINI_API_KEY
            logger.info(f"✅ Gemini client initialized with key: {self.current_api_key[:10]}...")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini client: {e}")
            raise
            
        self.retrieval_pipeline = VectorDatabasePipeline()
        
        # LLM configuration for optimal performance
        self.task_analyzer_model = config.LLM_MODEL  # Gemini for complex reasoning
        self.domain_expert_model = config.LLM_MODEL  # Gemini for detailed responses
        
        # Token counting for optimization (using Gemini's built-in counting)
        self.encoding = None  # Will use Gemini's count_tokens() method
        logger.info("ℹ️ Using Gemini's built-in token counting")
        
        # Performance tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        logger.info("🚀 Two-Stage LLM Pipeline initialized successfully")
    
    def stage1_task_analyzer(self, user_query: str) -> TaskAnalysis:
        """
        Stage 1: Analyze user query and determine optimal response strategy
        
        This is the first LLM that acts as a "meta-reasoner" to understand
        the user's intent and plan the optimal approach for the domain expert.
        """
        start_time = time.time()
        logger.info(f"🔍 Stage 1: Analyzing query - {user_query[:50]}...")
        
        # Step 1: Get initial context sample for analysis
        initial_context = self.retrieval_pipeline.search_similar(
            query=user_query,
            top_k=3,  # Small sample for understanding context
            hybrid=True,
            semantic_weight=0.8,
            namespace="documents"
        )
        
        # Step 2: Build Task Analyzer prompt
        task_prompt = self._build_task_analyzer_prompt(user_query, initial_context)
        
        # Step 3: Call LLM for task analysis
        try:
            response = self.openai_client.chat.completions.create(
                model=self.task_analyzer_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Task Analyzer for a document intelligence system. Analyze queries and provide structured JSON responses for optimal document retrieval and response generation."
                    },
                    {
                        "role": "user", 
                        "content": task_prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            analysis_json = json.loads(response.choices[0].message.content)
            
            # Track token usage
            tokens_used = response.usage.total_tokens
            self.total_tokens_used += tokens_used
            
            # Rate limiting: 40-second delay between API calls
            logger.info("⏳ Waiting 40 seconds before next API call to avoid rate limits...")
            time.sleep(3)
            
            # Build structured TaskAnalysis object
            task_analysis = TaskAnalysis(
                query_type=analysis_json.get("query_type", "general"),
                domain=analysis_json.get("domain", "general"),
                required_sections=analysis_json.get("required_sections", ["overview"]),
                search_strategy=analysis_json.get("search_strategy", {}),
                response_structure=analysis_json.get("response_structure", {}),
                confidence=analysis_json.get("confidence", 0.8),
                reasoning=analysis_json.get("reasoning", "Standard analysis")
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Stage 1 Complete: {task_analysis.query_type} query, {processing_time:.2f}s, {tokens_used} tokens")
            
            return task_analysis
            
        except Exception as e:
            logger.error(f"❌ Stage 1 failed: {e}")
            # Fallback to basic analysis
            return TaskAnalysis(
                query_type="general",
                domain="documents", 
                required_sections=["answer"],
                search_strategy={"primary_query": user_query, "filters": {}},
                response_structure={"format": "basic", "sections": ["answer"]},
                confidence=0.6,
                reasoning="Fallback analysis due to error"
            )
    
    def stage2_domain_expert(self, user_query: str, task_analysis: TaskAnalysis) -> ExpertResponse:
        """
        Stage 2: Generate expert response based on task analysis
        
        This is the second LLM that acts as a domain expert, using the task
        analysis to retrieve focused context and generate detailed responses.
        """
        start_time = time.time()
        logger.info(f"🎯 Stage 2: Generating expert response for {task_analysis.query_type} query")
        
        # Step 1: Execute targeted retrieval based on task analysis
        search_query = task_analysis.search_strategy.get("primary_query", user_query)
        filters = task_analysis.search_strategy.get("filters", {})
        
        expert_context = self.retrieval_pipeline.search_similar(
            query=search_query,
            top_k=7,  # More focused results for expert analysis
            hybrid=True,
            semantic_weight=0.9,  # Heavy semantic focus for expertise
            filter_dict=filters if filters else None,
            namespace="documents"
        )
        
        # Step 2: Build Domain Expert prompt
        expert_prompt = self._build_domain_expert_prompt(
            user_query, task_analysis, expert_context
        )
        
        # Step 3: Call LLM for expert response
        try:
            response = self.openai_client.chat.completions.create(
                model=self.domain_expert_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a domain expert providing detailed analysis based on retrieved documents. Always cite your sources and provide structured, accurate responses."
                    },
                    {
                        "role": "user",
                        "content": expert_prompt
                    }
                ],
                temperature=0.2,  # Slightly higher for more natural responses
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            expert_json = json.loads(response.choices[0].message.content)
            
            # Track token usage
            tokens_used = response.usage.total_tokens
            self.total_tokens_used += tokens_used
            
            # Rate limiting: 40-second delay between API calls
            logger.info("⏳ Waiting 40 seconds before next API call to avoid rate limits...")
            time.sleep(3)
            
            # Step 4: Extract citations and build structured response
            sections = self._build_response_sections(expert_json, expert_context)
            
            expert_response = ExpertResponse(
                answer=expert_json.get("answer", "Unable to generate response"),
                confidence=expert_json.get("confidence", 0.7),
                sections=sections,
                methodology="two_stage_hybrid_rag",
                token_usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": tokens_used
                },
                processing_time=time.time() - start_time
            )
            
            logger.info(f"✅ Stage 2 Complete: {expert_response.confidence:.2f} confidence, {len(sections)} sections, {tokens_used} tokens")
            
            return expert_response
            
        except Exception as e:
            logger.error(f"❌ Stage 2 failed: {e}")
            # Fallback response
            return ExpertResponse(
                answer="Unable to process query due to system error.",
                confidence=0.3,
                sections=[],
                methodology="error_fallback",
                token_usage={"total_tokens": 0},
                processing_time=time.time() - start_time
            )
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Complete two-stage processing pipeline
        
        This is the main entry point that orchestrates both stages
        and returns the final structured response.
        """
        pipeline_start = time.time()
        logger.info(f"🚀 Processing query: {user_query}")
        
        try:
            # Stage 1: Task Analysis
            task_analysis = self.stage1_task_analyzer(user_query)
            
            # Stage 2: Domain Expert Response  
            expert_response = self.stage2_domain_expert(user_query, task_analysis)
            
            # Calculate costs (GPT-4 pricing)
            cost = self._calculate_cost(expert_response.token_usage["total_tokens"])
            self.total_cost += cost
            
            # Combine results into final response
            final_response = {
                "query": user_query,
                "answer": expert_response.answer,
                "confidence": expert_response.confidence,
                "sections": [asdict(section) for section in expert_response.sections],
                "citations": self._extract_all_citations(expert_response.sections),
                "task_analysis": asdict(task_analysis),
                "methodology": expert_response.methodology,
                "performance": {
                    "total_processing_time": time.time() - pipeline_start,
                    "token_usage": expert_response.token_usage,
                    "estimated_cost": cost,
                    "retrieval_foundation": "person_1_and_2_complete"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🎉 Pipeline Complete: {final_response['performance']['total_processing_time']:.2f}s, ${cost:.4f}")
            
            return final_response
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return {
                "query": user_query,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "failed"
            }
    
    def _build_task_analyzer_prompt(self, query: str, context: Dict) -> str:
        """Build sophisticated prompt for Task Analyzer LLM"""
        
        # Format context sample for analysis
        context_sample = ""
        if context and "results" in context:
            for i, result in enumerate(context["results"][:2], 1):
                content = result["metadata"]["content"][:200]
                context_sample += f"\n{i}. [{result['metadata']['content_type']}] {content}..."
        
        return f"""
TASK: Analyze the user query and available document context to determine the optimal response strategy.

USER QUERY: "{query}"

AVAILABLE CONTEXT SAMPLE:
{context_sample}

ANALYZE AND DETERMINE:
1. Query Type: What kind of information is being requested?
   - factual (specific facts/data)
   - analytical (comparisons, analysis)  
   - procedural (how-to, process steps)
   - definitional (what is something)
   - comprehensive (broad overview)

2. Domain Focus: What subject area does this query relate to?
   - insurance, legal, financial, medical, technical, etc.

3. Required Information: What sections/types of information are needed?

4. Search Strategy: How should we search for the best context?
   - What refined query terms would work best?
   - What content types are most relevant?
   - What filters would improve results?

5. Response Structure: How should the final answer be organized?

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "query_type": "analytical",
    "domain": "insurance", 
    "required_sections": ["overview", "details", "examples"],
    "search_strategy": {{
        "primary_query": "optimized search terms based on query analysis",
        "filters": {{"content_type": ["text", "table"]}},
        "focus_areas": ["specific areas to emphasize"]
    }},
    "response_structure": {{
        "format": "structured_analysis",
        "sections": ["section1", "section2", "section3"]
    }},
    "confidence": 0.85,
    "reasoning": "Brief explanation of the analysis approach"
}}
"""
    
    def _build_domain_expert_prompt(self, query: str, analysis: TaskAnalysis, context: Dict) -> str:
        """Build sophisticated prompt for Domain Expert LLM"""
        
        # Format retrieved context with rich metadata
        formatted_context = ""
        if context and "results" in context:
            for i, result in enumerate(context["results"], 1):
                metadata = result["metadata"]
                formatted_context += f"""
CHUNK {i} [Score: {result['score']:.3f}]:
Source: {metadata['source_url']}, Page {metadata['page_number']}
Type: {metadata['content_type']} | ID: {metadata['chunk_id']}
Content: {metadata['content']}
---"""
        
        return f"""
TASK: Provide a comprehensive, expert-level response based on the retrieved document context.

ORIGINAL QUERY: "{query}"

TASK ANALYSIS: {analysis.reasoning}
- Query Type: {analysis.query_type}
- Domain: {analysis.domain}
- Required Sections: {', '.join(analysis.required_sections)}

RETRIEVED CONTEXT:
{formatted_context}

INSTRUCTIONS:
1. Answer the query using ONLY the information provided in the context above
2. Structure your response according to the required sections: {', '.join(analysis.required_sections)}
3. Include specific citations for every claim using the chunk IDs provided
4. Maintain high accuracy - only state what you can verify from the context
5. If information is insufficient, clearly state limitations
6. Use professional, clear language appropriate for the {analysis.domain} domain

RESPOND IN THIS EXACT JSON FORMAT:
{{
    "answer": "Comprehensive response addressing the query...",
    "confidence": 0.92,
    "sections": [
        {{
            "title": "Section Title",
            "content": "Detailed content with specific information...",
            "citations": [
                {{
                    "chunk_id": "doc_1_chunk_042",
                    "excerpt": "Specific text excerpt that supports this claim...",
                    "relevance": "How this citation supports the claim"
                }}
            ],
            "confidence": 0.90
        }}
    ],
    "limitations": "Any limitations or missing information",
    "methodology": "Brief explanation of how the answer was derived"
}}
"""
    
    def _build_response_sections(self, expert_json: Dict, context: Dict) -> List[ResponseSection]:
        """Build structured response sections with rich citations"""
        sections = []
        
        # Create context lookup for citation building
        context_lookup = {}
        if context and "results" in context:
            for result in context["results"]:
                chunk_id = result["metadata"]["chunk_id"]
                context_lookup[chunk_id] = result
        
        # Process each section from the expert response
        for section_data in expert_json.get("sections", []):
            citations = []
            
            # Build citations for this section
            for citation_data in section_data.get("citations", []):
                chunk_id = citation_data.get("chunk_id", "")
                if chunk_id in context_lookup:
                    result = context_lookup[chunk_id]
                    metadata = result["metadata"]
                    
                    citation = Citation(
                        source=metadata["source_url"],
                        page=metadata["page_number"],
                        chunk_id=chunk_id,
                        excerpt=citation_data.get("excerpt", metadata["content"][:200]),
                        relevance_score=result["score"],
                        content_type=metadata["content_type"]
                    )
                    citations.append(citation)
            
            section = ResponseSection(
                title=section_data.get("title", "Untitled Section"),
                content=section_data.get("content", ""),
                citations=citations,
                confidence=section_data.get("confidence", 0.8)
            )
            sections.append(section)
        
        return sections
    
    def _extract_all_citations(self, sections: List[ResponseSection]) -> List[Dict[str, Any]]:
        """Extract all citations for the final response"""
        all_citations = []
        
        for section in sections:
            for citation in section.citations:
                citation_dict = {
                    "source": citation.source,
                    "page": citation.page,
                    "chunk_id": citation.chunk_id,
                    "excerpt": citation.excerpt,
                    "relevance_score": citation.relevance_score,
                    "content_type": citation.content_type,
                    "section": section.title
                }
                all_citations.append(citation_dict)
        
        return all_citations
    
    def _estimate_tokens(self, text: str) -> int:
        """Simple token estimation fallback (when tiktoken is not available)"""
        # Rough estimation: ~4 characters per token for English text
        return len(text) // 4
    
    def _calculate_cost(self, total_tokens: int) -> float:
        """Calculate estimated cost based on Gemini pricing"""
        # Gemini 1.5 Flash is free up to 15 requests per minute
        # For paid tier: ~$0.00075 per 1K tokens (much cheaper than GPT-4)
        return (total_tokens / 1000) * 0.00075
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for monitoring"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "estimated_total_cost": self.total_cost,
            "average_cost_per_query": self.total_cost / max(1, self.total_tokens_used // 3000),  # Rough estimate
            "model_config": {
                "task_analyzer": self.task_analyzer_model,
                "domain_expert": self.domain_expert_model
            }
        }


# Example usage and testing
if __name__ == "__main__":
    # Initialize the pipeline
    logger.info("🚀 Initializing Two-Stage LLM Pipeline...")
    llm_pipeline = TwoStageLLMPipeline()
    
    # Test with sample queries
    test_queries = [
        "What are the premium calculation methods in this insurance policy?",
        "What medical conditions are excluded from coverage?",
        "How do I file a claim for medical expenses?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"🔍 Testing Query: {query}")
        print('='*60)
        
        try:
            result = llm_pipeline.process_query(query)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            print(f"📋 Answer: {result['answer'][:200]}...")
            print(f"🎯 Confidence: {result['confidence']:.2f}")
            print(f"📚 Citations: {len(result['citations'])}")
            print(f"⏱️  Processing Time: {result['performance']['total_processing_time']:.2f}s")
            print(f"💰 Cost: ${result['performance']['estimated_cost']:.4f}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    # Show performance stats
    stats = llm_pipeline.get_performance_stats()
    print(f"\n📊 Pipeline Performance Stats:")
    print(f"Total Tokens: {stats['total_tokens_used']:,}")
    print(f"Total Cost: ${stats['estimated_total_cost']:.4f}")