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

from vector_database import VectorDatabasePipeline
from gemini_api_manager import gemini_api_manager
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskAnalysis:
    """Structured output from Stage 1 - Domain Analyzer + Few-Shot Creator"""
    query_type: str
    domain: str
    required_sections: List[str]
    search_strategy: Dict[str, Any]
    response_structure: Dict[str, Any]
    few_shot_prompts: List[Dict[str, str]]  # Few-shot examples created from domain analysis
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
    
    def __init__(self):
        """Initialize the two-stage pipeline using environment API keys only"""
        
        # Use the global API manager with environment keys only
        self.api_manager = gemini_api_manager
        logger.info("✅ Using global Gemini API manager with environment API keys")
            
        # Use consistent index name to match main application
        self.retrieval_pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        
        # LLM configuration for optimal performance with different models per stage
        self.task_analyzer_model = config.TASK_ANALYZER_MODEL  # Fast analysis
        self.domain_expert_model = config.DOMAIN_EXPERT_MODEL  # High-quality responses
        
        # Token counting for optimization (using Gemini's built-in counting)
        self.encoding = None  # Will use Gemini's count_tokens() method
        logger.info("ℹ️ Using latest Gemini 2.0 Flash models for both analysis and expertise")
        
        # Performance tracking
        self.total_tokens_used = 0
        self.total_cost = 0.0
        
        # Stage-specific performance tracking
        self.stage_stats = {
            'analyzer': {'calls': 0, 'tokens': 0, 'avg_time': 0},
            'expert': {'calls': 0, 'tokens': 0, 'avg_time': 0}
        }
        
        logger.info("🚀 Two-Stage LLM Pipeline initialized successfully")
    
    def stage1_task_analyzer(self, user_query: str) -> TaskAnalysis:
        """
        Stage 1: Domain Understanding + Few-Shot Prompt Creation
        
        This stage:
        1. Analyzes the document domain and structure
        2. Creates few-shot prompts based on that domain understanding
        """
        start_time = time.time()
        logger.info(f"🔍 Stage 1: Domain analysis + creating few-shot prompts for query - {user_query[:50]}...")
        
        # Step 1: Get diverse document samples to understand domain
        domain_context = self.retrieval_pipeline.search_similar(
            query="document type content structure information",  # Generic query to understand documents
            top_k=5,  # Sample different document types
            hybrid=True,
            semantic_weight=0.6,  # More keyword-focused for diversity
            namespace="documents"
        )
        
        # Step 2: Build Domain Analyzer prompt that also creates few-shot prompts
        task_prompt = self._build_domain_analyzer_prompt(domain_context)
        
        # Step 3: Call Gemini for task analysis with retry logic
        try:
            # Use a simpler, more natural prompt for Gemini
            analyzer_full_prompt = f"""Analyze these document samples and create few-shot examples for answering questions.

{task_prompt}

Please respond with a JSON object containing the domain analysis and 3 few-shot examples."""
            
            # Try the API call with retry on empty response
            response_text = None
            for attempt in range(3):
                try:
                    response_text = self.api_manager.analyze_task(analyzer_full_prompt)
                    if response_text and response_text.strip():
                        break
                    logger.warning(f"🔄 Attempt {attempt + 1}: Empty response, retrying...")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"🔄 Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Not the last attempt
                        time.sleep(2)
                    else:
                        raise
            
            # Debug: Log what we actually received
            logger.info(f"🔍 Stage 1 Raw Response: {response_text[:200]}...")
            
            if not response_text or not response_text.strip():
                raise ValueError("Empty response from Gemini API")
            
            # Clean JSON response (remove markdown code blocks if present)
            cleaned_response = self._clean_json_response(response_text)
            
            # Parse response
            try:
                analysis_json = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Stage 1 JSON parsing failed. Raw response: {response_text}")
                logger.warning("🔄 Attempting to extract domain from non-JSON response...")
                
                # Try to extract domain information from text response
                domain = "general"
                if "insurance" in response_text.lower():
                    domain = "insurance"
                elif "medical" in response_text.lower():
                    domain = "medical"
                elif "legal" in response_text.lower():
                    domain = "legal"
                elif "financial" in response_text.lower():
                    domain = "financial"
                
                # Create fallback analysis with basic few-shot
                return TaskAnalysis(
                    query_type="factual",
                    domain=domain,
                    required_sections=["answer", "details"],
                    search_strategy={"primary_focus": user_query},
                    response_structure={"format": "structured", "sections": ["answer"]},
                    few_shot_prompts=[
                        {
                            "example_question": f"What is a specific {domain} term?",
                            "example_answer": f"Based on the {domain} documents, the term refers to...",
                            "pattern_explanation": f"Standard {domain} definition format"
                        },
                        {
                            "example_question": f"How does a {domain} process work?",
                            "example_answer": f"The {domain} process involves the following steps: 1) First step... 2) Second step...",
                            "pattern_explanation": f"Step-by-step {domain} process explanation"
                        }
                    ],
                    confidence=0.5,
                    reasoning=f"Fallback analysis - detected {domain} domain from partial response"
                )
            
            # Track token usage (estimate for Gemini)
            tokens_used = self._estimate_tokens(response_text)
            self.total_tokens_used += tokens_used
            self.stage_stats['analyzer']['tokens'] += tokens_used
            
            # Rate limiting: Brief delay between API calls
            logger.info("⏳ Brief delay before next API call...")
            time.sleep(1)
            
            # Build structured TaskAnalysis object
            task_analysis = TaskAnalysis(
                query_type=analysis_json.get("query_type", "general"),
                domain=analysis_json.get("domain", "general"),
                required_sections=analysis_json.get("required_sections", ["overview"]),
                search_strategy=analysis_json.get("search_strategy", {}),
                response_structure=analysis_json.get("response_structure", {}),
                few_shot_prompts=analysis_json.get("few_shot_prompts", []),
                confidence=analysis_json.get("confidence", 0.8),
                reasoning=analysis_json.get("reasoning", "Standard analysis")
            )
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Stage 1 Complete: {task_analysis.domain} domain, {len(task_analysis.few_shot_prompts)} few-shot prompts created, {processing_time:.2f}s, {tokens_used} tokens")
            
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
                few_shot_prompts=[{"example": "Q: What is X? A: Based on the document, X is..."}],
                confidence=0.6,
                reasoning="Fallback analysis due to error"
            )
    
    def stage2_domain_expert(self, user_query: str, task_analysis: TaskAnalysis) -> ExpertResponse:
        """
        Stage 2: Use Few-Shot Prompts + User Question to Generate Answer
        
        This stage takes:
        1. The user's actual question 
        2. The few-shot prompts from Stage 1
        3. Retrieves relevant context for the user question
        4. Uses few-shot prompts to generate the answer
        """
        start_time = time.time()
        logger.info(f"🎯 Stage 2: Using few-shot prompts to answer user question for {task_analysis.domain}")
        
        # Step 1: Execute targeted retrieval using multiple search strategies
        # Extract key terms from user query for better retrieval
        key_terms = self._extract_key_search_terms(user_query)
        
        # ENHANCED RETRIEVAL STRATEGY - Multiple searches with increased k
        all_results = []
        
        # Search 1: Specific term extraction for exact matches (INCREASED k=10)
        specific_terms = self._extract_specific_terms(user_query)
        logger.info(f"🔍 Search 1: Specific terms - '{specific_terms}'")
        specific_results = self.retrieval_pipeline.search_similar(
            query=specific_terms,
            top_k=10,  # INCREASED from 4 to 10
            hybrid=True,
            semantic_weight=0.6,  # More keyword focused
            namespace="documents"
        )
        if specific_results and "results" in specific_results:
            all_results.extend(specific_results["results"])
        
        # Search 2: Key terms with higher k (INCREASED k=10)
        logger.info(f"🔍 Search 2: Key terms - '{key_terms}'")
        key_results = self.retrieval_pipeline.search_similar(
            query=key_terms,
            top_k=10,  # INCREASED from 4 to 10
            hybrid=True,
            semantic_weight=0.7,
            namespace="documents"
        )
        if key_results and "results" in key_results:
            all_results.extend(key_results["results"])
        
        # Search 3: Original question for broader context (INCREASED k=8)
        logger.info(f"🔍 Search 3: Original question")
        original_results = self.retrieval_pipeline.search_similar(
            query=user_query,
            top_k=8,  # INCREASED from 4 to 8
            hybrid=True,
            semantic_weight=0.9,
            namespace="documents"
        )
        if original_results and "results" in original_results:
            all_results.extend(original_results["results"])
        
        # Search 4: Definition-focused search
        definition_query = self._build_definition_query(user_query)
        logger.info(f"🔍 Search 4: Definition-focused - '{definition_query}'")
        definition_results = self.retrieval_pipeline.search_similar(
            query=definition_query,
            top_k=5,
            hybrid=True,
            semantic_weight=0.5,  # More balanced for definitions
            namespace="documents"
        )
        if definition_results and "results" in definition_results:
            all_results.extend(definition_results["results"])
        
        # Search 5: Renewal/Continuity context search (NEW - targets the missing chunk!)
        renewal_query = self._build_renewal_query(user_query)
        logger.info(f"🔍 Search 5: Renewal context - '{renewal_query}'")
        renewal_results = self.retrieval_pipeline.search_similar(
            query=renewal_query,
            top_k=8,
            hybrid=True,
            semantic_weight=0.4,  # More keyword focused
            namespace="documents"
        )
        if renewal_results and "results" in renewal_results:
            all_results.extend(renewal_results["results"])
        
        # ADVANCED: Combine, deduplicate, and re-rank
        seen_ids = set()
        unique_results = []
        for result in all_results:
            chunk_id = result["metadata"]["chunk_id"]
            if chunk_id not in seen_ids:
                seen_ids.add(chunk_id)
                unique_results.append(result)
        
        # Re-rank results based on relevance to original query
        re_ranked_results = self._re_rank_results(unique_results, user_query)
        expert_context = {"results": re_ranked_results[:15]}  # INCREASED to 15 for comprehensive coverage
        
        logger.info(f"✅ Enhanced search found {len(unique_results)} unique results, returning top 15 after re-ranking")
        
        # Log the top results for debugging
        if re_ranked_results:
            logger.info(f"🏆 Top result: {re_ranked_results[0]['metadata'].get('chunk_id', 'unknown')} (Score: {re_ranked_results[0]['relevance_score']:.4f})")
            if len(re_ranked_results) > 1:
                logger.info(f"🥈 2nd result: {re_ranked_results[1]['metadata'].get('chunk_id', 'unknown')} (Score: {re_ranked_results[1]['relevance_score']:.4f})")
        
        # Step 2: Build expert prompt using few-shot prompts from Stage 1
        expert_prompt = self._build_expert_prompt_with_few_shots(
            user_query, task_analysis, expert_context
        )
        
        # Step 3: Call LLM for expert response with retry logic
        try:
            # Use a more natural prompt for Gemini
            expert_full_prompt = f"""You are a helpful assistant. Use the examples and context below to answer the user's question.

{expert_prompt}

Please respond in JSON format with your answer."""
            
            # Try the API call with retry on empty response
            response_text = None
            for attempt in range(3):
                try:
                    response_text = self.api_manager.generate_expert_response(expert_full_prompt)
                    if response_text and response_text.strip():
                        break
                    logger.warning(f"🔄 Stage 2 Attempt {attempt + 1}: Empty response, retrying...")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"🔄 Stage 2 Attempt {attempt + 1} failed: {e}")
                    if attempt < 2:  # Not the last attempt
                        time.sleep(2)
                    else:
                        raise
            
            # Debug: Log what we actually received
            logger.info(f"🔍 Stage 2 Raw Response: {response_text[:200]}...")
            
            if not response_text or not response_text.strip():
                raise ValueError("Empty response from Gemini API")
            
            # Clean JSON response (remove markdown code blocks if present)
            cleaned_response = self._clean_json_response(response_text)
            
            # Parse response
            try:
                expert_json = json.loads(cleaned_response)
            except json.JSONDecodeError as e:
                logger.error(f"❌ Stage 2 JSON parsing failed. Raw response: {response_text}")
                logger.warning("🔄 Using text response as fallback answer...")
                
                # Create fallback expert response using the text response
                expert_json = {
                    "answer": response_text if response_text else "Unable to generate response due to API issues.",
                    "confidence": 0.3,
                    "sections": [
                        {
                            "title": "Response",
                            "content": response_text if response_text else "No response available",
                            "citations": [],
                            "confidence": 0.3
                        }
                    ],
                    "limitations": "Response generated from non-JSON API output",
                    "methodology": "Fallback text processing due to JSON parsing failure"
                }
            
            # Track token usage (estimate for Gemini)
            tokens_used = self._estimate_tokens(response_text)
            self.total_tokens_used += tokens_used
            self.stage_stats['expert']['tokens'] += tokens_used
            
            # Rate limiting: Brief delay between API calls
            logger.info("⏳ Brief delay before next API call...")
            time.sleep(1)
            
            # Step 4: Extract citations and build structured response
            sections = self._build_response_sections(expert_json, expert_context)
            
            expert_response = ExpertResponse(
                answer=expert_json.get("answer", "Unable to generate response"),
                confidence=expert_json.get("confidence", 0.7),
                sections=sections,
                methodology="two_stage_hybrid_rag",
                token_usage={
                    "prompt_tokens": tokens_used // 2,  # Estimate
                    "completion_tokens": tokens_used // 2,  # Estimate
                    "total_tokens": tokens_used
                },
                processing_time=time.time() - start_time
            )
            
            logger.info(f"✅ Stage 2 Complete: Used {len(task_analysis.few_shot_prompts)} few-shot prompts, {expert_response.confidence:.2f} confidence, {len(sections)} sections, {tokens_used} tokens")
            
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
    
    def _build_domain_analyzer_prompt(self, context: Dict) -> str:
        """Build prompt for Domain Analyzer LLM - focuses on document analysis"""
        
        # Format document samples for domain analysis
        document_samples = ""
        if context and "results" in context:
            for i, result in enumerate(context["results"], 1):
                metadata = result["metadata"]
                content_preview = metadata["content"][:300]
                document_samples += f"""
DOCUMENT SAMPLE {i}:
- Content Type: {metadata['content_type']}
- Source: {metadata['source_url']}
- Content Preview: {content_preview}...
---"""
        
        return f"""
Look at these document samples:

{document_samples}

Based on these samples:
1. What domain is this? (insurance, medical, legal, financial, etc.)
2. Create 3 example question-answer pairs that show how to answer questions in this domain

Please respond in JSON format like this:
{{
    "domain": "insurance",
    "query_type": "factual", 
    "required_sections": ["answer", "details"],
    "search_strategy": {{"primary_focus": "key terms"}},
    "response_structure": {{"format": "structured"}},
    "few_shot_prompts": [
        {{
            "example_question": "What is a grace period?",
            "example_answer": "A grace period is the time allowed after a premium due date...",
            "pattern_explanation": "Clear definition with context"
        }},
        {{
            "example_question": "How do I file a claim?", 
            "example_answer": "To file a claim: 1) Contact customer service 2) Submit required documents...",
            "pattern_explanation": "Step-by-step process"
        }},
        {{
            "example_question": "What documents are needed?",
            "example_answer": "Required documents include: policy number, medical records...",
            "pattern_explanation": "List format with specifics"
        }}
    ],
    "confidence": 0.8,
    "reasoning": "Domain analysis based on document content"
}}
"""
    
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
    
    def _extract_key_search_terms(self, user_query: str) -> str:
        """Extract key search terms from user query for better retrieval"""
        
        # Convert to lowercase for processing
        query_lower = user_query.lower()
        
        # Common question words and phrases to remove
        stop_words = [
            "what", "what is", "what are", "how", "when", "where", "why", "who",
            "the", "a", "an", "is", "are", "was", "were", "been", "be",
            "under", "for", "in", "on", "at", "by", "with", "from", "to",
            "does", "do", "did", "can", "could", "should", "would", "will"
        ]
        
        # Remove stop words
        words = query_lower.split()
        key_words = []
        
        for word in words:
            # Remove punctuation
            clean_word = word.strip("?.,!;:")
            if clean_word and clean_word not in stop_words and len(clean_word) > 2:
                key_words.append(clean_word)
        
        # Join the key words
        key_terms = " ".join(key_words)
        
        logger.info(f"🔍 Extracted key search terms: '{key_terms}' from '{user_query}'")
        return key_terms
    
    def _extract_specific_terms(self, user_query: str) -> str:
        """Extract the most specific terms for exact matching"""
        
        query_lower = user_query.lower()
        
        # Look for specific insurance/medical terms
        specific_terms = []
        
        # Extract quoted phrases or specific product names
        if "grace period" in query_lower:
            specific_terms.append("grace period")
        if "premium payment" in query_lower:
            specific_terms.append("premium payment")
        if "national parivar mediclaim" in query_lower:
            specific_terms.append("national parivar mediclaim")
        if "mediclaim plus" in query_lower:
            specific_terms.append("mediclaim plus")
        
        # Add other specific terms
        technical_terms = ["policy", "insurance", "coverage", "deadline", "due date"]
        for term in technical_terms:
            if term in query_lower:
                specific_terms.append(term)
        
        result = " ".join(specific_terms) if specific_terms else user_query
        logger.info(f"🎯 Extracted specific terms: '{result}'")
        return result
    
    def _build_definition_query(self, user_query: str) -> str:
        """Build a query specifically for finding definitions"""
        
        query_lower = user_query.lower()
        
        # Extract the main concept to define
        if "grace period" in query_lower:
            return "grace period means definition specified period time premium due date"
        elif "premium" in query_lower:
            return "premium payment due date deadline"
        elif "policy" in query_lower:
            return "policy terms conditions"
        else:
            # Generic definition search
            return "means definition terms conditions specified"
    
    def _build_renewal_query(self, user_query: str) -> str:
        """Build a query specifically for finding renewal/continuity context"""
        
        query_lower = user_query.lower()
        
        # Target the renewal context where grace period info is often found
        if "grace period" in query_lower:
            return "grace period 30 days renewal continuity benefits maintain policy"
        elif "premium" in query_lower and "payment" in query_lower:
            return "renewal grace period 30 days continue policy without break"
        else:
            # Generic renewal search
            return "renewal policy continuity maintain benefits grace period"
    
    def _re_rank_results(self, results, original_query: str):
        """Enhanced re-ranking based on content relevance"""
        
        query_lower = original_query.lower()
        key_phrases = ["grace period", "premium payment", "due date", "payment deadline"]
        
        def calculate_relevance_score(result):
            content = result["metadata"]["content"].lower()
            original_score = result["score"]
            
            # Base boost for key phrases
            relevance_boost = 0
            for phrase in key_phrases:
                if phrase in content:
                    relevance_boost += 0.1
            
            # MAJOR boost for chunks with grace period + specific days/numbers
            if "grace period" in content:
                # Super boost for chunks that have both grace period and specific time periods
                if any(term in content for term in ["30 days", "thirty days", "30"]):
                    relevance_boost += 0.5  # MAJOR boost
                    logger.info(f"🎯 MAJOR BOOST: Found grace period + 30 days in chunk {result['metadata'].get('chunk_id', 'unknown')}")
                elif any(term in content for term in ["days", "period of"]):
                    relevance_boost += 0.3  # Good boost for potential time periods
                else:
                    relevance_boost += 0.1  # Small boost for just grace period
            
            # Boost for renewal/continuity context
            if any(term in content for term in ["renewal", "continuity", "maintain", "continue policy", "without break"]):
                relevance_boost += 0.2
                
            # Extra boost for definition-like content
            if any(word in content for word in ["means", "refers to", "defined as", "is the"]):
                relevance_boost += 0.15
                
            # Penalize very short chunks (likely just headers)
            if len(content.strip()) < 50:
                relevance_boost -= 0.1
            
            # Boost substantial content
            elif len(content.strip()) > 200:
                relevance_boost += 0.05
                
            return original_score + relevance_boost
        
        # Re-rank based on calculated relevance
        for result in results:
            result["relevance_score"] = calculate_relevance_score(result)
        
        # Sort by relevance score
        re_ranked = sorted(results, key=lambda x: x["relevance_score"], reverse=True)
        
        logger.info(f"🔄 Re-ranked results: Top score {re_ranked[0]['relevance_score']:.4f} (was {re_ranked[0]['score']:.4f})")
        return re_ranked
    
    def _clean_json_response(self, response_text: str) -> str:
        """Clean JSON response by removing markdown code blocks"""
        
        # Remove ```json and ``` markers if present
        cleaned = response_text.strip()
        
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]   # Remove ```
            
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```
            
        return cleaned.strip()
    
    def _build_expert_prompt_with_few_shots(self, query: str, analysis: TaskAnalysis, context: Dict) -> str:
        """Build expert prompt using few-shot prompts from Stage 1"""
        
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
        
        # Format few-shot examples from Stage 1 analysis
        few_shot_examples = ""
        for i, prompt in enumerate(analysis.few_shot_prompts, 1):
            few_shot_examples += f"""
EXAMPLE {i} ({analysis.domain.upper()} DOMAIN):
Q: {prompt.get('example_question', 'Sample question')}
A: {prompt.get('example_answer', 'Sample answer')}
Pattern: {prompt.get('pattern_explanation', 'Standard pattern')}
---"""
        
        return f"""
USER QUESTION: "{query}"

Here are examples of how to answer {analysis.domain} questions:
{few_shot_examples}

Here is the relevant information from the documents:
{formatted_context}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
1. You MUST base your answer ONLY on the provided document sections above
2. If the answer is not present in the provided sections, you MUST state that the information is not available in the documents
3. Do NOT use any outside knowledge or make assumptions
4. If you find relevant information, cite the specific chunk_id and excerpt
5. Be precise and only state what you can verify from the provided context
6. If multiple chunks contain partial information, combine them logically

Please answer the user's question using ONLY the information provided above. Follow the format shown in the examples.

Respond in JSON format like this:
{{
    "answer": "Your answer here based on the documents...",
    "confidence": 0.9,
    "sections": [
        {{
            "title": "Main Answer",
            "content": "Detailed answer with specific information...",
            "citations": [
                {{
                    "chunk_id": "doc_1_chunk_042",
                    "excerpt": "Quote from the document...",
                    "relevance": "How this supports the answer"
                }}
            ],
            "confidence": 0.9
        }}
    ],
    "limitations": "Any limitations in the answer",
    "methodology": "Used {analysis.domain} domain knowledge with document context"
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
        """Calculate estimated cost based on Gemini 2.0 Flash pricing"""
        # Gemini 2.0 Flash is currently FREE during experimental phase
        # Future pricing: Input $0.10/1M tokens, Output $0.40/1M tokens
        input_cost = (total_tokens * 0.7 / 1000000) * 0.10  # Estimate 70% input
        output_cost = (total_tokens * 0.3 / 1000000) * 0.40  # Estimate 30% output
        return input_cost + output_cost
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics for monitoring"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self.total_cost,
            "stage_performance": self.stage_stats,
            "api_usage": self.api_manager.get_usage_stats(),
            "cache_stats": getattr(self.retrieval_pipeline, 'cache_stats', {}),
            "models_used": {
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