"""
Agentic knowledge lookup as a LangGraph subgraph.

Adaptive retrieval over the knowledge repository:

    route ─┬─(simple)──────────────► retrieve ─► answer
           └─(complex)─► retrieve ─► grade ─┬─(sufficient)─► answer
                             ▲               └─(insufficient)─► rewrite ─┐
                             └───────────────────────────────────────────┘
                                       (loop capped at max_iterations)

Simple, definitional queries take the direct path; complex queries enter a
retrieve → grade → rewrite loop until the retrieved context is judged sufficient
or the iteration cap is hit. Every answer carries citations.

Authority note: this tool is assistive. It explains and cites domain knowledge;
it never overrides deterministic rules or control logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

from app.core.config import get_settings
from app.services.knowledge_retrieval_service import (
    KnowledgeRetrievalService,
    RetrievalCandidate,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Sentinel distinguishing "no llm argument given" (build the default) from an
# explicit llm=None (run in degraded, no-LLM mode).
_UNSET = object()


class KnowledgeAgentState(TypedDict, total=False):
    """State threaded through the knowledge-lookup graph."""

    query: str  # current (possibly rewritten) query
    original_query: str
    route: str  # "simple" | "complex"
    filters: Optional[Dict[str, str]]
    min_trust: Optional[str]
    candidates: List[RetrievalCandidate]
    iterations: int
    sufficient: bool
    grade_reason: str
    answer: str
    trace: List[Dict[str, Any]]  # per-step record for logging/debugging


def _get_llm():
    """Return a chat model for routing/grading/synthesis, or None if unconfigured."""
    model = settings.rag_agent_model
    try:
        if model.startswith("claude") and settings.anthropic_api_key:
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=model, api_key=settings.anthropic_api_key, temperature=0.0
            )
        if settings.openai_api_key:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(model=model, api_key=settings.openai_api_key, temperature=0.0)
    except ImportError:
        pass
    return None


def _llm_text(response: Any) -> str:
    return (getattr(response, "content", "") or "").strip()


class KnowledgeAgent:
    """Runs adaptive knowledge lookup against the retrieval service."""

    def __init__(
        self,
        retrieval: KnowledgeRetrievalService,
        llm: Any = _UNSET,
        max_iterations: Optional[int] = None,
        top_k: Optional[int] = None,
    ) -> None:
        self.retrieval = retrieval
        self.llm = _get_llm() if llm is _UNSET else llm
        self.max_iterations = max_iterations or settings.rag_agent_max_iterations
        self.top_k = top_k or settings.rag_agent_top_k
        self._graph = self._build_graph()

    # --- graph nodes --------------------------------------------------------

    async def _route(self, state: KnowledgeAgentState) -> KnowledgeAgentState:
        """Classify the query as simple (direct) or complex (agentic loop)."""
        query = state["query"]
        route = "simple"
        if self.llm is not None:
            prompt = (
                "Classify this knowledge-base question as SIMPLE or COMPLEX.\n"
                "SIMPLE: a single definitional or factual lookup.\n"
                "COMPLEX: needs multiple facts, comparison, or multi-step reasoning.\n"
                "Answer with exactly one word: SIMPLE or COMPLEX.\n\n"
                f"Question: {query}"
            )
            try:
                verdict = _llm_text(await self.llm.ainvoke(prompt)).upper()
                route = "complex" if "COMPLEX" in verdict else "simple"
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Route classification failed (%s); defaulting to simple", e)
        else:
            # Heuristic fallback: length / conjunctions hint at complexity
            lowered = query.lower()
            if len(query.split()) > 18 or any(
                w in lowered for w in (" and ", " versus", " vs ", "compare", "relationship between")
            ):
                route = "complex"
        state["route"] = route
        state.setdefault("trace", []).append({"step": "route", "route": route})
        return state

    async def _retrieve(self, state: KnowledgeAgentState) -> KnowledgeAgentState:
        candidates = await self.retrieval.search(
            state["query"],
            top_k=self.top_k,
            filters=state.get("filters"),
            min_trust=state.get("min_trust"),
        )
        state["candidates"] = candidates
        state.setdefault("trace", []).append(
            {
                "step": "retrieve",
                "query": state["query"],
                "iteration": state.get("iterations", 0),
                "chunk_ids": [str(c.chunk_id) for c in candidates],
            }
        )
        return state

    async def _grade(self, state: KnowledgeAgentState) -> KnowledgeAgentState:
        """Judge whether retrieved context can answer the original question."""
        candidates = state.get("candidates", [])
        if not candidates:
            state["sufficient"] = False
            state["grade_reason"] = "no candidates retrieved"
        elif self.llm is None:
            state["sufficient"] = True
            state["grade_reason"] = "no LLM; accepting retrieved context"
        else:
            context = "\n\n".join(
                f"[{i+1}] {c.content[:500]}" for i, c in enumerate(candidates[:5])
            )
            prompt = (
                "You are grading whether the retrieved context is sufficient to answer "
                "the question. Reply with 'YES: <reason>' or 'NO: <reason>'.\n\n"
                f"Question: {state['original_query']}\n\nContext:\n{context}"
            )
            try:
                verdict = _llm_text(await self.llm.ainvoke(prompt))
                state["sufficient"] = verdict.upper().startswith("YES")
                state["grade_reason"] = verdict
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Grading failed (%s); accepting context", e)
                state["sufficient"] = True
                state["grade_reason"] = f"grading error: {e}"
        state.setdefault("trace", []).append(
            {
                "step": "grade",
                "sufficient": state["sufficient"],
                "reason": state["grade_reason"][:200],
            }
        )
        return state

    async def _rewrite(self, state: KnowledgeAgentState) -> KnowledgeAgentState:
        state["iterations"] = state.get("iterations", 0) + 1
        if self.llm is not None:
            prompt = (
                "The previous search did not retrieve enough to answer the question. "
                "Rewrite it as a more effective search query (keywords and key concepts). "
                "Return only the rewritten query.\n\n"
                f"Original question: {state['original_query']}\n"
                f"Previous query: {state['query']}"
            )
            try:
                rewritten = _llm_text(await self.llm.ainvoke(prompt))
                if rewritten:
                    state["query"] = rewritten
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Rewrite failed (%s); reusing previous query", e)
        state.setdefault("trace", []).append(
            {"step": "rewrite", "iteration": state["iterations"], "new_query": state["query"]}
        )
        return state

    async def _answer(self, state: KnowledgeAgentState) -> KnowledgeAgentState:
        candidates = state.get("candidates", [])
        if not candidates:
            state["answer"] = (
                "I could not find supporting material in the knowledge repository for this question."
            )
            return state
        if self.llm is None:
            # Degraded mode: return the top passage verbatim
            state["answer"] = candidates[0].content.strip()
        else:
            context = "\n\n".join(
                f"[{i+1}] ({c.document_title or c.filename}"
                f"{' > ' + c.section if c.section else ''}) {c.content[:700]}"
                for i, c in enumerate(candidates)
            )
            prompt = (
                "Answer the question using only the numbered context below. Cite sources "
                "inline as [n]. If the context is insufficient, say so plainly. Be concise "
                "and precise for a banking-operations audience.\n\n"
                f"Question: {state['original_query']}\n\nContext:\n{context}"
            )
            try:
                state["answer"] = _llm_text(await self.llm.ainvoke(prompt))
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Answer synthesis failed (%s); returning top passage", e)
                state["answer"] = candidates[0].content.strip()
        state.setdefault("trace", []).append({"step": "answer", "chars": len(state["answer"])})
        return state

    # --- graph wiring -------------------------------------------------------

    def _grade_edge(self, state: KnowledgeAgentState) -> str:
        if state.get("sufficient"):
            return "answer"
        if state.get("iterations", 0) >= self.max_iterations:
            return "answer"
        return "rewrite"

    def _build_graph(self):
        from langgraph.graph import END, StateGraph

        # Node names must not collide with state keys (e.g. "route", "answer").
        graph = StateGraph(KnowledgeAgentState)
        graph.add_node("classify", self._route)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("grade", self._grade)
        graph.add_node("rewrite", self._rewrite)
        graph.add_node("synthesize", self._answer)

        graph.set_entry_point("classify")
        graph.add_edge("classify", "retrieve")
        # After retrieve: simple route answers directly; complex route grades.
        graph.add_conditional_edges(
            "retrieve",
            lambda s: "synthesize" if s.get("route") == "simple" else "grade",
            {"synthesize": "synthesize", "grade": "grade"},
        )
        graph.add_conditional_edges(
            "grade", self._grade_edge, {"answer": "synthesize", "rewrite": "rewrite"}
        )
        graph.add_edge("rewrite", "retrieve")
        graph.add_edge("synthesize", END)
        return graph.compile()

    # --- public API ---------------------------------------------------------

    async def run(
        self,
        query: str,
        *,
        filters: Optional[Dict[str, str]] = None,
        min_trust: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run the graph and return answer, citations, route, and trace."""
        initial: KnowledgeAgentState = {
            "query": query,
            "original_query": query,
            "filters": filters,
            "min_trust": min_trust,
            "iterations": 0,
            "trace": [],
        }
        final: KnowledgeAgentState = await self._graph.ainvoke(initial)
        candidates = final.get("candidates", [])
        result = {
            "query": query,
            "answer": final.get("answer", ""),
            "route": final.get("route", "simple"),
            "iterations": final.get("iterations", 0),
            "citations": [c.citation() for c in candidates],
            "trace": final.get("trace", []),
        }
        logger.info(
            "knowledge_lookup: route=%s iterations=%s citations=%s query=%r",
            result["route"],
            result["iterations"],
            len(result["citations"]),
            query,
        )
        return result
