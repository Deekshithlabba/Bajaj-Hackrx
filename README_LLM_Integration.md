# LLM Integration Pipeline - Person 3

> **Two-Stage LLM Lead for HackRx 6.0 Universal Document Intelligence System**

This module implements the sophisticated Two-Stage LLM reasoning pipeline that transforms Person 1+2's retrieval results into intelligent, structured responses with complete explainability.

## 🚀 Starting Point - WHAT'S READY FOR YOU

### ✅ **Complete Retrieval Foundation (Person 1 + 2)**
- **✅ Document Ingestion**: 802 chunks extracted from complex documents
- **✅ Vector Database**: Pinecone with hybrid search (semantic + keyword)
- **✅ Rich Metadata**: Complete traceability for citations
- **✅ Production Ready**: Auto-scaling, error-resilient infrastructure

### 🎯 **Your Mission: Complete the RAG Pipeline**

```
📄 Documents → 🔄 Processing → 📦 Chunks → 🧠 Embeddings → 🔍 Search → 📋 Context
   (DONE)        (DONE)       (DONE)      (DONE)       (DONE)     (READY)
                                                                     ↓
                                               🤖 LLM INTEGRATION (YOUR WORK)
                                                         ↓
                                              ✨ Intelligent Responses
```

## 🏗️ Architecture: Two-Stage LLM Pipeline

### **Stage 1: Task Analyzer LLM**
**Purpose**: Analyze user intent and dynamically determine response structure

```python
# YOUR IMPLEMENTATION TARGET
def task_analyzer_llm(user_query: str, sample_context: List[Dict]) -> Dict:
    """
    Stage 1: Analyze the user's query and determine optimal response strategy
    
    Input:
        - user_query: "What are the premium calculation methods?"
        - sample_context: Initial search results for context understanding
    
    Output:
        {
            "query_type": "analytical",
            "domain": "insurance",
            "required_sections": ["calculations", "formulas", "examples"],
            "search_strategy": {
                "primary_query": "premium calculation methods formulas",
                "filters": {"content_type": ["text", "table"]},
                "focus_areas": ["mathematical", "procedural"]
            },
            "response_structure": {
                "format": "structured_analysis",
                "sections": ["overview", "methods", "examples", "calculations"]
            }
        }
    """
    # YOUR CODE HERE
    pass
```

### **Stage 2: Domain Expert LLM** 
**Purpose**: Generate the final structured, cited response

```python
# YOUR IMPLEMENTATION TARGET
def domain_expert_llm(task_analysis: Dict, expert_context: List[Dict]) -> Dict:
    """
    Stage 2: Generate expert-level response with citations
    
    Input:
        - task_analysis: Output from Stage 1
        - expert_context: Targeted search results
    
    Output:
        {
            "answer": "Structured response based on retrieved context...",
            "confidence": 0.92,
            "sections": [
                {
                    "title": "Premium Calculation Overview",
                    "content": "...",
                    "citations": [
                        {
                            "source": "policy.pdf",
                            "page": 15,
                            "chunk_id": "doc_1_chunk_042",
                            "relevance": 0.94
                        }
                    ]
                }
            ],
            "methodology": "hybrid_search_analysis",
            "token_usage": {"prompt": 1200, "completion": 800}
        }
    """
    # YOUR CODE HERE  
    pass
```

## 🔧 Integration Guide

### **Step 1: Set Up Your Environment**

```bash
# You have the foundation - add LLM dependencies
pip install openai>=1.12.0  # Already installed
pip install anthropic>=0.8.0  # If using Claude
pip install tiktoken>=0.5.0  # Token counting

# Your workspace is ready:
# ✅ vector_database.py - Retrieval system
# ✅ processed_chunks/ - 802 chunks ready
# ✅ Pinecone integration working
```

### **Step 2: Initialize the Retrieval System**

```python
from vector_database import VectorDatabasePipeline

# Initialize the completed retrieval foundation
pipeline = VectorDatabasePipeline()

# Test the foundation (should work immediately)
test_results = pipeline.search_similar(
    query="insurance premium calculation",
    top_k=5,
    hybrid=True,
    namespace="documents"  # Use your document namespace
)

print(f"✅ Retrieval foundation ready: {len(test_results['results'])} results")
```

### **Step 3: Build Your LLM Integration**

Create `llm_integration.py`:

