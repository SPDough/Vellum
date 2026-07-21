"""
Agentic knowledge lookup as a LangGraph subgraph, with multi-turn memory.

Adaptive retrieval over the knowledge repository:

    contextualize ─► classify ─► retrieve ─┬─(simple)──────────► synthesize ─► END
    (standalone Q)                         └─(complex)─► grade ─┬─(ok|cap)──► synthesize ─► END
                                               ▲                └─(insufficient)─► rewrite ─┐
                                               └────────────────────── retrieve ◄───────────┘
                                                        (loop capped at max_iterations)

`contextualize` rewrites a follow-up (using recent conversation history) into a
self-contained question so retrieval works across turns. Simple/definitional
questions take the direct path; complex ones enter a retrieve → grade → rewrite
loop until the context is judged sufficient or the cap is hit. Every answer cites.

Memory (Phase 1): a shared in-process checkpointer (LangGraph MemorySaver) keyed
by `thread_id` (= conversation id) persists the conversation `messages` across
turns. Per-turn working fields are reset each turn so stale retrieval never leaks.
Phase 2 swaps the checkpointer for durable Postgres.

Authority note: this tool is assistive. It explains and cites domain knowledge;
it never overrides deterministic rules or control logic.
"""

from __future__ import annotations

import logging
import operator
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict

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


class ChatTurn(TypedDict, total=False):
    """One conversation message; assistant turns carry their citations."""

    role: Literal["user", "assistant"]
    content: str
    citations: List[Dict[str, Any]]
    created_at: str


