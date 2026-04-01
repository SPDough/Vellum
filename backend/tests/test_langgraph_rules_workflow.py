"""Scaffold tests for LangGraph-shaped rule orchestration."""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.langgraph_workflows import run_sample_rules_workflow


FIXTURES_ROOT = Path(__file__).parent / 'fixtures' / 'rules'


def load_fixture(name: str):
    with (FIXTURES_ROOT / name).open('r', encoding='utf-8') as fh:
        return json.load(fh)


def test_cash_rule_workflow_returns_exception_actions():
    facts = load_fixture('cash_activity_value_date_breach_trigger.json')
    result = run_sample_rules_workflow(
        rule_key='custody.cash_activity_value_date_breach',
        rule_version='1.0.0',
        facts=facts,
    )
    assert result['evaluation']['evaluation_status'] == 'success'
    assert result['evaluation']['triggered'] is True
    assert 'create_exception' in result['next_actions']
    assert 'open_workflow_case' in result['next_actions']


def test_position_rule_workflow_returns_break_actions():
    facts = load_fixture('position_quantity_tolerance_breach_trigger.json')
    result = run_sample_rules_workflow(
        rule_key='reconciliation.position_quantity_tolerance_breach',
        rule_version='1.0.0',
        facts=facts,
    )
    assert result['evaluation']['evaluation_status'] == 'success'
    assert result['evaluation']['triggered'] is True
    assert 'create_reconciliation_break' in result['next_actions']
    assert 'open_workflow_case' in result['next_actions']


def test_non_triggered_workflow_returns_record_pass():
    facts = load_fixture('position_quantity_tolerance_breach_not_trigger.json')
    result = run_sample_rules_workflow(
        rule_key='reconciliation.position_quantity_tolerance_breach',
        rule_version='1.0.0',
        facts=facts,
    )
    assert result['evaluation']['evaluation_status'] == 'success'
    assert result['evaluation']['triggered'] is False
    assert result['next_actions'] == ['record_rule_pass']
