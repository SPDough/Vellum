"""
Documentation Service for Otomeshon Platform

This service integrates the vellum_doc_tool.py functionality with the Otomeshon platform,
providing programmatic access to product documentation creation, management, and export.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.models.documentation import ProductDocument, DocumentSection
from app.schemas.documentation import (
    ProductDocumentCreate,
    ProductDocumentUpdate,
    DocumentSectionCreate,
    DocumentExportRequest
)
from app.core.config import settings
from app.tools.vellum_doc_tool import (
    create_otomeshon_template,
    md_to_json,
    parse_front_matter,
    split_sections
)


class DocumentationService:
    """Service for managing product documentation in the Otomeshon platform."""
    
    def __init__(self, db: Session):
        self.db = db
        self.docs_dir = Path(settings.DOCUMENTATION_DIR or "docs/products")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_product_document(
        self, 
        doc_data: ProductDocumentCreate,
        owner_id: str
    ) -> ProductDocument:
        """Create a new product document with template."""
        
        # Generate filename
        filename = f"{doc_data.product_name.lower().replace(' ', '-')}-{doc_data.version}.md"
        filepath = self.docs_dir / filename
        
        # Create markdown template
        template = create_otomeshon_template(
            product_name=doc_data.product_name,
            owner=doc_data.owner
        )
        
        # Write template to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(template)
        
        # Create database record
        db_doc = ProductDocument(
            title=doc_data.product_name,
            filename=filename,
            filepath=str(filepath),
            version=doc_data.version,
            status=doc_data.status,
            owner_id=owner_id,
            product_name=doc_data.product_name,
            owner=doc_data.owner,
            stakeholders=doc_data.stakeholders or [],
            target_users=doc_data.target_users or [],
            use_cases=doc_data.use_cases or [],
            primary_tech=doc_data.primary_tech or [],
            sla_requirements=doc_data.sla_requirements,
            data_residency=doc_data.data_residency,
            regulatory_considerations=doc_data.regulatory_considerations or []
        )
        
        self.db.add(db_doc)
        self.db.commit()
        self.db.refresh(db_doc)
        
        # Parse and store sections
        await self._parse_and_store_sections(db_doc.id, template)
        
        return db_doc
    
    async def update_product_document(
        self,
        doc_id: str,
        doc_data: ProductDocumentUpdate
    ) -> ProductDocument:
        """Update an existing product document."""
        
        db_doc = self.db.query(ProductDocument).filter(ProductDocument.id == doc_id).first()
        if not db_doc:
            raise HTTPException(status_code=404, detail="Product document not found")
        
        # Update fields
        for field, value in doc_data.dict(exclude_unset=True).items():
            setattr(db_doc, field, value)
        
        db_doc.updated_at = datetime.datetime.utcnow()
        
        # Update markdown file if content changed
        if doc_data.content:
            filepath = Path(db_doc.filepath)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(doc_data.content)
            
            # Re-parse sections
            await self._parse_and_store_sections(doc_id, doc_data.content)
        
        self.db.commit()
        self.db.refresh(db_doc)
        
        return db_doc
    
    async def get_product_document(self, doc_id: str) -> ProductDocument:
        """Get a product document by ID."""
        doc = self.db.query(ProductDocument).filter(ProductDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Product document not found")
        return doc
    
    async def list_product_documents(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Tuple[List[ProductDocument], int]:
        """List product documents with filtering and pagination."""
        
        query = self.db.query(ProductDocument)
        
        if status:
            query = query.filter(ProductDocument.status == status)
        if owner_id:
            query = query.filter(ProductDocument.owner_id == owner_id)
        
        total = query.count()
        documents = query.offset(skip).limit(limit).all()
        
        return documents, total
    
    async def delete_product_document(self, doc_id: str) -> bool:
        """Delete a product document."""
        doc = self.db.query(ProductDocument).filter(ProductDocument.id == doc_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Product document not found")
        
        # Delete file
        filepath = Path(doc.filepath)
        if filepath.exists():
            filepath.unlink()
        
        # Delete database record
        self.db.delete(doc)
        self.db.commit()
        
        return True
    
    async def export_document_json(
        self,
        doc_id: str,
        export_request: DocumentExportRequest
    ) -> Dict[str, Any]:
        """Export a product document to JSON format."""
        
        doc = await self.get_product_document(doc_id)
        filepath = Path(doc.filepath)
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Convert to JSON using vellum tool
        json_data = md_to_json(str(filepath))
        
        # Add metadata
        json_data.update({
            "document_id": doc.id,
            "exported_at": datetime.datetime.utcnow().isoformat() + "Z",
            "export_format": "vellum_json",
            "export_options": export_request.dict()
        })
        
        return json_data
    
    async def export_document_markdown(self, doc_id: str) -> str:
        """Export a product document as markdown."""
        
        doc = await self.get_product_document(doc_id)
        filepath = Path(doc.filepath)
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    
    async def validate_document(self, doc_id: str) -> Dict[str, Any]:
        """Validate a product document's structure and content."""
        
        doc = await self.get_product_document(doc_id)
        filepath = Path(doc.filepath)
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Parse front matter and sections
        front_matter, body = parse_front_matter(content)
        sections = split_sections(body)
        
        # Validation results
        validation = {
            "document_id": doc_id,
            "validated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "front_matter": {
                "present": bool(front_matter),
                "keys": list(front_matter.keys()),
                "missing_required": []
            },
            "sections": {
                "count": len(sections),
                "names": list(sections.keys()),
                "missing_required": []
            }
        }
        
        # Check required front matter keys
        required_keys = ["product_name", "version", "status", "last_updated", "owner"]
        for key in required_keys:
            if key not in front_matter or not str(front_matter[key]).strip():
                validation["front_matter"]["missing_required"].append(key)
                validation["is_valid"] = False
        
        # Check required sections
        required_sections = [
            "1. Executive Summary",
            "2. Problem Statement",
            "3. Goals and Non-Goals",
            "4. Personas",
            "5. User Journeys & Workflows",
            "6. Functional Requirements",
            "7. Non-Functional Requirements"
        ]
        
        for section in required_sections:
            if section not in sections:
                validation["sections"]["missing_required"].append(section)
                validation["warnings"].append(f"Missing recommended section: {section}")
        
        if validation["front_matter"]["missing_required"]:
            validation["errors"].append(
                f"Missing required front matter keys: {', '.join(validation['front_matter']['missing_required'])}"
            )
        
        return validation
    
    async def search_documents(
        self,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[ProductDocument], int]:
        """Search product documents by content."""
        
        # Simple text search in document content
        query = query.lower()
        results = []
        
        all_docs = self.db.query(ProductDocument).all()
        
        for doc in all_docs:
            filepath = Path(doc.filepath)
            if filepath.exists():
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        if query in content:
                            results.append(doc)
                except Exception:
                    continue
        
        total = len(results)
        paginated_results = results[skip:skip + limit]
        
        return paginated_results, total
    
    async def _parse_and_store_sections(
        self,
        doc_id: str,
        content: str
    ) -> None:
        """Parse document content and store sections in database."""
        
        # Clear existing sections
        self.db.query(DocumentSection).filter(DocumentSection.document_id == doc_id).delete()
        
        # Parse sections
        front_matter, body = parse_front_matter(content)
        sections = split_sections(body)
        
        # Store sections
        for title, section_content in sections.items():
            if title == "__body__":
                continue
                
            section = DocumentSection(
                document_id=doc_id,
                title=title,
                content=section_content,
                order=self._get_section_order(title)
            )
            self.db.add(section)
        
        self.db.commit()
    
    def _get_section_order(self, title: str) -> int:
        """Get the order of a section based on its title."""
        try:
            # Extract number from title like "1. Executive Summary"
            number = int(title.split(".")[0])
            return number
        except (ValueError, IndexError):
            return 999  # Put unnumbered sections at the end

