"""Orchestrate fixture ingest → Position contracts → JSON rules → breaks."""

from __future__ import annotations

import json
from datetime import datetime, UTC
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.oversight.store import OversightSnapshot, OversightStore, get_oversight_store
from app.rules.engine import RuleEngine


class OversightService:
    """P0 custodian oversight slice using synthetic OMS vs ABOR fixtures."""

    RULE_FAMILY = "reconciliation.position_quantity_tolerance_breach"
    RULE_VERSION = "1.0.0"

    def __init__(
        self,
        store: Optional[OversightStore] = None,
        engine: Optional[RuleEngine] = None,
        fixtures_dir: Optional[Path] = None,
    ) -> None:
        self.store = store or get_oversight_store()
        self.engine = engine or RuleEngine()
        self.fixtures_dir = fixtures_dir or (
            Path(__file__).resolve().parent / "fixtures"
        )

    def run_fixture_slice(self) -> Dict[str, Any]:
        oms_rows = self._load_fixture("oms_positions.json")
        abor_rows = self._load_fixture("abor_positions.json")

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

            comparison: Dict[str, Any] = {
                "account_id": account_id,
                "security_id": security_id,
                "entity_id": entity_id,
                "oms_quantity": expected_qty,
                "abor_quantity": actual_qty,
                "absolute_quantity_difference": difference,
                "status": "missing_leg"
                if expected_qty is None or actual_qty is None
                else ("matched" if difference == 0 else "mismatch"),
                "oms_contract_id": self._contract_id(oms_contract) if oms_contract else None,
                "abor_contract_id": self._contract_id(abor_contract)
                if abor_contract
                else None,
            }

            if abor_contract is not None and expected_qty is not None and difference is not None:
                facts = {
                    "target_contract_ids": [self._contract_id(abor_contract)],
                    "payload": {
                        "entity_id": entity_id,
                        "account_id": account_id,
                        "security_id": security_id,
                        "quantity": actual_qty,
                        "currency": abor_contract["payload"]["currency"],
                        "position_date": abor_contract["payload"]["position_date"],
                    },
                    "derived": {
                        "expected_quantity": expected_qty,
                        "absolute_quantity_difference": difference,
                        "oms_quantity": expected_qty,
                        "abor_quantity": actual_qty,
                    },
                }
                outcome = self.engine.evaluate_rule(
                    self.RULE_FAMILY, self.RULE_VERSION, facts
                )
                result = outcome.result
                result_payload = result.get("payload", {})
                rule_results.append(result)

                if outcome.triggered and outcome.evaluation_status == "success":
                    break_contract = self._build_break(
                        result_payload=result_payload,
                        comparison=comparison,
                        related_ids=[
                            cid
                            for cid in [
                                comparison["oms_contract_id"],
                                comparison["abor_contract_id"],
                            ]
                            if cid
                        ],
                        detected_at=now,
                    )
                    breaks.append(break_contract)
                    result_payload["created_reconciliation_break_id"] = break_contract[
                        "payload"
                    ]["break_id"]
                    comparison["break_id"] = break_contract["payload"]["break_id"]
                    comparison["rule_result_id"] = result_payload.get("rule_result_id")
                    comparison["status"] = "break"

            comparisons.append(comparison)

        snapshot = OversightSnapshot(
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
                    1 for c in comparisons if c["status"] == "missing_leg"
                ),
                "rule_family": self.RULE_FAMILY,
                "rule_version": self.RULE_VERSION,
            },
        )
        self.store.replace(snapshot)
        return self.snapshot_dict(snapshot)

    def get_snapshot(self) -> Dict[str, Any]:
        snapshot = self.store.get()
        if not snapshot.run_id:
            return self.run_fixture_slice()
        return self.snapshot_dict(snapshot)

    @staticmethod
    def snapshot_dict(snapshot: OversightSnapshot) -> Dict[str, Any]:
        return {
            "run_id": snapshot.run_id,
            "ran_at": snapshot.ran_at,
            "summary": snapshot.summary,
            "positions": snapshot.positions,
            "comparisons": snapshot.comparisons,
            "rule_results": snapshot.rule_results,
            "breaks": snapshot.breaks,
        }

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
                "break_type": "position_quantity_tolerance",
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


@lru_cache(maxsize=1)
def get_oversight_service() -> OversightService:
    return OversightService()
