"""RAG pipeline API: document ingest and semantic search."""

import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
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
from app.services.rag_pipeline_service import RAGPipelineService, get_rag_pipeline_service

router = APIRouter()
settings = get_settings()


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
    file: Optional[UploadFile] = None,
):
    """
    Register a document for RAG ingestion.
    Either upload a file (file=) or create a record pointing to an existing file path (use body for path).
    """
    if file and file.filename:
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
            title=title or file.filename,
            source=source or "upload",
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide a file upload (multipart/form-data with 'file') to add a document.",
        )
    return _doc_to_response(doc)


@router.post("/documents/from-path", response_model=RAGDocumentResponse)
async def create_document_from_path(
    filepath: str,
    filename: Optional[str] = None,
    title: Optional[str] = None,
    source: Optional[str] = None,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """
    Register an existing file on the server for RAG ingestion.
    The file must be readable by the backend (e.g. under RAG_UPLOAD_DIR or a mounted volume).
    """
    path = Path(filepath)
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {filepath}")
    name = filename or path.name
    doc = service.create_document(
        filename=name,
        filepath=str(path.resolve()),
        title=title or name,
        source=source or "path",
    )
    return _doc_to_response(doc)


@router.get("/documents", response_model=List[RAGDocumentResponse])
async def list_documents(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    service: RAGPipelineService = Depends(get_rag_pipeline_service),
):
    """List RAG documents, optionally filtered by status (pending, ingesting, completed, failed)."""
    docs = service.list_documents(status=status, limit=limit, offset=offset)
    return [_doc_to_response(d) for d in docs]


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
