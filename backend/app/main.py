from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import engine, create_tables
from app.core.logging import setup_logging, logger
from app.api.routes import api_router
from app.core.exceptions import CustomHTTPException
from app.core.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    try:
        # Create database tables
        await create_tables()
        logger.info("Database tables created successfully")
        
        # Initialize services
        # TODO: Initialize AI services, vector databases, etc.
        logger.info("Services initialized successfully")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    if hasattr(engine, 'dispose'):
        await engine.dispose()
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description="Multi-LLM based conversational AI service with advanced RAG capabilities",
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Add middleware (order matters!)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Request ID for tracing
    app.add_middleware(RequestIDMiddleware)
    
    # Logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Rate limiting
    if settings.RATE_LIMIT_ENABLED:
        app.add_middleware(RateLimitMiddleware)
    
    # CORS middleware
    if settings.CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=settings.CORS_METHODS,
            allow_headers=settings.CORS_HEADERS,
        )
    
    # Trusted host middleware for production
    if not settings.DEBUG:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["localhost", "127.0.0.1"]  # Update for production
        )
    
    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Exception handlers
    setup_exception_handlers(app)
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    
    @app.get("/")
    async def root():
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "version": settings.APP_VERSION,
            "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG else "Documentation not available in production",
        }
    
    return app


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(CustomHTTPException)
    async def custom_http_exception_handler(request: Request, exc: CustomHTTPException):
        logger.error(
            f"Custom HTTP error: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                    "details": exc.details,
                    "timestamp": exc.timestamp.isoformat(),
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(
            f"HTTP error: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
            }
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(
            f"Validation error: {exc.errors()}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": exc.errors(),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception(
            f"Unhandled exception: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "exception_type": type(exc).__name__,
            }
        )
        
        # Don't expose internal errors in production
        error_message = str(exc) if settings.DEBUG else "Internal server error"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": error_message,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            }
        )


# Create the FastAPI application
app = create_application()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )