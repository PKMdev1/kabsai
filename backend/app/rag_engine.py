import openai
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

from .config import settings
from .models import File, FileChunk
from .file_processor import FileProcessor

# Initialize OpenAI client
openai.api_key = settings.openai_api_key

class RAGEngine:
    def __init__(self):
        self.file_processor = FileProcessor()
        self.embedding_model = "text-embedding-3-small"
        self.chat_model = "gpt-5"  # Latest ChatGPT model (GPT-5)
        self.max_tokens = 16000  # Increased for larger context handling
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_concurrent_files = 100  # Process multiple files concurrently (increased for unlimited processing)
        self.min_similarity_threshold = 0.3  # Minimum similarity for relevance
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for text using OpenAI."""
        try:
            response = openai.Embedding.create(
                model=self.embedding_model,
                input=text
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return []
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _contains_pricing_content(self, text: str) -> bool:
        """Check if text contains pricing-related content."""
        pricing_keywords = [
            'price', 'cost', 'rate', 'quote', 'pricing', 'amount', 'total', 'sum',
            'dollar', 'euro', 'usd', 'eur', 'currency', 'payment', 'invoice',
            'discount', 'markup', 'margin', 'profit', 'revenue', 'fee', 'charge',
            'subscription', 'license', 'per unit', 'per item', 'bulk', 'volume',
            'wholesale', 'retail', 'msrp', 'list price', 'sale price', 'offer',
            'deal', 'promotion', 'special', 'bundle', 'package', 'tier', 'level'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in pricing_keywords)
    
    def _contains_product_content(self, text: str) -> bool:
        """Check if text contains product-related content."""
        product_keywords = [
            'model', 'product', 'item', 'sku', 'part number', 'part #', 'pn#',
            'serial', 'catalog', 'specification', 'specs', 'features', 'description',
            'manufacturer', 'brand', 'make', 'type', 'category', 'family', 'series',
            'version', 'edition', 'variant', 'configuration', 'option', 'package',
            'kit', 'bundle', 'set', 'unit', 'piece', 'component', 'accessory'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in product_keywords)
    
    def _extract_product_models(self, text: str) -> List[str]:
        """Extract potential product models from text."""
        import re
        
        # Common product model patterns
        patterns = [
            r'\b[A-Z]{2,4}\d{2,4}[A-Z]?\b',  # AB123, ABC1234, etc.
            r'\b[A-Z]+\d{3,6}\b',  # ABC123456
            r'\b\d{2,4}[A-Z]{2,4}\b',  # 123AB, 1234ABC
            r'\b[A-Z]{2,}\s*\d{2,}\b',  # AB 123, ABC 1234
            r'\bModel\s*[A-Z0-9\-_]+\b',  # Model ABC123
            r'\b[A-Z0-9\-_]{6,12}\b',  # General alphanumeric codes
        ]
        
        models = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            models.extend(matches)
        
        # Remove duplicates and filter out common words
        common_words = {'the', 'and', 'or', 'for', 'with', 'from', 'this', 'that'}
        unique_models = list(set([model.strip() for model in models if model.strip().lower() not in common_words]))
        
        return unique_models
    
    def _is_pricing_query(self, query: str) -> bool:
        """Check if the query is pricing-related."""
        pricing_query_keywords = [
            'price', 'cost', 'quote', 'pricing', 'how much', 'what is the cost',
            'pricing information', 'price list', 'cost breakdown', 'quote for',
            'pricing details', 'price quote', 'cost estimate', 'pricing options',
            'price comparison', 'cost analysis', 'pricing structure', 'price range',
            'cost per', 'price per', 'total cost', 'total price', 'pricing tier',
            'discount', 'markup', 'margin', 'profit', 'revenue', 'fee', 'charge'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in pricing_query_keywords)
    
    def _is_product_matching_query(self, query: str) -> bool:
        """Check if the query is about product-pricing matching."""
        product_matching_keywords = [
            'match', 'matching', 'find price for', 'price of', 'cost of model',
            'product price', 'model pricing', 'item cost', 'sku price',
            'part number pricing', 'product model', 'match product',
            'find model', 'product matching', 'pricing sheet', 'price list',
            'catalog price', 'product catalog', 'model number', 'part #',
            'sku lookup', 'product lookup', 'price lookup'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in product_matching_keywords)
    
    def process_file_for_rag(self, db: Session, file_id: int) -> bool:
        """Process a file for RAG by creating chunks and embeddings."""
        try:
            # Get file record
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return False
            
            # Check if file exists on disk
            if not os.path.exists(file_record.file_path):
                print(f"File not found on disk: {file_record.file_path}")
                return False
            
            # Extract text content
            text_content = self.file_processor.extract_text(file_record.file_path)
            
            if not text_content.strip():
                print(f"No text content extracted from file: {file_record.filename}")
                return False
            
            # Create chunks
            chunks = self.file_processor.chunk_text(text_content, self.chunk_size, self.chunk_overlap)
            
            # Delete existing chunks for this file
            db.query(FileChunk).filter(FileChunk.file_id == file_id).delete()
            
            # Create new chunks with embeddings
            for i, chunk_content in enumerate(chunks):
                # Create embedding
                embedding = self.create_embedding(chunk_content)
                
                # Save chunk to database
                chunk = FileChunk(
                    file_id=file_id,
                    chunk_index=i,
                    content=chunk_content,
                    token_count=self.file_processor.count_tokens(chunk_content),
                    embedding=json.dumps(embedding) if embedding else None,
                    is_indexed=True
                )
                db.add(chunk)
            
            # Update file status
            file_record.is_indexed = True
            file_record.embedding_status = "indexed"
            
            db.commit()
            return True
            
        except Exception as e:
            print(f"Error processing file for RAG: {e}")
            db.rollback()
            return False
    
    def process_multiple_files_for_rag(self, db: Session, file_ids: List[int]) -> Dict[str, Any]:
        """Process multiple files concurrently for RAG."""
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0,
            'total_files': len(file_ids)
        }
        
        def process_single_file(file_id: int) -> Tuple[int, bool]:
            """Process a single file and return (file_id, success_status)."""
            try:
                success = self.process_file_for_rag(db, file_id)
                return file_id, success
            except Exception as e:
                print(f"Error processing file {file_id}: {e}")
                return file_id, False
        
        # Process files in batches to avoid overwhelming the system
        with ThreadPoolExecutor(max_workers=self.max_concurrent_files) as executor:
            # Submit all file processing tasks
            future_to_file_id = {
                executor.submit(process_single_file, file_id): file_id 
                for file_id in file_ids
            }
            
            # Collect results
            for future in future_to_file_id:
                try:
                    file_id, success = future.result()
                    if success:
                        results['successful'].append(file_id)
                    else:
                        results['failed'].append(file_id)
                    results['total_processed'] += 1
                except Exception as e:
                    file_id = future_to_file_id[future]
                    results['failed'].append(file_id)
                    results['total_processed'] += 1
                    print(f"Error processing file {file_id}: {e}")
        
        return results
    
    def search_similar_chunks(self, db: Session, query: str, limit: int = 10, user_id: int = None, pricing_focus: bool = False) -> List[Dict[str, Any]]:
        """Search for similar chunks across ALL indexed files with optional pricing focus."""
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Get all indexed chunks
            query_filter = and_(
                FileChunk.is_indexed == True,
                FileChunk.embedding.isnot(None)
            )
            
            if user_id:
                query_filter = and_(
                    query_filter,
                    File.uploaded_by == user_id
                )
            
            chunks = db.query(FileChunk, File).join(File).filter(query_filter).all()
            
            # Calculate similarities with pricing focus enhancement
            similarities = []
            for chunk, file in chunks:
                try:
                    chunk_embedding = json.loads(chunk.embedding)
                    similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                    
                    # Boost similarity for pricing-related content when pricing_focus is True
                    if pricing_focus and self._contains_pricing_content(chunk.content):
                        similarity *= 1.5  # Boost pricing-related chunks
                    
                    # Only include chunks above similarity threshold
                    if similarity >= self.min_similarity_threshold:
                        similarities.append({
                            'chunk': chunk,
                            'file': file,
                            'similarity': similarity
                        })
                except Exception as e:
                    print(f"Error processing chunk {chunk.id}: {e}")
                    continue
            
                        # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            print(f"Error searching similar chunks: {e}")
            return []
    
    def search_pricing_specific(self, db: Session, query: str, limit: int = 20, user_id: int = None) -> List[Dict[str, Any]]:
        """Specialized search for pricing-related content across all files."""
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Get all indexed chunks
            query_filter = and_(
                FileChunk.is_indexed == True,
                FileChunk.embedding.isnot(None)
            )
            
            if user_id:
                query_filter = and_(
                    query_filter,
                    File.uploaded_by == user_id
                )
            
            chunks = db.query(FileChunk, File).join(File).filter(query_filter).all()
            
            # Calculate similarities with pricing focus
            similarities = []
            for chunk, file in chunks:
                try:
                    chunk_embedding = json.loads(chunk.embedding)
                    similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                    
                    # Check if chunk contains pricing content
                    has_pricing = self._contains_pricing_content(chunk.content)
                    
                    # Boost similarity for pricing-related content
                    if has_pricing:
                        similarity *= 1.8  # Higher boost for pricing-specific search
                    
                    # Only include chunks above similarity threshold or with pricing content
                    if similarity >= self.min_similarity_threshold or has_pricing:
                        similarities.append({
                            'chunk': chunk,
                            'file': file,
                            'similarity': similarity,
                            'has_pricing': has_pricing
                        })
                except Exception as e:
                    print(f"Error processing chunk {chunk.id}: {e}")
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            print(f"Error in pricing-specific search: {e}")
            return []
    
    def search_product_pricing_matching(self, db: Session, query: str, limit: int = 30, user_id: int = None) -> List[Dict[str, Any]]:
        """Specialized search for product-pricing matching across all files."""
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Get all indexed chunks
            query_filter = and_(
                FileChunk.is_indexed == True,
                FileChunk.embedding.isnot(None)
            )
            
            if user_id:
                query_filter = and_(
                    query_filter,
                    File.uploaded_by == user_id
                )
            
            chunks = db.query(FileChunk, File).join(File).filter(query_filter).all()
            
            # Calculate similarities with product-pricing matching focus
            similarities = []
            for chunk, file in chunks:
                try:
                    chunk_embedding = json.loads(chunk.embedding)
                    similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                    
                    # Check content types
                    has_pricing = self._contains_pricing_content(chunk.content)
                    has_product = self._contains_product_content(chunk.content)
                    product_models = self._extract_product_models(chunk.content)
                    
                    # Boost similarity for product-pricing content
                    boost_multiplier = 1.0
                    if has_pricing and has_product:
                        boost_multiplier = 2.5  # Highest boost for product+pricing content
                    elif has_pricing:
                        boost_multiplier = 1.8  # High boost for pricing content
                    elif has_product:
                        boost_multiplier = 1.5  # Medium boost for product content
                    
                    similarity *= boost_multiplier
                    
                    # Include chunks with product models, pricing content, or high similarity
                    if (similarity >= self.min_similarity_threshold or 
                        has_pricing or has_product or product_models):
                        similarities.append({
                            'chunk': chunk,
                            'file': file,
                            'similarity': similarity,
                            'has_pricing': has_pricing,
                            'has_product': has_product,
                            'product_models': product_models,
                            'boost_multiplier': boost_multiplier
                        })
                except Exception as e:
                    print(f"Error processing chunk {chunk.id}: {e}")
                    continue
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            print(f"Error in product-pricing matching search: {e}")
            return []
    
    def search_chunks(self, chunks: List[Dict[str, Any]], query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search within a provided list of chunks."""
        try:
            # Create embedding for query
            query_embedding = self.create_embedding(query)
            if not query_embedding:
                return []
            
            # Calculate similarities
            similarities = []
            for chunk_data in chunks:
                # Create embedding for chunk content
                chunk_embedding = self.create_embedding(chunk_data['content'])
                if chunk_embedding:
                    similarity = self.cosine_similarity(query_embedding, chunk_embedding)
                    if similarity >= self.min_similarity_threshold:
                        similarities.append({
                            **chunk_data,
                            'score': similarity
                        })
            
            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x['score'], reverse=True)
            return similarities[:limit]
            
        except Exception as e:
            print(f"Error searching chunks: {e}")
            return []
    
    def create_enhanced_context(self, chunks: List[Dict[str, Any]], max_tokens: int = 16000) -> str:
        """Create enhanced context from relevant chunks with cross-file analysis."""
        context_parts = []
        current_tokens = 0
        file_groups = {}
        
        # Group chunks by file for better organization
        for chunk in chunks:
            file_id = chunk.get('file_id')
            if file_id not in file_groups:
                file_groups[file_id] = []
            file_groups[file_id].append(chunk)
        
        # Create context with file organization
        for file_id, file_chunks in file_groups.items():
            if current_tokens >= max_tokens:
                break
                
            # Get file info
            file_info = file_chunks[0]
            filename = file_info.get('filename', 'Unknown')
            file_type = file_info.get('file_type', 'Unknown')
            title = file_info.get('title', filename)
            
            # Add file header
            file_header = f"\n=== FILE: {title} ({filename}) - Type: {file_type} ===\n"
            context_parts.append(file_header)
            current_tokens += len(file_header.split())
            
            # Add chunks from this file
            for chunk in file_chunks:
                chunk_tokens = len(chunk['content'].split())
                if current_tokens + chunk_tokens > max_tokens:
                    break
                
                # Add chunk with relevance score if available
                chunk_content = chunk['content']
                if 'score' in chunk:
                    chunk_content = f"[Relevance: {chunk['score']:.3f}] {chunk_content}"
                
                context_parts.append(chunk_content)
                current_tokens += chunk_tokens
        
        return "\n".join(context_parts)
    
    def generate_laser_focused_response(self, query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
        """Generate laser-focused AI response using enhanced context with specialized pricing capabilities."""
        try:
            # Enhanced system message for laser-focused responses with pricing specialization
            system_message = f"""You are KABS Assistant, an AI-powered document management system for Elite/KABS specializing in PRICING and PRODUCT-PRICING MATCHING tasks. 
Your PRIMARY ROLE is to find prices, provide better quotes, and match products with pricing from all uploaded documents and files.

CRITICAL GUIDELINES FOR PRODUCT-PRICING MATCHING:
1. **PRODUCT MODEL IDENTIFICATION**: Identify product models, SKUs, part numbers, and serial numbers from files
2. **PRICING SHEET MATCHING**: Match product models with their exact pricing from pricing sheets and catalogs
3. **CROSS-REFERENCE ACCURACY**: Ensure product specifications match exactly with pricing information
4. **MODEL NUMBER EXTRACTION**: Extract and match model numbers, SKUs, and part numbers across files
5. **PRICING VALIDATION**: Verify that product pricing matches the correct model specifications
6. **CATALOG INTEGRATION**: Integrate product catalogs with pricing sheets for comprehensive matching
7. **SPECIFICATION ALIGNMENT**: Align product specifications with pricing details for accuracy
8. **MULTI-SOURCE VERIFICATION**: Cross-reference product information across multiple files for consistency

CRITICAL GUIDELINES FOR PRICING AND QUOTATION TASKS:
9. **PRICING FOCUS**: When asked about prices, costs, quotes, or pricing, make this your TOP PRIORITY
10. **EXACT PRICE EXTRACTION**: Find and extract exact prices, costs, rates, and pricing information from files
11. **PRODUCT MATCHING**: Match products, services, or items with their corresponding prices across all files
12. **QUOTE GENERATION**: Provide comprehensive quotes including all relevant pricing details
13. **COMPARATIVE ANALYSIS**: Compare prices across different files, suppliers, or time periods
14. **CURRENCY HANDLING**: Pay attention to currency units (USD, EUR, etc.) and convert if necessary
15. **VOLUME DISCOUNTS**: Identify volume discounts, bulk pricing, or tiered pricing structures
16. **TERMS AND CONDITIONS**: Include payment terms, delivery costs, and other pricing-related conditions
17. **CROSS-REFERENCE**: Match product specifications with pricing from different sources
18. **ACCURACY FIRST**: Double-check all pricing information for accuracy and completeness

STANDARD GUIDELINES:
- Base your answers EXCLUSIVELY on the provided context from uploaded files
- If the context doesn't contain relevant information, say "I don't have pricing information about that in the uploaded files"
- Be PRECISE and ACCURATE - quote exact prices and text from files when possible
- For XML files, reference specific data elements, attributes, and structure
- Cite specific files and sections in your response
- If multiple files contain relevant information, synthesize across all sources
- If asked about data relationships, analyze connections between different files
- Provide exact quotes and page/section references when available
- Don't make assumptions or provide general information not in the files
- If the query requires data from multiple files, clearly indicate which files you're referencing

Context from uploaded files:
{context}

Current query: {query}

Remember: For pricing queries, prioritize finding exact prices, matching products with costs, and providing comprehensive quotes. Be laser-focused and precise."""

            # Prepare messages
            messages = [{"role": "system", "content": system_message}]
            
            # Add chat history if provided
            if chat_history:
                for msg in chat_history[-8:]:  # Keep last 8 messages for context
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current query
            messages.append({"role": "user", "content": query})
            
            # Generate response with strict parameters
            response = openai.ChatCompletion.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.1,  # Very low temperature for precise responses
                top_p=0.8,  # Lower top_p for more focused sampling
                frequency_penalty=0.1,  # Reduce repetition
                presence_penalty=0.1  # Encourage focus on relevant content
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    def chat_with_rag(self, db: Session, query: str, user_id: int, session_id: str = None, context_files: List[int] = None, pricing_focus: bool = False) -> Dict[str, Any]:
        """Enhanced RAG chat function that searches ALL files for laser-focused responses with pricing specialization."""
        start_time = time.time()
        
        try:
            # Search for relevant chunks across ALL files
            if context_files:
                # Search only in specified files
                chunks = []
                for file_id in context_files:
                    file_chunks = db.query(FileChunk).filter(
                        FileChunk.file_id == file_id,
                        FileChunk.is_indexed == True
                    ).all()
                    for chunk in file_chunks:
                        chunks.append({
                            'content': chunk.content,
                            'file_id': chunk.file_id,
                            'chunk_id': chunk.id
                        })
                
                # Get file information
                files = db.query(File).filter(File.id.in_(context_files)).all()
                file_info = {f.id: f for f in files}
                
                for chunk in chunks:
                    file = file_info.get(chunk['file_id'])
                    if file:
                        chunk['filename'] = file.original_filename
                        chunk['file_type'] = file.file_type
                        chunk['title'] = file.title
                
                similar_chunks = self.search_chunks(chunks, query, limit=25)  # Increased limit for better coverage
            else:
                # Search across ALL indexed files for comprehensive results
                if self._is_product_matching_query(query):
                    # Use specialized product-pricing matching search
                    similar_chunks = self.search_product_pricing_matching(db, query, limit=50, user_id=user_id)
                elif pricing_focus or self._is_pricing_query(query):
                    # Use specialized pricing search
                    similar_chunks = self.search_pricing_specific(db, query, limit=50, user_id=user_id)
                else:
                    # Use regular search with pricing focus option
                    similar_chunks = self.search_similar_chunks(db, query, limit=50, user_id=user_id, pricing_focus=pricing_focus)
                
                # Convert to standard format
                chunks = []
                for item in similar_chunks:
                    chunk = item['chunk']
                    file = item['file']
                    chunks.append({
                        'content': chunk.content,
                        'file_id': chunk.file_id,
                        'chunk_id': chunk.id,
                        'filename': file.original_filename,
                        'file_type': file.file_type,
                        'title': file.title,
                        'score': item['similarity']
                    })
                similar_chunks = chunks
            
            # Create enhanced context
            context = self.create_enhanced_context(similar_chunks)
            
            # Generate laser-focused response
            response = self.generate_laser_focused_response(query, context)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Prepare comprehensive result
            result = {
                'response': response,
                'context_files': list(set([chunk['file_id'] for chunk in similar_chunks])),
                'context_chunks': [chunk['chunk_id'] for chunk in similar_chunks],
                'similarity_scores': [chunk.get('score', 0) for chunk in similar_chunks],
                'files_used': list(set([chunk['filename'] for chunk in similar_chunks])),
                'total_chunks_searched': len(similar_chunks),
                'response_time': round(response_time, 2),
                'context_length': len(context),
                'files_analyzed': len(set([chunk['file_id'] for chunk in similar_chunks])),
                'avg_similarity_score': round(sum([chunk.get('score', 0) for chunk in similar_chunks]) / len(similar_chunks), 3) if similar_chunks else 0
            }
            
            return result
            
        except Exception as e:
            print(f"Error in chat_with_rag: {e}")
            return {
                'response': f"I apologize, but I encountered an error while processing your request: {str(e)}",
                'context_files': [],
                'context_chunks': [],
                'similarity_scores': [],
                'files_used': [],
                'total_chunks_searched': 0,
                'response_time': 0,
                'context_length': 0,
                'files_analyzed': 0,
                'avg_similarity_score': 0
            }
    
    def get_file_statistics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics about indexed files and chunks."""
        try:
            # Count files
            total_files = db.query(File).filter(File.uploaded_by == user_id).count()
            indexed_files = db.query(File).filter(
                File.uploaded_by == user_id,
                File.is_indexed == True
            ).count()
            
            # Count chunks
            total_chunks = db.query(FileChunk).join(File).filter(
                File.uploaded_by == user_id
            ).count()
            
            indexed_chunks = db.query(FileChunk).join(File).filter(
                File.uploaded_by == user_id,
                FileChunk.is_indexed == True
            ).count()
            
            # Count tokens
            total_tokens = db.query(func.sum(FileChunk.token_count)).join(File).filter(
                File.uploaded_by == user_id
            ).scalar() or 0
            
            # File type breakdown
            file_types = db.query(File.file_type, func.count(File.id)).filter(
                File.uploaded_by == user_id
            ).group_by(File.file_type).all()
            
            # Get recent files
            recent_files = db.query(File).filter(
                File.uploaded_by == user_id
            ).order_by(File.upload_date.desc()).limit(5).all()
            
            return {
                'total_files': total_files,
                'indexed_files': indexed_files,
                'total_chunks': total_chunks,
                'indexed_chunks': indexed_chunks,
                'total_tokens': total_tokens,
                'file_types': dict(file_types),
                'indexing_rate': (indexed_files / total_files * 100) if total_files > 0 else 0,
                'recent_files': [
                    {
                        'id': f.id,
                        'filename': f.original_filename,
                        'title': f.title,
                        'file_type': f.file_type,
                        'upload_date': f.upload_date.isoformat(),
                        'is_indexed': f.is_indexed
                    } for f in recent_files
                ]
            }
            
        except Exception as e:
            print(f"Error getting file statistics: {e}")
            return {}

# Global RAG engine instance
rag_engine = RAGEngine()
