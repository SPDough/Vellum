"""
Phase 3 knowledge-agent tests: routing, grade-driven looping, iteration cap,
citation assembly, and no-LLM degradation. Uses fake LLM + fake retrieval so no
network or database is required.
"""

import asyncio
import uuid
from typing import List, Optional

import pytest

from app.ai.langgraph_workflows.knowledge_agent import KnowledgeAgent
from app.services.knowledge_retrieval_service import RetrievalCandidate


def _candidate(text: str = "content") -> RetrievalCandidate:
    return RetrievalCandidate(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        content=text,
        chunk_index=0,
        document_title="Equity Modeling",
        filename="book.pdf",
        section="Mean-Variance",
        trust_level="internal_guidance",
        fused_score=0.5,
    )


class FakeRetrieval:
    """Records queries; returns a fixed candidate set (or empty)."""

    def __init__(self, candidates: Optional[List[RetrievalCandidate]] = None):
        self._candidates = candidates if candidates is not None else [_candidate()]
        self.queries: List[str] = []

    async def search(self, query, *, top_k=6, filters=None, min_trust=None):
        self.queries.append(query)
        return list(self._candidates)


class FakeLLM:
    """Async chat stub returning scripted responses by prompt keyword."""

    def __init__(
        self,
        route="SIMPLE",
        grade_sequence=None,
        rewrite="rewritten query",
        standalone="STANDALONE Q",
    ):
        self.route = route
        self.grade_sequence = list(grade_sequence or ["YES: sufficient"])
        self.rewrite = rewrite
        self.standalone = standalone
        self.calls: List[str] = []

    async def ainvoke(self, prompt: str):
        self.calls.append(prompt)

        class _Resp:
            def __init__(self, content):
                self.content = content

        if "standalone question" in prompt:  # contextualize (condense) step
            return _Resp(self.standalone)
        if "Classify" in prompt:
            return _Resp(self.route)
        if "grading" in prompt or "sufficient to answer" in prompt:
            verdict = self.grade_sequence.pop(0) if self.grade_sequence else "YES: ok"
            return _Resp(verdict)
        if "Rewrite" in prompt:
            return _Resp(self.rewrite)
        # answer synthesis
        return _Resp("Synthesized answer [1].")


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def test_simple_route_skips_grade_and_rewrite():
    retrieval = FakeRetrieval()
    llm = FakeLLM(route="SIMPLE")
    agent = KnowledgeAgent(retrieval, llm=llm)
    result = run(agent.run("What is beta?"))
    assert result["route"] == "simple"
    assert result["iterations"] == 0
    steps = [t["step"] for t in result["trace"]]
    assert "grade" not in steps
    assert "rewrite" not in steps
    assert result["answer"] == "Synthesized answer [1]."


def test_complex_route_grades_then_answers_when_sufficient():
    retrieval = FakeRetrieval()
    llm = FakeLLM(route="COMPLEX", grade_sequence=["YES: enough"])
    agent = KnowledgeAgent(retrieval, llm=llm)
    result = run(agent.run("Compare CAPM and APT assumptions and implications"))
    assert result["route"] == "complex"
    steps = [t["step"] for t in result["trace"]]
    assert "grade" in steps
    assert "rewrite" not in steps
    assert result["iterations"] == 0


# ---------------------------------------------------------------------------
# Grade-driven looping and the iteration cap
# ---------------------------------------------------------------------------


def test_insufficient_grade_triggers_rewrite_then_answers():
    retrieval = FakeRetrieval()
    # first grade fails, second passes
    llm = FakeLLM(route="COMPLEX", grade_sequence=["NO: missing", "YES: better"])
    agent = KnowledgeAgent(retrieval, llm=llm, max_iterations=3)
    result = run(agent.run("complex multi-part question"))
    assert result["iterations"] == 1
    assert "rewritten query" in retrieval.queries  # rewrite fed back into retrieve
    steps = [t["step"] for t in result["trace"]]
    assert steps.count("retrieve") == 2


def test_iteration_cap_forces_answer():
    retrieval = FakeRetrieval()
    # always insufficient — must stop at max_iterations, not loop forever
    llm = FakeLLM(route="COMPLEX", grade_sequence=["NO"] * 10)
    agent = KnowledgeAgent(retrieval, llm=llm, max_iterations=2)
    result = run(agent.run("unanswerable complex question"))
    assert result["iterations"] == 2
    assert result["answer"]  # produced an answer despite never grading sufficient
    assert [t["step"] for t in result["trace"]].count("rewrite") == 2


# ---------------------------------------------------------------------------
# Citations
# ---------------------------------------------------------------------------


def test_citations_assembled_from_candidates():
    retrieval = FakeRetrieval([_candidate("chunk a"), _candidate("chunk b")])
    agent = KnowledgeAgent(retrieval, llm=FakeLLM(route="SIMPLE"))
    result = run(agent.run("What is the efficient frontier?"))
    assert len(result["citations"]) == 2
    assert result["citations"][0]["document_title"] == "Equity Modeling"
    assert result["citations"][0]["section"] == "Mean-Variance"


