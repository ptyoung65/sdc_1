from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from app.schemas.common import (
    BaseResponse,
    DataResponse, 
    PaginatedResponse,
    TimestampMixin,
    MetadataMixin
)


class ConversationBase(BaseModel):
    """Base conversation schema"""
    title: str = Field(max_length=200, description="Conversation title")
    system_prompt: Optional[str] = Field(None, description="System prompt for the conversation")
    model_name: Optional[str] = Field(default="gpt-4-turbo-preview", description="AI model to use")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(default=4096, ge=1, description="Maximum tokens per response")
    tags: Optional[List[str]] = Field(None, description="Conversation tags")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation"""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating conversation"""
    title: Optional[str] = Field(None, max_length=200, description="Conversation title")
    system_prompt: Optional[str] = Field(None, description="System prompt for the conversation")
    model_name: Optional[str] = Field(None, description="AI model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens per response")
    tags: Optional[List[str]] = Field(None, description="Conversation tags")
    is_archived: Optional[bool] = Field(None, description="Whether conversation is archived")
    is_pinned: Optional[bool] = Field(None, description="Whether conversation is pinned")


class ConversationResponse(ConversationBase, TimestampMixin):
    """Schema for conversation responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Conversation ID")
    user_id: str = Field(description="Owner user ID")
    is_archived: bool = Field(description="Whether conversation is archived")
    is_pinned: bool = Field(description="Whether conversation is pinned")
    message_count: int = Field(description="Number of messages in conversation")
    last_message_at: Optional[datetime] = Field(None, description="Timestamp of last message")
    
    # Sharing information
    is_shared: bool = Field(description="Whether conversation is shared")
    share_token: Optional[str] = Field(None, description="Share token if shared")
    share_expires_at: Optional[datetime] = Field(None, description="Share expiration time")
    allow_comments: bool = Field(description="Whether comments are allowed on shared conversation")
    
    # Computed properties
    is_empty: bool = Field(description="Whether conversation has no messages")
    is_share_active: bool = Field(description="Whether sharing is active and not expired")
    
    # Summary (optional, for search results)
    summary: Optional[str] = Field(None, description="AI-generated conversation summary")


class ConversationDetail(ConversationResponse):
    """Detailed conversation with messages"""
    messages: Optional[List["MessageResponse"]] = Field(None, description="Conversation messages")


class ConversationListResponse(PaginatedResponse[ConversationResponse]):
    """Response for listing conversations"""
    items: List[ConversationResponse] = Field(description="List of conversations")


class ConversationDetailResponse(DataResponse[ConversationDetail]):
    """Response for conversation detail"""
    data: ConversationDetail = Field(description="Conversation details")


class ConversationCreateResponse(DataResponse[ConversationResponse]):
    """Response for conversation creation"""
    data: ConversationResponse = Field(description="Created conversation")


class ConversationUpdateResponse(DataResponse[ConversationResponse]):
    """Response for conversation update"""
    data: ConversationResponse = Field(description="Updated conversation")


class ConversationSearchRequest(BaseModel):
    """Conversation search request"""
    query: Optional[str] = Field(None, description="Search query")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_archived: Optional[bool] = Field(None, description="Filter by archived status")
    is_pinned: Optional[bool] = Field(None, description="Filter by pinned status")
    model_name: Optional[str] = Field(None, description="Filter by AI model")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    has_messages: Optional[bool] = Field(None, description="Filter by whether conversation has messages")


class ConversationBulkAction(BaseModel):
    """Bulk action on conversations"""
    conversation_ids: List[str] = Field(min_items=1, description="List of conversation IDs")
    action: str = Field(description="Action to perform")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['archive', 'unarchive', 'pin', 'unpin', 'delete']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class ConversationBulkActionResponse(BaseResponse):
    """Response for bulk conversation actions"""
    affected_count: int = Field(description="Number of conversations affected")
    failed_ids: Optional[List[str]] = Field(None, description="IDs that failed to process")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")


class ConversationShareRequest(BaseModel):
    """Request to share a conversation"""
    expires_in_hours: Optional[int] = Field(None, ge=1, description="Share expiration in hours")
    password: Optional[str] = Field(None, min_length=4, description="Optional password protection")
    allow_comments: bool = Field(default=False, description="Whether to allow comments")


class ConversationShareResponse(DataResponse[dict]):
    """Response for conversation sharing"""
    data: dict = Field(description="Share information including URL")


class ConversationExportRequest(BaseModel):
    """Request to export conversation"""
    format: str = Field(description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    include_system_messages: bool = Field(default=False, description="Include system messages")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'markdown', 'pdf', 'html', 'txt']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v.lower()


class ConversationImportRequest(BaseModel):
    """Request to import conversation"""
    format: str = Field(description="Import format")
    data: str = Field(description="Conversation data to import")
    title: Optional[str] = Field(None, description="Override conversation title")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'markdown', 'txt']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v.lower()


class ConversationStats(BaseModel):
    """Conversation statistics"""
    total_conversations: int = Field(description="Total number of conversations")
    active_conversations: int = Field(description="Number of active conversations")
    archived_conversations: int = Field(description="Number of archived conversations")
    shared_conversations: int = Field(description="Number of shared conversations")
    avg_messages_per_conversation: float = Field(description="Average messages per conversation")
    most_used_model: Optional[str] = Field(None, description="Most frequently used AI model")
    total_messages: int = Field(description="Total number of messages across all conversations")


class ConversationStatsResponse(DataResponse[ConversationStats]):
    """Response for conversation statistics"""
    data: ConversationStats = Field(description="Conversation statistics")


class ConversationTemplate(BaseModel):
    """Conversation template schema"""
    id: str = Field(description="Template ID")
    name: str = Field(description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    title_template: str = Field(description="Title template")
    system_prompt: str = Field(description="System prompt template")
    model_name: str = Field(description="Default AI model")
    temperature: float = Field(description="Default temperature")
    max_tokens: int = Field(description="Default max tokens")
    tags: List[str] = Field(description="Default tags")
    is_public: bool = Field(description="Whether template is publicly available")
    created_by: str = Field(description="User ID who created the template")
    usage_count: int = Field(description="Number of times template has been used")
    created_at: datetime = Field(description="Creation timestamp")


class ConversationTemplateCreate(BaseModel):
    """Schema for creating conversation template"""
    name: str = Field(max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    title_template: str = Field(max_length=200, description="Title template")
    system_prompt: str = Field(description="System prompt template")
    model_name: str = Field(default="gpt-4-turbo-preview", description="Default AI model")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Default temperature")
    max_tokens: int = Field(default=4096, ge=1, description="Default max tokens")
    tags: List[str] = Field(default_factory=list, description="Default tags")
    is_public: bool = Field(default=False, description="Whether template is publicly available")


class ConversationTemplateResponse(DataResponse[ConversationTemplate]):
    """Response for conversation template"""
    data: ConversationTemplate = Field(description="Conversation template")


class ConversationTemplateListResponse(PaginatedResponse[ConversationTemplate]):
    """Response for listing conversation templates"""
    items: List[ConversationTemplate] = Field(description="List of conversation templates")


class ConversationFromTemplate(BaseModel):
    """Request to create conversation from template"""
    template_id: str = Field(description="Template ID")
    title: Optional[str] = Field(None, description="Override title")
    variables: Optional[Dict[str, str]] = Field(None, description="Template variable substitutions")


# Forward reference resolution
from app.schemas.message import MessageResponse
ConversationDetail.model_rebuild()