"""
Rules Engine API Endpoints for Otomeshon Custodian Banking Platform

Provides REST API endpoints for managing and executing Drools rules
for custodian banking operations including trade validation, risk management,
compliance checks, and settlement processing.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.endpoints.auth_unified import get_current_user
from app.core.database import get_db
from app.models.trade import Trade
from app.models.user import User
from app.services.drools_service import (
    DroolsService,
    RuleFact,
    RuleResult,
    get_drools_service,
)

router = APIRouter(prefix="/rules", tags=["Rules Engine"])

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


class RuleDeploymentRequest(BaseModel):
    """Request model for rule deployment"""

    rule_name: str = Field(..., description="Name of the rule set")
    rule_content: str = Field(..., description="DRL rule content")


class RuleValidationRequest(BaseModel):
    """Request model for rule validation"""

    rule_content: str = Field(..., description="DRL rule content to validate")


@router.get("/status", response_model=Dict[str, Any])
async def get_rules_status(
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get status of the rules engine and deployed rules

    Returns:
        Dict: Status information including deployed rules and engine health
    """
    try:
        async with drools_service:
            status = await drools_service.get_rule_status()
            return {
                "engine_status": "online" if drools_service.connected else "offline",
                "timestamp": datetime.now().isoformat(),
                "user": current_user.email,
                "rules_status": status,
            }
    except Exception as e:
        raise HTTPException(

            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rules status: {str(e)}",
        )


@router.post("/execute", response_model=RuleExecutionResponse)
async def execute_rules(
    request: RuleExecutionRequest,
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Execute rules against provided facts

    Args:
        request: Rule execution request with rule set and facts

    Returns:
        RuleExecutionResponse: Execution results
    """
    try:
        # Convert request facts to RuleFact objects
        rule_facts = []
        for i, fact_data in enumerate(request.facts):
            rule_fact = RuleFact(
                fact_type=fact_data.get("fact_type", "Unknown"),
                fact_id=fact_data.get("fact_id", f"fact_{i}"),
                data=fact_data.get("data", {}),
                timestamp=datetime.now(),
            )
            rule_facts.append(rule_fact)

        async with drools_service:
            result = await drools_service.execute_rules(
                rule_set=request.rule_set,
                facts=rule_facts,
                timeout_seconds=request.timeout_seconds,
            )

        return RuleExecutionResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule execution failed: {str(e)}",
        )


@router.post("/validate-trade", response_model=RuleExecutionResponse)
async def validate_trade(
    request: TradeValidationRequest,
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Execute trade validation rules against a specific trade

    Args:
        request: Trade validation request

    Returns:
        RuleExecutionResponse: Validation results
    """
    try:
        # Get trade from database
        trade = db.query(Trade).filter(Trade.id == request.trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trade {request.trade_id} not found",
            )

        async with drools_service:
            result = await drools_service.validate_trade(trade)

        return RuleExecutionResponse(**result.to_dict())

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
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Execute risk management rules for a trade

    Args:
        request: Risk check request

    Returns:
        RuleExecutionResponse: Risk check results
    """
    try:
        # Get trade from database
        trade = db.query(Trade).filter(Trade.id == request.trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trade {request.trade_id} not found",
            )

        async with drools_service:
            result = await drools_service.check_risk_limits(
                trade, request.portfolio_data
            )

        return RuleExecutionResponse(**result.to_dict())

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
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Execute compliance rules for a trade

    Args:
        request: Compliance check request

    Returns:
        RuleExecutionResponse: Compliance check results
    """
    try:
        # Get trade from database
        trade = db.query(Trade).filter(Trade.id == request.trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trade {request.trade_id} not found",
            )

        async with drools_service:
            result = await drools_service.check_compliance(trade, request.client_data)

        return RuleExecutionResponse(**result.to_dict())

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
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Execute settlement processing rules

    Args:
        request: Settlement processing request

    Returns:
        RuleExecutionResponse: Settlement processing results
    """
    try:
        # Get trade from database
        trade = db.query(Trade).filter(Trade.id == request.trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trade {request.trade_id} not found",
            )

        async with drools_service:
            result = await drools_service.process_settlement_rules(
                trade, request.settlement_data
            )

        return RuleExecutionResponse(**result.to_dict())

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Settlement processing failed: {str(e)}",
        )


@router.post("/deploy")
async def deploy_rules(
    request: RuleDeploymentRequest,
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Deploy new rules to the Drools runtime

    Args:
        request: Rule deployment request

    Returns:
        Dict: Deployment result
    """
    try:
        # Check user permissions (admin or manager required)
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to deploy rules",
            )

        async with drools_service:
            success = await drools_service.deploy_rules(
                rule_content=request.rule_content, rule_name=request.rule_name
            )

        if success:
            return {
                "status": "success",
                "message": f"Rules '{request.rule_name}' deployed successfully",
                "deployed_by": current_user.email,
                "deployment_time": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rule deployment failed",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule deployment error: {str(e)}",
        )


