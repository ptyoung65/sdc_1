from fastapi import APIRouter

from app.api.routes import auth, users, conversations, messages, documents, chunks, ai, search, indexing

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# User management routes
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Conversation routes
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])

# Message routes (includes both conversation-specific and global message routes)
api_router.include_router(messages.router, prefix="", tags=["messages"])

# Document routes
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])

# Chunk routes
api_router.include_router(chunks.router, prefix="/chunks", tags=["chunks"])

# AI services routes
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

# Search services routes
api_router.include_router(search.router, prefix="/search", tags=["search"])

# Indexing services routes
api_router.include_router(indexing.router, prefix="/indexing", tags=["indexing"])

__all__ = ["api_router"]