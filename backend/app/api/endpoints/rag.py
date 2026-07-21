"""RAG pipeline API: document ingest, metadata contract enforcement, and semantic search."""

import json
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_sync_db
from app.models.rag import RAGDocument
from app.schemas.rag import (
    RAGDocumentCreate,
    RAGDocumentResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResult,
)
from app.schemas.rag_metadata import CORPUS_FILTER_FIELDS, KnowledgeDocumentMetadata
from app.services.rag_pipeline_service import RAGPipelineService, get_rag_pipeline_service

router = APIRouter()
settings = get_settings()

_CONTRACT_REQUIRED = (
    "title, source_type, domain, provider, document_type, effective_date, trust_level, tags"
)


def _validated_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Enforce the knowledge metadata contract (RAG_ENFORCE_METADATA_CONTRACT).
    Returns contract-normalized metadata for storage, or raises 422.
    """
    enforce = get_settings().rag_enforce_metadata_contract
    if not metadata:
        if enforce:
            raise HTTPException(
                status_code=422,
                detail=(
                    "Metadata contract enforced: provide document metadata with required "
                    f"fields ({_CONTRACT_REQUIRED}). See RAG_MVP_METADATA_CONTRACT.md."
                ),
            )
        return {}
    try:
        contract = KnowledgeDocumentMetadata.model_validate(metadata)
    except ValidationError as e:
        if enforce:
            errors = "; ".join(
                f"{'.'.join(str(p) for p in err['loc'])}: {err['msg']}" for err in e.errors()
            )
            raise HTTPException(
                status_code=422, detail=f"Metadata contract violation: {errors}"
            )
        return metadata
    return contract.to_document_metadata()


def _doc_to_response(doc: RAGDocument) -> RAGDocumentResponse:
    """Map RAGDocument ORM to response schema."""
    return RAGDocumentResponse(
        id=doc.id,
        filename=doc.filename,
        filepath=doc.filepath,
        content_type=doc.content_type,
        title=doc.title,
        source=doc.source,
        metadata=doc.metadata_ or {},
        status=doc.status,
        error_message=doc.error_message,
        chunk_count=doc.chunk_count,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        ingested_at=doc.ingested_at,
    )


@router.post("/documents", response_model=RAGDocumentResponse)
async def create_document(
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
    title: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[str] = Form(
        None, description="Metadata contract fields as a JSON object string"
    ),
    file: Optional[UploadFile] = None,
):
    """
    Register a document for RAG ingestion via file upload.
    `metadata` must satisfy the knowledge metadata contract unless enforcement is disabled.
    """
    if not (file and file.filename):
        raise HTTPException(
            status_code=400,
            detail="Provide a file upload (multipart/form-data with 'file') to add a document.",
        )
    try:
        metadata_dict = json.loads(metadata) if metadata else None
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="metadata must be a valid JSON object")
    stored_metadata = _validated_metadata(metadata_dict)
    upload_dir = Path(settings.rag_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = os.path.basename(file.filename).replace("..", "")
    filepath = upload_dir / safe_name
    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)
    doc = service.create_document(
        filename=file.filename,
        filepath=str(filepath.resolve()),
        content_type=file.content_type,
        title=title or stored_metadata.get("title") or file.filename,
        source=source or "upload",
        metadata=stored_metadata,
    )
    return _doc_to_response(doc)


@router.post("/documents/from-path", response_model=RAGDocumentResponse)
async def create_document_from_path(
    filepath: str,
    filename: Optional[str] = None,
    title: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = Body(
        None, description="Metadata contract fields for the document"
    ),
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """
    Register an existing file on the server for RAG ingestion.
    The file must be readable by the backend (e.g. under RAG_UPLOAD_DIR or a mounted volume).
    Request body must satisfy the knowledge metadata contract unless enforcement is disabled.
    """
    stored_metadata = _validated_metadata(metadata)
    path = Path(filepath)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
    name = filename or path.name
    doc = service.create_document(
        filename=name,
        filepath=str(path.resolve()),
        title=title or stored_metadata.get("title") or name,
        source=source or "path",
        metadata=stored_metadata,
    )
    return _doc_to_response(doc)


class BulkFromPathRequest(BaseModel):
    """Bulk-register every matching file in a server-side directory."""

    directory: str
    glob: str = Field(default="*.pdf", description="Filename pattern, e.g. *.pdf or *.md")
    metadata: Dict[str, Any] = Field(
        description="Shared metadata contract fields applied to every file"
    )
    title_from_filename: bool = Field(
        default=True,
        description="Use each file's stem as its title instead of the shared metadata title",
    )


class BulkFromPathResponse(BaseModel):
    """Result of a bulk registration."""

    registered: List[RAGDocumentResponse]
    skipped: List[str]


@router.post("/documents/bulk-from-path", response_model=BulkFromPathResponse)
async def bulk_create_from_path(
    body: BulkFromPathRequest,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """
    Power-user bulk registration: register every file matching `glob` under `directory`,
    all sharing one metadata contract (per-file titles derived from filenames by default).
    Files already registered (same resolved path) are skipped.
    """
    directory = Path(body.directory)
    if not directory.is_dir():
        raise HTTPException(status_code=404, detail=f"Directory not found: {body.directory}")
    shared = _validated_metadata(body.metadata)
    files = sorted(p for p in directory.glob(body.glob) if p.is_file())
    if not files:
        raise HTTPException(
            status_code=404, detail=f"No files matching {body.glob} in {body.directory}"
        )
    existing = {
        d.filepath for d in service.list_documents(limit=10000)
    }
    registered: List[RAGDocumentResponse] = []
    skipped: List[str] = []
    for path in files:
        resolved = str(path.resolve())
        if resolved in existing:
            skipped.append(path.name)
            continue
        metadata = dict(shared)
        if body.title_from_filename:
            metadata["title"] = path.stem
        doc = service.create_document(
            filename=path.name,
            filepath=resolved,
            title=metadata.get("title") or path.name,
            source="bulk_path",
            metadata=metadata,
        )
        registered.append(_doc_to_response(doc))
    return BulkFromPathResponse(registered=registered, skipped=skipped)


@router.get("/documents", response_model=List[RAGDocumentResponse])
async def list_documents(
    status: Optional[str] = None,
    domain: Optional[str] = None,
    provider: Optional[str] = None,
    source_type: Optional[str] = None,
    document_type: Optional[str] = None,
    trust_level: Optional[str] = None,
    asset_class: Optional[str] = None,
    business_process: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """
    List RAG documents. Filter by ingestion status and/or corpus metadata
    (domain, provider, source_type, document_type, trust_level, asset_class, business_process).
    """
    requested = {
        "domain": domain,
        "provider": provider,
        "source_type": source_type,
        "document_type": document_type,
        "trust_level": trust_level,
        "asset_class": asset_class,
        "business_process": business_process,
    }
    metadata_filters = {
        k: v for k, v in requested.items() if v is not None and k in CORPUS_FILTER_FIELDS
    }
    docs = service.list_documents(
        status=status, metadata_filters=metadata_filters or None, limit=limit, offset=offset
    )
    return [_doc_to_response(d) for d in docs]


@router.get("/ingestion/summary")
async def ingestion_summary(
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """Document counts by ingestion status (pending, ingesting, completed, failed)."""
    return service.status_summary()


@router.get("/documents/{document_id}", response_model=RAGDocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """Get a single RAG document by ID."""
    doc = service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return _doc_to_response(doc)


@router.post("/documents/{document_id}/ingest", response_model=RAGDocumentResponse)
async def ingest_document(
    document_id: uuid.UUID,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """
    Run the RAG pipeline on a document: load text, chunk, embed, and store in the RAG database.
    """
    try:
        doc = await service.ingest_document_async(document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _doc_to_response(doc)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """Delete a RAG document and all its chunks."""
    if not service.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": str(document_id)}


@router.post("/search", response_model=RAGSearchResponse)
async def search(
    body: RAGSearchRequest,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """Semantic search over ingested RAG chunks. Returns top-k closest chunks by embedding similarity."""
    results = await service.search(
        query=body.query,
        top_k=body.top_k,
        document_ids=body.document_ids,
    )
    return RAGSearchResponse(
        query=body.query,
        results=[
            RAGSearchResult(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                filename=r["filename"],
                content=r["content"],
                chunk_index=r["chunk_index"],
                score=r["score"],
                metadata=r["metadata"],
            )
            for r in results
        ],
    )
