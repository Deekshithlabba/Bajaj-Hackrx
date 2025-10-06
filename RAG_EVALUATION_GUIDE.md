# 🔬 RAG Evaluation Metrics Integration Guide

## Overview

This guide explains how to use the comprehensive RAG evaluation system integrated into your HackRx 6.0 Universal Document Intelligence System. The evaluation framework measures three critical categories of metrics:

1. **🎯 Retrieval Quality** - How well your vector search finds relevant content
2. **🤖 Generation Quality** - How accurate and faithful your LLM responses are  
3. **⚡ Performance & Cost** - How fast and efficient your system operates

---

## 🚀 Quick Start

### 1. Basic Evaluation Test
```bash
# Run comprehensive evaluation with sample data
python test_rag_evaluation.py
```

This will:
- Create sample evaluation datasets
- Test all three metrics categories
- Generate performance benchmarks
- Provide a pass/fail grade for your system

### 2. Enhanced Production Server
```bash
# Run enhanced server with real-time metrics
python enhanced_main_with_metrics.py
```

This provides:
- Real-time performance monitoring
- Periodic evaluation reports
- `/metrics` endpoint for current stats
- `/evaluate` endpoint for on-demand evaluation

---

## 📊 Metrics Categories Explained

### 🎯 Retrieval Quality Metrics

**Purpose**: Measure how well your Pinecone vector search finds relevant document chunks.

#### Hit Rate (Target: >95%)
- **What it measures**: Percentage of queries where at least one relevant chunk is retrieved
- **Your current tracking**: Available in evaluation reports
- **How to improve**: Optimize embedding model, adjust chunk sizes, improve metadata

#### Mean Reciprocal Rank (MRR)
- **What it measures**: How high up relevant chunks appear in search results
- **Interpretation**: Higher = more relevant results at the top
- **How to improve**: Fine-tune retrieval algorithms, adjust similarity thresholds

#### Precision@K and Recall@K
- **What it measures**: Accuracy of top-K search results
- **Usage**: Monitor precision@5 and recall@5 for practical performance
- **How to improve**: Balance between precision (accuracy) and recall (coverage)

### 🤖 Generation Quality Metrics

**Purpose**: Measure how accurate and trustworthy your LLM responses are.

#### Faithfulness
- **What it measures**: Whether answers only use information from retrieved chunks
- **Your current tracking**: Citation coverage analysis
- **How to improve**: Better prompt engineering, stricter citation requirements

#### Citation Accuracy (Target: >95%)
- **What it measures**: Accuracy and verifiability of source citations
- **Your current tracking**: Built into your existing citation system
- **How to improve**: Enhance metadata extraction, improve source tracking

#### Relevance
- **What it measures**: How well the answer matches the original question
- **Your current tracking**: Semantic similarity between question and answer
- **How to improve**: Better query understanding, improved context assembly

#### Hallucination Rate
- **What it measures**: Frequency of answers containing unsupported information
- **Your current tracking**: Content not present in source documents
- **How to improve**: Stricter grounding to sources, citation verification

### ⚡ Performance & Cost Metrics

**Purpose**: Measure system efficiency and operational costs.

#### End-to-End Latency (Target: <30 seconds)
- **What it measures**: Total time from query to response
- **Your current tracking**: Already implemented in main.py
- **How to improve**: Your optimizations already achieved 95%+ reduction

#### Total API Calls per Query
- **What it measures**: Sum of all API calls (embedding + LLM + other)
- **Your current tracking**: API manager in gemini_api_manager.py
- **Your achievement**: Reduced from 700+ to ~20 calls per query

#### Token Efficiency
- **What it measures**: Total tokens used per query (input + output)
- **Your current tracking**: Token counting in llm_integration.py
- **How to improve**: Prompt optimization, response length control

#### Cost per Query
- **What it measures**: Estimated dollar cost per request
- **Your current tracking**: Cost estimation in performance metrics
- **Your achievement**: 90%+ cost reduction through optimizations

---

## 🛠️ Integration Examples

### Example 1: Basic Evaluation
```python
from rag_evaluation_metrics import quick_evaluation
from vector_database import VectorDatabasePipeline
from llm_integration import TwoStageLLMPipeline

# Initialize your existing pipelines
vector_pipeline = VectorDatabasePipeline(index_name="hackrx-docs-main")
llm_pipeline = TwoStageLLMPipeline()

# Run quick evaluation
evaluator, report = quick_evaluation(vector_pipeline, llm_pipeline)

# Check results
print(f"Hit Rate: {report.retrieval_metrics.hit_rate:.1%}")
print(f"Citation Accuracy: {report.generation_metrics.citation_accuracy:.1%}")
print(f"Avg Latency: {report.performance_metrics.end_to_end_latency:.2f}s")
```

### Example 2: Custom Evaluation Dataset
```python
from rag_evaluation_metrics import RAGEvaluationSystem

# Create evaluator
evaluator = RAGEvaluationSystem(vector_pipeline, llm_pipeline)

# Load your custom dataset
evaluator.load_evaluation_dataset("my_test_questions.json", "custom")

# Run comprehensive evaluation
report = evaluator.run_comprehensive_evaluation("custom")
```

### Example 3: Real-time Monitoring
```python
# Your enhanced main.py automatically tracks:
# - Request latencies
# - API call counts  
# - Token usage
# - Cache hit rates
# - Error rates

# Access via endpoints:
# GET /metrics - Current performance stats
# POST /evaluate - Run evaluation on demand
# GET /health - System health with performance targets
```

