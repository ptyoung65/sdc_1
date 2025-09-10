from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError
)
from app.core.logging import logger
from app.services.chunk import ChunkService
from app.models.user import User
from app.schemas.chunk import (
    ChunkResponse,
    ChunkDetailResponse,
    ChunkUpdate,
    ChunkListResponse,
    ChunkSearchRequest,
    ChunkStatsResponse,
    ChunkStats,
    SimilaritySearchRequest,
    SimilaritySearchResponse,
    BatchEmbeddingResponse
)
from app.schemas.common import BaseResponse, create_success_response
from app.api.dependencies import (
    get_current_active_user,
    pagination_standard
)


router = APIRouter()


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
async def list_chunks_by_document(
    document_id: str,
    pagination: tuple[int, int] = Depends(pagination_standard),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chunks from a specific document"""
    try:
        page, limit = pagination
        chunk_service = ChunkService(db)
        
        chunks, pagination_meta = await chunk_service.get_chunks_by_document(
            document_id=document_id,
            user_id=current_user.id,
            page=page,
            limit=limit
        )
        
        chunk_responses = [
            ChunkResponse.model_validate(chunk) for chunk in chunks
        ]
        
        return ChunkListResponse(
            success=True,
            message="문서의 청크를 조회했습니다",
            items=chunk_responses,
            pagination=pagination_meta
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"List chunks by document error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/search", response_model=ChunkListResponse)
async def search_chunks(
    query: Optional[str] = Query(None, description="Search query"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    min_length: Optional[int] = Query(None, description="Minimum content length"),
    max_length: Optional[int] = Query(None, description="Maximum content length"),
    has_embeddings: Optional[bool] = Query(None, description="Filter by embedding status"),
    pagination: tuple[int, int] = Depends(pagination_standard),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search chunks with filters"""
    try:
        page, limit = pagination
        chunk_service = ChunkService(db)
        
        # Build search parameters
        search_params = ChunkSearchRequest(
            query=query,
            document_id=document_id,
            min_length=min_length,
            max_length=max_length,
            has_embeddings=has_embeddings
        )
        
        chunks, pagination_meta = await chunk_service.search_chunks(
            user_id=current_user.id,
            search_params=search_params,
            page=page,
            limit=limit
        )
        
        chunk_responses = [
            ChunkResponse.model_validate(chunk) for chunk in chunks
        ]
        
        return ChunkListResponse(
            success=True,
            message="청크 검색 결과입니다",
            items=chunk_responses,
            pagination=pagination_meta
        )
        
    except Exception as e:
        logger.error(f"Search chunks error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 검색 중 오류가 발생했습니다"
        )


@router.get("/{chunk_id}", response_model=ChunkDetailResponse)
async def get_chunk(
    chunk_id: str,
    include_context: bool = Query(False, description="Include surrounding chunks for context"),
    context_size: int = Query(2, description="Number of chunks before and after for context"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chunk by ID with optional context"""
    try:
        chunk_service = ChunkService(db)
        
        if include_context:
            chunks = await chunk_service.get_chunk_context(
                chunk_id=chunk_id,
                user_id=current_user.id,
                context_size=context_size
            )
            
            chunk_responses = [
                ChunkResponse.model_validate(chunk) for chunk in chunks
            ]
            
            return ChunkDetailResponse(
                success=True,
                message="청크와 컨텍스트를 조회했습니다",
                data=chunk_responses
            )
        else:
            chunk = await chunk_service.get_chunk_by_id(
                chunk_id=chunk_id,
                user_id=current_user.id
            )
            
            if not chunk:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="청크를 찾을 수 없습니다"
                )
            
            return ChunkDetailResponse(
                success=True,
                message="청크를 조회했습니다",
                data=[ChunkResponse.model_validate(chunk)]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get chunk error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 조회 중 오류가 발생했습니다"
        )


@router.put("/{chunk_id}", response_model=ChunkDetailResponse)
async def update_chunk(
    chunk_id: str,
    updates: ChunkUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update chunk content or metadata"""
    try:
        chunk_service = ChunkService(db)
        
        updated_chunk = await chunk_service.update_chunk(
            chunk_id=chunk_id,
            updates=updates,
            user_id=current_user.id
        )
        
        return ChunkDetailResponse(
            success=True,
            message="청크가 업데이트되었습니다",
            data=[ChunkResponse.model_validate(updated_chunk)]
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="청크를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Update chunk error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 업데이트 중 오류가 발생했습니다"
        )


@router.delete("/{chunk_id}")
async def delete_chunk(
    chunk_id: str,
    soft_delete: bool = Query(True, description="Soft delete (default) or hard delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete chunk"""
    try:
        chunk_service = ChunkService(db)
        
        await chunk_service.delete_chunk(
            chunk_id=chunk_id,
            user_id=current_user.id,
            soft_delete=soft_delete
        )
        
        return create_success_response(
            message="청크가 삭제되었습니다"
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="청크를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Delete chunk error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 삭제 중 오류가 발생했습니다"
        )


@router.post("/{chunk_id}/embeddings", response_model=ChunkDetailResponse)
async def create_chunk_embeddings(
    chunk_id: str,
    embedding_model: str = Query("mock-embedding-model", description="Embedding model to use"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create embeddings for a chunk"""
    try:
        chunk_service = ChunkService(db)
        
        chunk_with_embeddings = await chunk_service.create_embeddings(
            chunk_id=chunk_id,
            user_id=current_user.id,
            embedding_model=embedding_model
        )
        
        return ChunkDetailResponse(
            success=True,
            message="청크 임베딩이 생성되었습니다",
            data=[ChunkResponse.model_validate(chunk_with_embeddings)]
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="청크를 찾을 수 없습니다"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create chunk embeddings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="임베딩 생성 중 오류가 발생했습니다"
        )


@router.post("/embeddings/batch", response_model=BatchEmbeddingResponse)
async def batch_create_embeddings(
    document_id: Optional[str] = Query(None, description="Limit to specific document"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of chunks to process"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create embeddings for multiple chunks in batch"""
    try:
        chunk_service = ChunkService(db)
        
        result = await chunk_service.batch_create_embeddings(
            user_id=current_user.id,
            document_id=document_id,
            limit=limit
        )
        
        return BatchEmbeddingResponse(
            success=True,
            message=f"{result['processed_count']}개 청크의 임베딩이 생성되었습니다",
            processed_count=result['processed_count'],
            failed_count=result['failed_count'],
            total_requested=result['total_requested']
        )
        
    except Exception as e:
        logger.error(f"Batch create embeddings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="배치 임베딩 생성 중 오류가 발생했습니다"
        )


@router.post("/search/similarity", response_model=SimilaritySearchResponse)
async def similarity_search(
    search_request: SimilaritySearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Perform semantic similarity search using embeddings"""
    try:
        chunk_service = ChunkService(db)
        
        chunks = await chunk_service.similarity_search(
            user_id=current_user.id,
            query_text=search_request.query,
            limit=search_request.limit or 10,
            document_id=search_request.document_id,
            similarity_threshold=search_request.similarity_threshold or 0.5
        )
        
        # Convert chunks to response format with similarity scores
        chunk_results = []
        for chunk in chunks:
            chunk_response = ChunkResponse.model_validate(chunk)
            # Add similarity score from mock implementation
            score = getattr(chunk, '_similarity_score', 0.0)
            chunk_results.append({
                "chunk": chunk_response,
                "similarity_score": score
            })
        
        return SimilaritySearchResponse(
            success=True,
            message=f"'{search_request.query}' 유사도 검색 결과입니다",
            results=chunk_results,
            total_count=len(chunk_results)
        )
        
    except Exception as e:
        logger.error(f"Similarity search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="유사도 검색 중 오류가 발생했습니다"
        )


@router.get("/stats/overview", response_model=ChunkStatsResponse)
async def get_chunk_statistics(
    document_id: Optional[str] = Query(None, description="Limit stats to specific document"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chunk statistics"""
    try:
        chunk_service = ChunkService(db)
        
        stats = await chunk_service.get_chunk_statistics(
            user_id=current_user.id,
            document_id=document_id
        )
        
        return ChunkStatsResponse(
            success=True,
            message="청크 통계를 조회했습니다",
            data=ChunkStats(**stats)
        )
        
    except Exception as e:
        logger.error(f"Get chunk statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 통계 조회 중 오류가 발생했습니다"
        )