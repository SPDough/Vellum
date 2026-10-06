"""
Rules Engine API Endpoints for Vellum/Otomeshon Custodian Banking Platform

Provides REST API endpoints for executing Vellum's native JSON-first
deterministic rules for custodian banking operations including trade
validation, risk management, compliance checks, settlement processing, and
equity pricing alerts. Migrated off Drools/Kogito — see
docs/contracts/RULE_DEFINITION_CONTRACT.md.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.endpoints.auth_unified import get_current_user
from app.core.database import get_sync_db
from app.models.trade import Trade
from app.models.user import User
from app.rules.engine import RULE_SET_TO_GROUP, RuleEngine, get_rule_engine
from app.rules.fact_builder import (
    build_compliance_facts,
    build_pricing_alert_facts,
    build_risk_management_facts,
    build_settlement_facts,
    build_trade_validation_facts,
)
from app.rules.loader import NON_RULE_FILES, RuleLoader

router = APIRouter(prefix="/rules", tags=["Rules Engine"])

CATEGORY_LABELS = {
    "trade_validation": "Trade Validation",
    "risk_management": "Risk Management",
    "compliance_checks": "Compliance & KYC",
    "settlement_processing": "Settlement & Operations",
    "pricing_alerts": "Pricing & Valuation",
    "custody": "Custody",
    "reconciliation": "Reconciliation",
}

SEVERITY_TO_SALIENCE = {"critical": 100, "high": 85, "medium": 60, "low": 30}


# Pydantic models for request/response


class RuleExecutionRequest(BaseModel):
    """Request model for rule execution"""

    rule_set: str = Field(..., description="Name of the rule set to execute")
    facts: List[Dict[str, Any]] = Field(
        ..., description="Facts to evaluate against rules"
    )
    timeout_seconds: int = Field(
        default=30, ge=1, le=300, description="Execution timeout"
    )


class RuleExecutionResponse(BaseModel):
    """Response model for rule execution results"""

    rule_name: str
    status: str
    facts_processed: int
    rules_fired: List[str]
    actions_triggered: List[Dict[str, Any]]
    execution_time_ms: float
    error_message: Optional[str] = None


class TradeValidationRequest(BaseModel):
    """Request model for trade validation"""

    trade_id: int = Field(..., description="ID of the trade to validate")


class RiskCheckRequest(BaseModel):
    """Request model for risk limit checking"""

    trade_id: int = Field(..., description="ID of the trade to check")
    portfolio_data: Dict[str, Any] = Field(
        ..., description="Portfolio positions and limits"
    )


class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking"""

    trade_id: int = Field(..., description="ID of the trade to check")
    client_data: Dict[str, Any] = Field(
        ..., description="Client information and compliance status"
    )


class SettlementProcessingRequest(BaseModel):
    """Request model for settlement processing"""

    trade_id: int = Field(..., description="ID of the trade to settle")
    settlement_data: Dict[str, Any] = Field(
        ..., description="Settlement instructions and constraints"
    )


def _trade_to_dict(trade: Trade) -> Dict[str, Any]:
    return {
        "trade_id": trade.id,
        "trade_type": trade.trade_type,
        "counterparty_id": trade.counterparty_id,
        "security_id": trade.instrument_id,
        "quantity": float(trade.quantity) if trade.quantity is not None else None,
        "price": float(trade.price) if trade.price is not None else None,
        "trade_value": float(trade.trade_value) if trade.trade_value is not None else None,
        "currency": trade.currency,
        "trade_date": trade.trade_date.isoformat() if trade.trade_date else None,
        "settlement_date": trade.settlement_date.isoformat() if trade.settlement_date else None,
        "status": trade.status,
    }


def _same_day_trade_count(db: Session, trade: Trade) -> int:
    if not trade.trade_date:
        return 0
    day_start = datetime.combine(trade.trade_date.date(), datetime.min.time())
    day_end = datetime.combine(trade.trade_date.date(), datetime.max.time())
    return (
        db.query(Trade)
        .filter(
            Trade.counterparty_id == trade.counterparty_id,
            Trade.trade_date >= day_start,
            Trade.trade_date <= day_end,
        )
        .count()
    )


def _get_trade_or_404(db: Session, trade_id: Any) -> Trade:
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trade {trade_id} not found",
        )
    return trade


@router.get("/status", response_model=Dict[str, Any])
async def get_rules_status(
    rule_engine: RuleEngine = Depends(get_rule_engine),
    current_user: User = Depends(get_current_user),
):
    """Get status of the native rules engine and loaded rule versions."""
    try:
        versions = rule_engine.rule_registry.list_rule_versions()
        return {
            "engine_status": "online",
            "engine": "vellum-native-rule-engine",
            "timestamp": datetime.now().isoformat(),
            "user": current_user.email,
            "rule_versions": versions,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rules status: {str(e)}",
        )


@router.post("/execute", response_model=RuleExecutionResponse)
async def execute_rules(
    request: RuleExecutionRequest,
    rule_engine: RuleEngine = Depends(get_rule_engine),
    current_user: User = Depends(get_current_user),
):
    """Execute a named rule group against provided facts."""
    group = RULE_SET_TO_GROUP.get(request.rule_set)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown rule_set: {request.rule_set}. Valid values: {sorted(RULE_SET_TO_GROUP)}",
        )

    facts_by_type: Dict[str, Dict[str, Any]] = {
        fact.get("fact_type", ""): fact.get("data", {}) for fact in request.facts
    }

    try:
        if group == "trade_validation":
            facts = build_trade_validation_facts(facts_by_type.get("Trade", {}))
        elif group == "risk_management":
            facts = build_risk_management_facts(
                facts_by_type.get("Trade", {}), facts_by_type.get("Portfolio", {})
            )
        elif group == "compliance_checks":
            facts = build_compliance_facts(
                facts_by_type.get("Trade", {}), facts_by_type.get("Client", {})
            )
        elif group == "settlement_processing":
            facts = build_settlement_facts(
                facts_by_type.get("Trade", {}), facts_by_type.get("Settlement", {})
            )
        else:  # pricing_alerts
            facts = build_pricing_alert_facts(
                facts_by_type.get("EquityPricingRequest", {}), facts_by_type.get("MarketData", {})
            )

        result = rule_engine.evaluate_rule_group(group, facts)
        return RuleExecutionResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule execution failed: {str(e)}",
        )


@router.post("/validate-trade", response_model=RuleExecutionResponse)
async def validate_trade(
    request: TradeValidationRequest,
    db: Session = Depends(get_sync_db),
    rule_engine: RuleEngine = Depends(get_rule_engine),
    current_user: User = Depends(get_current_user),
):
    """Execute trade validation rules against a specific trade."""
    try:
        trade = _get_trade_or_404(db, request.trade_id)
        facts = build_trade_validation_facts(_trade_to_dict(trade))
        result = rule_engine.evaluate_rule_group("trade_validation", facts)
        return RuleExecutionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade validation failed: {str(e)}",
        )


@router.post("/check-risk", response_model=RuleExecutionResponse)
async def check_risk_limits(
    request: RiskCheckRequest,
    db: Session = Depends(get_sync_db),
    rule_engine: RuleEngine = Depends(get_rule_engine),
    current_user: User = Depends(get_current_user),
):
    """Execute risk management rules for a trade."""
    try:
        trade = _get_trade_or_404(db, request.trade_id)
        same_day_count = _same_day_trade_count(db, trade)
        facts = build_risk_management_facts(
            _trade_to_dict(trade), request.portfolio_data, same_day_trade_count=same_day_count
        )
        result = rule_engine.evaluate_rule_group("risk_management", facts)
        return RuleExecutionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk check failed: {str(e)}",
        )


@router.post("/check-compliance", response_model=RuleExecutionResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_sync_db),
    rule_engine: RuleEngine = Depends(get_rule_engine),
    current_user: User = Depends(get_current_user),
):
    """Execute compliance rules for a trade."""
    try:
        trade = _get_trade_or_404(db, request.trade_id)
        facts = build_compliance_facts(_trade_to_dict(trade), request.client_data)
        result = rule_engine.evaluate_rule_group("compliance_checks", facts)
        return RuleExecutionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}",
        )


@router.post("/process-settlement", response_model=RuleExecutionResponse)
async def process_settlement(
    request: SettlementProcessingRequest,
    db: Session = Depends(get_sync_db),
    rule_engine: RuleEngine = Depends(get_rule_engine),
    current_user: User = Depends(get_current_user),
):
    """Execute settlement processing rules."""
    try:
        trade = _get_trade_or_404(db, request.trade_id)
        facts = build_settlement_facts(_trade_to_dict(trade), request.settlement_data)
        result = rule_engine.evaluate_rule_group("settlement_processing", facts)
        return RuleExecutionResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Settlement processing failed: {str(e)}",
        )


def _load_rule_definitions() -> List[Dict[str, Any]]:
    rules_root = RuleLoader().rules_root / "1.0.0"
    definitions = []
    for path in sorted(rules_root.glob("*.json")):
        if path.name in NON_RULE_FILES:
            continue
        definitions.append(json.loads(path.read_text(encoding="utf-8")))
    return definitions


def _build_catalog() -> Dict[str, Any]:
    catalog: Dict[str, Any] = {}
    for definition in _load_rule_definitions():
        payload = definition["payload"]
        family = payload["rule_family"]
        bucket = catalog.setdefault(
            family,
            {
                "category": CATEGORY_LABELS.get(family, family.replace("_", " ").title()),
                "description": f"Deterministic rules for {CATEGORY_LABELS.get(family, family).lower()}.",
                "rules": [],
            },
        )

        outcome = payload["outcome"]
        actions = []
        if outcome.get("create_exception"):
            actions.append("Create exception")
        if outcome.get("create_reconciliation_break"):
            actions.append("Create reconciliation break")
        if outcome.get("open_workflow_case"):
            actions.append("Open workflow case")
        if outcome.get("require_approval"):
            actions.append("Require approval")
        actions.append(f"Result code: {outcome.get('result_code', '')}")

        bucket["rules"].append(
            {
                "name": payload["rule_name"],
                "description": payload.get("description", ""),
                "salience": SEVERITY_TO_SALIENCE.get(payload.get("severity", ""), 50),
                "trigger_condition": json.dumps(payload["predicate"]),
                "actions": actions,
                "file": f"contracts/rule-definition/{payload['version']}/{payload['rule_id']}.json",
                "line_range": "",
                "rule_id": payload["rule_id"],
                "status": payload["status"],
            }
        )
    return catalog


@router.get("/catalog")
async def get_rules_catalog(current_user: User = Depends(get_current_user)):
    """Get catalog of all available native rules, organized by rule family."""
    try:
        catalog = _build_catalog()
        total_rules = sum(len(category["rules"]) for category in catalog.values())

        return {
            "catalog": catalog,
            "summary": {
                "total_rules": total_rules,
                "total_categories": len(catalog),
                "categories": list(catalog.keys()),
            },
            "metadata": {
                "requested_by": current_user.email,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rules catalog: {str(e)}",
        )


@router.get("/catalog/{category}")
async def get_rules_by_category(
    category: str, current_user: User = Depends(get_current_user)
):
    """Get rules for a specific rule family."""
    try:
        full_catalog_response = await get_rules_catalog(current_user)
        catalog = full_catalog_response["catalog"]

        if category not in catalog:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category '{category}' not found",
            )

        return {
            "category": category,
            "rules": catalog[category],
            "count": len(catalog[category]["rules"]),
            "requested_by": current_user.email,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get category rules: {str(e)}",
        )


@router.get("/search")
async def search_rules(
    query: str,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Search rules by name, description, or trigger condition."""
    try:
        full_catalog_response = await get_rules_catalog(current_user)
        catalog = full_catalog_response["catalog"]

        matching_rules = []
        query_lower = query.lower()

        for cat_name, cat_data in catalog.items():
            if category and cat_name != category:
                continue

            for rule in cat_data["rules"]:
                searchable_text = " ".join(
                    [rule["name"], rule["description"], rule["trigger_condition"]]
                ).lower()

                if query_lower in searchable_text:
                    matching_rules.append(
                        {
                            **rule,
                            "category": cat_name,
                            "category_name": cat_data["category"],
                        }
                    )

        return {
            "query": query,
            "category_filter": category,
            "results": matching_rules,
            "count": len(matching_rules),
            "searched_by": current_user.email,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )
