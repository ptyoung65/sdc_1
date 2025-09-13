#!/usr/bin/env python3
"""
Korean RAG Orchestrator Service - 한국어 최적화 RAG 오케스트레이터
PyTorch/Transformers 없이 TF-IDF + Kiwi를 활용한 한국어 특화 문서 처리 파이프라인
"""

import sys
import os
import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# FastAPI 및 기본 의존성
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import aiohttp
import httpx

# 한국어 처리 및 벡터화 (기존 backend 모듈 활용)
sys.path.append('/home/ptyoung/work/sdc_i/backend')
from services.korean_embeddings import KoreanEmbeddingService, KoreanTextProcessor

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# FastAPI 앱 설정
app = FastAPI(
    title="Korean RAG Orchestrator",
    description="한국어 특화 RAG 파이프라인 오케스트레이터 (TF-IDF + Kiwi)",
    version="2.0.0-korean-optimized"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 URL 설정
MAIN_BACKEND_URL = "http://localhost:8000"
MILVUS_SERVICE_URL = "http://localhost:8010"
KOREAN_RAG_SERVICE_URL = "http://localhost:8009"

# 전역 서비스 인스턴스
korean_embedding_service = None
korean_text_processor = None

# Pydantic 모델
class DocumentUploadRequest(BaseModel):
    user_id: str
    filename: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    vector: List[float]
    metadata: Dict[str, Any]
    korean_features: Dict[str, Any]

class RAGQueryRequest(BaseModel):
    query: str
    user_id: str
    max_chunks: int = 5
    similarity_threshold: float = 0.3

class RAGResponse(BaseModel):
    query: str
    response: str
    sources: List[Dict[str, Any]]
    korean_analysis: Dict[str, Any]
    processing_time: float

# 서비스 상태 관리
class ServiceStatus:
    def __init__(self):
        self.korean_embedding_ready = False
        self.milvus_connected = False
        self.korean_rag_ready = False
        
    async def check_services(self):
        """모든 서비스 상태 확인"""
        try:
            # Korean embedding service 확인 (로컬)
            global korean_embedding_service, korean_text_processor
            if korean_embedding_service is None:
                korean_embedding_service = KoreanEmbeddingService(embedding_dim=768)
                korean_text_processor = KoreanTextProcessor()
                logger.info("✅ Korean Embedding Service 로컬 인스턴스 생성 완료")
            self.korean_embedding_ready = True
            
            # Milvus 서비스 확인
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{MILVUS_SERVICE_URL}/health", timeout=5.0)
                    self.milvus_connected = response.status_code == 200
            except:
                self.milvus_connected = False
                logger.warning("⚠️ Milvus 서비스 연결 실패")
            
            # Korean RAG 서비스 확인
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"{KOREAN_RAG_SERVICE_URL}/health", timeout=5.0)
                    self.korean_rag_ready = response.status_code == 200
            except:
                self.korean_rag_ready = False
                logger.warning("⚠️ Korean RAG 서비스 연결 실패")
                
        except Exception as e:
            logger.error(f"서비스 상태 확인 실패: {e}")

service_status = ServiceStatus()

@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    logger.info("🚀 Korean RAG Orchestrator 시작 중...")
    await service_status.check_services()
    logger.info("📍 Korean RAG Orchestrator 준비 완료 (Port 8008)")

@app.get("/")
async def root():
    return {
        "service": "Korean RAG Orchestrator",
        "version": "2.0.0-korean-optimized",
        "status": "running",
        "features": [
            "TF-IDF 기반 한국어 임베딩",
            "Kiwi 형태소 분석",
            "Milvus 벡터 저장",
            "한국어 최적화 청킹"
        ]
    }

