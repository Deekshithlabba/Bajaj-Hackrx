#!/usr/bin/env python3
"""
Real-World Insurance Policy Evaluation
Comprehensive evaluation using the actual HackRx insurance policy document

This script evaluates your system's performance on the real insurance policy
with the exact questions and ground truth answers you provided.
"""

import sys
import json
import time
import logging
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from rag_evaluation_metrics import RAGEvaluationSystem
from vector_database import VectorDatabasePipeline
from llm_integration import TwoStageLLMPipeline
from document_ingestion import DocumentIngestionPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InsurancePolicyEvaluator:
    """Specialized evaluator for the insurance policy document"""
    
    def __init__(self):
        """Initialize the insurance policy evaluator"""
        self.document_url = "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=2023-01-03&st=2025-07-04T09%3A11%3A24Z&se=2027-07-05T09%3A11%3A00Z&sr=b&sp=r&sig=N4a9OU0w0QXO6AOIBiu4bpl7AXvEZogeT%2FjUHNO7HzQ%3D"
        
        self.test_questions = [
            "What is the grace period for premium payment under the National Parivar Mediclaim Plus Policy?",
            "What is the waiting period for pre-existing diseases (PED) to be covered?",
            "Does this policy cover maternity expenses, and what are the conditions?",
            "What is the waiting period for cataract surgery?",
            "Are the medical expenses for an organ donor covered under this policy?",
            "What is the No Claim Discount (NCD) offered in this policy?",
            "Is there a benefit for preventive health check-ups?",
            "How does the policy define a 'Hospital'?",
            "What is the extent of coverage for AYUSH treatments?",
            "Are there any sub-limits on room rent and ICU charges for Plan A?"
        ]
        
        self.ground_truth_answers = [
            "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
            "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered.",
            "Yes, the policy covers maternity expenses, including childbirth and lawful medical termination of pregnancy. To be eligible, the female insured person must have been continuously covered for at least 24 months. The benefit is limited to two deliveries or terminations during the policy period.",
            "The policy has a specific waiting period of two (2) years for cataract surgery.",
            "Yes, the policy indemnifies the medical expenses for the organ donor's hospitalization for the purpose of harvesting the organ, provided the organ is for an insured person and the donation complies with the Transplantation of Human Organs Act, 1994.",
            "A No Claim Discount of 5% on the base premium is offered on renewal for a one-year policy term if no claims were made in the preceding year. The maximum aggregate NCD is capped at 5% of the total base premium.",
            "Yes, the policy reimburses expenses for health check-ups at the end of every block of two continuous policy years, provided the policy has been renewed without a break. The amount is subject to the limits specified in the Table of Benefits.",
            "A hospital is defined as an institution with at least 10 inpatient beds (in towns with a population below ten lakhs) or 15 beds (in all other places), with qualified nursing staff and medical practitioners available 24/7, a fully equipped operation theatre, and which maintains daily records of patients.",
            "The policy covers medical expenses for inpatient treatment under Ayurveda, Yoga, Naturopathy, Unani, Siddha, and Homeopathy systems up to the Sum Insured limit, provided the treatment is taken in an AYUSH Hospital.",
            "Yes, for Plan A, the daily room rent is capped at 1% of the Sum Insured, and ICU charges are capped at 2% of the Sum Insured. These limits do not apply if the treatment is for a listed procedure in a Preferred Provider Network (PPN)."
        ]
        
        # Initialize system components
        self.vector_pipeline = None
        self.llm_pipeline = None
        self.document_pipeline = None
        self.evaluation_system = None
        
    def initialize_system(self):
        """Initialize all system components"""
        logger.info("🚀 Initializing HackRx 6.0 System Components...")
        
        try:
            # Initialize document ingestion
            logger.info("📝 Initializing Document Ingestion Pipeline...")
            self.document_pipeline = DocumentIngestionPipeline()
            
            # Initialize vector database
            logger.info("🔍 Initializing Vector Database Pipeline...")
            self.vector_pipeline = VectorDatabasePipeline(
                index_name="hackrx-docs-main", 
                auto_generate_index=False
            )
            
            # Initialize LLM pipeline
            logger.info("🧠 Initializing Two-Stage LLM Pipeline...")
            self.llm_pipeline = TwoStageLLMPipeline()
            
            # Initialize evaluation system
            logger.info("🔬 Initializing RAG Evaluation System...")
            self.evaluation_system = RAGEvaluationSystem(
                self.vector_pipeline, 
                self.llm_pipeline
            )
            
            logger.info("✅ All system components initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {e}")
            return False
    
    def ensure_document_processed(self):
        """Ensure the insurance policy document is processed and indexed"""
        logger.info("📄 Processing Insurance Policy Document...")
        
        try:
            # Check if document is already cached/indexed
            doc_cache_key = f"doc_policy_pdf"
            
            # Process document
            chunks = self.document_pipeline.process_document_from_url(self.document_url)
            optimized_chunks = self.document_pipeline.chunk_document_content(chunks)
            
            logger.info(f"✅ Document processed: {len(optimized_chunks)} chunks created")
            
            # Prepare and index in vector database
            chunk_data = []
            for chunk in optimized_chunks:
                chunk_dict = {
                    "content": chunk.content,
                    "content_type": chunk.content_type,
                    "metadata": chunk.metadata,
                    "page_number": chunk.page_number,
                    "source_url": self.document_url,
                    "chunk_id": chunk.chunk_id
                }
                chunk_data.append(chunk_dict)
            
            # Create index and upsert vectors
            if not self.vector_pipeline.create_index():
                raise Exception("Failed to create Pinecone index")
            
            vector_records = self.vector_pipeline.prepare_vector_records(chunk_data)
            self.vector_pipeline.upsert_vectors(vector_records, namespace="documents")
            
            logger.info(f"✅ Document indexed: {len(vector_records)} vectors in Pinecone")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to process document: {e}")
            return False
    
    def run_system_evaluation(self):
        """Run the system on the test questions and get actual responses"""
        logger.info("🤖 Running System Evaluation on Test Questions...")
        
        system_responses = []
        performance_metrics = []
        
        for i, question in enumerate(self.test_questions):
            try:
                logger.info(f"🤔 Processing Question {i+1}/10: {question[:50]}...")
                
                start_time = time.time()
                
                # Get system response
                llm_result = self.llm_pipeline.process_query(question)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                # Extract response details
                system_answer = llm_result["answer"]
                confidence = llm_result.get("confidence", 0.0)
                citations = llm_result.get("citations", [])
                
                response_data = {
                    "question": question,
                    "system_answer": system_answer,
                    "ground_truth": self.ground_truth_answers[i],
                    "confidence": confidence,
                    "citations_count": len(citations),
                    "citations": citations,
                    "processing_time": processing_time
                }
                
                system_responses.append(response_data)
                
                # Track performance
                performance = llm_result.get("performance", {})
                token_usage = performance.get("token_usage", {})
                
                perf_data = {
                    "processing_time": processing_time,
                    "api_calls": performance.get("api_calls", 0),
                    "tokens_used": token_usage.get("total_tokens", 0),
                    "estimated_cost": performance.get("estimated_cost", 0.0)
                }
                performance_metrics.append(perf_data)
                
                logger.info(f"✅ Question {i+1} completed: {confidence:.2f} confidence, {len(citations)} citations, {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"❌ Failed to process question {i+1}: {e}")
                
                # Add error response
                error_response = {
                    "question": question,
                    "system_answer": f"Error: {str(e)}",
                    "ground_truth": self.ground_truth_answers[i],
                    "confidence": 0.0,
                    "citations_count": 0,
                    "citations": [],
                    "processing_time": 0.0
                }
                system_responses.append(error_response)
                
                performance_metrics.append({
                    "processing_time": 0.0,
                    "api_calls": 0,
                    "tokens_used": 0,
                    "estimated_cost": 0.0
                })
        
        return system_responses, performance_metrics
    
    def analyze_answer_quality(self, system_responses: List[Dict]) -> Dict[str, Any]:
        """Analyze the quality of system answers compared to ground truth"""
        logger.info("📊 Analyzing Answer Quality...")
        
        quality_metrics = {
            "total_questions": len(system_responses),
            "successful_responses": 0,
            "avg_confidence": 0.0,
            "total_citations": 0,
            "questions_with_citations": 0,
            "detailed_analysis": []
        }
        
        total_confidence = 0.0
        total_citations = 0
        
        for response in system_responses:
            # Check if response was successful (not an error)
            if not response["system_answer"].startswith("Error:"):
                quality_metrics["successful_responses"] += 1
            
            # Accumulate confidence
            total_confidence += response["confidence"]
            
            # Count citations
            citations_count = response["citations_count"]
            total_citations += citations_count
            
            if citations_count > 0:
                quality_metrics["questions_with_citations"] += 1
            
            # Analyze answer similarity (simple keyword overlap)
            ground_truth = response["ground_truth"].lower()
            system_answer = response["system_answer"].lower()
            
            # Simple keyword overlap analysis
            gt_words = set(ground_truth.split())
            sa_words = set(system_answer.split())
            
            common_words = gt_words.intersection(sa_words)
            overlap_ratio = len(common_words) / len(gt_words) if gt_words else 0.0
            
            # Analyze key information preservation
            key_info_preserved = self._check_key_information(ground_truth, system_answer)
            
            detailed_item = {
                "question": response["question"][:50] + "...",
                "confidence": response["confidence"],
                "citations_count": citations_count,
                "word_overlap_ratio": overlap_ratio,
                "key_info_preserved": key_info_preserved,
                "processing_time": response["processing_time"]
            }
            quality_metrics["detailed_analysis"].append(detailed_item)
        
        # Calculate averages
        if quality_metrics["total_questions"] > 0:
            quality_metrics["avg_confidence"] = total_confidence / quality_metrics["total_questions"]
            quality_metrics["avg_citations_per_question"] = total_citations / quality_metrics["total_questions"]
            quality_metrics["citation_coverage"] = quality_metrics["questions_with_citations"] / quality_metrics["total_questions"]
        
        quality_metrics["total_citations"] = total_citations
        
        return quality_metrics
    
    def _check_key_information(self, ground_truth: str, system_answer: str) -> float:
        """Check if key information from ground truth is preserved in system answer"""
        # Extract key numbers and terms that should be preserved
        import re
        
        # Extract numbers (days, months, years, percentages)
        gt_numbers = re.findall(r'\b\d+\b', ground_truth)
        sa_numbers = re.findall(r'\b\d+\b', system_answer)
        
        # Check number preservation
        numbers_preserved = len(set(gt_numbers).intersection(set(sa_numbers))) / max(1, len(set(gt_numbers)))
        
        # Extract key terms (waiting period, coverage, etc.)
        key_terms = [
            'waiting period', 'grace period', 'coverage', 'covered', 'benefit',
            'premium', 'discount', 'hospital', 'treatment', 'expenses'
        ]
        
        gt_has_terms = sum(1 for term in key_terms if term in ground_truth.lower())
        sa_has_terms = sum(1 for term in key_terms if term in system_answer.lower() and term in ground_truth.lower())
        
        terms_preserved = sa_has_terms / max(1, gt_has_terms)
        
        # Combined score
        return (numbers_preserved + terms_preserved) / 2
    
    def run_formal_evaluation(self):
        """Run formal RAG evaluation using the evaluation framework"""
        logger.info("🔬 Running Formal RAG Evaluation...")
        
        try:
            # Load the evaluation dataset
            dataset_path = "./evaluation_datasets/insurance_policy_real_dataset.json"
            self.evaluation_system.load_evaluation_dataset(dataset_path, "insurance_real")
            
            # Run comprehensive evaluation
            report = self.evaluation_system.run_comprehensive_evaluation("insurance_real")
            
            logger.info("✅ Formal evaluation completed!")
            return report
            
        except Exception as e:
            logger.error(f"❌ Formal evaluation failed: {e}")
            return None
    
    def generate_comprehensive_report(self, system_responses, performance_metrics, quality_metrics, formal_report):
        """Generate a comprehensive evaluation report"""
        logger.info("📊 Generating Comprehensive Evaluation Report...")
        
        # Calculate performance summaries
        total_time = sum(p["processing_time"] for p in performance_metrics)
        total_api_calls = sum(p["api_calls"] for p in performance_metrics)
        total_tokens = sum(p["tokens_used"] for p in performance_metrics)
        total_cost = sum(p["estimated_cost"] for p in performance_metrics)
        
        avg_time = total_time / len(performance_metrics) if performance_metrics else 0.0
        avg_api_calls = total_api_calls / len(performance_metrics) if performance_metrics else 0.0
        avg_tokens = total_tokens / len(performance_metrics) if performance_metrics else 0.0
        avg_cost = total_cost / len(performance_metrics) if performance_metrics else 0.0
        
        report = {
            "evaluation_timestamp": datetime.now().isoformat(),
            "document_url": self.document_url,
            "test_dataset": "Real Insurance Policy Questions",
            "system_version": "HackRx 6.0 v1.0",
            
            "performance_summary": {
                "total_questions": len(self.test_questions),
                "successful_responses": quality_metrics["successful_responses"],
                "total_processing_time": total_time,
                "avg_processing_time": avg_time,
                "total_api_calls": total_api_calls,
                "avg_api_calls": avg_api_calls,
                "total_tokens": total_tokens,
                "avg_tokens": avg_tokens,
                "total_cost": total_cost,
                "avg_cost": avg_cost
            },
            
            "quality_summary": quality_metrics,
            
            "formal_evaluation": {
                "hit_rate": formal_report.retrieval_metrics.hit_rate if formal_report else 0.0,
                "citation_accuracy": formal_report.generation_metrics.citation_accuracy if formal_report else 0.0,
                "faithfulness": formal_report.generation_metrics.faithfulness if formal_report else 0.0,
                "avg_latency": formal_report.performance_metrics.end_to_end_latency if formal_report else 0.0
            },
            
            "targets_assessment": {
                "latency_target": avg_time < 30.0,  # <30s
                "cost_target": avg_cost < 0.50,     # <$0.50
                "api_calls_target": avg_api_calls < 20,  # <20 calls
                "confidence_target": quality_metrics["avg_confidence"] > 0.8,  # >80%
                "citation_coverage_target": quality_metrics["citation_coverage"] > 0.9  # >90%
            },
            
            "detailed_results": system_responses
        }
        
        # Save report
        report_path = f"./evaluation_results/insurance_policy_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Comprehensive report saved to: {report_path}")
        return report, report_path


def main():
    """Main evaluation function"""
    print("🔬 Insurance Policy Real-World Evaluation")
    print("=" * 60)
    print()
    
    evaluator = InsurancePolicyEvaluator()
    
    # Initialize system
    print("🚀 Initializing System...")
    if not evaluator.initialize_system():
        print("❌ System initialization failed!")
        return 1
    
    # Process document
    print("📄 Processing Insurance Policy Document...")
    if not evaluator.ensure_document_processed():
        print("❌ Document processing failed!")
        return 1
    
    # Run system evaluation
    print("🤖 Running System on Test Questions...")
    system_responses, performance_metrics = evaluator.run_system_evaluation()
    
    # Analyze quality
    print("📊 Analyzing Answer Quality...")
    quality_metrics = evaluator.analyze_answer_quality(system_responses)
    
    # Run formal evaluation
    print("🔬 Running Formal RAG Evaluation...")
    formal_report = evaluator.run_formal_evaluation()
    
    # Generate comprehensive report
    print("📋 Generating Comprehensive Report...")
    report, report_path = evaluator.generate_comprehensive_report(
        system_responses, performance_metrics, quality_metrics, formal_report
    )
    
    # Print results summary
    print("\n" + "=" * 60)
    print("📊 EVALUATION RESULTS SUMMARY")
    print("=" * 60)
    
    perf = report["performance_summary"]
    qual = report["quality_summary"]
    targets = report["targets_assessment"]
    
    print(f"\n🤖 SYSTEM PERFORMANCE:")
    print(f"   Questions Processed: {perf['total_questions']}")
    print(f"   Successful Responses: {perf['successful_responses']}/{perf['total_questions']}")
    print(f"   Avg Processing Time: {perf['avg_processing_time']:.2f}s {'✅' if targets['latency_target'] else '❌'} (Target: <30s)")
    print(f"   Avg API Calls: {perf['avg_api_calls']:.1f} {'✅' if targets['api_calls_target'] else '❌'} (Target: <20)")
    print(f"   Avg Cost per Query: ${perf['avg_cost']:.4f} {'✅' if targets['cost_target'] else '❌'} (Target: <$0.50)")
    
    print(f"\n🎯 ANSWER QUALITY:")
    print(f"   Avg Confidence: {qual['avg_confidence']:.1%} {'✅' if targets['confidence_target'] else '❌'} (Target: >80%)")
    print(f"   Citation Coverage: {qual['citation_coverage']:.1%} {'✅' if targets['citation_coverage_target'] else '❌'} (Target: >90%)")
    print(f"   Avg Citations per Question: {qual['avg_citations_per_question']:.1f}")
    print(f"   Total Citations Generated: {qual['total_citations']}")
    
    if formal_report:
        formal = report["formal_evaluation"]
        print(f"\n🔬 FORMAL RAG METRICS:")
        print(f"   Hit Rate: {formal['hit_rate']:.1%} {'✅' if formal['hit_rate'] > 0.95 else '❌'} (Target: >95%)")
        print(f"   Citation Accuracy: {formal['citation_accuracy']:.1%} {'✅' if formal['citation_accuracy'] > 0.95 else '❌'} (Target: >95%)")
        print(f"   Faithfulness: {formal['faithfulness']:.1%}")
    
    # Overall grade
    targets_met = sum(targets.values())
    total_targets = len(targets)
    grade = "EXCELLENT" if targets_met >= total_targets * 0.8 else "GOOD" if targets_met >= total_targets * 0.6 else "NEEDS IMPROVEMENT"
    
    print(f"\n🏆 OVERALL GRADE: {grade} ({targets_met}/{total_targets} targets met)")
    
    # Sample question analysis
    print(f"\n📋 SAMPLE QUESTION ANALYSIS:")
    for i, response in enumerate(system_responses[:3]):  # Show first 3
        print(f"\n   Question {i+1}: {response['question'][:60]}...")
        print(f"   Confidence: {response['confidence']:.1%}")
        print(f"   Citations: {response['citations_count']}")
        print(f"   Processing Time: {response['processing_time']:.2f}s")
        
        # Show a snippet of system vs ground truth
        system_snippet = response['system_answer'][:100] + "..." if len(response['system_answer']) > 100 else response['system_answer']
        print(f"   System Answer: {system_snippet}")
    
    print(f"\n📄 Full detailed report saved to: {report_path}")
    print("\n" + "=" * 60)
    print("🎉 Insurance Policy Evaluation Complete!")
    
    return 0 if grade in ["EXCELLENT", "GOOD"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


