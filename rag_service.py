"""
Otomeshon RAG → FastAPI integration — redirect to backend package.

Use:
  from app.rag.rag_service import (
      get_rag_retriever,
      build_explanation_prompt,
      build_rule_prompt,
      build_report_prompt,
  )

Ensure backend is on PYTHONPATH (e.g. PYTHONPATH=backend when running).
"""
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_BACKEND = os.path.join(_REPO_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

from app.rag.rag_service import (
    get_rag_retriever,
    build_explanation_prompt,
    build_rule_prompt,
    build_report_prompt,
)

__all__ = [
    "get_rag_retriever",
    "build_explanation_prompt",
    "build_rule_prompt",
    "build_report_prompt",
]
