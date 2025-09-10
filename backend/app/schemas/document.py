from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum
from app.schemas.common import (
    BaseResponse,
    DataResponse,
    PaginatedResponse,
    TimestampMixin,
    FileInfo
)


class DocumentType(str, Enum):
    """Document type enumeration"""
    PDF = "pdf"
    DOCX = "docx"
    DOC = "doc"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    RTF = "rtf"
    ODT = "odt"
    XLSX = "xlsx"
    XLS = "xls"
    PPTX = "pptx"
    PPT = "ppt"


class DocumentStatus(str, Enum):
    """Document processing status enumeration"""
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class ProcessingStage(str, Enum):
    """Document processing stage enumeration"""
    UPLOAD = "upload"
    EXTRACTION = "extraction"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"


class DocumentBase(BaseModel):
    """Base document schema"""
    title: str = Field(max_length=255, description="Document title")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    category: Optional[str] = Field(None, description="Document category")
    is_public: bool = Field(default=False, description="Whether document is publicly accessible")


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""
    file_info: FileInfo = Field(description="File information")


class DocumentUpdate(BaseModel):
    """Schema for updating document"""
    title: Optional[str] = Field(None, max_length=255, description="Document title")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    category: Optional[str] = Field(None, description="Document category")
    is_public: Optional[bool] = Field(None, description="Whether document is publicly accessible")


