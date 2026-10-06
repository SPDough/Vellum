"""Tests for the rule groups ported from drools/*.drl onto Vellum's native
JSON-first rules engine (see docs/contracts/RULE_DEFINITION_CONTRACT.md).

Each test exercises RuleEngine.evaluate_rule_group against representative
facts built the same way the migrated callers (API routes, LangGraph nodes)
build them, via app.rules.fact_builder.
"""

from __future__ import annotations

from datetime import datetime

from app.rules import derived_facts, fact_builder
from app.rules.engine import RuleEngine
from app.services import pricing_service


def test_trade_validation_group_triggers_large_trade_and_zero_price():
    engine = RuleEngine()
    trade = {
        "tradeId": "T1",
        "tradeType": "EQUITY",
        "counterpartyId": "CP1",
        "securityId": "SEC1",
        "price": 0,
        "tradeValue": 2_000_000,
        "tradeDate": "2026-10-05",
        "settlementDate": "2026-10-07",
    }
    facts = fact_builder.build_trade_validation_facts(trade)
    result = engine.evaluate_rule_group("trade_validation", facts)

    assert result["status"] == "success"
    assert set(result["rules_fired"]) == {
        "trade_validation.large_trade_alert",
        "trade_validation.zero_price_validation",
    }
    assert all(a["type"] in {"Alert", "ValidationError"} for a in result["actions_triggered"])


def test_trade_validation_group_clean_trade_does_not_trigger():
    engine = RuleEngine()
    trade = {
        "tradeId": "T2",
        "price": 100,
        "tradeValue": 5000,
        "tradeDate": "2026-10-05",
        "settlementDate": "2026-10-06",
    }
    facts = fact_builder.build_trade_validation_facts(trade)
    result = engine.evaluate_rule_group("trade_validation", facts)

    assert result["rules_fired"] == []
    assert result["actions_triggered"] == []


def test_risk_management_group_triggers_position_limit_and_hft():
    engine = RuleEngine()
    trade = {"tradeId": "T3", "securityId": "SEC1", "tradeValue": 2_000_000, "counterpartyId": "CP1"}
    portfolio = {
        "portfolioId": "P1",
        "totalExposure": 9_000_000,
        "exposureLimit": 10_000_000,
        "concentrationLimit": 500_000,
        "availableCash": 1_000_000,
        "securityExposures": {"SEC1": 600_000},
    }
    facts = fact_builder.build_risk_management_facts(
        trade, portfolio, same_day_trade_count=12, now=datetime(2026, 10, 5, 12, 0)
    )
    result = engine.evaluate_rule_group("risk_management", facts)

    assert "risk_management.position_limit_check" in result["rules_fired"]
    assert "risk_management.concentration_risk_check" in result["rules_fired"]
    assert "risk_management.high_frequency_trading_detection" in result["rules_fired"]
    assert "risk_management.market_hours_check" not in result["rules_fired"]


def test_risk_management_group_outside_business_hours_triggers_overnight_and_market_hours():
    engine = RuleEngine()
    trade = {"tradeId": "T4", "securityId": "SEC2", "tradeValue": 6_000_000, "counterpartyId": "CP2"}
    portfolio = {
        "portfolioId": "P2",
        "totalExposure": 0,
        "exposureLimit": 100_000_000,
        "concentrationLimit": 500_000,
        "availableCash": 1_000_000,
    }
    facts = fact_builder.build_risk_management_facts(
        trade, portfolio, same_day_trade_count=1, now=datetime(2026, 10, 5, 20, 0)
    )
    result = engine.evaluate_rule_group("risk_management", facts)

    assert "risk_management.overnight_risk_limit" in result["rules_fired"]
    assert "risk_management.market_hours_check" in result["rules_fired"]


def test_compliance_checks_group_triggers_kyc_aml_stale_and_sanctions():
    engine = RuleEngine()
    trade = {"tradeId": "T5", "counterpartyId": "C1", "tradeValue": 50000}
    client = {
        "clientId": "C1",
        "kycStatus": "PENDING",
        "amlRiskRating": "HIGH",
        "countryCode": "KP",
        "lastReviewDate": "2024-01-01",
    }
    facts = fact_builder.build_compliance_facts(trade, client, now=datetime(2026, 10, 5).date())
    result = engine.evaluate_rule_group("compliance_checks", facts)

    assert set(result["rules_fired"]) == {
        "compliance_checks.kyc_status_check",
        "compliance_checks.aml_high_risk_screening",
        "compliance_checks.stale_kyc_review",
        "compliance_checks.sanctioned_country_check",
    }


def test_compliance_checks_group_approved_client_does_not_trigger():
    engine = RuleEngine()
    trade = {"tradeId": "T6", "counterpartyId": "C2", "tradeValue": 500}
    client = {
        "clientId": "C2",
        "kycStatus": "APPROVED",
        "amlRiskRating": "LOW",
        "countryCode": "US",
        "lastReviewDate": "2026-09-01",
    }
    facts = fact_builder.build_compliance_facts(trade, client, now=datetime(2026, 10, 5).date())
    result = engine.evaluate_rule_group("compliance_checks", facts)

    assert result["rules_fired"] == []


def test_settlement_processing_group_triggers_cash_and_cutoff():
    engine = RuleEngine()
    trade = {"tradeId": "T7", "tradeType": "EQUITY", "tradeValue": 2_000_000, "securityId": "SEC3"}
    settlement = {"settlementId": "S1", "cutoffTime": "2026-10-05T10:00:00"}
    facts = fact_builder.build_settlement_facts(trade, settlement, now=datetime(2026, 10, 5, 12, 0))
    # Cash availability needs a portfolio namespace too; build it directly since
    # build_settlement_facts only covers trade+settlement+derived.
    facts["portfolio"] = {"available_cash": 1_000_000}
    result = engine.evaluate_rule_group("settlement_processing", facts)

    assert "settlement_processing.settlement_cutoff_time" in result["rules_fired"]
    assert "settlement_processing.cash_availability_check" in result["rules_fired"]
    assert "settlement_processing.corporate_action_pending" not in result["rules_fired"]


def test_pricing_alerts_group_flags_variance_and_stale_data():
    now = datetime(2026, 10, 5, 15, 0)
    calculated = pricing_service.calculate_market_price(
        "REQ1", "AAPL", last_price=100.0, bid_price=94.0, ask_price=96.0, volume=5000, volatility=0.5
    )
    facts = pricing_service.build_pricing_alert_facts(
        calculated,
        last_price=100.0,
        market_data_timestamp=datetime(2026, 10, 5, 14, 15),
        now=now,
    )

    engine = RuleEngine()
    result = engine.evaluate_rule_group("pricing_alerts", facts)

    assert "pricing_alerts.price_variance_check" in result["rules_fired"]
    assert "pricing_alerts.stale_market_data_warning" in result["rules_fired"]


def test_pricing_alerts_group_from_raw_fact_builder():
    equity_request = {"symbol": "MSFT", "pricingMethod": "MARKET", "requestId": "REQ2"}
    market_data = {
        "symbol": "MSFT",
        "lastPrice": 50.0,
        "bidPrice": 49.9,
        "askPrice": 50.1,
        "volume": 50000,
        "volatility": 0.1,
        "timestamp": "2026-10-05T14:55:00",
    }
    facts = fact_builder.build_pricing_alert_facts(
        equity_request, market_data, now=datetime(2026, 10, 5, 15, 0)
    )

    engine = RuleEngine()
    result = engine.evaluate_rule_group("pricing_alerts", facts)

    # High volume, low volatility, fresh data, no liquidity/volatility
    # discount -> high confidence, low variance, no alerts expected.
    assert result["rules_fired"] == []


def test_jsonlogic_multiply_divide_and_if():
    from app.rules.jsonlogic import JsonLogicEvaluator

    evaluator = JsonLogicEvaluator()
    assert evaluator.evaluate({"*": [3, 4]}, {}) == 12
    assert evaluator.evaluate({"/": [10, 2]}, {}) == 5
    assert evaluator.evaluate({"if": [True, "yes", "no"]}, {}) == "yes"
    assert evaluator.evaluate({"if": [False, "yes", "no"]}, {}) == "no"


def test_loader_directory_scan_finds_all_ported_rules():
    from app.rules.loader import RuleLoader

    rule_ids = RuleLoader().list_rule_ids_by_tag("trade_validation", "1.0.0")
    assert len(rule_ids) == 4
    assert "trade_validation.large_trade_alert" in rule_ids


def test_camel_to_snake_round_trip_is_idempotent():
    data = {"tradeId": "T1", "tradeValue": 100, "already_snake": True}
    converted = fact_builder.to_snake_dict(data)
    assert converted == {"trade_id": "T1", "trade_value": 100, "already_snake": True}
    assert fact_builder.to_snake_dict(converted) == converted
