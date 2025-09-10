from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json
import asyncio

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    InsufficientPermissionsError,
    ValidationError
)
from app.core.logging import logger
from app.services.message import MessageService
from app.services.conversation import ConversationService
from app.models.user import User
from app.schemas.message import (
    MessageResponse,
    MessageDetailResponse,
    MessageCreate,
    MessageUpdate,
    MessageListResponse,
    MessageStatsResponse,
    MessageStats,
    MessageSearchRequest
)
from app.schemas.common import BaseResponse, create_success_response
from app.api.dependencies import (
    get_current_active_user,
    get_request_info
)


router = APIRouter()


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def list_messages(
    conversation_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of messages to retrieve"),
    before_message_id: Optional[str] = Query(None, description="Get messages before this ID"),
    after_message_id: Optional[str] = Query(None, description="Get messages after this ID"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get messages from conversation"""
    try:
        message_service = MessageService(db)
        
        messages = await message_service.get_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
            limit=limit,
            before_message_id=before_message_id,
            after_message_id=after_message_id
        )
        
        message_responses = [
            MessageResponse.model_validate(msg) for msg in messages
        ]
        
        return MessageListResponse(
            success=True,
            message="메시지를 조회했습니다",
            items=message_responses,
            total_count=len(message_responses),
            has_more=len(message_responses) >= limit
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"List messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 조회 중 오류가 발생했습니다"
        )


@router.post("/{conversation_id}/messages", response_model=MessageDetailResponse)
async def create_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new message in conversation"""
    try:
        message_service = MessageService(db)
        
        # Create user message
        user_message = await message_service.create_message(
            conversation_id=conversation_id,
            message_data=message_data,
            user_id=current_user.id
        )
        
        return MessageDetailResponse(
            success=True,
            message="메시지가 생성되었습니다",
            data=MessageResponse.model_validate(user_message)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 생성 중 오류가 발생했습니다"
        )


@router.post("/{conversation_id}/messages/stream")
async def create_message_with_stream(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Create message and stream AI response"""
    try:
        message_service = MessageService(db)
        
        # Create user message first
        user_message = await message_service.create_message(
            conversation_id=conversation_id,
            message_data=message_data,
            user_id=current_user.id
        )
        
        # Create assistant message for streaming response
        assistant_message_data = MessageCreate(
            role="assistant",
            content="",
            metadata={"status": "generating"},
            parent_message_id=user_message.id
        )
        
        assistant_message = await message_service.create_message(
            conversation_id=conversation_id,
            message_data=assistant_message_data,
            user_id=current_user.id
        )
        
        # Generate streaming response
        async def generate_response():
            try:
                # Initial response with user message
                yield f"data: {json.dumps({
                    'type': 'user_message',
                    'message': MessageResponse.model_validate(user_message).model_dump()
                })}\n\n"
                
                # Stream assistant response
                content_generator = message_service._mock_ai_response_generator(
                    user_message.content or ""
                )
                
                async for response_chunk in message_service.stream_message_response(
                    assistant_message, content_generator
                ):
                    yield f"data: {json.dumps(response_chunk)}\n\n"
                
                # Final assistant message
                await db.refresh(assistant_message)
                yield f"data: {json.dumps({
                    'type': 'assistant_message',
                    'message': MessageResponse.model_validate(assistant_message).model_dump()
                })}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Stream generation error: {e}")
                yield f"data: {json.dumps({
                    'type': 'error',
                    'error': str(e)
                })}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="대화를 찾을 수 없습니다"
        )
    except Exception as e:
        logger.error(f"Create streaming message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="스트리밍 메시지 생성 중 오류가 발생했습니다"
        )


@router.get("/messages/{message_id}", response_model=MessageDetailResponse)
async def get_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message by ID"""
    try:
        message_service = MessageService(db)
        
        message = await message_service.get_message_by_id(
            message_id=message_id,
            user_id=current_user.id
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="메시지를 찾을 수 없습니다"
            )
        
        return MessageDetailResponse(
            success=True,
            message="메시지를 조회했습니다",
            data=MessageResponse.model_validate(message)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 조회 중 오류가 발생했습니다"
        )


@router.put("/messages/{message_id}", response_model=MessageDetailResponse)
async def update_message(
    message_id: str,
    updates: MessageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update message"""
    try:
        message_service = MessageService(db)
        
        updated_message = await message_service.update_message(
            message_id=message_id,
            updates=updates,
            user_id=current_user.id
        )
        
        return MessageDetailResponse(
            success=True,
            message="메시지가 업데이트되었습니다",
            data=MessageResponse.model_validate(updated_message)
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="메시지를 찾을 수 없습니다"
        )
    except InsufficientPermissionsError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 업데이트 중 오류가 발생했습니다"
        )


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    soft_delete: bool = Query(True, description="Soft delete (default) or hard delete"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete message"""
    try:
        message_service = MessageService(db)
        
        await message_service.delete_message(
            message_id=message_id,
            user_id=current_user.id,
            soft_delete=soft_delete
        )
        
        return create_success_response(
            message="메시지가 삭제되었습니다"
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="메시지를 찾을 수 없습니다"
        )
    except InsufficientPermissionsError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Delete message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 삭제 중 오류가 발생했습니다"
        )


@router.post("/messages/{message_id}/regenerate")
async def regenerate_message(
    message_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate AI response for a message"""
    try:
        message_service = MessageService(db)
        
        # Create new regenerated message
        new_message = await message_service.regenerate_response(
            message_id=message_id,
            user_id=current_user.id
        )
        
        # Generate streaming response
        async def generate_response():
            try:
                # Get the original user message to use as context
                original_message = await message_service.get_message_by_id(
                    message_id, current_user.id
                )
                
                if not original_message or not original_message.parent_message_id:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Cannot find context message'})}\n\n"
                    return
                
                parent_message = await message_service.get_message_by_id(
                    original_message.parent_message_id, current_user.id
                )
                
                if not parent_message:
                    yield f"data: {json.dumps({'type': 'error', 'error': 'Cannot find parent message'})}\n\n"
                    return
                
                # Stream regenerated response
                content_generator = message_service._mock_ai_response_generator(
                    parent_message.content or ""
                )
                
                async for response_chunk in message_service.stream_message_response(
                    new_message, content_generator
                ):
                    yield f"data: {json.dumps(response_chunk)}\n\n"
                
                # Final regenerated message
                await db.refresh(new_message)
                yield f"data: {json.dumps({
                    'type': 'regenerated_message',
                    'message': MessageResponse.model_validate(new_message).model_dump()
                })}\n\n"
                
                yield "data: [DONE]\n\n"
                
            except Exception as e:
                logger.error(f"Regenerate stream error: {e}")
                yield f"data: {json.dumps({
                    'type': 'error',
                    'error': str(e)
                })}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="메시지를 찾을 수 없습니다"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Regenerate message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 재생성 중 오류가 발생했습니다"
        )


@router.get("/search", response_model=MessageListResponse)
async def search_messages(
    query: str = Query(..., min_length=1, description="Search query"),
    conversation_id: Optional[str] = Query(None, description="Limit search to specific conversation"),
    limit: int = Query(50, ge=1, le=100, description="Number of results to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Search messages by content"""
    try:
        message_service = MessageService(db)
        
        messages = await message_service.search_messages(
            user_id=current_user.id,
            query=query,
            conversation_id=conversation_id,
            limit=limit
        )
        
        message_responses = [
            MessageResponse.model_validate(msg) for msg in messages
        ]
        
        return MessageListResponse(
            success=True,
            message=f"'{query}' 검색 결과입니다",
            items=message_responses,
            total_count=len(message_responses),
            has_more=len(message_responses) >= limit
        )
        
    except Exception as e:
        logger.error(f"Search messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 검색 중 오류가 발생했습니다"
        )


@router.get("/{conversation_id}/messages/stats", response_model=MessageStatsResponse)
async def get_message_statistics(
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get message statistics"""
    try:
        message_service = MessageService(db)
        
        stats = await message_service.get_message_statistics(
            user_id=current_user.id,
            conversation_id=conversation_id
        )
        
        return MessageStatsResponse(
            success=True,
            message="메시지 통계를 조회했습니다",
            data=MessageStats(**stats)
        )
        
    except Exception as e:
        logger.error(f"Get message statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="메시지 통계 조회 중 오류가 발생했습니다"
        )