class DocumentResponse(DocumentBase, TimestampMixin):
    """Schema for document responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Document ID")
    user_id: str = Field(description="Owner user ID")
    original_filename: str = Field(description="Original filename")
    file_type: DocumentType = Field(description="Document file type")
    file_size: int = Field(description="File size in bytes")
    file_size_mb: float = Field(description="File size in MB")
    mime_type: Optional[str] = Field(None, description="MIME type")
    file_extension: str = Field(description="File extension")
    
    # Processing status
    status: DocumentStatus = Field(description="Processing status")
    processing_stage: Optional[ProcessingStage] = Field(None, description="Current processing stage")
    processing_progress: float = Field(description="Processing progress (0-100)")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start time")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    processing_duration: Optional[float] = Field(None, description="Processing duration in seconds")
    
    # Error information
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    error_code: Optional[str] = Field(None, description="Error code if processing failed")
    retry_count: int = Field(description="Number of processing retries")
    
    # Content analysis
    content_length: int = Field(description="Content length in characters")
    page_count: Optional[int] = Field(None, description="Number of pages")
    word_count: Optional[int] = Field(None, description="Number of words")
    character_count: Optional[int] = Field(None, description="Number of characters")
    language: Optional[str] = Field(None, description="Detected language")
    
    # Chunking information
    chunk_count: int = Field(description="Number of chunks")
    chunk_strategy: Optional[str] = Field(None, description="Chunking strategy used")
    chunk_size: Optional[int] = Field(None, description="Chunk size used")
    chunk_overlap: Optional[int] = Field(None, description="Chunk overlap used")
    
    # Vector embedding
    embedding_model: Optional[str] = Field(None, description="Embedding model used")
    embedding_dimension: Optional[int] = Field(None, description="Embedding vector dimension")
    
    # Indexing
    is_indexed: bool = Field(description="Whether document is indexed for search")
    vector_index_id: Optional[str] = Field(None, description="Vector database index ID")
    fulltext_indexed: bool = Field(description="Whether document is full-text indexed")
    
    # Quality metrics
    quality_score: Optional[float] = Field(None, description="Document quality score (0-100)")
    readability_score: Optional[float] = Field(None, description="Readability score (0-100)")
    
    # Usage statistics
    view_count: int = Field(description="Number of views")
    search_count: int = Field(description="Number of searches")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access time")
    
    # Sharing
    is_shared: bool = Field(description="Whether document is shared")
    share_token: Optional[str] = Field(None, description="Share token if shared")
    
    # Computed properties
    is_processing: bool = Field(description="Whether document is currently processing")
    is_ready: bool = Field(description="Whether document is ready for use")
    is_failed: bool = Field(description="Whether document processing failed")
    content_preview: str = Field(description="Preview of document content")


class DocumentDetail(DocumentResponse):
    """Detailed document with content and chunks"""
    content: Optional[str] = Field(None, description="Full document content")
    chunks: Optional[List["ChunkResponse"]] = Field(None, description="Document chunks")
    analysis_results: Optional[Dict[str, Any]] = Field(None, description="Content analysis results")


class DocumentListResponse(PaginatedResponse[DocumentResponse]):
    """Response for listing documents"""
    items: List[DocumentResponse] = Field(description="List of documents")


class DocumentDetailResponse(DataResponse[DocumentDetail]):
    """Response for document detail"""
    data: DocumentDetail = Field(description="Document details")


class DocumentCreateResponse(DataResponse[DocumentResponse]):
    """Response for document creation"""
    data: DocumentResponse = Field(description="Created document")


class DocumentUpdateResponse(DataResponse[DocumentResponse]):
    """Response for document update"""
    data: DocumentResponse = Field(description="Updated document")


class DocumentUploadRequest(BaseModel):
    """Document upload request"""
    title: Optional[str] = Field(None, description="Document title (defaults to filename)")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    category: Optional[str] = Field(None, description="Document category")
    processing_options: Optional[Dict[str, Any]] = Field(None, description="Processing options")


class DocumentUploadResponse(DataResponse[dict]):
    """Document upload response"""
    data: dict = Field(description="Upload response with document ID and upload URL")


class DocumentProcessingRequest(BaseModel):
    """Document processing request"""
    processing_options: Optional[Dict[str, Any]] = Field(None, description="Processing options")
    
    @validator('processing_options')
    def validate_processing_options(cls, v):
        if v is None:
            return {}
        
        allowed_options = {
            'extract_images', 'enable_ocr', 'chunk_strategy', 
            'chunk_size', 'overlap_size', 'embedding_model'
        }
        
        invalid_options = set(v.keys()) - allowed_options
        if invalid_options:
            raise ValueError(f'Invalid processing options: {", ".join(invalid_options)}')
        
        return v


class DocumentProcessingResponse(DataResponse[DocumentResponse]):
    """Document processing response"""
    data: DocumentResponse = Field(description="Document with updated processing status")


class DocumentSearchRequest(BaseModel):
    """Document search request"""
    query: str = Field(min_length=1, description="Search query")
    search_type: str = Field(default="hybrid", description="Search type")
    document_types: Optional[List[DocumentType]] = Field(None, description="Filter by document types")
    categories: Optional[List[str]] = Field(None, description="Filter by categories")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    language: Optional[str] = Field(None, description="Filter by language")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="Date range filter")
    quality_threshold: Optional[float] = Field(None, ge=0, le=100, description="Minimum quality score")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")
    include_content: bool = Field(default=False, description="Include document content in results")
    highlight_results: bool = Field(default=True, description="Highlight search terms in results")
    
    @validator('search_type')
    def validate_search_type(cls, v):
        allowed_types = ['semantic', 'keyword', 'hybrid']
        if v not in allowed_types:
            raise ValueError(f'Search type must be one of: {", ".join(allowed_types)}')
        return v


class SearchResult(BaseModel):
    """Document search result"""
    document: DocumentResponse = Field(description="Document information")
    relevance_score: float = Field(description="Search relevance score")
    chunk_results: Optional[List[Dict[str, Any]]] = Field(None, description="Matching chunks")
    highlights: Optional[List[str]] = Field(None, description="Highlighted text snippets")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional search metadata")


class DocumentSearchResponse(BaseResponse):
    """Document search response"""
    results: List[SearchResult] = Field(description="Search results")
    total_results: int = Field(description="Total number of matching documents")
    search_time_ms: float = Field(description="Search execution time in milliseconds")
    query: str = Field(description="Original search query")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters that were applied")


class DocumentAnalysisRequest(BaseModel):
    """Document analysis request"""
    analysis_types: List[str] = Field(description="Types of analysis to perform")
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        allowed_types = [
            'summary', 'keywords', 'entities', 'sentiment', 
            'topics', 'language_detection', 'readability'
        ]
        invalid_types = set(v) - set(allowed_types)
        if invalid_types:
            raise ValueError(f'Invalid analysis types: {", ".join(invalid_types)}')
        return v


class DocumentAnalysisResult(BaseModel):
    """Document analysis result"""
    summary: Optional[str] = Field(None, description="Document summary")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="Sentiment analysis")
    topics: Optional[List[Dict[str, Any]]] = Field(None, description="Topic analysis")
    language: Optional[str] = Field(None, description="Detected language")
    readability_score: Optional[float] = Field(None, description="Readability score")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Analysis confidence scores")


class DocumentAnalysisResponse(DataResponse[DocumentAnalysisResult]):
    """Document analysis response"""
    data: DocumentAnalysisResult = Field(description="Analysis results")


class DocumentBulkAction(BaseModel):
    """Bulk action on documents"""
    document_ids: List[str] = Field(min_items=1, description="List of document IDs")
    action: str = Field(description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            'delete', 'reprocess', 'update_status', 'add_tags', 
            'remove_tags', 'set_category', 'update_sharing'
        ]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class DocumentBulkActionResponse(BaseResponse):
    """Response for bulk document actions"""
    affected_count: int = Field(description="Number of documents affected")
    failed_ids: Optional[List[str]] = Field(None, description="IDs that failed to process")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")
    results: Optional[Dict[str, Any]] = Field(None, description="Detailed results by document ID")


class DocumentExportRequest(BaseModel):
    """Document export request"""
    format: str = Field(description="Export format")
    include_metadata: bool = Field(default=True, description="Include metadata")
    include_chunks: bool = Field(default=False, description="Include chunk information")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['txt', 'markdown', 'json', 'pdf', 'html']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v.lower()


class DocumentShareRequest(BaseModel):
    """Document sharing request"""
    expires_in_hours: Optional[int] = Field(None, ge=1, description="Share expiration in hours")
    password: Optional[str] = Field(None, min_length=4, description="Optional password protection")
    allow_download: bool = Field(default=True, description="Allow download of shared document")


class DocumentShareResponse(DataResponse[dict]):
    """Document sharing response"""
    data: dict = Field(description="Share information including URL")


class DocumentStats(BaseModel):
    """Document statistics"""
    total_documents: int = Field(description="Total number of documents")
    by_status: Dict[str, int] = Field(description="Document count by status")
    by_type: Dict[str, int] = Field(description="Document count by file type")
    total_size_mb: float = Field(description="Total storage used in MB")
    avg_processing_time: float = Field(description="Average processing time in seconds")
    success_rate: float = Field(description="Processing success rate")
    most_common_language: Optional[str] = Field(None, description="Most common document language")
    processing_queue_size: int = Field(description="Number of documents in processing queue")


class DocumentStatsResponse(DataResponse[DocumentStats]):
    """Document statistics response"""
    data: DocumentStats = Field(description="Document statistics")


class DocumentProcessingStatus(BaseModel):
    """Document processing status"""
    status: DocumentStatus = Field(description="Current processing status")
    stage: Optional[ProcessingStage] = Field(None, description="Current processing stage")
    progress: float = Field(description="Processing progress (0-100)")
    message: Optional[str] = Field(None, description="Status message")
    error: Optional[str] = Field(None, description="Error message if failed")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    can_retry: bool = Field(description="Whether processing can be retried")


class DocumentProcessingStatusResponse(DataResponse[DocumentProcessingStatus]):
    """Document processing status response"""
    data: DocumentProcessingStatus = Field(description="Processing status")


# Forward reference resolution
from app.schemas.chunk import ChunkResponse
DocumentDetail.model_rebuild()