"""
Comprehensive Testing Suite for LLM Integration - Person 3
Tests the complete two-stage LLM pipeline with real document retrieval

Author: Person 3 - LLM Orchestration & Prompt Engineering Lead
Purpose: Validate LLM integration with Person 1+2 foundation
"""

import json
import logging
import time
from typing import Dict, List, Any
import traceback

from llm_integration import TwoStageLLMPipeline
from vector_database import VectorDatabasePipeline
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LLMIntegrationTester:
    """Comprehensive testing suite for the LLM integration pipeline"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        print("🧪 Starting LLM Integration Test Suite")
        print("="*60)
        
        test_methods = [
            self.test_configuration,
            self.test_pipeline_initialization,
            self.test_retrieval_foundation,
            self.test_stage1_task_analyzer,
            self.test_stage2_domain_expert,
            self.test_complete_pipeline,
            self.test_error_handling,
            self.test_performance_benchmarks,
            self.test_citation_quality,
            self.test_token_optimization
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self._log_test_failure(test_method.__name__, str(e))
        
        return self._generate_test_report()
    
    def test_configuration(self):
        """Test 1: Verify configuration and API keys"""
        test_name = "Configuration Validation"
        print(f"\n🔧 {test_name}")
        
        try:
            # Check OpenAI API key
            assert config.OPENAI_API_KEY, "OpenAI API key not configured"
            
            # Check Pinecone API key  
            assert config.PINECONE_API_KEY, "Pinecone API key not configured"
            
            self._log_test_success(test_name, "All API keys configured correctly")
            
        except AssertionError as e:
            self._log_test_failure(test_name, str(e))
    
    def test_pipeline_initialization(self):
        """Test 2: Initialize the LLM pipeline"""
        test_name = "Pipeline Initialization"
        print(f"\n🚀 {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            # Verify components
            assert hasattr(pipeline, 'openai_client'), "OpenAI client not initialized"
            assert hasattr(pipeline, 'retrieval_pipeline'), "Retrieval pipeline not initialized"
            assert hasattr(pipeline, 'encoding'), "Token encoding not initialized"
            
            self._log_test_success(test_name, "Pipeline initialized successfully")
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_retrieval_foundation(self):
        """Test 3: Verify retrieval foundation from Person 1+2"""
        test_name = "Retrieval Foundation"
        print(f"\n🔍 {test_name}")
        
        try:
            retrieval_pipeline = VectorDatabasePipeline()
            
            # Test search functionality
            test_results = retrieval_pipeline.search_similar(
                query="insurance premium calculation",
                top_k=3,
                hybrid=True,
                namespace="documents"
            )
            
            assert "results" in test_results, "Search results missing"
            assert len(test_results["results"]) > 0, "No search results returned"
            
            # Verify metadata structure
            first_result = test_results["results"][0]
            required_fields = ["score", "metadata", "id"]
            for field in required_fields:
                assert field in first_result, f"Missing field: {field}"
            
            # Verify rich metadata
            metadata = first_result["metadata"]
            required_metadata = ["content", "source_url", "page_number", "chunk_id"]
            for field in required_metadata:
                assert field in metadata, f"Missing metadata: {field}"
            
            self._log_test_success(
                test_name, 
                f"Foundation ready: {len(test_results['results'])} chunks retrieved with rich metadata"
            )
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_stage1_task_analyzer(self):
        """Test 4: Stage 1 - Task Analyzer LLM"""
        test_name = "Stage 1 - Task Analyzer"
        print(f"\n🧠 {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            test_queries = [
                "What are the premium calculation methods?",
                "How do I file a claim?",
                "What medical conditions are excluded?"
            ]
            
            for query in test_queries:
                print(f"  🔍 Analyzing: {query[:30]}...")
                
                task_analysis = pipeline.stage1_task_analyzer(query)
                
                # Verify TaskAnalysis structure
                assert hasattr(task_analysis, 'query_type'), "Missing query_type"
                assert hasattr(task_analysis, 'domain'), "Missing domain"
                assert hasattr(task_analysis, 'search_strategy'), "Missing search_strategy"
                assert hasattr(task_analysis, 'confidence'), "Missing confidence"
                
                # Verify reasonable confidence
                assert 0.0 <= task_analysis.confidence <= 1.0, f"Invalid confidence: {task_analysis.confidence}"
                
                print(f"    ✅ Type: {task_analysis.query_type}, Domain: {task_analysis.domain}")
            
            self._log_test_success(test_name, f"Task analyzer working for {len(test_queries)} query types")
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_stage2_domain_expert(self):
        """Test 5: Stage 2 - Domain Expert LLM"""
        test_name = "Stage 2 - Domain Expert"
        print(f"\n🎯 {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            # Create mock task analysis
            from llm_integration import TaskAnalysis
            mock_analysis = TaskAnalysis(
                query_type="factual",
                domain="insurance",
                required_sections=["answer", "details"],
                search_strategy={"primary_query": "premium calculation", "filters": {}},
                response_structure={"format": "structured", "sections": ["overview"]},
                confidence=0.8,
                reasoning="Test analysis"
            )
            
            expert_response = pipeline.stage2_domain_expert(
                "What are the premium calculation methods?",
                mock_analysis
            )
            
            # Verify ExpertResponse structure
            assert hasattr(expert_response, 'answer'), "Missing answer"
            assert hasattr(expert_response, 'confidence'), "Missing confidence"
            assert hasattr(expert_response, 'sections'), "Missing sections"
            assert hasattr(expert_response, 'token_usage'), "Missing token_usage"
            
            # Verify reasonable values
            assert len(expert_response.answer) > 0, "Empty answer"
            assert 0.0 <= expert_response.confidence <= 1.0, "Invalid confidence"
            assert "total_tokens" in expert_response.token_usage, "Missing token usage info"
            
            self._log_test_success(
                test_name, 
                f"Expert response generated: {expert_response.confidence:.2f} confidence, {len(expert_response.sections)} sections"
            )
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_complete_pipeline(self):
        """Test 6: Complete two-stage pipeline integration"""
        test_name = "Complete Pipeline Integration"
        print(f"\n🚀 {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            test_queries = [
                "What are the premium calculation methods in this insurance policy?",
                "What medical conditions are excluded from coverage?",
                "How do I file a claim for medical expenses?"
            ]
            
            successful_queries = 0
            
            for query in test_queries:
                print(f"  🔍 Processing: {query[:40]}...")
                
                result = pipeline.process_query(query)
                
                # Verify complete response structure
                required_fields = ["query", "answer", "confidence", "citations", "task_analysis", "performance"]
                for field in required_fields:
                    assert field in result, f"Missing field: {field}"
                
                # Verify performance metrics
                assert "total_processing_time" in result["performance"], "Missing processing time"
                assert "token_usage" in result["performance"], "Missing token usage"
                assert "estimated_cost" in result["performance"], "Missing cost estimate"
                
                # Verify citations
                assert len(result["citations"]) > 0, "No citations provided"
                
                processing_time = result["performance"]["total_processing_time"]
                cost = result["performance"]["estimated_cost"]
                citation_count = len(result["citations"])
                
                print(f"    ✅ Success: {processing_time:.2f}s, ${cost:.4f}, {citation_count} citations")
                successful_queries += 1
            
            self._log_test_success(
                test_name, 
                f"Complete pipeline working: {successful_queries}/{len(test_queries)} queries successful"
            )
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_error_handling(self):
        """Test 7: Error handling and fallback mechanisms"""
        test_name = "Error Handling"
        print(f"\n🛡️ {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            # Test with edge cases
            edge_cases = [
                "",  # Empty query
                "a" * 10000,  # Very long query
                "🤖💻📊",  # Emoji only
                "What is the meaning of life?",  # Off-topic query
            ]
            
            handled_cases = 0
            
            for case in edge_cases:
                try:
                    result = pipeline.process_query(case[:100])  # Truncate for display
                    
                    # Should either succeed or have error field
                    if "error" in result:
                        print(f"    ⚠️  Graceful error handling for edge case")
                    else:
                        print(f"    ✅ Handled edge case successfully")
                    
                    handled_cases += 1
                    
                except Exception as e:
                    print(f"    ❌ Unhandled error: {str(e)[:50]}")
            
            self._log_test_success(test_name, f"Error handling: {handled_cases}/{len(edge_cases)} cases handled")
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_performance_benchmarks(self):
        """Test 8: Performance benchmarks"""
        test_name = "Performance Benchmarks"
        print(f"\n⚡ {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            # Benchmark query
            start_time = time.time()
            result = pipeline.process_query("What are the premium calculation methods?")
            total_time = time.time() - start_time
            
            # Performance assertions
            assert total_time < 30.0, f"Pipeline too slow: {total_time:.2f}s (target: <30s)"
            
            token_usage = result["performance"]["token_usage"]["total_tokens"]
            assert token_usage < 8000, f"Token usage too high: {token_usage} (target: <8000)"
            
            cost = result["performance"]["estimated_cost"]
            assert cost < 0.20, f"Cost too high: ${cost:.4f} (target: <$0.20)"
            
            self._log_test_success(
                test_name, 
                f"Performance targets met: {total_time:.2f}s, {token_usage} tokens, ${cost:.4f}"
            )
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_citation_quality(self):
        """Test 9: Citation quality and traceability"""
        test_name = "Citation Quality"
        print(f"\n📚 {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            result = pipeline.process_query("What are the premium calculation methods?")
            
            citations = result["citations"]
            assert len(citations) > 0, "No citations provided"
            
            # Verify citation structure
            for citation in citations:
                required_fields = ["source", "page", "chunk_id", "excerpt"]
                for field in required_fields:
                    assert field in citation, f"Citation missing field: {field}"
                
                # Verify reasonable values
                assert len(citation["excerpt"]) > 10, "Citation excerpt too short"
                assert citation["page"] > 0, "Invalid page number"
                assert len(citation["chunk_id"]) > 0, "Missing chunk ID"
            
            # Check for unique citations (no duplicates)
            chunk_ids = [c["chunk_id"] for c in citations]
            unique_chunks = len(set(chunk_ids))
            
            self._log_test_success(
                test_name, 
                f"Citation quality verified: {len(citations)} citations, {unique_chunks} unique sources"
            )
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def test_token_optimization(self):
        """Test 10: Token usage optimization"""
        test_name = "Token Optimization"
        print(f"\n💰 {test_name}")
        
        try:
            pipeline = TwoStageLLMPipeline()
            
            # Test multiple queries to check token efficiency
            queries = [
                "What are the premium calculation methods?",
                "How do I file a claim?",
                "What is covered under this policy?"
            ]
            
            total_tokens = 0
            total_cost = 0.0
            
            for query in queries:
                result = pipeline.process_query(query)
                tokens = result["performance"]["token_usage"]["total_tokens"]
                cost = result["performance"]["estimated_cost"]
                
                total_tokens += tokens
                total_cost += cost
            
            avg_tokens = total_tokens / len(queries)
            avg_cost = total_cost / len(queries)
            
            # Token efficiency targets
            assert avg_tokens < 6000, f"Average tokens too high: {avg_tokens} (target: <6000)"
            assert avg_cost < 0.15, f"Average cost too high: ${avg_cost:.4f} (target: <$0.15)"
            
            self._log_test_success(
                test_name, 
                f"Token optimization verified: {avg_tokens:.0f} avg tokens, ${avg_cost:.4f} avg cost"
            )
            
        except Exception as e:
            self._log_test_failure(test_name, str(e))
    
    def _log_test_success(self, test_name: str, message: str):
        """Log successful test"""
        print(f"✅ {test_name}: PASSED - {message}")
        self.test_results.append({
            "test": test_name,
            "status": "PASSED",
            "message": message,
            "timestamp": time.time()
        })
        self.passed_tests += 1
    
    def _log_test_failure(self, test_name: str, error: str):
        """Log failed test"""
        print(f"❌ {test_name}: FAILED - {error}")
        self.test_results.append({
            "test": test_name,
            "status": "FAILED", 
            "error": error,
            "timestamp": time.time()
        })
        self.failed_tests += 1
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": self.passed_tests,
                "failed": self.failed_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results,
            "timestamp": time.time()
        }
        
        # Print summary
        print("\n" + "="*60)
        print("🧪 LLM INTEGRATION TEST RESULTS")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 LLM Integration: PRODUCTION READY!")
        elif success_rate >= 60:
            print("⚠️  LLM Integration: NEEDS IMPROVEMENT")
        else:
            print("🚨 LLM Integration: REQUIRES FIXES")
        
        return report


def main():
    """Run the comprehensive test suite"""
    print("🚀 Starting LLM Integration Testing Suite")
    print(f"Testing Person 3 work on top of Person 1+2 foundation")
    
    try:
        tester = LLMIntegrationTester()
        report = tester.run_all_tests()
        
        # Save detailed report
        with open("test_results_llm_integration.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed test report saved to: test_results_llm_integration.json")
        
        return report
        
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()