"""Orchestrate fixture ingest → Position contracts → JSON rules → breaks."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.oversight.csv_ingest import PositionCsvIngestError, parse_position_csv
from app.oversight.repository import InMemoryOversightRepository, OversightRepository
from app.oversight.store import OversightSnapshot
from app.rules.engine import RuleEngine


class OversightService:
    """Custodian oversight slice: industry meaning stays in backend control objects."""

    RULE_FAMILY = "reconciliation.position_quantity_tolerance_breach"
    RULE_VERSION = "1.0.0"
    QUANTITY_RULE = "reconciliation.position_quantity_tolerance_breach"
    MISSING_LEG_RULE = "reconciliation.position_missing_leg"
    VALUATION_RULE = "reconciliation.valuation_mismatch"

    def __init__(
        self,
        repository: Optional[OversightRepository] = None,
        engine: Optional[RuleEngine] = None,
        fixtures_dir: Optional[Path] = None,
    ) -> None:
        self.repository: OversightRepository = repository or InMemoryOversightRepository()
        self.engine = engine or RuleEngine()
        self.fixtures_dir = fixtures_dir or (
            Path(__file__).resolve().parent / "fixtures"
        )

    async def run_fixture_slice(self) -> Dict[str, Any]:
        oms_rows = self._load_fixture("oms_positions.json")
        abor_rows = self._load_fixture("abor_positions.json")
        snapshot = self._evaluate_books(oms_rows, abor_rows, source="fixture")
        return await self.repository.save_snapshot(snapshot)

    async def run_csv_slice(
        self,
        oms_csv: str | bytes,
        abor_csv: str | bytes,
        *,
        custodian: str | None = "state_street",
    ) -> Dict[str, Any]:
        """Ingest OMS + ABOR position CSVs, normalize, evaluate rules, persist."""
        try:
            oms_rows = parse_position_csv(
                oms_csv, book="oms", source_system="oms"
            )
            abor_rows = parse_position_csv(
                abor_csv,
                book="abor",
                source_system="abor",
                custodian=custodian,
            )
        except PositionCsvIngestError:
            raise
        snapshot = self._evaluate_books(oms_rows, abor_rows, source="csv_ingest")
        return await self.repository.save_snapshot(snapshot)

    async def run_sample_csv_slice(self) -> Dict[str, Any]:
        oms_path = self.fixtures_dir / "sample_oms_positions.csv"
        abor_path = self.fixtures_dir / "sample_abor_positions.csv"
        return await self.run_csv_slice(
            oms_path.read_text(encoding="utf-8"),
            abor_path.read_text(encoding="utf-8"),
            custodian="state_street",
        )

    async def get_snapshot(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        if run_id:
            found = await self.repository.get_by_run_id(run_id)
            if found is None:
                raise KeyError(f"Oversight run not found: {run_id}")
            return found

        latest = await self.repository.get_latest()
        if latest is None:
            return await self.run_fixture_slice()
        return latest

    async def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        return await self.repository.list_runs(limit=limit)

    def _evaluate_books(
        self,
        oms_rows: List[Dict[str, Any]],
        abor_rows: List[Dict[str, Any]],
        source: str,
    ) -> OversightSnapshot:
        oms_by_key = {self._position_key(row): row for row in oms_rows}
        abor_by_key = {self._position_key(row): row for row in abor_rows}
        keys = sorted(set(oms_by_key) | set(abor_by_key))

        positions: List[Dict[str, Any]] = []
        comparisons: List[Dict[str, Any]] = []
        rule_results: List[Dict[str, Any]] = []
        breaks: List[Dict[str, Any]] = []
        now = datetime.now(UTC).isoformat()
        run_id = str(uuid4())

        for key in keys:
            oms = oms_by_key.get(key)
            abor = abor_by_key.get(key)
            oms_contract = self._to_position_contract(oms, book="oms") if oms else None
            abor_contract = (
                self._to_position_contract(abor, book="abor") if abor else None
            )

            if oms_contract:
                positions.append(oms_contract)
            if abor_contract:
                positions.append(abor_contract)

            expected_qty = float(oms["quantity"]) if oms else None
            actual_qty = float(abor["quantity"]) if abor else None
            if expected_qty is None or actual_qty is None:
                difference = None
            else:
                difference = abs(actual_qty - expected_qty)

            account_id = (abor or oms or {}).get("account_id", "")
            security_id = (abor or oms or {}).get("security_id", "")
            entity_id = (abor or oms or {}).get("entity_id", "")

            oms_mv = float(oms["market_value"]) if oms and oms.get("market_value") is not None else None
            abor_mv = (
                float(abor["market_value"])
                if abor and abor.get("market_value") is not None
                else None
            )
            if oms_mv is None or abor_mv is None:
                mv_difference = None
            else:
                mv_difference = abs(abor_mv - oms_mv)

            comparison: Dict[str, Any] = {
                "account_id": account_id,
                "security_id": security_id,
                "entity_id": entity_id,
                "oms_quantity": expected_qty,
                "abor_quantity": actual_qty,
                "absolute_quantity_difference": difference,
                "oms_market_value": oms_mv,
                "abor_market_value": abor_mv,
                "absolute_market_value_difference": mv_difference,
                "status": "missing_leg"
                if expected_qty is None or actual_qty is None
                else ("matched" if difference == 0 and (mv_difference in (None, 0)) else "mismatch"),
                "oms_contract_id": self._contract_id(oms_contract) if oms_contract else None,
                "abor_contract_id": self._contract_id(abor_contract)
                if abor_contract
                else None,
                "break_ids": [],
                "rule_result_ids": [],
            }

            related_ids = [
                cid
                for cid in [
                    comparison["oms_contract_id"],
                    comparison["abor_contract_id"],
                ]
                if cid
            ]
            present_contract = abor_contract or oms_contract
            if present_contract is not None:
                base_payload = {
                    "entity_id": entity_id,
                    "account_id": account_id,
                    "security_id": security_id,
                    "quantity": actual_qty
                    if actual_qty is not None
                    else expected_qty,
                    "currency": present_contract["payload"]["currency"],
                    "position_date": present_contract["payload"]["position_date"],
                }

                rules_to_run: List[str] = []
                if expected_qty is None or actual_qty is None:
                    rules_to_run.append(self.MISSING_LEG_RULE)
                else:
                    rules_to_run.append(self.QUANTITY_RULE)
                    if mv_difference is not None:
                        rules_to_run.append(self.VALUATION_RULE)

                for rule_family in rules_to_run:
                    derived: Dict[str, Any] = {
                        "expected_quantity": expected_qty,
                        "absolute_quantity_difference": difference
                        if difference is not None
                        else 0,
                        "oms_quantity": expected_qty,
                        "abor_quantity": actual_qty,
                        "oms_market_value": oms_mv,
                        "abor_market_value": abor_mv,
                        "absolute_market_value_difference": mv_difference
                        if mv_difference is not None
                        else 0,
                        "missing_leg": expected_qty is None or actual_qty is None,
                        "missing_book": "abor"
                        if abor is None
                        else ("oms" if oms is None else ""),
                        "present_book": "oms"
                        if oms is not None and abor is None
                        else (
                            "abor"
                            if abor is not None and oms is None
                            else "both"
                        ),
                    }
                    facts = {
                        "target_contract_ids": [self._contract_id(present_contract)],
                        "payload": base_payload,
                        "derived": derived,
                    }
                    outcome = self.engine.evaluate_rule(
                        rule_family, self.RULE_VERSION, facts
                    )
                    result = outcome.result
                    result_payload = result.get("payload", {})
                    rule_results.append(result)
                    comparison["rule_result_ids"].append(
                        result_payload.get("rule_result_id")
                    )

                    if outcome.triggered and outcome.evaluation_status == "success":
                        break_contract = self._build_break(
                            result_payload=result_payload,
                            comparison=comparison,
                            related_ids=related_ids,
                            detected_at=now,
                        )
                        breaks.append(break_contract)
                        result_payload["created_reconciliation_break_id"] = (
                            break_contract["payload"]["break_id"]
                        )
                        comparison["break_ids"].append(
                            break_contract["payload"]["break_id"]
                        )
                        comparison["break_id"] = break_contract["payload"]["break_id"]
                        comparison["rule_result_id"] = result_payload.get(
                            "rule_result_id"
                        )
                        comparison["status"] = "break"

            comparisons.append(comparison)

        return OversightSnapshot(
            run_id=run_id,
            ran_at=now,
            positions=positions,
            comparisons=comparisons,
            rule_results=rule_results,
            breaks=breaks,
            summary={
                "position_pairs": len(comparisons),
                "matched": sum(1 for c in comparisons if c["status"] == "matched"),
                "breaks": len(breaks),
                "missing_leg": sum(
                    1 for c in comparisons if c.get("absolute_quantity_difference") is None
                    and (c.get("oms_quantity") is None or c.get("abor_quantity") is None)
                ),
                "rule_family": self.RULE_FAMILY,
                "rule_version": self.RULE_VERSION,
                "rules_evaluated": [
                    self.QUANTITY_RULE,
                    self.MISSING_LEG_RULE,
                    self.VALUATION_RULE,
                ],
                "source": source,
            },
        )

    def _load_fixture(self, name: str) -> List[Dict[str, Any]]:
        path = self.fixtures_dir / name
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, list):
            raise ValueError(f"Fixture {name} must be a JSON array")
        return data

    @staticmethod
    def _position_key(row: Dict[str, Any]) -> Tuple[str, str]:
        return (str(row.get("account_id", "")), str(row.get("security_id", "")))

    @staticmethod
    def _to_position_contract(row: Dict[str, Any], book: str) -> Dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        source_system = str(row.get("source_system") or book)
        source_record_id = str(
            row.get("source_record_id")
            or f"{book}-{row.get('account_id')}-{row.get('security_id')}"
        )
        return {
            "contract_type": "Position",
            "contract_version": "1.0.0",
            "source_system": source_system,
            "source_type": "fixture",
            "source_record_id": source_record_id,
            "ingested_at": now,
            "effective_at": now,
            "lineage": {
                "book": book,
                "custodian": row.get("custodian"),
            },
            "payload": {
                "entity_id": str(row["entity_id"]),
                "account_id": str(row["account_id"]),
                "security_id": str(row["security_id"]),
                "instrument_id": str(row.get("instrument_id") or ""),
                "quantity": float(row["quantity"]),
                "currency": str(row.get("currency") or "USD"),
                "position_date": str(row["position_date"]),
                "status": str(row.get("status") or "open"),
            },
            "data_quality_flags": [],
        }

    @staticmethod
    def _contract_id(contract: Dict[str, Any]) -> str:
        payload = contract["payload"]
        book = (contract.get("lineage") or {}).get("book", "unknown")
        return (
            f"position:{book}:{payload['account_id']}:{payload['security_id']}"
        )

    @staticmethod
    def _build_break(
        result_payload: Dict[str, Any],
        comparison: Dict[str, Any],
        related_ids: List[str],
        detected_at: str,
    ) -> Dict[str, Any]:
        break_id = str(uuid4())
        return {
            "contract_type": "ReconciliationBreak",
            "contract_version": "1.0.0",
            "source_system": "vellum",
            "source_type": "native-rule-engine",
            "source_record_id": result_payload.get("rule_result_id", ""),
            "ingested_at": detected_at,
            "effective_at": detected_at,
            "lineage": {
                "rule_id": result_payload.get("rule_id"),
                "rule_result_id": result_payload.get("rule_result_id"),
            },
            "payload": {
                "break_id": break_id,
                "break_type": result_payload.get("result_code", "reconciliation_break").lower(),
                "entity_id": comparison.get("entity_id") or "",
                "account_id": comparison.get("account_id") or "",
                "related_contract_ids": related_ids,
                "severity": result_payload.get("severity") or "high",
                "status": "open",
                "detected_at": detected_at,
                "reason_code": result_payload.get("result_code")
                or "POSITION_QUANTITY_TOLERANCE_BREACH",
                "explanation": result_payload.get("explanation") or "",
            },
        }


# Module-level memory repo so process restarts aren't required for demo without DB wiring.
_MEMORY_REPO = InMemoryOversightRepository()


def get_memory_oversight_service() -> OversightService:
    return OversightService(repository=_MEMORY_REPO)
