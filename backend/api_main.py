from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from backend.llm_service import LLMService
from backend.vector_service import VectorService
import asyncio
import hashlib

# .env 파일 로드
load_dotenv()

app = FastAPI(title="SDC Backend with LLM", version="0.2.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
llm_service = LLMService()
vector_service = VectorService()

# 데이터베이스 서비스 import
from backend.database import db_service

# 서비스 초기화 (백그라운드에서 실행)
@app.on_event("startup")
async def startup_event():
    await db_service.initialize()
    vector_service.initialize()

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = None
    system_prompt: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None
    use_rag: Optional[bool] = False
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    provider: Optional[str] = None
    model: Optional[str] = None
    error: Optional[str] = None
    tokens: Optional[Dict] = None
    sources: Optional[List[Dict]] = None
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None

class RatingRequest(BaseModel):
    message_id: str
    user_id: str
    rating: int  # 1-5
    feedback: Optional[str] = None

@app.get("/")
async def root():
    return {
        "message": "SDC Backend with LLM is running!",
        "status": "healthy",
        "version": "0.2.0"
    }

@app.get("/health")
async def health_check():
    providers = llm_service.get_available_providers()
    return {
        "status": "healthy",
        "service": "sdc-backend",
        "llm_providers": providers
    }

@app.get("/api/v1/providers")
async def get_providers():
    """사용 가능한 LLM 제공자 목록 반환"""
    return {
        "providers": llm_service.get_available_providers()
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """LLM과 대화 (RAG 지원, 채팅 기록 저장)"""
    try:
        # 사용자 ID 처리 (기본값 사용)
        user_id = request.user_id or "default_user"
        user_id = await db_service.get_or_create_user(user_id)
        
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # 대화 ID 처리
        conversation_id = request.conversation_id
        if not conversation_id:
            # 새 대화 생성
            conversation_title = request.message[:50] + ("..." if len(request.message) > 50 else "")
            conversation_id = await db_service.create_conversation(user_id, conversation_title)
            
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        # 사용자 메시지 저장
        user_message_id = await db_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata={
                "provider": request.provider,
                "use_rag": request.use_rag
            }
        )
        
        # RAG 모드인 경우 벡터 검색 수행
        if request.use_rag:
            # 관련 문서 검색
            search_results = vector_service.search_similar(request.message, limit=3)
            
            if search_results:
                # RAG 기반 응답 생성
                result = await llm_service.generate_rag_response(
                    message=request.message,
                    context_chunks=search_results,
                    provider=request.provider,
                    system_prompt=request.system_prompt,
                    conversation_history=request.conversation_history
                )
            else:
                # 관련 문서가 없으면 일반 응답
                result = await llm_service.generate_response(
                    message=request.message,
                    provider=request.provider,
                    system_prompt=request.system_prompt,
                    conversation_history=request.conversation_history
                )
                result["sources"] = []
        else:
            # 일반 LLM 응답 생성
            result = await llm_service.generate_response(
                message=request.message,
                provider=request.provider,
                system_prompt=request.system_prompt,
                conversation_history=request.conversation_history
            )
        
        # AI 응답 저장
        assistant_message_id = await db_service.save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=result.get("response", ""),
            metadata={
                "provider": result.get("provider"),
                "model": result.get("model"),
                "tokens": result.get("tokens")
            },
            sources=result.get("sources", [])
        )
        
        return ChatResponse(
            success=result.get("success", False),
            response=result.get("response", ""),
            provider=result.get("provider"),
            model=result.get("model"),
            error=result.get("error"),
            tokens=result.get("tokens"),
            sources=result.get("sources"),
            message_id=assistant_message_id,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/stream")
async def chat_stream(request: ChatRequest):
    """스트리밍 응답 (향후 구현)"""
    return {
        "message": "Streaming not yet implemented",
        "fallback": await chat(request)
    }

# Document upload endpoint for RAG
@app.post("/api/v1/documents")
async def upload_document(file: UploadFile = File(...)):
    """문서 업로드 및 벡터화"""
    try:
        # Read file content
        content = await file.read()
        filename = file.filename or "unnamed_file"
        text_content = content.decode('utf-8')
        
        # Generate document ID
        document_id = hashlib.md5(f"{filename}_{len(content)}".encode()).hexdigest()[:16]
        
        # Metadata
        metadata = {
            "filename": filename,
            "content_type": file.content_type,
            "size": len(content),
            "upload_timestamp": asyncio.get_event_loop().time()
        }
        
        # Add to vector database
        vectorization_success = vector_service.add_document(
            document_id=document_id,
            content=text_content,
            metadata=metadata
        )
        
        return {
            "success": True,
            "message": "문서가 업로드되고 벡터화되었습니다" if vectorization_success else "문서가 업로드되었으나 벡터화에 실패했습니다",
            "data": {
                "document_id": document_id,
                "filename": filename,
                "size": len(content),
                "content_type": file.content_type,
                "status": "vectorized" if vectorization_success else "uploaded_only",
                "vectorization_success": vectorization_success
            }
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="텍스트 파일만 지원됩니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}")

# RAG search endpoint
@app.get("/api/v1/search")
async def search_documents(query: str):
    """RAG 기반 문서 검색"""
    try:
        results = vector_service.search_similar(query, limit=5)
        
        return {
            "success": True,
            "message": "검색 완료",
            "data": {
                "query": query,
                "results": results,
                "total": len(results)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/v1/documents")
async def list_documents():
    """문서 목록 조회 및 벡터 DB 통계"""
    try:
        stats = vector_service.get_collection_stats()
        
        return {
            "success": True,
            "message": "문서 통계 조회 완료",
            "data": {
                "statistics": stats,
                "note": "개별 문서 목록 기능은 PostgreSQL 연동 후 구현됩니다"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": "통계 조회 실패",
            "data": {
                "error": str(e),
                "note": "문서 저장 기능은 데이터베이스 연동 후 구현됩니다"
            }
        }

# Chat history and rating endpoints
@app.post("/api/v1/chat/rate")
async def rate_message(request: RatingRequest):
    """메시지 평가 (1-5점)"""
    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        success = await db_service.rate_message(
            message_id=request.message_id,
            user_id=request.user_id,
            rating=request.rating,
            feedback=request.feedback
        )
        
        if success:
            return {
                "success": True,
                "message": "평가가 저장되었습니다"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save rating")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversations/{user_id}")
async def get_user_conversations(user_id: str, limit: int = 50):
    """사용자의 대화 목록 조회"""
    try:
        conversations = await db_service.get_conversations(user_id, limit)
        
        return {
            "success": True,
            "data": conversations,
            "total": len(conversations)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """대화의 메시지 목록 조회"""
    try:
        messages = await db_service.get_conversation_messages(conversation_id)
        
        return {
            "success": True,
            "data": messages,
            "total": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user_id: str):
    """대화 삭제"""
    try:
        success = await db_service.delete_conversation(conversation_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": "대화가 삭제되었습니다"
            }
        else:
            raise HTTPException(status_code=404, detail="Conversation not found or access denied")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/messages/{message_id}/rating/{user_id}")
async def get_message_rating(message_id: str, user_id: str):
    """특정 메시지의 사용자 평가 조회"""
    try:
        rating = await db_service.get_message_rating(message_id, user_id)
        
        return {
            "success": True,
            "data": rating
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    # Gemini API 키 확인
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and gemini_key != "YOUR_GEMINI_API_KEY_HERE":
        print(f"✅ Gemini API Key configured")
    else:
        print("⚠️  Gemini API Key not configured. Please set GEMINI_API_KEY in .env file")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)