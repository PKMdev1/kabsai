import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database import get_db
from ..models import User, File as FileModel, FileChunk
from ..schemas import File as FileSchema, FileCreate, FileUpdate, FileUploadResponse, SearchRequest, SearchResponse, SearchResult
# Authentication removed - no user system
from ..file_processor import file_processor
from ..rag_engine import rag_engine
from ..config import settings
import uuid
import json

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    project: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a file to the vault"""
    
    # Validate file size (only if limit is set)
    if settings.max_file_size > 0 and file.size and file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.upload_dir, unique_filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Process file
    result = file_processor.process_file(file_path)
    
    # Parse tags
    tag_list = []
    if tags:
        try:
            tag_list = json.loads(tags)
        except json.JSONDecodeError:
            tag_list = [tags]
    
    # Create file record
    db_file = FileModel(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file.size or 0,
        file_type=result['file_info']['file_type'],
        mime_type=result['file_info']['mime_type'],
        content_hash=result['file_info']['content_hash'],
        title=title,
        description=description,
        tags=tag_list,
        project=project,
        department=department,
        owner_id=1,  # Default user ID
        uploaded_by=1,  # Default user ID
        is_processed=result['success'],
        embedding_status="pending" if result['success'] else "failed"
    )
    
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    
    # Process for RAG if successful
    if result['success']:
        try:
            rag_engine.process_file_for_rag(db, db_file.id)
        except Exception as e:
            print(f"Error processing file for RAG: {e}")
    
    return FileUploadResponse(
        file_id=db_file.id,
        filename=db_file.filename,
        original_filename=db_file.original_filename,
        file_size=db_file.file_size,
        file_type=db_file.file_type,
        title=db_file.title,
        description=db_file.description,
        tags=db_file.tags,
        project=db_file.project,
        department=db_file.department,
                    upload_date=db_file.created_at,
        is_processed=db_file.is_processed,
        embedding_status=db_file.embedding_status,
        message="File uploaded successfully"
    )


@router.post("/upload-multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    project: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload multiple files to the vault with batch processing"""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 100:  # Increased limit to 100 files per batch
        raise HTTPException(status_code=400, detail="Maximum 100 files allowed per batch")
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    uploaded_files = []
    file_ids_for_rag = []
    
    for file in files:
        # Validate file size (only if limit is set)
        if settings.max_file_size > 0 and file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} too large. Maximum size is {settings.max_file_size} bytes"
            )
        
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ""
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.upload_dir, unique_filename)
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving file {file.filename}: {str(e)}")
        
        # Process file
        result = file_processor.process_file(file_path)
        
        # Create file record
        db_file = FileModel(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size or 0,
            file_type=result['file_info']['file_type'],
            mime_type=result['file_info']['mime_type'],
            content_hash=result['file_info']['content_hash'],
            title=file.filename,  # Use filename as default title
            description=f"Uploaded as part of batch upload",
            tags=[],
            project=project,
            department=department,
            owner_id=1,  # Default user ID
            uploaded_by=1,  # Default user ID
            is_processed=result['success'],
            embedding_status="pending" if result['success'] else "failed"
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        # Add to RAG processing list if successful
        if result['success']:
            file_ids_for_rag.append(db_file.id)
        
        uploaded_files.append(FileUploadResponse(
            file_id=db_file.id,
            filename=db_file.filename,
            original_filename=db_file.original_filename,
            file_size=db_file.file_size,
            file_type=db_file.file_type,
            title=db_file.title,
            description=db_file.description,
            tags=db_file.tags,
            project=db_file.project,
            department=db_file.department,
            upload_date=db_file.created_at,
            is_processed=db_file.is_processed,
            embedding_status=db_file.embedding_status,
            message="File uploaded successfully"
        ))
    
    # Process all files for RAG concurrently
    if file_ids_for_rag:
        try:
            rag_results = rag_engine.process_multiple_files_for_rag(db, file_ids_for_rag)
            print(f"RAG processing results: {rag_results}")
        except Exception as e:
            print(f"Error in batch RAG processing: {e}")
    
    return uploaded_files


@router.post("/reindex-batch")
async def reindex_multiple_files(
    file_ids: List[int],
    db: Session = Depends(get_db)
):
    """Reindex multiple files for RAG processing"""
    
    if not file_ids:
        raise HTTPException(status_code=400, detail="No file IDs provided")
    
    # No user verification needed - open access
    user_files = db.query(FileModel).filter(FileModel.id.in_(file_ids)).all()
    
    if len(user_files) != len(file_ids):
        raise HTTPException(status_code=404, detail="Some files not found")
    
    # Process files for RAG
    try:
        results = rag_engine.process_multiple_files_for_rag(db, file_ids)
        return {
            "message": "Batch reindexing completed",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during batch reindexing: {str(e)}")


@router.get("/", response_model=List[FileSchema])
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    project: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List files with optional filtering"""
    
    query = db.query(FileModel)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                FileModel.title.contains(search),
                FileModel.description.contains(search),
                FileModel.original_filename.contains(search),
                FileModel.tags.contains([search])
            )
        )
    
    if project:
        query = query.filter(FileModel.project == project)
    
    if department:
        query = query.filter(FileModel.department == department)
    
    if file_type:
        query = query.filter(FileModel.file_type == file_type)
    
    # Apply pagination
    files = query.offset(skip).limit(limit).all()
    
    return files


@router.get("/{file_id}", response_model=FileSchema)
async def get_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Get file details"""
    
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return file


@router.get("/{file_id}/download")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Download a file"""
    
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.exists(file.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file.file_path,
        filename=file.original_filename,
        media_type=file.mime_type
    )


@router.put("/{file_id}", response_model=FileSchema)
async def update_file(
    file_id: int,
    file_update: FileUpdate,
    db: Session = Depends(get_db)
):
    """Update file metadata"""
    
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # No permission check needed - open access
    
    # Update fields
    update_data = file_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(file, field, value)
    
    db.commit()
    db.refresh(file)
    
    return file


@router.delete("/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """Delete a file"""
    
    file = db.query(FileModel).filter(FileModel.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # No permission check needed - open access
    
    # Delete file chunks
    db.query(FileChunk).filter(FileChunk.file_id == file_id).delete()
    
    # Delete physical file
    if os.path.exists(file.file_path):
        os.remove(file.file_path)
    
    # Delete database record
    db.delete(file)
    db.commit()
    
    return {"message": "File deleted successfully"}


@router.post("/search", response_model=SearchResponse)
async def search_files(
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """Search files using RAG"""
    
    # Get similar chunks
    similar_chunks = rag_engine.search_similar_chunks(db, search_request.query, limit=search_request.limit)
    
    # Convert to search results
    results = []
    for item in similar_chunks:
        chunk = item['chunk']
        file = db.query(FileModel).filter(FileModel.id == chunk.file_id).first()
        
        if file:
            # Get snippet from chunk content
            content_snippet = chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            
            results.append(SearchResult(
                file_id=file.id,
                filename=file.original_filename,
                title=file.title,
                content_snippet=content_snippet,
                relevance_score=item['similarity'],
                tags=file.tags or [],
                project=file.project,
                department=file.department
            ))
    
    return SearchResponse(
        results=results,
        total_count=len(results),
        query=search_request.query
    )


@router.get("/projects/list")
async def list_projects(
    db: Session = Depends(get_db)
):
    """Get list of all projects"""
    
    projects = db.query(FileModel.project).filter(
        FileModel.project.isnot(None)
    ).distinct().all()
    
    return [project[0] for project in projects if project[0]]


@router.get("/departments/list")
async def list_departments(
    db: Session = Depends(get_db)
):
    """Get list of all departments"""
    
    departments = db.query(FileModel.department).filter(
        FileModel.department.isnot(None)
    ).distinct().all()
    
    return [dept[0] for dept in departments if dept[0]]
