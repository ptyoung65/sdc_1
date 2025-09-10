"""
Graph RAG Microservice
지식 그래프 기반 RAG 마이크로서비스 - FastAPI 독립 서비스
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import argparse
import sys
import os
import uvicorn
from datetime import datetime
import uuid
import httpx

from knowledge_graph import get_knowledge_graph_builder

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Graph RAG Service",
    description="지식 그래프 기반 RAG (Retrieval-Augmented Generation) 마이크로서비스",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델들
class DocumentRequest(BaseModel):
    title: str = Field(..., description="문서 제목")
    content: str = Field(..., description="문서 내용")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")
    document_id: Optional[str] = Field(None, description="문서 ID (자동 생성 가능)")

class QueryRequest(BaseModel):
    query: str = Field(..., description="검색 질문")
    max_hops: Optional[int] = Field(2, description="최대 탐색 깊이")
    max_results: Optional[int] = Field(10, description="최대 결과 수")

class HybridQueryRequest(BaseModel):
    query: str = Field(..., description="검색 질문")
    use_vector_rag: bool = Field(True, description="벡터 RAG 사용 여부")
    use_graph_rag: bool = Field(True, description="그래프 RAG 사용 여부")
    vector_rag_url: Optional[str] = Field("http://localhost:8009", description="벡터 RAG 서비스 URL")
    max_hops: Optional[int] = Field(2, description="그래프 탐색 최대 깊이")
    max_results: Optional[int] = Field(10, description="최대 결과 수")

class DocumentDeleteRequest(BaseModel):
    document_id: str = Field(..., description="삭제할 문서 ID")

# 지식 그래프 빌더 초기화
try:
    graph_builder = get_knowledge_graph_builder()
    logger.info("Graph RAG 시스템 초기화 완료")
except Exception as e:
    logger.error(f"Graph RAG 시스템 초기화 실패: {e}")
    graph_builder = None

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not initialized")
    
    try:
        health_status = graph_builder.health_check()
        return {
            "status": "healthy",
            "service": "graph-rag-service",
            "timestamp": datetime.now().isoformat(),
            "graph_rag_system": health_status
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")

@app.post("/graph/build")
async def build_knowledge_graph(document: DocumentRequest):
    """문서로부터 지식 그래프 구축"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not available")
    
    try:
        result = graph_builder.build_graph_from_document(
            document_id=document.document_id or f"doc_{uuid.uuid4().hex[:8]}",
            title=document.title,
            content=document.content,
            metadata=document.metadata
        )
        
        if result.get("status") == "success":
            return {
                "success": True,
                "data": result,
                "message": f"지식 그래프 구축 완료: {result['nodes_added']}개 노드, {result['edges_added']}개 엣지 추가"
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("message", "지식 그래프 구축 실패"))
            
    except Exception as e:
        logger.error(f"지식 그래프 구축 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"지식 그래프 구축 중 오류: {str(e)}")

@app.post("/graph/query")
async def query_knowledge_graph(query: QueryRequest):
    """지식 그래프 검색"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not available")
    
    try:
        subgraphs = graph_builder.query_graph(
            query=query.query,
            max_hops=query.max_hops,
            max_results=query.max_results
        )
        
        # 컨텍스트 생성
        graph_context = graph_builder.generate_graph_context(subgraphs)
        
        return {
            "success": True,
            "data": {
                "query": query.query,
                "subgraphs_found": len(subgraphs),
                "graph_context": graph_context,
                "subgraphs": subgraphs,
                "parameters": {
                    "max_hops": query.max_hops,
                    "max_results": query.max_results
                }
            },
            "message": f"그래프 검색 완료: {len(subgraphs)}개 서브그래프 발견"
        }
        
    except Exception as e:
        logger.error(f"지식 그래프 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"검색 중 오류: {str(e)}")

@app.post("/hybrid/query")
async def hybrid_rag_query(query: HybridQueryRequest):
    """하이브리드 RAG 검색 (Vector + Graph RAG)"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not available")
    
    try:
        results = {
            "query": query.query,
            "vector_rag_results": None,
            "graph_rag_results": None,
            "hybrid_context": "",
            "timestamp": datetime.now().isoformat()
        }
        
        # Vector RAG 호출
        if query.use_vector_rag:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    vector_response = await client.post(
                        f"{query.vector_rag_url}/search",
                        json={"query": query.query}
                    )
                    if vector_response.status_code == 200:
                        results["vector_rag_results"] = vector_response.json()
                        logger.info(f"Vector RAG 호출 성공")
                    else:
                        logger.warning(f"Vector RAG 호출 실패: {vector_response.status_code}")
            except Exception as e:
                logger.warning(f"Vector RAG 연결 실패: {e}")
        
        # Graph RAG 호출
        if query.use_graph_rag:
            try:
                subgraphs = graph_builder.query_graph(
                    query=query.query,
                    max_hops=query.max_hops,
                    max_results=query.max_results
                )
                graph_context = graph_builder.generate_graph_context(subgraphs)
                
                results["graph_rag_results"] = {
                    "subgraphs_found": len(subgraphs),
                    "graph_context": graph_context,
                    "subgraphs": subgraphs
                }
                logger.info(f"Graph RAG 검색 완료: {len(subgraphs)}개 서브그래프")
            except Exception as e:
                logger.error(f"Graph RAG 검색 실패: {e}")
        
        # 하이브리드 컨텍스트 생성
        context_parts = []
        
        if results["vector_rag_results"] and results["vector_rag_results"].get("success"):
            vector_context = results["vector_rag_results"]["data"].get("context", "")
            if vector_context:
                context_parts.append(f"=== 벡터 검색 결과 ===\n{vector_context}")
        
        if results["graph_rag_results"]:
            graph_context = results["graph_rag_results"].get("graph_context", "")
            if graph_context:
                context_parts.append(f"=== 지식 그래프 검색 결과 ===\n{graph_context}")
        
        results["hybrid_context"] = "\n\n".join(context_parts)
        
        # 하이브리드 RAG 프롬프트 생성
        if results["hybrid_context"]:
            hybrid_prompt = f"""다음 정보들을 종합하여 질문에 답변해주세요.

{results["hybrid_context"]}

=== 질문 ===
{query.query}

=== 답변 지침 ===
1. 벡터 검색과 지식 그래프 결과를 모두 활용하여 종합적으로 답변하세요
2. 정확한 정보만 사용하고 추측하지 마세요
3. 한국어로 자연스럽게 답변하세요
4. 가능하면 정보의 출처를 언급하세요

답변:"""
            results["hybrid_prompt"] = hybrid_prompt
        
        return {
            "success": True,
            "data": results,
            "message": f"하이브리드 RAG 검색 완료 (Vector: {'O' if results['vector_rag_results'] else 'X'}, Graph: {'O' if results['graph_rag_results'] else 'X'})"
        }
        
    except Exception as e:
        logger.error(f"하이브리드 RAG 검색 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"하이브리드 검색 중 오류: {str(e)}")

@app.delete("/graph/documents/{document_id}")
async def delete_document_from_graph(document_id: str):
    """지식 그래프에서 문서 삭제"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not available")
    
    try:
        success = graph_builder.delete_document_from_graph(document_id)
        
        if success:
            return {
                "success": True,
                "data": {"document_id": document_id},
                "message": f"문서 '{document_id}'가 지식 그래프에서 삭제되었습니다"
            }
        else:
            raise HTTPException(status_code=400, detail=f"문서 '{document_id}' 삭제 실패")
            
    except Exception as e:
        logger.error(f"문서 삭제 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문서 삭제 중 오류: {str(e)}")

@app.get("/graph/stats")
async def get_graph_stats():
    """지식 그래프 통계"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not available")
    
    try:
        stats = graph_builder.get_graph_stats()
        
        return {
            "success": True,
            "data": stats,
            "message": "지식 그래프 통계 조회 완료"
        }
        
    except Exception as e:
        logger.error(f"통계 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")

