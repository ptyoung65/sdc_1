"""
Vector Database Service with Document Permission Filtering
Enterprise-grade unstructured data vector DB with RBAC/ABAC access control
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
import os
import uuid
from datetime import datetime
import json
import logging
from contextlib import asynccontextmanager

# Vector database and ML imports
try:
    from pymilvus import (
        connections, Collection, FieldSchema, CollectionSchema,
        DataType, utility, MilvusException
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False

# Document processing imports
import numpy as np
# from sentence_transformers import SentenceTransformer  # PyTorch/Transformers disabled
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Models
class DocumentMetadata(BaseModel):
    """Comprehensive document metadata for enterprise access control"""
    doc_id: str = Field(..., description="Original document unique ID")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    filename: str = Field(..., description="Original filename")
    source: str = Field(..., description="Document source path")
    page_number: Optional[int] = Field(None, description="Page number in original document")
    author: Optional[str] = Field(None, description="Document author")
    creation_date: str = Field(..., description="Document creation date")
    document_type: str = Field(default="unstructured_doc", description="Document type")
    
    # Permission management fields
    access_control_list: List[str] = Field(default=[], description="ACL - user/group IDs with access")
    roles: List[str] = Field(default=[], description="Required roles for access")
    classification: str = Field(default="internal", description="Security classification")
    department: Optional[str] = Field(None, description="Owning department")
    project_id: Optional[str] = Field(None, description="Associated project ID")
    
    # Additional attributes for ABAC
    attributes: Dict[str, Any] = Field(default={}, description="Custom attributes for ABAC")

class VectorRecord(BaseModel):
    """Vector database record with embeddings and metadata"""
    id: str
    vector: List[float]
    text: str
    metadata: DocumentMetadata

class UserContext(BaseModel):
    """User context for permission evaluation"""
    user_id: str
    roles: List[str] = Field(default=[])
    department: Optional[str] = None
    clearance_level: Optional[str] = None
    project_access: List[str] = Field(default=[])
    attributes: Dict[str, Any] = Field(default={})

class SearchRequest(BaseModel):
    """Vector search request with permission context"""
    query: str
    user_context: UserContext
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata filters")

class SearchResponse(BaseModel):
    """Search response with permission-filtered results"""
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    accessible_count: int
    filtered_count: int
    search_time_ms: float

class DocumentIngestRequest(BaseModel):
    """Document ingestion request"""
    documents: List[Dict[str, Any]]
    user_context: UserContext
    processing_options: Optional[Dict[str, Any]] = Field(default={})

# Vector Database Manager
class VectorDBManager:
    """Manages vector database operations with permission filtering"""
    
    def __init__(self):
        self.collection_name = "enterprise_documents"
        self.embedding_model = None
        self.collection = None
        self.dimension = 384  # sentence-transformers/all-MiniLM-L6-v2
        
    async def initialize(self):
        """Initialize vector database connection and schema"""
        try:
            if not MILVUS_AVAILABLE:
                logger.warning("⚠️ Milvus not available, using mock implementation")
                return
                
            # Connect to Milvus
            milvus_host = os.getenv("MILVUS_HOST", "localhost")
            milvus_port = os.getenv("MILVUS_PORT", "19530")
            
            connections.connect(
                alias="default",
                host=milvus_host,
                port=milvus_port
            )
            
            # Initialize embedding model
            # self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # PyTorch/Transformers disabled
            self.embedding_model = None  # Using mock embeddings instead
            logger.info("🤖 Using mock embeddings (PyTorch/Transformers disabled)")
            
            # Create collection if not exists
            await self._create_collection()
            
            logger.info("✅ Vector database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize vector database: {e}")
            raise
    
    async def _create_collection(self):
        """Create Milvus collection with enterprise metadata schema"""
        if utility.has_collection(self.collection_name):
            self.collection = Collection(self.collection_name)
            logger.info(f"📚 Using existing collection: {self.collection_name}")
            return
        
        # Define collection schema with comprehensive metadata
        fields = [
            # Vector fields
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=255, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dimension),
            
            # Content fields
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
            
            # Document metadata
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="filename", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="page_number", dtype=DataType.INT32),
            FieldSchema(name="author", dtype=DataType.VARCHAR, max_length=255),
            FieldSchema(name="creation_date", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="document_type", dtype=DataType.VARCHAR, max_length=100),
            
            # Permission fields
            FieldSchema(name="access_control_list", dtype=DataType.VARCHAR, max_length=2048),
            FieldSchema(name="roles", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="classification", dtype=DataType.VARCHAR, max_length=50),
            FieldSchema(name="department", dtype=DataType.VARCHAR, max_length=100),
            FieldSchema(name="project_id", dtype=DataType.VARCHAR, max_length=255),
            
            # Extended attributes (JSON string)
            FieldSchema(name="attributes", dtype=DataType.VARCHAR, max_length=4096),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="Enterprise document vectors with permission metadata"
        )
        
        self.collection = Collection(
            name=self.collection_name,
            schema=schema
        )
        
        # Create index for vector field
        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="vector",
            index_params=index_params
        )
        
        logger.info(f"✅ Created collection with schema: {self.collection_name}")
    
    def _evaluate_permission(self, metadata: Dict[str, Any], user_context: UserContext) -> bool:
        """Evaluate document access permission using RBAC/ABAC"""
        try:
            # Parse access control list
            acl = json.loads(metadata.get("access_control_list", "[]"))
            required_roles = json.loads(metadata.get("roles", "[]"))
            
            # Check direct user access
            if user_context.user_id in acl:
                return True
            
            # Check role-based access (RBAC)
            user_roles = set(user_context.roles)
            required_roles_set = set(required_roles)
            if user_roles.intersection(required_roles_set):
                return True
            
            # Check department access
            if (metadata.get("department") and 
                metadata.get("department") == user_context.department):
                return True
            
            # Check project access
            project_id = metadata.get("project_id")
            if project_id and project_id in user_context.project_access:
                return True
            
            # Check classification clearance level
            classification = metadata.get("classification", "internal")
            user_clearance = user_context.clearance_level
            
            clearance_hierarchy = {
                "public": 0,
                "internal": 1,
                "confidential": 2,
                "secret": 3,
                "top_secret": 4
            }
            
            if (user_clearance and 
                clearance_hierarchy.get(user_clearance, 0) >= 
                clearance_hierarchy.get(classification, 1)):
                return True
            
            # ABAC - Attribute-based access control
            attributes = json.loads(metadata.get("attributes", "{}"))
            for attr_key, attr_value in attributes.items():
                user_attr_value = user_context.attributes.get(attr_key)
                if user_attr_value and user_attr_value == attr_value:
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Permission evaluation error: {e}")
            return False
    
    async def search_with_permissions(self, search_request: SearchRequest) -> SearchResponse:
        """Perform permission-filtered vector search"""
        start_time = datetime.now()
        
        try:
            if not MILVUS_AVAILABLE or not self.embedding_model:
                # Mock response for development
                return SearchResponse(
                    query=search_request.query,
                    results=[],
                    total_found=0,
                    accessible_count=0,
                    filtered_count=0,
                    search_time_ms=10.0
                )
            
            # Generate query embedding
            # query_embedding = self.embedding_model.encode([search_request.query])[0].tolist()  # PyTorch/Transformers disabled
            # Using mock random embedding instead
            query_embedding = np.random.rand(self.dimension).tolist()
            
            # Build base search parameters
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10}
            }
            
            # Load collection
            self.collection.load()
            
            # Perform vector search (get more results for permission filtering)
            search_top_k = min(search_request.top_k * 3, 300)  # Get extra results for filtering
            
            results = self.collection.search(
                data=[query_embedding],
                anns_field="vector",
                param=search_params,
                limit=search_top_k,
                output_fields=[
                    "text", "doc_id", "chunk_id", "filename", "source",
                    "page_number", "author", "creation_date", "document_type",
                    "access_control_list", "roles", "classification",
                    "department", "project_id", "attributes"
                ]
            )
            
            # Filter results by permissions
            accessible_results = []
            total_found = len(results[0]) if results and len(results) > 0 else 0
            
            for hit in results[0] if results and len(results) > 0 else []:
                # Create metadata dict from hit entity
                metadata = {}
                for field in hit.entity.fields:
                    metadata[field.name] = field.value
                
                # Check permission
                if self._evaluate_permission(metadata, search_request.user_context):
                    # Check similarity threshold
                    if hit.score >= search_request.similarity_threshold:
                        accessible_results.append({
                            "id": hit.id,
                            "score": float(hit.score),
                            "text": hit.entity.get("text"),
                            "metadata": {
                                "doc_id": hit.entity.get("doc_id"),
                                "chunk_id": hit.entity.get("chunk_id"),
                                "filename": hit.entity.get("filename"),
                                "source": hit.entity.get("source"),
                                "page_number": hit.entity.get("page_number"),
                                "author": hit.entity.get("author"),
                                "creation_date": hit.entity.get("creation_date"),
                                "classification": hit.entity.get("classification"),
                                "department": hit.entity.get("department")
                            }
                        })
                
                # Limit results
                if len(accessible_results) >= search_request.top_k:
                    break
            
            end_time = datetime.now()
            search_time_ms = (end_time - start_time).total_seconds() * 1000
            
            return SearchResponse(
                query=search_request.query,
                results=accessible_results,
                total_found=total_found,
                accessible_count=len(accessible_results),
                filtered_count=total_found - len(accessible_results),
                search_time_ms=search_time_ms
            )
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    async def ingest_documents(self, ingest_request: DocumentIngestRequest) -> Dict[str, Any]:
        """Ingest documents into vector database with metadata"""
        try:
            if not MILVUS_AVAILABLE or not self.embedding_model:
                return {
                    "status": "success",
                    "message": "Mock ingestion (Milvus not available)",
                    "processed_count": len(ingest_request.documents),
                    "failed_count": 0
                }
            
            processed_count = 0
            failed_count = 0
            insert_data = []
            
            for doc in ingest_request.documents:
                try:
                    # Extract text content
                    text_content = doc.get("text", "")
                    if not text_content:
                        failed_count += 1
                        continue
                    
                    # Generate embedding
                    # embedding = self.embedding_model.encode([text_content])[0].tolist()  # PyTorch/Transformers disabled
                    # Using mock random embedding instead
                    embedding = np.random.rand(self.dimension).tolist()
                    
                    # Create document ID if not provided
                    doc_id = doc.get("doc_id", str(uuid.uuid4()))
                    chunk_id = doc.get("chunk_id", f"{doc_id}_chunk_{processed_count}")
                    record_id = f"{doc_id}_{chunk_id}"
                    
                    # Prepare metadata
                    metadata = doc.get("metadata", {})
                    
                    # Create record for insertion
                    record = {
                        "id": record_id,
                        "vector": embedding,
                        "text": text_content,
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "filename": metadata.get("filename", "unknown"),
                        "source": metadata.get("source", ""),
                        "page_number": metadata.get("page_number", 0),
                        "author": metadata.get("author", ""),
                        "creation_date": metadata.get("creation_date", datetime.now().isoformat()),
                        "document_type": metadata.get("document_type", "unstructured_doc"),
                        "access_control_list": json.dumps(metadata.get("access_control_list", [])),
                        "roles": json.dumps(metadata.get("roles", [])),
                        "classification": metadata.get("classification", "internal"),
                        "department": metadata.get("department", ""),
                        "project_id": metadata.get("project_id", ""),
                        "attributes": json.dumps(metadata.get("attributes", {}))
                    }
                    
                    insert_data.append(record)
                    processed_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Failed to process document: {e}")
                    failed_count += 1
            
            # Insert into Milvus
            if insert_data:
                # Prepare data for insertion
                insert_fields = {
                    "id": [record["id"] for record in insert_data],
                    "vector": [record["vector"] for record in insert_data],
                    "text": [record["text"] for record in insert_data],
                    "doc_id": [record["doc_id"] for record in insert_data],
                    "chunk_id": [record["chunk_id"] for record in insert_data],
                    "filename": [record["filename"] for record in insert_data],
                    "source": [record["source"] for record in insert_data],
                    "page_number": [record["page_number"] for record in insert_data],
                    "author": [record["author"] for record in insert_data],
                    "creation_date": [record["creation_date"] for record in insert_data],
                    "document_type": [record["document_type"] for record in insert_data],
                    "access_control_list": [record["access_control_list"] for record in insert_data],
                    "roles": [record["roles"] for record in insert_data],
                    "classification": [record["classification"] for record in insert_data],
                    "department": [record["department"] for record in insert_data],
                    "project_id": [record["project_id"] for record in insert_data],
                    "attributes": [record["attributes"] for record in insert_data],
                }
                
                self.collection.insert(list(insert_fields.values()))
                self.collection.flush()
            
            return {
                "status": "success",
                "message": f"Successfully ingested {processed_count} documents",
                "processed_count": processed_count,
                "failed_count": failed_count,
                "total_records": len(insert_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Document ingestion error: {e}")
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

# Global vector DB manager
vector_db_manager = VectorDBManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting Vector Database Service...")
    await vector_db_manager.initialize()
    logger.info("✅ Vector Database Service ready")
    
    yield
    
    # Shutdown
    logger.info("🔌 Shutting down Vector Database Service...")

# FastAPI app
app = FastAPI(
    title="Vector Database Service with Permission Filtering",
    description="Enterprise-grade vector database service with RBAC/ABAC access control",
    version="1.0.0",
    lifespan=lifespan
)

# Authentication helper
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Extract user context from JWT token (simplified for demo)"""
    # In production, validate JWT and extract user claims
    # For now, return mock user context
    return {
        "user_id": "user-123",
        "roles": ["employee", "finance"],
        "department": "finance",
        "clearance_level": "confidential",
        "project_access": ["proj-001", "proj-002"]
    }

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "vector-db-service",
        "milvus_available": MILVUS_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    }

# Vector search with permission filtering
@app.post("/api/v1/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search documents with permission filtering"""
    logger.info(f"🔍 Search request: '{search_request.query}' by user: {search_request.user_context.user_id}")
    
    try:
        results = await vector_db_manager.search_with_permissions(search_request)
        
        logger.info(f"✅ Search completed: {results.accessible_count}/{results.total_found} accessible results")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Document ingestion
@app.post("/api/v1/ingest")
async def ingest_documents(
    ingest_request: DocumentIngestRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Ingest documents into vector database"""
    logger.info(f"📥 Document ingestion: {len(ingest_request.documents)} documents by user: {ingest_request.user_context.user_id}")
    
    try:
        result = await vector_db_manager.ingest_documents(ingest_request)
        
        logger.info(f"✅ Ingestion completed: {result['processed_count']} processed, {result['failed_count']} failed")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Get collection statistics
@app.get("/api/v1/stats")
async def get_collection_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get vector collection statistics"""
    try:
        if not MILVUS_AVAILABLE or not vector_db_manager.collection:
            return {
                "collection_name": vector_db_manager.collection_name,
                "total_entities": 0,
                "status": "milvus_unavailable"
            }
        
        vector_db_manager.collection.load()
        stats = vector_db_manager.collection.num_entities
        
        return {
            "collection_name": vector_db_manager.collection_name,
            "total_entities": stats,
            "status": "active",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)