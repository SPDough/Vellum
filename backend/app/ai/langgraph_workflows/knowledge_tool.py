"""
Tool surface for the agentic knowledge lookup.

Exposes the KnowledgeAgent both as a plain async callable (for services and the
API) and as a LangChain StructuredTool (for LLM agents and other LangGraph
workflows to call as `knowledge_lookup`).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.ai.langgraph_workflows.knowledge_agent import KnowledgeAgent
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService

logger = logging.getLogger(__name__)

TOOL_NAME = "knowledge_lookup"
TOOL_DESCRIPTION = (
    "Look up authoritative domain knowledge (security mechanics, accounting "
    "treatments, market conventions, custody operations) from the Vellum knowledge "
    "repository. Returns a cited answer. Use for 'how does X work' / 'what is the "
    "treatment for Y' questions. Advisory only: it does not decide rule outcomes."
)


async def knowledge_lookup(
    query: str,
    db: Session,
    *,
    filters: Optional[Dict[str, str]] = None,
    min_trust: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the knowledge agent against the repository and return answer + citations."""
    retrieval = KnowledgeRetrievalService(db)
    agent = KnowledgeAgent(retrieval)
    return await agent.run(query, filters=filters, min_trust=min_trust)


def build_knowledge_tool(db: Session):
    """
    Build a LangChain StructuredTool bound to a DB session so LLM agents and
    LangGraph workflows can invoke knowledge lookup as `knowledge_lookup`.
    """
    from langchain_core.tools import StructuredTool

    async def _run(query: str, min_trust: Optional[str] = None) -> str:
        result = await knowledge_lookup(query, db, min_trust=min_trust)
        answer = result["answer"]
        cites = result["citations"]
        if cites:
            refs = "; ".join(
                f"[{i+1}] {c['document_title']}"
                f"{' > ' + c['section'] if c.get('section') else ''}"
                for i, c in enumerate(cites)
            )
            return f"{answer}\n\nSources: {refs}"
        return answer

    return StructuredTool.from_function(
        coroutine=_run,
        name=TOOL_NAME,
        description=TOOL_DESCRIPTION,
    )