class KnowledgeAgentState(TypedDict, total=False):
    """State threaded through the knowledge-lookup graph."""

    # Conversation history — accumulates across turns (append reducer, persisted).
    messages: Annotated[List[ChatTurn], operator.add]
    # Per-turn working fields — reset every turn by `contextualize`.
    query: str  # current (possibly rewritten) retrieval query
    original_query: str  # standalone question for this turn
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeAgent:
    """Runs adaptive, multi-turn knowledge lookup against the retrieval service."""

    def __init__(
        self,
        retrieval: KnowledgeRetrievalService,
        llm: Any = _UNSET,
        max_iterations: Optional[int] = None,
        top_k: Optional[int] = None,
        checkpointer: Any = _UNSET,
        max_history_turns: Optional[int] = None,
    ) -> None:
        self.retrieval = retrieval
        self.llm = _get_llm() if llm is _UNSET else llm
        self.max_iterations = max_iterations or settings.rag_agent_max_iterations
        self.top_k = top_k or settings.rag_agent_top_k
        self.max_history_turns = max_history_turns or settings.rag_agent_max_history_turns
        if checkpointer is _UNSET:
            from app.ai.langgraph_workflows.knowledge_checkpointer import (
                default_sync_checkpointer,
            )

            checkpointer = default_sync_checkpointer()
        self.checkpointer = checkpointer
        self._graph = self._build_graph()

    # --- helpers ------------------------------------------------------------

    def _recent_history(self, messages: List[ChatTurn], exclude_last: bool) -> List[ChatTurn]:
        """Last N messages (optionally excluding the just-added current user turn)."""
        history = messages[:-1] if exclude_last and messages else list(messages)
        return history[-self.max_history_turns :]

    @staticmethod
    def _history_text(history: List[ChatTurn]) -> str:
        return "\n".join(f"{m.get('role', '?')}: {m.get('content', '')}" for m in history)

    # --- graph nodes (return PARTIAL state updates) -------------------------

    async def _contextualize(self, state: KnowledgeAgentState) -> Dict[str, Any]:
        """Resolve a follow-up into a standalone question and reset per-turn fields.

        The current user turn is already appended to `messages` via the input
        reducer, so history is everything before it.
        """
        messages = state.get("messages", [])
        question = messages[-1]["content"] if messages else state.get("query", "")
        history = self._recent_history(messages, exclude_last=True)

        standalone = question
        if history and self.llm is not None:
            prompt = (
                "Given the conversation history, rewrite the user's latest message into a "
                "standalone question that can be understood on its own (resolve pronouns and "
                "references). If it is already standalone, return it unchanged. Return only "
                "the question.\n\n"
                f"History:\n{self._history_text(history)}\n\nLatest: {question}"
            )
            try:
                rewritten = _llm_text(await self.llm.ainvoke(prompt))
                if rewritten:
                    standalone = rewritten
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Contextualize failed (%s); using raw question", e)

        # Reset all per-turn working fields (checkpointer restored the prior turn's).
        return {
            "query": standalone,
            "original_query": standalone,
            "route": "",
            "candidates": [],
            "iterations": 0,
            "sufficient": False,
            "grade_reason": "",
            "answer": "",
            "trace": [{"step": "contextualize", "standalone": standalone, "had_history": bool(history)}],
        }

    async def _route(self, state: KnowledgeAgentState) -> Dict[str, Any]:
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
            lowered = query.lower()
            if len(query.split()) > 18 or any(
                w in lowered for w in (" and ", " versus", " vs ", "compare", "relationship between")
            ):
                route = "complex"
        return {"route": route, "trace": state.get("trace", []) + [{"step": "route", "route": route}]}

    async def _retrieve(self, state: KnowledgeAgentState) -> Dict[str, Any]:
        candidates = await self.retrieval.search(
            state["query"],
            top_k=self.top_k,
            filters=state.get("filters"),
            min_trust=state.get("min_trust"),
        )
        trace = state.get("trace", []) + [
            {
                "step": "retrieve",
                "query": state["query"],
                "iteration": state.get("iterations", 0),
                "chunk_ids": [str(c.chunk_id) for c in candidates],
            }
        ]
        return {"candidates": candidates, "trace": trace}

    async def _grade(self, state: KnowledgeAgentState) -> Dict[str, Any]:
        """Judge whether retrieved context can answer the original question."""
        candidates = state.get("candidates", [])
        if not candidates:
            sufficient, reason = False, "no candidates retrieved"
        elif self.llm is None:
            sufficient, reason = True, "no LLM; accepting retrieved context"
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
                sufficient, reason = verdict.upper().startswith("YES"), verdict
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Grading failed (%s); accepting context", e)
                sufficient, reason = True, f"grading error: {e}"
        trace = state.get("trace", []) + [
            {"step": "grade", "sufficient": sufficient, "reason": reason[:200]}
        ]
        return {"sufficient": sufficient, "grade_reason": reason, "trace": trace}

    async def _rewrite(self, state: KnowledgeAgentState) -> Dict[str, Any]:
        iterations = state.get("iterations", 0) + 1
        query = state["query"]
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
                    query = rewritten
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Rewrite failed (%s); reusing previous query", e)
        trace = state.get("trace", []) + [
            {"step": "rewrite", "iteration": iterations, "new_query": query}
        ]
        return {"query": query, "iterations": iterations, "trace": trace}

    async def _answer(self, state: KnowledgeAgentState) -> Dict[str, Any]:
        candidates = state.get("candidates", [])
        if not candidates:
            answer = (
                "I could not find supporting material in the knowledge repository for this question."
            )
        elif self.llm is None:
            answer = candidates[0].content.strip()
        else:
            context = "\n\n".join(
                f"[{i+1}] ({c.document_title or c.filename}"
                f"{' > ' + c.section if c.section else ''}) {c.content[:700]}"
                for i, c in enumerate(candidates)
            )
            history = self._recent_history(state.get("messages", []), exclude_last=True)
            history_block = (
                f"Conversation so far (for context):\n{self._history_text(history)}\n\n"
                if history
                else ""
            )
            prompt = (
                "Answer the question using only the numbered context below. Cite sources "
                "inline as [n]. If the context is insufficient, say so plainly. Be concise "
                "and precise for a banking-operations audience.\n\n"
                f"{history_block}Question: {state['original_query']}\n\nContext:\n{context}"
            )
            try:
                answer = _llm_text(await self.llm.ainvoke(prompt))
            except Exception as e:  # pragma: no cover - network dependent
                logger.warning("Answer synthesis failed (%s); returning top passage", e)
                answer = candidates[0].content.strip()

        citations = [c.citation() for c in candidates]
        assistant_turn: ChatTurn = {
            "role": "assistant",
            "content": answer,
            "citations": citations,
            "created_at": _now(),
        }
        trace = state.get("trace", []) + [{"step": "answer", "chars": len(answer)}]
        # Clear candidates from the final persisted state: they are heavy and the
        # citations we need are carried on the assistant message (design §4.3).
        return {"answer": answer, "messages": [assistant_turn], "candidates": [], "trace": trace}

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
        graph.add_node("contextualize", self._contextualize)
        graph.add_node("classify", self._route)
        graph.add_node("retrieve", self._retrieve)
        graph.add_node("grade", self._grade)
        graph.add_node("rewrite", self._rewrite)
        graph.add_node("synthesize", self._answer)

        graph.set_entry_point("contextualize")
        graph.add_edge("contextualize", "classify")
        graph.add_edge("classify", "retrieve")
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
        return graph.compile(checkpointer=self.checkpointer)

    # --- public API ---------------------------------------------------------

    async def run(
        self,
        query: str,
        *,
        thread_id: Optional[str] = None,
        filters: Optional[Dict[str, str]] = None,
        min_trust: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run one turn and return answer, citations, route, and conversation id.

        Pass `thread_id` (conversation id) to continue a conversation; omit it for
        a one-off question. With memory enabled, an omitted thread_id gets an
        ephemeral id so the turn is isolated.
        """
        user_turn: ChatTurn = {
            "role": "user",
            "content": query,
            "citations": [],
            "created_at": _now(),
        }
        # Input carries the new user turn (appended via reducer) + per-turn inputs.
        turn_input: KnowledgeAgentState = {
            "messages": [user_turn],
            "query": query,
            "original_query": query,
            "filters": filters,
            "min_trust": min_trust,
        }

        config = None
        conversation_id = thread_id
        if self.checkpointer is not None:
            conversation_id = thread_id or uuid.uuid4().hex
            config = {"configurable": {"thread_id": conversation_id}}

        final: KnowledgeAgentState = await self._graph.ainvoke(turn_input, config=config)
        # Citations come from the assistant message (candidates are cleared from
        # persisted state in `_answer`).
        messages = final.get("messages", [])
        citations = messages[-1].get("citations", []) if messages else []
        result = {
            "query": query,
            "conversation_id": conversation_id,
            "answer": final.get("answer", ""),
            "route": final.get("route", "simple"),
            "iterations": final.get("iterations", 0),
            "citations": citations,
            "trace": final.get("trace", []),
        }
        logger.info(
            "knowledge_lookup: conv=%s route=%s iterations=%s citations=%s query=%r",
            conversation_id,
            result["route"],
            result["iterations"],
            len(result["citations"]),
            query,
        )
        return result
