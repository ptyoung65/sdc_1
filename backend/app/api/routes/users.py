from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    InsufficientPermissionsError,
    ValidationError
)
from app.core.logging import logger
from app.services.user import UserService
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserProfile,
    UserUpdate,
    UserProfileUpdate,
    UserListResponse,
    UserDetailResponse,
    UserUpdateResponse,
    UserSearchRequest,
    UserStatsResponse,
    UserStats,
    AdminUserUpdate,
    AdminUserResponse,
    BulkUserAction,
    BulkUserActionResponse,
    UserPreferences,
    UserPreferencesResponse,
    UserQuotaResponse,
    UserQuotaInfo
)
from app.schemas.common import create_success_response, create_paginated_response
from app.api.dependencies import (
    get_current_active_user,
    get_current_superuser,
    validate_user_access,
    pagination_standard,
    search_query,
    get_request_info
)


router = APIRouter()


@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's detailed profile"""
    try:
        user_service = UserService(db)
        user_profile = await user_service.get_user_profile(current_user.id)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자 프로필을 찾을 수 없습니다"
            )
        
        return UserDetailResponse(
            success=True,
            message="프로필 조회가 완료되었습니다",
            data=UserProfile.model_validate(user_profile)
        )
        
    except Exception as e:
        logger.error(f"Get current user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 조회 중 오류가 발생했습니다"
        )


