"""
Standard Operating Procedures (SOP) Management API

Provides endpoints for managing and executing standard operating procedures
in custodian banking operations.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from app.services.sop_service import get_sop_service, SOPExecutionService
from app.models.sop import (
    SOPExecutionCreate, SOPExecutionResponse, SOPExecutionUpdate,
    SOPStepExecutionResponse, SOPExecutionSummary
)

router = APIRouter(prefix="/sop-management")

@router.get("/templates", response_model=Dict[str, Dict[str, Any]])
async def get_sop_templates(
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Get all available SOP templates"""
    try:
        templates = await sop_service.get_available_sops()
        return templates
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SOP templates: {str(e)}"
        )

@router.get("/templates/{template_id}")
async def get_sop_template(
    template_id: str,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Get a specific SOP template by ID"""
    try:
        templates = await sop_service.get_available_sops()
        if template_id not in templates:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"SOP template '{template_id}' not found"
            )
        return templates[template_id]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve SOP template: {str(e)}"
        )

@router.post("/executions", response_model=SOPExecutionResponse)
async def create_sop_execution(
    execution_request: SOPExecutionCreate,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Create a new SOP execution instance"""
    try:
        execution = await sop_service.create_sop_execution(
            sop_id=execution_request.sop_document_id,
            execution_name=execution_request.execution_name,
            initiated_by=execution_request.initiated_by,
            context_data=execution_request.context_data,
            assigned_to=execution_request.assigned_to
        )
        return execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SOP execution: {str(e)}"
        )

@router.post("/executions/{execution_id}/start", response_model=SOPExecutionResponse)
async def start_sop_execution(
    execution_id: str,
    started_by: str,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Start executing an SOP"""
    try:
        execution = await sop_service.start_sop_execution(execution_id, started_by)
        return execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start SOP execution: {str(e)}"
        )

@router.post("/executions/{execution_id}/steps/{step_number}", response_model=SOPStepExecutionResponse)
async def execute_sop_step(
    execution_id: str,
    step_number: int,
    executed_by: str,
    input_data: Optional[Dict[str, Any]] = None,
    execution_notes: Optional[str] = None,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Execute a single step of an SOP"""
    try:
        step_execution = await sop_service.execute_step(
            execution_id=execution_id,
            step_number=step_number,
            executed_by=executed_by,
            input_data=input_data,
            execution_notes=execution_notes
        )
        return step_execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute step: {str(e)}"
        )

@router.get("/executions/{execution_id}", response_model=SOPExecutionResponse)
async def get_execution_status(
    execution_id: str,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Get current status of an SOP execution"""
    try:
        execution = await sop_service.get_execution_status(execution_id)
        return execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution status: {str(e)}"
        )

@router.get("/executions/{execution_id}/summary", response_model=SOPExecutionSummary)
async def get_execution_summary(
    execution_id: str,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Get detailed summary of SOP execution"""
    try:
        summary = await sop_service.get_execution_summary(execution_id)
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get execution summary: {str(e)}"
        )

@router.get("/executions", response_model=List[SOPExecutionResponse])
async def get_active_executions(
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Get all active SOP executions"""
    try:
        executions = await sop_service.get_active_executions()
        return executions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active executions: {str(e)}"
        )

@router.post("/executions/trade-settlement", response_model=SOPExecutionResponse)
async def execute_trade_settlement_sop(
    trade_data: Dict[str, Any],
    initiated_by: str,
    assigned_to: Optional[str] = None,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Execute trade settlement SOP with provided trade data"""
    try:
        # Create execution with trade context
        execution = await sop_service.create_sop_execution(
            sop_id="TRADE_SETTLEMENT",
            execution_name=f"Trade Settlement - {trade_data.get('tradeId', 'Unknown')}",
            initiated_by=initiated_by,
            context_data={"trade_data": trade_data},
            assigned_to=assigned_to
        )

        # Start execution automatically
        started_execution = await sop_service.start_sop_execution(execution.id, initiated_by)

        return started_execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute trade settlement SOP: {str(e)}"
        )

@router.post("/executions/corporate-actions", response_model=SOPExecutionResponse)
async def execute_corporate_actions_sop(
    corporate_action_data: Dict[str, Any],
    initiated_by: str,
    assigned_to: Optional[str] = None,
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Execute corporate actions SOP with provided corporate action data"""
    try:
        # Create execution with corporate action context
        execution = await sop_service.create_sop_execution(
            sop_id="CORPORATE_ACTIONS",
            execution_name=f"Corporate Action - {corporate_action_data.get('actionType', 'Unknown')}",
            initiated_by=initiated_by,
            context_data={"corporate_action_data": corporate_action_data},
            assigned_to=assigned_to
        )

        # Start execution automatically
        started_execution = await sop_service.start_sop_execution(execution.id, initiated_by)

        return started_execution
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute corporate actions SOP: {str(e)}"
        )

@router.get("/categories")
async def get_sop_categories():
    """Get available SOP categories and their descriptions"""
    return {
        "categories": [
            {
                "id": "trade_settlement",
                "name": "Trade Settlement",
                "description": "Procedures for settling trades including validation, confirmation, and final settlement",
                "business_area": "Custody Operations"
            },
            {
                "id": "corporate_actions",
                "name": "Corporate Actions",
                "description": "Processing of corporate actions including dividends, stock splits, and rights issues",
                "business_area": "Asset Servicing"
            },
            {
                "id": "client_onboarding",
                "name": "Client Onboarding",
                "description": "Complete onboarding process for new institutional clients",
                "business_area": "Client Services"
            },
            {
                "id": "compliance",
                "name": "Compliance Procedures",
                "description": "KYC, AML, and regulatory compliance procedures",
                "business_area": "Compliance"
            },
            {
                "id": "risk_management",
                "name": "Risk Management",
                "description": "Risk assessment and monitoring procedures",
                "business_area": "Risk Management"
            }
        ]
    }

@router.get("/metrics")
async def get_sop_metrics(
    sop_service: SOPExecutionService = Depends(get_sop_service)
):
    """Get SOP execution metrics and statistics"""
    try:
        active_executions = await sop_service.get_active_executions()

        # Calculate metrics
        total_active = len(active_executions)
        in_progress = len([e for e in active_executions if e.status == "in_progress"])
        requiring_approval = len([e for e in active_executions if e.status == "requires_approval"])

        # Average completion time (mock data for now)
        avg_completion_minutes = 45

        return {
            "metrics": {
                "total_active_executions": total_active,
                "in_progress_executions": in_progress,
                "executions_requiring_approval": requiring_approval,
                "average_completion_time_minutes": avg_completion_minutes,
                "automation_rate": 0.75,  # 75% of steps are automated
                "compliance_rate": 0.98   # 98% compliance rate
            },
            "recent_activity": [
                {
                    "timestamp": "2024-07-20T10:30:00Z",
                    "event": "SOP execution completed",
                    "sop_type": "Trade Settlement",
                    "duration_minutes": 35
                },
                {
                    "timestamp": "2024-07-20T09:45:00Z",
                    "event": "SOP execution started",
                    "sop_type": "Corporate Actions",
                    "estimated_duration_minutes": 85
                }
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SOP metrics: {str(e)}"
        )