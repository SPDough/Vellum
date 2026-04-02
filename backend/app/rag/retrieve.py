"""
Otomeshon RAG Retrieval Module (NAV/findings).
Called by the FastAPI backend when generating AI explanations for findings.

Uses nav_rag_documents and nav_rag_chunks (migration 003).
"""

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import openai
import psycopg2
from psycopg2.extras import RealDictCursor

log = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMS = 1536

# Pre-built query expansions for known finding types
FINDING_QUERIES = {
    "missed_dividend": (
        "dividend income not processed by custodian, "
        "ex-dividend date record date payable date takeoff control account, "
        "DIVINC transaction missing, dividendAppliedIndicator not updated, "
        "NAV overstatement due to missing dividend accrual"
    ),
    "missing_corporate_action": (
        "corporate action not processed, merger acquisition spinoff stock split, "
        "takeoff record date custodian corporate actions department, "
        "DTC DTCC allocation control account reorg"
    ),
    "pricing_error": (
        "stale price market price error, marketPriceStaleIndicator, "
        "incorrect market value NAV impact, pricing vendor feed failure"
    ),
    "accrual_error": (
        "interest accrual error, income accrual incorrect, "
        "interestAccruedAmountBase wrong, bond interest coupon payment, "
        "accrued income receivable discrepancy"
    ),
    "settlement_fail": (
        "fail to deliver fail to receive settlement failure, "
        "T+2 settlement cycle DTC NSCC continuous net settlement, "
        "position discrepancy between custodian and fund accountant"
    ),
}


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_type: str
    score: float
    content: str
    chapter: Optional[str] = None
    chapter_title: Optional[str] = None
    section: Optional[str] = None
    section_title: Optional[str] = None
    page_start: Optional[int] = None
    mart_name: Optional[str] = None
    topics: list = field(default_factory=list)


RetrievalPurpose = str  # 'explain' | 'rule' | 'report'

PURPOSE_DOC_TYPE_BIAS: dict[str, list[str]] = {
    "explain": ["book", "manual"],
    "rule": ["manual", "api_spec"],
    "report": ["book", "paper"],
}

PURPOSE_TAG_BIAS: dict[str, list[str]] = {
    "explain": ["nav_validation", "fund_accounting", "corporate_actions", "settlement_ops"],
    "rule": ["validation_rules", "regulatory_basis", "api_reference"],
    "report": ["client_reporting", "nav_validation", "corporate_actions"],
}


