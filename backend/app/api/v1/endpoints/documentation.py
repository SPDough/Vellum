"""
API endpoints for the Product Documentation system.

This module provides REST API endpoints for managing product documents,
templates, reviews, and exports.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.documentation import (
    ProductDocument,
    ProductDocumentCreate,
    ProductDocumentUpdate,
    ProductDocumentList,
    DocumentSection,
    DocumentExportRequest,
    DocumentExportResponse,
    DocumentValidationRequest,
    DocumentValidationResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentTemplate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
    DocumentReview,
    DocumentReviewCreate,
    DocumentReviewUpdate,
    DocumentStats
)
from app.services.documentation_service import DocumentationService
from app.core.auth import User, get_current_user

router = APIRouter()


@router.post("/", response_model=ProductDocument)
async def create_product_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_data: ProductDocumentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new product document."""
    service = DocumentationService(db)
    return await service.create_product_document(doc_data, str(current_user.id))


@router.get("/", response_model=ProductDocumentList)
async def list_product_documents(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None)
):
    """List product documents with filtering and pagination."""
    service = DocumentationService(db)
    documents, total = await service.list_product_documents(
        skip=skip, limit=limit, status=status, owner_id=owner_id
    )
    return ProductDocumentList(
        documents=documents, total=total, skip=skip, limit=limit
    )


@router.get("/{doc_id}", response_model=ProductDocument)
async def get_product_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str
):
    """Get a product document by ID."""
    service = DocumentationService(db)
    return await service.get_product_document(doc_id)


@router.put("/{doc_id}", response_model=ProductDocument)
async def update_product_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str,
    doc_data: ProductDocumentUpdate
):
    """Update a product document."""
    service = DocumentationService(db)
    return await service.update_product_document(doc_id, doc_data)


@router.delete("/{doc_id}")
async def delete_product_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str
):
    """Delete a product document."""
    service = DocumentationService(db)
    await service.delete_product_document(doc_id)
    return {"message": "Document deleted successfully"}


@router.get("/{doc_id}/sections", response_model=List[DocumentSection])
async def get_document_sections(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str
):
    """Get all sections of a product document."""
    service = DocumentationService(db)
    doc = await service.get_product_document(doc_id)
    return doc.sections


@router.post("/{doc_id}/export", response_model=DocumentExportResponse)
async def export_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str,
    export_request: DocumentExportRequest
):
    """Export a product document to JSON format."""
    service = DocumentationService(db)
    export_data = await service.export_document_json(doc_id, export_request)
    
    return DocumentExportResponse(
        document_id=export_data["document_id"],
        export_format=export_data["export_format"],
        exported_at=export_data["exported_at"],
        content=export_data,
        metadata={
            "source_path": export_data.get("source_path"),
            "format_version": export_data.get("format_version"),
            "platform": export_data.get("platform")
        }
    )


@router.get("/{doc_id}/export/markdown")
async def export_document_markdown(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str
):
    """Export a product document as markdown."""
    service = DocumentationService(db)
    content = await service.export_document_markdown(doc_id)
    return {"content": content, "format": "markdown"}


@router.post("/{doc_id}/validate", response_model=DocumentValidationResponse)
async def validate_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str,
    validation_request: DocumentValidationRequest
):
    """Validate a product document's structure and content."""
    service = DocumentationService(db)
    validation = await service.validate_document(doc_id)
    return DocumentValidationResponse(**validation)


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    *,
    db: Session = Depends(deps.get_db),
    search_request: DocumentSearchRequest
):
    """Search product documents by content."""
    service = DocumentationService(db)
    results, total = await service.search_documents(
        query=search_request.query,
        skip=search_request.skip,
        limit=search_request.limit
    )
    
    return DocumentSearchResponse(
        query=search_request.query,
        results=results,
        total=total,
        skip=search_request.skip,
        limit=search_request.limit
    )


