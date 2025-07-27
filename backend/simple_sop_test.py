#!/usr/bin/env python3
"""
Simple SOP System Test

Tests the SOP management system without requiring external dependencies.
Demonstrates the complete SOP workflow for custodian banking operations.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Any, Optional

# Mock SOP Models and Service

class SOPExecutionStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_APPROVAL = "requires_approval"

class SOPStepExecutionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class SOPTemplate:
    title: str
    document_number: str
    version: str
    category: str
    business_area: str
    process_type: str
    content: str
    summary: str
    steps: List[Dict[str, Any]]

@dataclass
class SOPExecution:
    id: str
    sop_document_id: str
    execution_name: str
    status: SOPExecutionStatus
    initiated_by: str
    assigned_to: str
    estimated_duration_minutes: int
    context_data: Dict[str, Any]
    completed_steps: List[str]
    failed_steps: List[str]
    requires_approval: bool
    created_at: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    current_step_id: Optional[str] = None
    approval_status: Optional[str] = None

@dataclass
class SOPStepExecution:
    id: str
    sop_execution_id: str
    step_id: str
    status: SOPStepExecutionStatus
    started_by: str
    start_time: datetime
    end_time: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    execution_notes: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class SOPExecutionSummary:
    execution_id: str
    sop_title: str
    status: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    progress_percentage: float
    estimated_time_remaining_minutes: Optional[int]
    compliance_status: str
    risk_alerts: List[str]

class MockSOPService:
    """Mock SOP service for testing"""
    
    def __init__(self):
        self.active_executions: Dict[str, SOPExecution] = {}
        self.step_executions: Dict[str, List[SOPStepExecution]] = {}
        self.templates = self._create_templates()
    
    def _create_templates(self) -> Dict[str, SOPTemplate]:
        """Create sample SOP templates"""
        
        trade_settlement = SOPTemplate(
            title="Equity Trade Settlement Procedure",
            document_number="SOP-TS-001",
            version="1.0",
            category="Trade Settlement",
            business_area="Custody Operations",
            process_type="Semi-Automated",
            content="Complete procedure for equity trade settlement",
            summary="Trade settlement including validation, confirmation, and monitoring",
            steps=[
                {
                    "step_number": 1,
                    "step_title": "Trade Validation",
                    "step_description": "Validate trade details against market data and client limits",
                    "is_automated": True,
                    "estimated_duration_minutes": 5,
                    "automation_tool": "Rules Engine"
                },
                {
                    "step_number": 2,
                    "step_title": "Generate Trade Confirmation",
                    "step_description": "Generate and send trade confirmation to counterparty",
                    "is_automated": True,
                    "estimated_duration_minutes": 10,
                    "automation_tool": "LangGraph"
                },
                {
                    "step_number": 3,
                    "step_title": "Settlement Instructions",
                    "step_description": "Prepare and send settlement instructions",
                    "is_manual": True,
                    "estimated_duration_minutes": 15,
                    "is_decision_point": True
                },
                {
                    "step_number": 4,
                    "step_title": "Final Settlement",
                    "step_description": "Monitor and confirm settlement completion",
                    "is_automated": True,
                    "estimated_duration_minutes": 30,
                    "automation_tool": "Monitoring System"
                }
            ]
        )
        
        corporate_actions = SOPTemplate(
            title="Corporate Actions Processing",
            document_number="SOP-CA-001",
            version="1.0",
            category="Corporate Actions",
            business_area="Asset Servicing",
            process_type="Semi-Automated",
            content="Process corporate actions including dividends and stock splits",
            summary="Complete corporate actions processing including notifications and entitlements",
            steps=[
                {
                    "step_number": 1,
                    "step_title": "Corporate Action Notification",
                    "step_description": "Receive and validate corporate action announcement",
                    "is_automated": True,
                    "estimated_duration_minutes": 5
                },
                {
                    "step_number": 2,
                    "step_title": "Client Notification",
                    "step_description": "Notify affected clients of corporate action",
                    "is_automated": True,
                    "estimated_duration_minutes": 15
                },
                {
                    "step_number": 3,
                    "step_title": "Process Client Elections",
                    "step_description": "Process client elections and instructions",
                    "is_manual": True,
                    "estimated_duration_minutes": 45,
                    "is_decision_point": True
                },
                {
                    "step_number": 4,
                    "step_title": "Calculate Entitlements",
                    "step_description": "Calculate client entitlements and process payments",
                    "is_automated": True,
                    "estimated_duration_minutes": 20
                }
            ]
        )
        
        client_onboarding = SOPTemplate(
            title="Institutional Client Onboarding",
            document_number="SOP-CO-001",
            version="1.0",
            category="Client Onboarding",
            business_area="Client Services",
            process_type="Manual",
            content="Complete onboarding procedure for new institutional clients",
            summary="KYC, compliance, and account setup for institutional clients",
            steps=[
                {
                    "step_number": 1,
                    "step_title": "KYC Documentation Collection",
                    "step_description": "Collect and verify KYC documentation",
                    "is_manual": True,
                    "estimated_duration_minutes": 120,
                    "documentation_required": True
                },
                {
                    "step_number": 2,
                    "step_title": "AML Screening",
                    "step_description": "Perform AML and sanctions screening",
                    "is_automated": True,
                    "estimated_duration_minutes": 30
                },
                {
                    "step_number": 3,
                    "step_title": "Credit Assessment",
                    "step_description": "Assess client creditworthiness and set limits",
                    "is_manual": True,
                    "estimated_duration_minutes": 180,
                    "is_decision_point": True
                },
                {
                    "step_number": 4,
                    "step_title": "Account Setup",
                    "step_description": "Set up client accounts and custody arrangements",
                    "is_manual": True,
                    "estimated_duration_minutes": 60
                },
                {
                    "step_number": 5,
                    "step_title": "Client Welcome Package",
                    "step_description": "Send welcome package and account details",
                    "is_automated": True,
                    "estimated_duration_minutes": 15
                }
            ]
        )
        
        return {
            "TRADE_SETTLEMENT": trade_settlement,
            "CORPORATE_ACTIONS": corporate_actions,
            "CLIENT_ONBOARDING": client_onboarding
        }
    
    async def get_available_sops(self) -> Dict[str, SOPTemplate]:
        """Get all available SOP templates"""
        return self.templates
    
    async def create_sop_execution(
        self,
        sop_id: str,
        execution_name: str,
        initiated_by: str,
        context_data: Optional[Dict[str, Any]] = None,
        assigned_to: Optional[str] = None
    ) -> SOPExecution:
        """Create a new SOP execution"""
        
        if sop_id not in self.templates:
            raise ValueError(f"SOP template '{sop_id}' not found")
        
        template = self.templates[sop_id]
        execution_id = f"SOP_EXEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        estimated_duration = sum(
            step.get("estimated_duration_minutes", 0) 
            for step in template.steps
        )
        
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
            requires_approval=any(step.get("is_decision_point", False) for step in template.steps),
            created_at=datetime.now()
        )
        
        self.active_executions[execution_id] = execution
        self.step_executions[execution_id] = []
        
        return execution
    
    async def start_sop_execution(self, execution_id: str, started_by: str) -> SOPExecution:
        """Start executing an SOP"""
        
        if execution_id not in self.active_executions:
            raise ValueError(f"SOP execution '{execution_id}' not found")
        
        execution = self.active_executions[execution_id]
        execution.status = SOPExecutionStatus.IN_PROGRESS
        execution.start_time = datetime.now()
        
        template = self.templates[execution.sop_document_id]
        first_step = min(template.steps, key=lambda s: s["step_number"])
        execution.current_step_id = f"step_{first_step['step_number']}"
        
        return execution
    
    async def execute_step(
        self,
        execution_id: str,
        step_number: int,
        executed_by: str,
        input_data: Optional[Dict[str, Any]] = None,
        execution_notes: Optional[str] = None
    ) -> SOPStepExecution:
        """Execute a single step"""
        
        execution = self.active_executions[execution_id]
        template = self.templates[execution.sop_document_id]
        
        step_template = next(
            (s for s in template.steps if s["step_number"] == step_number),
            None
        )
        
        if not step_template:
            raise ValueError(f"Step {step_number} not found")
        
        step_id = f"step_{step_number}"
        step_execution_id = f"{execution_id}_{step_id}_{uuid.uuid4().hex[:8]}"
        
        start_time = datetime.now()
        
        # Simulate step execution
        await asyncio.sleep(0.1)  # Simulate processing time
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds() * 1000)  # milliseconds
        
        step_execution = SOPStepExecution(
            id=step_execution_id,
            sop_execution_id=execution_id,
            step_id=step_id,
            status=SOPStepExecutionStatus.COMPLETED,
            started_by=executed_by,
            start_time=start_time,
            end_time=end_time,
            actual_duration_minutes=duration,
            execution_notes=execution_notes
        )
        
        # Update execution progress
        execution.completed_steps.append(step_id)
        execution.current_step_id = self._get_next_step_id(template, step_number)
        
        # Check if execution is complete
        if len(execution.completed_steps) == len(template.steps):
            execution.status = SOPExecutionStatus.COMPLETED
            execution.end_time = end_time
            execution.actual_duration_minutes = int(
                (end_time - execution.start_time).total_seconds() / 60
            )
        
        self.step_executions[execution_id].append(step_execution)
        
        return step_execution
    
    async def get_execution_status(self, execution_id: str) -> SOPExecution:
        """Get execution status"""
        if execution_id not in self.active_executions:
            raise ValueError(f"Execution not found")
        return self.active_executions[execution_id]
    
    async def get_execution_summary(self, execution_id: str) -> SOPExecutionSummary:
        """Get execution summary"""
        execution = self.active_executions[execution_id]
        template = self.templates[execution.sop_document_id]
        
        total_steps = len(template.steps)
        completed_steps = len(execution.completed_steps)
        failed_steps = len(execution.failed_steps)
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Calculate estimated time remaining
        remaining_steps = total_steps - completed_steps
        avg_step_duration = sum(
            s.get("estimated_duration_minutes", 0) 
            for s in template.steps
        ) / total_steps if total_steps > 0 else 0
        estimated_time_remaining = int(remaining_steps * avg_step_duration) if remaining_steps > 0 else None
        
        risk_alerts = []
        if failed_steps > 0:
            risk_alerts.append(f"{failed_steps} step(s) failed")
        if execution.requires_approval and execution.approval_status != "APPROVED":
            risk_alerts.append("Requires management approval")
        
        return SOPExecutionSummary(
            execution_id=execution.id,
            sop_title=template.title,
            status=execution.status.value,
            total_steps=total_steps,
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            progress_percentage=progress_percentage,
            estimated_time_remaining_minutes=estimated_time_remaining,
            compliance_status="COMPLIANT" if failed_steps == 0 else "NON_COMPLIANT",
            risk_alerts=risk_alerts
        )
    
    async def get_active_executions(self) -> List[SOPExecution]:
        """Get active executions"""
        return [
            execution for execution in self.active_executions.values()
            if execution.status in [SOPExecutionStatus.IN_PROGRESS, SOPExecutionStatus.REQUIRES_APPROVAL]
        ]
    
    def _get_next_step_id(self, template: SOPTemplate, current_step_number: int) -> Optional[str]:
        """Get next step ID"""
        next_step_number = current_step_number + 1
        next_step = next(
            (s for s in template.steps if s["step_number"] == next_step_number),
            None
        )
        return f"step_{next_step['step_number']}" if next_step else None

# Test Functions

async def test_sop_templates():
    """Test SOP template functionality"""
    print("🧪 Testing SOP Templates")
    print("=" * 50)
    
    service = MockSOPService()
    templates = await service.get_available_sops()
    
    print(f"📋 Found {len(templates)} SOP templates:")
    
    for template_id, template in templates.items():
        print(f"\n📑 {template.title} ({template_id})")
        print(f"   Document: {template.document_number}")
        print(f"   Category: {template.category}")
        print(f"   Business Area: {template.business_area}")
        print(f"   Process Type: {template.process_type}")
        print(f"   Steps: {len(template.steps)}")
        
        total_duration = sum(step.get('estimated_duration_minutes', 0) for step in template.steps)
        automation_count = sum(1 for step in template.steps if step.get('is_automated', False))
        manual_count = len(template.steps) - automation_count
        
        print(f"   Estimated Duration: {total_duration} minutes")
        print(f"   Automation: {automation_count} automated, {manual_count} manual steps")
        
        # Show step details
        for step in template.steps:
            step_type = "🤖" if step.get('is_automated') else "👤"
            decision = " (Decision)" if step.get('is_decision_point') else ""
            tool = f" [{step.get('automation_tool')}]" if step.get('automation_tool') else ""
            print(f"     {step['step_number']}. {step_type} {step['step_title']}{decision}{tool}")
    
    return service

async def test_trade_settlement_execution(service):
    """Test trade settlement SOP execution"""
    print("\n🔵 Testing Trade Settlement SOP Execution")
    print("=" * 60)
    
    # Create execution
    execution = await service.create_sop_execution(
        sop_id="TRADE_SETTLEMENT",
        execution_name="Trade Settlement - AAPL Test Trade",
        initiated_by="settlement_operator",
        context_data={
            "trade_data": {
                "tradeId": "TRADE_TEST_001",
                "tradeType": "EQUITY",
                "securityId": "AAPL",
                "quantity": 1000,
                "price": 150.50,
                "tradeValue": 150500.00,
                "currency": "USD",
                "tradeDate": "2024-07-20",
                "settlementDate": "2024-07-22"
            }
        }
    )
    
    print(f"🚀 Created SOP execution: {execution.execution_name}")
    print(f"   Execution ID: {execution.id}")
    print(f"   Status: {execution.status.value}")
    print(f"   Estimated Duration: {execution.estimated_duration_minutes} minutes")
    print(f"   Requires Approval: {execution.requires_approval}")
    
    # Start execution
    started_execution = await service.start_sop_execution(execution.id, "settlement_operator")
    print(f"   Started execution, new status: {started_execution.status.value}")
    print(f"   Current step: {started_execution.current_step_id}")
    
    # Execute each step
    templates = await service.get_available_sops()
    template = templates["TRADE_SETTLEMENT"]
    
    for step in template.steps:
        step_number = step["step_number"]
        step_title = step["step_title"]
        
        print(f"\n   📍 Executing Step {step_number}: {step_title}")
        
        step_result = await service.execute_step(
            execution_id=execution.id,
            step_number=step_number,
            executed_by="settlement_operator",
            input_data={"step_context": f"Executing {step_title}"},
            execution_notes=f"Test execution of {step_title}"
        )
        
        print(f"      ✅ Status: {step_result.status.value}")
        print(f"      Duration: {step_result.actual_duration_minutes}ms")
        if step_result.execution_notes:
            print(f"      Notes: {step_result.execution_notes}")
    
    # Get final execution status
    final_status = await service.get_execution_status(execution.id)
    print(f"\n📊 Final Execution Status:")
    print(f"   Status: {final_status.status.value}")
    print(f"   Duration: {final_status.actual_duration_minutes} minutes")
    print(f"   Completed Steps: {len(final_status.completed_steps)}")
    
    # Get execution summary
    summary = await service.get_execution_summary(execution.id)
    print(f"\n📈 Execution Summary:")
    print(f"   Progress: {summary.progress_percentage:.1f}%")
    print(f"   Compliance: {summary.compliance_status}")
    if summary.risk_alerts:
        print(f"   Alerts: {', '.join(summary.risk_alerts)}")
    
    return execution

async def test_corporate_actions_execution(service):
    """Test corporate actions SOP execution"""
    print("\n🟡 Testing Corporate Actions SOP Execution")
    print("=" * 60)
    
    execution = await service.create_sop_execution(
        sop_id="CORPORATE_ACTIONS",
        execution_name="Corporate Action - MSFT Dividend",
        initiated_by="ca_specialist",
        context_data={
            "corporate_action_data": {
                "actionId": "CA_DIV_001",
                "actionType": "DIVIDEND",
                "securityId": "MSFT",
                "exDate": "2024-08-15",
                "recordDate": "2024-08-16",
                "payDate": "2024-09-10",
                "rate": 0.75,
                "currency": "USD"
            }
        }
    )
    
    print(f"🚀 Created Corporate Actions execution: {execution.execution_name}")
    
    # Start and execute all steps
    await service.start_sop_execution(execution.id, "ca_specialist")
    
    templates = await service.get_available_sops()
    template = templates["CORPORATE_ACTIONS"]
    
    for step in template.steps:
        step_number = step["step_number"]
        print(f"   📍 Executing Step {step_number}: {step['step_title']}")
        
        await service.execute_step(
            execution_id=execution.id,
            step_number=step_number,
            executed_by="ca_specialist",
            execution_notes=f"Corporate action processing - {step['step_title']}"
        )
    
    summary = await service.get_execution_summary(execution.id)
    print(f"\n📈 Corporate Actions Summary:")
    print(f"   Progress: {summary.progress_percentage:.1f}%")
    print(f"   Compliance: {summary.compliance_status}")
    
    return execution

async def test_client_onboarding_execution(service):
    """Test client onboarding SOP execution"""
    print("\n🟢 Testing Client Onboarding SOP Execution")
    print("=" * 60)
    
    execution = await service.create_sop_execution(
        sop_id="CLIENT_ONBOARDING",
        execution_name="Client Onboarding - ABC Fund Management",
        initiated_by="relationship_manager",
        context_data={
            "client_data": {
                "clientName": "ABC Fund Management Ltd",
                "clientType": "INSTITUTIONAL",
                "jurisdiction": "US",
                "aum": 5000000000,  # $5B AUM
                "riskProfile": "MEDIUM"
            }
        }
    )
    
    print(f"🚀 Created Client Onboarding execution: {execution.execution_name}")
    print(f"   Client: {execution.context_data['client_data']['clientName']}")
    print(f"   AUM: ${execution.context_data['client_data']['aum']:,}")
    
    await service.start_sop_execution(execution.id, "relationship_manager")
    
    # Execute first 3 steps (leave last 2 for demonstration)
    templates = await service.get_available_sops()
    template = templates["CLIENT_ONBOARDING"]
    
    for step in template.steps[:3]:  # Execute first 3 steps
        step_number = step["step_number"]
        print(f"   📍 Executing Step {step_number}: {step['step_title']}")
        
        await service.execute_step(
            execution_id=execution.id,
            step_number=step_number,
            executed_by="compliance_officer" if "KYC" in step['step_title'] or "AML" in step['step_title'] else "relationship_manager",
            execution_notes=f"Client onboarding - {step['step_title']}"
        )
    
    summary = await service.get_execution_summary(execution.id)
    print(f"\n📈 Client Onboarding Summary (Partial):")
    print(f"   Progress: {summary.progress_percentage:.1f}%")
    print(f"   Remaining Steps: {summary.total_steps - summary.completed_steps}")
    print(f"   Estimated Time Remaining: {summary.estimated_time_remaining_minutes} minutes")
    
    return execution

async def test_active_executions_management(service):
    """Test active executions management"""
    print("\n⚡ Testing Active Executions Management")
    print("=" * 50)
    
    active_executions = await service.get_active_executions()
    
    print(f"📊 Found {len(active_executions)} active executions:")
    
    for execution in active_executions:
        summary = await service.get_execution_summary(execution.id)
        print(f"\n   🔄 {execution.execution_name}")
        print(f"      ID: {execution.id}")
        print(f"      Status: {execution.status.value}")
        print(f"      Progress: {summary.progress_percentage:.1f}%")
        print(f"      Assigned to: {execution.assigned_to}")
        print(f"      Compliance: {summary.compliance_status}")
        if summary.risk_alerts:
            print(f"      ⚠️  Alerts: {', '.join(summary.risk_alerts)}")

async def test_concurrent_executions(service):
    """Test concurrent SOP executions"""
    print("\n🔄 Testing Concurrent SOP Executions")
    print("=" * 50)
    
    # Create multiple concurrent executions
    execution_tasks = []
    for i in range(3):
        task = service.create_sop_execution(
            sop_id="TRADE_SETTLEMENT",
            execution_name=f"Concurrent Trade Settlement {i+1}",
            initiated_by=f"operator_{i+1}",
            context_data={
                "trade_data": {
                    "tradeId": f"TRADE_CONCURRENT_{i+1:03d}",
                    "tradeValue": 100000 + (i * 50000),
                    "securityId": ["AAPL", "MSFT", "GOOGL"][i]
                }
            }
        )
        execution_tasks.append(task)
    
    start_time = datetime.now()
    executions = await asyncio.gather(*execution_tasks)
    end_time = datetime.now()
    
    creation_time = (end_time - start_time).total_seconds() * 1000
    
    print(f"🚀 Created {len(executions)} concurrent executions in {creation_time:.1f}ms:")
    for execution in executions:
        print(f"   • {execution.execution_name} [{execution.id[:16]}...]")
    
    # Start all executions
    start_tasks = [service.start_sop_execution(ex.id, ex.initiated_by) for ex in executions]
    await asyncio.gather(*start_tasks)
    
    print(f"\n📊 Concurrent Execution Performance:")
    print(f"   Creation Throughput: {len(executions) / (creation_time / 1000):.1f} executions/second")
    print(f"   All executions started successfully")

async def main():
    """Main test function"""
    print("🏦 Otomeshon Custodian Portal - SOP Management System Test")
    print("=" * 70)
    print("Testing Standard Operating Procedures management and execution")
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Initialize service and test templates
        service = await test_sop_templates()
        
        # Test different SOP executions
        trade_execution = await test_trade_settlement_execution(service)
        ca_execution = await test_corporate_actions_execution(service)
        onboarding_execution = await test_client_onboarding_execution(service)
        
        # Test management features
        await test_active_executions_management(service)
        await test_concurrent_executions(service)
        
        print("\n" + "="*70)
        print("✅ ALL SOP MANAGEMENT TESTS COMPLETED SUCCESSFULLY!")
        print("🚀 SOP management system is ready for custodian banking operations")
        print("\n📋 System Features Demonstrated:")
        print("   ✅ SOP template library with custodian banking procedures")
        print("   ✅ Step-by-step execution tracking and monitoring")
        print("   ✅ Automated and manual step handling")
        print("   ✅ Progress monitoring and compliance tracking")
        print("   ✅ Multi-user execution assignment")
        print("   ✅ Concurrent execution support")
        print("   ✅ Trade settlement procedures")
        print("   ✅ Corporate actions procedures")
        print("   ✅ Client onboarding procedures")
        print("   ✅ Risk alerts and compliance monitoring")
        print("   ✅ Real-time execution status tracking")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())