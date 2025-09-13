#!/usr/bin/env python3
"""
Korean RAG Gemini Response Service - Gemini API를 활용한 한국어 RAG 응답 생성 서비스
"""

import os
import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# FastAPI 및 기본 의존성
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Gemini API
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai 라이브러리가 설치되지 않았습니다. 'pip install google-generativeai' 실행 필요")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Pydantic 모델
class KoreanAnalysis(BaseModel):
    original_query: str
    processed_query: str
    tokenized: List[str]
    keywords: List[str]

class GenerateRequest(BaseModel):
    query: str
    context: str
    korean_analysis: Optional[KoreanAnalysis] = None
    user_id: Optional[str] = "default"

class GenerateResponse(BaseModel):
    response: str
    model_used: str
    processing_time: float
    context_length: int
    korean_optimized: bool

class HealthResponse(BaseModel):
    status: str
    gemini_api_available: bool
    model: Optional[str]
    timestamp: str

# Gemini API 설정 및 모델 초기화
class GeminiRAGService:
    def __init__(self):
        self.model = None
        self.model_name = "gemini-1.5-flash"
        self.api_key = None
        self.initialized = False
        
    def initialize(self):
        """Gemini API 초기화"""
        if not GEMINI_AVAILABLE:
            logger.error("❌ Gemini API 라이브러리가 설치되지 않았습니다.")
            return False
            
        # API 키 확인
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.error("❌ GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")
            logger.info("💡 export GEMINI_API_KEY=your_api_key_here")
            return False
        
        try:
            # Gemini API 설정
            genai.configure(api_key=self.api_key)
            
            # 모델 초기화
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info(f"✅ Gemini API 초기화 완료: {self.model_name}")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Gemini API 초기화 실패: {e}")
            return False
    
    def create_korean_prompt(self, query: str, context: str, korean_analysis: Optional[KoreanAnalysis] = None) -> str:
        """한국어 최적화 프롬프트 생성"""
        
        # 기본 한국어 RAG 프롬프트
        base_prompt = f"""당신은 한국어 문서 기반 질의응답 전문가입니다. 
제공된 문서 내용을 바탕으로 사용자의 질문에 정확하고 도움이 되는 답변을 제공하세요.

**답변 지침:**
1. 제공된 문서 내용을 기반으로만 답변하세요
2. 문서에 없는 내용은 추측하지 마세요
3. 한국어로 자연스럽고 정확하게 답변하세요
4. 구체적인 정보와 예시를 포함하세요
5. 만약 문서 내용이 질문과 관련이 없다면 그렇게 알려주세요

**사용자 질문:** {query}

**관련 문서 내용:**
{context}

**답변:**"""

        # 한국어 분석 정보가 있으면 추가
        if korean_analysis:
            korean_info = f"""
**한국어 분석 정보:**
- 처리된 쿼리: {korean_analysis.processed_query}
- 주요 키워드: {', '.join(korean_analysis.keywords)}
- 토큰: {', '.join(korean_analysis.tokenized)}

"""
            # 프롬프트에 한국어 분석 정보 삽입
            base_prompt = base_prompt.replace("**사용자 질문:**", korean_info + "**사용자 질문:**")
        
        return base_prompt
    
    async def generate_response(self, request: GenerateRequest) -> GenerateResponse:
        """Gemini API를 사용하여 한국어 RAG 응답 생성"""
        start_time = datetime.now()
        
        # API 키가 없는 경우 fallback 응답 제공
        if not self.initialized:
            logger.warning("Gemini API가 초기화되지 않았습니다. Fallback 응답을 제공합니다.")
            
            # 컨텍스트 기반 간단한 응답 생성
            fallback_response = f"""제공된 문서 내용을 기반으로 답변드리겠습니다.

**질문:** {request.query}

**관련 문서 내용:**
{request.context[:500]}{'...' if len(request.context) > 500 else ''}

**답변:** 
문서 내용을 검토한 결과, 한국어 자연어 처리 시스템과 관련된 정보를 확인할 수 있습니다. 더 정확한 AI 응답을 위해서는 Gemini API 키 설정이 필요합니다.

⚠️ 현재 Gemini API 키가 설정되지 않아 제한된 응답을 제공하고 있습니다. 완전한 AI 응답을 위해 `export GEMINI_API_KEY=your_api_key` 명령으로 API 키를 설정해 주세요."""

            processing_time = (datetime.now() - start_time).total_seconds()
            
            return GenerateResponse(
                response=fallback_response,
                model_used="fallback-mode",
                processing_time=processing_time,
                context_length=len(request.context),
                korean_optimized=False
            )
        
        try:
            # 한국어 최적화 프롬프트 생성
            prompt = self.create_korean_prompt(
                query=request.query,
                context=request.context,
                korean_analysis=request.korean_analysis
            )
            
            # Gemini API 호출
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # 응답 텍스트 추출
            if response.candidates and len(response.candidates) > 0:
                generated_text = response.candidates[0].content.parts[0].text.strip()
            else:
                generated_text = "죄송합니다. 응답을 생성할 수 없습니다. 다시 시도해 주세요."
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return GenerateResponse(
                response=generated_text,
                model_used=self.model_name,
                processing_time=processing_time,
                context_length=len(request.context),
                korean_optimized=True
            )
            
        except Exception as e:
            logger.error(f"Gemini API 응답 생성 실패: {e}")
            raise HTTPException(status_code=500, detail=f"응답 생성 중 오류 발생: {str(e)}")

