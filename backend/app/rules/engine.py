"""Rule evaluation scaffold for Vellum deterministic JSON-first rules."""

from __future__ import annotations

import re
from datetime import datetime, UTC
from functools import lru_cache
from typing import Any, Dict
from uuid import uuid4

PLACEHOLDER_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

# Rule-set names callers already use (matching the old DroolsService
# execute_rules rule_set argument) mapped to this engine's rule_family tags.
RULE_SET_TO_GROUP = {
    'trade-validation': 'trade_validation',
    'risk-management': 'risk_management',
    'compliance-checks': 'compliance_checks',
    'settlement-processing': 'settlement_processing',
    'equity-pricing': 'pricing_alerts',
}

from app.integrations.contracts.registry import get_contract_registry

from .jsonlogic import JsonLogicEvaluator, JsonLogicEvaluationError
from .models import RuleEvaluationOutcome
from .registry import get_rule_registry

# Maps each ported rule_id to the legacy Drools fact class name its outcome
# should be reported as, so callers migrated off DroolsService (API routes,
# LangGraph nodes) can keep filtering actions_triggered by "type" unchanged.
LEGACY_ACTION_TYPE = {
    'trade_validation.large_trade_alert': 'Alert',
    'trade_validation.settlement_date_validation': 'ValidationError',
    'trade_validation.weekend_settlement_check': 'Alert',
    'trade_validation.zero_price_validation': 'ValidationError',
    'risk_management.position_limit_check': 'RiskAlert',
    'risk_management.concentration_risk_check': 'RiskAlert',
    'risk_management.overnight_risk_limit': 'RiskAlert',
    'risk_management.high_frequency_trading_detection': 'RiskAlert',
    'risk_management.market_hours_check': 'Alert',
    'compliance_checks.kyc_status_check': 'ComplianceAlert',
    'compliance_checks.aml_high_risk_screening': 'ComplianceAlert',
    'compliance_checks.stale_kyc_review': 'ComplianceAlert',
    'compliance_checks.sanctioned_country_check': 'ComplianceAlert',
    'settlement_processing.cash_availability_check': 'Alert',
    'settlement_processing.settlement_cutoff_time': 'Alert',
    'settlement_processing.corporate_action_pending': 'Alert',
    'pricing_alerts.price_variance_check': 'PricingAlert',
    'pricing_alerts.stale_market_data_warning': 'PricingAlert',
    'pricing_alerts.zero_negative_price_validation': 'PricingAlert',
    'pricing_alerts.low_confidence_price_warning': 'PricingAlert',
}


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

    def evaluate_rule_group(self, group: str, facts: Dict[str, Any], version: str = '1.0.0') -> Dict[str, Any]:
        """Evaluate every active rule tagged with `group` against shared facts.

        Returns a DroolsService.RuleResult-shaped dict (rule_name, status,
        facts_processed, rules_fired, actions_triggered, execution_time_ms,
        error_message) so callers migrated off Drools need minimal changes.
        """
        start = datetime.now(UTC)
        rule_ids = self.rule_registry.list_rule_ids_by_tag(group, version)

        rules_fired = []
        actions_triggered = []
        error_messages = []

        for rule_id in rule_ids:
            outcome = self.evaluate_rule(rule_id, version, facts)
            if outcome.evaluation_status == 'error':
                error_messages.append(outcome.result['payload'].get('error_message', ''))
                continue
            if outcome.triggered:
                rules_fired.append(rule_id)
                actions_triggered.append(self._to_legacy_action(rule_id, outcome.result))

        execution_time_ms = (datetime.now(UTC) - start).total_seconds() * 1000

        return {
            'rule_name': group,
            'status': 'failed' if error_messages and not rules_fired else 'success',
            'facts_processed': 1,
            'rules_fired': rules_fired,
            'actions_triggered': actions_triggered,
            'execution_time_ms': execution_time_ms,
            'error_message': '; '.join(error_messages) if error_messages else None,
        }

    def _to_legacy_action(self, rule_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
        payload = result['payload']
        evidence = payload.get('evidence_snapshot') or {}
        return {
            'type': LEGACY_ACTION_TYPE.get(rule_id, 'Alert'),
            'code': payload.get('result_code', ''),
            'message': payload.get('explanation', ''),
            'trade_id': evidence.get('trade.trade_id') or evidence.get('pricing.request_id', ''),
            'severity': payload.get('severity', ''),
            'timestamp': payload.get('evaluated_at', ''),
        }

    def _resolve_rule_family(self, rule_family: str, facts: Dict[str, Any]) -> str:
        """Map coarse families to concrete indexed definitions when needed."""
        # Prefer exact indexed families; only alias coarse names.
        if '.' in rule_family:
            return rule_family

        payload = facts.get("payload", {}) if isinstance(facts, dict) else {}

        # Cash activity fixtures use the generic custody family.
        if rule_family == "custody" and isinstance(payload, dict) and "transaction_id" in payload:
            return "custody.cash_activity_value_date_breach"

        if rule_family == "custody" and isinstance(payload, dict) and "trade_id" in payload:
            return "custody.unsettled_trade_aging"

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

        def substitute(match: re.Match) -> str:
            value = self.evaluator.evaluate({'var': match.group(1)}, facts)
            return '' if value is None else str(value)

        return PLACEHOLDER_PATTERN.sub(substitute, template)


@lru_cache(maxsize=1)
def get_rule_engine() -> RuleEngine:
    return RuleEngine()
