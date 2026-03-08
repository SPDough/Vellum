"""
NAV RAG findings API: explanation, rule-basis, and client-communication.

Uses app.rag (retrieve + rag_service) and nav_rag_* tables.
Pass finding as JSON body; optional ?generate=true to call Claude for generated text.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class FindingEvidence(BaseModel):
    source: str
    finding: str


class FindingPayload(BaseModel):
    """Minimal finding payload for RAG prompt builders."""

    finding_id: str
    finding_type: str
    severity: str
    description: Optional[str] = None
    security_name: str
    ticker: str
    cusip: str
    shares_held: int
    dividend_per_share: float
    total_impact: float
    ex_date: str
    record_date: str
    pay_date: str
    detection_date: str
    custodian: str
    nav_per_unit_incorrect: float
    nav_per_unit_correct: float
    units_outstanding: int
    evidence: List[FindingEvidence] = Field(default_factory=list)
    fund_name: Optional[str] = None


def _finding_to_dict(p: FindingPayload) -> dict:
    return {
        "finding_id": p.finding_id,
        "finding_type": p.finding_type,
        "severity": p.severity,
        "description": p.description or "",
        "security_name": p.security_name,
        "ticker": p.ticker,
        "cusip": p.cusip,
        "shares_held": p.shares_held,
        "dividend_per_share": p.dividend_per_share,
        "total_impact": p.total_impact,
        "ex_date": p.ex_date,
        "record_date": p.record_date,
        "pay_date": p.pay_date,
        "detection_date": p.detection_date,
        "custodian": p.custodian,
        "nav_per_unit_incorrect": p.nav_per_unit_incorrect,
        "nav_per_unit_correct": p.nav_per_unit_correct,
        "units_outstanding": p.units_outstanding,
        "evidence": [{"source": e.source, "finding": e.finding} for e in p.evidence],
        "fund_name": p.fund_name or "the Fund",
    }


def _get_retriever():
    """Build RagRetriever (uses its own psycopg2 connection from config)."""
    from app.rag.rag_service import get_rag_retriever
    return get_rag_retriever()


@router.post("/findings/explanation")
async def get_explanation(
    finding: FindingPayload,
    generate: bool = False,
) -> Dict[str, Any]:
    """
    RAG-backed explanation for a finding (Screen 3 / fund ops director).
    Returns prompt + citations; if generate=true, also calls Claude and returns explanation.
    """
    try:
        retriever = _get_retriever()
        finding_dict = _finding_to_dict(finding)
        retrieval = retriever.retrieve_for_finding(
            finding_type=finding.finding_type,
            mart_names=[e.source for e in finding.evidence] if finding.evidence else None,
            top_k=8,
            purpose="explain",
        )
        from app.rag.rag_service import build_explanation_prompt
        prompt = build_explanation_prompt(finding_dict, retrieval)
        out = {"prompt": prompt, "citations": retrieval.to_citations()}
        if generate:
            out["explanation"] = _call_claude(prompt, max_tokens=1024)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/findings/rule-basis")
async def get_rule_basis(
    finding: FindingPayload,
    generate: bool = False,
) -> Dict[str, Any]:
    """
    RAG-backed rule justification for the validation engine audit trail.
    """
    try:
        retriever = _get_retriever()
        finding_dict = _finding_to_dict(finding)
        retrieval = retriever.retrieve_for_finding(
            finding_type=finding.finding_type,
            mart_names=[e.source for e in finding.evidence] if finding.evidence else None,
            top_k=8,
            purpose="rule",
        )
        from app.rag.rag_service import build_rule_prompt
        prompt = build_rule_prompt(finding_dict, retrieval)
        out = {"prompt": prompt, "citations": retrieval.to_citations()}
        if generate:
            out["rule_basis"] = _call_claude(prompt, max_tokens=512)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/findings/client-communication")
async def get_client_communication(
    finding: FindingPayload,
    generate: bool = False,
) -> Dict[str, Any]:
    """
    RAG-backed client-facing communication (investor letter).
    """
    try:
        retriever = _get_retriever()
        finding_dict = _finding_to_dict(finding)
        retrieval = retriever.retrieve_for_finding(
            finding_type=finding.finding_type,
            mart_names=[e.source for e in finding.evidence] if finding.evidence else None,
            top_k=8,
            purpose="report",
        )
        from app.rag.rag_service import build_report_prompt
        prompt = build_report_prompt(finding_dict, retrieval)
        out = {"prompt": prompt, "citations": retrieval.to_citations()}
        if generate:
            out["communication"] = _call_claude(prompt, max_tokens=512)
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _call_claude(prompt: str, max_tokens: int = 1024) -> str:
    """Call Claude (Anthropic) for generated text. Requires ANTHROPIC_API_KEY."""
    try:
        import os

        from anthropic import Anthropic

        from app.core.config import get_settings

        settings = get_settings()
        api_key = getattr(settings, "anthropic_api_key", None) or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "(Set ANTHROPIC_API_KEY and ?generate=true to generate text)"
        client = Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return f"(Claude call failed: {e})"
