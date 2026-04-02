"""Scaffold tests for Vellum's JSON-first rules engine.

These are contract-shape/unit-style tests for when Python runtime becomes available.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.rules.engine import RuleEngine


FIXTURES_ROOT = Path(__file__).parent / 'fixtures' / 'rules'


def load_fixture(name: str):
    with (FIXTURES_ROOT / name).open('r', encoding='utf-8') as fh:
        return json.load(fh)


def test_unsettled_trade_aging_triggers():
    engine = RuleEngine()
    facts = {
        'target_contract_ids': ['trade-status:trade-001'],
        'payload': {
            'trade_id': 'TRADE-001',
            'account_id': 'ACCOUNT-001',
            'security_id': 'SEC-ABC',
            'trade_date': '2026-03-28',
            'settlement_date': '2026-03-29',
            'settlement_status': 'UNSETTLED',
        },
        'derived': {
            'days_past_settlement': 3,
        },
    }
    outcome = engine.evaluate_rule('custody', '1.0.0', facts)
    assert outcome.evaluation_status == 'success'
    assert outcome.triggered is True
    assert outcome.result['payload']['result_code'] == 'UNSETTLED_TRADE_AGING_BREACH'


def test_cash_activity_value_date_breach_triggers():
    engine = RuleEngine()
    facts = load_fixture('cash_activity_value_date_breach_trigger.json')
    outcome = engine.evaluate_rule('custody', '1.0.0', facts)
    assert outcome.evaluation_status == 'success'
    assert outcome.triggered is True


def test_cash_activity_value_date_breach_does_not_trigger():
    engine = RuleEngine()
    facts = load_fixture('cash_activity_value_date_breach_not_trigger.json')
    outcome = engine.evaluate_rule('custody', '1.0.0', facts)
    assert outcome.evaluation_status == 'success'
    assert outcome.triggered is False


def test_position_quantity_tolerance_breach_triggers():
    engine = RuleEngine()
    facts = load_fixture('position_quantity_tolerance_breach_trigger.json')
    outcome = engine.evaluate_rule('reconciliation', '1.0.0', facts)
    assert outcome.evaluation_status == 'success'
    assert outcome.triggered is True


def test_position_quantity_tolerance_breach_does_not_trigger():
    engine = RuleEngine()
    facts = load_fixture('position_quantity_tolerance_breach_not_trigger.json')
    outcome = engine.evaluate_rule('reconciliation', '1.0.0', facts)
    assert outcome.evaluation_status == 'success'
    assert outcome.triggered is False
