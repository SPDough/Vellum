"""Custodian oversight API: fixture ingest → contracts → JSON rules → breaks."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.oversight.service import OversightService, get_oversight_service

router = APIRouter(prefix="/oversight", tags=["Custodian Oversight"])


@router.post("/run", response_model=Dict[str, Any])
async def run_oversight_slice(
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Run the synthetic OMS vs ABOR position reconciliation slice."""
    return service.run_fixture_slice()


@router.get("/snapshot", response_model=Dict[str, Any])
async def get_oversight_snapshot(
    service: OversightService = Depends(get_oversight_service),
) -> Dict[str, Any]:
    """Return the latest oversight snapshot (runs fixtures on first call)."""
    return service.get_snapshot()


@router.get("/positions", response_model=List[Dict[str, Any]])
async def list_oversight_positions(
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = service.get_snapshot()
    return list(snapshot.get("positions") or [])


@router.get("/comparisons", response_model=List[Dict[str, Any]])
async def list_oversight_comparisons(
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = service.get_snapshot()
    return list(snapshot.get("comparisons") or [])


@router.get("/breaks", response_model=List[Dict[str, Any]])
async def list_oversight_breaks(
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = service.get_snapshot()
    return list(snapshot.get("breaks") or [])


@router.get("/rule-results", response_model=List[Dict[str, Any]])
async def list_oversight_rule_results(
    service: OversightService = Depends(get_oversight_service),
) -> List[Dict[str, Any]]:
    snapshot = service.get_snapshot()
    return list(snapshot.get("rule_results") or [])