@router.post("/deploy-file")
async def deploy_rules_from_file(
    rule_name: str,
    file: UploadFile = File(..., description="DRL rule file"),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Deploy rules from uploaded DRL file

    Args:
        rule_name: Name for the rule set
        file: Uploaded DRL file

    Returns:
        Dict: Deployment result
    """
    try:
        # Check user permissions
        if current_user.role not in ["admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to deploy rules",
            )

        # Validate file type
        if not file.filename.endswith(".drl"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a .drl file",
            )

        # Read file content
        rule_content = await file.read()
        rule_content_str = rule_content.decode("utf-8")

        async with drools_service:
            success = await drools_service.deploy_rules(
                rule_content=rule_content_str, rule_name=rule_name
            )

        if success:
            return {
                "status": "success",
                "message": f"Rules '{rule_name}' deployed from file '{file.filename}'",
                "deployed_by": current_user.email,
                "deployment_time": datetime.now().isoformat(),
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rule deployment failed",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule deployment error: {str(e)}",
        )


@router.post("/validate", response_model=Dict[str, Any])
async def validate_rule_syntax(
    request: RuleValidationRequest,
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user),
):
    """
    Validate DRL rule syntax without deploying

    Args:
        request: Rule validation request

    Returns:
        Dict: Validation results
    """
    try:
        async with drools_service:
            validation_result = await drools_service.validate_rule_syntax(
                request.rule_content
            )

        return {
            **validation_result,
            "validated_by": current_user.email,
            "validation_time": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule validation failed: {str(e)}",
        )


@router.get("/templates")
async def get_rule_templates(current_user: User = Depends(get_current_user)):
    """
    Get predefined rule templates for custodian banking operations

    Returns:
        Dict: Available rule templates
    """
    try:
        templates = {
            "trade-validation": {
                "name": "Trade Validation Rules",
                "description": "Basic trade validation rules for custodian operations",
                "template": """
package com.otomeshon.custodian.rules

import com.otomeshon.custodian.model.Trade

rule "Trade Amount Validation"
    when
        $trade : Trade(tradeValue > 1000000)
    then
        $trade.setRequiresApproval(true);
        $trade.setPriority("HIGH");
        insert(new Alert("Large Trade Alert", $trade.getTradeId()));
end

rule "Settlement Date Validation"
    when
        $trade : Trade(settlementDate < tradeDate)
    then
        $trade.setStatus("VALIDATION_FAILED");
        insert(new ValidationError("Invalid settlement date", $trade.getTradeId()));
end
                """,
            },
            "risk-management": {
                "name": "Risk Management Rules",
                "description": "Risk limit and exposure monitoring rules",
                "template": """
package com.otomeshon.custodian.rules

import com.otomeshon.custodian.model.Trade
import com.otomeshon.custodian.model.Portfolio

rule "Position Limit Check"
    when
        $trade : Trade()
        $portfolio : Portfolio(totalExposure + $trade.tradeValue > exposureLimit)
    then
        $trade.setStatus("RISK_LIMIT_EXCEEDED");
        insert(new RiskAlert("Position limit exceeded", $trade.getTradeId()));
end

rule "Concentration Risk"
    when
        $trade : Trade()
        $portfolio : Portfolio(getSecurityExposure($trade.securityId) > concentrationLimit)
    then
        $trade.setRequiresRiskReview(true);
        insert(new RiskAlert("Concentration limit exceeded", $trade.getTradeId()));
end
                """,
            },
            "compliance-checks": {
                "name": "Compliance Rules",
                "description": "Regulatory compliance and KYC rules",
                "template": """
package com.otomeshon.custodian.rules

import com.otomeshon.custodian.model.Trade
import com.otomeshon.custodian.model.Client

rule "KYC Status Check"
    when
        $trade : Trade()
        $client : Client(clientId == $trade.counterpartyId, kycStatus != "APPROVED")
    then
        $trade.setStatus("COMPLIANCE_HOLD");
        insert(new ComplianceAlert("KYC not approved", $trade.getTradeId()));
end

rule "AML Screening"
    when
        $trade : Trade(tradeValue > 10000)
        $client : Client(clientId == $trade.counterpartyId, amlRiskRating == "HIGH")
    then
        $trade.setRequiresAmlReview(true);
        insert(new ComplianceAlert("AML review required", $trade.getTradeId()));
end
                """,
            },
        }

        return {
            "templates": templates,
            "total_templates": len(templates),
            "requested_by": current_user.email,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule templates: {str(e)}",
        )


@router.get("/catalog")
async def get_rules_catalog(current_user: User = Depends(get_current_user)):
    """
    Get catalog of all available Drools rules

    Returns:
        Dict: Complete catalog of rules organized by category
    """
    try:
        catalog = {
            "trade_validation": {
                "category": "Trade Validation",
                "description": "Rules for validating trade data and ensuring data integrity",
                "rules": [
                    {
                        "name": "Large Trade Alert",
                        "description": "Flags trades exceeding $1M for approval",
                        "salience": 100,
                        "trigger_condition": "tradeValue > $1,000,000",
                        "actions": [
                            "Set requires approval",
                            "Set priority to HIGH",
                            "Create alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "93-106",
                    },
                    {
                        "name": "Settlement Date Validation",
                        "description": "Ensures settlement date is not before trade date",
                        "salience": 90,
                        "trigger_condition": "settlementDate < tradeDate",
                        "actions": [
                            "Set status to VALIDATION_FAILED",
                            "Create validation error",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "108-119",
                    },
                    {
                        "name": "Weekend Settlement Check",
                        "description": "Alerts when settlement falls on weekend",
                        "salience": 80,
                        "trigger_condition": "settlementDate on weekend",
                        "actions": ["Create weekend settlement alert"],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "121-133",
                    },
                    {
                        "name": "Zero Price Validation",
                        "description": "Validates trade price is greater than zero",
                        "salience": 85,
                        "trigger_condition": "price <= 0",
                        "actions": [
                            "Set status to VALIDATION_FAILED",
                            "Create validation error",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "135-146",
                    },
                ],
            },
            "risk_management": {
                "category": "Risk Management",
                "description": "Rules for monitoring and controlling trading risks",
                "rules": [
                    {
                        "name": "Position Limit Check",
                        "description": "Monitors portfolio exposure against limits",
                        "salience": 75,
                        "trigger_condition": "totalExposure + tradeValue > exposureLimit",
                        "actions": [
                            "Set status to RISK_LIMIT_EXCEEDED",
                            "Require risk review",
                            "Create risk alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "152-169",
                    },
                    {
                        "name": "Concentration Risk Check",
                        "description": "Monitors security concentration limits",
                        "salience": 70,
                        "trigger_condition": "securityExposure > concentrationLimit",
                        "actions": [
                            "Require risk review",
                            "Create concentration risk alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "171-185",
                    },
                    {
                        "name": "Overnight Risk Limit",
                        "description": "Special approval for large trades outside business hours",
                        "salience": 65,
                        "trigger_condition": "tradeValue > $5M AND outside business hours",
                        "actions": [
                            "Require approval",
                            "Set priority to HIGH",
                            "Create overnight risk alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "187-201",
                    },
                ],
            },
            "compliance": {
                "category": "Compliance & KYC",
                "description": "Rules for regulatory compliance and client verification",
                "rules": [
                    {
                        "name": "KYC Status Check",
                        "description": "Verifies client KYC approval status",
                        "salience": 95,
                        "trigger_condition": "client kycStatus != APPROVED",
                        "actions": [
                            "Set status to COMPLIANCE_HOLD",
                            "Create compliance alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "207-220",
                    },
                    {
                        "name": "AML High Risk Screening",
                        "description": "Screens high-risk clients for large trades",
                        "salience": 90,
                        "trigger_condition": "tradeValue > $10K AND amlRiskRating = HIGH",
                        "actions": ["Require AML review", "Create compliance alert"],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "222-235",
                    },
                    {
                        "name": "Stale KYC Review",
                        "description": "Identifies clients with outdated KYC reviews",
                        "salience": 60,
                        "trigger_condition": "lastReviewDate > 1 year ago",
                        "actions": ["Require approval", "Create stale KYC alert"],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "237-251",
                    },
                    {
                        "name": "Sanctioned Country Check",
                        "description": "Blocks trades from sanctioned countries",
                        "salience": 100,
                        "trigger_condition": "client from sanctioned country",
                        "actions": [
                            "Set status to COMPLIANCE_BLOCKED",
                            "Create sanctions alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "253-267",
                    },
                ],
            },
            "settlement": {
                "category": "Settlement & Operations",
                "description": "Rules for settlement processing and operational controls",
                "rules": [
                    {
                        "name": "Cash Availability Check",
                        "description": "Verifies sufficient cash for settlement",
                        "salience": 70,
                        "trigger_condition": "availableCash < tradeValue",
                        "actions": [
                            "Require approval",
                            "Create insufficient cash alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "273-288",
                    },
                    {
                        "name": "Settlement Cutoff Time",
                        "description": "Checks trade submission against cutoff times",
                        "salience": 80,
                        "trigger_condition": "currentTime > cutoffTime",
                        "actions": ["Create settlement cutoff alert"],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "290-303",
                    },
                    {
                        "name": "Corporate Action Pending",
                        "description": "Identifies securities with pending corporate actions",
                        "salience": 75,
                        "trigger_condition": "hasPendingCorporateAction = true",
                        "actions": [
                            "Require approval",
                            "Create corporate action alert",
                        ],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "305-318",
                    },
                ],
            },
            "market_timing": {
                "category": "Market Hours & Timing",
                "description": "Rules for market hours and trading frequency monitoring",
                "rules": [
                    {
                        "name": "Market Hours Check",
                        "description": "Monitors trades executed outside market hours",
                        "salience": 50,
                        "trigger_condition": "!isMarketOpen",
                        "actions": ["Create outside market hours alert"],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "324-336",
                    },
                    {
                        "name": "High Frequency Trading Detection",
                        "description": "Detects high-frequency trading patterns",
                        "salience": 80,
                        "trigger_condition": ">=10 trades per day from same counterparty",
                        "actions": ["Require approval", "Create HFT detection alert"],
                        "file": "custodian-banking-rules.drl",
                        "line_range": "338-355",
                    },
                ],
            },
            "pricing": {
                "category": "Pricing & Valuation",
                "description": "Rules for equity pricing and valuation calculations",
                "rules": [
                    {
                        "name": "Equity Price Calculator",
                        "description": "Calculates equity prices using market data and adjustments",
                        "salience": 50,
                        "trigger_condition": "Equity pricing request with market data",
                        "actions": [
                            "Calculate base price",
                            "Apply adjustments",
                            "Set calculated price",
                        ],
                        "file": "equity-pricing-rules.drl",
                        "line_range": "1-45",
                    },
                    {
                        "name": "Fair Value Adjustment",
                        "description": "Applies fair value adjustments to equity prices",
                        "salience": 40,
                        "trigger_condition": "Price variance > threshold",
                        "actions": [
                            "Calculate adjustment",
                            "Apply fair value correction",
                        ],
                        "file": "equity-pricing-rules.drl",
                        "line_range": "47-65",
                    },
                ],
            },
        }

        # Calculate summary statistics
        total_rules = sum(len(category["rules"]) for category in catalog.values())
        categories_count = len(catalog)

        return {
            "catalog": catalog,
            "summary": {
                "total_rules": total_rules,
                "total_categories": categories_count,
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
    """
    Get rules for a specific category

    Args:
        category: Category name (trade_validation, risk_management, etc.)

    Returns:
        Dict: Rules in the specified category
    """
    try:
        # Get full catalog
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
    """
    Search rules by name, description, or trigger condition

    Args:
        query: Search query string
        category: Optional category filter

    Returns:
        Dict: Matching rules
    """
    try:
        # Get full catalog
        full_catalog_response = await get_rules_catalog(current_user)
        catalog = full_catalog_response["catalog"]

        matching_rules = []
        query_lower = query.lower()

        for cat_name, cat_data in catalog.items():
            # Skip if category filter specified and doesn't match
            if category and cat_name != category:
                continue

            for rule in cat_data["rules"]:
                # Search in name, description, and trigger condition
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
