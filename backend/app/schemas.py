from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str
    full_name: str
    role: str = "viewer"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# File schemas
class FileBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None
    department: Optional[str] = None


class FileCreate(FileBase):
    pass


class FileUpdate(FileBase):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None
    department: Optional[str] = None


class File(FileBase):
    id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    mime_type: str
    is_processed: bool
    is_indexed: bool
    embedding_status: str
    owner_id: int
    uploaded_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Enhanced File Upload Response
class FileUploadResponse(BaseModel):
    file_id: int
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    project: Optional[str] = None
    department: Optional[str] = None
    upload_date: datetime
    is_processed: bool
    embedding_status: str
    message: str


# Batch Upload Response
class BatchUploadResponse(BaseModel):
    successful: List[FileUploadResponse]
    failed: List[Dict[str, Any]]
    total_processed: int
    total_files: int


# Chat schemas
class ChatMessageBase(BaseModel):
    content: str
    message_type: str = "user"


class ChatMessageCreate(ChatMessageBase):
    session_id: Optional[str] = None


class ChatMessage(ChatMessageBase):
    id: int
    user_id: int
    session_id: str
    context_files: Optional[List[int]] = None
    context_chunks: Optional[List[int]] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    response_time: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Enhanced Chat Request
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_files: Optional[List[int]] = None  # Specific files to search in


# Enhanced Chat Response
class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_files: List[int]
    context_chunks: List[int]
    tokens_used: int
    model_used: str
    response_time: int
    files_analyzed: Optional[int] = None
    avg_similarity_score: Optional[float] = None
    context_length: Optional[int] = None


# Search schemas
class SearchRequest(BaseModel):
    query: str
    file_types: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    departments: Optional[List[str]] = None
    limit: int = 10


class SearchResult(BaseModel):
    file_id: int
    filename: str
    title: str
    file_type: str
    similarity_score: float
    content_preview: str
    chunk_id: int


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float


# Enhanced Search Results
class FileSearchResult(BaseModel):
    file_id: int
    filename: str
    title: str
    file_type: str
    chunks: List[Dict[str, Any]]
    total_relevance: float
    chunk_count: int
    avg_relevance: float


class ComprehensiveSearchResponse(BaseModel):
    query: str
    total_files_found: int
    total_chunks_found: int
    files: List[FileSearchResult]
    search_metadata: Dict[str, Any]


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Statistics schemas
class FileStatistics(BaseModel):
    total_files: int
    indexed_files: int
    total_chunks: int
    indexed_chunks: int
    total_tokens: int
    file_types: Dict[str, int]
    indexing_rate: float
    recent_files: List[Dict[str, Any]]


class ChatStatistics(BaseModel):
    total_messages: int
    total_sessions: int
    recent_activity: List[Dict[str, Any]]


class SystemCapabilities(BaseModel):
    max_concurrent_files: int
    min_similarity_threshold: float
    chunk_size: int
    embedding_model: str
    chat_model: str


class ComprehensiveStats(BaseModel):
    file_statistics: FileStatistics
    chat_statistics: ChatStatistics
    system_capabilities: SystemCapabilities


# XML Processing Schemas
class XMLSearchRequest(BaseModel):
    search_criteria: Dict[str, Any]  # tag, attributes, text, value


class XMLMatchResponse(BaseModel):
    file_id: int
    filename: str
    title: str
    matched_element: Dict[str, Any]
    relevance_score: float


class XMLSchemaResponse(BaseModel):
    file_id: int
    filename: str
    schema: Dict[str, Any]


# Batch Processing schemas
class BatchProcessingRequest(BaseModel):
    file_ids: List[int]


class BatchProcessingResponse(BaseModel):
    message: str
    results: Dict[str, Any]
    total_files: int


# Reindex schemas
class ReindexRequest(BaseModel):
    file_ids: Optional[List[int]] = None  # If None, reindex all files


class ReindexResponse(BaseModel):
    message: str
    results: Dict[str, Any]
    total_files: int
