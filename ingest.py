"""
Otomeshon RAG ingestion — entry point (redirects to backend).

The ingestion pipeline lives in backend/app/rag/ingest.py.

Run from repo root:
  PYTHONPATH=backend python -m app.rag.ingest --doc weiss_book
  PYTHONPATH=backend python -m app.rag.ingest --all

Or from backend directory:
  python -m app.rag.ingest --doc weiss_book
"""
import os
import sys

# Add backend to path so app.rag is resolvable
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_REPO_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

if __name__ == "__main__":
    from app.rag.ingest import main
    main()
