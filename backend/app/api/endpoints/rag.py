"""RAG pipeline API: document ingest, metadata contract enforcement, and semantic search."""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_sync_db
from app.models.rag import RAGDocument
from app.schemas.rag import (
    Citation,
    ConversationDetail,
    ConversationMessage,
    ConversationSummary,
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    RAGDocumentCreate,
    RAGDocumentResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResult,
)
from app.schemas.rag_metadata import CORPUS_FILTER_FIELDS, KnowledgeDocumentMetadata
from app.services.knowledge_conversation_service import KnowledgeConversationService
from app.services.knowledge_retrieval_service import (
    KnowledgeRetrievalService,
    get_knowledge_retrieval_service,
)
from app.services.rag_pipeline_service import RAGPipelineService, get_rag_pipeline_service

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

_optional_bearer = HTTPBearer(auto_error=False)


async def get_conversation_owner(
    credentials=Depends(_optional_bearer),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
) -> str:
    """
    Resolve the conversation owner (the isolation boundary).

    Prefers the authenticated user id (valid bearer token); falls back to an
    explicit `X-User-Id` header for demo/dev, then "anonymous". Production should
    enforce real authentication so `owner` is always a trusted user id.
    """
    if credentials and getattr(credentials, "credentials", None):
        try:
            from app.core.auth import keycloak_auth

            user = await keycloak_auth.validate_token(credentials.credentials)
            if user and getattr(user, "id", None):
                return user.id
        except Exception:
            pass
    return x_user_id or "anonymous"

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


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(
    body: KnowledgeSearchRequest,
    service: KnowledgeRetrievalService = Depends(get_knowledge_retrieval_service),
):
    """
    Hybrid knowledge search: dense vector + full-text retrieval fused with RRF,
    optionally reranked with a local cross-encoder. Returns citation-bearing results.
    """
    try:
        candidates = await service.search(
            query=body.query,
            top_k=body.top_k,
            filters=body.filters,
            min_trust=body.min_trust,
            use_reranker=body.use_reranker,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    reranked = any(c.rerank_score is not None for c in candidates)
    return KnowledgeSearchResponse(
        query=body.query,
        reranked=reranked,
        results=[
            KnowledgeSearchResult(
                chunk_id=c.chunk_id,
                content=c.content,
                citation=Citation(**c.citation()),
                vector_score=c.vector_score,
                text_score=c.text_score,
                fused_score=c.fused_score,
                rerank_score=c.rerank_score,
            )
            for c in candidates
        ],
    )


@router.post("/knowledge/ask", response_model=KnowledgeAskResponse)
async def knowledge_ask(
    body: KnowledgeAskRequest,
    db: Session = Depends(get_sync_db),
    owner: str = Depends(get_conversation_owner),
):
    """
    Agentic knowledge lookup: adaptive route → hybrid retrieve → grade → rewrite
    loop → cited answer, with multi-turn memory. Assistive only; does not decide
    rule outcomes.

    Pass `conversation_id` to continue a conversation (must belong to the caller);
    omit it to start a new one.
    """
    from app.ai.langgraph_workflows.knowledge_tool import knowledge_lookup

    conv_service = KnowledgeConversationService(db)

    # If continuing a conversation, it must belong to the caller.
    if body.conversation_id:
        try:
            requested = uuid.UUID(body.conversation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="conversation_id must be a UUID")
        existing = conv_service.exists(requested)
        if existing is not None and existing.owner != owner:
            raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        result = await knowledge_lookup(
            body.query,
            db,
            conversation_id=body.conversation_id,
            filters=body.filters,
            min_trust=body.min_trust,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Record/refresh the conversation index row (owner, title, TTL, count).
    conversation_id = result.get("conversation_id")
    if conversation_id:
        try:
            conv_service.touch(uuid.UUID(conversation_id), owner, title=body.query)
        except Exception:  # index is best-effort; never fail the answer over it
            logger.warning("Failed to record conversation %s", conversation_id, exc_info=True)

    return KnowledgeAskResponse(
        query=result["query"],
        conversation_id=conversation_id,
        answer=result["answer"],
        route=result["route"],
        iterations=result["iterations"],
        citations=[Citation(**c) for c in result["citations"]],
    )


@router.get("/knowledge/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_sync_db),
    owner: str = Depends(get_conversation_owner),
):
    """List the caller's conversations, most recently updated first."""
    convs = KnowledgeConversationService(db).list_for_owner(owner, limit=limit, offset=offset)
    return [ConversationSummary.model_validate(c) for c in convs]


@router.get("/knowledge/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_sync_db),
    owner: str = Depends(get_conversation_owner),
):
    """Full history of a conversation (owner-checked), with persisted citations."""
    conv = KnowledgeConversationService(db).get_for_owner(conversation_id, owner)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    from app.ai.langgraph_workflows.knowledge_checkpointer import (
        get_conversation_checkpointer,
        get_thread_messages,
    )

    checkpointer = await get_conversation_checkpointer()
    raw = await get_thread_messages(checkpointer, str(conversation_id)) if checkpointer else None
    messages = [
        ConversationMessage(
            role=m.get("role", "assistant"),
            content=m.get("content", ""),
            citations=[Citation(**c) for c in m.get("citations", [])],
            created_at=m.get("created_at"),
        )
        for m in (raw or [])
    ]
    return ConversationDetail(id=conv.id, title=conv.title, messages=messages)


@router.delete("/knowledge/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_sync_db),
    owner: str = Depends(get_conversation_owner),
):
    """Delete a conversation (owner-checked) and its checkpointer state."""
    deleted = KnowledgeConversationService(db).delete_for_owner(conversation_id, owner)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    from app.ai.langgraph_workflows.knowledge_checkpointer import (
        delete_thread,
        get_conversation_checkpointer,
    )

    checkpointer = await get_conversation_checkpointer()
    if checkpointer is not None:
        try:
            await delete_thread(checkpointer, str(conversation_id))
        except Exception:  # pragma: no cover - infra dependent
            logger.warning("Failed to delete checkpoint state for %s", conversation_id, exc_info=True)
    return {"status": "deleted", "id": str(conversation_id)}
