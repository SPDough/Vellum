"""
Knowledge-repository evaluation harness.

Runs the knowledge agent over a golden Q&A set and scores each answer with two
RAGAS-style LLM-judge metrics plus a deterministic keyword check:

  - faithfulness: is the answer grounded in the retrieved citations (no fabrication)?
  - answer_relevance: does the answer actually address the question?
  - keyword_coverage: fraction of expected substrings present (deterministic sanity)

Designed to run against a populated knowledge database. Use as a pytest
integration test (skipped without DB+data) or standalone:

    python -m app.ai.eval.knowledge_eval
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.langgraph_workflows.knowledge_agent import KnowledgeAgent, _get_llm
from app.services.knowledge_retrieval_service import KnowledgeRetrievalService

logger = logging.getLogger(__name__)

GOLDEN_QA_PATH = Path(__file__).with_name("knowledge_golden_qa.json")


def load_golden_qa(path: Path = GOLDEN_QA_PATH) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]


def keyword_coverage(answer: str, must_include: List[str]) -> float:
    if not must_include:
        return 1.0
    lowered = answer.lower()
    hits = sum(1 for kw in must_include if kw.lower() in lowered)
    return hits / len(must_include)


async def _judge(llm, prompt: str) -> float:
    """Ask the judge for a 1-5 score; normalize to 0-1. Returns 0.0 on failure."""
    try:
        resp = await llm.ainvoke(prompt)
        text = (getattr(resp, "content", "") or "").strip()
        digits = [c for c in text if c in "12345"]
        if not digits:
            return 0.0
        return (int(digits[0]) - 1) / 4.0
    except Exception as e:  # pragma: no cover - network dependent
        logger.warning("Judge scoring failed: %s", e)
        return 0.0


async def score_answer(
    judge_llm, question: str, answer: str, contexts: List[str]
) -> Dict[str, float]:
    """LLM-judge faithfulness and answer-relevance, each normalized to 0-1."""
    context_block = "\n\n".join(f"[{i+1}] {c[:600]}" for i, c in enumerate(contexts)) or "(none)"
    faithfulness = await _judge(
        judge_llm,
        "Rate 1-5 how well the ANSWER is supported by the CONTEXT only "
        "(5 = fully grounded, 1 = fabricated/unsupported). Reply with a single digit.\n\n"
        f"CONTEXT:\n{context_block}\n\nANSWER:\n{answer}",
    )
    relevance = await _judge(
        judge_llm,
        "Rate 1-5 how directly the ANSWER addresses the QUESTION "
        "(5 = fully answers, 1 = off-topic). Reply with a single digit.\n\n"
        f"QUESTION:\n{question}\n\nANSWER:\n{answer}",
    )
    return {"faithfulness": faithfulness, "answer_relevance": relevance}


async def run_eval(
    db: Session,
    questions: Optional[List[Dict[str, Any]]] = None,
    *,
    judge_llm=None,
) -> Dict[str, Any]:
    """Run the agent over the golden set and return per-item and aggregate scores."""
    questions = questions if questions is not None else load_golden_qa()
    retrieval = KnowledgeRetrievalService(db)
    agent = KnowledgeAgent(retrieval)
    judge_llm = judge_llm if judge_llm is not None else _get_llm()

    per_item: List[Dict[str, Any]] = []
    for q in questions:
        result = await agent.run(q["query"])
        contexts = [c.get("document_title", "") for c in result["citations"]]
        # Pull chunk text for faithfulness scoring via a fresh retrieval read
        candidates = await retrieval.search(q["query"], top_k=agent.top_k)
        context_texts = [c.content for c in candidates]

        coverage = keyword_coverage(result["answer"], q.get("must_include", []))
        scores = (
            await score_answer(judge_llm, q["query"], result["answer"], context_texts)
            if judge_llm is not None
            else {"faithfulness": 0.0, "answer_relevance": 0.0}
        )
        per_item.append(
            {
                "id": q["id"],
                "query": q["query"],
                "route": result["route"],
                "iterations": result["iterations"],
                "num_citations": len(result["citations"]),
                "keyword_coverage": coverage,
                **scores,
            }
        )

    def _mean(key: str) -> float:
        return round(sum(item[key] for item in per_item) / len(per_item), 3) if per_item else 0.0

    aggregate = {
        "n": len(per_item),
        "keyword_coverage": _mean("keyword_coverage"),
        "faithfulness": _mean("faithfulness"),
        "answer_relevance": _mean("answer_relevance"),
        "answered_with_citations": round(
            sum(1 for i in per_item if i["num_citations"] > 0) / len(per_item), 3
        )
        if per_item
        else 0.0,
    }
    return {"aggregate": aggregate, "per_item": per_item}


def _main() -> None:
    import os

    from dotenv import load_dotenv
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    load_dotenv()
    db_url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://")
    engine = create_engine(db_url)
    db = sessionmaker(bind=engine)()
    try:
        report = asyncio.run(run_eval(db))
    finally:
        db.close()
    print(json.dumps(report["aggregate"], indent=2))
    for item in report["per_item"]:
        print(
            f"  {item['id']} route={item['route']} iters={item['iterations']} "
            f"cov={item['keyword_coverage']:.2f} faith={item['faithfulness']:.2f} "
            f"rel={item['answer_relevance']:.2f} :: {item['query'][:60]}"
        )


if __name__ == "__main__":
    _main()
