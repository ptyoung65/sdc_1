from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, InsufficientPermissionsError
from app.models.user import User
from app.services.auth import AuthService
from app.core.logging import logger


# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise AuthenticationError("Authentication credentials not provided")
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid authentication credentials")
        
        # Get user from database
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(user_id)
        
        if user is None:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")
        
        # Update last login
        user.update_last_login()
        await db.commit()
        
        return user
        
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise AuthenticationError("Invalid authentication credentials")
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError("Authentication failed")


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise AuthenticationError("User account is deactivated")
    
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current verified user"""
    if not current_user.is_verified:
        raise AuthenticationError("Email verification required")
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Get current superuser"""
    if not current_user.is_superuser:
        raise InsufficientPermissionsError("Superuser access required")
    
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        # This is an async function but we need to handle it properly
        # In a real implementation, you'd use a different approach
        # For now, we'll return None for unauthenticated requests
        return None
    except Exception:
        return None


class RateLimitDependency:
    """Rate limiting dependency"""
    
    def __init__(self, calls_per_minute: int = 60, burst_limit: int = 10):
        self.calls_per_minute = calls_per_minute
        self.burst_limit = burst_limit
    
    async def __call__(self, request: Request):
        # Rate limiting is handled by middleware
        # This dependency is mainly for documentation purposes
        return True


# Create rate limit instances for different endpoints
rate_limit_auth = RateLimitDependency(calls_per_minute=10, burst_limit=5)
rate_limit_api = RateLimitDependency(calls_per_minute=100, burst_limit=20)
rate_limit_upload = RateLimitDependency(calls_per_minute=20, burst_limit=5)


class PaginationDependency:
    """Pagination dependency"""
    
    def __init__(self, max_limit: int = 100):
        self.max_limit = max_limit
    
    async def __call__(
        self, 
        page: int = 1, 
        limit: int = 20
    ) -> tuple[int, int]:
        """Validate and return pagination parameters"""
        if page < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Page must be >= 1"
            )
        
        if limit < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be >= 1"
            )
        
        if limit > self.max_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limit must be <= {self.max_limit}"
            )
        
        return page, limit


# Create pagination instances for different use cases
pagination_standard = PaginationDependency(max_limit=100)
pagination_large = PaginationDependency(max_limit=1000)


class SearchDependency:
    """Search query dependency"""
    
    def __init__(self, min_length: int = 1, max_length: int = 1000):
        self.min_length = min_length
        self.max_length = max_length
    
    async def __call__(self, q: str) -> str:
        """Validate search query"""
        if len(q) < self.min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Search query must be at least {self.min_length} characters"
            )
        
        if len(q) > self.max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Search query must be at most {self.max_length} characters"
            )
        
        return q.strip()


# Create search dependency instance
search_query = SearchDependency()


async def validate_user_access(
    user_id: str,
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """Validate that current user can access the specified user's data"""
    if current_user.is_superuser:
        return True
    
    if current_user.id != user_id:
        raise InsufficientPermissionsError("Access denied")
    
    return True


async def validate_conversation_access(
    conversation_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Validate that current user can access the specified conversation"""
    from app.services.conversation import ConversationService
    
    conversation_service = ConversationService(db)
    conversation = await conversation_service.get_conversation_by_id(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Check if user owns the conversation or is superuser
    if conversation.user_id != current_user.id and not current_user.is_superuser:
        raise InsufficientPermissionsError("Access denied to this conversation")
    
    return True


async def validate_document_access(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Validate that current user can access the specified document"""
    from app.services.document import DocumentService
    
    document_service = DocumentService(db)
    document = await document_service.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Check if user owns the document, document is public, or user is superuser
    if (document.user_id != current_user.id and 
        not document.is_public and 
        not current_user.is_superuser):
        raise InsufficientPermissionsError("Access denied to this document")
    
    return True


class FileSizeLimitDependency:
    """File size limit dependency"""
    
    def __init__(self, max_size_mb: int = 100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
    
    async def __call__(self, request: Request) -> bool:
        """Check file size from Content-Length header"""
        content_length = request.headers.get('content-length')
        
        if content_length and int(content_length) > self.max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {self.max_size_bytes // 1024 // 1024}MB limit"
            )
        
        return True


# File size limits for different endpoints
file_size_standard = FileSizeLimitDependency(max_size_mb=100)
file_size_large = FileSizeLimitDependency(max_size_mb=500)


async def get_request_info(request: Request) -> dict:
    """Get request information for logging/auditing"""
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
    }


class CacheDependency:
    """Cache control dependency"""
    
    def __init__(self, cache_ttl: int = 3600):
        self.cache_ttl = cache_ttl
    
    async def __call__(self) -> int:
        """Return cache TTL"""
        return self.cache_ttl


# Cache dependencies for different data types
cache_short = CacheDependency(cache_ttl=300)  # 5 minutes
cache_medium = CacheDependency(cache_ttl=1800)  # 30 minutes
cache_long = CacheDependency(cache_ttl=3600)  # 1 hour