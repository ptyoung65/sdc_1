"""
Full API with PostgreSQL database connection
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import os
import google.generativeai as genai
from dotenv import load_dotenv
from database import DatabaseService

# .env 파일 로드
load_dotenv()

app = FastAPI(title="SDC Backend - Full", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database service
db_service = DatabaseService()

# Gemini AI 초기화
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')  # 올바른 모델명 사용
    print("✅ Gemini API initialized successfully")
else:
    gemini_model = None
    print("⚠️ GEMINI_API_KEY not found. Using mock responses.")

# Models
class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = "gemini"
    use_rag: Optional[bool] = False
    user_id: Optional[str] = "default_user"
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    success: bool
    response: str
    provider: Optional[str] = None
    sources: Optional[List[Dict]] = None
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None

class RatingRequest(BaseModel):
    message_id: str
    user_id: str
    rating: int
    feedback: Optional[str] = None

# AI 응답 생성 함수
async def generate_ai_response(message: str, provider: str = "gemini") -> str:
    """Generate AI response using the specified provider"""
    try:
        if provider == "gemini" and gemini_model:
            response = gemini_model.generate_content(message)
            return response.text
        else:
            # Fallback to mock response
            return f"안녕하세요! 메시지 '{message}'에 대한 답변입니다. (사용 모델: {provider})"
    except Exception as e:
        print(f"AI 응답 생성 오류: {str(e)}")
        return f"죄송합니다. AI 응답 생성 중 오류가 발생했습니다: {str(e)}"

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    success = await db_service.initialize()
    if success:
        print("✅ Database initialized successfully")
    else:
        print("❌ Failed to initialize database")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "SDC Backend API with PostgreSQL is running",
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected" if db_service.pool else "disconnected"
    }

@app.get("/api/v1/providers")
async def get_providers():
    """사용 가능한 LLM 제공자 목록 반환"""
    return {
        "providers": [
            {
                "name": "gemini",
                "display_name": "Google Gemini",
                "available": bool(os.getenv("GEMINI_API_KEY")),
                "models": ["gemini-pro"]
            },
            {
                "name": "claude",
                "display_name": "Anthropic Claude", 
                "available": bool(os.getenv("ANTHROPIC_API_KEY")),
                "models": ["claude-3-sonnet"]
            }
        ]
    }

@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """채팅 엔드포인트 - 데이터베이스에 저장"""
    try:
        # 사용자 생성/가져오기
        user_id = await db_service.get_or_create_user(request.user_id or "default_user")
        if not user_id:
            raise HTTPException(status_code=500, detail="Failed to create user")
        
        # 대화 생성/가져오기
        conversation_id = request.conversation_id
        if not conversation_id:
            conversation_id = await db_service.create_conversation(user_id, "New Chat")
            if not conversation_id:
                raise HTTPException(status_code=500, detail="Failed to create conversation")
        
        # 사용자 메시지 저장
        user_message_id = await db_service.save_message(
            conversation_id=conversation_id,
            role="user",
            content=request.message,
            metadata={"provider": request.provider}
        )
        
        # AI 응답 생성
        ai_response = await generate_ai_response(request.message, request.provider)
        
        # AI 응답 저장
        ai_message_id = await db_service.save_message(
            conversation_id=conversation_id,
            role="assistant", 
            content=ai_response,
            metadata={"provider": request.provider, "model": "gemini-pro"}
        )
        
        return ChatResponse(
            success=True,
            response=ai_response,
            provider=request.provider,
            message_id=ai_message_id,
            conversation_id=conversation_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/rate")
async def rate_message(request: RatingRequest):
    """메시지 평가"""
    try:
        if not 1 <= request.rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Convert user_id string to actual UUID if needed
        user_uuid = await db_service.get_or_create_user(request.user_id)
        if not user_uuid:
            raise HTTPException(status_code=500, detail="Failed to get or create user")
        
        success = await db_service.rate_message(
            message_id=request.message_id,
            user_id=user_uuid,
            rating=request.rating,
            feedback=request.feedback
        )
        
        if success:
            return {"success": True, "message": "평가가 저장되었습니다"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save rating")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/conversations/{user_id}")
async def get_user_conversations(user_id: str, limit: int = 50, offset: int = 0):
    """사용자의 대화 목록 조회 (페이지네이션 지원)"""
    try:
        # Convert user_id string to actual UUID if needed
        user_uuid = await db_service.get_or_create_user(user_id)
        if not user_uuid:
            raise HTTPException(status_code=500, detail="Failed to get or create user")
        
        conversations = await db_service.get_conversations(user_uuid, limit, offset)
        total_count = await db_service.get_conversations_count(user_uuid)
        
        return {
            "success": True,
            "data": conversations,
            "total": total_count,
            "limit": limit,
            "offset": offset
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

@app.get("/api/v1/database/status")
async def database_status():
    """데이터베이스 상태 확인"""
    try:
        if not db_service.pool:
            return {"status": "disconnected", "message": "Database not initialized"}
        
        # Test query
        async with db_service.pool.acquire() as conn:
            result = await conn.fetchval("SELECT COUNT(*) FROM users")
            
        return {
            "status": "connected",
            "message": "Database is healthy",
            "user_count": result
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Database error: {str(e)}"
        }

@app.get("/health")
async def health_check():
    """상세 Health check"""
    return {
        "status": "ok",
        "database": "connected" if db_service.pool else "disconnected",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)