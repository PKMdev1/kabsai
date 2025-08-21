from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    role = Column(String, default="viewer")  # admin, contributor, viewer
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    files = relationship("File", back_populates="owner")
    chat_messages = relationship("ChatMessage", back_populates="user")


class File(Base):
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    original_filename = Column(String)
    file_path = Column(String)  # S3 path or local path
    file_size = Column(Integer)
    file_type = Column(String)
    mime_type = Column(String)
    content_hash = Column(String, index=True)
    
    # Metadata
    title = Column(String)
    description = Column(Text)
    tags = Column(JSON)  # List of tags
    project = Column(String, index=True)
    department = Column(String, index=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    is_indexed = Column(Boolean, default=False)
    embedding_status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Ownership and audit
    owner_id = Column(Integer, ForeignKey("users.id"))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="files")
    chat_messages = relationship("ChatMessage", back_populates="file")


class FileChunk(Base):
    __tablename__ = "file_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"))
    chunk_index = Column(Integer)
    content = Column(Text)
    embedding = Column(Text)  # JSON string of embedding vector
    metadata = Column(JSON)  # Additional metadata for the chunk
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, index=True)
    message_type = Column(String)  # user, assistant, system
    content = Column(Text)
    
    # RAG context
    context_files = Column(JSON)  # List of file IDs used for context
    context_chunks = Column(JSON)  # List of chunk IDs used for context
    
    # Metadata
    tokens_used = Column(Integer)
    model_used = Column(String)
    response_time = Column(Integer)  # milliseconds
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_messages")
    file = relationship("File", back_populates="chat_messages")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)  # file_upload, file_delete, chat_query, login, etc.
    resource_type = Column(String)  # file, chat, user, etc.
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
