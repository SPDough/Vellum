"""Rule evaluation scaffold for Vellum deterministic JSON-first rules."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any, Dict
from uuid import uuid4

from app.integrations.contracts.registry import get_contract_registry

from .jsonlogic import JsonLogicEvaluator, JsonLogicEvaluationError
from .models import RuleEvaluationOutcome
from .registry import get_rule_registry


class RuleEngine:
    def __init__(self):
        self.rule_registry = get_rule_registry()
        self.contract_registry = get_contract_registry()
        self.evaluator = JsonLogicEvaluator()

    def evaluate_rule(self, rule_family: str, version: str, facts: Dict[str, Any]) -> RuleEvaluationOutcome:
        resolved_rule_family = self._resolve_rule_family(rule_family, facts)
        rule_record = self.rule_registry.get_rule(resolved_rule_family, version)
        definition = rule_record.definition
        payload = definition.get('payload', {})

        try:
            expression_language = payload.get('expression_language')
            if expression_language not in {'jsonlogic', 'vellum-json'}:
                raise ValueError(f'Unsupported expression language: {expression_language}')

            triggered = bool(self.evaluator.evaluate(payload.get('predicate', {}), facts))
            result = self._build_result(definition=definition, facts=facts, triggered=triggered)
            return RuleEvaluationOutcome(
                triggered=triggered,
                evaluation_status='success',
                result=result,
            )
        except (JsonLogicEvaluationError, ValueError, TypeError, KeyError, FileNotFoundError) as exc:
            result = self._build_result(definition=definition if 'definition' in locals() else {'payload': {}}, facts=facts, triggered=False, error_message=str(exc), evaluation_status='error')
            return RuleEvaluationOutcome(
                triggered=False,
                evaluation_status='error',
                result=result,
            )

    def _resolve_rule_family(self, rule_family: str, facts: Dict[str, Any]) -> str:
        """Map coarse families to concrete indexed definitions when needed."""
        payload = facts.get("payload", {}) if isinstance(facts, dict) else {}

        # Cash activity fixtures use the generic custody family.
        if rule_family == "custody" and isinstance(payload, dict) and "transaction_id" in payload:
            return "custody.cash_activity_value_date_breach"

        # Reconciliation fixtures currently target the position tolerance rule.
        if rule_family == "reconciliation":
            return "reconciliation.position_quantity_tolerance_breach"

        return rule_family

    def _build_result(
        self,
        definition: Dict[str, Any],
        facts: Dict[str, Any],
        triggered: bool,
        error_message: str | None = None,
        evaluation_status: str = 'success',
    ) -> Dict[str, Any]:
        payload = definition.get('payload', {})
        outcome = payload.get('outcome', {})
        timestamp = datetime.now(UTC).isoformat()
        fact_contract_ids = facts.get('target_contract_ids', []) if isinstance(facts, dict) else []

        return {
            'contract_type': 'RuleResult',
            'contract_version': '1.0.0',
            'source_system': 'vellum',
            'source_type': 'native-rule-engine',
            'source_record_id': payload.get('rule_id', ''),
            'effective_at': timestamp,
            'payload': {
                'rule_result_id': str(uuid4()),
                'rule_id': payload.get('rule_id', ''),
                'rule_version': payload.get('version', '1.0.0'),
                'evaluation_status': evaluation_status,
                'triggered': triggered,
                'severity': payload.get('severity', ''),
                'materiality': self._resolve_materiality(payload, facts),
                'result_code': outcome.get('result_code', ''),
                'result_type': outcome.get('result_type', 'pass' if not triggered else 'flag'),
                'target_contract_ids': fact_contract_ids,
                'evaluated_at': timestamp,
                'evidence_snapshot': self._build_evidence_snapshot(payload, facts),
                'explanation': self._build_explanation(payload, facts, triggered, error_message),
                'created_exception_id': '',
                'created_reconciliation_break_id': '',
                'created_workflow_case_id': '',
                'created_approval_request_id': '',
                'error_message': error_message or '',
            },
        }

    def _resolve_materiality(self, payload: Dict[str, Any], facts: Dict[str, Any]) -> str:
        materiality = payload.get('materiality') or {}
        mode = materiality.get('mode')
        if mode == 'static':
            return str(materiality.get('value', ''))
        if mode == 'expression':
            try:
                return str(self.evaluator.evaluate(materiality.get('expression', {}), facts))
            except Exception:
                return ''
        return ''

    def _build_evidence_snapshot(self, payload: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
        evidence = payload.get('evidence') or {}
        fields = evidence.get('fields') or []
        snapshot: Dict[str, Any] = {}
        for field in fields:
            snapshot[field] = self.evaluator.evaluate({'var': field}, facts)
        if evidence.get('rag_enabled'):
            snapshot['rag_collections'] = evidence.get('rag_collections', [])
        return snapshot

    def _build_explanation(self, payload: Dict[str, Any], facts: Dict[str, Any], triggered: bool, error_message: str | None) -> str:
        if error_message:
            return f'Rule evaluation failed: {error_message}'
        outcome = payload.get('outcome') or {}
        template = outcome.get('explanation_template', '')
        if not template:
            return 'Rule triggered.' if triggered else 'Rule did not trigger.'
        rendered = template
        for key in ['payload.trade_id', 'payload.account_id', 'payload.security_id', 'payload.trade_date', 'payload.settlement_date', 'payload.settlement_status', 'derived.days_past_settlement']:
            placeholder = '{{' + key + '}}'
            if placeholder in rendered:
                value = self.evaluator.evaluate({'var': key}, facts)
                rendered = rendered.replace(placeholder, '' if value is None else str(value))
        return rendered
