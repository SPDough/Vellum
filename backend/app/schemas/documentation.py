"""
Pydantic schemas for the Product Documentation system.

These schemas define the data structures for API requests and responses
in the documentation system.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID


class DocumentSectionBase(BaseModel):
    """Base schema for document sections."""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content in markdown")
    order: int = Field(0, description="Section display order")


class DocumentSectionCreate(DocumentSectionBase):
    """Schema for creating a document section."""
    pass


class DocumentSectionUpdate(BaseModel):
    """Schema for updating a document section."""
    title: Optional[str] = Field(None, description="Section title")
    content: Optional[str] = Field(None, description="Section content in markdown")
    order: Optional[int] = Field(None, description="Section display order")


class DocumentSection(DocumentSectionBase):
    """Schema for document section responses."""
    id: UUID
    document_id: UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductDocumentBase(BaseModel):
    """Base schema for product documents."""
    title: str = Field(..., description="Document title")
    product_name: str = Field(..., description="Product name")
    version: str = Field(..., description="Document version")
    status: str = Field("Draft", description="Document status")
    owner: str = Field(..., description="Document owner")
    stakeholders: Optional[List[str]] = Field(default_factory=list, description="List of stakeholders")
    target_users: Optional[List[str]] = Field(default_factory=list, description="List of target users")
    use_cases: Optional[List[str]] = Field(default_factory=list, description="List of use cases")
    primary_tech: Optional[List[str]] = Field(default_factory=list, description="List of primary technologies")
    sla_requirements: Optional[str] = Field(None, description="SLA requirements")
    data_residency: Optional[str] = Field(None, description="Data residency requirements")
    regulatory_considerations: Optional[List[str]] = Field(default_factory=list, description="Regulatory considerations")


class ProductDocumentCreate(ProductDocumentBase):
    """Schema for creating a product document."""
    pass


class ProductDocumentUpdate(BaseModel):
    """Schema for updating a product document."""
    title: Optional[str] = Field(None, description="Document title")
    product_name: Optional[str] = Field(None, description="Product name")
    version: Optional[str] = Field(None, description="Document version")
    status: Optional[str] = Field(None, description="Document status")
    owner: Optional[str] = Field(None, description="Document owner")
    stakeholders: Optional[List[str]] = Field(None, description="List of stakeholders")
    target_users: Optional[List[str]] = Field(None, description="List of target users")
    use_cases: Optional[List[str]] = Field(None, description="List of use cases")
    primary_tech: Optional[List[str]] = Field(None, description="List of primary technologies")
    sla_requirements: Optional[str] = Field(None, description="SLA requirements")
    data_residency: Optional[str] = Field(None, description="Data residency requirements")
    regulatory_considerations: Optional[List[str]] = Field(None, description="Regulatory considerations")
    content: Optional[str] = Field(None, description="Full document content in markdown")


class ProductDocument(ProductDocumentBase):
    """Schema for product document responses."""
    id: UUID
    filename: str
    filepath: str
    owner_id: UUID
    created_at: datetime
    updated_at: datetime
    sections: List[DocumentSection] = []
    
    class Config:
        from_attributes = True


class ProductDocumentList(BaseModel):
    """Schema for paginated product document lists."""
    documents: List[ProductDocument]
    total: int
    skip: int
    limit: int


class DocumentExportRequest(BaseModel):
    """Schema for document export requests."""
    format: str = Field("vellum_json", description="Export format")
    include_metadata: bool = Field(True, description="Include document metadata")
    include_sections: bool = Field(True, description="Include section content")
    include_raw_markdown: bool = Field(True, description="Include raw markdown content")
    include_parsed_content: bool = Field(True, description="Include parsed tables, lists, code blocks")


class DocumentExportResponse(BaseModel):
    """Schema for document export responses."""
    document_id: UUID
    export_format: str
    exported_at: datetime
    content: Dict[str, Any]
    metadata: Dict[str, Any]


class DocumentValidationRequest(BaseModel):
    """Schema for document validation requests."""
    validate_front_matter: bool = Field(True, description="Validate front matter structure")
    validate_sections: bool = Field(True, description="Validate required sections")
    validate_content: bool = Field(False, description="Validate content quality")


class DocumentValidationResponse(BaseModel):
    """Schema for document validation responses."""
    document_id: UUID
    validated_at: datetime
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    front_matter: Dict[str, Any]
    sections: Dict[str, Any]


class DocumentSearchRequest(BaseModel):
    """Schema for document search requests."""
    query: str = Field(..., description="Search query")
    skip: int = Field(0, description="Number of results to skip")
    limit: int = Field(100, description="Maximum number of results")
    status_filter: Optional[str] = Field(None, description="Filter by document status")
    owner_filter: Optional[str] = Field(None, description="Filter by document owner")


class DocumentSearchResponse(BaseModel):
    """Schema for document search responses."""
    query: str
    results: List[ProductDocument]
    total: int
    skip: int
    limit: int


class DocumentTemplateBase(BaseModel):
    """Base schema for document templates."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: str = Field(..., description="Template type (feature, api, workflow, etc.)")
    front_matter_template: Dict[str, Any] = Field(..., description="Front matter structure")
    sections_template: Dict[str, Any] = Field(..., description="Section structure and content")


