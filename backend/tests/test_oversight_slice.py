"""Tests for the P0 custodian oversight vertical slice."""

from __future__ import annotations

from app.oversight.service import OversightService
from app.oversight.store import OversightStore
from app.rules.engine import RuleEngine


def test_oversight_fixture_slice_detects_position_breaks():
    service = OversightService(store=OversightStore(), engine=RuleEngine())
    snapshot = service.run_fixture_slice()

    assert snapshot["summary"]["position_pairs"] == 3
    assert snapshot["summary"]["matched"] == 1
    assert snapshot["summary"]["breaks"] == 2
    assert len(snapshot["breaks"]) == 2
    assert len(snapshot["rule_results"]) == 3

    break_accounts = {
        b["payload"]["account_id"] + ":" + next(
            c["security_id"]
            for c in snapshot["comparisons"]
            if c.get("break_id") == b["payload"]["break_id"]
        )
        for b in snapshot["breaks"]
    }
    assert "ACCOUNT-001:SEC-ABC" in break_accounts
    assert "ACCOUNT-002:SEC-DEF" in break_accounts

    matched = [c for c in snapshot["comparisons"] if c["status"] == "matched"]
    assert len(matched) == 1
    assert matched[0]["security_id"] == "SEC-XYZ"

    for result in snapshot["rule_results"]:
        assert result["contract_type"] == "RuleResult"
        assert result["source_type"] == "native-rule-engine"


def test_oversight_snapshot_reuses_store_until_rerun():
    store = OversightStore()
    service = OversightService(store=store, engine=RuleEngine())
    first = service.run_fixture_slice()
    second = service.get_snapshot()
    assert first["run_id"] == second["run_id"]

    third = service.run_fixture_slice()
    assert third["run_id"] != first["run_id"]