@app.get("/health")
async def health_check():
    await service_status.check_services()
    return {
        "status": "healthy",
        "services": {
            "korean_embedding": service_status.korean_embedding_ready,
            "milvus": service_status.milvus_connected,
            "korean_rag": service_status.korean_rag_ready
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/process_document")
async def process_document(request: DocumentUploadRequest):
    """문서를 한국어 최적화 처리하여 벡터화 및 저장"""
    try:
        start_time = datetime.now()
        
        # 1. 한국어 텍스트 전처리
        processed_text = korean_text_processor.preprocess_text(request.content)
        
        # 2. 한국어 청킹 (의미 단위 분할)
        chunks = korean_text_processor.chunk_text(processed_text, chunk_size=500, overlap=50)
        
        # 3. 각 청크를 TF-IDF 벡터로 변환
        processed_chunks = []
        for i, chunk_text in enumerate(chunks):
            # 청크 벡터화
            try:
                vector = korean_embedding_service.embed_text(chunk_text)
                
                # 한국어 특성 분석
                korean_features = {
                    "tokenized": korean_text_processor.tokenize(chunk_text),
                    "keywords": korean_text_processor.extract_keywords(chunk_text),
                    "char_count": len(chunk_text),
                    "token_count": len(korean_text_processor.tokenize(chunk_text))
                }
                
                chunk_obj = DocumentChunk(
                    chunk_id=f"{request.user_id}_{uuid.uuid4().hex[:8]}_{i}",
                    content=chunk_text,
                    vector=vector.tolist(),
                    metadata={
                        "user_id": request.user_id,
                        "filename": request.filename,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "processed_at": datetime.now().isoformat(),
                        **request.metadata
                    },
                    korean_features=korean_features
                )
                processed_chunks.append(chunk_obj)
                
            except Exception as e:
                logger.error(f"청크 {i} 벡터화 실패: {e}")
                continue
        
        # 4. Milvus에 벡터 저장 (서비스 연결 시)
        stored_count = 0
        if service_status.milvus_connected:
            try:
                async with httpx.AsyncClient() as client:
                    for chunk in processed_chunks:
                        store_data = {
                            "chunk_id": chunk.chunk_id,
                            "vector": chunk.vector,
                            "content": chunk.content,
                            "metadata": chunk.metadata,
                            "korean_features": chunk.korean_features
                        }
                        response = await client.post(
                            f"{MILVUS_SERVICE_URL}/store",
                            json=store_data,
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            stored_count += 1
            except Exception as e:
                logger.error(f"Milvus 저장 실패: {e}")
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "document_id": f"{request.user_id}_{uuid.uuid4().hex[:8]}",
            "chunks_processed": len(processed_chunks),
            "chunks_stored": stored_count,
            "korean_features": {
                "total_tokens": sum(len(chunk.korean_features.get("tokenized", [])) for chunk in processed_chunks),
                "total_keywords": sum(len(chunk.korean_features.get("keywords", [])) for chunk in processed_chunks),
                "average_chunk_size": sum(chunk.korean_features.get("char_count", 0) for chunk in processed_chunks) / len(processed_chunks) if processed_chunks else 0
            },
            "processing_time": processing_time,
            "services_used": {
                "korean_embedding": True,
                "milvus_storage": service_status.milvus_connected
            }
        }
        
    except Exception as e:
        logger.error(f"문서 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"문서 처리 중 오류 발생: {str(e)}")

@app.post("/query")
async def rag_query(request: RAGQueryRequest):
    """한국어 최적화 RAG 질의 처리"""
    try:
        start_time = datetime.now()
        
        # 1. 질의 한국어 전처리 및 벡터화
        query_processed = korean_text_processor.preprocess_text(request.query)
        query_vector = korean_embedding_service.embed_text(query_processed)
        
        # 2. 질의 분석
        korean_analysis = {
            "original_query": request.query,
            "processed_query": query_processed,
            "tokenized": korean_text_processor.tokenize(query_processed),
            "keywords": korean_text_processor.extract_keywords(query_processed)
        }
        
        # 3. 벡터 유사도 검색 (Milvus 연결 시)
        retrieved_chunks = []
        if service_status.milvus_connected:
            try:
                async with httpx.AsyncClient() as client:
                    search_data = {
                        "vector": query_vector.tolist(),
                        "top_k": request.max_chunks,
                        "threshold": request.similarity_threshold
                    }
                    response = await client.post(
                        f"{MILVUS_SERVICE_URL}/search",
                        json=search_data,
                        timeout=15.0
                    )
                    if response.status_code == 200:
                        retrieved_chunks = response.json().get("results", [])
            except Exception as e:
                logger.error(f"벡터 검색 실패: {e}")
        
        # 4. 컨텍스트 구성 및 응답 생성
        context_text = "\n\n".join([chunk.get("content", "") for chunk in retrieved_chunks])
        
        # 5. LLM 응답 생성 (Korean RAG 서비스 연결 시)
        response_text = "문서 검색이 완료되었지만 응답 생성 서비스가 연결되지 않았습니다."
        if service_status.korean_rag_ready:
            try:
                async with httpx.AsyncClient() as client:
                    llm_data = {
                        "query": request.query,
                        "context": context_text,
                        "korean_analysis": korean_analysis
                    }
                    response = await client.post(
                        f"{KOREAN_RAG_SERVICE_URL}/generate",
                        json=llm_data,
                        timeout=30.0
                    )
                    if response.status_code == 200:
                        response_text = response.json().get("response", response_text)
            except Exception as e:
                logger.error(f"응답 생성 실패: {e}")
                response_text = f"검색된 컨텍스트를 기반으로 응답: {context_text[:500]}..." if context_text else "관련 문서를 찾을 수 없습니다."
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return RAGResponse(
            query=request.query,
            response=response_text,
            sources=[{
                "chunk_id": chunk.get("chunk_id"),
                "content": chunk.get("content", "")[:200] + "...",
                "similarity": chunk.get("similarity", 0.0),
                "metadata": chunk.get("metadata", {})
            } for chunk in retrieved_chunks],
            korean_analysis=korean_analysis,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"RAG 질의 처리 실패: {e}")
        raise HTTPException(status_code=500, detail=f"질의 처리 중 오류 발생: {str(e)}")

@app.get("/stats")
async def get_stats():
    """서비스 통계 정보"""
    await service_status.check_services()
    return {
        "service": "Korean RAG Orchestrator",
        "status": {
            "korean_embedding": service_status.korean_embedding_ready,
            "milvus": service_status.milvus_connected,
            "korean_rag": service_status.korean_rag_ready
        },
        "features": {
            "korean_tokenization": KIWI_AVAILABLE if 'KIWI_AVAILABLE' in globals() else False,
            "tfidf_vectorization": True,
            "korean_preprocessing": True,
            "milvus_storage": service_status.milvus_connected
        },
        "version": "2.0.0-korean-optimized"
    }

@app.get("/documents")
async def get_all_documents():
    """모든 문서 조회"""
    try:
        if service_status.milvus_connected:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{MILVUS_SERVICE_URL}/stats", timeout=5.0)
                if response.status_code == 200:
                    stats = response.json()
                    return {
                        "documents": [],
                        "total_vectors": stats.get("milvus", {}).get("total_vectors", 0),
                        "status": "connected"
                    }
        return {"documents": [], "total_vectors": 0, "status": "disconnected"}
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}")
        return {"documents": [], "total_vectors": 0, "status": "error"}

@app.get("/documents/{user_id}")
async def get_user_documents(user_id: str):
    """사용자별 문서 조회"""
    try:
        # Korean RAG Service에서 문서 목록 조회 시도
        if service_status.korean_rag_connected:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{KOREAN_RAG_SERVICE_URL}/documents/{user_id}", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
        
        # 폴백: 빈 문서 목록 반환
        return {"documents": [], "user_id": user_id, "total": 0}
    except Exception as e:
        logger.error(f"사용자 문서 조회 실패: {e}")
        return {"documents": [], "user_id": user_id, "total": 0}

@app.get("/documents/{document_id}")
async def get_document_details(document_id: str):
    """문서 상세 정보 조회"""
    try:
        if service_status.korean_rag_connected:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{KOREAN_RAG_SERVICE_URL}/documents/{document_id}", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
        
        return {"document_id": document_id, "status": "not_found"}
    except Exception as e:
        logger.error(f"문서 상세 조회 실패: {e}")
        return {"document_id": document_id, "status": "error"}

@app.get("/documents/{document_id}/chunks")
async def get_document_chunks(document_id: str):
    """문서 청크 조회"""
    try:
        if service_status.korean_rag_connected:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{KOREAN_RAG_SERVICE_URL}/documents/{document_id}/chunks", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
        
        return {"chunks": [], "document_id": document_id, "total": 0}
    except Exception as e:
        logger.error(f"문서 청크 조회 실패: {e}")
        return {"chunks": [], "document_id": document_id, "total": 0}

if __name__ == "__main__":
    print("🚀 Korean RAG Orchestrator 시작 중...")
    print("📍 한국어 특화 TF-IDF + Kiwi 기반 RAG 파이프라인")
    print("🔗 Running on http://0.0.0.0:8008")
    print("✅ PyTorch/Transformers 의존성 없음")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8008,
        log_level="info"
    )