class DocumentTemplateCreate(DocumentTemplateBase):
    """Schema for creating a document template."""
    pass


class DocumentTemplateUpdate(BaseModel):
    """Schema for updating a document template."""
    name: Optional[str] = Field(None, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: Optional[str] = Field(None, description="Template type")
    front_matter_template: Optional[Dict[str, Any]] = Field(None, description="Front matter structure")
    sections_template: Optional[Dict[str, Any]] = Field(None, description="Section structure and content")
    is_active: Optional[bool] = Field(None, description="Template active status")


class DocumentTemplate(DocumentTemplateBase):
    """Schema for document template responses."""
    id: UUID
    is_active: bool
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentReviewBase(BaseModel):
    """Base schema for document reviews."""
    status: str = Field(..., description="Review status")
    comments: Optional[str] = Field(None, description="Review comments")
    technical_accuracy: Optional[int] = Field(None, ge=1, le=5, description="Technical accuracy rating (1-5)")
    completeness: Optional[int] = Field(None, ge=1, le=5, description="Completeness rating (1-5)")
    clarity: Optional[int] = Field(None, ge=1, le=5, description="Clarity rating (1-5)")
    compliance: Optional[int] = Field(None, ge=1, le=5, description="Compliance rating (1-5)")


class DocumentReviewCreate(DocumentReviewBase):
    """Schema for creating a document review."""
    document_id: UUID = Field(..., description="Document to review")


class DocumentReviewUpdate(BaseModel):
    """Schema for updating a document review."""
    status: Optional[str] = Field(None, description="Review status")
    comments: Optional[str] = Field(None, description="Review comments")
    technical_accuracy: Optional[int] = Field(None, ge=1, le=5, description="Technical accuracy rating (1-5)")
    completeness: Optional[int] = Field(None, ge=1, le=5, description="Completeness rating (1-5)")
    clarity: Optional[int] = Field(None, ge=1, le=5, description="Clarity rating (1-5)")
    compliance: Optional[int] = Field(None, ge=1, le=5, description="Compliance rating (1-5)")


class DocumentReview(DocumentReviewBase):
    """Schema for document review responses."""
    id: UUID
    document_id: UUID
    reviewer_id: UUID
    review_date: datetime
    
    class Config:
        from_attributes = True


class DocumentStats(BaseModel):
    """Schema for document statistics."""
    total_documents: int
    documents_by_status: Dict[str, int]
    documents_by_owner: Dict[str, int]
    recent_documents: List[ProductDocument]
    documents_needing_review: int
    average_review_rating: float

