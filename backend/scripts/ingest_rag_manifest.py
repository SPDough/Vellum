"""Manifest-driven RAG ingestion runner for Vellum MVP.

Operational features:
- reads a manifest JSON file
- creates RAG document records
- ingests chunks/embeddings into the canonical RAG store
- supports explicit embedding provider selection
- can skip already-ingested documents by filepath
- can limit run size for smoke tests / partial waves
- continues past per-document failures with a final summary

Usage:
  source backend/.venv/bin/activate
  PYTHONPATH=backend python backend/scripts/ingest_rag_manifest.py \
    --manifest data/rag/manifests/wave1-industry-reference.json \
    --provider openai \
    --skip-existing \
    --continue-on-error
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.rag import RAGDocument  # noqa: E402
from app.services.embedding_service import embedding_service  # noqa: E402
from app.services.rag_pipeline_service import RAGPipelineService  # noqa: E402


def load_manifest(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("Manifest must be a JSON array of document entries")
    return data


def select_embedding_provider(provider_name: str) -> None:
    if provider_name not in embedding_service.providers:
        available = ", ".join(sorted(embedding_service.providers.keys()))
        raise RuntimeError(
            f"Embedding provider '{provider_name}' is not available. Available: {available}"
        )
    embedding_service.primary_provider = embedding_service.providers[provider_name]


def find_existing_document(db, filepath: str) -> Optional[RAGDocument]:
    stmt = select(RAGDocument).where(RAGDocument.filepath == filepath).order_by(RAGDocument.created_at.desc())
    return db.execute(stmt).scalars().first()


def format_title(entry: Dict[str, Any]) -> str:
    filepath = entry["filepath"]
    return entry.get("title") or Path(filepath).name


def ingest_manifest(
    manifest_path: Path,
    *,
    provider: str,
    limit: Optional[int],
    skip_existing: bool,
    continue_on_error: bool,
) -> int:
    entries = load_manifest(manifest_path)
    if limit is not None:
        entries = entries[:limit]

    select_embedding_provider(provider)
    print(
        f"MANIFEST_START :: file={manifest_path} :: entries={len(entries)} :: provider={provider}"
    )

    db = SessionLocal()
    service = RAGPipelineService(db)
    success = 0
    skipped = 0
    failed = 0

    try:
        for index, entry in enumerate(entries, start=1):
            filepath = entry["filepath"]
            filename = Path(filepath).name
            title = format_title(entry)
            metadata = {k: v for k, v in entry.items() if k not in {"filepath", "title"}}

            print(f"INGEST_ITEM_START :: {index}/{len(entries)} :: {title}")

            try:
                if skip_existing:
                    existing = find_existing_document(db, filepath)
                    if existing and existing.status == "completed":
                        print(
                            "INGEST_ITEM_SKIP :: "
                            f"{title} :: reason=existing_completed :: id={existing.id} :: chunks={existing.chunk_count}"
                        )
                        skipped += 1
                        continue

                doc = service.create_document(
                    filename=filename,
                    filepath=filepath,
                    title=title,
                    source=entry.get("source_type") or "manifest",
                    metadata=metadata,
                )
                doc = service.ingest_document(doc.id)
                print(
                    "INGEST_ITEM_OK :: "
                    f"{doc.title} :: status={doc.status} :: chunks={doc.chunk_count} :: id={doc.id}"
                )
                success += 1

            except Exception as exc:
                failed += 1
                print(
                    "INGEST_ITEM_ERROR :: "
                    f"{title} :: error={exc.__class__.__name__}: {exc}"
                )
                traceback.print_exc()
                if not continue_on_error:
                    raise

    finally:
        db.close()

    print(
        "MANIFEST_INGEST_COMPLETE :: "
        f"success={success} :: skipped={skipped} :: failed={failed} :: total={len(entries)}"
    )
    return success


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON file")
    parser.add_argument(
        "--provider",
        default="openai",
        help="Embedding provider to force for this run (default: openai)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N manifest entries",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip entries whose filepath already has a completed RAG document",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing remaining manifest entries after a document failure",
    )
    args = parser.parse_args()

    manifest_path = (
        (ROOT / args.manifest).resolve()
        if not Path(args.manifest).is_absolute()
        else Path(args.manifest)
    )
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    ingest_manifest(
        manifest_path,
        provider=args.provider,
        limit=args.limit,
        skip_existing=args.skip_existing,
        continue_on_error=args.continue_on_error,
    )


if __name__ == "__main__":
    main()
