"""Durable and in-memory repositories for oversight control objects."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.oversight import (
    OversightBreakRow,
    OversightComparisonRow,
    OversightPositionRow,
    OversightRuleResultRow,
    OversightRunRow,
)
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


class OversightRepository(Protocol):
    async def save_snapshot(self, snapshot: OversightSnapshot) -> Dict[str, Any]:
        ...

    async def get_latest(self) -> Optional[Dict[str, Any]]:
        ...

    async def get_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        ...

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        ...


class InMemoryOversightRepository:
    """Test / fallback store when Postgres is unavailable."""

    def __init__(self) -> None:
        self._runs: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []

    async def save_snapshot(self, snapshot: OversightSnapshot) -> Dict[str, Any]:
        payload = snapshot_to_dict(snapshot)
        self._runs[snapshot.run_id] = payload
        if snapshot.run_id in self._order:
            self._order.remove(snapshot.run_id)
        self._order.append(snapshot.run_id)
        return payload

    async def get_latest(self) -> Optional[Dict[str, Any]]:
        if not self._order:
            return None
        return self._runs[self._order[-1]]

    async def get_by_run_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        return self._runs.get(run_id)

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
                    contract_json=break_contract,
                )
            )

        await self.session.commit()
        return snapshot_to_dict(snapshot)

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
        return {
            "run_id": row.run_id,
            "ran_at": row.ran_at.isoformat(),
            "summary": row.summary_json,
            "source": row.source,
            "positions": [p.contract_json for p in row.positions],
            "comparisons": [c.comparison_json for c in row.comparisons],
            "rule_results": [r.contract_json for r in row.rule_results],
            "breaks": [b.contract_json for b in row.breaks],
        }