# 전역 Gemini 서비스 인스턴스
gemini_service = GeminiRAGService()

# FastAPI 앱 설정
app = FastAPI(
    title="Korean RAG Gemini Service",
    description="Gemini API를 활용한 한국어 RAG 응답 생성 서비스",
    version="1.0.0-gemini"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 Gemini API 초기화"""
    logger.info("🚀 Korean RAG Gemini Service 시작 중...")
    success = gemini_service.initialize()
    if success:
        logger.info("✅ Gemini API 연결 및 모델 로드 완료")
    else:
        logger.warning("⚠️ Gemini API 초기화 실패 - 모의 모드로 실행")

# API 엔드포인트
@app.get("/", response_model=dict)
async def root():
    return {
        "service": "Korean RAG Gemini Service",
        "version": "1.0.0-gemini",
        "status": "running",
        "description": "Gemini API를 활용한 한국어 RAG 응답 생성 서비스",
        "features": [
            "Gemini 1.5 Flash 모델",
            "한국어 최적화 프롬프트",
            "컨텍스트 기반 응답 생성",
            "한국어 분석 정보 활용"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy" if gemini_service.initialized else "degraded",
        gemini_api_available=gemini_service.initialized,
        model=gemini_service.model_name if gemini_service.initialized else None,
        timestamp=datetime.now().isoformat()
    )

@app.post("/generate", response_model=GenerateResponse)
async def generate_response(request: GenerateRequest):
    """
    컨텍스트를 기반으로 Gemini API를 사용하여 한국어 응답 생성
    """
    try:
        # 입력 검증
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="쿼리가 비어있습니다.")
        
        if not request.context.strip():
            raise HTTPException(status_code=400, detail="컨텍스트가 비어있습니다.")
        
        # Gemini API로 응답 생성
        response = await gemini_service.generate_response(request)
        
        logger.info(f"✅ 응답 생성 완료 - 사용자: {request.user_id}, 처리시간: {response.processing_time:.3f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"응답 생성 API 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    """서비스 통계 정보"""
    return {
        "service": "Korean RAG Gemini Service",
        "gemini": {
            "available": gemini_service.initialized,
            "model": gemini_service.model_name,
            "api_key_configured": bool(gemini_service.api_key)
        },
        "features": {
            "korean_optimization": True,
            "context_based_generation": True,
            "multilingual": True
        },
        "version": "1.0.0-gemini"
    }

if __name__ == "__main__":
    print("🚀 Korean RAG Gemini Service 시작 중...")
    print("📍 Gemini API 기반 한국어 응답 생성 서비스")
    print("🔗 Running on http://0.0.0.0:8009")
    print("✅ 컨텍스트 기반 응답 생성, 한국어 최적화")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8009,
        log_level="info"
    )