```python
"""
LLM Integration Pipeline - Person 3
Two-Stage RAG with Task Analyzer and Domain Expert
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

from vector_database import VectorDatabasePipeline
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TaskAnalysis:
    query_type: str
    domain: str
    required_sections: List[str]
    search_strategy: Dict[str, Any]
    response_structure: Dict[str, Any]
    confidence: float


@dataclass
class ExpertResponse:
    answer: str
    confidence: float
    sections: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    methodology: str
    token_usage: Dict[str, int]


class TwoStageLLMPipeline:
    """
    Complete two-stage LLM pipeline for document intelligence
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the two-stage pipeline"""
        self.openai_client = OpenAI(api_key=openai_api_key or config.OPENAI_API_KEY)
        self.retrieval_pipeline = VectorDatabasePipeline()
        
        # Your LLM configuration
        self.task_analyzer_model = "gpt-4"  # For complex reasoning
        self.domain_expert_model = "gpt-4"  # For detailed responses
        
        logger.info("🚀 Two-Stage LLM Pipeline initialized")
    
    def stage1_task_analyzer(self, user_query: str) -> TaskAnalysis:
        """
        Stage 1: Analyze user query and determine optimal response strategy
        
        YOUR MAIN IMPLEMENTATION AREA
        """
        # Step 1: Get initial context sample
        initial_context = self.retrieval_pipeline.search_similar(
            query=user_query,
            top_k=3,  # Small sample for analysis
            hybrid=True,
            semantic_weight=0.8
        )
        
        # Step 2: Build Task Analyzer prompt
        task_prompt = self._build_task_analyzer_prompt(user_query, initial_context)
        
        # Step 3: Call LLM for task analysis
        # YOUR CODE HERE - implement the LLM call and response parsing
        
        # Step 4: Return structured analysis
        # YOUR CODE HERE - return TaskAnalysis object
        
        pass
    
    def stage2_domain_expert(self, user_query: str, task_analysis: TaskAnalysis) -> ExpertResponse:
        """
        Stage 2: Generate expert response based on task analysis
        
        YOUR MAIN IMPLEMENTATION AREA
        """
        # Step 1: Execute targeted retrieval based on task analysis
        expert_context = self.retrieval_pipeline.search_similar(
            query=task_analysis.search_strategy.get("primary_query", user_query),
            top_k=5,  # Focused results
            hybrid=True,
            semantic_weight=0.9,  # Heavy semantic focus
            filter_dict=task_analysis.search_strategy.get("filters")
        )
        
        # Step 2: Build Domain Expert prompt
        expert_prompt = self._build_domain_expert_prompt(
            user_query, task_analysis, expert_context
        )
        
        # Step 3: Call LLM for expert response
        # YOUR CODE HERE - implement the LLM call and response parsing
        
        # Step 4: Extract citations and structure response
        # YOUR CODE HERE - build ExpertResponse with citations
        
        pass
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Complete two-stage processing pipeline
        
        YOUR INTEGRATION POINT
        """
        try:
            logger.info(f"🔍 Processing query: {user_query}")
            
            # Stage 1: Task Analysis
            task_analysis = self.stage1_task_analyzer(user_query)
            logger.info(f"📊 Task Analysis: {task_analysis.query_type}")
            
            # Stage 2: Domain Expert Response
            expert_response = self.stage2_domain_expert(user_query, task_analysis)
            logger.info(f"🎯 Expert Response: {expert_response.confidence:.2f} confidence")
            
            # Combine results
            return {
                "query": user_query,
                "task_analysis": task_analysis.__dict__,
                "expert_response": expert_response.__dict__,
                "processing_method": "two_stage_llm",
                "retrieval_foundation": "person_1_and_2_complete"
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            raise
    
    def _build_task_analyzer_prompt(self, query: str, context: Dict) -> str:
        """Build prompt for Task Analyzer LLM - YOUR IMPLEMENTATION"""
        # YOUR CODE HERE
        pass
    
    def _build_domain_expert_prompt(self, query: str, analysis: TaskAnalysis, context: Dict) -> str:
        """Build prompt for Domain Expert LLM - YOUR IMPLEMENTATION"""
        # YOUR CODE HERE  
        pass


# Example usage for Person 3
if __name__ == "__main__":
    # Initialize your pipeline
    llm_pipeline = TwoStageLLMPipeline()
    
    # Test with sample query
    result = llm_pipeline.process_query(
        "What are the premium calculation methods in this insurance policy?"
    )
    
    print("🎉 Two-Stage LLM Pipeline Result:")
    print(json.dumps(result, indent=2))
```

