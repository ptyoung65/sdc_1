from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# Generic type for paginated responses
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Standard response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class BaseResponse(BaseModel):
    """Base response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = Field(description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class SuccessResponse(BaseResponse):
    """Success response schema"""
    success: bool = Field(default=True, description="Operation was successful")


class ErrorResponse(BaseResponse):
    """Error response schema"""
    success: bool = Field(default=False, description="Operation failed")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class DataResponse(BaseResponse, Generic[T]):
    """Response with data payload"""
    data: T = Field(description="Response data")


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.limit


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int = Field(ge=0, description="Total number of items")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    @classmethod
    def create(cls, total: int, page: int, limit: int) -> "PaginationMeta":
        """Create pagination metadata from parameters"""
        pages = (total + limit - 1) // limit  # Ceiling division
        return cls(
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response schema"""
    items: List[T] = Field(description="List of items")
    pagination: PaginationMeta = Field(description="Pagination metadata")


class SearchParams(BaseModel):
    """Search parameters"""
    query: str = Field(min_length=1, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field(default="desc", pattern="^(asc|desc)$", description="Sort order")


class SortOrder(str, Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operator enumeration"""
    EQ = "eq"      # Equal
    NE = "ne"      # Not equal
    GT = "gt"      # Greater than
    GTE = "gte"    # Greater than or equal
    LT = "lt"      # Less than
    LTE = "lte"    # Less than or equal
    IN = "in"      # In list
    NOT_IN = "not_in"  # Not in list
    LIKE = "like"  # Like (string contains)
    ILIKE = "ilike"  # Case-insensitive like
    IS_NULL = "is_null"  # Is null
    IS_NOT_NULL = "is_not_null"  # Is not null


class FilterCondition(BaseModel):
    """Filter condition"""
    field: str = Field(description="Field name to filter on")
    operator: FilterOperator = Field(description="Filter operator")
    value: Any = Field(description="Filter value")


class ComplexFilter(BaseModel):
    """Complex filter with multiple conditions"""
    conditions: List[FilterCondition] = Field(description="Filter conditions")
    logic: str = Field(default="and", pattern="^(and|or)$", description="Logic operator between conditions")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(description="Service status")
    version: str = Field(description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Dependent service status")


class MetricsResponse(BaseModel):
    """Metrics response"""
    metrics: Dict[str, Any] = Field(description="System metrics")
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str = Field(description="Field that failed validation")
    message: str = Field(description="Validation error message")
    code: str = Field(description="Error code")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    error_code: str = Field(default="VALIDATION_ERROR", description="Error code")
    validation_errors: List[ValidationErrorDetail] = Field(description="Validation error details")


# Common field validators
class TimestampMixin(BaseModel):
    """Mixin for timestamp fields"""
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


class SoftDeleteMixin(BaseModel):
    """Mixin for soft delete functionality"""
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    
    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class MetadataMixin(BaseModel):
    """Mixin for metadata field"""
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class AuditMixin(BaseModel):
    """Mixin for audit fields"""
    created_by: Optional[str] = Field(None, description="ID of user who created this record")
    updated_by: Optional[str] = Field(None, description="ID of user who last updated this record")


# File upload schemas
class FileInfo(BaseModel):
    """File information"""
    filename: str = Field(description="Original filename")
    size: int = Field(ge=0, description="File size in bytes")
    mime_type: str = Field(description="MIME type")
    hash: Optional[str] = Field(None, description="File hash")


class UploadResponse(SuccessResponse):
    """File upload response"""
    file_id: str = Field(description="Unique file identifier")
    file_info: FileInfo = Field(description="File information")
    upload_url: Optional[str] = Field(None, description="Upload URL if using signed URLs")


# API versioning
class APIVersion(BaseModel):
    """API version information"""
    version: str = Field(description="API version")
    release_date: datetime = Field(description="Release date")
    deprecated: bool = Field(default=False, description="Whether this version is deprecated")
    sunset_date: Optional[datetime] = Field(None, description="When this version will be removed")


# Rate limiting
class RateLimitInfo(BaseModel):
    """Rate limit information"""
    limit: int = Field(description="Request limit per window")
    remaining: int = Field(description="Remaining requests in current window")
    reset_time: datetime = Field(description="When the rate limit window resets")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retrying")


# WebSocket schemas
class WebSocketMessage(BaseModel):
    """WebSocket message schema"""
    type: str = Field(description="Message type")
    data: Optional[Dict[str, Any]] = Field(None, description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: Optional[str] = Field(None, description="Unique message identifier")


class WebSocketResponse(BaseModel):
    """WebSocket response schema"""
    type: str = Field(description="Response type")
    success: bool = Field(description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now)


# Utility functions
def create_success_response(
    data: Optional[Any] = None,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a success response"""
    response = {
        "success": True,
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    if data is not None:
        response["data"] = data
    
    return response


def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create an error response"""
    response = {
        "success": False,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    limit: int,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a paginated response"""
    pagination = PaginationMeta.create(total=total, page=page, limit=limit)
    
    response = {
        "success": True,
        "items": items,
        "pagination": pagination.model_dump(),
        "timestamp": datetime.now().isoformat()
    }
    
    if message:
        response["message"] = message
    
    return response