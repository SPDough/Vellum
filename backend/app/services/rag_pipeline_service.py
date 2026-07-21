"""
RAG pipeline service: ingest documents, chunk, embed, and store in the RAG database.

Supports .txt, .md, .pdf, and .docx. Parsing prefers Docling (structure-preserving
Markdown, tables intact) with pypdf/plain-text fallback. Chunking is structure-aware
for Markdown output; chunks can optionally be prefixed with an LLM-generated context
blurb before embedding (RAG_CONTEXTUAL_ENRICHMENT). Uses the shared embedding
service and pgvector for storage.
"""

import asyncio
import logging
import mimetypes
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_sync_db
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


_MD_HEADERS = [("#", "h1"), ("##", "h2"), ("###", "h3")]


def _split_markdown(text: str, base_metadata: Dict[str, Any]) -> tuple[List[str], List[Dict[str, Any]]]:
    """
    Structure-aware split: divide on Markdown headings, then recursively split any
    section larger than RAG_CHUNK_SIZE. Each chunk's metadata carries its section
    path (e.g. "Accrual conventions > Mezzanine tranches") for citation and filtering.
    Falls back to the plain splitter if Markdown splitting is unavailable.
    """
    try:
        from langchain_text_splitters import (
            MarkdownHeaderTextSplitter,
            RecursiveCharacterTextSplitter,
        )
    except ImportError:
        return _split_plain(text, base_metadata)

    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=_MD_HEADERS, strip_headers=False
    )
    sections = header_splitter.split_text(text)
    if not sections:
        return _split_plain(text, base_metadata)
    size_splitter = RecursiveCharacterTextSplitter(
        chunk_size=RAG_CHUNK_SIZE,
        chunk_overlap=RAG_CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = size_splitter.split_documents(sections)
    texts: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    for c in chunks:
        # Skip fragments too small to be meaningful (e.g. a bare heading chunk)
        if len(c.page_content.strip()) < 40:
            continue
        meta = dict(base_metadata)
        headers = [c.metadata.get(k) for _, k in _MD_HEADERS]
        section = " > ".join(h for h in headers if h)
        if section:
            meta["section"] = section
        texts.append(c.page_content)
        metadatas.append(meta)
    return texts, metadatas


def _split_plain(text: str, base_metadata: Dict[str, Any]) -> tuple[List[str], List[Dict[str, Any]]]:
    """Character-based split for non-Markdown content (legacy path)."""
    try:
        from langchain.schema.document import Document as LCDocument
    except ImportError:
        from langchain_core.documents import Document as LCDocument
    lc_doc = LCDocument(page_content=text, metadata=dict(base_metadata))
    splitter = _get_text_splitter()
    chunks_lc = splitter.split_documents([lc_doc])
    return (
        [c.page_content for c in chunks_lc],
        [dict(getattr(c, "metadata", {}) or {}) for c in chunks_lc],
    )


def _docling_available() -> bool:
    """Return True if docling is importable (heavy optional dependency)."""
    try:
        import docling.document_converter  # noqa: F401
        return True
    except ImportError:
        return False


def _load_with_docling(filepath: str) -> str:
    """Parse a document with Docling and return structure-preserving Markdown."""
    from docling.document_converter import DocumentConverter

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    converter = DocumentConverter()
    result = converter.convert(str(path))
    return result.document.export_to_markdown()


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


def load_document(filepath: str, content_type: Optional[str] = None) -> tuple[str, str]:
    """
    Load document content. Returns (text, format) where format is "markdown" or "text".

    PDFs and Office documents go through Docling when available and enabled
    (RAG_USE_DOCLING), yielding Markdown with tables preserved; otherwise PDF
    falls back to pypdf plain-text extraction. .md files are Markdown natively.
    """
    path = Path(filepath)
    suffix = path.suffix.lower()
    is_pdf = suffix == ".pdf" or bool(content_type and "pdf" in content_type)
    is_office = suffix in (".docx", ".pptx", ".html", ".htm")

    if (is_pdf or is_office) and settings.rag_use_docling and _docling_available():
        try:
            return _load_with_docling(filepath), "markdown"
        except Exception as e:
            if not is_pdf:
                raise
            logger.warning("Docling parse failed for %s (%s); falling back to pypdf", filepath, e)
    if is_pdf:
        return _load_pdf(filepath), "text"
    if is_office:
        raise ValueError(
            f"Unsupported format {suffix} without docling. Install docling for Office/HTML support."
        )
    if suffix in (".md", ".markdown"):
        return _load_text_file(filepath), "markdown"
    if suffix == ".txt" or (content_type and "text" in content_type):
        return _load_text_file(filepath), "text"
    # Default: try as text
    return _load_text_file(filepath), "text"


def load_document_text(filepath: str, content_type: Optional[str] = None) -> str:
    """Load document content as text (back-compat wrapper for load_document)."""
    return load_document(filepath, content_type)[0]


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

    def _load_and_chunk(
        self, document_id: uuid.UUID
    ) -> tuple[RAGDocument, str, List[str], List[Dict[str, Any]]]:
        """Load document text and return (doc, full_text, chunk texts, chunk metadata)."""
        doc = self.db.get(RAGDocument, document_id)
        if not doc:
            raise ValueError(f"Document not found: {document_id}")
        if doc.status == "ingesting":
            raise ValueError("Document is already being ingested")
        doc.status = "ingesting"
        doc.error_message = None
        self.db.commit()
        try:
            text, fmt = load_document(doc.filepath, doc.content_type)
        except Exception as e:
            doc.status = "failed"
            doc.error_message = str(e)
            self.db.commit()
            raise
        base_metadata = {"source": doc.filename, "format": fmt}
        if fmt == "markdown":
            texts, metadatas = _split_markdown(text, base_metadata)
        else:
            texts, metadatas = _split_plain(text, base_metadata)
        return doc, text, texts, metadatas

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

    def _get_enrichment_llm(self):
        """Return a chat model for contextual enrichment, or None if unconfigured."""
        model = settings.rag_enrichment_model
        try:
            if model.startswith("claude") and settings.anthropic_api_key:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=model, api_key=settings.anthropic_api_key, temperature=0.0
                )
            if settings.openai_api_key:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=model, api_key=settings.openai_api_key, temperature=0.0
                )
        except ImportError:
            pass
        logger.warning("Contextual enrichment enabled but no usable LLM; skipping")
        return None

    async def _contextualize_chunks(
        self,
        doc: RAGDocument,
        full_text: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Prepend an LLM-generated context blurb to each chunk before embedding
        (contextual retrieval). No-op unless RAG_CONTEXTUAL_ENRICHMENT is set.
        The original chunk text is preserved in chunk metadata under "original_content".
        """
        if not settings.rag_contextual_enrichment:
            return texts
        llm = self._get_enrichment_llm()
        if llm is None:
            return texts
        doc_context = full_text[: settings.rag_enrichment_doc_context_chars]
        semaphore = asyncio.Semaphore(5)

        async def enrich(i: int, chunk: str) -> str:
            section = metadatas[i].get("section", "")
            prompt = (
                "You are indexing a banking-operations knowledge base. "
                "Give a 2-3 sentence context situating this chunk within the document, "
                "for retrieval. Answer with the context only.\n\n"
                f"Document title: {doc.title}\n"
                f"Section: {section or 'n/a'}\n"
                f"Document start:\n{doc_context}\n\n"
                f"Chunk:\n{chunk[:2000]}"
            )
            async with semaphore:
                try:
                    response = await llm.ainvoke(prompt)
                except Exception as e:
                    logger.warning("Enrichment failed for chunk %s of %s: %s", i, doc.id, e)
                    return chunk
            context = (response.content or "").strip()
            if not context:
                return chunk
            metadatas[i]["original_content"] = chunk
            metadatas[i]["context"] = context
            return f"{context}\n\n{chunk}"

        return list(await asyncio.gather(*(enrich(i, c) for i, c in enumerate(texts))))

    async def _enrich_and_embed(
        self,
        doc: RAGDocument,
        full_text: str,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> tuple[List[str], List[List[float]]]:
        """Optionally contextualize chunks, then embed them."""
        texts = await self._contextualize_chunks(doc, full_text, texts, metadatas)
        embeddings = await embedding_service.get_embeddings(texts)
        return texts, embeddings

    def _complete_empty(self, doc: RAGDocument) -> RAGDocument:
        """Mark a document with no extractable chunks as completed."""
        doc.status = "completed"
        doc.chunk_count = 0
        doc.ingested_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def ingest_document(self, document_id: uuid.UUID) -> RAGDocument:
        """
        Synchronous ingest: load, chunk, optionally contextualize, embed (blocking), store.
        Prefer ingest_document_async from async code.
        """
        doc, full_text, texts, metadatas = self._load_and_chunk(document_id)
        if not texts:
            return self._complete_empty(doc)
        # Sync callers (CLI, scripts): use asyncio.run. From async code use ingest_document_async.
        texts, embeddings = asyncio.run(self._enrich_and_embed(doc, full_text, texts, metadatas))
        self._ensure_embedding_dimension()
        self._write_chunks(doc, texts, embeddings, metadatas)
        return doc

    async def ingest_document_async(self, document_id: uuid.UUID) -> RAGDocument:
        """Async ingest: load/chunk in executor (no DB in executor), await embeddings, write in main thread."""
        loop = asyncio.get_event_loop()
        doc, full_text, texts, metadatas = await loop.run_in_executor(
            None,
            lambda: self._load_and_chunk(document_id),
        )
        if not texts:
            return self._complete_empty(doc)
        self._ensure_embedding_dimension()
        texts, embeddings = await self._enrich_and_embed(doc, full_text, texts, metadatas)
        # DB writes in main thread (session not thread-safe)
        self._write_chunks(doc, texts, embeddings, metadatas)
        self.db.refresh(doc)
        return doc

    def list_documents(
        self,
        *,
        status: Optional[str] = None,
        metadata_filters: Optional[Dict[str, str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RAGDocument]:
        """
        List RAG documents with optional status filter and corpus filters
        (equality matches on metadata contract fields, e.g. domain, trust_level).
        """
        q = self.db.query(RAGDocument).order_by(RAGDocument.created_at.desc())
        if status:
            q = q.filter(RAGDocument.status == status)
        for key, value in (metadata_filters or {}).items():
            q = q.filter(RAGDocument.metadata_[key].astext == value)
        return q.offset(offset).limit(limit).all()

    def status_summary(self) -> Dict[str, int]:
        """Return document counts by ingestion status (power-user job overview)."""
        from sqlalchemy import func

        rows = (
            self.db.query(RAGDocument.status, func.count(RAGDocument.id))
            .group_by(RAGDocument.status)
            .all()
        )
        return {status: count for status, count in rows}

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


def get_rag_pipeline_service(db: Session = Depends(get_sync_db)) -> RAGPipelineService:
    """Dependency: return RAG pipeline service."""
    return RAGPipelineService(db)
