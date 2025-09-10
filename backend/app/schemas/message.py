from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum
from app.schemas.common import (
    BaseResponse,
    DataResponse,
    PaginatedResponse,
    TimestampMixin
)


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageBase(BaseModel):
    """Base message schema"""
    role: MessageRole = Field(description="Message role (user, assistant, system)")
    content: str = Field(description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message"""
    conversation_id: str = Field(description="Conversation ID")
    attachments: Optional[List[dict]] = Field(None, description="File attachments")
    context_documents: Optional[List[dict]] = Field(None, description="Context documents")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID for threading")


class MessageUpdate(BaseModel):
    """Schema for updating message"""
    content: Optional[str] = Field(None, description="Message content")
    is_hidden: Optional[bool] = Field(None, description="Whether message is hidden")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Message rating (1-5)")
    feedback: Optional[str] = Field(None, description="User feedback")


class MessageResponse(MessageBase, TimestampMixin):
    """Schema for message responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Message ID")
    conversation_id: str = Field(description="Conversation ID")
    sequence_number: int = Field(description="Message sequence in conversation")
    status: MessageStatus = Field(description="Message processing status")
    
    # AI model information
    model_name: Optional[str] = Field(None, description="AI model used")
    temperature: Optional[float] = Field(None, description="Temperature used")
    max_tokens: Optional[int] = Field(None, description="Max tokens setting")
    
    # Token usage
    prompt_tokens: Optional[int] = Field(None, description="Prompt tokens used")
    completion_tokens: Optional[int] = Field(None, description="Completion tokens used")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    
    # Processing time
    processing_started_at: Optional[datetime] = Field(None, description="Processing start time")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    processing_duration: Optional[float] = Field(None, description="Processing duration in seconds")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    
    # Attachments and context
    attachments: Optional[List[dict]] = Field(None, description="File attachments")
    context_documents: Optional[List[dict]] = Field(None, description="Context documents used")
    sources: Optional[List[dict]] = Field(None, description="Information sources")
    
    # Message quality and feedback
    rating: Optional[int] = Field(None, description="Message rating (1-5)")
    feedback: Optional[str] = Field(None, description="User feedback")
    
    # Message flags
    is_edited: bool = Field(description="Whether message has been edited")
    is_regenerated: bool = Field(description="Whether message is regenerated")
    is_hidden: bool = Field(description="Whether message is hidden")
    
    # Parent/child relationships
    parent_message_id: Optional[str] = Field(None, description="Parent message ID")
    
    # Computed properties
    is_user_message: bool = Field(description="Whether message is from user")
    is_assistant_message: bool = Field(description="Whether message is from assistant")
    is_system_message: bool = Field(description="Whether message is system message")
    is_processing: bool = Field(description="Whether message is currently processing")
    is_completed: bool = Field(description="Whether message processing is completed")
    is_failed: bool = Field(description="Whether message processing failed")
    content_preview: str = Field(description="Preview of message content")


class MessageListResponse(PaginatedResponse[MessageResponse]):
    """Response for listing messages"""
    items: List[MessageResponse] = Field(description="List of messages")


class MessageDetailResponse(DataResponse[MessageResponse]):
    """Response for message detail"""
    data: MessageResponse = Field(description="Message details")


class MessageCreateResponse(DataResponse[MessageResponse]):
    """Response for message creation"""
    data: MessageResponse = Field(description="Created message")


class MessageUpdateResponse(DataResponse[MessageResponse]):
    """Response for message update"""
    data: MessageResponse = Field(description="Updated message")


class MessageSendRequest(BaseModel):
    """Request to send a message"""
    conversation_id: Optional[str] = Field(None, description="Conversation ID (create new if not provided)")
    message: str = Field(min_length=1, description="Message content")
    files: Optional[List[str]] = Field(None, description="File IDs to attach")
    options: Optional[dict] = Field(None, description="AI model options")
    context: Optional[dict] = Field(None, description="Additional context")


class MessageSendResponse(DataResponse[dict]):
    """Response for sending a message"""
    data: dict = Field(description="Send response with conversation and message info")


class StreamingMessageChunk(BaseModel):
    """Streaming message chunk"""
    type: str = Field(description="Chunk type (content, metadata, error, done)")
    content: Optional[str] = Field(None, description="Content chunk")
    metadata: Optional[dict] = Field(None, description="Metadata chunk")
    error: Optional[str] = Field(None, description="Error message")
    finished: bool = Field(default=False, description="Whether streaming is finished")


class MessageRegenerateRequest(BaseModel):
    """Request to regenerate a message"""
    options: Optional[dict] = Field(None, description="AI model options override")


class MessageSearchRequest(BaseModel):
    """Message search request"""
    query: str = Field(min_length=1, description="Search query")
    conversation_id: Optional[str] = Field(None, description="Filter by conversation")
    role: Optional[MessageRole] = Field(None, description="Filter by message role")
    status: Optional[MessageStatus] = Field(None, description="Filter by message status")
    model_name: Optional[str] = Field(None, description="Filter by AI model")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date")
    has_attachments: Optional[bool] = Field(None, description="Filter by attachment presence")
    min_rating: Optional[int] = Field(None, ge=1, le=5, description="Minimum rating filter")


class MessageSearchResult(MessageResponse):
    """Message search result with highlighting"""
    highlights: Optional[List[str]] = Field(None, description="Search result highlights")
    relevance_score: Optional[float] = Field(None, description="Search relevance score")


class MessageSearchResponse(PaginatedResponse[MessageSearchResult]):
    """Response for message search"""
    items: List[MessageSearchResult] = Field(description="Search results")
    query: str = Field(description="Original search query")
    total_time_ms: Optional[float] = Field(None, description="Search time in milliseconds")


class MessageBulkAction(BaseModel):
    """Bulk action on messages"""
    message_ids: List[str] = Field(min_items=1, description="List of message IDs")
    action: str = Field(description="Action to perform")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['delete', 'hide', 'unhide', 'export']
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class MessageBulkActionResponse(BaseResponse):
    """Response for bulk message actions"""
    affected_count: int = Field(description="Number of messages affected")
    failed_ids: Optional[List[str]] = Field(None, description="IDs that failed to process")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")


class MessageExportRequest(BaseModel):
    """Request to export messages"""
    message_ids: Optional[List[str]] = Field(None, description="Specific message IDs to export")
    conversation_id: Optional[str] = Field(None, description="Export all messages from conversation")
    format: str = Field(description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata in export")
    include_attachments: bool = Field(default=False, description="Include attachment references")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'markdown', 'txt', 'csv']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v.lower()


class MessageStats(BaseModel):
    """Message statistics"""
    total_messages: int = Field(description="Total number of messages")
    user_messages: int = Field(description="Number of user messages")
    assistant_messages: int = Field(description="Number of assistant messages")
    system_messages: int = Field(description="Number of system messages")
    avg_message_length: float = Field(description="Average message length")
    total_tokens_used: int = Field(description="Total tokens used across all messages")
    avg_processing_time: float = Field(description="Average processing time in seconds")
    success_rate: float = Field(description="Message processing success rate")
    most_used_model: Optional[str] = Field(None, description="Most frequently used AI model")


class MessageStatsResponse(DataResponse[MessageStats]):
    """Response for message statistics"""
    data: MessageStats = Field(description="Message statistics")


class MessageFeedback(BaseModel):
    """Message feedback schema"""
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5")
    feedback: Optional[str] = Field(None, max_length=1000, description="Detailed feedback")
    categories: Optional[List[str]] = Field(None, description="Feedback categories")
    is_helpful: Optional[bool] = Field(None, description="Whether message was helpful")
    improvement_suggestions: Optional[str] = Field(None, description="Suggestions for improvement")


class MessageFeedbackResponse(DataResponse[dict]):
    """Response for message feedback submission"""
    data: dict = Field(description="Feedback submission confirmation")


class MessageThread(BaseModel):
    """Message thread schema"""
    parent_message: MessageResponse = Field(description="Parent message")
    child_messages: List[MessageResponse] = Field(description="Child messages")
    depth: int = Field(description="Thread depth")


class MessageThreadResponse(DataResponse[MessageThread]):
    """Response for message thread"""
    data: MessageThread = Field(description="Message thread")


class MessageAttachment(BaseModel):
    """Message attachment schema"""
    id: str = Field(description="Attachment ID")
    file_name: str = Field(description="Original file name")
    file_type: str = Field(description="File type/extension")
    file_size: int = Field(description="File size in bytes")
    mime_type: str = Field(description="MIME type")
    upload_url: Optional[str] = Field(None, description="Upload URL if not yet uploaded")
    download_url: Optional[str] = Field(None, description="Download URL if uploaded")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail URL for images")
    processing_status: str = Field(description="Attachment processing status")
    uploaded_at: Optional[datetime] = Field(None, description="Upload timestamp")


class MessageContext(BaseModel):
    """Message context information"""
    documents: Optional[List[dict]] = Field(None, description="Context documents")
    search_query: Optional[str] = Field(None, description="Search query used")
    filters: Optional[dict] = Field(None, description="Search filters applied")
    retrieval_method: Optional[str] = Field(None, description="Retrieval method used")
    relevance_threshold: Optional[float] = Field(None, description="Relevance threshold")


class MessageWithContext(MessageResponse):
    """Message with additional context information"""
    context: Optional[MessageContext] = Field(None, description="Message context")
    related_messages: Optional[List[str]] = Field(None, description="Related message IDs")
    conversation_summary: Optional[str] = Field(None, description="Conversation summary at this point")