"""
Knowledge document metadata contract.

Pydantic enforcement of docs' RAG_MVP_METADATA_CONTRACT.md: required fields and
allowed values for documents ingested into the knowledge repository. Extra keys
are permitted (the contract is a minimum standard, not a ceiling).
"""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

SourceType = Literal[
    "custodian_api_spec",
    "custodian_file_spec",
    "custodian_operating_guide",
    "internal_sop",
    "internal_playbook",
    "market_convention",
    "regulation",
    "client_document",
    "implementation_note",
    "training_material",
]

Domain = Literal[
    "custody",
    "reconciliation",
    "settlements",
    "fund_accounting",
    "cash",
    "corporate_actions",
    "tax",
    "workflow",
    "controls",
    "client_reporting",
    "reference_data",
]

Provider = Literal[
    "state_street",
    "bny",
    "northern_trust",
    "bbh",
    "simcorp",
    "aladdin",
    "internal",
    "sec",
    "industry",
    "other",
]

DocumentType = Literal[
    "pdf",
    "markdown",
    "text",
    "spreadsheet_extract",
    "playbook",
    "guide",
    "specification",
    "regulatory_text",
]

TrustLevel = Literal[
    "authoritative",
    "internal_guidance",
    "working_note",
    "draft",
]


class KnowledgeDocumentMetadata(BaseModel):
    """Metadata contract for a knowledge-repository document."""

    # Required by the contract
    title: str = Field(min_length=1)
    source_type: SourceType
    domain: Domain
    provider: Provider
    document_type: DocumentType
    effective_date: date
    trust_level: TrustLevel
    tags: List[str] = Field(min_length=1)

    # Optional by the contract
    source_url: Optional[str] = None
    author: Optional[str] = None
    version_label: Optional[str] = None
    jurisdiction: Optional[str] = None
    audience: Optional[str] = None
    confidentiality: Optional[str] = None
    business_process: Optional[str] = None
    asset_class: Optional[str] = None
    client_scope: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"extra": "allow"}

    @field_validator("tags")
    @classmethod
    def tags_not_blank(cls, v: List[str]) -> List[str]:
        if any(not t.strip() for t in v):
            raise ValueError("tags must not contain blank entries")
        return v

    def to_document_metadata(self) -> dict:
        """Serialize for storage in RAGDocument.metadata (JSON column)."""
        data = self.model_dump(mode="json", exclude_none=True)
        return data


# Fields retrievable as corpus filters on the documents listing endpoint
CORPUS_FILTER_FIELDS = (
    "domain",
    "provider",
    "source_type",
    "document_type",
    "trust_level",
    "asset_class",
    "business_process",
)
