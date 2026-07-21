"""
Prefect flow for knowledge-repository document ingestion.

Wraps the RAG pipeline (parse -> chunk -> optional contextual enrichment -> embed
-> store) with retries and observable task states, for power-user batch loading.

Run locally (from backend/):
    python -m flows.knowledge_ingestion /path/to/doc.pdf --metadata /path/to/meta.json
"""

import argparse
import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from prefect import flow, get_run_logger, task


@task(name="validate-metadata")
def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce the knowledge metadata contract before touching the database."""
    from app.schemas.rag_metadata import KnowledgeDocumentMetadata

    contract = KnowledgeDocumentMetadata.model_validate(metadata)
    return contract.to_document_metadata()


@task(name="register-document")
def register_document(filepath: str, metadata: Dict[str, Any]) -> str:
    """Create the RAGDocument record (pending ingestion). Returns document id."""
    from app.core.database import SessionLocal
    from app.services.rag_pipeline_service import RAGPipelineService

    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    with SessionLocal() as db:
        service = RAGPipelineService(db)
        doc = service.create_document(
            filename=path.name,
            filepath=str(path.resolve()),
            title=metadata.get("title") or path.stem,
            source="prefect_flow",
            metadata=metadata,
        )
        return str(doc.id)


@task(name="ingest-document", retries=2, retry_delay_seconds=30)
def ingest_document(document_id: str) -> Dict[str, Any]:
    """Run the pipeline: load, chunk, optionally contextualize, embed, store."""
    from app.core.database import SessionLocal
    from app.services.rag_pipeline_service import RAGPipelineService

    with SessionLocal() as db:
        service = RAGPipelineService(db)
        doc = service.ingest_document(uuid.UUID(document_id))
        return {
            "document_id": str(doc.id),
            "status": doc.status,
            "chunk_count": doc.chunk_count,
            "error": doc.error_message,
        }


@flow(name="knowledge-ingestion")
def knowledge_ingestion_flow(
    filepaths: List[str],
    metadata: Dict[str, Any],
    title_from_filename: bool = True,
) -> List[Dict[str, Any]]:
    """
    Ingest one or more documents into the knowledge repository under a shared
    metadata contract. Per-file titles default to the filename stem.
    """
    logger = get_run_logger()
    validated = validate_metadata(metadata)
    results: List[Dict[str, Any]] = []
    for filepath in filepaths:
        file_metadata = dict(validated)
        if title_from_filename:
            file_metadata["title"] = Path(filepath).stem
        document_id = register_document(filepath, file_metadata)
        result = ingest_document(document_id)
        logger.info(
            "Ingested %s: status=%s chunks=%s",
            filepath,
            result["status"],
            result["chunk_count"],
        )
        results.append(result)
    return results


def _main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Ingest documents into the knowledge repository")
    parser.add_argument("filepaths", nargs="+", help="Document paths to ingest")
    parser.add_argument(
        "--metadata",
        required=True,
        help="Path to a JSON file with metadata contract fields shared by all documents",
    )
    args = parser.parse_args(argv)
    with open(args.metadata, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    results = knowledge_ingestion_flow(args.filepaths, metadata)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    _main()