def test_no_candidates_yields_honest_answer():
    agent = KnowledgeAgent(FakeRetrieval([]), llm=FakeLLM(route="SIMPLE"))
    result = run(agent.run("something not in the corpus"))
    assert result["citations"] == []
    assert "could not find" in result["answer"].lower()


# ---------------------------------------------------------------------------
# No-LLM degradation
# ---------------------------------------------------------------------------


def test_without_llm_returns_top_passage_and_simple_route():
    retrieval = FakeRetrieval([_candidate("the top passage text")])
    agent = KnowledgeAgent(retrieval, llm=None)
    result = run(agent.run("short query"))
    assert result["route"] == "simple"
    assert result["answer"] == "the top passage text"


def test_without_llm_long_query_routes_complex_by_heuristic():
    retrieval = FakeRetrieval()
    agent = KnowledgeAgent(retrieval, llm=None)
    result = run(agent.run("compare the relationship between factor models and principal component analysis in equity"))
    assert result["route"] == "complex"


# ---------------------------------------------------------------------------
# Multi-turn memory (Phase 1)
# ---------------------------------------------------------------------------


def _fresh_memory_agent(retrieval, llm):
    """Agent with an isolated in-process checkpointer (not the shared singleton)."""
    from langgraph.checkpoint.memory import MemorySaver

    return KnowledgeAgent(retrieval, llm=llm, checkpointer=MemorySaver())


def test_conversation_id_minted_and_stable_across_turns():
    retrieval = FakeRetrieval()
    agent = _fresh_memory_agent(retrieval, FakeLLM(route="SIMPLE"))
    r1 = run(agent.run("What is a mezzanine bond?", thread_id="conv-1"))
    r2 = run(agent.run("How does it accrue interest?", thread_id="conv-1"))
    assert r1["conversation_id"] == "conv-1"
    assert r2["conversation_id"] == "conv-1"


def test_memory_persists_and_followup_is_contextualized():
    retrieval = FakeRetrieval()
    agent = _fresh_memory_agent(retrieval, FakeLLM(route="SIMPLE", standalone="STANDALONE Q"))
    run(agent.run("What is a mezzanine bond?", thread_id="c"))
    run(agent.run("How does it accrue interest?", thread_id="c"))
    # Turn 1 had no history -> retrieval used the raw question.
    assert retrieval.queries[0] == "What is a mezzanine bond?"
    # Turn 2 saw persisted history -> contextualize rewrote the follow-up.
    assert retrieval.queries[-1] == "STANDALONE Q"


def test_no_thread_id_turns_are_isolated():
    retrieval = FakeRetrieval()
    agent = _fresh_memory_agent(retrieval, FakeLLM(route="SIMPLE", standalone="STANDALONE Q"))
    r1 = run(agent.run("What is a mezzanine bond?"))
    r2 = run(agent.run("How does it accrue interest?"))
    # No shared thread -> turn 2 has no history -> raw query used (not contextualized).
    assert retrieval.queries[-1] == "How does it accrue interest?"
    assert r1["conversation_id"] != r2["conversation_id"]


def test_working_state_resets_between_turns():
    retrieval = FakeRetrieval()
    # Turn 1 is complex and never satisfied -> loops to the iteration cap.
    llm = FakeLLM(route="COMPLEX", grade_sequence=["NO", "NO", "NO", "NO"])
    agent = _fresh_memory_agent(retrieval, llm)
    r1 = run(agent.run("a complex first question", thread_id="c"))
    assert r1["iterations"] == agent.max_iterations  # looped
    # Turn 2 is simple; iterations must reset, not carry over from turn 1.
    llm.route = "SIMPLE"
    r2 = run(agent.run("a simple follow-up", thread_id="c"))
    assert r2["iterations"] == 0


def test_single_shot_when_memory_disabled():
    retrieval = FakeRetrieval()
    agent = KnowledgeAgent(retrieval, llm=FakeLLM(route="SIMPLE"), checkpointer=None)
    result = run(agent.run("What is beta?"))
    assert result["conversation_id"] is None
    assert result["answer"] == "Synthesized answer [1]."


def test_assistant_turn_persists_citations():
    retrieval = FakeRetrieval([_candidate("chunk a")])
    saver_agent = _fresh_memory_agent(retrieval, FakeLLM(route="SIMPLE"))
    run(saver_agent.run("q1", thread_id="c"))
    # Inspect persisted state: assistant turn should carry citations.
    state = saver_agent._graph.get_state({"configurable": {"thread_id": "c"}})
    messages = state.values["messages"]
    assistant = [m for m in messages if m["role"] == "assistant"][-1]
    assert len(assistant["citations"]) == 1
    assert assistant["citations"][0]["document_title"] == "Equity Modeling"
