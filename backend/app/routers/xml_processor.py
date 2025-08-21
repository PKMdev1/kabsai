from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import tempfile
import os

from ..database import get_db
from ..models import User, File as FileModel
# Authentication removed - no user system
from ..file_processor import FileProcessor
from ..schemas import XMLSearchRequest, XMLMatchResponse, XMLSchemaResponse

router = APIRouter(prefix="/xml", tags=["XML Processing"])

file_processor = FileProcessor()

@router.post("/upload", response_model=Dict[str, Any])
async def upload_xml_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    tags: str = Form(""),
    project: str = Form(""),
    department: str = Form(""),
    db: Session = Depends(get_db)
):
    """Upload and process XML file with data extraction."""
    
    # Validate file type
    if not file.filename.lower().endswith(('.xml', '.xsd')):
        raise HTTPException(status_code=400, detail="Only XML and XSD files are supported")
    
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Extract XML data and schema
        xml_data = file_processor.extract_xml_data(temp_file_path)
        xml_schema = file_processor.extract_xml_schema(temp_file_path)
        text_content = file_processor.extract_text(temp_file_path)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        # Save file metadata to database
        file_record = FileModel(
            filename=file.filename,
            title=title,
            description=description,
            file_type="xml",
            file_size=len(content),
            owner_id=1,  # Default user ID
            uploaded_by=1,  # Default user ID
            tags=tags,
            project=project,
            department=department,
            file_metadata=json.dumps({
                'xml_data': xml_data,
                'xml_schema': xml_schema,
                'root_element': xml_data.get('root_tag'),
                'element_count': len(xml_data.get('elements', [])),
                'has_namespaces': bool(xml_schema.get('namespaces')),
                'data_types': xml_schema.get('data_types', {})
            })
        )
        
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        
        return {
            "success": True,
            "file_id": file_record.id,
            "xml_data": xml_data,
            "schema": xml_schema,
            "message": "XML file processed successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing XML file: {str(e)}")

@router.post("/search", response_model=List[XMLMatchResponse])
async def search_xml_data(
    request: XMLSearchRequest,
    db: Session = Depends(get_db)
):
    """Search XML data across uploaded files."""
    
    try:
        # Get XML files from database
        xml_files = db.query(FileModel).filter(
            FileModel.file_type == "xml"
        ).all()
        
        all_matches = []
        
        for file_record in xml_files:
            if not file_record.file_metadata:
                continue
                
            metadata = json.loads(file_record.file_metadata)
            xml_data = metadata.get('xml_data', {})
            
            # Search in XML data
            matches = file_processor.match_xml_data(xml_data, request.search_criteria)
            
            for match in matches:
                all_matches.append(XMLMatchResponse(
                    file_id=file_record.id,
                    filename=file_record.filename,
                    title=file_record.title,
                    matched_element=match,
                    relevance_score=1.0  # Could implement scoring algorithm
                ))
        
        return all_matches
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching XML data: {str(e)}")

@router.get("/schema/{file_id}", response_model=XMLSchemaResponse)
async def get_xml_schema(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get XML schema information for a specific file."""
    
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.file_type == "xml",
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="XML file not found")
    
    if not file_record.file_metadata:
        raise HTTPException(status_code=400, detail="No schema information available")
    
    try:
        metadata = json.loads(file_record.file_metadata)
        schema = metadata.get('xml_schema', {})
        
        return XMLSchemaResponse(
            file_id=file_record.id,
            filename=file_record.filename,
            schema=schema
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schema: {str(e)}")

@router.get("/structure/{file_id}")
async def get_xml_structure(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get XML structure information for a specific file."""
    
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.file_type == "xml",
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="XML file not found")
    
    if not file_record.file_metadata:
        raise HTTPException(status_code=400, detail="No structure information available")
    
    try:
        metadata = json.loads(file_record.file_metadata)
        xml_data = metadata.get('xml_data', {})
        
        return {
            "file_id": file_record.id,
            "filename": file_record.filename,
            "root_element": xml_data.get('root_tag'),
            "structure": xml_data.get('structure', {}),
            "element_count": len(xml_data.get('elements', [])),
            "namespaces": metadata.get('xml_schema', {}).get('namespaces', {})
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving structure: {str(e)}")

@router.post("/validate")
async def validate_xml_structure(
    file_id: int,
    validation_rules: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate XML structure against custom rules."""
    
    file_record = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.file_type == "xml",
        FileModel.owner_id == current_user.id
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="XML file not found")
    
    try:
        metadata = json.loads(file_record.file_metadata)
        xml_data = metadata.get('xml_data', {})
        
        validation_results = []
        
        # Validate required elements
        if 'required_elements' in validation_rules:
            for required_element in validation_rules['required_elements']:
                found = False
                for element in xml_data.get('elements', []):
                    if element.get('tag') == required_element:
                        found = True
                        break
                
                validation_results.append({
                    'rule': f"Required element: {required_element}",
                    'status': 'PASS' if found else 'FAIL',
                    'details': f"Element '{required_element}' {'found' if found else 'not found'}"
                })
        
        # Validate data types
        if 'data_types' in validation_rules:
            schema = metadata.get('xml_schema', {})
            inferred_types = schema.get('data_types', {})
            
            for element_name, expected_type in validation_rules['data_types'].items():
                actual_type = inferred_types.get(element_name, 'string')
                validation_results.append({
                    'rule': f"Data type for {element_name}",
                    'status': 'PASS' if actual_type == expected_type else 'WARNING',
                    'details': f"Expected: {expected_type}, Found: {actual_type}"
                })
        
        return {
            "file_id": file_record.id,
            "filename": file_record.filename,
            "validation_results": validation_results,
            "overall_status": "PASS" if all(r['status'] == 'PASS' for r in validation_results) else "FAIL"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating XML: {str(e)}")

@router.get("/files", response_model=List[Dict[str, Any]])
async def list_xml_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all XML files uploaded by the user."""
    
    xml_files = db.query(FileModel).filter(
        FileModel.file_type == "xml",
        FileModel.owner_id == current_user.id
    ).all()
    
    files_list = []
    for file_record in xml_files:
        metadata = json.loads(file_record.file_metadata) if file_record.file_metadata else {}
        xml_data = metadata.get('xml_data', {})
        
        files_list.append({
            "id": file_record.id,
            "filename": file_record.filename,
            "title": file_record.title,
            "description": file_record.description,
            "upload_date": file_record.created_at.isoformat(),
            "root_element": xml_data.get('root_tag'),
            "element_count": len(xml_data.get('elements', [])),
            "file_size": file_record.file_size,
            "tags": file_record.tags,
            "project": file_record.project,
            "department": file_record.department
        })
    
    return files_list
