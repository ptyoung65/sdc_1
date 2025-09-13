#!/usr/bin/env python3
"""
Korean Vector DB Service - 한국어 최적화 Milvus 벡터 데이터베이스 서비스
TF-IDF 기반 벡터 저장 및 검색, PyTorch/Transformers 의존성 없음
"""

import os
import sys
import asyncio
import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import asynccontextmanager

# FastAPI 및 기본 의존성
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

# Milvus 벡터 데이터베이스
try:
    from pymilvus import (
        connections, Collection, FieldSchema, CollectionSchema,
        DataType, utility, MilvusException
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    logger.warning("Milvus 라이브러리가 설치되지 않았습니다. 모의 모드로 실행합니다.")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Pydantic 모델
class KoreanDocumentMetadata(BaseModel):
    user_id: str
    filename: str
    chunk_index: int
    total_chunks: int
    processed_at: str
    korean_features: Dict[str, Any] = Field(default_factory=dict)
    doc_type: str = "korean_document"

class VectorStoreRequest(BaseModel):
    chunk_id: str
    vector: List[float]
    content: str
    metadata: KoreanDocumentMetadata
    korean_features: Dict[str, Any] = Field(default_factory=dict)

class VectorSearchRequest(BaseModel):
    vector: List[float]
    top_k: int = 5
    threshold: float = 0.3
    user_id: Optional[str] = None
    filter_metadata: Dict[str, Any] = Field(default_factory=dict)

class VectorSearchResult(BaseModel):
    chunk_id: str
    content: str
    similarity: float
    metadata: Dict[str, Any]
    korean_features: Dict[str, Any]

class VectorSearchResponse(BaseModel):
    results: List[VectorSearchResult]
    total_found: int
    search_time: float

# Milvus 연결 및 컬렉션 관리
class KoreanMilvusManager:
    def __init__(self):
        self.collection_name = "korean_documents"
        self.collection = None
        self.connected = False
        self.dimension = 768  # TF-IDF 벡터 차원
        
    async def connect(self):
        """Milvus 연결 시도"""
        if not MILVUS_AVAILABLE:
            logger.warning("Milvus 라이브러리 없음, 모의 모드로 실행")
            return False
            
        try:
            # Milvus 연결 (Docker compose에서 설정된 호스트)
            milvus_host = os.getenv("MILVUS_HOST", "localhost")
            milvus_port = os.getenv("MILVUS_PORT", "19530")
            
            connections.connect("default", host=milvus_host, port=milvus_port)
            logger.info(f"✅ Milvus 연결 성공: {milvus_host}:{milvus_port}")
            
            # 컬렉션 생성 또는 로드
            await self.setup_collection()
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Milvus 연결 실패: {e}")
            self.connected = False
            return False
    
    async def setup_collection(self):
        """Korean 문서용 컬렉션 설정"""
        if not MILVUS_AVAILABLE:
            return
            
        try:
            # 컬렉션이 이미 존재하는지 확인
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"✅ 기존 컬렉션 로드: {self.collection_name}")
            else:
                # 새 컬렉션 생성
                fields = [
                    FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=100, is_primary=True),
                    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
                    FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=8192),
                    FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
                    FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=256),
                    FieldSchema(name="metadata_json", dtype=DataType.VARCHAR, max_length=4096),
                    FieldSchema(name="korean_features_json", dtype=DataType.VARCHAR, max_length=2048),
                    FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=50)
                ]
                
                schema = CollectionSchema(fields, "Korean documents with TF-IDF vectors")
                self.collection = Collection(self.collection_name, schema)
                
                # 인덱스 생성
                index = {
                    "index_type": "IVF_FLAT",
                    "metric_type": "COSINE",  # 코사인 유사도
                    "params": {"nlist": 128}
                }
                self.collection.create_index("vector", index)
                logger.info(f"✅ 새 컬렉션 생성: {self.collection_name}")
            
            # 컬렉션 로드
            self.collection.load()
            logger.info("✅ 컬렉션 메모리 로드 완료")
            
        except Exception as e:
            logger.error(f"컬렉션 설정 실패: {e}")
            raise
    
    async def store_vector(self, request: VectorStoreRequest) -> bool:
        """벡터 저장"""
        if not self.connected or not MILVUS_AVAILABLE:
            logger.warning("Milvus 미연결, 벡터 저장 생략")
            return False
            
        try:
            data = [
                [request.chunk_id],
                [request.vector],
                [request.content],
                [request.metadata.user_id],
                [request.metadata.filename],
                [json.dumps(request.metadata.dict(), ensure_ascii=False)],
                [json.dumps(request.korean_features, ensure_ascii=False)],
                [datetime.now().isoformat()]
            ]
            
            result = self.collection.insert(data)
            self.collection.flush()
            
            logger.info(f"✅ 벡터 저장 완료: {request.chunk_id}")
            return True
            
        except Exception as e:
            logger.error(f"벡터 저장 실패: {e}")
            return False
    
    async def search_vectors(self, request: VectorSearchRequest) -> List[VectorSearchResult]:
        """벡터 유사도 검색"""
        if not self.connected or not MILVUS_AVAILABLE:
            logger.warning("Milvus 미연결, 빈 결과 반환")
            return []
            
        try:
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            # 사용자별 필터링 (있는 경우)
            expr = None
            if request.user_id:
                expr = f'user_id == "{request.user_id}"'
            
            results = self.collection.search(
                data=[request.vector],
                anns_field="vector",
                param=search_params,
                limit=request.top_k,
                expr=expr,
                output_fields=["chunk_id", "content", "user_id", "filename", "metadata_json", "korean_features_json"]
            )
            
            search_results = []
            for hits in results:
                for hit in hits:
                    if hit.score >= request.threshold:  # 유사도 임계값 적용
                        try:
                            metadata = json.loads(hit.entity.get("metadata_json", "{}"))
                            korean_features = json.loads(hit.entity.get("korean_features_json", "{}"))
                        except:
                            metadata = {}
                            korean_features = {}
                        
                        search_results.append(VectorSearchResult(
                            chunk_id=hit.entity.get("chunk_id"),
                            content=hit.entity.get("content", ""),
                            similarity=float(hit.score),
                            metadata=metadata,
                            korean_features=korean_features
                        ))
            
            logger.info(f"✅ 벡터 검색 완료: {len(search_results)} 결과")
            return search_results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """컬렉션 통계"""
        if not self.connected or not MILVUS_AVAILABLE:
            return {"connected": False, "error": "Milvus not available"}
            
        try:
            stats = self.collection.num_entities
            return {
                "connected": True,
                "collection_name": self.collection_name,
                "total_vectors": stats,
                "dimension": self.dimension
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

# 전역 Milvus 매니저
milvus_manager = KoreanMilvusManager()

# FastAPI 앱 설정
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    logger.info("🚀 Korean Vector DB Service 시작 중...")
    await milvus_manager.connect()
    yield
    # 종료 시
    logger.info("⏹️ Korean Vector DB Service 종료")

app = FastAPI(
    title="Korean Vector DB Service",
    description="한국어 최적화 Milvus 벡터 데이터베이스 서비스",
    version="2.0.0-korean-optimized",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 엔드포인트
@app.get("/")
async def root():
    return {
        "service": "Korean Vector DB Service",
        "version": "2.0.0-korean-optimized",
        "status": "running",
        "description": "한국어 TF-IDF 벡터 저장 및 검색 서비스",
        "features": [
            "Milvus 벡터 데이터베이스",
            "한국어 메타데이터 지원",
            "코사인 유사도 검색",
            "사용자별 필터링"
        ]
    }

@app.get("/health")
async def health_check():
    stats = await milvus_manager.get_stats()
    return {
        "status": "healthy" if stats.get("connected") else "degraded",
        "milvus": stats,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/store")
async def store_vector(request: VectorStoreRequest):
    """벡터 저장"""
    try:
        success = await milvus_manager.store_vector(request)
        
        if success:
            return {
                "status": "success",
                "chunk_id": request.chunk_id,
                "message": "벡터가 성공적으로 저장되었습니다."
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "failed",
                    "message": "벡터 저장에 실패했습니다. Milvus 연결을 확인해주세요."
                }
            )
    except Exception as e:
        logger.error(f"벡터 저장 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_vectors(request: VectorSearchRequest):
    """벡터 유사도 검색"""
    try:
        start_time = datetime.now()
        
        results = await milvus_manager.search_vectors(request)
        
        search_time = (datetime.now() - start_time).total_seconds()
        
        return VectorSearchResponse(
            results=results,
            total_found=len(results),
            search_time=search_time
        )
        
    except Exception as e:
        logger.error(f"벡터 검색 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """벡터 데이터베이스 통계"""
    stats = await milvus_manager.get_stats()
    return {
        "service": "Korean Vector DB Service",
        "milvus": stats,
        "korean_optimization": {
            "tfidf_vectors": True,
            "korean_metadata": True,
            "cosine_similarity": True
        }
    }

@app.delete("/clear/{user_id}")
async def clear_user_vectors(user_id: str):
    """특정 사용자의 벡터 삭제"""
    try:
        if not milvus_manager.connected:
            raise HTTPException(status_code=503, detail="Milvus not connected")
        
        expr = f'user_id == "{user_id}"'
        result = milvus_manager.collection.delete(expr)
        
        return {
            "status": "success",
            "user_id": user_id,
            "message": f"사용자 {user_id}의 벡터가 삭제되었습니다."
        }
        
    except Exception as e:
        logger.error(f"벡터 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Korean Vector DB Service 시작 중...")
    print("📍 한국어 최적화 Milvus 벡터 데이터베이스")
    print("🔗 Running on http://0.0.0.0:8010")
    print("✅ TF-IDF 벡터 지원, PyTorch/Transformers 의존성 없음")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8010,
        log_level="info"
    )