@router.get("/stats/overview", response_model=DocumentStats)
async def get_document_stats(
    *,
    db: Session = Depends(deps.get_db)
):
    """Get overview statistics for product documents."""
    service = DocumentationService(db)
    
    # Get basic counts
    all_docs, total = await service.list_product_documents(limit=10000)
    
    # Calculate statistics
    docs_by_status = {}
    docs_by_owner = {}
    recent_docs = sorted(all_docs, key=lambda x: x.created_at, reverse=True)[:10]
    
    for doc in all_docs:
        # Status counts
        docs_by_status[doc.status] = docs_by_status.get(doc.status, 0) + 1
        
        # Owner counts
        docs_by_owner[doc.owner] = docs_by_owner.get(doc.owner, 0) + 1
    
    # Calculate documents needing review (simplified)
    docs_needing_review = docs_by_status.get("Draft", 0) + docs_by_status.get("Review", 0)
    
    return DocumentStats(
        total_documents=total,
        documents_by_status=docs_by_status,
        documents_by_owner=docs_by_owner,
        recent_documents=recent_docs,
        documents_needing_review=docs_needing_review,
        average_review_rating=0.0  # TODO: Implement review rating calculation
    )


# Template management endpoints
@router.post("/templates/", response_model=DocumentTemplate)
async def create_document_template(
    *,
    db: Session = Depends(deps.get_db),
    template_data: DocumentTemplateCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new document template."""
    # TODO: Implement template creation service
    raise HTTPException(status_code=501, detail="Template creation not yet implemented")


@router.get("/templates/", response_model=List[DocumentTemplate])
async def list_document_templates(
    *,
    db: Session = Depends(deps.get_db),
    template_type: Optional[str] = Query(None)
):
    """List available document templates."""
    # TODO: Implement template listing service
    return []


@router.get("/templates/{template_id}", response_model=DocumentTemplate)
async def get_document_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: str
):
    """Get a document template by ID."""
    # TODO: Implement template retrieval service
    raise HTTPException(status_code=404, detail="Template not found")


# Review management endpoints
@router.post("/{doc_id}/reviews", response_model=DocumentReview)
async def create_document_review(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str,
    review_data: DocumentReviewCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new document review."""
    # TODO: Implement review creation service
    raise HTTPException(status_code=501, detail="Review creation not yet implemented")


@router.get("/{doc_id}/reviews", response_model=List[DocumentReview])
async def list_document_reviews(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: str
):
    """List reviews for a document."""
    # TODO: Implement review listing service
    return []


# CLI tool integration endpoints
@router.post("/cli/init")
async def cli_init_document(
    *,
    product_name: str = Query(..., description="Product name"),
    owner: str = Query(..., description="Document owner"),
    filename: str = Query(..., description="Output filename")
):
    """Initialize a new document using the CLI tool."""
    try:
        from app.tools.vellum_doc_tool import create_otomeshon_template
        
        template = create_otomeshon_template(product_name, owner)
        
        # Generate filename
        safe_filename = f"{product_name.lower().replace(' ', '-')}-{filename}.md"
        filepath = f"docs/products/{safe_filename}"
        
        # Ensure directory exists
        import os
        os.makedirs("docs/products", exist_ok=True)
        
        # Write template
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)
        
        return {
            "message": "Document created successfully",
            "filename": safe_filename,
            "filepath": filepath,
            "product_name": product_name,
            "owner": owner
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.post("/cli/export-json")
async def cli_export_json(
    *,
    filepath: str = Query(..., description="Path to markdown file")
):
    """Export a markdown file to JSON using the CLI tool."""
    try:
        from app.tools.vellum_doc_tool import md_to_json
        
        json_data = md_to_json(filepath)
        
        return {
            "message": "Export successful",
            "filepath": filepath,
            "export_data": json_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export document: {str(e)}")


@router.post("/cli/validate")
async def cli_validate_document(
    *,
    filepath: str = Query(..., description="Path to markdown file")
):
    """Validate a markdown file using the CLI tool."""
    try:
        from app.tools.vellum_doc_tool import parse_front_matter, split_sections
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        front_matter, body = parse_front_matter(content)
        sections = split_sections(body)
        
        # Basic validation
        required_keys = ["product_name", "version", "status", "last_updated", "owner"]
        missing_keys = [k for k in required_keys if k not in front_matter or not str(front_matter[k]).strip()]
        
        validation_result = {
            "filepath": filepath,
            "is_valid": len(missing_keys) == 0,
            "front_matter_keys": list(front_matter.keys()),
            "sections_count": len(sections),
            "section_names": list(sections.keys()),
            "missing_required_keys": missing_keys,
            "errors": [] if len(missing_keys) == 0 else [f"Missing required keys: {', '.join(missing_keys)}"]
        }
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate document: {str(e)}")

