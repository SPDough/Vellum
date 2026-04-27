"""
Procedure document endpoints.

Serves NAV validation procedure documents with a cell-based structure.
The in-memory store seeds a sample document; DB persistence is deferred.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.schemas.procedure_document import (
    ExceptionDecisionRequest,
    ExceptionDecisionResponse,
    ExceptionResolution,
    ProcedureDocument,
    SignoffRequest,
    SignoffResponse,
)

router = APIRouter()

# ---------------------------------------------------------------------------
# Seed document — mirrors src/lib/mockData.ts in otomeshon-portal.
# ---------------------------------------------------------------------------
_SEED: Dict = {
    "id": "doc-apac-eq-01-2026-04-24",
    "title": "Daily NAV Validation",
    "fund_code": "APAC-EQ-01",
    "as_of_date": "2026-04-24",
    "status": "awaiting_review",
    "cells": [
        {
            "cell_id": "cell-1",
            "position": 1,
            "cell_role": "narrative",
            "label": "Overview",
            "body": (
                "Daily NAV validation for APAC-EQ-01 as of 2026-04-24. "
                "This procedure verifies pricing source coverage across the portfolio "
                "and confirms the day-over-day NAV movement falls within the 2.0% "
                "tolerance threshold defined in the fund's valuation policy."
            ),
        },
        {
            "cell_id": "cell-2",
            "position": 2,
            "cell_role": "result",
            "label": "Pricing coverage",
            "status": "pass",
            "summary": "Pricing source coverage check passed: 247 of 247 securities priced from primary pricing sources.",
            "metrics": [
                {"label": "Securities priced", "value": "247 / 247"},
                {"label": "Stale prices (>1d)", "value": "0"},
                {"label": "Manual overrides", "value": "0"},
            ],
        },
        {
            "cell_id": "cell-3",
            "position": 3,
            "cell_role": "narrative",
            "label": "Tolerance checks",
            "body": (
                "Comparing today's calculated NAV per share to the prior business day. "
                "The fund's valuation policy requires escalation when the absolute "
                "day-over-day move exceeds 2.0%."
            ),
        },
        {
            "cell_id": "cell-4",
            "position": 4,
            "cell_role": "result",
            "label": "NAV move",
            "status": "breach",
            "summary": "Day-over-day NAV move of 4.20% exceeds the 2.00% tolerance threshold.",
            "metrics": [
                {"label": "NAV per share (T-1)", "value": "USD 12.4583"},
                {"label": "NAV per share (T)", "value": "USD 12.9819"},
                {"label": "Move", "value": "+4.20%"},
                {"label": "Threshold", "value": "±2.00%"},
            ],
        },
        {
            "cell_id": "cell-5",
            "position": 5,
            "cell_role": "exception",
            "label": "Tolerance breach",
            "severity": "high",
            "description": (
                "NAV move of +4.20% on APAC-EQ-01 exceeds the 2.00% policy tolerance. "
                "Controller decision required before signoff. Largest contributors: "
                "TSMC (+8.1%), Samsung Electronics (+5.4%), driven by overnight earnings announcements."
            ),
            "linked_result_cell_id": "cell-4",
            "remediation_options": [
                {
                    "id": "accept-with-rationale",
                    "label": "Accept move with documented rationale",
                    "description": (
                        "Confirm the move is explained by market events and proceed to signoff. "
                        "Rationale will be attached to the audit record."
                    ),
                },
                {
                    "id": "escalate-pm",
                    "label": "Escalate to portfolio manager",
                    "description": (
                        "Pause the NAV publication and request PM confirmation of overnight "
                        "market moves before proceeding."
                    ),
                },
                {
                    "id": "rerun-pricing",
                    "label": "Reject and rerun pricing",
                    "description": (
                        "Reject the current run and re-fetch closing prices from secondary "
                        "sources before recomputing NAV."
                    ),
                },
            ],
        },
        {
            "cell_id": "cell-6",
            "position": 6,
            "cell_role": "signoff",
            "label": "Controller signoff",
            "required_role": "Fund Controller",
        },
    ],
}

# Mutable in-memory store, keyed by document ID.
_store: Dict[str, Dict] = {_SEED["id"]: copy.deepcopy(_SEED)}


def _get_doc_or_404(doc_id: str) -> Dict:
    doc = _store.get(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Procedure document not found")
    return doc


def _get_cell_or_404(doc: Dict, cell_id: str) -> Dict:
    for cell in doc["cells"]:
        if cell["cell_id"] == cell_id:
            return cell
    raise HTTPException(status_code=404, detail="Cell not found")


@router.get("/{doc_id}", response_model=ProcedureDocument)
async def get_procedure_document(doc_id: str) -> ProcedureDocument:
    doc = _get_doc_or_404(doc_id)
    return ProcedureDocument.model_validate(copy.deepcopy(doc))


@router.post(
    "/{doc_id}/cells/{cell_id}/exception-decision",
    response_model=ExceptionDecisionResponse,
)
async def decide_exception(
    doc_id: str,
    cell_id: str,
    payload: ExceptionDecisionRequest,
) -> ExceptionDecisionResponse:
    doc = _get_doc_or_404(doc_id)
    cell = _get_cell_or_404(doc, cell_id)

    if cell["cell_role"] != "exception":
        raise HTTPException(status_code=400, detail="Cell is not an exception cell")

    option_ids = {o["id"] for o in cell.get("remediation_options", [])}
    if payload.option_id not in option_ids:
        raise HTTPException(status_code=400, detail="Unknown remediation option")

    resolution = {
        "option_id": payload.option_id,
        "rationale": payload.rationale,
        "decided_by": "current.user@vellum.ops",  # replaced by JWT identity in auth phase
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    cell["resolution"] = resolution

    return ExceptionDecisionResponse(
        cell_id=cell_id,
        resolution=ExceptionResolution(**resolution),
    )


@router.post(
    "/{doc_id}/cells/{cell_id}/signoff",
    response_model=SignoffResponse,
)
async def signoff_cell(
    doc_id: str,
    cell_id: str,
    payload: SignoffRequest,
) -> SignoffResponse:
    doc = _get_doc_or_404(doc_id)
    cell = _get_cell_or_404(doc, cell_id)

    if cell["cell_role"] != "signoff":
        raise HTTPException(status_code=400, detail="Cell is not a signoff cell")

    unresolved = [
        c for c in doc["cells"]
        if c["cell_role"] == "exception" and not c.get("resolution")
    ]
    if unresolved:
        raise HTTPException(
            status_code=409,
            detail="Cannot sign off while exceptions remain unresolved",
        )

    signed_by = "current.user@vellum.ops"  # replaced by JWT identity in auth phase
    signed_at = datetime.now(timezone.utc).isoformat()
    cell["signed_by"] = signed_by
    cell["signed_at"] = signed_at
    doc["status"] = "signed"

    return SignoffResponse(cell_id=cell_id, signed_by=signed_by, signed_at=signed_at)
