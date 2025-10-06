"""
RAG Evaluation Test Script
Integration test for the comprehensive evaluation system

Run this script to evaluate your HackRx 6.0 document intelligence system
"""

import sys
import logging
from pathlib import Path
import json

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from rag_evaluation_metrics import RAGEvaluationSystem, quick_evaluation
from vector_database import VectorDatabasePipeline
from llm_integration import TwoStageLLMPipeline
from document_ingestion import DocumentIngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_evaluation_system():
    """Test the RAG evaluation system with existing pipelines"""
    
    logger.info("🧪 Testing RAG Evaluation System Integration")
    
    try:
        # Initialize existing pipelines (same as in main.py)
        logger.info("📝 Initializing Document Ingestion Pipeline...")
        document_pipeline = DocumentIngestionPipeline()
        
        logger.info("🔍 Initializing Vector Database Pipeline...")
        vector_pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        
        logger.info("🧠 Initializing Two-Stage LLM Pipeline...")
        llm_pipeline = TwoStageLLMPipeline()
        
        logger.info("✅ All pipelines initialized successfully!")
        
        # Test quick evaluation
        logger.info("🔬 Running quick evaluation with sample dataset...")
        evaluator, report = quick_evaluation(vector_pipeline, llm_pipeline, create_sample=True)
        
        if report:
            logger.info("✅ Evaluation completed successfully!")
            logger.info(f"📊 Results summary:")
            logger.info(f"   - Hit Rate: {report.retrieval_metrics.hit_rate:.1%}")
            logger.info(f"   - Citation Accuracy: {report.generation_metrics.citation_accuracy:.1%}")
            logger.info(f"   - Avg Latency: {report.performance_metrics.end_to_end_latency:.2f}s")
            logger.info(f"   - Total API Calls: {report.performance_metrics.total_api_calls}")
            
            return True, evaluator, report
        else:
            logger.error("❌ Evaluation failed to generate report")
            return False, None, None
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False, None, None


def test_with_real_document():
    """Test evaluation with a real document (if available)"""
    
    logger.info("📄 Testing with real document evaluation...")
    
    try:
        # Initialize pipelines
        vector_pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        llm_pipeline = TwoStageLLMPipeline()
        
        # Create evaluator
        evaluator = RAGEvaluationSystem(vector_pipeline, llm_pipeline)
        
        # Create a realistic test dataset
        realistic_dataset = [
            {
                "question": "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
                "document_url": "https://hackrx.blob.core.windows.net/assets/policy.pdf",
                "expected_answer": "A grace period of thirty days is provided for premium payment after the due date",
                "relevant_chunks": ["policy_chunk_grace_period", "policy_chunk_payment_terms"],
                "answer_type": "factual",
                "domain": "insurance",
                "difficulty": 2
            },
            {
                "question": "What is the waiting period for pre-existing diseases (PED) to be covered?",
                "document_url": "https://hackrx.blob.core.windows.net/assets/policy.pdf",
                "expected_answer": "There is a waiting period of thirty-six (36) months of continuous coverage",
                "relevant_chunks": ["policy_chunk_ped_waiting", "policy_chunk_coverage_terms"],
                "answer_type": "factual",
                "domain": "insurance",
                "difficulty": 3
            },
            {
                "question": "Does this policy cover maternity expenses, and what are the conditions?",
                "document_url": "https://hackrx.blob.core.windows.net/assets/policy.pdf",
                "expected_answer": "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy",
                "relevant_chunks": ["policy_chunk_maternity", "policy_chunk_coverage_details"],
                "answer_type": "reasoning",
                "domain": "insurance",
                "difficulty": 4
            }
        ]
        
        # Save realistic dataset
        dataset_path = "./evaluation_datasets/realistic_insurance_dataset.json"
        Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
        with open(dataset_path, 'w') as f:
            json.dump(realistic_dataset, f, indent=2)
        
        # Load and evaluate
        evaluator.load_evaluation_dataset(dataset_path, "realistic")
        
        logger.info("🔍 Running comprehensive evaluation...")
        report = evaluator.run_comprehensive_evaluation("realistic")
        
        logger.info("✅ Realistic document evaluation completed!")
        return True, evaluator, report
        
    except Exception as e:
        logger.error(f"❌ Realistic document test failed: {e}")
        return False, None, None


def benchmark_performance():
    """Benchmark system performance against targets"""
    
    logger.info("🏃 Running performance benchmark...")
    
    try:
        vector_pipeline = VectorDatabasePipeline(
            index_name="hackrx-docs-main", 
            auto_generate_index=False
        )
        llm_pipeline = TwoStageLLMPipeline()
        evaluator = RAGEvaluationSystem(vector_pipeline, llm_pipeline)
        
        # Create performance-focused dataset
        performance_dataset = [
            {
                "question": f"Test query {i} for performance evaluation",
                "document_url": "https://example.com/test.pdf",
                "expected_answer": f"Test answer {i}",
                "relevant_chunks": [f"chunk_{i}"],
                "answer_type": "factual",
                "domain": "test",
                "difficulty": 1
            }
            for i in range(10)  # 10 queries for performance testing
        ]
        
        dataset_path = "./evaluation_datasets/performance_benchmark.json"
        Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
        with open(dataset_path, 'w') as f:
            json.dump(performance_dataset, f, indent=2)
        
        evaluator.load_evaluation_dataset(dataset_path, "performance")
        
        # Run performance evaluation only
        performance_metrics = evaluator.evaluate_performance("performance")
        
        # Check against targets
        targets_met = {
            "latency": performance_metrics.end_to_end_latency < 30.0,  # <30s target
            "cost": performance_metrics.cost_per_query < 0.50,        # <$0.50 target
            "api_calls": performance_metrics.total_api_calls < 20     # <20 API calls target
        }
        
        logger.info("🎯 Performance benchmark results:")
        for metric, passed in targets_met.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {metric}: {status}")
        
        overall_pass = all(targets_met.values())
        logger.info(f"🏆 Overall benchmark: {'✅ PASS' if overall_pass else '❌ FAIL'}")
        
        return overall_pass, performance_metrics
        
    except Exception as e:
        logger.error(f"❌ Performance benchmark failed: {e}")
        return False, None


def generate_evaluation_report():
    """Generate a comprehensive evaluation report for the system"""
    
    logger.info("📊 Generating comprehensive evaluation report...")
    
    # Run all tests
    basic_test_pass, basic_evaluator, basic_report = test_evaluation_system()
    realistic_test_pass, realistic_evaluator, realistic_report = test_with_real_document()
    performance_pass, performance_metrics = benchmark_performance()
    
    # Compile overall report
    overall_report = {
        "evaluation_timestamp": "2024-01-15T10:30:00",
        "system_version": "hackrx_6.0_v1.0",
        "test_results": {
            "basic_functionality": {
                "passed": basic_test_pass,
                "hit_rate": basic_report.retrieval_metrics.hit_rate if basic_report else 0.0,
                "citation_accuracy": basic_report.generation_metrics.citation_accuracy if basic_report else 0.0,
                "avg_latency": basic_report.performance_metrics.end_to_end_latency if basic_report else 0.0
            },
            "realistic_documents": {
                "passed": realistic_test_pass,
                "hit_rate": realistic_report.retrieval_metrics.hit_rate if realistic_report else 0.0,
                "citation_accuracy": realistic_report.generation_metrics.citation_accuracy if realistic_report else 0.0,
                "avg_latency": realistic_report.performance_metrics.end_to_end_latency if realistic_report else 0.0
            },
            "performance_benchmark": {
                "passed": performance_pass,
                "avg_latency": performance_metrics.end_to_end_latency if performance_metrics else 0.0,
                "cost_per_query": performance_metrics.cost_per_query if performance_metrics else 0.0,
                "total_api_calls": performance_metrics.total_api_calls if performance_metrics else 0
            }
        },
        "overall_grade": "PASS" if all([basic_test_pass, realistic_test_pass, performance_pass]) else "FAIL",
        "recommendations": [
            "System meets HackRx 6.0 requirements" if all([basic_test_pass, realistic_test_pass, performance_pass]) else "System needs optimization",
            "Citation accuracy is excellent" if (basic_report and basic_report.generation_metrics.citation_accuracy > 0.95) else "Improve citation accuracy",
            "Performance is within targets" if performance_pass else "Optimize for better performance"
        ]
    }
    
    # Save overall report
    report_path = "./evaluation_results/comprehensive_evaluation_report.json"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(overall_report, f, indent=2)
    
    logger.info(f"📄 Comprehensive report saved to: {report_path}")
    logger.info(f"🏆 Overall Grade: {overall_report['overall_grade']}")
    
    return overall_report


if __name__ == "__main__":
    print("🔬 RAG Evaluation System Test Suite")
    print("=" * 50)
    
    # Run comprehensive evaluation
    report = generate_evaluation_report()
    
    print(f"\n🎯 Final Results:")
    print(f"Overall Grade: {report['overall_grade']}")
    print(f"Basic Functionality: {'✅ PASS' if report['test_results']['basic_functionality']['passed'] else '❌ FAIL'}")
    print(f"Realistic Documents: {'✅ PASS' if report['test_results']['realistic_documents']['passed'] else '❌ FAIL'}")
    print(f"Performance Benchmark: {'✅ PASS' if report['test_results']['performance_benchmark']['passed'] else '❌ FAIL'}")
    
    print(f"\n📋 Recommendations:")
    for rec in report['recommendations']:
        print(f"   • {rec}")
    
    print(f"\n📊 Key Metrics:")
    if report['test_results']['realistic_documents']['passed']:
        real_results = report['test_results']['realistic_documents']
        print(f"   • Hit Rate: {real_results['hit_rate']:.1%}")
        print(f"   • Citation Accuracy: {real_results['citation_accuracy']:.1%}")
        print(f"   • Avg Latency: {real_results['avg_latency']:.2f}s")
    
    if report['test_results']['performance_benchmark']['passed']:
        perf_results = report['test_results']['performance_benchmark']
        print(f"   • Cost/Query: ${perf_results['cost_per_query']:.4f}")
        print(f"   • API Calls: {perf_results['total_api_calls']}")
    
    print("\n" + "=" * 50)
    print("🎉 Evaluation complete!")
    
    # Exit with appropriate code
    exit_code = 0 if report['overall_grade'] == 'PASS' else 1
    sys.exit(exit_code)


