#!/usr/bin/env python3
"""
Vector Database System Integration Test
Tests complete workflow: document processing → vector ingestion → permission-filtered search
"""

import asyncio
import aiohttp
import json
import base64
from datetime import datetime
import time
import tempfile
import os

class VectorSystemIntegrationTest:
    def __init__(self):
        self.permission_service_url = "http://localhost:8005"
        self.document_service_url = "http://localhost:8004"
        self.vector_service_url = "http://localhost:8003"
        self.proxy_url = "http://localhost:8090"
        self.test_results = []
        
    async def test_permission_service(self):
        """Test permission management service"""
        print("🧪 Testing Permission Management Service...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health check
                async with session.get(f"{self.permission_service_url}/health") as response:
                    if response.status != 200:
                        self.test_results.append(("Permission Service Health", "FAIL"))
                        return False
                
                # Create test user
                user_data = {
                    "username": "test_engineer",
                    "email": "engineer@company.com",
                    "full_name": "Test Engineer",
                    "department": "engineering",
                    "clearance_level": "confidential",
                    "roles": ["employee", "engineer"],
                    "project_access": ["proj-001", "proj-002"]
                }
                
                async with session.post(
                    f"{self.permission_service_url}/api/v1/users",
                    json=user_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status in [200, 201, 400]:  # 400 if user exists
                        data = await response.text()
                        if response.status == 400 and "already exists" in data:
                            print("✅ User already exists (expected)")
                        else:
                            user_result = await response.json()
                            print(f"✅ Created user: {user_result.get('username')}")
                        
                        self.test_results.append(("Permission Service User Creation", "PASS"))
                        return True
                    else:
                        print(f"❌ User creation failed: {response.status}")
                        self.test_results.append(("Permission Service User Creation", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ Permission service test error: {e}")
            self.test_results.append(("Permission Service", "ERROR"))
            return False
    
    async def test_document_processing(self):
        """Test document processing service"""
        print("🧪 Testing Document Processing Service...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health check
                async with session.get(f"{self.document_service_url}/health") as response:
                    if response.status != 200:
                        self.test_results.append(("Document Processing Health", "FAIL"))
                        return False
                
                # Test supported formats
                async with session.get(f"{self.document_service_url}/api/v1/formats") as response:
                    if response.status == 200:
                        formats = await response.json()
                        print(f"✅ Supported formats: {len(formats['supported_formats'])} formats")
                        self.test_results.append(("Document Processing Formats", "PASS"))
                    else:
                        self.test_results.append(("Document Processing Formats", "FAIL"))
                        return False
                
                # Test chunking templates
                async with session.get(f"{self.document_service_url}/api/v1/chunking/templates") as response:
                    if response.status == 200:
                        templates = await response.json()
                        print(f"✅ Chunking templates: {len(templates['templates'])} templates")
                        self.test_results.append(("Document Processing Templates", "PASS"))
                        return True
                    else:
                        self.test_results.append(("Document Processing Templates", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ Document processing test error: {e}")
            self.test_results.append(("Document Processing", "ERROR"))
            return False
    
    async def test_vector_database(self):
        """Test vector database service"""
        print("🧪 Testing Vector Database Service...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test health check
                async with session.get(f"{self.vector_service_url}/health") as response:
                    if response.status != 200:
                        self.test_results.append(("Vector DB Health", "FAIL"))
                        return False
                
                # Test collection stats
                async with session.get(f"{self.vector_service_url}/api/v1/stats") as response:
                    if response.status == 200:
                        stats = await response.json()
                        print(f"✅ Vector DB stats: {stats['total_entities']} entities")
                        self.test_results.append(("Vector DB Stats", "PASS"))
                        return True
                    else:
                        print(f"❌ Vector DB stats failed: {response.status}")
                        self.test_results.append(("Vector DB Stats", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ Vector database test error: {e}")
            self.test_results.append(("Vector Database", "ERROR"))
            return False
    
    async def test_end_to_end_workflow(self):
        """Test complete document processing and search workflow"""
        print("🧪 Testing End-to-End Workflow...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Process a test document
                test_document = "This is a test document about machine learning algorithms. It contains information about neural networks, deep learning, and artificial intelligence applications in enterprise environments."
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(test_document)
                    temp_file_path = f.name
                
                try:
                    # Prepare permission template
                    permission_template = {
                        "template_name": "engineering_doc",
                        "access_control_list": ["test_engineer"],
                        "roles": ["employee", "engineer"],
                        "classification": "internal",
                        "department": "engineering",
                        "attributes": {"project": "ai_research"}
                    }
                    
                    # Upload document for processing
                    with open(temp_file_path, 'rb') as file_data:
                        form_data = aiohttp.FormData()
                        form_data.add_field('file', file_data, filename='test_doc.txt', content_type='text/plain')
                        form_data.add_field('permission_template', json.dumps(permission_template))
                        form_data.add_field('user_id', 'test_user')
                        
                        async with session.post(
                            f"{self.document_service_url}/api/v1/process/upload",
                            data=form_data
                        ) as response:
                            if response.status == 200:
                                processing_result = await response.json()
                                doc_id = processing_result['doc_id']
                                chunks = processing_result['chunks']
                                print(f"✅ Document processed: {doc_id}, {len(chunks)} chunks")
                                
                                # Step 2: Ingest into vector database
                                ingest_request = {
                                    "documents": [
                                        {
                                            "doc_id": doc_id,
                                            "chunk_id": chunk['chunk_id'],
                                            "text": chunk['text'],
                                            "metadata": {
                                                "filename": "test_doc.txt",
                                                "source": "test_upload",
                                                **processing_result['permission_metadata']
                                            }
                                        }
                                        for chunk in chunks[:2]  # Use first 2 chunks for testing
                                    ],
                                    "user_context": {
                                        "user_id": "test_user",
                                        "roles": ["admin"]
                                    }
                                }
                                
                                async with session.post(
                                    f"{self.vector_service_url}/api/v1/ingest",
                                    json=ingest_request,
                                    headers={"Content-Type": "application/json"}
                                ) as response:
                                    if response.status == 200:
                                        ingest_result = await response.json()
                                        print(f"✅ Vector ingestion: {ingest_result['processed_count']} documents")
                                        
                                        # Step 3: Test permission-filtered search
                                        search_request = {
                                            "query": "machine learning algorithms",
                                            "user_context": {
                                                "user_id": "test_engineer",
                                                "roles": ["employee", "engineer"],
                                                "department": "engineering",
                                                "clearance_level": "confidential"
                                            },
                                            "top_k": 5
                                        }
                                        
                                        async with session.post(
                                            f"{self.vector_service_url}/api/v1/search",
                                            json=search_request,
                                            headers={"Content-Type": "application/json"}
                                        ) as response:
                                            if response.status == 200:
                                                search_result = await response.json()
                                                print(f"✅ Permission-filtered search: {search_result['accessible_count']} accessible results")
                                                self.test_results.append(("End-to-End Workflow", "PASS"))
                                                return True
                                            else:
                                                print(f"❌ Search failed: {response.status}")
                                                self.test_results.append(("End-to-End Workflow", "FAIL"))
                                                return False
                                    else:
                                        print(f"❌ Vector ingestion failed: {response.status}")
                                        self.test_results.append(("End-to-End Workflow", "FAIL"))
                                        return False
                            else:
                                print(f"❌ Document processing failed: {response.status}")
                                self.test_results.append(("End-to-End Workflow", "FAIL"))
                                return False
                
                finally:
                    # Cleanup
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                        
        except Exception as e:
            print(f"❌ End-to-end workflow error: {e}")
            self.test_results.append(("End-to-End Workflow", "ERROR"))
            return False
    
    async def test_proxy_integration(self):
        """Test system proxy integration"""
        print("🧪 Testing System Proxy Integration...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test main system endpoint
                async with session.get(f"{self.proxy_url}/") as response:
                    if response.status == 200:
                        system_info = await response.json()
                        print(f"✅ System proxy: {system_info['service']}")
                        self.test_results.append(("Proxy Integration", "PASS"))
                        return True
                    else:
                        print(f"❌ Proxy integration failed: {response.status}")
                        self.test_results.append(("Proxy Integration", "FAIL"))
                        return False
                        
        except Exception as e:
            print(f"❌ Proxy integration test error: {e}")
            self.test_results.append(("Proxy Integration", "ERROR"))
            return False
    
    async def run_all_tests(self):
        """Run comprehensive system tests"""
        print("🚀 Starting Vector Database System Integration Tests")
        print("=" * 70)
        
        start_time = time.time()
        
        # Run tests in sequence
        await self.test_permission_service()
        print()
        
        await self.test_document_processing()
        print()
        
        await self.test_vector_database()
        print()
        
        await self.test_proxy_integration()
        print()
        
        await self.test_end_to_end_workflow()
        print()
        
        # Print results summary
        end_time = time.time()
        print("=" * 70)
        print("🏁 Test Results Summary")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, result in self.test_results if result == "PASS")
        failed_tests = sum(1 for _, result in self.test_results if result == "FAIL")
        error_tests = sum(1 for _, result in self.test_results if result == "ERROR")
        
        for test_name, result in self.test_results:
            status_emoji = "✅" if result == "PASS" else ("❌" if result == "FAIL" else "⚠️")
            print(f"{status_emoji} {test_name}: {result}")
        
        print("-" * 50)
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Errors: {error_tests}")
        print(f"⏱️ Duration: {end_time - start_time:.2f} seconds")
        
        if passed_tests == total_tests:
            print("\n🎉 All tests passed! Vector Database System is fully operational.")
            return True
        else:
            print(f"\n⚠️ {failed_tests + error_tests} test(s) failed. Check system configuration.")
            return False

async def main():
    """Main test function"""
    test_suite = VectorSystemIntegrationTest()
    success = await test_suite.run_all_tests()
    
    if success:
        print("\n📝 System Endpoints:")
        print("  🔍 Vector Search: http://localhost:8090/api/v1/search")
        print("  📄 Document Processing: http://localhost:8090/api/v1/process/upload")
        print("  🔐 Permission Management: http://localhost:8090/api/v1/permissions/evaluate")
        print("  📊 System Stats: http://localhost:8090/api/v1/stats")
        print("  🏥 Health Checks: http://localhost:8090/health")
        print("\n🚀 The Vector Database System with Enterprise Permission Management is ready!")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())