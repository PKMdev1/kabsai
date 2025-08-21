from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import uuid
import time
from datetime import datetime

from ..database import get_db
from ..models import User, ChatMessage, File
# Authentication removed - no user system
from ..rag_engine import rag_engine
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat_with_rag(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with RAG-powered assistant for laser-focused responses from ALL files."""
    
    # Check if this is a pricing-related query
    pricing_focus = rag_engine._is_pricing_query(request.message)
    
    try:
        start_time = time.time()
        
        # Generate session ID if not provided
        session_id = request.session_id or f"session_{int(time.time())}"
        
        # Use RAG engine to get response (searches ALL files by default)
        rag_result = rag_engine.chat_with_rag(
            db=db,
            query=request.message,
            user_id=1,  # Default user ID
            session_id=session_id,
            context_files=request.context_files,  # If None, searches ALL files
            pricing_focus=pricing_focus  # Enable pricing focus for pricing queries
        )
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # milliseconds
        
        # Save user message to database
        user_message = ChatMessage(
            user_id=1,  # Default user ID
            session_id=session_id,
            message_type="user",
            content=request.message,
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # Save assistant response to database with enhanced metadata
        assistant_message = ChatMessage(
            user_id=1,  # Default user ID
            session_id=session_id,
            message_type="assistant",
            content=rag_result['response'],
            context_files=rag_result['context_files'],
            context_chunks=rag_result['context_chunks'],
            tokens_used=len(rag_result['response'].split()),  # Approximate token count
            model_used="gpt-5",  # Latest ChatGPT model (GPT-5)
            response_time=response_time,
            created_at=datetime.now()
        )
        db.add(assistant_message)
        
        db.commit()
        
        return ChatResponse(
            response=rag_result['response'],
            session_id=session_id,
            context_files=rag_result['context_files'],
            context_chunks=rag_result['context_chunks'],
            tokens_used=assistant_message.tokens_used,
            model_used=assistant_message.model_used,
            response_time=response_time,
            files_analyzed=rag_result.get('files_analyzed', 0),
            avg_similarity_score=rag_result.get('avg_similarity_score', 0),
            context_length=rag_result.get('context_length', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")

@router.post("/search-pricing")
async def search_pricing_files(
    query: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Specialized search for pricing-related content across all files."""
    
    try:
                # Use specialized pricing search
        similar_chunks = rag_engine.search_pricing_specific(
            db=db,
            query=query,
            limit=limit,
            user_id=1  # Default user ID
        )
        
        # Group results by file
        file_results = {}
        for item in similar_chunks:
            chunk = item['chunk']
            file = item['file']
            similarity = item['similarity']
            has_pricing = item.get('has_pricing', False)
            
            if file.id not in file_results:
                file_results[file.id] = {
                    'file_id': file.id,
                    'filename': file.original_filename,
                    'title': file.title,
                    'file_type': file.file_type,
                    'chunks': [],
                    'total_relevance': 0,
                    'chunk_count': 0,
                    'pricing_chunks': 0
                }
            
            file_results[file.id]['chunks'].append({
                'chunk_id': chunk.id,
                'content': chunk.content,
                'similarity_score': similarity,
                'token_count': chunk.token_count,
                'has_pricing': has_pricing
            })
            file_results[file.id]['total_relevance'] += similarity
            file_results[file.id]['chunk_count'] += 1
            if has_pricing:
                file_results[file.id]['pricing_chunks'] += 1
        
        # Calculate average relevance for each file
        for file_data in file_results.values():
            file_data['avg_relevance'] = file_data['total_relevance'] / file_data['chunk_count']
        
        # Sort files by average relevance
        sorted_files = sorted(
            file_results.values(), 
            key=lambda x: x['avg_relevance'], 
            reverse=True
        )
        
        return {
            'query': query,
            'search_type': 'pricing_specific',
            'total_files_found': len(sorted_files),
            'total_chunks_found': len(similar_chunks),
            'files': sorted_files,
            'search_metadata': {
                'min_similarity_threshold': rag_engine.min_similarity_threshold,
                'search_limit': limit,
                'pricing_boost_applied': True
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching pricing files: {str(e)}")

@router.post("/search-product-pricing")
async def search_product_pricing_matching(
    query: str,
    limit: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Specialized search for product-pricing matching across all files."""
    
    try:
        # Use specialized product-pricing matching search
        similar_chunks = rag_engine.search_product_pricing_matching(
            db=db, 
            query=query, 
            limit=limit, 
            user_id=current_user.id
        )
        
        # Group results by file
        file_results = {}
        for item in similar_chunks:
            chunk = item['chunk']
            file = item['file']
            similarity = item['similarity']
            has_pricing = item.get('has_pricing', False)
            has_product = item.get('has_product', False)
            product_models = item.get('product_models', [])
            boost_multiplier = item.get('boost_multiplier', 1.0)
            
            if file.id not in file_results:
                file_results[file.id] = {
                    'file_id': file.id,
                    'filename': file.original_filename,
                    'title': file.title,
                    'file_type': file.file_type,
                    'chunks': [],
                    'total_relevance': 0,
                    'chunk_count': 0,
                    'pricing_chunks': 0,
                    'product_chunks': 0,
                    'product_models_found': set()
                }
            
            file_results[file.id]['chunks'].append({
                'chunk_id': chunk.id,
                'content': chunk.content,
                'similarity_score': similarity,
                'token_count': chunk.token_count,
                'has_pricing': has_pricing,
                'has_product': has_product,
                'product_models': product_models,
                'boost_multiplier': boost_multiplier
            })
            file_results[file.id]['total_relevance'] += similarity
            file_results[file.id]['chunk_count'] += 1
            if has_pricing:
                file_results[file.id]['pricing_chunks'] += 1
            if has_product:
                file_results[file.id]['product_chunks'] += 1
            file_results[file.id]['product_models_found'].update(product_models)
        
        # Calculate average relevance and convert sets to lists for JSON serialization
        for file_data in file_results.values():
            file_data['avg_relevance'] = file_data['total_relevance'] / file_data['chunk_count']
            file_data['product_models_found'] = list(file_data['product_models_found'])
        
        # Sort files by average relevance
        sorted_files = sorted(
            file_results.values(), 
            key=lambda x: x['avg_relevance'], 
            reverse=True
        )
        
        return {
            'query': query,
            'search_type': 'product_pricing_matching',
            'total_files_found': len(sorted_files),
            'total_chunks_found': len(similar_chunks),
            'files': sorted_files,
            'search_metadata': {
                'min_similarity_threshold': rag_engine.min_similarity_threshold,
                'search_limit': limit,
                'product_pricing_boost_applied': True,
                'matching_algorithm': 'enhanced_product_pricing_matching'
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching product-pricing matching: {str(e)}")

@router.post("/generate-quote")
async def generate_pricing_quote(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive pricing quotes from all uploaded files."""
    
    try:
        start_time = time.time()
        
        # Generate session ID if not provided
        session_id = request.session_id or f"quote_session_{current_user.id}_{int(time.time())}"
        
        # Use RAG engine with pricing focus for quote generation
        rag_result = rag_engine.chat_with_rag(
            db=db,
            query=f"Generate a comprehensive quote for: {request.message}. Include all pricing details, product specifications, terms and conditions, and any applicable discounts or promotions.",
            user_id=current_user.id,
            session_id=session_id,
            context_files=request.context_files,
            pricing_focus=True  # Force pricing focus for quote generation
        )
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # milliseconds
        
        # Save quote request to database
        user_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            message_type="user",
            content=f"Quote Request: {request.message}",
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # Save quote response to database
        quote_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            message_type="assistant",
            content=rag_result['response'],
            context_files=rag_result['context_files'],
            context_chunks=rag_result['context_chunks'],
            tokens_used=len(rag_result['response'].split()),
            model_used="gpt-5",
            response_time=response_time,
            created_at=datetime.now()
        )
        db.add(quote_message)
        
        db.commit()
        
        return ChatResponse(
            response=rag_result['response'],
            session_id=session_id,
            context_files=rag_result['context_files'],
            context_chunks=rag_result['context_chunks'],
            tokens_used=quote_message.tokens_used,
            model_used=quote_message.model_used,
            response_time=response_time,
            files_analyzed=rag_result.get('files_analyzed', 0),
            avg_similarity_score=rag_result.get('avg_similarity_score', 0),
            context_length=rag_result.get('context_length', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quote: {str(e)}")

@router.post("/generate-product-pricing-report")
async def generate_product_pricing_report(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive product-pricing matching report from all uploaded files."""
    
    try:
        start_time = time.time()
        
        # Generate session ID if not provided
        session_id = request.session_id or f"product_pricing_report_{current_user.id}_{int(time.time())}"
        
        # Use RAG engine with product-pricing matching focus
        rag_result = rag_engine.chat_with_rag(
            db=db,
            query=f"Generate a comprehensive product-pricing matching report for: {request.message}. Include all product models, SKUs, part numbers, their exact pricing from pricing sheets, specifications, and cross-reference validation. Ensure accurate matching between product catalogs and pricing sheets.",
            user_id=current_user.id,
            session_id=session_id,
            context_files=request.context_files,
            pricing_focus=True  # Force pricing focus for product-pricing matching
        )
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # milliseconds
        
        # Save report request to database
        user_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            message_type="user",
            content=f"Product-Pricing Report Request: {request.message}",
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # Save report response to database
        report_message = ChatMessage(
            user_id=current_user.id,
            session_id=session_id,
            message_type="assistant",
            content=rag_result['response'],
            context_files=rag_result['context_files'],
            context_chunks=rag_result['context_chunks'],
            tokens_used=len(rag_result['response'].split()),
            model_used="gpt-5",
            response_time=response_time,
            created_at=datetime.now()
        )
        db.add(report_message)
        
        db.commit()
        
        return ChatResponse(
            response=rag_result['response'],
            session_id=session_id,
            context_files=rag_result['context_files'],
            context_chunks=rag_result['context_chunks'],
            tokens_used=report_message.tokens_used,
            model_used=report_message.model_used,
            response_time=response_time,
            files_analyzed=rag_result.get('files_analyzed', 0),
            avg_similarity_score=rag_result.get('avg_similarity_score', 0),
            context_length=rag_result.get('context_length', 0)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating product-pricing report: {str(e)}")

@router.post("/search-all")
async def search_all_files(
    query: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search across ALL uploaded files for comprehensive results."""
    
    try:
        # Search across all indexed files
        similar_chunks = rag_engine.search_similar_chunks(
            db=db, 
            query=query, 
            limit=limit, 
            user_id=current_user.id
        )
        
        # Group results by file
        file_results = {}
        for item in similar_chunks:
            chunk = item['chunk']
            file = item['file']
            similarity = item['similarity']
            
            if file.id not in file_results:
                file_results[file.id] = {
                    'file_id': file.id,
                    'filename': file.original_filename,
                    'title': file.title,
                    'file_type': file.file_type,
                    'chunks': [],
                    'total_relevance': 0,
                    'chunk_count': 0
                }
            
            file_results[file.id]['chunks'].append({
                'chunk_id': chunk.id,
                'content': chunk.content,
                'similarity_score': similarity,
                'token_count': chunk.token_count
            })
            file_results[file.id]['total_relevance'] += similarity
            file_results[file.id]['chunk_count'] += 1
        
        # Calculate average relevance for each file
        for file_data in file_results.values():
            file_data['avg_relevance'] = file_data['total_relevance'] / file_data['chunk_count']
        
        # Sort files by average relevance
        sorted_files = sorted(
            file_results.values(), 
            key=lambda x: x['avg_relevance'], 
            reverse=True
        )
        
        return {
            'query': query,
            'total_files_found': len(sorted_files),
            'total_chunks_found': len(similar_chunks),
            'files': sorted_files,
            'search_metadata': {
                'min_similarity_threshold': rag_engine.min_similarity_threshold,
                'search_limit': limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching files: {str(e)}")

@router.post("/search-by-type")
async def search_by_file_type(
    query: str,
    file_types: List[str],
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search within specific file types across all files."""
    
    try:
        # Get files of specified types
        files = db.query(File).filter(
            File.uploaded_by == current_user.id,
            File.file_type.in_(file_types),
            File.is_indexed == True
        ).all()
        
        if not files:
            return {
                'query': query,
                'file_types': file_types,
                'total_files_found': 0,
                'total_chunks_found': 0,
                'files': []
            }
        
        # Search within these files
        file_ids = [f.id for f in files]
        rag_result = rag_engine.chat_with_rag(
            db=db,
            query=query,
            user_id=current_user.id,
            context_files=file_ids
        )
        
        return {
            'query': query,
            'file_types': file_types,
            'response': rag_result['response'],
            'files_analyzed': rag_result.get('files_analyzed', 0),
            'avg_similarity_score': rag_result.get('avg_similarity_score', 0),
            'context_files': rag_result['context_files'],
            'files_used': rag_result['files_used']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching by file type: {str(e)}")

@router.get("/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for the user."""
    
    query = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)
    
    if session_id:
        query = query.filter(ChatMessage.session_id == session_id)
    
    messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
    
    # Convert to response format
    history = []
    for message in reversed(messages):  # Reverse to get chronological order
        history.append({
            'id': message.id,
            'session_id': message.session_id,
            'message_type': message.message_type,
            'content': message.content,
            'context_files': message.context_files,
            'context_chunks': message.context_chunks,
            'tokens_used': message.tokens_used,
            'model_used': message.model_used,
            'response_time': message.response_time,
            'created_at': message.created_at.isoformat()
        })
    
    return {
        'messages': history,
        'total_messages': len(history)
    }

@router.get("/sessions")
async def get_chat_sessions(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of chat sessions for the user."""
    
    # Get unique session IDs with latest message info
    sessions = db.query(
        ChatMessage.session_id,
        ChatMessage.content,
        ChatMessage.created_at,
        ChatMessage.message_type
    ).filter(
        ChatMessage.user_id == current_user.id
    ).order_by(
        ChatMessage.created_at.desc()
    ).all()
    
    # Group by session
    session_data = {}
    for session in sessions:
        session_id = session.session_id
        if session_id not in session_data:
            session_data[session_id] = {
                'session_id': session_id,
                'last_message': session.content,
                'last_message_type': session.message_type,
                'last_activity': session.created_at.isoformat(),
                'message_count': 0
            }
        session_data[session_id]['message_count'] += 1
    
    # Convert to list and sort by last activity
    sessions_list = list(session_data.values())
    sessions_list.sort(key=lambda x: x['last_activity'], reverse=True)
    
    return {
        'sessions': sessions_list[:limit],
        'total_sessions': len(sessions_list)
    }

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session and all its messages."""
    
    # Delete all messages in the session
    deleted_count = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == current_user.id
    ).delete()
    
    db.commit()
    
    return {
        'message': f"Session {session_id} deleted successfully",
        'messages_deleted': deleted_count
    }

@router.get("/stats")
async def get_chat_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive chat and file statistics."""
    
    try:
        # Get file statistics from RAG engine
        file_stats = rag_engine.get_file_statistics(db, current_user.id)
        
        # Get chat statistics
        total_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).count()
        
        total_sessions = db.query(ChatMessage.session_id).filter(
            ChatMessage.user_id == current_user.id
        ).distinct().count()
        
        # Get recent activity
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.user_id == current_user.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        recent_activity = []
        for msg in recent_messages:
            recent_activity.append({
                'message_type': msg.message_type,
                'content_preview': msg.content[:100] + "..." if len(msg.content) > 100 else msg.content,
                'created_at': msg.created_at.isoformat(),
                'session_id': msg.session_id
            })
        
        return {
            'file_statistics': file_stats,
            'chat_statistics': {
                'total_messages': total_messages,
                'total_sessions': total_sessions,
                'recent_activity': recent_activity
            },
            'system_capabilities': {
                'max_concurrent_files': rag_engine.max_concurrent_files,
                'min_similarity_threshold': rag_engine.min_similarity_threshold,
                'chunk_size': rag_engine.chunk_size,
                'embedding_model': rag_engine.embedding_model,
                'chat_model': rag_engine.chat_model  # Latest GPT-5 model
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.post("/reindex/{file_id}")
async def reindex_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reindex a specific file for RAG processing."""
    
    # Verify file ownership
    file_record = db.query(File).filter(
        File.id == file_id,
        File.uploaded_by == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        success = rag_engine.process_file_for_rag(db, file_id)
        if success:
            return {"message": f"File {file_record.original_filename} reindexed successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to reindex file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing file: {str(e)}")

@router.post("/reindex-all")
async def reindex_all_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reindex all user files for RAG processing."""
    
    # Get all user files
    user_files = db.query(File).filter(
        File.uploaded_by == current_user.id
    ).all()
    
    if not user_files:
        return {"message": "No files found to reindex"}
    
    file_ids = [f.id for f in user_files]
    
    try:
        results = rag_engine.process_multiple_files_for_rag(db, file_ids)
        return {
            "message": "Batch reindexing completed",
            "results": results,
            "total_files": len(file_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during batch reindexing: {str(e)}")
