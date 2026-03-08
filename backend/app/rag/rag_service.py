"""
Otomeshon RAG → FastAPI Integration (NAV/findings).

Three retrieval purposes, three prompt builders:
  build_explanation_prompt()  → Screen 3, fund ops director audience
  build_rule_prompt()         → Validation engine, rule justification
  build_report_prompt()       → Client-facing investor communication
"""

import logging
from typing import Optional

import openai
import psycopg2

from app.rag.retrieve import RagRetriever, RetrievalResult

log = logging.getLogger(__name__)


def get_rag_retriever(
    db_conn=None,
    openai_client: Optional[openai.OpenAI] = None,
):
    """
    Return a RagRetriever. For use from FastAPI, pass db_conn from the sync session's
    raw connection and optionally openai_client (else uses OPENAI_API_KEY).
    If db_conn is None, creates a new connection from OTOMESHON_DB_DSN or DATABASE_URL.
    """
    from app.core.config import get_settings
    settings = get_settings()
    dsn = getattr(settings, "database_url", None) or settings.__dict__.get("database_url")
    if not dsn:
        import os
        dsn = os.environ.get("OTOMESHON_DB_DSN") or os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("Set DATABASE_URL or OTOMESHON_DB_DSN for RAG retriever")
    # Ensure postgresql:// for psycopg2 (not postgresql+psycopg://)
    if dsn.startswith("postgresql+psycopg"):
        dsn = dsn.replace("postgresql+psycopg", "postgresql", 1)
    if db_conn is None:
        db_conn = psycopg2.connect(dsn)
    if openai_client is None:
        api_key = getattr(settings, "openai_api_key", None) or settings.__dict__.get("openai_api_key")
        if not api_key:
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Set OPENAI_API_KEY for RAG retriever")
        openai_client = openai.OpenAI(api_key=api_key)
    log.info("RAG retriever initialised")
    return RagRetriever(db_conn=db_conn, openai_client=openai_client)


def build_explanation_prompt(finding: dict, retrieval: RetrievalResult) -> str:
    """Prompt for Screen 3 AI explanation panel (fund ops director audience)."""
    evidence_lines = "\n".join(
        f"  - {e['source']}: {e['finding']}"
        for e in finding.get("evidence", [])
    )
    rag_context = retrieval.to_prompt_block()

    return f"""You are a senior fund operations analyst at Otomeshon, an AI-powered NAV validation platform.
You have detected a critical discrepancy in a fund's NAV calculation.
Explain it clearly and precisely to a fund operations director.

Your explanation must:
- Use correct industry terminology grounded in the reference materials below
- Be technically accurate about the custody/dividend processing chain
- End with specific, actionable next steps

---

{rag_context}

---

FINDING DETAILS:

Finding ID:       {finding['finding_id']}
Severity:         {finding['severity']}
Security:         {finding['security_name']} ({finding['ticker']}) — CUSIP {finding['cusip']}
Shares Held:      {finding['shares_held']:,}
Dividend/Share:   ${finding['dividend_per_share']:.2f}
Total NAV Impact: ${finding['total_impact']:,.2f}

Ex-Date:     {finding['ex_date']}
Record Date: {finding['record_date']}
Pay Date:    {finding['pay_date']}
Detected:    {finding['detection_date']}
Custodian:   {finding['custodian']}

API Evidence:
{evidence_lines}

NAV Impact:
  Reported NAV/unit (incorrect): ${finding['nav_per_unit_incorrect']:.2f}
  Correct NAV/unit:              ${finding['nav_per_unit_correct']:.2f}
  Units outstanding:             {finding['units_outstanding']:,}
  Total overstatement:           ${finding['total_impact']:,.2f}

---

Write your explanation using exactly this structure:

WHAT HAPPENED
[2-3 sentences: what operational step failed, where in the custody chain]

EVIDENCE FROM CUSTODIAN APIs
[4 bullet points, one per API signal, describing exactly what each showed]

NAV IMPACT
[2-3 sentences with corrected NAV and investor impact]

NEXT STEPS
[4 numbered, specific, actionable steps for the fund ops team]

CONFIDENCE: [HIGH / MEDIUM / LOW] — [number] API signals corroborated
"""


def build_rule_prompt(finding: dict, retrieval: RetrievalResult) -> str:
    """Prompt for validation rule justification (audit trail)."""
    rag_context = retrieval.to_prompt_block()

    return f"""You are documenting the rule basis for a NAV validation check performed by Otomeshon.

{rag_context}

---

VALIDATION CHECK PERFORMED:
  Check type:    {finding['finding_type']}
  Finding:       {finding['severity']} — {finding.get('description', '')}
  Custodian:     {finding['custodian']}
  APIs queried:  {', '.join(e['source'] for e in finding.get('evidence', []))}

---

Provide a concise rule justification in the following format:

GOVERNING RULE OR PROCEDURE
[Name the specific rule, regulation, or industry procedure that makes this check necessary.
 Include rule numbers or section references where available from the context above.]

OPERATIONAL REQUIREMENT
[1-2 sentences: what the custodian is required to do and by when]

DETECTION METHOD
[1-2 sentences: how Otomeshon detects the failure — which API signals indicate non-compliance]

REGULATORY BASIS (if applicable)
[Any SEC, FINRA, or exchange rules that underpin this requirement]

Keep each section to 2-3 sentences maximum. This output goes into an audit trail, not a dashboard.
"""


def build_report_prompt(finding: dict, retrieval: RetrievalResult) -> str:
    """Prompt for client-facing communication (investor letter)."""
    rag_context = retrieval.to_prompt_block()

    return f"""You are drafting a client communication on behalf of a fund manager.
The fund's custodian made an error in calculating the fund's NAV.
The error has been identified and corrected. You must communicate this professionally
to a sophisticated institutional investor.

The communication must:
- Be factual and transparent without being alarming
- Explain what happened in plain language (no internal jargon)
- State the NAV impact clearly
- Confirm the corrective action taken
- Be appropriate for inclusion in a formal client letter

Reference context (use as background, do not quote directly):
{rag_context}

---

FINDING SUMMARY:

Fund:            {finding.get('fund_name', 'the Fund')}
Security:        {finding['security_name']} ({finding['ticker']})
Issue:           A quarterly cash dividend was not reflected in the Fund's NAV
                 for the period ending {finding['record_date']}
Dividend/Share:  ${finding['dividend_per_share']:.2f}
Shares Held:     {finding['shares_held']:,}
Original NAV/unit:  ${finding['nav_per_unit_incorrect']:.2f}
Corrected NAV/unit: ${finding['nav_per_unit_correct']:.2f}
Difference:         ${abs(finding['nav_per_unit_correct'] - finding['nav_per_unit_incorrect']):.2f} per unit
Units Outstanding:  {finding['units_outstanding']:,}
Total Impact:       ${finding['total_impact']:,.2f}

---

Write a 3-paragraph client communication:

Paragraph 1: What occurred (plain language, no jargon)
Paragraph 2: The corrected NAV and impact on the investor's position
Paragraph 3: Corrective action taken and controls being strengthened

Tone: professional, factual, measured. Do not over-explain or use defensive language.
Length: 150-200 words total. This is a formal letter section, not a dashboard widget.
"""
