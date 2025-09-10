#!/usr/bin/env python3
"""
RAG Evaluation System Integration Test
Tests the complete RAG evaluation integration with the main backend API
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import time

class RAGEvaluationIntegrationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.rag_evaluator_url = "http://localhost:8002"
        self.rag_dashboard_url = "http://localhost:3002"
        self.test_results = []
        
    async def test_backend_integration(self):
        """Test RAG evaluation through main backend API"""
        print("🧪 Testing Backend RAG Integration...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test chat with RAG enabled
                chat_payload = {
                    "message": "What is machine learning?",
                    "provider": "gemini",
                    "use_rag": True,
                    "user_id": "integration_test_user",
                    "conversation_id": f"test-conv-{int(time.time())}"
                }
                
                print(f"📝 Sending chat request: {chat_payload['message']}")
                
                async with session.post(
                    f"{self.backend_url}/api/v1/chat",
                    json=chat_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Chat Response Success: {data['success']}")
                        print(f"📄 Response Length: {len(data.get('response', ''))}")
                        print(f"🔍 Sources: {len(data.get('sources', []))} sources")
                        self.test_results.append(("Backend RAG Integration", "PASS"))
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Chat Request Failed: {response.status} - {error_text}")
                        self.test_results.append(("Backend RAG Integration", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ Backend Integration Test Error: {e}")
            self.test_results.append(("Backend RAG Integration", "ERROR"))
            return False
    
    async def test_rag_evaluator_direct(self):
        """Test RAG evaluator service directly"""
        print("🧪 Testing RAG Evaluator Service...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.rag_evaluator_url}/health") as response:
                    if response.status != 200:
                        print(f"❌ RAG Evaluator Health Check Failed: {response.status}")
                        self.test_results.append(("RAG Evaluator Health", "FAIL"))
                        return False
                
                print("✅ RAG Evaluator Health Check Passed")
                
                # Test evaluation endpoint
                evaluation_payload = {
                    "session_id": f"direct-test-{int(time.time())}",
                    "query": "Test query for direct evaluation",
                    "retrieval_stage": {
                        "stage": "retrieval",
                        "start_time": time.time(),
                        "end_time": time.time() + 0.5,
                        "latency_ms": 500,
                        "retrieved_chunks": [
                            {"content": "Test chunk 1", "score": 0.8},
                            {"content": "Test chunk 2", "score": 0.7}
                        ],
                        "num_chunks": 2
                    },
                    "generation_stage": {
                        "stage": "generation",
                        "start_time": time.time() + 0.5,
                        "end_time": time.time() + 2.0,
                        "latency_ms": 1500,
                        "llm_response": "This is a test response for direct evaluation.",
                        "model_name": "test-model"
                    },
                    "user_id": "direct_test_user"
                }
                
                async with session.post(
                    f"{self.rag_evaluator_url}/api/v1/rag/evaluate",
                    json=evaluation_payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Direct Evaluation Success")
                        print(f"📊 Context Relevance: {data.get('context_relevance', 'N/A')}")
                        print(f"📊 Answer Relevance: {data.get('answer_relevance', 'N/A')}")
                        print(f"📊 Overall Quality: {data.get('overall_quality_score', 'N/A')}")
                        self.test_results.append(("RAG Evaluator Direct", "PASS"))
                        return True
                    else:
                        error_text = await response.text()
                        print(f"❌ Direct Evaluation Failed: {response.status} - {error_text}")
                        self.test_results.append(("RAG Evaluator Direct", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ RAG Evaluator Direct Test Error: {e}")
            self.test_results.append(("RAG Evaluator Direct", "ERROR"))
            return False
    
    async def test_rag_dashboard(self):
        """Test RAG dashboard accessibility"""
        print("🧪 Testing RAG Dashboard...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.rag_dashboard_url}") as response:
                    if response.status == 200:
                        print("✅ RAG Dashboard Accessible")
                        self.test_results.append(("RAG Dashboard Access", "PASS"))
                        return True
                    else:
                        print(f"❌ RAG Dashboard Not Accessible: {response.status}")
                        self.test_results.append(("RAG Dashboard Access", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ RAG Dashboard Test Error: {e}")
            self.test_results.append(("RAG Dashboard Access", "ERROR"))
            return False
    
    async def test_backend_health(self):
        """Test main backend health"""
        print("🧪 Testing Main Backend Health...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Backend Health: {data.get('status', 'unknown')}")
                        self.test_results.append(("Backend Health", "PASS"))
                        return True
                    else:
                        print(f"❌ Backend Health Check Failed: {response.status}")
                        self.test_results.append(("Backend Health", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ Backend Health Test Error: {e}")
            self.test_results.append(("Backend Health", "ERROR"))
            return False
    
    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting RAG Evaluation System Integration Tests")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run tests in sequence
        await self.test_backend_health()
        print()
        
        await self.test_rag_evaluator_direct()
        print()
        
        await self.test_rag_dashboard()
        print()
        
        await self.test_backend_integration()
        print()
        
        # Print results summary
        end_time = time.time()
        print("=" * 60)
        print("🏁 Test Results Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result in self.test_results if result == "PASS")
        failed_tests = sum(1 for _, result in self.test_results if result == "FAIL")
        error_tests = sum(1 for _, result in self.test_results if result == "ERROR")
        
        for test_name, result in self.test_results:
            status_emoji = "✅" if result == "PASS" else ("❌" if result == "FAIL" else "⚠️")
            print(f"{status_emoji} {test_name}: {result}")
        
        print("-" * 40)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        print(f"⏱️ Duration: {end_time - start_time:.2f} seconds")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! RAG Evaluation System is working correctly.")
            return True
        else:
            print(f"\n⚠️ {failed_tests + error_tests} test(s) failed. Check the system configuration.")
            return False

async def main():
    """Main test function"""
    test_suite = RAGEvaluationIntegrationTest()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n📝 Next Steps:")
        print("  1. Access RAG Dashboard: http://localhost:3002")
        print("  2. Test chat with RAG in main application")
        print("  3. Monitor evaluation metrics in real-time")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())