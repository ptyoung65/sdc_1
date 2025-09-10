from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError
)
from app.core.logging import logger
from app.services.document import DocumentService
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentDetailResponse,
    DocumentUpdate,
    DocumentListResponse,
    DocumentSearchRequest,
    DocumentStatsResponse,
    DocumentStats
)
from app.schemas.common import BaseResponse, create_success_response
from app.api.dependencies import (
    get_current_active_user,
    pagination_standard
)


router = APIRouter()


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    query: Optional[str] = Query(None, description="Search query"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    is_processed: Optional[bool] = Query(None, description="Filter by processing status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    min_size: Optional[int] = Query(None, description="Minimum file size in bytes"),
    max_size: Optional[int] = Query(None, description="Maximum file size in bytes"),
    pagination: tuple[int, int] = Depends(pagination_standard),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's documents"""
    try:
        page, limit = pagination
        document_service = DocumentService(db)
        
        # Build search parameters
        search_params = DocumentSearchRequest(
            query=query,
            content_type=content_type,
            is_processed=is_processed,
            tags=tags.split(',') if tags else None,
            min_size=min_size,
            max_size=max_size
        )
        
        documents, pagination_meta = await document_service.get_documents(
            user_id=current_user.id,
            page=page,
            limit=limit,
            search_params=search_params
        )
        
        document_responses = [
            DocumentResponse.model_validate(doc) for doc in documents
        ]
        
        return DocumentListResponse(
            success=True,
            message="문서 목록을 조회했습니다",
            items=document_responses,
            pagination=pagination_meta
        )
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 목록 조회 중 오류가 발생했습니다"
        )


@router.post("", response_model=DocumentDetailResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload new document"""
    try:
        document_service = DocumentService(db)
        
        # Parse tags
        tag_list = tags.split(',') if tags else None
        if tag_list:
            tag_list = [tag.strip() for tag in tag_list if tag.strip()]
        
        # Upload document
        document = await document_service.upload_document(
            user_id=current_user.id,
            file=file.file,
            filename=file.filename or "unnamed_file",
            content_type=file.content_type,
            title=title,
            description=description,
            tags=tag_list
        )
        
        return DocumentDetailResponse(
            success=True,
            message="문서가 업로드되었습니다",
            data=DocumentResponse.model_validate(document)
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Upload document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 업로드 중 오류가 발생했습니다"
        )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document by ID"""
    try:
        document_service = DocumentService(db)
        
        document = await document_service.get_document_by_id(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문서를 찾을 수 없습니다"
            )
        
        return DocumentDetailResponse(
            success=True,
            message="문서를 조회했습니다",
            data=DocumentResponse.model_validate(document)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 조회 중 오류가 발생했습니다"
        )


@router.put("/{document_id}", response_model=DocumentDetailResponse)
async def update_document(
    document_id: str,
    updates: DocumentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update document metadata"""
    try:
        document_service = DocumentService(db)
        
        updated_document = await document_service.update_document(
            document_id=document_id,
            updates=updates,
            user_id=current_user.id
        )
        
        return DocumentDetailResponse(
            success=True,
            message="문서가 업데이트되었습니다",
            data=DocumentResponse.model_validate(updated_document)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Update document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 업데이트 중 오류가 발생했습니다"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    soft_delete: bool = Query(True, description="Soft delete (default) or hard delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete document"""
    try:
        document_service = DocumentService(db)
        
        await document_service.delete_document(
            document_id=document_id,
            user_id=current_user.id,
            soft_delete=soft_delete
        )
        
        return create_success_response(
            message="문서가 삭제되었습니다"
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 삭제 중 오류가 발생했습니다"
        )


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Download document file"""
    try:
        document_service = DocumentService(db)
        
        document = await document_service.get_document_by_id(
            document_id=document_id,
            user_id=current_user.id
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="문서를 찾을 수 없습니다"
            )
        
        file_content = await document_service.get_document_content(
            document_id=document_id,
            user_id=current_user.id
        )
        
        def generate():
            yield file_content
        
        return StreamingResponse(
            generate(),
            media_type=document.content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename=\"{document.filename}\"",
                "Content-Length": str(document.file_size)
            }
        )
        
    except HTTPException:
        raise
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Download document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 다운로드 중 오류가 발생했습니다"
        )


@router.post("/{document_id}/process", response_model=DocumentDetailResponse)
async def process_document(
    document_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Process document for search indexing"""
    try:
        document_service = DocumentService(db)
        
        processed_document = await document_service.process_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        return DocumentDetailResponse(
            success=True,
            message="문서 처리가 완료되었습니다",
            data=DocumentResponse.model_validate(processed_document)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Process document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 처리 중 오류가 발생했습니다"
        )


@router.get("/search/content", response_model=DocumentListResponse)
async def search_documents_by_content(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search documents by content"""
    try:
        document_service = DocumentService(db)
        
        documents = await document_service.search_documents_by_content(
            user_id=current_user.id,
            query=query,
            limit=limit
        )
        
        document_responses = [
            DocumentResponse.model_validate(doc) for doc in documents
        ]
        
        return DocumentListResponse(
            success=True,
            message=f"'{query}' 콘텐츠 검색 결과입니다",
            items=document_responses,
            total_count=len(document_responses),
            has_more=len(document_responses) >= limit
        )
        
    except Exception as e:
        logger.error(f"Search documents by content error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 콘텐츠 검색 중 오류가 발생했습니다"
        )


@router.get("/stats/overview", response_model=DocumentStatsResponse)
async def get_document_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get document statistics for current user"""
    try:
        document_service = DocumentService(db)
        stats = await document_service.get_document_statistics(current_user.id)
        
        return DocumentStatsResponse(
            success=True,
            message="문서 통계를 조회했습니다",
            data=DocumentStats(**stats)
        )
        
    except Exception as e:
        logger.error(f"Get document statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 통계 조회 중 오류가 발생했습니다"
        )