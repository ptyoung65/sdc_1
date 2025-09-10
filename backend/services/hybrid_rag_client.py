"""
Hybrid RAG Client
Vector RAG + Graph RAG 하이브리드 검색 클라이언트
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class HybridRAGClient:
    """Vector RAG + Graph RAG 하이브리드 클라이언트"""
    
    def __init__(self, 
                 vector_rag_url: str = "http://localhost:8009",
                 graph_rag_url: str = "http://localhost:8010"):
        """
        하이브리드 RAG 클라이언트 초기화
        
        Args:
            vector_rag_url: 벡터 RAG 서비스 URL
            graph_rag_url: 그래프 RAG 서비스 URL
        """
        self.vector_rag_url = vector_rag_url
        self.graph_rag_url = graph_rag_url
        
        logger.info(f"Hybrid RAG Client 초기화 완료")
        logger.info(f"Vector RAG URL: {vector_rag_url}")
        logger.info(f"Graph RAG URL: {graph_rag_url}")
    
    async def add_document_to_both(self, 
                                   title: str, 
                                   content: str, 
                                   metadata: Dict[str, Any] = None,
                                   document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        벡터 RAG와 그래프 RAG 모두에 문서 추가
        
        Args:
            title: 문서 제목
            content: 문서 내용
            metadata: 메타데이터
            document_id: 문서 ID
            
        Returns:
            통합 결과
        """
        try:
            document_data = {
                "title": title,
                "content": content,
                "metadata": metadata or {},
                "document_id": document_id
            }
            
            # 동시에 두 서비스에 문서 추가
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Vector RAG에 문서 추가
                vector_task = client.post(
                    f"{self.vector_rag_url}/documents",
                    json=document_data
                )
                
                # Graph RAG에 문서 추가
                graph_task = client.post(
                    f"{self.graph_rag_url}/graph/build",
                    json=document_data
                )
                
                # 동시 실행
                vector_response, graph_response = await asyncio.gather(
                    vector_task, graph_task, return_exceptions=True
                )
            
            result = {
                "status": "success",
                "document_id": document_id,
                "vector_rag_result": None,
                "graph_rag_result": None,
                "timestamp": datetime.now().isoformat()
            }
            
            # Vector RAG 결과 처리
            if isinstance(vector_response, Exception):
                logger.error(f"Vector RAG 문서 추가 실패: {vector_response}")
                result["vector_rag_result"] = {"status": "error", "message": str(vector_response)}
            elif vector_response.status_code == 200:
                vector_data = vector_response.json()
                result["vector_rag_result"] = vector_data
                logger.info("Vector RAG 문서 추가 성공")
            else:
                error_msg = f"Vector RAG HTTP {vector_response.status_code}"
                result["vector_rag_result"] = {"status": "error", "message": error_msg}
                logger.warning(error_msg)
            
            # Graph RAG 결과 처리
            if isinstance(graph_response, Exception):
                logger.error(f"Graph RAG 문서 추가 실패: {graph_response}")
                result["graph_rag_result"] = {"status": "error", "message": str(graph_response)}
            elif graph_response.status_code == 200:
                graph_data = graph_response.json()
                result["graph_rag_result"] = graph_data
                logger.info("Graph RAG 문서 추가 성공")
            else:
                error_msg = f"Graph RAG HTTP {graph_response.status_code}"
                result["graph_rag_result"] = {"status": "error", "message": error_msg}
                logger.warning(error_msg)
            
            # 전체 성공 여부 판단
            vector_success = result["vector_rag_result"] and result["vector_rag_result"].get("success", False)
            graph_success = result["graph_rag_result"] and result["graph_rag_result"].get("success", False)
            
            if not vector_success and not graph_success:
                result["status"] = "error"
                result["message"] = "Vector RAG와 Graph RAG 모두 문서 추가 실패"
            elif not vector_success:
                result["status"] = "partial_success"
                result["message"] = "Graph RAG만 성공, Vector RAG 실패"
            elif not graph_success:
                result["status"] = "partial_success"
                result["message"] = "Vector RAG만 성공, Graph RAG 실패"
            else:
                result["message"] = "Vector RAG와 Graph RAG 모두 성공"
            
            return result
            
        except Exception as e:
            logger.error(f"하이브리드 문서 추가 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def hybrid_search(self, 
                          query: str,
                          use_vector: bool = True,
                          use_graph: bool = True,
                          max_hops: int = 2,
                          max_results: int = 10) -> Dict[str, Any]:
        """
        하이브리드 검색 수행
        
        Args:
            query: 검색 쿼리
            use_vector: 벡터 검색 사용 여부
            use_graph: 그래프 검색 사용 여부
            max_hops: 그래프 탐색 최대 깊이
            max_results: 최대 결과 수
            
        Returns:
            통합 검색 결과
        """
        try:
            tasks = []
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Vector RAG 검색
                if use_vector:
                    vector_task = client.post(
                        f"{self.vector_rag_url}/search",
                        json={"query": query}
                    )
                    tasks.append(("vector", vector_task))
                
                # Graph RAG 검색
                if use_graph:
                    graph_task = client.post(
                        f"{self.graph_rag_url}/graph/query",
                        json={
                            "query": query,
                            "max_hops": max_hops,
                            "max_results": max_results
                        }
                    )
                    tasks.append(("graph", graph_task))
                
                # 동시 실행
                if not tasks:
                    return {
                        "status": "error",
                        "message": "Vector 또는 Graph 검색 중 하나는 활성화되어야 합니다"
                    }
                
                responses = await asyncio.gather(
                    *[task for _, task in tasks], 
                    return_exceptions=True
                )
            
            result = {
                "status": "success",
                "query": query,
                "vector_results": None,
                "graph_results": None,
                "hybrid_context": "",
                "hybrid_prompt": "",
                "timestamp": datetime.now().isoformat()
            }
            
            # 응답 처리
            for i, (search_type, _) in enumerate(tasks):
                response = responses[i]
                
                if isinstance(response, Exception):
                    logger.error(f"{search_type.title()} RAG 검색 실패: {response}")
                    result[f"{search_type}_results"] = {"status": "error", "message": str(response)}
                elif response.status_code == 200:
                    data = response.json()
                    result[f"{search_type}_results"] = data
                    logger.info(f"{search_type.title()} RAG 검색 성공")
                else:
                    error_msg = f"{search_type.title()} RAG HTTP {response.status_code}"
                    result[f"{search_type}_results"] = {"status": "error", "message": error_msg}
                    logger.warning(error_msg)
            
            # 하이브리드 컨텍스트 생성
            context_parts = []
            
            # Vector RAG 컨텍스트 추가
            if (result["vector_results"] and 
                result["vector_results"].get("success") and 
                result["vector_results"]["data"].get("context")):
                
                vector_context = result["vector_results"]["data"]["context"]
                context_parts.append(f"=== 벡터 검색 결과 ===\n{vector_context}")
            
            # Graph RAG 컨텍스트 추가
            if (result["graph_results"] and 
                result["graph_results"].get("success") and 
                result["graph_results"]["data"].get("graph_context")):
                
                graph_context = result["graph_results"]["data"]["graph_context"]
                context_parts.append(f"=== 지식 그래프 검색 결과 ===\n{graph_context}")
            
            result["hybrid_context"] = "\n\n".join(context_parts)
            
            # 하이브리드 프롬프트 생성
            if result["hybrid_context"]:
                result["hybrid_prompt"] = self._generate_hybrid_prompt(query, result["hybrid_context"])
            
            # 검색 품질 평가
            result["search_quality"] = self._evaluate_search_quality(result)
            
            return result
            
        except Exception as e:
            logger.error(f"하이브리드 검색 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_hybrid_prompt(self, query: str, context: str) -> str:
        """하이브리드 RAG 프롬프트 생성"""
        return f"""다음 정보들을 종합하여 질문에 답변해주세요.

{context}

=== 질문 ===
{query}

=== 답변 지침 ===
1. 벡터 검색과 지식 그래프 결과를 모두 활용하여 종합적으로 답변하세요
2. 정확한 정보만 사용하고 추측하지 마세요
3. 한국어로 자연스럽게 답변하세요
4. 가능하면 정보의 출처를 언급하세요
5. 벡터 검색과 그래프 검색 결과가 상충할 경우, 더 신뢰할 수 있는 정보를 우선하세요

답변:"""
    
    def _evaluate_search_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """검색 품질 평가"""
        quality = {
            "vector_available": bool(result.get("vector_results", {}).get("success")),
            "graph_available": bool(result.get("graph_results", {}).get("success")),
            "context_length": len(result.get("hybrid_context", "")),
            "search_completeness": 0.0
        }
        
        # 완성도 계산
        if quality["vector_available"] and quality["graph_available"]:
            quality["search_completeness"] = 1.0  # 완전한 하이브리드
        elif quality["vector_available"] or quality["graph_available"]:
            quality["search_completeness"] = 0.5  # 부분적 검색
        else:
            quality["search_completeness"] = 0.0  # 검색 실패
        
        # 컨텍스트 품질 평가
        if quality["context_length"] > 500:
            quality["context_richness"] = "high"
        elif quality["context_length"] > 100:
            quality["context_richness"] = "medium"
        else:
            quality["context_richness"] = "low"
        
        return quality
    
    async def delete_document_from_both(self, document_id: str) -> Dict[str, Any]:
        """양쪽 서비스에서 문서 삭제"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 동시에 두 서비스에서 문서 삭제
                vector_task = client.delete(f"{self.vector_rag_url}/documents/{document_id}")
                graph_task = client.delete(f"{self.graph_rag_url}/graph/documents/{document_id}")
                
                vector_response, graph_response = await asyncio.gather(
                    vector_task, graph_task, return_exceptions=True
                )
            
            result = {
                "status": "success",
                "document_id": document_id,
                "vector_deleted": False,
                "graph_deleted": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # Vector RAG 삭제 결과
            if not isinstance(vector_response, Exception) and vector_response.status_code == 200:
                result["vector_deleted"] = True
            
            # Graph RAG 삭제 결과
            if not isinstance(graph_response, Exception) and graph_response.status_code == 200:
                result["graph_deleted"] = True
            
            if result["vector_deleted"] and result["graph_deleted"]:
                result["message"] = "양쪽 서비스에서 문서 삭제 성공"
            elif result["vector_deleted"]:
                result["message"] = "Vector RAG에서만 삭제 성공"
            elif result["graph_deleted"]:
                result["message"] = "Graph RAG에서만 삭제 성공"
            else:
                result["status"] = "error"
                result["message"] = "양쪽 서비스에서 모두 삭제 실패"
            
            return result
            
        except Exception as e:
            logger.error(f"하이브리드 문서 삭제 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_service_status(self) -> Dict[str, Any]:
        """양쪽 서비스 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                vector_task = client.get(f"{self.vector_rag_url}/health")
                graph_task = client.get(f"{self.graph_rag_url}/health")
                
                vector_response, graph_response = await asyncio.gather(
                    vector_task, graph_task, return_exceptions=True
                )
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "vector_rag_status": "healthy" if (
                    not isinstance(vector_response, Exception) and 
                    vector_response.status_code == 200
                ) else "unhealthy",
                "graph_rag_status": "healthy" if (
                    not isinstance(graph_response, Exception) and 
                    graph_response.status_code == 200
                ) else "unhealthy"
            }
            
            status["overall_status"] = "healthy" if (
                status["vector_rag_status"] == "healthy" and 
                status["graph_rag_status"] == "healthy"
            ) else "degraded"
            
            return status
            
        except Exception as e:
            logger.error(f"서비스 상태 확인 중 오류: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 전역 하이브리드 RAG 클라이언트 인스턴스
_hybrid_rag_client = None

def get_hybrid_rag_client() -> HybridRAGClient:
    """하이브리드 RAG 클라이언트 인스턴스 반환"""
    global _hybrid_rag_client
    if _hybrid_rag_client is None:
        _hybrid_rag_client = HybridRAGClient()
    return _hybrid_rag_client


if __name__ == "__main__":
    import asyncio
    
    async def test_hybrid_rag():
        client = HybridRAGClient()
        
        # 서비스 상태 확인
        status = await client.get_service_status()
        print("=== 서비스 상태 ===")
        print(f"전체 상태: {status['overall_status']}")
        print(f"Vector RAG: {status['vector_rag_status']}")
        print(f"Graph RAG: {status['graph_rag_status']}")
        
        # 테스트 문서 추가
        test_doc = {
            "title": "하이브리드 RAG 테스트",
            "content": """
            하이브리드 RAG는 벡터 검색과 지식 그래프 검색을 결합한 시스템입니다.
            벡터 검색은 의미적 유사성을 기반으로 검색하고, 지식 그래프는 개체 간의 관계를 활용합니다.
            이 두 방식을 결합하면 더 정확하고 풍부한 검색 결과를 얻을 수 있습니다.
            """,
            "metadata": {"source": "test", "category": "hybrid_rag"}
        }
        
        print("\n=== 문서 추가 테스트 ===")
        add_result = await client.add_document_to_both(**test_doc)
        print(f"추가 결과: {add_result['status']}")
        print(f"메시지: {add_result.get('message', '')}")
        
        # 하이브리드 검색 테스트
        print("\n=== 하이브리드 검색 테스트 ===")
        search_result = await client.hybrid_search("하이브리드 RAG가 무엇인가요?")
        print(f"검색 상태: {search_result['status']}")
        print(f"검색 품질: {search_result.get('search_quality', {})}")
        
        if search_result.get('hybrid_context'):
            print(f"컨텍스트 길이: {len(search_result['hybrid_context'])}자")
            print(f"컨텍스트 미리보기: {search_result['hybrid_context'][:200]}...")
    
    asyncio.run(test_hybrid_rag())