## 📊 Key Implementation Areas for Person 3

### **1. Prompt Engineering (Critical)**

**Task Analyzer Prompt Template:**
```python
def _build_task_analyzer_prompt(self, query: str, context: Dict) -> str:
    return f"""
    You are a Task Analyzer for a document intelligence system.
    
    USER QUERY: {query}
    
    AVAILABLE CONTEXT SAMPLE:
    {self._format_context_sample(context)}
    
    ANALYZE THE QUERY AND DETERMINE:
    1. Query type (factual, analytical, procedural, comparative)
    2. Domain focus (insurance, legal, financial, etc.)
    3. Required information sections
    4. Optimal search strategy
    5. Best response structure
    
    RESPOND IN JSON FORMAT:
    {{
        "query_type": "analytical",
        "domain": "insurance", 
        "required_sections": ["overview", "details", "examples"],
        "search_strategy": {{
            "primary_query": "optimized search terms",
            "filters": {{"content_type": ["text", "table"]}},
            "focus_areas": ["specific", "areas"]
        }},
        "response_structure": {{
            "format": "structured_analysis",
            "sections": ["section1", "section2"]
        }}
    }}
    """
```

**Domain Expert Prompt Template:**
```python
def _build_domain_expert_prompt(self, query: str, analysis: TaskAnalysis, context: Dict) -> str:
    return f"""
    You are a Domain Expert providing detailed analysis based on retrieved documents.
    
    ORIGINAL QUERY: {query}
    TASK ANALYSIS: {analysis.__dict__}
    
    RETRIEVED CONTEXT:
    {self._format_expert_context(context)}
    
    PROVIDE A COMPREHENSIVE RESPONSE:
    1. Answer the query using ONLY the provided context
    2. Structure according to the task analysis
    3. Include specific citations for each claim
    4. Maintain high accuracy and professional tone
    
    RESPONSE FORMAT:
    {{
        "answer": "Comprehensive response...",
        "sections": [
            {{
                "title": "Section Title",
                "content": "Detailed content...",
                "citations": [
                    {{
                        "source": "document.pdf",
                        "page": 15,
                        "chunk_id": "chunk_042",
                        "excerpt": "Relevant text excerpt..."
                    }}
                ]
            }}
        ],
        "confidence": 0.92,
        "methodology": "retrieval_augmented_analysis"
    }}
    """
```

### **2. Token Efficiency (Your Focus)**

```python
def optimize_token_usage(self, text: str, max_tokens: int) -> str:
    """
    Optimize prompts for token efficiency - Person 3 responsibility
    """
    # YOUR IMPLEMENTATION:
    # - Use tiktoken to count tokens
    # - Truncate context intelligently
    # - Preserve most relevant information
    # - Maintain citation capability
    pass

def track_token_usage(self, prompt: str, response: str) -> Dict[str, int]:
    """Track token usage for optimization"""
    # YOUR IMPLEMENTATION - track costs and efficiency
    pass
```

### **3. Citation System (Critical for Explainability)**

```python
def extract_citations(self, response_text: str, context_chunks: List[Dict]) -> List[Dict]:
    """
    Extract and verify citations from LLM response
    
    YOUR IMPLEMENTATION:
    - Parse LLM response for citation references
    - Map to actual context chunks
    - Verify accuracy of citations
    - Return structured citation data
    """
    pass

def build_citation_metadata(self, chunk: Dict) -> Dict[str, Any]:
    """Build rich citation metadata for explainability"""
    return {
        "source": chunk["metadata"]["source_url"],
        "page": chunk["metadata"]["page_number"],
        "chunk_id": chunk["metadata"]["chunk_id"],
        "content_type": chunk["metadata"]["content_type"],
        "extraction_method": chunk["metadata"]["extraction_method"],
        "relevance_score": chunk["score"],
        "excerpt": chunk["metadata"]["content"][:200] + "..."
    }
```

## 🧪 Testing Your Implementation

Create `test_llm_integration.py`:

