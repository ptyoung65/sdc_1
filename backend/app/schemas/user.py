from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, ConfigDict
from app.schemas.common import (
    BaseResponse, 
    DataResponse, 
    PaginatedResponse, 
    TimestampMixin,
    MetadataMixin
)


class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(
        min_length=3,
        max_length=50,
        description="Username"
    )
    email: EmailStr = Field(description="User email address")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    timezone: Optional[str] = Field(default="Asia/Seoul", description="User timezone")
    language: Optional[str] = Field(default="ko", description="Preferred language")


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(min_length=8, description="User password")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in v)
        has_number = any(c.isdigit() for c in v)
        
        if not has_letter:
            raise ValueError('Password must contain at least one letter')
        
        if not has_number:
            raise ValueError('Password must contain at least one number')
        
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="Preferred language")


class UserResponse(UserBase, TimestampMixin):
    """Schema for user responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="User ID")
    is_active: bool = Field(description="Whether user account is active")
    is_verified: bool = Field(description="Whether email is verified")
    is_superuser: bool = Field(description="Whether user is a superuser")
    
    # Account limits
    max_conversations: int = Field(description="Maximum number of conversations")
    max_documents: int = Field(description="Maximum number of documents")
    max_file_size_mb: int = Field(description="Maximum file size in MB")
    
    # Computed fields
    full_name: str = Field(description="Full display name")
    conversation_count: int = Field(description="Number of conversations")
    document_count: int = Field(description="Number of documents")
    
    # Timestamps
    last_login_at: Optional[datetime] = Field(None, description="Last login time")
    email_verified_at: Optional[datetime] = Field(None, description="Email verification time")
    password_changed_at: Optional[datetime] = Field(None, description="Last password change time")


class UserProfile(UserResponse):
    """Extended user profile schema"""
    # Usage statistics
    total_messages: Optional[int] = Field(None, description="Total number of messages sent")
    total_documents_processed: Optional[int] = Field(None, description="Total documents processed")
    total_storage_used_mb: Optional[float] = Field(None, description="Total storage used in MB")
    
    # Preferences
    notification_preferences: Optional[dict] = Field(None, description="Notification preferences")
    theme_preferences: Optional[dict] = Field(None, description="Theme preferences")
    privacy_settings: Optional[dict] = Field(None, description="Privacy settings")


class UserProfileUpdate(BaseModel):
    """Schema for updating extended user profile"""
    display_name: Optional[str] = Field(None, max_length=100, description="Display name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL") 
    bio: Optional[str] = Field(None, max_length=500, description="User bio")
    timezone: Optional[str] = Field(None, description="User timezone")
    language: Optional[str] = Field(None, description="Preferred language")
    notification_preferences: Optional[dict] = Field(None, description="Notification preferences")
    theme_preferences: Optional[dict] = Field(None, description="Theme preferences")
    privacy_settings: Optional[dict] = Field(None, description="Privacy settings")


class UserListResponse(PaginatedResponse[UserResponse]):
    """Response for listing users"""
    items: List[UserResponse] = Field(description="List of users")


class UserDetailResponse(DataResponse[UserProfile]):
    """Response for user detail"""
    data: UserProfile = Field(description="User profile information")


class UserCreateResponse(DataResponse[UserResponse]):
    """Response for user creation"""
    data: UserResponse = Field(description="Created user information")


class UserUpdateResponse(DataResponse[UserResponse]):
    """Response for user update"""
    data: UserResponse = Field(description="Updated user information")


class UserSearchRequest(BaseModel):
    """User search request"""
    query: Optional[str] = Field(None, description="Search query")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")
    is_superuser: Optional[bool] = Field(None, description="Filter by superuser status")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_users: int = Field(description="Total number of users")
    active_users: int = Field(description="Number of active users")
    verified_users: int = Field(description="Number of verified users")
    new_users_today: int = Field(description="New users registered today")
    new_users_this_week: int = Field(description="New users registered this week")
    new_users_this_month: int = Field(description="New users registered this month")


class UserActivityLog(BaseModel):
    """User activity log entry"""
    id: str = Field(description="Activity log ID")
    user_id: str = Field(description="User ID")
    action: str = Field(description="Action performed")
    resource: Optional[str] = Field(None, description="Resource affected")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")
    created_at: datetime = Field(description="When the action occurred")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UserActivityResponse(PaginatedResponse[UserActivityLog]):
    """Response for user activity logs"""
    items: List[UserActivityLog] = Field(description="List of activity logs")


class AdminUserUpdate(UserUpdate):
    """Schema for admin user updates (includes additional fields)"""
    is_active: Optional[bool] = Field(None, description="Whether user account is active")
    is_verified: Optional[bool] = Field(None, description="Whether email is verified")
    is_superuser: Optional[bool] = Field(None, description="Whether user is a superuser")
    max_conversations: Optional[int] = Field(None, ge=0, description="Maximum number of conversations")
    max_documents: Optional[int] = Field(None, ge=0, description="Maximum number of documents")
    max_file_size_mb: Optional[int] = Field(None, ge=1, description="Maximum file size in MB")


class AdminUserResponse(UserProfile):
    """Admin view of user with sensitive information"""
    # Security information
    failed_login_attempts: int = Field(description="Number of failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account locked until")
    is_locked: bool = Field(description="Whether account is currently locked")
    
    # Additional metadata
    created_by: Optional[str] = Field(None, description="ID of user who created this account")
    updated_by: Optional[str] = Field(None, description="ID of user who last updated this account")


class BulkUserAction(BaseModel):
    """Bulk action on multiple users"""
    user_ids: List[str] = Field(min_items=1, description="List of user IDs")
    action: str = Field(description="Action to perform (activate, deactivate, delete)")


class BulkUserActionResponse(BaseResponse):
    """Response for bulk user actions"""
    affected_count: int = Field(description="Number of users affected")
    failed_ids: Optional[List[str]] = Field(None, description="IDs that failed to process")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")


class UserPreferences(BaseModel):
    """User preferences schema"""
    theme: str = Field(default="light", description="UI theme preference")
    language: str = Field(default="ko", description="Language preference")
    timezone: str = Field(default="Asia/Seoul", description="Timezone preference")
    notifications: dict = Field(default_factory=dict, description="Notification preferences")
    privacy: dict = Field(default_factory=dict, description="Privacy preferences")
    accessibility: dict = Field(default_factory=dict, description="Accessibility preferences")


class UserPreferencesResponse(DataResponse[UserPreferences]):
    """Response for user preferences"""
    data: UserPreferences = Field(description="User preferences")


class UserQuotaInfo(BaseModel):
    """User quota information"""
    conversations: dict = Field(description="Conversation quota info")
    documents: dict = Field(description="Document quota info")
    storage: dict = Field(description="Storage quota info")
    api_calls: dict = Field(description="API call quota info")


class UserQuotaResponse(DataResponse[UserQuotaInfo]):
    """Response for user quota information"""
    data: UserQuotaInfo = Field(description="User quota information")