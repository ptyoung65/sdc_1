"""
Text-to-SQL RAG 마이크로서비스
자연어 질문을 SQL로 변환하고 결과를 RAG 처리하여 LLM 답변 생성
"""

import logging
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional
import argparse

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from text_to_sql_converter import TextToSQLConverter, get_text_to_sql_converter, DatabaseSchema
from sql_rag_processor import SQLRAGProcessor, get_sql_rag_processor, RAGData

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Text-to-SQL RAG Service",
    description="자연어를 SQL로 변환하여 RAG 처리하는 마이크로서비스",
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
class QuestionRequest(BaseModel):
    question: str
    user_id: str
    db_schema: Optional[Dict[str, Any]] = None
    max_results: int = 100

class SQLQueryRequest(BaseModel):
    sql_query: str
    user_id: str

class SchemaUpdateRequest(BaseModel):
    schema_info: Dict[str, Any]

class TextToSQLResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str
    timestamp: str
    processing_time: float
    error: Optional[str] = None

# 전역 변수들
text_to_sql_converter: Optional[TextToSQLConverter] = None
sql_rag_processor: Optional[SQLRAGProcessor] = None

# 환경 변수에서 설정 읽기
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://sdc_user:sdc_password@localhost:5432/sdc_db"
)

@app.on_event("startup")
async def startup_event():
    """서비스 시작 시 초기화"""
    global text_to_sql_converter, sql_rag_processor
    
    try:
        # Text-to-SQL 변환기 초기화
        text_to_sql_converter = get_text_to_sql_converter()
        
        # SQL RAG 프로세서 초기화
        sql_rag_processor = get_sql_rag_processor(DATABASE_URL)
        try:
            await sql_rag_processor.initialize_db_pool()
        except Exception as e:
            logger.warning(f"DB 연결 실패, 일부 기능만 사용 가능: {e}")
            # DB 연결이 실패해도 서비스는 계속 실행
        
        # 기본 스키마 로드 (예시)
        default_schema = {
            "tables": {
                "users": {
                    "id": "INTEGER",
                    "name": "VARCHAR(100)",
                    "email": "VARCHAR(255)",
                    "created_at": "TIMESTAMP",
                    "status": "VARCHAR(20)"
                },
                "posts": {
                    "id": "INTEGER", 
                    "user_id": "INTEGER",
                    "title": "VARCHAR(255)",
                    "content": "TEXT",
                    "created_at": "TIMESTAMP",
                    "views": "INTEGER"
                }
            },
            "relationships": [
                {"from": "posts.user_id", "to": "users.id", "type": "foreign_key"}
            ],
            "descriptions": {
                "users": "사용자 정보를 저장하는 테이블",
                "posts": "게시물 정보를 저장하는 테이블"
            }
        }
        
        text_to_sql_converter.load_database_schema(default_schema)
        
        logger.info("Text-to-SQL RAG 서비스 초기화 완료")
        
    except Exception as e:
        logger.error(f"서비스 초기화 실패: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """서비스 종료 시 정리"""
    try:
        if sql_rag_processor:
            await sql_rag_processor.close_db_pool()
        logger.info("Text-to-SQL RAG 서비스 종료 완료")
    except Exception as e:
        logger.error(f"서비스 종료 중 오류: {e}")

@app.get("/")
async def root():
    """서비스 정보 반환"""
    return {
        "service": "Text-to-SQL RAG Service",
        "version": "1.0.0",
        "description": "자연어를 SQL로 변환하여 RAG 처리하는 마이크로서비스",
        "endpoints": {
            "health": "GET /health",
            "ask_question": "POST /ask",
            "execute_sql": "POST /execute",
            "update_schema": "POST /schema",
            "get_schema": "GET /schema",
            "question_analysis": "POST /analyze"
        },
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        health_status = {
            "status": "healthy",
            "service": "text-to-sql-rag-service",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "text_to_sql_converter": "healthy" if text_to_sql_converter else "unhealthy",
                "sql_rag_processor": "healthy" if sql_rag_processor else "unhealthy",
                "database_connection": "unknown"
            }
        }
        
        # 데이터베이스 연결 확인
        if sql_rag_processor and sql_rag_processor.db_pool:
            try:
                async with sql_rag_processor.db_pool.acquire() as connection:
                    await connection.fetchrow("SELECT 1")
                health_status["components"]["database_connection"] = "healthy"
            except:
                health_status["components"]["database_connection"] = "unhealthy"
                health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/ask", response_model=TextToSQLResponse)
async def ask_question(request: QuestionRequest):
    """자연어 질문을 받아 SQL 변환 후 RAG 처리하여 답변"""
    start_time = datetime.now()
    
    try:
        logger.info(f"질문 처리 시작: {request.question}")
        
        if not text_to_sql_converter or not sql_rag_processor:
            raise HTTPException(status_code=500, detail="서비스가 초기화되지 않았습니다")
        
        # 1. 질문 의도 분석
        intent = text_to_sql_converter.analyze_question_intent(request.question)
        
        if not intent.get("needs_db_search", False):
            # DB 검색이 필요하지 않은 경우
            return TextToSQLResponse(
                success=False,
                message="이 질문은 데이터베이스 검색이 필요하지 않습니다",
                timestamp=datetime.now().isoformat(),
                processing_time=(datetime.now() - start_time).total_seconds(),
                error="NO_DB_SEARCH_NEEDED"
            )
        
        # 2. 스키마 업데이트 (요청에 포함된 경우)
        if request.db_schema:
            text_to_sql_converter.load_database_schema(request.db_schema)
        
        # 3. 자연어를 SQL로 변환
        sql_query = await text_to_sql_converter.convert_to_sql(request.question)
        
        if not sql_query.safety_check:
            raise HTTPException(status_code=400, detail="안전하지 않은 SQL이 생성되었습니다")
        
        # 4. SQL 실행
        query_result = await sql_rag_processor.execute_sql_query(sql_query)
        
        # 5. SQL 결과를 RAG 데이터로 처리
        rag_data = await sql_rag_processor.process_sql_results_to_rag(
            request.question, sql_query, query_result
        )
        
        # 6. 응답 구성
        response_data = {
            "question_analysis": {
                "original_question": request.question,
                "intent": intent,
                "needs_db_search": intent.get("needs_db_search", False)
            },
            "sql_generation": {
                "generated_sql": sql_query.sql,
                "confidence": sql_query.confidence,
                "reasoning": sql_query.reasoning,
                "complexity": sql_query.estimated_complexity,
                "tables_involved": sql_query.tables_involved
            },
            "query_execution": {
                "success": query_result.success,
                "row_count": query_result.row_count,
                "execution_time": query_result.execution_time,
                "error": query_result.error_message
            },
            "rag_processing": {
                "structured_context": rag_data.structured_context,
                "summary": rag_data.summary,
                "insights": rag_data.insights,
                "quality_score": rag_data.quality_score,
                "processing_time": rag_data.processing_time
            },
            "final_answer": {
                "context": rag_data.structured_context,
                "ready_for_llm": True,
                "suggested_prompt": f"다음 데이터를 바탕으로 '{request.question}'에 대해 답변해주세요:\n\n{rag_data.structured_context}\n\n요약: {rag_data.summary}"
            }
        }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"질문 처리 완료: {processing_time:.3f}초, 품질점수: {rag_data.quality_score:.2f}")
        
        return TextToSQLResponse(
            success=True,
            data=response_data,
            message=f"질문 처리 완료: SQL 실행 성공, {query_result.row_count}개 결과",
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"질문 처리 실패: {e}")
        
        return TextToSQLResponse(
            success=False,
            message=f"질문 처리 실패: {str(e)}",
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time,
            error=str(e)
        )

@app.post("/execute", response_model=TextToSQLResponse)
async def execute_sql_directly(request: SQLQueryRequest):
    """SQL을 직접 실행하여 RAG 처리"""
    start_time = datetime.now()
    
    try:
        if not sql_rag_processor:
            raise HTTPException(status_code=500, detail="서비스가 초기화되지 않았습니다")
        
        # SQL 안전성 검증
        if not text_to_sql_converter._validate_sql_safety(request.sql_query):
            raise HTTPException(status_code=400, detail="안전하지 않은 SQL입니다")
        
        # 더미 SQLQuery 객체 생성
        from text_to_sql_converter import SQLQuery
        sql_query = SQLQuery(
            sql=request.sql_query,
            confidence=1.0,
            reasoning="직접 입력된 SQL",
            parameters={},
            estimated_complexity="unknown",
            safety_check=True,
            tables_involved=[]
        )
        
        # SQL 실행
        query_result = await sql_rag_processor.execute_sql_query(sql_query)
        
        # RAG 처리
        rag_data = await sql_rag_processor.process_sql_results_to_rag(
            "직접 SQL 실행", sql_query, query_result
        )
        
        response_data = {
            "sql_execution": {
                "sql": request.sql_query,
                "success": query_result.success,
                "row_count": query_result.row_count,
                "execution_time": query_result.execution_time
            },
            "rag_data": {
                "context": rag_data.structured_context,
                "summary": rag_data.summary,
                "insights": rag_data.insights,
                "quality_score": rag_data.quality_score
            }
        }
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TextToSQLResponse(
            success=True,
            data=response_data,
            message=f"SQL 직접 실행 완료: {query_result.row_count}개 결과",
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time
        )
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.error(f"SQL 직접 실행 실패: {e}")
        
        return TextToSQLResponse(
            success=False,
            message=f"SQL 실행 실패: {str(e)}",
            timestamp=datetime.now().isoformat(),
            processing_time=processing_time,
            error=str(e)
        )

@app.post("/analyze")
async def analyze_question(request: QuestionRequest):
    """질문만 분석 (SQL 실행 없이)"""
    try:
        if not text_to_sql_converter:
            raise HTTPException(status_code=500, detail="서비스가 초기화되지 않았습니다")
        
        intent = text_to_sql_converter.analyze_question_intent(request.question)
        
        result = {
            "question": request.question,
            "analysis": intent,
            "recommendation": {
                "should_use_db": intent.get("needs_db_search", False),
                "confidence": intent.get("confidence", 0.0),
                "suggested_operations": intent.get("operations", [])
            }
        }
        
        if intent.get("needs_db_search", False):
            # SQL 생성 (실행하지 않음)
            sql_query = await text_to_sql_converter.convert_to_sql(request.question)
            result["generated_sql"] = {
                "sql": sql_query.sql,
                "confidence": sql_query.confidence,
                "reasoning": sql_query.reasoning,
                "safety_check": sql_query.safety_check
            }
        
        return {
            "success": True,
            "data": result,
            "message": "질문 분석 완료",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"질문 분석 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/schema")
async def update_schema(request: SchemaUpdateRequest):
    """데이터베이스 스키마 업데이트"""
    try:
        if not text_to_sql_converter:
            raise HTTPException(status_code=500, detail="서비스가 초기화되지 않았습니다")
        
        text_to_sql_converter.load_database_schema(request.schema_info)
        
        return {
            "success": True,
            "message": "스키마 업데이트 완료",
            "timestamp": datetime.now().isoformat(),
            "tables_loaded": len(request.schema_info.get("tables", {}))
        }
        
    except Exception as e:
        logger.error(f"스키마 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_current_schema():
    """현재 로드된 스키마 정보 반환"""
    try:
        if not text_to_sql_converter or not text_to_sql_converter.db_schema:
            return {
                "success": False,
                "message": "스키마가 로드되지 않았습니다"
            }
        
        schema = text_to_sql_converter.db_schema
        return {
            "success": True,
            "data": {
                "tables": schema.tables,
                "relationships": schema.relationships,
                "descriptions": schema.descriptions
            },
            "message": "현재 스키마 정보",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"스키마 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8012, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto reload")
    
    args = parser.parse_args()
    
    logger.info(f"Text-to-SQL RAG 서비스 시작: {args.host}:{args.port}")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )