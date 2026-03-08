"""
RAG pipeline service: ingest documents, chunk, embed, and store in the RAG database.

Supports .txt, .md, and .pdf. Uses the shared embedding service and pgvector for storage.
"""

import asyncio
import logging
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.rag import DEFAULT_EMBEDDING_DIMENSION, RAGChunk, RAGDocument
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()

# Chunking defaults (override with env RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)
RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "1000"))
RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "200"))


def _get_text_splitter():
    """Lazy import and return RecursiveCharacterTextSplitter."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        return RecursiveCharacterTextSplitter(
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
    except ImportError:
        try:
            from langchain_core.documents import Document
        except ImportError:
            from langchain.schema.document import Document
        # Fallback: simple split by double newline then by size
        class SimpleSplitter:
            def split_documents(self, docs: List[Any]) -> List[Any]:
                out: List[Any] = []
                for d in docs:
                    content = getattr(d, "page_content", str(d))
                    meta = getattr(d, "metadata", {}) or {}
                    parts = content.replace("\r\n", "\n").split("\n\n")
                    current = []
                    current_len = 0
                    for p in parts:
                        if current_len + len(p) > RAG_CHUNK_SIZE and current:
                            text = "\n\n".join(current)
                            out.append(Document(page_content=text, metadata=meta))
                            overlap = "\n\n".join(current[-2:]) if len(current) >= 2 else current[-1]
                            overlap = overlap[-RAG_CHUNK_OVERLAP:] if len(overlap) > RAG_CHUNK_OVERLAP else overlap
                            current = [overlap] if overlap else []
                            current_len = len(overlap)
                        current.append(p)
                        current_len += len(p)
                    if current:
                        out.append(Document(page_content="\n\n".join(current), metadata=meta))
                return out
        return SimpleSplitter()


def _load_text_file(filepath: str) -> str:
    """Load plain text or markdown file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def _load_pdf(filepath: str) -> str:
    """Load PDF and return extracted text."""
    try:
        from pypdf import PdfReader
    except ImportError:
        raise ImportError("pypdf is required for PDF support. Install with: pip install pypdf")
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def load_document_text(filepath: str, content_type: Optional[str] = None) -> str:
    """Load document content as text. Supports .txt, .md, .pdf."""
    path = Path(filepath)
    suffix = path.suffix.lower()
    if content_type and "pdf" in content_type:
        return _load_pdf(filepath)
    if suffix == ".pdf":
        return _load_pdf(filepath)
    if suffix in (".txt", ".md", ".markdown"):
        return _load_text_file(filepath)
    # Guess by content type
    if content_type:
        if "text" in content_type:
            return _load_text_file(filepath)
        if "pdf" in content_type:
            return _load_pdf(filepath)
    # Default: try as text
    return _load_text_file(filepath)


class RAGPipelineService:
    """Service for ingesting documents into the RAG database and searching."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _ensure_embedding_dimension(self) -> int:
        """Return embedding dimension and ensure it matches our schema."""
        dim = embedding_service.get_dimension()
        if dim != DEFAULT_EMBEDDING_DIMENSION:
            logger.warning(
                "RAG embedding dimension %s does not match schema default %s. "
                "Ensure your embedding model matches DEFAULT_EMBEDDING_DIMENSION or run a migration.",
                dim,
                DEFAULT_EMBEDDING_DIMENSION,
            )
        return dim

    def create_document(
        self,
        filename: str,
        filepath: str,
        *,
        content_type: Optional[str] = None,
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> RAGDocument:
        """Create a RAG document record (pending ingestion)."""
        doc = RAGDocument(
            filename=filename,
            filepath=filepath,
            content_type=content_type or mimetypes.guess_type(filename)[0],
            title=title or filename,
            source=source or "upload",
            metadata_=metadata or {},
            status="pending",
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def _load_and_chunk(self, document_id: uuid.UUID) -> tuple[RAGDocument, List[str], List[Dict[str, Any]]]:
        """Load document text and return chunks (texts and metadata). Raises on failure."""
        doc = self.db.get(RAGDocument, document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")
        if doc.status == "ingesting":
            raise ValueError("Document is already being ingested")
        doc.status = "ingesting"
        doc.error_message = None
        self.db.commit()
        try:
            text = load_document_text(doc.filepath, doc.content_type)
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            self.db.commit()
            raise
        try:
            from langchain.schema.document import Document as LCDocument
        except ImportError:
            from langchain_core.documents import Document as LCDocument
        lc_doc = LCDocument(page_content=text, metadata={"source": doc.filename})
        splitter = _get_text_splitter()
        chunks_lc = splitter.split_documents([lc_doc])
        texts = [c.page_content for c in chunks_lc]
        metadatas = [getattr(c, "metadata", {}) or {} for c in chunks_lc]
        return doc, texts, metadatas

    def _write_chunks(self, doc: RAGDocument, texts: List[str], embeddings: List[List[float]], metadatas: List[Dict[str, Any]]) -> None:
        """Write chunks to DB and update document status."""
        document_id = doc.id
        self.db.query(RAGChunk).filter(RAGChunk.document_id == document_id).delete()
        for i, (content, emb) in enumerate(zip(texts, embeddings)):
            chunk = RAGChunk(
                document_id=document_id,
                content=content,
                chunk_index=i,
                metadata_=metadatas[i] if i < len(metadatas) else {},
                embedding=emb,
            )
            self.db.add(chunk)
        doc.chunk_count = len(texts)
        doc.status = "completed"
        doc.ingested_at = datetime.utcnow()
        doc.error_message = None
        self.db.commit()
        self.db.refresh(doc)

    def ingest_document(self, document_id: uuid.UUID) -> RAGDocument:
        """
        Synchronous ingest: load, chunk, embed (blocking), store.
        Prefer ingest_document_async from async code.
        """
        doc, texts, metadatas = self._load_and_chunk(document_id)
        if not texts:
            doc.status = "completed"
            doc.chunk_count = 0
            doc.ingested_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(doc)
            return doc
        # Sync callers (CLI, scripts): use asyncio.run. From async code use ingest_document_async.
        embeddings = asyncio.run(embedding_service.get_embeddings(texts))
        self._ensure_embedding_dimension()
        self._write_chunks(doc, texts, embeddings, metadatas)
        return doc

    async def ingest_document_async(self, document_id: uuid.UUID) -> RAGDocument:
        """Async ingest: load/chunk in executor (no DB in executor), await embeddings, write in main thread."""
        loop = asyncio.get_event_loop()
        doc, texts, metadatas = await loop.run_in_executor(
            None,
            lambda: self._load_and_chunk(document_id),
        )
        if not texts:
            doc.status = "completed"
            doc.chunk_count = 0
            doc.ingested_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(doc)
            return doc
        self._ensure_embedding_dimension()
        embeddings = await embedding_service.get_embeddings(texts)
        # DB writes in main thread (session not thread-safe)
        self._write_chunks(doc, texts, embeddings, metadatas)
        self.db.refresh(doc)
        return doc

    def list_documents(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RAGDocument]:
        """List RAG documents with optional status filter."""
        q = self.db.query(RAGDocument).order_by(RAGDocument.created_at.desc())
        if status:
            q = q.filter(RAGDocument.status == status)
        return q.offset(offset).limit(limit).all()

    def get_document(self, document_id: uuid.UUID) -> Optional[RAGDocument]:
        """Get a single RAG document by id."""
        return self.db.get(RAGDocument, document_id)

    def delete_document(self, document_id: uuid.UUID) -> bool:
        """Delete a document and its chunks. Returns True if deleted."""
        doc = self.db.get(RAGDocument, document_id)
        if not doc:
            return False
        self.db.delete(doc)
        self.db.commit()
        return True

    def search_sync(
        self,
        query: str,
        top_k: int = 10,
        document_ids: Optional[List[uuid.UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Synchronous semantic search. From async code use search() instead.
        """
        try:
            query_embedding = asyncio.run(embedding_service.get_embedding(query))
        except RuntimeError:
            raise RuntimeError("Use search() from async code (e.g. FastAPI), not search_sync")
        return self._search_impl(query_embedding, top_k, document_ids)

    async def search(
        self,
        query: str,
        top_k: int = 10,
        document_ids: Optional[List[uuid.UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search: embed query, find nearest chunks by cosine distance.
        Returns list of dicts with chunk_id, document_id, filename, content, chunk_index, score, metadata.
        """
        query_embedding = await embedding_service.get_embedding(query)
        return self._search_impl(query_embedding, top_k, document_ids)

    def _search_impl(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        document_ids: Optional[List[uuid.UUID]] = None,
    ) -> List[Dict[str, Any]]:
        # Use pgvector cosine distance (<=>); order by distance ascending
        q = (
            select(
                RAGChunk.id,
                RAGChunk.document_id,
                RAGChunk.content,
                RAGChunk.chunk_index,
                RAGChunk.metadata_,
                RAGDocument.filename,
                (1 - RAGChunk.embedding.cosine_distance(query_embedding)).label("score"),
            )
            .join(RAGDocument, RAGChunk.document_id == RAGDocument.id)
            .where(RAGChunk.embedding.isnot(None))
        )
        if document_ids:
            q = q.where(RAGDocument.id.in_(document_ids))
        q = q.order_by(RAGChunk.embedding.cosine_distance(query_embedding)).limit(top_k)
        rows = self.db.execute(q).all()
        return [
            {
                "chunk_id": r.id,
                "document_id": r.document_id,
                "filename": r.filename,
                "content": r.content,
                "chunk_index": r.chunk_index,
                "score": float(r.score),
                "metadata": r.metadata_ or {},
            }
            for r in rows
        ]


def get_rag_pipeline_service(db: Session) -> RAGPipelineService:
    """Dependency: return RAG pipeline service."""
    return RAGPipelineService(db)
