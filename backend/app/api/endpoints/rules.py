"""
Rules Engine API Endpoints for Otomeshon Custodian Banking Platform

Provides REST API endpoints for managing and executing Drools rules
for custodian banking operations including trade validation, risk management,
compliance checks, and settlement processing.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.drools_service import get_drools_service, DroolsService, RuleFact, RuleResult
from app.models.trade import Trade
from app.models.user import User
from app.api.endpoints.auth_unified import get_current_user

router = APIRouter(prefix="/rules", tags=["Rules Engine"])

# Pydantic models for request/response

class RuleExecutionRequest(BaseModel):
    """Request model for rule execution"""
    rule_set: str = Field(..., description="Name of the rule set to execute")
    facts: List[Dict[str, Any]] = Field(..., description="Facts to evaluate against rules")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="Execution timeout")

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
    portfolio_data: Dict[str, Any] = Field(..., description="Portfolio positions and limits")

class ComplianceCheckRequest(BaseModel):
    """Request model for compliance checking"""
    trade_id: int = Field(..., description="ID of the trade to check")
    client_data: Dict[str, Any] = Field(..., description="Client information and compliance status")

class SettlementProcessingRequest(BaseModel):
    """Request model for settlement processing"""
    trade_id: int = Field(..., description="ID of the trade to settle")
    settlement_data: Dict[str, Any] = Field(..., description="Settlement instructions and constraints")

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
    current_user: User = Depends(get_current_user)
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
                "rules_status": status
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rules status: {str(e)}"
        )

@router.post("/execute", response_model=RuleExecutionResponse)
async def execute_rules(
    request: RuleExecutionRequest,
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                timestamp=datetime.now()
            )
            rule_facts.append(rule_fact)
        
        async with drools_service:
            result = await drools_service.execute_rules(
                rule_set=request.rule_set,
                facts=rule_facts,
                timeout_seconds=request.timeout_seconds
            )
        
        return RuleExecutionResponse(**result.to_dict())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule execution failed: {str(e)}"
        )

@router.post("/validate-trade", response_model=RuleExecutionResponse)
async def validate_trade(
    request: TradeValidationRequest,
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                detail=f"Trade {request.trade_id} not found"
            )
        
        async with drools_service:
            result = await drools_service.validate_trade(trade)
        
        return RuleExecutionResponse(**result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade validation failed: {str(e)}"
        )

@router.post("/check-risk", response_model=RuleExecutionResponse)
async def check_risk_limits(
    request: RiskCheckRequest,
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                detail=f"Trade {request.trade_id} not found"
            )
        
        async with drools_service:
            result = await drools_service.check_risk_limits(trade, request.portfolio_data)
        
        return RuleExecutionResponse(**result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk check failed: {str(e)}"
        )

@router.post("/check-compliance", response_model=RuleExecutionResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                detail=f"Trade {request.trade_id} not found"
            )
        
        async with drools_service:
            result = await drools_service.check_compliance(trade, request.client_data)
        
        return RuleExecutionResponse(**result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}"
        )

@router.post("/process-settlement", response_model=RuleExecutionResponse)
async def process_settlement(
    request: SettlementProcessingRequest,
    db: Session = Depends(get_db),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                detail=f"Trade {request.trade_id} not found"
            )
        
        async with drools_service:
            result = await drools_service.process_settlement_rules(trade, request.settlement_data)
        
        return RuleExecutionResponse(**result.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Settlement processing failed: {str(e)}"
        )

@router.post("/deploy")
async def deploy_rules(
    request: RuleDeploymentRequest,
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                detail="Insufficient permissions to deploy rules"
            )
        
        async with drools_service:
            success = await drools_service.deploy_rules(
                rule_content=request.rule_content,
                rule_name=request.rule_name
            )
        
        if success:
            return {
                "status": "success",
                "message": f"Rules '{request.rule_name}' deployed successfully",
                "deployed_by": current_user.email,
                "deployment_time": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rule deployment failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule deployment error: {str(e)}"
        )

@router.post("/deploy-file")
async def deploy_rules_from_file(
    rule_name: str,
    file: UploadFile = File(..., description="DRL rule file"),
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
                detail="Insufficient permissions to deploy rules"
            )
        
        # Validate file type
        if not file.filename.endswith('.drl'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a .drl file"
            )
        
        # Read file content
        rule_content = await file.read()
        rule_content_str = rule_content.decode('utf-8')
        
        async with drools_service:
            success = await drools_service.deploy_rules(
                rule_content=rule_content_str,
                rule_name=rule_name
            )
        
        if success:
            return {
                "status": "success",
                "message": f"Rules '{rule_name}' deployed from file '{file.filename}'",
                "deployed_by": current_user.email,
                "deployment_time": datetime.now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Rule deployment failed"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule deployment error: {str(e)}"
        )

@router.post("/validate", response_model=Dict[str, Any])
async def validate_rule_syntax(
    request: RuleValidationRequest,
    drools_service: DroolsService = Depends(get_drools_service),
    current_user: User = Depends(get_current_user)
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
            validation_result = await drools_service.validate_rule_syntax(request.rule_content)
        
        return {
            **validation_result,
            "validated_by": current_user.email,
            "validation_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rule validation failed: {str(e)}"
        )

@router.get("/templates")
async def get_rule_templates(
    current_user: User = Depends(get_current_user)
):
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
                """
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
                """
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
                """
            }
        }
        
        return {
            "templates": templates,
            "total_templates": len(templates),
            "requested_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rule templates: {str(e)}"
        )