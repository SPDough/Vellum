"""
Database models for the Product Documentation system.

These models store product documents, sections, and metadata in the database
for easy querying and management.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.base_class import Base


class ProductDocument(Base):
    """Product document stored in the database."""
    
    __tablename__ = "product_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    filename = Column(String, nullable=False, unique=True)
    filepath = Column(String, nullable=False)
    
    # Version and status
    version = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="Draft", index=True)  # Draft, Review, Approved, Deprecated
    
    # Ownership
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    owner = Column(String, nullable=False)  # Owner name for display
    
    # Product metadata
    product_name = Column(String, nullable=False, index=True)
    stakeholders = Column(JSON, default=list)  # List of stakeholder names
    target_users = Column(JSON, default=list)  # List of target user types
    use_cases = Column(JSON, default=list)  # List of use cases
    primary_tech = Column(JSON, default=list)  # List of primary technologies
    
    # Requirements
    sla_requirements = Column(Text)
    data_residency = Column(String)
    regulatory_considerations = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ProductDocument(id={self.id}, title='{self.title}', version='{self.version}')>"


class DocumentSection(Base):
    """Individual sections within a product document."""
    
    __tablename__ = "document_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("product_documents.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, default=0, index=True)  # Section order for display
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("ProductDocument", back_populates="sections")
    
    def __repr__(self):
        return f"<DocumentSection(id={self.id}, title='{self.title}', order={self.order})>"


class DocumentTemplate(Base):
    """Reusable document templates for different product types."""
    
    __tablename__ = "document_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text)
    template_type = Column(String, nullable=False, index=True)  # e.g., "feature", "api", "workflow"
    
    # Template content
    front_matter_template = Column(JSON, nullable=False)  # Front matter structure
    sections_template = Column(JSON, nullable=False)  # Section structure and content
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"


class DocumentReview(Base):
    """Review records for product documents."""
    
    __tablename__ = "document_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("product_documents.id"), nullable=False)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Review details
    status = Column(String, nullable=False, default="Pending")  # Pending, Approved, Rejected, Changes_Requested
    comments = Column(Text)
    review_date = Column(DateTime, default=datetime.utcnow)
    
    # Review criteria
    technical_accuracy = Column(Integer)  # 1-5 rating
    completeness = Column(Integer)  # 1-5 rating
    clarity = Column(Integer)  # 1-5 rating
    compliance = Column(Integer)  # 1-5 rating
    
    def __repr__(self):
        return f"<DocumentReview(id={self.id}, document_id={self.document_id}, status='{self.status}')>"