@app.post("/sync/document")
async def sync_document_with_vector_rag(document: DocumentRequest, background_tasks: BackgroundTasks):
    """벡터 RAG와 동기화하여 문서 처리"""
    if graph_builder is None:
        raise HTTPException(status_code=503, detail="Graph RAG system not available")
    
    try:
        # 지식 그래프 구축
        graph_result = graph_builder.build_graph_from_document(
            document_id=document.document_id or f"doc_{uuid.uuid4().hex[:8]}",
            title=document.title,
            content=document.content,
            metadata=document.metadata
        )
        
        # 백그라운드에서 벡터 RAG에도 문서 추가
        background_tasks.add_task(
            sync_to_vector_rag,
            document.dict(),
            "http://localhost:8009"  # Korean RAG 서비스 URL
        )
        
        return {
            "success": True,
            "data": {
                "graph_result": graph_result,
                "sync_status": "백그라운드에서 벡터 RAG와 동기화 중"
            },
            "message": f"문서 처리 완료 및 동기화 시작"
        }
        
    except Exception as e:
        logger.error(f"문서 동기화 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"문서 동기화 중 오류: {str(e)}")

async def sync_to_vector_rag(document_data: Dict[str, Any], vector_rag_url: str):
    """벡터 RAG 서비스와 동기화"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{vector_rag_url}/documents",
                json=document_data
            )
            if response.status_code == 200:
                logger.info(f"벡터 RAG 동기화 성공: {document_data.get('title', 'Unknown')}")
            else:
                logger.warning(f"벡터 RAG 동기화 실패: {response.status_code}")
    except Exception as e:
        logger.error(f"벡터 RAG 동기화 중 오류: {e}")

@app.get("/")
async def root():
    """서비스 정보"""
    return {
        "service": "Graph RAG Service",
        "version": "1.0.0",
        "description": "지식 그래프 기반 RAG 마이크로서비스",
        "endpoints": {
            "health": "GET /health",
            "build_graph": "POST /graph/build",
            "query_graph": "POST /graph/query",
            "hybrid_query": "POST /hybrid/query",
            "delete_document": "DELETE /graph/documents/{document_id}",
            "graph_stats": "GET /graph/stats",
            "sync_document": "POST /sync/document"
        },
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Graph RAG Service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8010, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Graph RAG Service on {args.host}:{args.port}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )