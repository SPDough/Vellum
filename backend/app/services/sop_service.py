"""
Standard Operating Procedures (SOP) Service

Manages the execution of standard operating procedures for custodian banking operations.
Integrates with the workflow execution system and provides step-by-step guidance for operations staff.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from app.models.sop import (
    SOPDocument, SOPStep, SOPExecution, SOPStepExecution,
    SOPExecutionStatus, SOPStepExecutionStatus, SOPTemplateLibrary,
    SOPExecutionCreate, SOPExecutionResponse, SOPStepExecutionResponse,
    SOPExecutionSummary
)

logger = logging.getLogger(__name__)

class SOPExecutionService:
    """Service for managing SOP execution and step tracking"""

    def __init__(self):
        self.active_executions: Dict[str, SOPExecution] = {}
        self.execution_history: List[SOPExecution] = []
        self.sop_templates = SOPTemplateLibrary.get_all_templates()

    async def get_available_sops(self) -> Dict[str, Dict[str, Any]]:
        """Get all available SOP templates"""
        return self.sop_templates

    async def create_sop_execution(
        self,
        sop_id: str,
        execution_name: str,
        initiated_by: str,
        context_data: Optional[Dict[str, Any]] = None,
        assigned_to: Optional[str] = None
    ) -> SOPExecutionResponse:
        """Create a new SOP execution instance"""

        if sop_id not in self.sop_templates:
            raise ValueError(f"SOP template '{sop_id}' not found")

        sop_template = self.sop_templates[sop_id]
        execution_id = f"SOP_EXEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Calculate estimated duration
        estimated_duration = sum(
            step.get("estimated_duration_minutes", 0)
            for step in sop_template["steps"]
        )

        # Create execution record
        execution = SOPExecution(
            id=execution_id,
            sop_document_id=sop_id,
            execution_name=execution_name,
            status=SOPExecutionStatus.NOT_STARTED,
            initiated_by=initiated_by,
            assigned_to=assigned_to or initiated_by,
            estimated_duration_minutes=estimated_duration,
            context_data=context_data or {},
            completed_steps=[],
            failed_steps=[],
            requires_approval=any(step.get("is_decision_point", False) for step in sop_template["steps"]),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            execution_log=[]
        )

        self.active_executions[execution_id] = execution

        # Log creation
        await self._log_execution_event(
            execution_id,
            "EXECUTION_CREATED",
            f"SOP execution created for template {sop_id}"
        )

        logger.info(f"Created SOP execution {execution_id} for template {sop_id}")

        return SOPExecutionResponse(
            id=execution.id,
            sop_document_id=execution.sop_document_id,
            execution_name=execution.execution_name,
            status=execution.status,
            initiated_by=execution.initiated_by,
            assigned_to=execution.assigned_to,
            estimated_duration_minutes=execution.estimated_duration_minutes,
            requires_approval=execution.requires_approval,
            created_at=execution.created_at
        )

    async def start_sop_execution(self, execution_id: str, started_by: str) -> SOPExecutionResponse:
        """Start executing an SOP"""

        if execution_id not in self.active_executions:
            raise ValueError(f"SOP execution '{execution_id}' not found")

        execution = self.active_executions[execution_id]

        if execution.status != SOPExecutionStatus.NOT_STARTED:
            raise ValueError(f"SOP execution is already {execution.status}")

        # Update execution status
        execution.status = SOPExecutionStatus.IN_PROGRESS
        execution.start_time = datetime.utcnow()
        execution.updated_at = datetime.utcnow()

        # Get SOP template to find first step
        sop_template = self.sop_templates[execution.sop_document_id]
        first_step = min(sop_template["steps"], key=lambda s: s["step_number"])
        execution.current_step_id = f"step_{first_step['step_number']}"

        await self._log_execution_event(
            execution_id,
            "EXECUTION_STARTED",
            f"SOP execution started by {started_by}"
        )

        logger.info(f"Started SOP execution {execution_id}")

        return await self.get_execution_status(execution_id)

    async def execute_step(
        self,
        execution_id: str,
        step_number: int,
        executed_by: str,
        input_data: Optional[Dict[str, Any]] = None,
        execution_notes: Optional[str] = None
    ) -> SOPStepExecutionResponse:
        """Execute a single step of an SOP"""

        if execution_id not in self.active_executions:
            raise ValueError(f"SOP execution '{execution_id}' not found")

        execution = self.active_executions[execution_id]
        sop_template = self.sop_templates[execution.sop_document_id]

        # Find the step
        step_template = next(
            (s for s in sop_template["steps"] if s["step_number"] == step_number),
            None
        )

        if not step_template:
            raise ValueError(f"Step {step_number} not found in SOP")

        step_id = f"step_{step_number}"
        step_execution_id = f"{execution_id}_{step_id}_{uuid.uuid4().hex[:8]}"

        start_time = datetime.utcnow()

        # Create step execution record
        step_execution = SOPStepExecution(
            id=step_execution_id,
            sop_execution_id=execution_id,
            step_id=step_id,
            status=SOPStepExecutionStatus.IN_PROGRESS,
            started_by=executed_by,
            start_time=start_time,
            input_data=input_data or {},
            execution_notes=execution_notes,
            created_at=start_time,
            updated_at=start_time
        )

        try:
            # Execute step based on type
            if step_template.get("is_automated", False):
                output_data = await self._execute_automated_step(
                    step_template,
                    input_data or {},
                    execution.context_data
                )
            else:
                output_data = await self._execute_manual_step(
                    step_template,
                    input_data or {},
                    execution_notes
                )

            # Complete the step
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds() / 60  # minutes

            step_execution.status = SOPStepExecutionStatus.COMPLETED
            step_execution.end_time = end_time
            step_execution.actual_duration_minutes = int(duration)
            step_execution.output_data = output_data
            step_execution.updated_at = end_time

            # Update execution progress
            execution.completed_steps.append(step_id)
            execution.current_step_id = self._get_next_step_id(sop_template, step_number)
            execution.updated_at = end_time

            # Check if execution is complete
            if len(execution.completed_steps) == len(sop_template["steps"]):
                execution.status = SOPExecutionStatus.COMPLETED
                execution.end_time = end_time
                execution.actual_duration_minutes = int(
                    (end_time - execution.start_time).total_seconds() / 60
                )

            await self._log_execution_event(
                execution_id,
                "STEP_COMPLETED",
                f"Step {step_number} ({step_template['step_title']}) completed by {executed_by}"
            )

            logger.info(f"Completed step {step_number} in execution {execution_id}")

        except Exception as e:
            # Handle step failure
            step_execution.status = SOPStepExecutionStatus.FAILED
            step_execution.error_message = str(e)
            step_execution.end_time = datetime.utcnow()
            step_execution.updated_at = datetime.utcnow()

            execution.failed_steps.append(step_id)
            execution.updated_at = datetime.utcnow()

            await self._log_execution_event(
                execution_id,
                "STEP_FAILED",
                f"Step {step_number} failed: {str(e)}"
            )

            logger.error(f"Step {step_number} failed in execution {execution_id}: {str(e)}")

            raise

        return SOPStepExecutionResponse(
            id=step_execution.id,
            sop_execution_id=step_execution.sop_execution_id,
            step_id=step_execution.step_id,
            status=step_execution.status,
            started_by=step_execution.started_by,
            start_time=step_execution.start_time,
            end_time=step_execution.end_time,
            actual_duration_minutes=step_execution.actual_duration_minutes,
            execution_notes=step_execution.execution_notes,
            error_message=step_execution.error_message,
            retry_count=step_execution.retry_count,
            created_at=step_execution.created_at
        )

    async def get_execution_status(self, execution_id: str) -> SOPExecutionResponse:
        """Get current status of an SOP execution"""

        if execution_id not in self.active_executions:
            raise ValueError(f"SOP execution '{execution_id}' not found")

        execution = self.active_executions[execution_id]
        sop_template = self.sop_templates[execution.sop_document_id]

        # Calculate completion percentage
        total_steps = len(sop_template["steps"])
        completed_steps = len(execution.completed_steps)
        completion_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        return SOPExecutionResponse(
            id=execution.id,
            sop_document_id=execution.sop_document_id,
            execution_name=execution.execution_name,
            status=execution.status,
            initiated_by=execution.initiated_by,
            assigned_to=execution.assigned_to,
            start_time=execution.start_time,
            end_time=execution.end_time,
            estimated_duration_minutes=execution.estimated_duration_minutes,
            actual_duration_minutes=execution.actual_duration_minutes,
            current_step_id=execution.current_step_id,
            completion_percentage=completion_percentage,
            requires_approval=execution.requires_approval,
            approval_status=execution.approval_status,
            created_at=execution.created_at
        )

    async def get_execution_summary(self, execution_id: str) -> SOPExecutionSummary:
        """Get detailed summary of SOP execution"""

        if execution_id not in self.active_executions:
            raise ValueError(f"SOP execution '{execution_id}' not found")

        execution = self.active_executions[execution_id]
        sop_template = self.sop_templates[execution.sop_document_id]

        total_steps = len(sop_template["steps"])
        completed_steps = len(execution.completed_steps)
        failed_steps = len(execution.failed_steps)
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0

        # Calculate estimated time remaining
        remaining_steps = total_steps - completed_steps
        avg_step_duration = sum(
            s.get("estimated_duration_minutes", 0)
            for s in sop_template["steps"]
        ) / total_steps if total_steps > 0 else 0
        estimated_time_remaining = int(remaining_steps * avg_step_duration) if remaining_steps > 0 else None

        # Check for risk alerts
        risk_alerts = []
        if failed_steps > 0:
            risk_alerts.append(f"{failed_steps} step(s) failed")
        if execution.requires_approval and execution.approval_status != "APPROVED":
            risk_alerts.append("Requires management approval")

        return SOPExecutionSummary(
            execution_id=execution.id,
            sop_title=sop_template["title"],
            status=execution.status,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            progress_percentage=progress_percentage,
            estimated_time_remaining_minutes=estimated_time_remaining,
            compliance_status="COMPLIANT" if failed_steps == 0 else "NON_COMPLIANT",
            risk_alerts=risk_alerts
        )

    async def get_active_executions(self) -> List[SOPExecutionResponse]:
        """Get all active SOP executions"""

        active_executions = []
        for execution_id, execution in self.active_executions.items():
            if execution.status in [SOPExecutionStatus.IN_PROGRESS, SOPExecutionStatus.REQUIRES_APPROVAL]:
                status_response = await self.get_execution_status(execution_id)
                active_executions.append(status_response)

        return active_executions

    async def _execute_automated_step(
        self,
        step_template: Dict[str, Any],
        input_data: Dict[str, Any],
        context_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an automated step using appropriate automation tool"""

        automation_tool = step_template.get("automation_tool", "Generic")
        step_title = step_template["step_title"]

        # Simulate automation execution
        await asyncio.sleep(0.1)  # Simulate processing time

        output_data = {
            "automation_tool": automation_tool,
            "execution_method": "automated",
            "step_result": "completed",
            "processing_time_ms": 100,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add tool-specific results
        if automation_tool == "Rules Engine":
            output_data.update({
                "rules_executed": ["validation_rule_1", "limit_check_rule"],
                "rules_passed": True,
                "alerts_generated": []
            })
        elif automation_tool == "LangGraph":
            output_data.update({
                "agent_response": f"Successfully processed {step_title}",
                "confidence_score": 0.95,
                "documents_generated": [f"{step_title.lower().replace(' ', '_')}_document.pdf"]
            })
        elif automation_tool == "Monitoring System":
            output_data.update({
                "monitoring_status": "active",
                "alerts_count": 0,
                "system_health": "healthy"
            })

        logger.info(f"Automated step executed: {step_title} using {automation_tool}")
        return output_data

    async def _execute_manual_step(
        self,
        step_template: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_notes: Optional[str]
    ) -> Dict[str, Any]:
        """Execute a manual step with user guidance"""

        step_title = step_template["step_title"]

        output_data = {
            "execution_method": "manual",
            "step_result": "completed",
            "user_notes": execution_notes or "Step completed manually",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add decision point results if applicable
        if step_template.get("is_decision_point", False):
            output_data.update({
                "decision_made": "proceed",
                "decision_rationale": execution_notes or "Standard processing",
                "requires_review": True
            })

        logger.info(f"Manual step executed: {step_title}")
        return output_data

    def _get_next_step_id(self, sop_template: Dict[str, Any], current_step_number: int) -> Optional[str]:
        """Get the ID of the next step to execute"""

        next_step_number = current_step_number + 1
        next_step = next(
            (s for s in sop_template["steps"] if s["step_number"] == next_step_number),
            None
        )

        return f"step_{next_step['step_number']}" if next_step else None

    async def _log_execution_event(self, execution_id: str, event_type: str, message: str):
        """Log an event in the execution log"""

        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            if execution.execution_log is None:
                execution.execution_log = []

            execution.execution_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": event_type,
                "message": message
            })

            execution.updated_at = datetime.utcnow()


# Global service instance
_sop_service = None

def get_sop_service() -> SOPExecutionService:
    """Get the global SOP service instance"""
    global _sop_service
    if _sop_service is None:
        _sop_service = SOPExecutionService()
    return _sop_service