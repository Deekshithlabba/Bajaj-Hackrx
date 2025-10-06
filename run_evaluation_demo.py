#!/usr/bin/env python3
"""
RAG Evaluation System Demo
Quick demonstration of the comprehensive evaluation metrics system

Run this script to see the evaluation system in action with your existing HackRx 6.0 system.
"""

import sys
import json
import logging
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from rag_evaluation_metrics import RAGEvaluationSystem, quick_evaluation
from vector_database import VectorDatabasePipeline
from llm_integration import TwoStageLLMPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main demonstration function"""
    print("🔬 RAG Evaluation System Demo")
    print("=" * 60)
    print()
    
    try:
        # Initialize existing pipelines
        print("🚀 Initializing HackRx 6.0 pipelines...")
        vector_pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        llm_pipeline = TwoStageLLMPipeline()
        print("✅ Pipelines initialized successfully!")
        print()
        
        # Quick evaluation demonstration
        print("🎯 Running Quick Evaluation Demo...")
        print("-" * 40)
        evaluator, report = quick_evaluation(vector_pipeline, llm_pipeline, create_sample=True)
        
        if report:
            print("\n📊 EVALUATION RESULTS:")
            print("=" * 40)
            
            # Retrieval Quality
            print(f"🎯 RETRIEVAL QUALITY:")
            print(f"   Hit Rate: {report.retrieval_metrics.hit_rate:.1%} {'✅ PASS' if report.retrieval_metrics.hit_rate > 0.95 else '❌ FAIL'} (Goal: >95%)")
            print(f"   Mean Reciprocal Rank: {report.retrieval_metrics.mean_reciprocal_rank:.3f}")
            print(f"   Precision@5: {report.retrieval_metrics.precision_at_k.get(5, 0.0):.3f}")
            print()
            
            # Generation Quality
            print(f"🤖 GENERATION QUALITY:")
            print(f"   Faithfulness: {report.generation_metrics.faithfulness:.1%}")
            print(f"   Citation Accuracy: {report.generation_metrics.citation_accuracy:.1%} {'✅ PASS' if report.generation_metrics.citation_accuracy > 0.95 else '❌ FAIL'} (Goal: >95%)")
            print(f"   Relevance: {report.generation_metrics.relevance:.1%}")
            print(f"   Hallucination Rate: {report.generation_metrics.hallucination_rate:.1%}")
            print()
            
            # Performance & Cost
            print(f"⚡ PERFORMANCE & COST:")
            print(f"   Avg Latency: {report.performance_metrics.end_to_end_latency:.2f}s {'✅ PASS' if report.performance_metrics.end_to_end_latency < 30 else '❌ FAIL'} (Goal: <30s)")
            print(f"   Total API Calls: {report.performance_metrics.total_api_calls}")
            print(f"   Cost per Query: ${report.performance_metrics.cost_per_query:.4f}")
            print(f"   Cache Hit Rate: {report.performance_metrics.cache_hit_rate:.1%}")
            print(f"   Throughput: {report.performance_metrics.throughput_qps:.2f} QPS")
            print()
            
            # Overall Assessment
            targets_met = {
                'hit_rate': report.retrieval_metrics.hit_rate > 0.95,
                'citation_accuracy': report.generation_metrics.citation_accuracy > 0.95,
                'latency': report.performance_metrics.end_to_end_latency < 30.0
            }
            
            overall_grade = "✅ EXCELLENT" if all(targets_met.values()) else "⚠️ NEEDS OPTIMIZATION"
            print(f"🏆 OVERALL GRADE: {overall_grade}")
            print()
            
            # Recommendations
            print("💡 RECOMMENDATIONS:")
            if targets_met['hit_rate']:
                print("   ✅ Retrieval quality is excellent")
            else:
                print("   ❌ Improve retrieval: optimize embeddings and chunk size")
                
            if targets_met['citation_accuracy']:
                print("   ✅ Citation system is highly accurate")
            else:
                print("   ❌ Improve citations: enhance metadata extraction")
                
            if targets_met['latency']:
                print("   ✅ Performance meets real-time requirements")
            else:
                print("   ❌ Optimize performance: implement caching and batching")
            
            print()
            
        else:
            print("❌ Evaluation failed to generate report")
            return 1
            
        # Demonstrate individual metric evaluation
        print("🔍 Individual Metrics Demonstration:")
        print("-" * 40)
        
        # Create a custom mini-dataset
        mini_dataset = [
            {
                "question": "What is the premium payment grace period?",
                "document_url": "https://example.com/policy.pdf",
                "expected_answer": "30 days grace period",
                "relevant_chunks": ["chunk_grace_period"],
                "answer_type": "factual",
                "domain": "insurance",
                "difficulty": 2
            }
        ]
        
        dataset_path = "./evaluation_datasets/demo_dataset.json"
        Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
        with open(dataset_path, 'w') as f:
            json.dump(mini_dataset, f, indent=2)
        
        evaluator.load_evaluation_dataset(dataset_path, "demo")
        
        # Individual evaluations
        print("📍 Retrieval Quality Evaluation...")
        retrieval_metrics = evaluator.evaluate_retrieval_quality("demo")
        print(f"   Result: Hit Rate {retrieval_metrics.hit_rate:.1%}")
        
        print("🎯 Generation Quality Evaluation...")
        generation_metrics = evaluator.evaluate_generation_quality("demo")
        print(f"   Result: Citation Accuracy {generation_metrics.citation_accuracy:.1%}")
        
        print("⚡ Performance Evaluation...")
        performance_metrics = evaluator.evaluate_performance("demo")
        print(f"   Result: Avg Latency {performance_metrics.end_to_end_latency:.2f}s")
        print()
        
        # Usage instructions
        print("🛠️ HOW TO USE IN YOUR WORKFLOW:")
        print("=" * 40)
        print("1. Basic Evaluation:")
        print("   python test_rag_evaluation.py")
        print()
        print("2. Enhanced Server with Metrics:")
        print("   python enhanced_main_with_metrics.py")
        print()
        print("3. Check Real-time Metrics:")
        print("   curl -H 'Authorization: Bearer your_token' http://localhost:8000/metrics")
        print()
        print("4. Run On-demand Evaluation:")
        print("   curl -X POST -H 'Authorization: Bearer your_token' http://localhost:8000/evaluate")
        print()
        print("5. Custom Evaluation:")
        print("   Create dataset JSON → Load with evaluator.load_evaluation_dataset() → Run evaluation")
        print()
        
        print("📚 For detailed guide, see: RAG_EVALUATION_GUIDE.md")
        print()
        print("🎉 Demo completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


