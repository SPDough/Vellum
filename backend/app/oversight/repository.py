"""Durable and in-memory repositories for oversight control objects."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oversight import (
    OversightBreakEventRow,
    OversightBreakRow,
    OversightComparisonRow,
    OversightPositionRow,
    OversightRuleResultRow,
    OversightRunRow,
)
from app.oversight.lifecycle import assert_transition
from app.oversight.store import OversightSnapshot


def snapshot_to_dict(snapshot: OversightSnapshot) -> Dict[str, Any]:
    return {
        "run_id": snapshot.run_id,
        "ran_at": snapshot.ran_at,
        "summary": snapshot.summary,
        "positions": snapshot.positions,
        "comparisons": snapshot.comparisons,
        "rule_results": snapshot.rule_results,
        "breaks": snapshot.breaks,
        "source": snapshot.summary.get("source", "fixture")
        if isinstance(snapshot.summary, dict)
        else "fixture",
    }


def _overlay_break_payload(
    break_contract: Dict[str, Any],
    *,
    status: str,
    assignee: Optional[str] = None,
    updated_at: Optional[str] = None,
) -> Dict[str, Any]:
    contract = copy.deepcopy(break_contract)
    payload = dict(contract.get("payload") or {})
    payload["status"] = status
    if assignee is not None:
        payload["assignee"] = assignee
    elif "assignee" not in payload:
        payload["assignee"] = None
    if updated_at is not None:
        payload["updated_at"] = updated_at
    contract["payload"] = payload
    return contract


class OversightRepository(Protocol):
    async def save_snapshot(self, snapshot: OversightSnapshot) -> Dict[str, Any]:
        ...

    async def get_latest(self) -> Optional[Dict[str, Any]]:
        ...

    async def get_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        ...

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        ...

    async def update_break_status(
        self,
        break_id: str,
        *,
        new_status: str,
        actor: str,
        note: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    async def list_break_events(self, break_id: str) -> List[Dict[str, Any]]:
        ...


class InMemoryOversightRepository:
    """Test / fallback store when Postgres is unavailable."""

    def __init__(self) -> None:
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []
        # break_id -> mutable lifecycle state (source of truth for status)
        self._break_state: Dict[str, Dict[str, Any]] = {}
        self._break_events: Dict[str, List[Dict[str, Any]]] = {}

    def _apply_overlays(self, snap: Dict[str, Any]) -> Dict[str, Any]:
        out = copy.deepcopy(snap)
        overlays: List[Dict[str, Any]] = []
        for break_contract in out.get("breaks") or []:
            bid = (break_contract.get("payload") or {}).get("break_id")
            state = self._break_state.get(str(bid)) if bid else None
            if state:
                overlays.append(
                    _overlay_break_payload(
                        break_contract,
                        status=str(state["status"]),
                        assignee=state.get("assignee"),
                        updated_at=state.get("updated_at"),
                    )
                )
            else:
                overlays.append(break_contract)
        out["breaks"] = overlays
        return out

    async def save_snapshot(self, snapshot: OversightSnapshot) -> Dict[str, Any]:
        payload = snapshot_to_dict(snapshot)
        self._runs[snapshot.run_id] = payload
        if snapshot.run_id in self._order:
            self._order.remove(snapshot.run_id)
        self._order.append(snapshot.run_id)
        now = datetime.now(timezone.utc).isoformat()
        for break_contract in snapshot.breaks:
            bp = break_contract.get("payload") or {}
            bid = str(bp.get("break_id") or "")
            if not bid:
                continue
            self._break_state[bid] = {
                "status": str(bp.get("status") or "open"),
                "assignee": bp.get("assignee"),
                "updated_at": now,
                "run_id": snapshot.run_id,
            }
            self._break_events.setdefault(bid, [])
        return self._apply_overlays(payload)

    async def get_latest(self) -> Optional[Dict[str, Any]]:
        if not self._order:
            return None
        return self._apply_overlays(self._runs[self._order[-1]])

    async def get_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        snap = self._runs.get(run_id)
        if snap is None:
            return None
        return self._apply_overlays(snap)

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for run_id in reversed(self._order[-limit:]):
            snap = self._runs[run_id]
            items.append(
                {
                    "run_id": snap["run_id"],
                    "ran_at": snap["ran_at"],
                    "summary": snap["summary"],
                    "source": snap.get("source", "fixture"),
                }
            )
        return items

    async def update_break_status(
        self,
        break_id: str,
        *,
        new_status: str,
        actor: str,
        note: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        state = self._break_state.get(break_id)
        if state is None:
            raise KeyError(f"Break not found: {break_id}")
        current = str(state["status"])
        assert_transition(current, new_status)
        now = datetime.now(timezone.utc).isoformat()
        next_assignee = assignee if assignee is not None else state.get("assignee")
        event = {
            "break_id": break_id,
            "from_status": current,
            "to_status": new_status.lower(),
            "actor": actor,
            "note": note,
            "assignee": next_assignee,
            "created_at": now,
        }
        self._break_events.setdefault(break_id, []).append(event)
        state["status"] = new_status.lower()
        state["assignee"] = next_assignee
        state["updated_at"] = now

        run_id = state.get("run_id")
        snap = await self.get_by_run_id(str(run_id)) if run_id else None
        break_contract = None
        if snap:
            break_contract = next(
                (
                    b
                    for b in snap.get("breaks") or []
                    if (b.get("payload") or {}).get("break_id") == break_id
                ),
                None,
            )
        return {
            "break_id": break_id,
            "status": state["status"],
            "assignee": state.get("assignee"),
            "updated_at": state["updated_at"],
            "event": event,
            "break": break_contract,
        }

    async def list_break_events(self, break_id: str) -> List[Dict[str, Any]]:
        if break_id not in self._break_state:
            raise KeyError(f"Break not found: {break_id}")
        return list(self._break_events.get(break_id) or [])


class SqlOversightRepository:
    """Postgres-backed persistence for oversight control objects."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_snapshot(self, snapshot: OversightSnapshot) -> Dict[str, Any]:
        ran_at = datetime.fromisoformat(snapshot.ran_at.replace("Z", "+00:00"))
        if ran_at.tzinfo is None:
            ran_at = ran_at.replace(tzinfo=timezone.utc)

        source = "fixture"
        if isinstance(snapshot.summary, dict):
            source = str(snapshot.summary.get("source") or "fixture")

        row = OversightRunRow(
            run_id=snapshot.run_id,
            ran_at=ran_at,
            source=source,
            rule_family=str(
                (snapshot.summary or {}).get("rule_family")
                or "reconciliation.position_quantity_tolerance_breach"
            ),
            rule_version=str((snapshot.summary or {}).get("rule_version") or "1.0.0"),
            summary_json=snapshot.summary or {},
        )
        self.session.add(row)

        for contract in snapshot.positions:
            payload = contract.get("payload") or {}
            lineage = contract.get("lineage") or {}
            book = lineage.get("book")
            contract_id = (
                f"position:{book}:{payload.get('account_id')}:{payload.get('security_id')}"
            )
            self.session.add(
                OversightPositionRow(
                    run_id=snapshot.run_id,
                    contract_id=contract_id,
                    book=book,
                    account_id=payload.get("account_id"),
                    security_id=payload.get("security_id"),
                    contract_json=contract,
                )
            )

        for comparison in snapshot.comparisons:
            self.session.add(
                OversightComparisonRow(
                    run_id=snapshot.run_id,
                    account_id=comparison.get("account_id"),
                    security_id=comparison.get("security_id"),
                    status=str(comparison.get("status") or "unknown"),
                    break_id=comparison.get("break_id"),
                    comparison_json=comparison,
                )
            )

        for result in snapshot.rule_results:
            result_payload = result.get("payload") or {}
            self.session.add(
                OversightRuleResultRow(
                    run_id=snapshot.run_id,
                    rule_result_id=str(result_payload.get("rule_result_id") or ""),
                    rule_id=result_payload.get("rule_id"),
                    triggered=bool(result_payload.get("triggered")),
                    contract_json=result,
                )
            )

        now = datetime.now(timezone.utc)
        for break_contract in snapshot.breaks:
            break_payload = break_contract.get("payload") or {}
            self.session.add(
                OversightBreakRow(
                    run_id=snapshot.run_id,
                    break_id=str(break_payload.get("break_id") or ""),
                    account_id=break_payload.get("account_id"),
                    reason_code=break_payload.get("reason_code"),
                    status=str(break_payload.get("status") or "open"),
                    severity=break_payload.get("severity"),
                    explanation=break_payload.get("explanation"),
                    assignee=break_payload.get("assignee"),
                    updated_at=now,
                    contract_json=break_contract,
                )
            )

        await self.session.commit()
        return snapshot_to_dict(snapshot)

    async def update_break_status(
        self,
        break_id: str,
        *,
        new_status: str,
        actor: str,
        note: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Dict[str, Any]:
        stmt = select(OversightBreakRow).where(OversightBreakRow.break_id == break_id)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            raise KeyError(f"Break not found: {break_id}")

        current = str(row.status or "open")
        assert_transition(current, new_status)
        now = datetime.now(timezone.utc)
        next_status = new_status.lower()
        next_assignee = assignee if assignee is not None else row.assignee

        event = OversightBreakEventRow(
            break_id=break_id,
            from_status=current,
            to_status=next_status,
            actor=actor,
            note=note,
            assignee=next_assignee,
            created_at=now,
        )
        self.session.add(event)

        row.status = next_status
        row.assignee = next_assignee
        row.updated_at = now
        row.contract_json = _overlay_break_payload(
            row.contract_json,
            status=next_status,
            assignee=next_assignee,
            updated_at=now.isoformat(),
        )

        await self.session.commit()
        await self.session.refresh(row)

        return {
            "break_id": break_id,
            "status": row.status,
            "assignee": row.assignee,
            "updated_at": row.updated_at.isoformat(),
            "event": {
                "break_id": break_id,
                "from_status": current,
                "to_status": next_status,
                "actor": actor,
                "note": note,
                "assignee": next_assignee,
                "created_at": now.isoformat(),
            },
            "break": row.contract_json,
        }

    async def list_break_events(self, break_id: str) -> List[Dict[str, Any]]:
        exists = await self.session.execute(
            select(OversightBreakRow.break_id).where(
                OversightBreakRow.break_id == break_id
            )
        )
        if exists.scalar_one_or_none() is None:
            raise KeyError(f"Break not found: {break_id}")

        stmt = (
            select(OversightBreakEventRow)
            .where(OversightBreakEventRow.break_id == break_id)
            .order_by(OversightBreakEventRow.created_at.asc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "break_id": e.break_id,
                "from_status": e.from_status,
                "to_status": e.to_status,
                "actor": e.actor,
                "note": e.note,
                "assignee": e.assignee,
                "created_at": e.created_at.isoformat(),
            }
            for e in rows
        ]

    async def get_latest(self) -> Optional[Dict[str, Any]]:
        stmt = (
            select(OversightRunRow)
            .options(
                selectinload(OversightRunRow.positions),
                selectinload(OversightRunRow.comparisons),
                selectinload(OversightRunRow.rule_results),
                selectinload(OversightRunRow.breaks),
            )
            .order_by(OversightRunRow.ran_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_snapshot(row)

    async def get_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        stmt = (
            select(OversightRunRow)
            .where(OversightRunRow.run_id == run_id)
            .options(
                selectinload(OversightRunRow.positions),
                selectinload(OversightRunRow.comparisons),
                selectinload(OversightRunRow.rule_results),
                selectinload(OversightRunRow.breaks),
            )
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._row_to_snapshot(row)

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        stmt = (
            select(OversightRunRow)
            .order_by(OversightRunRow.ran_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "run_id": row.run_id,
                "ran_at": row.ran_at.isoformat(),
                "summary": row.summary_json,
                "source": row.source,
                "rule_family": row.rule_family,
                "rule_version": row.rule_version,
            }
            for row in rows
        ]

    @staticmethod
    def _row_to_snapshot(row: OversightRunRow) -> Dict[str, Any]:
        breaks: List[Dict[str, Any]] = []
        for b in row.breaks:
            breaks.append(
                _overlay_break_payload(
                    b.contract_json,
                    status=str(b.status or "open"),
                    assignee=b.assignee,
                    updated_at=b.updated_at.isoformat() if b.updated_at else None,
                )
            )
        return {
            "run_id": row.run_id,
            "ran_at": row.ran_at.isoformat(),
            "summary": row.summary_json,
            "source": row.source,
            "positions": [p.contract_json for p in row.positions],
            "comparisons": [c.comparison_json for c in row.comparisons],
            "rule_results": [r.contract_json for r in row.rule_results],
            "breaks": breaks,
        }