@dataclass
class RetrievalResult:
    query: str
    purpose: RetrievalPurpose
    chunks: list[RetrievedChunk]
    latency_ms: int

    def to_prompt_block(self) -> str:
        if not self.chunks:
            return ""
        if self.purpose == "rule":
            return self._prompt_block_rule()
        elif self.purpose == "report":
            return self._prompt_block_report()
        return self._prompt_block_explain()

    def _prompt_block_explain(self) -> str:
        lines = [
            "=== KNOWLEDGE BASE: OPERATIONAL CONTEXT ===",
            "The following passages are from industry reference documents.",
            "Use them to ground your explanation in established operational practice.",
            "Cite the source when it adds credibility to a specific claim.",
            "",
        ]
        for i, chunk in enumerate(self.chunks, 1):
            lines.append(f"[{i}] {self._citation(chunk)}")
            lines.append(chunk.content)
            lines.append("")
        lines.append("=== END CONTEXT ===")
        return "\n".join(lines)

    def _prompt_block_rule(self) -> str:
        lines = [
            "=== KNOWLEDGE BASE: RULES AND PROCEDURES ===",
            "The following passages contain regulatory rules, operational procedures,",
            "and API field definitions relevant to this validation check.",
            "Identify the specific rule or procedure that governs the check being performed.",
            "",
        ]
        for i, chunk in enumerate(self.chunks, 1):
            lines.append(f"[{i}] {self._citation(chunk)}")
            lines.append(chunk.content)
            lines.append("")
        lines.append("=== END CONTEXT ===")
        return "\n".join(lines)

    def _prompt_block_report(self) -> str:
        lines = [
            "=== KNOWLEDGE BASE: REFERENCE CONTEXT ===",
            "The following background passages may inform the client communication.",
            "Use accessible language. Avoid internal jargon. Do not quote directly.",
            "Summarise the relevant concept in plain terms appropriate for a sophisticated",
            "institutional investor who is not a daily operations professional.",
            "",
        ]
        for i, chunk in enumerate(self.chunks, 1):
            lines.append(f"[{i}] {self._citation(chunk)}")
            lines.append(chunk.content)
            lines.append("")
        lines.append("=== END CONTEXT ===")
        return "\n".join(lines)

    def _citation(self, chunk: RetrievedChunk) -> str:
        parts = [chunk.doc_title]
        if chunk.chapter_title:
            parts.append(chunk.chapter_title)
        if chunk.section_title:
            parts.append(chunk.section_title)
        elif chunk.mart_name:
            parts.append(f"API Mart: {chunk.mart_name}")
        if chunk.page_start:
            parts.append(f"p.{chunk.page_start}")
        return " > ".join(parts)

    def to_citations(self) -> list[dict]:
        return [
            {
                "index": i + 1,
                "chunk_id": c.chunk_id,
                "doc_title": c.doc_title,
                "doc_type": c.doc_type,
                "chapter_title": c.chapter_title,
                "section_title": c.section_title,
                "mart_name": c.mart_name,
                "page": c.page_start,
                "score": round(c.score, 4),
                "purpose": self.purpose,
            }
            for i, c in enumerate(self.chunks)
        ]


