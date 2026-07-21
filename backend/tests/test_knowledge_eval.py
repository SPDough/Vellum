"""Unit tests for the eval harness scoring (no DB/network)."""

import asyncio

from app.ai.eval.knowledge_eval import keyword_coverage, load_golden_qa, score_answer


def test_golden_set_loads_and_is_well_formed():
    questions = load_golden_qa()
    assert len(questions) >= 20
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "golden question ids must be unique"
    for q in questions:
        assert q["query"]
        assert isinstance(q.get("must_include", []), list)


def test_keyword_coverage_full_partial_none():
    assert keyword_coverage("risk and return tradeoff", ["risk", "return"]) == 1.0
    assert keyword_coverage("only risk here", ["risk", "return"]) == 0.5
    assert keyword_coverage("nothing relevant", ["risk", "return"]) == 0.0
    assert keyword_coverage("anything", []) == 1.0


def test_score_answer_normalizes_judge_digits():
    class FakeJudge:
        def __init__(self, digit):
            self.digit = digit

        async def ainvoke(self, prompt):
            class R:
                content = self.digit

            return R()

    # judge returns "5" -> normalized 1.0; "1" -> 0.0; "3" -> 0.5
    top = asyncio.run(score_answer(FakeJudge("5"), "q", "a", ["ctx"]))
    assert top["faithfulness"] == 1.0 and top["answer_relevance"] == 1.0
    low = asyncio.run(score_answer(FakeJudge("1"), "q", "a", ["ctx"]))
    assert low["faithfulness"] == 0.0
    mid = asyncio.run(score_answer(FakeJudge("3"), "q", "a", ["ctx"]))
    assert mid["faithfulness"] == 0.5


def test_score_answer_handles_nondigit_judge_output():
    class BadJudge:
        async def ainvoke(self, prompt):
            class R:
                content = "I cannot rate this"

            return R()

    out = asyncio.run(score_answer(BadJudge(), "q", "a", ["ctx"]))
    assert out["faithfulness"] == 0.0
    assert out["answer_relevance"] == 0.0
