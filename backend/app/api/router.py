from fastapi import APIRouter
from app.api.routes import auth, users, conversations, messages, documents, chunks

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["Conversations"])
api_router.include_router(messages.router, prefix="/messages", tags=["Messages"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(chunks.router, prefix="/chunks", tags=["Chunks"])