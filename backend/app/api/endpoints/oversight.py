"""Custodian oversight API: durable control objects + JSON rules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.oversight.csv_ingest import PositionCsvIngestError
from app.oversight.lifecycle import BreakTransitionError
from app.oversight.repository import SqlOversightRepository
from app.oversight.service import OversightService

router = APIRouter(prefix="/oversight", tags=["Custodian Oversight"])


class BreakStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Target break status")
    note: Optional[str] = Field(None, description="Operator note for audit trail")
    assignee: Optional[str] = Field(None, description="Owner of next step")
    actor: str = Field("portal-user", description="Who performed the transition")


async def get_oversight_service(
    db: AsyncSession = Depends(get_db),
) -> OversightService:
    """Postgres-backed oversight service (moat control objects are durable)."""
    return OversightService(repository=SqlOversightRepository(db))


@router.post("/run", response_model=Dict[str, Any])
async def run_oversight_slice(
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Run the synthetic OMS vs ABOR position reconciliation slice and persist it."""
    return await service.run_fixture_slice()


@router.post("/ingest/csv", response_model=Dict[str, Any])
async def ingest_position_csv(
    oms_file: UploadFile = File(..., description="OMS positions CSV"),
    abor_file: UploadFile = File(..., description="ABOR/custodian positions CSV"),
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Ingest paired position CSVs into contracts, evaluate JSON rules, persist breaks."""
    try:
        oms_bytes = await oms_file.read()
        abor_bytes = await abor_file.read()
        return await service.run_csv_slice(oms_bytes, abor_bytes)
    except PositionCsvIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.post("/ingest/sample-csv", response_model=Dict[str, Any])
async def ingest_sample_position_csv(
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Run the bundled sample OMS/ABOR CSV pair (demo ingest path)."""
    try:
        return await service.run_sample_csv_slice()
    except PositionCsvIngestError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc


@router.get("/snapshot", response_model=Dict[str, Any])
async def get_oversight_snapshot(
    run_id: Optional[str] = Query(None, description="Optional run id; latest if omitted"),
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Return a persisted oversight snapshot (runs fixtures if none exist yet)."""
    try:
        return await service.get_snapshot(run_id=run_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/runs", response_model=List[Dict[str, Any]])
async def list_oversight_runs(
    limit: int = Query(20, ge=1, le=100),
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    """List recent oversight runs (durable history)."""
    return await service.list_runs(limit=limit)


@router.get("/runs/{run_id}", response_model=Dict[str, Any])
async def get_oversight_run(
    run_id: str,
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    try:
        return await service.get_snapshot(run_id=run_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/positions", response_model=List[Dict[str, Any]])
async def list_oversight_positions(
    run_id: Optional[str] = Query(None),
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = await service.get_snapshot(run_id=run_id)
    return list(snapshot.get("positions") or [])


@router.get("/comparisons", response_model=List[Dict[str, Any]])
async def list_oversight_comparisons(
    run_id: Optional[str] = Query(None),
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = await service.get_snapshot(run_id=run_id)
    return list(snapshot.get("comparisons") or [])


@router.get("/breaks", response_model=List[Dict[str, Any]])
async def list_oversight_breaks(
    run_id: Optional[str] = Query(None),
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = await service.get_snapshot(run_id=run_id)
    return list(snapshot.get("breaks") or [])


@router.patch("/breaks/{break_id}/status", response_model=Dict[str, Any])
async def update_break_status(
    break_id: str,
    body: BreakStatusUpdateRequest,
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Transition official break status (control loop — backend enforces legality)."""
    try:
        return await service.update_break_status(
            break_id,
            new_status=body.status,
            actor=body.actor,
            note=body.note,
            assignee=body.assignee,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except BreakTransitionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc


@router.get("/breaks/{break_id}/events", response_model=List[Dict[str, Any]])
async def list_break_events(
    break_id: str,
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    """Immutable audit trail for a break's control-loop transitions."""
    try:
        return await service.list_break_events(break_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc


@router.get("/breaks/{break_id}/explain", response_model=Dict[str, Any])
async def explain_oversight_break(
    break_id: str,
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Expertise-level explanation of a persisted break (moat accessibility)."""
    snapshot = await service.get_snapshot()
    break_contract = next(
        (
            b
            for b in snapshot.get("breaks") or []
            if (b.get("payload") or {}).get("break_id") == break_id
        ),
        None,
    )
    if break_contract is None:
        # Search recent runs for the break id.
        for run in await service.list_runs(limit=50):
            try:
                snap = await service.get_snapshot(run_id=run["run_id"])
            except KeyError:
                continue
            break_contract = next(
                (
                    b
                    for b in snap.get("breaks") or []
                    if (b.get("payload") or {}).get("break_id") == break_id
                ),
                None,
            )
            if break_contract is not None:
                snapshot = snap
                break
    if break_contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Break not found: {break_id}",
        )

    payload = break_contract.get("payload") or {}
    lineage = break_contract.get("lineage") or {}
    comparison = next(
        (
            c
            for c in snapshot.get("comparisons") or []
            if c.get("break_id") == break_id
        ),
        None,
    )
    rule_result = None
    rule_result_id = (comparison or {}).get("rule_result_id") or lineage.get(
        "rule_result_id"
    )
    if rule_result_id:
        rule_result = next(
            (
                r
                for r in snapshot.get("rule_results") or []
                if (r.get("payload") or {}).get("rule_result_id") == rule_result_id
            ),
            None,
        )

    result_payload = (rule_result or {}).get("payload") or {}
    return {
        "break_id": break_id,
        "run_id": snapshot.get("run_id"),
        "headline": payload.get("reason_code") or "RECONCILIATION_BREAK",
        "plain_language": payload.get("explanation")
        or "A deterministic reconciliation rule detected a break.",
        "severity": payload.get("severity"),
        "status": payload.get("status"),
        "assignee": payload.get("assignee"),
        "rule": {
            "rule_id": lineage.get("rule_id") or result_payload.get("rule_id"),
            "rule_version": result_payload.get("rule_version")
            or (snapshot.get("summary") or {}).get("rule_version"),
            "result_code": result_payload.get("result_code"),
        },
        "comparison": comparison,
        "evidence": result_payload.get("evidence_snapshot") or {},
        "expertise_levels": {
            "operator": payload.get("explanation"),
            "control": {
                "rule_id": lineage.get("rule_id") or result_payload.get("rule_id"),
                "rule_version": result_payload.get("rule_version"),
                "contract_ids": payload.get("related_contract_ids") or [],
                "status": payload.get("status"),
                "assignee": payload.get("assignee"),
            },
            "power_user": {
                "break_contract": break_contract,
                "rule_result": rule_result,
            },
        },
    }


@router.get("/rule-results", response_model=List[Dict[str, Any]])
async def list_oversight_rule_results(
    run_id: Optional[str] = Query(None),
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = await service.get_snapshot(run_id=run_id)
    return list(snapshot.get("rule_results") or [])