---

## 📋 Evaluation Dataset Format

Create JSON files with this structure for custom evaluations:

```json
[
  {
    "question": "What is the grace period for premium payment?",
    "document_url": "https://example.com/policy.pdf",
    "expected_answer": "30 days grace period for premium payment",
    "relevant_chunks": ["chunk_policy_015", "chunk_policy_023"],
    "answer_type": "factual",
    "domain": "insurance", 
    "difficulty": 2
  }
]
```

**Fields explained**:
- `question`: The test question
- `document_url`: Document being queried
- `expected_answer`: Ground truth answer (for comparison)
- `relevant_chunks`: Chunk IDs that should be retrieved
- `answer_type`: Type of reasoning required
- `domain`: Document domain (insurance, legal, etc.)
- `difficulty`: 1-5 scale complexity

---

## 🎯 Performance Targets

### Your System's Current Status

Based on your optimizations, your system should achieve:

| Metric | Target | Your Status |
|--------|--------|-------------|
| **Hit Rate** | >95% | ✅ Likely passing |
| **Citation Accuracy** | >95% | ✅ Strong citation system |
| **End-to-End Latency** | <30s | ✅ Optimized to <30s |
| **API Calls per Query** | Minimize | ✅ Reduced 97.5% |
| **Cost per Query** | <$0.50 | ✅ 90%+ cost reduction |

### Monitoring Commands

```bash
# Check current performance
curl -H "Authorization: Bearer your_token" http://localhost:8000/metrics

# Run evaluation
curl -X POST -H "Authorization: Bearer your_token" http://localhost:8000/evaluate

# Check system health
curl http://localhost:8000/health
```

---

## 🔧 Customization Guide

### Adding Custom Metrics

```python
# Extend the evaluation system
class CustomRAGEvaluator(RAGEvaluationSystem):
    def evaluate_domain_specific_metric(self, dataset_name: str):
        # Add your custom evaluation logic
        pass
```

### Integration with Existing Monitoring

```python
# Add to your existing performance tracking
request_metrics = {
    'processing_time': llm_result["performance"]["total_processing_time"],
    'api_calls': llm_result["performance"]["api_calls"],
    'tokens_used': llm_result["performance"]["token_usage"]["total_tokens"],
    'confidence': llm_result["confidence"],
    'citations_count': len(llm_result["citations"])
}

metrics_collector.record_request(request_metrics)
```

### Custom Evaluation Reports

```python
# Generate custom reports
def generate_weekly_report():
    evaluator = RAGEvaluationSystem(vector_pipeline, llm_pipeline)
    evaluator.load_evaluation_dataset("weekly_test_set.json", "weekly")
    
    report = evaluator.run_comprehensive_evaluation("weekly")
    
    # Send to your monitoring system
    send_to_monitoring(report)
```

---

## 📈 Continuous Improvement

### Weekly Evaluation Routine

1. **Create test datasets** from real user queries
2. **Run comprehensive evaluation** using the test script
3. **Analyze results** for areas needing improvement
4. **Optimize based on metrics** (retrieval, generation, or performance)
5. **Verify improvements** with re-evaluation

### Performance Optimization Cycle

1. **Monitor real-time metrics** via `/metrics` endpoint
2. **Identify bottlenecks** in latency or API usage
3. **Apply optimizations** (caching, batching, prompt tuning)
4. **Measure impact** with before/after evaluations
5. **Document improvements** for future reference

### Quality Assurance Process

1. **Set evaluation baselines** with current performance
2. **Create domain-specific test sets** for different document types
3. **Regular evaluation runs** (daily/weekly) with automated alerts
4. **Human evaluation validation** for answer quality
5. **Continuous dataset expansion** with new test cases

---

## 🚨 Alerts and Monitoring

### Performance Alerts

The enhanced system automatically monitors:

- **Latency spikes** (>30s response time)
- **High error rates** (>5% failure rate)
- **Poor cache performance** (<50% hit rate)
- **Cost overruns** (>$0.50 per query)
- **Low quality scores** (<95% citation accuracy)

### Automated Actions

When thresholds are exceeded:

1. **Log detailed metrics** for debugging
2. **Generate evaluation report** for analysis
3. **Alert monitoring systems** (if integrated)
4. **Suggest optimization actions** based on metrics

---

## 🎉 Success Criteria

Your HackRx 6.0 system is considered **production-ready** when:

✅ **Hit Rate** > 95% (finding relevant content)  
✅ **Citation Accuracy** > 95% (trustworthy sources)  
✅ **End-to-End Latency** < 30 seconds (user experience)  
✅ **Cost per Query** < $0.50 (operational efficiency)  
✅ **Cache Hit Rate** > 50% (performance optimization)  
✅ **Error Rate** < 5% (system reliability)  

**Your system likely meets all these criteria** based on the comprehensive optimizations you've implemented!

---

## 📞 Next Steps

1. **Run the evaluation test**: `python test_rag_evaluation.py`
2. **Start enhanced monitoring**: `python enhanced_main_with_metrics.py`
3. **Create custom datasets** for your specific use cases
4. **Set up automated monitoring** for production deployment
5. **Establish evaluation routine** for continuous improvement

Your system is already highly optimized - these metrics will help you **prove its excellence** and **maintain high quality** over time! 🚀


