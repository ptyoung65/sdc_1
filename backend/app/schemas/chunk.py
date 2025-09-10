from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, ConfigDict
from app.schemas.common import (
    BaseResponse,
    DataResponse,
    PaginatedResponse,
    TimestampMixin
)


class ChunkBase(BaseModel):
    """Base chunk schema"""
    content: str = Field(description="Chunk content")
    sequence_number: int = Field(ge=0, description="Sequence number within document")
    start_index: int = Field(ge=0, description="Start index in original document")
    end_index: int = Field(gt=0, description="End index in original document")
    page_number: Optional[int] = Field(None, ge=1, description="Page number if applicable")
    section_title: Optional[str] = Field(None, description="Section title")


class ChunkCreate(ChunkBase):
    """Schema for creating a chunk"""
    document_id: str = Field(description="Document ID")
    parent_chunk_id: Optional[str] = Field(None, description="Parent chunk ID for hierarchy")
    hierarchy_level: int = Field(default=0, ge=0, description="Hierarchy level")
    chunking_strategy: Optional[str] = Field(None, description="Chunking strategy used")
    chunk_overlap: Optional[int] = Field(None, ge=0, description="Overlap with adjacent chunks")


class ChunkUpdate(BaseModel):
    """Schema for updating chunk"""
    content: Optional[str] = Field(None, description="Chunk content")
    section_title: Optional[str] = Field(None, description="Section title")
    keywords: Optional[List[str]] = Field(None, description="Keywords")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities")
    is_valid: Optional[bool] = Field(None, description="Whether chunk is valid")


