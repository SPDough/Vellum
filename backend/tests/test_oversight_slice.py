"""Tests for durable custodian oversight vertical slice (P1a/P1b)."""

from __future__ import annotations

import pytest

from app.oversight.repository import InMemoryOversightRepository
from app.oversight.service import OversightService
from app.rules.engine import RuleEngine


@pytest.mark.asyncio
async def test_oversight_fixture_slice_detects_position_breaks():
    service = OversightService(
        repository=InMemoryOversightRepository(), engine=RuleEngine()
    )
    snapshot = await service.run_fixture_slice()

    assert snapshot["summary"]["position_pairs"] == 4
    assert snapshot["summary"]["breaks"] == 4
    assert snapshot["summary"]["source"] == "fixture"
    assert "reconciliation.valuation_mismatch" in snapshot["summary"]["rules_evaluated"]

    reason_codes = {b["payload"]["reason_code"] for b in snapshot["breaks"]}
    assert "POSITION_QUANTITY_TOLERANCE_BREACH" in reason_codes
    assert "POSITION_VALUATION_MISMATCH" in reason_codes
    assert "POSITION_MISSING_LEG" in reason_codes

    matched = [c for c in snapshot["comparisons"] if c["status"] == "matched"]
    assert matched == []

    for result in snapshot["rule_results"]:
        assert result["contract_type"] == "RuleResult"
        assert result["source_type"] == "native-rule-engine"


@pytest.mark.asyncio
async def test_oversight_snapshot_history_across_runs():
    repo = InMemoryOversightRepository()
    service = OversightService(repository=repo, engine=RuleEngine())
    first = await service.run_fixture_slice()
    second = await service.get_snapshot()
    assert first["run_id"] == second["run_id"]

    third = await service.run_fixture_slice()
    assert third["run_id"] != first["run_id"]

    runs = await service.list_runs()
    assert len(runs) == 2
    assert runs[0]["run_id"] == third["run_id"]
    assert runs[1]["run_id"] == first["run_id"]

    loaded = await service.get_snapshot(run_id=first["run_id"])
    assert loaded["run_id"] == first["run_id"]
    assert loaded["summary"]["breaks"] == 4


def test_missing_leg_and_valuation_rules():
    engine = RuleEngine()

    missing = engine.evaluate_rule(
        "reconciliation.position_missing_leg",
        "1.0.0",
        {
            "target_contract_ids": ["position:oms:A:S"],
            "payload": {"account_id": "A", "security_id": "S", "quantity": 100},
            "derived": {
                "missing_leg": True,
                "missing_book": "abor",
                "present_book": "oms",
                "oms_quantity": 100,
                "abor_quantity": None,
            },
        },
    )
    assert missing.triggered is True
    assert missing.result["payload"]["result_code"] == "POSITION_MISSING_LEG"

    valuation = engine.evaluate_rule(
        "reconciliation.valuation_mismatch",
        "1.0.0",
        {
            "target_contract_ids": ["position:abor:A:S"],
            "payload": {"account_id": "A", "security_id": "S", "quantity": 500},
            "derived": {
                "absolute_quantity_difference": 0,
                "absolute_market_value_difference": 3500,
                "oms_market_value": 87500,
                "abor_market_value": 91000,
            },
        },
    )
    assert valuation.triggered is True
    assert valuation.result["payload"]["result_code"] == "POSITION_VALUATION_MISMATCH"
