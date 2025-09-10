"""
Triple RAG Client
Vector RAG + Graph RAG + Keyword RAG 트리플 검색 클라이언트
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class TripleRAGClient:
    """Vector RAG + Graph RAG + Keyword RAG 트리플 클라이언트"""
    
    def __init__(self, 
                 vector_rag_url: str = "http://localhost:8009",
                 graph_rag_url: str = "http://localhost:8010",
                 keyword_rag_url: str = "http://localhost:8011"):
        """
        트리플 RAG 클라이언트 초기화
        
        Args:
            vector_rag_url: 벡터 RAG 서비스 URL
            graph_rag_url: 그래프 RAG 서비스 URL
            keyword_rag_url: 키워드 RAG 서비스 URL
        """
        self.vector_rag_url = vector_rag_url
        self.graph_rag_url = graph_rag_url
        self.keyword_rag_url = keyword_rag_url
        
        logger.info(f"Triple RAG Client 초기화 완료")
        logger.info(f"Vector RAG URL: {vector_rag_url}")
        logger.info(f"Graph RAG URL: {graph_rag_url}")
        logger.info(f"Keyword RAG URL: {keyword_rag_url}")
    
    async def add_document_to_all(self, 
                                  title: str, 
                                  content: str, 
                                  metadata: Dict[str, Any] = None,
                                  document_id: Optional[str] = None) -> Dict[str, Any]:
        """
        세 RAG 시스템 모두에 문서 추가
        
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
            
            # 동시에 세 서비스에 문서 추가
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
                
                # Keyword RAG에 문서 추가
                keyword_task = client.post(
                    f"{self.keyword_rag_url}/keyword/index",
                    json=document_data
                )
                
                # 동시 실행
                vector_response, graph_response, keyword_response = await asyncio.gather(
                    vector_task, graph_task, keyword_task, return_exceptions=True
                )
            
            result = {
                "status": "success",
                "document_id": document_id,
                "vector_rag_result": None,
                "graph_rag_result": None,
                "keyword_rag_result": None,
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
            
            # Keyword RAG 결과 처리
            if isinstance(keyword_response, Exception):
                logger.error(f"Keyword RAG 문서 추가 실패: {keyword_response}")
                result["keyword_rag_result"] = {"status": "error", "message": str(keyword_response)}
            elif keyword_response.status_code == 200:
                keyword_data = keyword_response.json()
                result["keyword_rag_result"] = keyword_data
                logger.info("Keyword RAG 문서 추가 성공")
            else:
                error_msg = f"Keyword RAG HTTP {keyword_response.status_code}"
                result["keyword_rag_result"] = {"status": "error", "message": error_msg}
                logger.warning(error_msg)
            
            # 전체 성공 여부 판단
            vector_success = result["vector_rag_result"] and result["vector_rag_result"].get("success", False)
            graph_success = result["graph_rag_result"] and result["graph_rag_result"].get("success", False)
            keyword_success = result["keyword_rag_result"] and result["keyword_rag_result"].get("success", False)
            
            success_count = sum([vector_success, graph_success, keyword_success])
            
            if success_count == 0:
                result["status"] = "error"
                result["message"] = "모든 RAG 시스템에서 문서 추가 실패"
            elif success_count == 3:
                result["message"] = "모든 RAG 시스템에서 문서 추가 성공"
            else:
                result["status"] = "partial_success"
                result["message"] = f"3개 중 {success_count}개 RAG 시스템에서 성공"
            
            return result
            
        except Exception as e:
            logger.error(f"트리플 문서 추가 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def triple_search(self, 
                           query: str,
                           use_vector: bool = True,
                           use_graph: bool = True,
                           use_keyword: bool = True,
                           max_hops: int = 2,
                           max_results: int = 10,
                           min_score: float = 1.0) -> Dict[str, Any]:
        """
        트리플 검색 수행
        
        Args:
            query: 검색 쿼리
            use_vector: 벡터 검색 사용 여부
            use_graph: 그래프 검색 사용 여부
            use_keyword: 키워드 검색 사용 여부
            max_hops: 그래프 탐색 최대 깊이
            max_results: 최대 결과 수
            min_score: 최소 관련도 점수
            
        Returns:
            통합 검색 결과
        """
        try:
            results = {
                "query": query,
                "vector_results": None,
                "graph_results": None,
                "keyword_results": None,
                "triple_context": "",
                "timestamp": datetime.now().isoformat()
            }
            
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
                
                # Keyword RAG 검색
                if use_keyword:
                    keyword_task = client.post(
                        f"{self.keyword_rag_url}/keyword/search",
                        json={
                            "query": query,
                            "max_results": max_results,
                            "min_score": min_score
                        }
                    )
                    tasks.append(("keyword", keyword_task))
                
                # 동시 실행
                if not tasks:
                    return {
                        "status": "error",
                        "message": "최소 하나의 검색 방법은 활성화되어야 합니다"
                    }
                
                responses = await asyncio.gather(
                    *[task for _, task in tasks], 
                    return_exceptions=True
                )
            
            # 응답 처리
            for i, (search_type, _) in enumerate(tasks):
                response = responses[i]
                
                if isinstance(response, Exception):
                    logger.error(f"{search_type.title()} RAG 검색 실패: {response}")
                    results[f"{search_type}_results"] = {"status": "error", "message": str(response)}
                elif response.status_code == 200:
                    data = response.json()
                    results[f"{search_type}_results"] = data
                    logger.info(f"{search_type.title()} RAG 검색 성공")
                else:
                    error_msg = f"{search_type.title()} RAG HTTP {response.status_code}"
                    results[f"{search_type}_results"] = {"status": "error", "message": error_msg}
                    logger.warning(error_msg)
            
            # 트리플 컨텍스트 생성
            context_parts = []
            
            # Vector RAG 컨텍스트 추가
            if (results["vector_results"] and 
                results["vector_results"].get("success") and 
                results["vector_results"]["data"].get("context")):
                
                vector_context = results["vector_results"]["data"]["context"]
                context_parts.append(f"=== 벡터 검색 결과 ===\n{vector_context}")
            
            # Graph RAG 컨텍스트 추가
            if (results["graph_results"] and 
                results["graph_results"].get("success") and 
                results["graph_results"]["data"].get("graph_context")):
                
                graph_context = results["graph_results"]["data"]["graph_context"]
                context_parts.append(f"=== 지식 그래프 검색 결과 ===\n{graph_context}")
            
            # Keyword RAG 컨텍스트 추가
            if (results["keyword_results"] and 
                results["keyword_results"].get("success") and 
                results["keyword_results"]["data"].get("keyword_context")):
                
                keyword_context = results["keyword_results"]["data"]["keyword_context"]
                context_parts.append(f"=== 키워드 검색 결과 ===\n{keyword_context}")
            
            results["triple_context"] = "\n\n".join(context_parts)
            
            # 트리플 프롬프트 생성
            if results["triple_context"]:
                results["triple_prompt"] = self._generate_triple_prompt(query, results["triple_context"])
            
            # 검색 품질 평가
            results["search_quality"] = self._evaluate_triple_search_quality(results)
            
            return results
            
        except Exception as e:
            logger.error(f"트리플 검색 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_triple_prompt(self, query: str, context: str) -> str:
        """트리플 RAG 프롬프트 생성"""
        return f"""다음 세 가지 검색 방법의 결과를 종합하여 질문에 답변해주세요.

{context}

=== 질문 ===
{query}

=== 답변 지침 ===
1. 벡터 검색(의미적 유사도), 지식 그래프(개체 관계), 키워드 검색(정확 매칭) 결과를 모두 활용하세요
2. 각 검색 방법의 장점을 활용해 완전하고 정확한 답변을 제공하세요
3. 정확한 정보만 사용하고 추측하지 마세요
4. 한국어로 자연스럽게 답변하세요
5. 가능하면 정보의 출처와 검색 방법을 언급하세요
6. 서로 다른 검색 결과가 상충할 경우, 더 신뢰할 수 있는 정보를 우선하세요
7. 세 검색 방법의 결과를 종합해 가장 완성도 높은 답변을 제공하세요

답변:"""
    
    def _evaluate_triple_search_quality(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """트리플 검색 품질 평가"""
        quality = {
            "vector_available": bool(results.get("vector_results", {}).get("success")),
            "graph_available": bool(results.get("graph_results", {}).get("success")),
            "keyword_available": bool(results.get("keyword_results", {}).get("success")),
            "context_length": len(results.get("triple_context", "")),
            "search_completeness": 0.0,
            "method_diversity": 0.0
        }
        
        # 완성도 계산 (3가지 검색 방법)
        available_methods = sum([
            quality["vector_available"],
            quality["graph_available"], 
            quality["keyword_available"]
        ])
        
        quality["search_completeness"] = available_methods / 3.0
        
        # 방법론 다양성 점수 (각각 다른 방식의 검색)
        quality["method_diversity"] = quality["search_completeness"]
        
        # 컨텍스트 품질 평가
        context_length = quality["context_length"]
        if context_length > 1500:
            quality["context_richness"] = "excellent"
        elif context_length > 1000:
            quality["context_richness"] = "very_high"
        elif context_length > 500:
            quality["context_richness"] = "high"
        elif context_length > 200:
            quality["context_richness"] = "medium"
        elif context_length > 0:
            quality["context_richness"] = "low"
        else:
            quality["context_richness"] = "none"
        
        # 전체 품질 점수 계산
        quality["overall_quality"] = (
            quality["search_completeness"] * 0.4 +
            quality["method_diversity"] * 0.3 +
            min(context_length / 1000, 1.0) * 0.3
        )
        
        return quality
    
    async def delete_document_from_all(self, document_id: str) -> Dict[str, Any]:
        """모든 RAG 시스템에서 문서 삭제"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 동시에 세 서비스에서 문서 삭제
                vector_task = client.delete(f"{self.vector_rag_url}/documents/{document_id}")
                graph_task = client.delete(f"{self.graph_rag_url}/graph/documents/{document_id}")
                keyword_task = client.delete(f"{self.keyword_rag_url}/keyword/documents/{document_id}")
                
                vector_response, graph_response, keyword_response = await asyncio.gather(
                    vector_task, graph_task, keyword_task, return_exceptions=True
                )
            
            result = {
                "status": "success",
                "document_id": document_id,
                "vector_deleted": False,
                "graph_deleted": False,
                "keyword_deleted": False,
                "timestamp": datetime.now().isoformat()
            }
            
            # 삭제 결과 확인
            if not isinstance(vector_response, Exception) and vector_response.status_code == 200:
                result["vector_deleted"] = True
            
            if not isinstance(graph_response, Exception) and graph_response.status_code == 200:
                result["graph_deleted"] = True
                
            if not isinstance(keyword_response, Exception) and keyword_response.status_code == 200:
                result["keyword_deleted"] = True
            
            deleted_count = sum([
                result["vector_deleted"],
                result["graph_deleted"],
                result["keyword_deleted"]
            ])
            
            if deleted_count == 3:
                result["message"] = "모든 RAG 시스템에서 문서 삭제 성공"
            elif deleted_count > 0:
                result["message"] = f"3개 중 {deleted_count}개 시스템에서 삭제 성공"
            else:
                result["status"] = "error"
                result["message"] = "모든 RAG 시스템에서 삭제 실패"
            
            return result
            
        except Exception as e:
            logger.error(f"트리플 문서 삭제 중 오류: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_all_service_status(self) -> Dict[str, Any]:
        """모든 RAG 서비스 상태 확인"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                vector_task = client.get(f"{self.vector_rag_url}/health")
                graph_task = client.get(f"{self.graph_rag_url}/health")
                keyword_task = client.get(f"{self.keyword_rag_url}/health")
                
                vector_response, graph_response, keyword_response = await asyncio.gather(
                    vector_task, graph_task, keyword_task, return_exceptions=True
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
                ) else "unhealthy",
                "keyword_rag_status": "healthy" if (
                    not isinstance(keyword_response, Exception) and 
                    keyword_response.status_code == 200
                ) else "unhealthy"
            }
            
            healthy_count = sum([
                status["vector_rag_status"] == "healthy",
                status["graph_rag_status"] == "healthy",
                status["keyword_rag_status"] == "healthy"
            ])
            
            if healthy_count == 3:
                status["overall_status"] = "healthy"
            elif healthy_count > 0:
                status["overall_status"] = "degraded"
            else:
                status["overall_status"] = "unhealthy"
            
            return status
            
        except Exception as e:
            logger.error(f"서비스 상태 확인 중 오류: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 전역 트리플 RAG 클라이언트 인스턴스
_triple_rag_client = None

def get_triple_rag_client() -> TripleRAGClient:
    """트리플 RAG 클라이언트 인스턴스 반환"""
    global _triple_rag_client
    if _triple_rag_client is None:
        _triple_rag_client = TripleRAGClient()
    return _triple_rag_client


if __name__ == "__main__":
    import asyncio
    
    async def test_triple_rag():
        client = TripleRAGClient()
        
        # 서비스 상태 확인
        status = await client.get_all_service_status()
        print("=== 트리플 RAG 서비스 상태 ===")
        print(f"전체 상태: {status['overall_status']}")
        print(f"Vector RAG: {status['vector_rag_status']}")
        print(f"Graph RAG: {status['graph_rag_status']}")
        print(f"Keyword RAG: {status['keyword_rag_status']}")
        
        # 테스트 문서 추가
        test_doc = {
            "title": "트리플 RAG 테스트",
            "content": """
            트리플 RAG는 벡터 검색, 지식 그래프 검색, 키워드 검색을 결합한 고급 시스템입니다.
            벡터 검색은 의미적 유사성을 기반으로 하고, 지식 그래프는 개체 간의 관계를 활용하며,
            키워드 검색은 정확한 용어 매칭을 제공합니다.
            이 세 가지를 결합하면 가장 포괄적이고 정확한 검색 결과를 얻을 수 있습니다.
            """,
            "metadata": {"source": "test", "category": "triple_rag"}
        }
        
        print("\n=== 문서 추가 테스트 ===")
        add_result = await client.add_document_to_all(**test_doc)
        print(f"추가 결과: {add_result['status']}")
        print(f"메시지: {add_result.get('message', '')}")
        
        # 트리플 검색 테스트
        print("\n=== 트리플 검색 테스트 ===")
        search_result = await client.triple_search("트리플 RAG가 무엇인가요?")
        print(f"검색 상태: {search_result.get('status', 'unknown')}")
        print(f"검색 품질: {search_result.get('search_quality', {})}")
        
        if search_result.get("triple_context"):
            print(f"컨텍스트 길이: {len(search_result['triple_context'])}자")
            print(f"컨텍스트 미리보기: {search_result['triple_context'][:200]}...")
    
    asyncio.run(test_triple_rag())