class ChunkResponse(ChunkBase, TimestampMixin):
    """Schema for chunk responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(description="Chunk ID")
    document_id: str = Field(description="Document ID")
    content_length: int = Field(description="Content length in characters")
    
    # Hierarchy information
    parent_chunk_id: Optional[str] = Field(None, description="Parent chunk ID")
    hierarchy_level: int = Field(description="Hierarchy level")
    
    # Chunking metadata
    chunking_strategy: Optional[str] = Field(None, description="Chunking strategy used")
    chunk_overlap: Optional[int] = Field(None, description="Overlap with adjacent chunks")
    
    # Content analysis
    word_count: Optional[int] = Field(None, description="Number of words")
    sentence_count: Optional[int] = Field(None, description="Number of sentences")
    language: Optional[str] = Field(None, description="Detected language")
    
    # Content classification
    content_type: Optional[str] = Field(None, description="Content type (text, code, table, etc.)")
    is_title: bool = Field(description="Whether chunk is a title")
    is_header: bool = Field(description="Whether chunk is a header")
    is_code: bool = Field(description="Whether chunk contains code")
    is_table: bool = Field(description="Whether chunk contains table data")
    is_list: bool = Field(description="Whether chunk contains list data")
    
    # Vector embeddings
    embedding_model: Optional[str] = Field(None, description="Embedding model used")
    embedding_dimension: Optional[int] = Field(None, description="Embedding vector dimension")
    vector_id: Optional[str] = Field(None, description="Vector database ID")
    
    # Search and retrieval metadata
    keyword_density: Optional[float] = Field(None, description="Keyword density score")
    semantic_density: Optional[float] = Field(None, description="Semantic density score")
    importance_score: Optional[float] = Field(None, description="Importance score (0-100)")
    
    # Extracted information
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities")
    
    # Quality metrics
    quality_score: Optional[float] = Field(None, description="Chunk quality score (0-100)")
    is_valid: bool = Field(description="Whether chunk is considered valid")
    
    # Usage statistics
    search_count: int = Field(description="Number of times chunk appeared in search")
    retrieval_count: int = Field(description="Number of times chunk was retrieved")
    
    # Computed properties
    content_preview: str = Field(description="Preview of chunk content")
    is_structural: bool = Field(description="Whether chunk contains structural elements")
    content_density: float = Field(description="Content density (words per character)")


class ChunkWithEmbedding(ChunkResponse):
    """Chunk response including embedding vector"""
    embedding_vector: Optional[List[float]] = Field(None, description="Embedding vector")


class ChunkListResponse(PaginatedResponse[ChunkResponse]):
    """Response for listing chunks"""
    items: List[ChunkResponse] = Field(description="List of chunks")


class ChunkDetailResponse(DataResponse[ChunkResponse]):
    """Response for chunk detail"""
    data: ChunkResponse = Field(description="Chunk details")


class ChunkCreateResponse(DataResponse[ChunkResponse]):
    """Response for chunk creation"""
    data: ChunkResponse = Field(description="Created chunk")


class ChunkUpdateResponse(DataResponse[ChunkResponse]):
    """Response for chunk update"""
    data: ChunkResponse = Field(description="Updated chunk")


class ChunkSearchRequest(BaseModel):
    """Chunk search request"""
    query: str = Field(min_length=1, description="Search query")
    document_id: Optional[str] = Field(None, description="Filter by specific document")
    search_type: str = Field(default="semantic", description="Search type")
    content_types: Optional[List[str]] = Field(None, description="Filter by content types")
    importance_threshold: Optional[float] = Field(None, ge=0, le=100, description="Minimum importance score")
    quality_threshold: Optional[float] = Field(None, ge=0, le=100, description="Minimum quality score")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")
    include_embeddings: bool = Field(default=False, description="Include embedding vectors")
    
    @validator('search_type')
    def validate_search_type(cls, v):
        allowed_types = ['semantic', 'keyword', 'hybrid']
        if v not in allowed_types:
            raise ValueError(f'Search type must be one of: {", ".join(allowed_types)}')
        return v


class ChunkSearchResult(ChunkResponse):
    """Chunk search result with relevance information"""
    relevance_score: float = Field(description="Search relevance score")
    distance_score: Optional[float] = Field(None, description="Vector distance score")
    highlights: Optional[List[str]] = Field(None, description="Highlighted text snippets")
    context_chunks: Optional[List["ChunkResponse"]] = Field(None, description="Surrounding chunks for context")


class ChunkSearchResponse(BaseResponse):
    """Chunk search response"""
    results: List[ChunkSearchResult] = Field(description="Search results")
    total_results: int = Field(description="Total number of matching chunks")
    search_time_ms: float = Field(description="Search execution time in milliseconds")
    query: str = Field(description="Original search query")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Filters that were applied")


class ChunkSimilarityRequest(BaseModel):
    """Request to find similar chunks"""
    chunk_id: str = Field(description="Reference chunk ID")
    limit: int = Field(default=10, ge=1, le=50, description="Number of similar chunks to return")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    same_document_only: bool = Field(default=False, description="Only find chunks from same document")
    include_self: bool = Field(default=False, description="Include the reference chunk in results")


class ChunkSimilarityResult(ChunkResponse):
    """Similar chunk result"""
    similarity_score: float = Field(description="Similarity score (0-1)")
    document_title: Optional[str] = Field(None, description="Title of source document")


class ChunkSimilarityResponse(BaseResponse):
    """Response for chunk similarity search"""
    reference_chunk: ChunkResponse = Field(description="Reference chunk")
    similar_chunks: List[ChunkSimilarityResult] = Field(description="Similar chunks")
    search_time_ms: float = Field(description="Search execution time")


class ChunkAnalysisRequest(BaseModel):
    """Chunk analysis request"""
    analysis_types: List[str] = Field(description="Types of analysis to perform")
    
    @validator('analysis_types')
    def validate_analysis_types(cls, v):
        allowed_types = [
            'keywords', 'entities', 'sentiment', 'topics', 
            'content_type', 'importance', 'quality'
        ]
        invalid_types = set(v) - set(allowed_types)
        if invalid_types:
            raise ValueError(f'Invalid analysis types: {", ".join(invalid_types)}')
        return v


class ChunkAnalysisResult(BaseModel):
    """Chunk analysis result"""
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    entities: Optional[List[Dict[str, Any]]] = Field(None, description="Named entities")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="Sentiment analysis")
    topics: Optional[List[Dict[str, Any]]] = Field(None, description="Topic analysis")
    content_type: Optional[str] = Field(None, description="Detected content type")
    importance_score: Optional[float] = Field(None, description="Calculated importance score")
    quality_score: Optional[float] = Field(None, description="Calculated quality score")
    confidence_scores: Optional[Dict[str, float]] = Field(None, description="Analysis confidence scores")


class ChunkAnalysisResponse(DataResponse[ChunkAnalysisResult]):
    """Chunk analysis response"""
    data: ChunkAnalysisResult = Field(description="Analysis results")


class ChunkBulkAction(BaseModel):
    """Bulk action on chunks"""
    chunk_ids: List[str] = Field(min_items=1, description="List of chunk IDs")
    action: str = Field(description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = [
            'delete', 'reanalyze', 'update_embeddings', 'recalculate_scores',
            'mark_valid', 'mark_invalid', 'add_keywords', 'remove_keywords'
        ]
        if v not in allowed_actions:
            raise ValueError(f'Action must be one of: {", ".join(allowed_actions)}')
        return v


class ChunkBulkActionResponse(BaseResponse):
    """Response for bulk chunk actions"""
    affected_count: int = Field(description="Number of chunks affected")
    failed_ids: Optional[List[str]] = Field(None, description="IDs that failed to process")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")


class ChunkHierarchy(BaseModel):
    """Chunk hierarchy representation"""
    parent_chunk: Optional[ChunkResponse] = Field(None, description="Parent chunk")
    current_chunk: ChunkResponse = Field(description="Current chunk")
    child_chunks: List[ChunkResponse] = Field(description="Child chunks")
    sibling_chunks: List[ChunkResponse] = Field(description="Sibling chunks")
    hierarchy_path: List[str] = Field(description="Path from root to current chunk")


class ChunkHierarchyResponse(DataResponse[ChunkHierarchy]):
    """Response for chunk hierarchy"""
    data: ChunkHierarchy = Field(description="Chunk hierarchy information")


class ChunkContext(BaseModel):
    """Chunk context information"""
    document_title: str = Field(description="Source document title")
    surrounding_context: str = Field(description="Text around this chunk")
    section_hierarchy: List[str] = Field(description="Section hierarchy path")
    page_info: Optional[Dict[str, Any]] = Field(None, description="Page information if applicable")
    related_chunks: List[str] = Field(description="IDs of related chunks")


class ChunkWithContext(ChunkResponse):
    """Chunk with additional context information"""
    context: ChunkContext = Field(description="Additional context information")


class ChunkStats(BaseModel):
    """Chunk statistics"""
    total_chunks: int = Field(description="Total number of chunks")
    by_document: Dict[str, int] = Field(description="Chunk count by document")
    by_content_type: Dict[str, int] = Field(description="Chunk count by content type")
    avg_chunk_size: float = Field(description="Average chunk size in characters")
    avg_quality_score: float = Field(description="Average quality score")
    valid_chunks: int = Field(description="Number of valid chunks")
    chunks_with_embeddings: int = Field(description="Number of chunks with embeddings")
    most_common_language: Optional[str] = Field(None, description="Most common chunk language")


class ChunkStatsResponse(DataResponse[ChunkStats]):
    """Chunk statistics response"""
    data: ChunkStats = Field(description="Chunk statistics")


class ChunkEmbeddingRequest(BaseModel):
    """Request to generate/update chunk embeddings"""
    chunk_ids: Optional[List[str]] = Field(None, description="Specific chunk IDs (all if not provided)")
    embedding_model: Optional[str] = Field(None, description="Embedding model to use")
    force_regenerate: bool = Field(default=False, description="Regenerate existing embeddings")
    batch_size: int = Field(default=32, ge=1, le=100, description="Batch size for processing")


class ChunkEmbeddingResponse(BaseResponse):
    """Response for chunk embedding generation"""
    processed_count: int = Field(description="Number of chunks processed")
    failed_count: int = Field(description="Number of chunks that failed")
    processing_time_ms: float = Field(description="Total processing time")
    model_used: str = Field(description="Embedding model used")


class ChunkExportRequest(BaseModel):
    """Chunk export request"""
    chunk_ids: Optional[List[str]] = Field(None, description="Specific chunk IDs to export")
    document_id: Optional[str] = Field(None, description="Export all chunks from document")
    format: str = Field(description="Export format")
    include_embeddings: bool = Field(default=False, description="Include embedding vectors")
    include_metadata: bool = Field(default=True, description="Include chunk metadata")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'csv', 'txt']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v.lower()