@router.put("/me", response_model=UserUpdateResponse)
async def update_current_user_profile(
    updates: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile"""
    try:
        user_service = UserService(db)
        
        # Check if email/username are available if being updated
        if updates.username and updates.username != current_user.username:
            if not await user_service.check_username_available(updates.username, current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="사용자명이 이미 사용 중입니다"
                )
        
        updated_user = await user_service.update_user(
            user_id=current_user.id,
            updates=updates,
            current_user_id=current_user.id
        )
        
        return UserUpdateResponse(
            success=True,
            message="프로필이 업데이트되었습니다",
            data=UserResponse.model_validate(updated_user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 업데이트 중 오류가 발생했습니다"
        )


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's preferences"""
    try:
        preferences = current_user.metadata or {}
        
        return UserPreferencesResponse(
            success=True,
            message="사용자 환경설정을 조회했습니다",
            data=UserPreferences(**preferences)
        )
        
    except Exception as e:
        logger.error(f"Get user preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="환경설정 조회 중 오류가 발생했습니다"
        )


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's preferences"""
    try:
        user_service = UserService(db)
        
        updated_user = await user_service.update_user_preferences(
            user_id=current_user.id,
            preferences=preferences.model_dump()
        )
        
        return UserPreferencesResponse(
            success=True,
            message="환경설정이 업데이트되었습니다",
            data=preferences
        )
        
    except Exception as e:
        logger.error(f"Update user preferences error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="환경설정 업데이트 중 오류가 발생했습니다"
        )


@router.get("/me/quota", response_model=UserQuotaResponse)
async def get_user_quota(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's quota information"""
    try:
        user_service = UserService(db)
        quota_info = await user_service.get_user_quota_info(current_user.id)
        
        return UserQuotaResponse(
            success=True,
            message="할당량 정보를 조회했습니다",
            data=UserQuotaInfo(**quota_info)
        )
        
    except Exception as e:
        logger.error(f"Get user quota error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="할당량 정보 조회 중 오류가 발생했습니다"
        )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(validate_user_access)
):
    """Get user by ID (own profile or admin)"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_profile(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다"
            )
        
        # Use admin response if current user is superuser
        if current_user.is_superuser:
            return UserDetailResponse(
                success=True,
                data=AdminUserResponse.model_validate(user)
            )
        else:
            return UserDetailResponse(
                success=True,
                data=UserProfile.model_validate(user)
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user by ID error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 조회 중 오류가 발생했습니다"
        )


# Admin-only routes
@router.get("", response_model=UserListResponse)
async def list_users(
    query: Optional[str] = Query(None, description="Search query"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verified status"),
    is_superuser: Optional[bool] = Query(None, description="Filter by superuser status"),
    pagination: tuple[int, int] = Depends(pagination_standard),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """List users (admin only)"""
    try:
        page, limit = pagination
        user_service = UserService(db)
        
        # Build search parameters
        search_params = UserSearchRequest(
            query=query,
            is_active=is_active,
            is_verified=is_verified,
            is_superuser=is_superuser
        )
        
        users, pagination_meta = await user_service.get_users(
            page=page,
            limit=limit,
            search_params=search_params
        )
        
        user_responses = [AdminUserResponse.model_validate(user) for user in users]
        
        return UserListResponse(
            success=True,
            message="사용자 목록을 조회했습니다",
            items=user_responses,
            pagination=pagination_meta
        )
        
    except Exception as e:
        logger.error(f"List users error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 목록 조회 중 오류가 발생했습니다"
        )


@router.put("/{user_id}", response_model=UserUpdateResponse)
async def admin_update_user(
    user_id: str,
    updates: AdminUserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Update user (admin only)"""
    try:
        user_service = UserService(db)
        
        updated_user = await user_service.admin_update_user(
            user_id=user_id,
            updates=updates,
            admin_user_id=current_user.id
        )
        
        return UserUpdateResponse(
            success=True,
            message="사용자 정보가 업데이트되었습니다",
            data=AdminUserResponse.model_validate(updated_user)
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Admin update user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 정보 업데이트 중 오류가 발생했습니다"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    soft_delete: bool = Query(True, description="Soft delete (default) or hard delete"),
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Delete user (admin only)"""
    try:
        user_service = UserService(db)
        
        await user_service.delete_user(
            user_id=user_id,
            admin_user_id=current_user.id,
            soft_delete=soft_delete
        )
        
        return create_success_response(
            message="사용자 계정이 삭제되었습니다"
        )
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Delete user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 삭제 중 오류가 발생했습니다"
        )


@router.post("/bulk-action", response_model=BulkUserActionResponse)
async def bulk_user_action(
    action_data: BulkUserAction,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk action on users (admin only)"""
    try:
        user_service = UserService(db)
        
        updates = {}
        if action_data.action == "activate":
            updates = {"is_active": True}
        elif action_data.action == "deactivate":
            updates = {"is_active": False}
        elif action_data.action == "verify":
            updates = {"is_verified": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 작업입니다: {action_data.action}"
            )
        
        successful_count, failed_ids = await user_service.bulk_update_users(
            user_ids=action_data.user_ids,
            updates=updates,
            admin_user_id=current_user.id
        )
        
        return BulkUserActionResponse(
            success=True,
            message=f"{successful_count}명의 사용자에 대해 작업이 완료되었습니다",
            affected_count=successful_count,
            failed_ids=failed_ids if failed_ids else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk user action error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="일괄 작업 중 오류가 발생했습니다"
        )


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics (admin only)"""
    try:
        user_service = UserService(db)
        stats = await user_service.get_user_statistics()
        
        return UserStatsResponse(
            success=True,
            message="사용자 통계를 조회했습니다",
            data=UserStats(**stats)
        )
        
    except Exception as e:
        logger.error(f"Get user statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 통계 조회 중 오류가 발생했습니다"
        )


@router.get("/check/username/{username}")
async def check_username_availability(
    username: str,
    current_user: Optional[User] = Depends(get_current_active_user)
):
    """Check if username is available"""
    try:
        user_service = UserService(db)
        exclude_user_id = current_user.id if current_user else None
        
        is_available = await user_service.check_username_available(
            username=username,
            exclude_user_id=exclude_user_id
        )
        
        return create_success_response(
            data={"available": is_available},
            message="사용 가능" if is_available else "이미 사용 중"
        )
        
    except Exception as e:
        logger.error(f"Check username availability error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자명 확인 중 오류가 발생했습니다"
        )


@router.get("/check/email/{email}")
async def check_email_availability(
    email: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Check if email is available"""
    try:
        user_service = UserService(db)
        exclude_user_id = current_user.id if current_user else None
        
        is_available = await user_service.check_email_available(
            email=email,
            exclude_user_id=exclude_user_id
        )
        
        return create_success_response(
            data={"available": is_available},
            message="사용 가능" if is_available else "이미 사용 중"
        )
        
    except Exception as e:
        logger.error(f"Check email availability error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이메일 확인 중 오류가 발생했습니다"
        )