class RagRetriever:
    """Main retrieval interface for NAV/findings RAG. Uses nav_rag_* tables."""

    # Table names used by this retriever (NAV RAG schema)
    DOCS_TABLE = "nav_rag_documents"
    CHUNKS_TABLE = "nav_rag_chunks"
    LOG_TABLE = "rag_retrieval_log"

    def __init__(self, db_conn, openai_client: openai.OpenAI):
        self.conn = db_conn
        self.client = openai_client

    def _embed_query(self, query: str) -> list[float]:
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[query],
            dimensions=EMBEDDING_DIMS,
        )
        return response.data[0].embedding

    def retrieve(
        self,
        query: str,
        top_k: int = 6,
        purpose: RetrievalPurpose = "explain",
        filter_doc_type: Optional[str] = None,
        filter_tags: Optional[list[str]] = None,
        filter_mart: Optional[str] = None,
        min_score: float = 0.30,
    ) -> RetrievalResult:
        t0 = time.monotonic()
        query_embedding = self._embed_query(query)
        embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

        conditions = [f"1 - (c.embedding <=> '{embedding_str}'::vector) >= {min_score}"]
        params: dict = {}

        if filter_doc_type:
            conditions.append("d.doc_type = %(doc_type)s")
            params["doc_type"] = filter_doc_type

        if filter_tags:
            conditions.append("c.relevance_tags && %(tags)s::text[]")
            params["tags"] = filter_tags

        if filter_mart:
            conditions.append("c.mart_name = %(mart)s")
            params["mart"] = filter_mart

        where_clause = " AND ".join(conditions)
        docs_t = self.DOCS_TABLE
        chunks_t = self.CHUNKS_TABLE

        sql = f"""
            SELECT
                c.chunk_id,
                c.doc_id,
                d.title          AS doc_title,
                d.doc_type,
                1 - (c.embedding <=> %(embedding)s::vector) AS score,
                c.content,
                c.chapter,
                c.chapter_title,
                c.section,
                c.section_title,
                c.page_start,
                c.mart_name,
                c.topics
            FROM {chunks_t} c
            JOIN {docs_t} d ON c.doc_id = d.doc_id
            WHERE {where_clause}
            ORDER BY c.embedding <=> %(embedding)s::vector
            LIMIT %(top_k)s
        """
        params["embedding"] = embedding_str
        params["top_k"] = top_k

        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        chunks = [
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                doc_id=row["doc_id"],
                doc_title=row["doc_title"],
                doc_type=row["doc_type"],
                score=float(row["score"]),
                content=row["content"],
                chapter=row.get("chapter"),
                chapter_title=row.get("chapter_title"),
                section=row.get("section"),
                section_title=row.get("section_title"),
                page_start=row.get("page_start"),
                mart_name=row.get("mart_name"),
                topics=row.get("topics") or [],
            )
            for row in rows
        ]

        latency_ms = int((time.monotonic() - t0) * 1000)
        self._log_retrieval(query, purpose, top_k, filter_tags, chunks, latency_ms)

        return RetrievalResult(
            query=query,
            purpose=purpose,
            chunks=chunks,
            latency_ms=latency_ms,
        )

    def retrieve_for_finding(
        self,
        finding_type: str,
        mart_names: Optional[list[str]] = None,
        top_k: int = 8,
        purpose: RetrievalPurpose = "explain",
    ) -> RetrievalResult:
        query = FINDING_QUERIES.get(finding_type, f"NAV validation error: {finding_type}")
        doc_types = PURPOSE_DOC_TYPE_BIAS.get(purpose, ["book", "manual"])
        tag_filters = PURPOSE_TAG_BIAS.get(purpose, ["nav_validation"])

        primary_doc_type = "manual" if purpose == "rule" else "book"

        prose_result = self.retrieve(
            query=query,
            top_k=top_k // 2 + 1,
            purpose=purpose,
            filter_doc_type=primary_doc_type if primary_doc_type in doc_types else None,
            filter_tags=tag_filters,
        )

        if len(prose_result.chunks) < 2:
            prose_result = self.retrieve(
                query=query,
                top_k=top_k // 2 + 1,
                purpose=purpose,
                filter_tags=tag_filters,
            )

        # Chunks may have empty relevance_tags when keyword tagging misses; tag overlap
        # then filters out every row. Fall back to pure semantic search.
        if len(prose_result.chunks) < 2:
            log.info(
                "retrieve_for_finding: insufficient chunks with tag filters; retrying without tags"
            )
            prose_result = self.retrieve(
                query=query,
                top_k=top_k // 2 + 1,
                purpose=purpose,
                filter_tags=None,
            )

        if len(prose_result.chunks) < 2:
            log.info(
                "retrieve_for_finding: insufficient chunks at min_score=0.30; retrying at 0.15"
            )
            prose_result = self.retrieve(
                query=query,
                top_k=top_k // 2 + 1,
                purpose=purpose,
                filter_tags=None,
                min_score=0.15,
            )

        api_chunks: list[RetrievedChunk] = []
        if mart_names:
            for mart in mart_names:
                mart_result = self.retrieve(
                    query=f"API fields for {mart}: {query}",
                    top_k=2,
                    purpose=purpose,
                    filter_mart=mart,
                )
                api_chunks.extend(mart_result.chunks)

        seen: set[str] = set()
        combined: list[RetrievedChunk] = []
        for chunk in sorted(
            prose_result.chunks + api_chunks,
            key=lambda c: c.score,
            reverse=True,
        ):
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                combined.append(chunk)
            if len(combined) >= top_k:
                break

        return RetrievalResult(
            query=query,
            purpose=purpose,
            chunks=combined,
            latency_ms=prose_result.latency_ms,
        )

    def _log_retrieval(self, query, purpose, top_k, filter_tags, chunks, latency_ms):
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    f"""
                    INSERT INTO {self.LOG_TABLE}
                        (query_text, query_context, top_k, filter_tags, chunks_returned, latency_ms)
                    VALUES (%s, %s, %s, %s::text[], %s, %s)
                    """,
                    (
                        query[:500],
                        purpose,
                        top_k,
                        filter_tags,
                        json.dumps([
                            {"chunk_id": c.chunk_id, "score": c.score, "doc_id": c.doc_id}
                            for c in chunks
                        ]),
                        latency_ms,
                    ),
                )
                self.conn.commit()
        except Exception:
            pass