```python
"""
Test your LLM integration with the completed retrieval foundation
"""

def test_two_stage_pipeline():
    """Test the complete two-stage pipeline"""
    
    # Initialize your pipeline
    pipeline = TwoStageLLMPipeline()
    
    # Test queries
    test_queries = [
        "What are the premium calculation methods?",
        "What medical conditions are excluded from coverage?", 
        "How do I file a claim?",
        "What is the maximum coverage amount?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        
        try:
            result = pipeline.process_query(query)
            
            # Validate results
            assert "task_analysis" in result
            assert "expert_response" in result
            assert "citations" in result["expert_response"]
            
            print(f"✅ Success: {result['expert_response']['confidence']:.2f} confidence")
            print(f"📚 Citations: {len(result['expert_response']['citations'])}")
            
        except Exception as e:
            print(f"❌ Failed: {e}")

if __name__ == "__main__":
    test_two_stage_pipeline()
```

## 📈 Performance Targets for Person 3

### **Token Efficiency Goals:**
- **Task Analyzer**: <2,000 tokens per query
- **Domain Expert**: <4,000 tokens per query  
- **Total Cost**: <$0.10 per query (GPT-4 pricing)

### **Latency Goals:**
- **Stage 1 (Task Analysis)**: <5 seconds
- **Stage 2 (Expert Response)**: <15 seconds
- **Total Pipeline**: <20 seconds

### **Quality Metrics:**
- **Citation Accuracy**: >95% verifiable citations
- **Response Relevance**: >90% user satisfaction
- **Token Efficiency**: <6,000 total tokens per query

## 🔗 Integration with Other Components

### **From Person 1 + 2 (Your Foundation):**
```python
# ✅ READY TO USE
from vector_database import VectorDatabasePipeline

pipeline = VectorDatabasePipeline()
search_results = pipeline.search_similar(query, top_k=5, hybrid=True)
```

### **For Person 4 (Backend API):**
```python
# YOUR OUTPUT TARGET
{
    "query": "user question",
    "answer": "Structured response with citations",
    "confidence": 0.92,
    "citations": [
        {
            "source": "policy.pdf",
            "page": 15,
            "excerpt": "Relevant text...",
            "chunk_id": "doc_1_chunk_042"
        }
    ],
    "methodology": "two_stage_llm_hybrid_search",
    "token_usage": {"total": 3500, "cost": 0.07}
}
```

### **For Person 5 (Frontend):**
```python
# YOUR STRUCTURED OUTPUT FOR UI
{
    "sections": [
        {
            "title": "Premium Calculation Methods",
            "content": "Based on the policy document...",
            "citations": [
                {
                    "source": "policy.pdf", 
                    "page": 15,
                    "clickable_reference": "doc_1_chunk_042",
                    "excerpt": "Premium is calculated based on..."
                }
            ]
        }
    ]
}
```

## 🎯 **SUCCESS CRITERIA FOR PERSON 3**

### ✅ **Must Have:**
1. **Two-Stage Pipeline**: Task Analyzer + Domain Expert working
2. **Citation System**: Every claim traceable to source
3. **Token Efficiency**: Optimized prompts under budget
4. **Structured Output**: JSON format ready for Person 4
5. **Error Handling**: Graceful degradation for edge cases

### 🚀 **Should Have:**
1. **Dynamic Prompts**: Adaptive based on query type
2. **Confidence Scoring**: Accuracy indicators
3. **Multiple LLM Support**: GPT-4, Claude options
4. **Token Tracking**: Cost monitoring and optimization

### 🎉 **Could Have:**
1. **Prompt Caching**: Reuse optimized prompts
2. **Response Validation**: Self-checking mechanisms  
3. **Multi-language Support**: International documents
4. **Advanced Reasoning**: Chain-of-thought prompting

## 🤝 **READY TO START!**

### **What's Already Working:**
- ✅ 802 chunks extracted and indexed
- ✅ Hybrid search with 89%+ accuracy
- ✅ Rich metadata for citations
- ✅ Auto-scaling Pinecone infrastructure
- ✅ Production-ready retrieval pipeline

### **Your Starting Command:**
```bash
# Initialize your LLM integration
python -c "
from vector_database import VectorDatabasePipeline
pipeline = VectorDatabasePipeline()
results = pipeline.search_similar('insurance premium calculation', top_k=5, hybrid=True)
print(f'✅ Foundation ready: {len(results[\"results\"])} chunks retrieved')
print('🚀 Ready for Person 3 LLM integration!')
"
```

---

> **Person 3: Your retrieval foundation is ready! Time to build the intelligent reasoning layer on top of the solid base Person 1 and 2 have created.** 🚀