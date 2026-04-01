"""LangGraph-oriented scaffold for deterministic rule orchestration.

This file intentionally does not make LangGraph a hard runtime dependency yet.
If LangGraph is installed later, the same state model and node split can be
ported directly into a real StateGraph. For now, this gives Vellum a clean,
product-aligned orchestration shape around deterministic rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from app.rules.engine import RuleEngine


@dataclass
class RulesWorkflowState:
    rule_key: str
    rule_version: str
    facts: Dict[str, Any]
    evaluation: Optional[Dict[str, Any]] = None
    next_actions: list[str] = field(default_factory=list)
    rag_context: Dict[str, Any] = field(default_factory=dict)
    summary: str = ''


class SampleRulesWorkflow:
    """A LangGraph-shaped scaffold for rule orchestration.

    Intended future graph:
    - load_rule_context
    - evaluate_rule
    - determine_follow_up
    - assemble_response
    """

    def __init__(self):
        self.rule_engine = RuleEngine()

    def load_rule_context(self, state: RulesWorkflowState) -> RulesWorkflowState:
        state.rag_context = {
            'enabled': True,
            'collections': self._infer_rag_collections(state.rule_key),
            'note': 'RAG is advisory context for explanation/workflows; deterministic rule outcome remains authoritative.',
        }
        return state

    def evaluate_rule(self, state: RulesWorkflowState) -> RulesWorkflowState:
        outcome = self.rule_engine.evaluate_rule(state.rule_key, state.rule_version, state.facts)
        state.evaluation = {
            'triggered': outcome.triggered,
            'evaluation_status': outcome.evaluation_status,
            'rule_result': outcome.result,
        }
        return state

    def determine_follow_up(self, state: RulesWorkflowState) -> RulesWorkflowState:
        if not state.evaluation:
            state.next_actions = ['investigate_evaluation_failure']
            return state

        rule_result = state.evaluation.get('rule_result', {})
        payload = rule_result.get('payload', {})

        if state.evaluation.get('evaluation_status') != 'success':
            state.next_actions = ['investigate_evaluation_failure']
        elif payload.get('triggered'):
            result_type = payload.get('result_type')
            if result_type == 'exception':
                state.next_actions = ['create_exception', 'open_workflow_case']
            elif result_type == 'break':
                state.next_actions = ['create_reconciliation_break', 'open_workflow_case']
            else:
                state.next_actions = ['record_rule_hit']
        else:
            state.next_actions = ['record_rule_pass']

        return state

    def assemble_response(self, state: RulesWorkflowState) -> RulesWorkflowState:
        evaluation_status = (state.evaluation or {}).get('evaluation_status', 'unknown')
        triggered = (state.evaluation or {}).get('triggered', False)
        state.summary = (
            f'Rule workflow completed for {state.rule_key}@{state.rule_version}. '
            f'status={evaluation_status}; triggered={triggered}; '
            f'next_actions={", ".join(state.next_actions) if state.next_actions else "none"}.'
        )
        return state

    def run(self, rule_key: str, rule_version: str, facts: Dict[str, Any]) -> Dict[str, Any]:
        state = RulesWorkflowState(
            rule_key=rule_key,
            rule_version=rule_version,
            facts=facts,
        )
        state = self.load_rule_context(state)
        state = self.evaluate_rule(state)
        state = self.determine_follow_up(state)
        state = self.assemble_response(state)
        return {
            'rule_key': state.rule_key,
            'rule_version': state.rule_version,
            'evaluation': state.evaluation,
            'rag_context': state.rag_context,
            'next_actions': state.next_actions,
            'summary': state.summary,
        }

    @staticmethod
    def _infer_rag_collections(rule_key: str) -> list[str]:
        if 'cash' in rule_key:
            return ['custody-cash-playbooks']
        if 'reconciliation' in rule_key or 'position' in rule_key:
            return ['position-reconciliation-playbooks']
        return ['custody-ops-playbooks', 'market-settlement-conventions']


def build_sample_rules_workflow() -> SampleRulesWorkflow:
    return SampleRulesWorkflow()


def run_sample_rules_workflow(rule_key: str, rule_version: str, facts: Dict[str, Any]) -> Dict[str, Any]:
    workflow = build_sample_rules_workflow()
    return workflow.run(rule_key=rule_key, rule_version=rule_version, facts=facts)
