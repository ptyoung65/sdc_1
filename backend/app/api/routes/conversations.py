from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    InsufficientPermissionsError,
    ValidationError
)
from app.core.logging import logger
from app.services.conversation import ConversationService
from app.models.user import User
from app.schemas.conversation import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationCreateRequest,
    ConversationUpdate,
    ConversationListResponse,
    ConversationSearchRequest,
    ConversationStatsResponse,
    ConversationStats
)
from app.schemas.common import BaseResponse, PaginationMeta, create_success_response
from app.api.dependencies import (
    get_current_active_user,
    pagination_standard,
    get_request_info
)


router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    query: Optional[str] = Query(None, description="Search query"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    tags: Optional[str] = Query(None, description="Comma-separated tags to filter by"),
    pagination: tuple[int, int] = Depends(pagination_standard),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversations"""
    try:
        page, limit = pagination
        conversation_service = ConversationService(db)
        
        # Build search parameters
        search_params = ConversationSearchRequest(
            query=query,
            is_archived=is_archived,
            is_pinned=is_pinned,
            tags=tags.split(',') if tags else None
        )
        
        conversations, pagination_meta = await conversation_service.get_conversations(
            user_id=current_user.id,
            page=page,
            limit=limit,
            search_params=search_params
        )
        
        conversation_responses = [
            ConversationResponse.model_validate(conv) for conv in conversations
        ]
        
        return ConversationListResponse(
            success=True,
            message="대화 목록을 조회했습니다",
            items=conversation_responses,
            pagination=pagination_meta
        )
        
    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 목록 조회 중 오류가 발생했습니다"
        )


@router.post("", response_model=ConversationDetailResponse)
async def create_conversation(
    conversation_data: ConversationCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new conversation"""
    try:
        conversation_service = ConversationService(db)
        
        conversation = await conversation_service.create_conversation(
            user_id=current_user.id,
            title=conversation_data.title,
            system_prompt=conversation_data.system_prompt,
            metadata=conversation_data.metadata
        )
        
        return ConversationDetailResponse(
            success=True,
            message="새 대화가 생성되었습니다",
            data=ConversationResponse.model_validate(conversation)
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 생성 중 오류가 발생했습니다"
        )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    include_messages: bool = Query(True, description="Include recent messages"),
    message_limit: int = Query(50, description="Number of recent messages to include"),
    before_message_id: Optional[str] = Query(None, description="Get messages before this ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation by ID"""
    try:
        conversation_service = ConversationService(db)
        
        if include_messages:
            conversation = await conversation_service.get_conversation_with_messages(
                conversation_id=conversation_id,
                user_id=current_user.id,
                limit=message_limit,
                before_message_id=before_message_id
            )
        else:
            conversation = await conversation_service.get_conversation_by_id(
                conversation_id=conversation_id,
                user_id=current_user.id
            )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="대화를 찾을 수 없습니다"
            )
        
        return ConversationDetailResponse(
            success=True,
            message="대화를 조회했습니다",
            data=ConversationResponse.model_validate(conversation)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 조회 중 오류가 발생했습니다"
        )


@router.put("/{conversation_id}", response_model=ConversationDetailResponse)
async def update_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation"""
    try:
        conversation_service = ConversationService(db)
        
        updated_conversation = await conversation_service.update_conversation(
            conversation_id=conversation_id,
            updates=updates,
            user_id=current_user.id
        )
        
        return ConversationDetailResponse(
            success=True,
            message="대화가 업데이트되었습니다",
            data=ConversationResponse.model_validate(updated_conversation)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Update conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 업데이트 중 오류가 발생했습니다"
        )


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    soft_delete: bool = Query(True, description="Soft delete (default) or hard delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete conversation"""
    try:
        conversation_service = ConversationService(db)
        
        await conversation_service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            soft_delete=soft_delete
        )
        
        return create_success_response(
            message="대화가 삭제되었습니다"
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 삭제 중 오류가 발생했습니다"
        )


@router.post("/{conversation_id}/archive", response_model=ConversationDetailResponse)
async def archive_conversation(
    conversation_id: str,
    archive: bool = Query(True, description="Archive (true) or unarchive (false)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Archive or unarchive conversation"""
    try:
        conversation_service = ConversationService(db)
        
        updated_conversation = await conversation_service.archive_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            archive=archive
        )
        
        action = "보관" if archive else "보관 해제"
        return ConversationDetailResponse(
            success=True,
            message=f"대화가 {action}되었습니다",
            data=ConversationResponse.model_validate(updated_conversation)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Archive conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 보관 처리 중 오류가 발생했습니다"
        )


@router.post("/{conversation_id}/pin", response_model=ConversationDetailResponse)
async def pin_conversation(
    conversation_id: str,
    pin: bool = Query(True, description="Pin (true) or unpin (false)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Pin or unpin conversation"""
    try:
        conversation_service = ConversationService(db)
        
        updated_conversation = await conversation_service.pin_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            pin=pin
        )
        
        action = "고정" if pin else "고정 해제"
        return ConversationDetailResponse(
            success=True,
            message=f"대화가 {action}되었습니다",
            data=ConversationResponse.model_validate(updated_conversation)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Pin conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 고정 처리 중 오류가 발생했습니다"
        )


@router.put("/{conversation_id}/title", response_model=ConversationDetailResponse)
async def update_conversation_title(
    conversation_id: str,
    auto_generate: bool = Query(False, description="Auto-generate title from messages"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update conversation title"""
    try:
        conversation_service = ConversationService(db)
        
        updated_conversation = await conversation_service.update_conversation_title(
            conversation_id=conversation_id,
            user_id=current_user.id,
            auto_generate=auto_generate
        )
        
        return ConversationDetailResponse(
            success=True,
            message="대화 제목이 업데이트되었습니다",
            data=ConversationResponse.model_validate(updated_conversation)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Update conversation title error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 제목 업데이트 중 오류가 발생했습니다"
        )


@router.get("/stats/overview", response_model=ConversationStatsResponse)
async def get_conversation_statistics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get conversation statistics for current user"""
    try:
        conversation_service = ConversationService(db)
        stats = await conversation_service.get_conversation_statistics(current_user.id)
        
        return ConversationStatsResponse(
            success=True,
            message="대화 통계를 조회했습니다",
            data=ConversationStats(**stats)
        )
        
    except Exception as e:
        logger.error(f"Get conversation statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대화 통계 조회 중 오류가 발생했습니다"
        )