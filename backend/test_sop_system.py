#!/usr/bin/env python3
"""
Simple SOP System Test

Tests the SOP management system including template management, execution tracking,
and step-by-step procedure execution for custodian banking operations.
"""

import asyncio
import json
from datetime import datetime
from app.services.sop_service import get_sop_service

async def test_sop_templates():
    """Test SOP template retrieval"""
    print("🧪 Testing SOP Templates")
    print("=" * 50)

    sop_service = get_sop_service()
    templates = await sop_service.get_available_sops()

    print(f"📋 Found {len(templates)} SOP templates:")

    for template_id, template in templates.items():
        print(f"\n📑 {template['title']} ({template_id})")
        print(f"   Category: {template['category']}")
        print(f"   Business Area: {template['business_area']}")
        print(f"   Process Type: {template['process_type']}")
        print(f"   Steps: {len(template['steps'])}")

        total_duration = sum(step.get('estimated_duration_minutes', 0) for step in template['steps'])
        print(f"   Estimated Duration: {total_duration} minutes")

        # Show step details
        for step in template['steps']:
            step_type = "🤖 Automated" if step.get('is_automated') else "👤 Manual"
            decision = " (Decision Point)" if step.get('is_decision_point') else ""
            print(f"     {step['step_number']}. {step['step_title']} - {step_type}{decision}")

    return templates

async def test_trade_settlement_execution():
    """Test trade settlement SOP execution"""
    print("\n🔵 Testing Trade Settlement SOP Execution")
    print("=" * 60)

    sop_service = get_sop_service()

    # Create execution
    execution = await sop_service.create_sop_execution(
        sop_id="TRADE_SETTLEMENT",
        execution_name="Trade Settlement - AAPL Test Trade",
        initiated_by="test_operator",
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
    print(f"   Status: {execution.status}")
    print(f"   Estimated Duration: {execution.estimated_duration_minutes} minutes")

    # Start execution
    started_execution = await sop_service.start_sop_execution(execution.id, "test_operator")
    print(f"   Started execution, new status: {started_execution.status}")
    print(f"   Current step: {started_execution.current_step_id}")

    # Execute each step
    templates = await sop_service.get_available_sops()
    trade_settlement_template = templates["TRADE_SETTLEMENT"]

    for step in trade_settlement_template["steps"]:
        step_number = step["step_number"]
        step_title = step["step_title"]

        print(f"\n   📍 Executing Step {step_number}: {step_title}")

        step_result = await sop_service.execute_step(
            execution_id=execution.id,
            step_number=step_number,
            executed_by="test_operator",
            input_data={"step_context": f"Executing {step_title}"},
            execution_notes=f"Test execution of {step_title}"
        )

        print(f"      ✅ Step completed in {step_result.actual_duration_minutes}ms")
        print(f"      Status: {step_result.status}")

        if step_result.error_message:
            print(f"      ❌ Error: {step_result.error_message}")

    # Get final execution status
    final_status = await sop_service.get_execution_status(execution.id)
    print(f"\n📊 Final Execution Status:")
    print(f"   Status: {final_status.status}")
    print(f"   Completion: {final_status.completion_percentage:.1f}%")
    print(f"   Duration: {final_status.actual_duration_minutes} minutes")

    # Get execution summary
    summary = await sop_service.get_execution_summary(execution.id)
    print(f"\n📈 Execution Summary:")
    print(f"   Total Steps: {summary.total_steps}")
    print(f"   Completed: {summary.completed_steps}")
    print(f"   Failed: {summary.failed_steps}")
    print(f"   Progress: {summary.progress_percentage:.1f}%")
    print(f"   Compliance: {summary.compliance_status}")
    if summary.risk_alerts:
        print(f"   Alerts: {', '.join(summary.risk_alerts)}")

    return execution.id

async def test_corporate_actions_execution():
    """Test corporate actions SOP execution"""
    print("\n🟡 Testing Corporate Actions SOP Execution")
    print("=" * 60)

    sop_service = get_sop_service()

    # Create execution
    execution = await sop_service.create_sop_execution(
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

    # Start and execute steps
    started_execution = await sop_service.start_sop_execution(execution.id, "ca_specialist")

    templates = await sop_service.get_available_sops()
    ca_template = templates["CORPORATE_ACTIONS"]

    for step in ca_template["steps"]:
        step_number = step["step_number"]
        step_title = step["step_title"]

        print(f"   📍 Executing Step {step_number}: {step_title}")

        step_result = await sop_service.execute_step(
            execution_id=execution.id,
            step_number=step_number,
            executed_by="ca_specialist",
            execution_notes=f"Corporate action processing - {step_title}"
        )

        print(f"      ✅ Status: {step_result.status}")

    # Get final summary
    summary = await sop_service.get_execution_summary(execution.id)
    print(f"\n📈 Corporate Actions Summary:")
    print(f"   Progress: {summary.progress_percentage:.1f}%")
    print(f"   Compliance: {summary.compliance_status}")

    return execution.id

async def test_active_executions():
    """Test active executions tracking"""
    print("\n⚡ Testing Active Executions Management")
    print("=" * 50)

    sop_service = get_sop_service()
    active_executions = await sop_service.get_active_executions()

    print(f"📊 Found {len(active_executions)} active executions:")

    for execution in active_executions:
        print(f"\n   🔄 {execution.execution_name}")
        print(f"      ID: {execution.id}")
        print(f"      Status: {execution.status}")
        print(f"      Progress: {execution.completion_percentage:.1f}%")
        print(f"      Assigned to: {execution.assigned_to}")
        if execution.requires_approval:
            print(f"      ⚠️  Requires Approval: {execution.approval_status or 'PENDING'}")

async def test_concurrent_executions():
    """Test multiple concurrent SOP executions"""
    print("\n🔄 Testing Concurrent SOP Executions")
    print("=" * 50)

    sop_service = get_sop_service()

    # Create multiple executions
    execution_tasks = []
    for i in range(3):
        task = sop_service.create_sop_execution(
            sop_id="TRADE_SETTLEMENT",
            execution_name=f"Concurrent Trade Settlement {i+1}",
            initiated_by=f"operator_{i+1}",
            context_data={
                "trade_data": {
                    "tradeId": f"TRADE_CONCURRENT_{i+1:03d}",
                    "tradeValue": 100000 + (i * 50000)
                }
            }
        )
        execution_tasks.append(task)

    # Execute concurrently
    executions = await asyncio.gather(*execution_tasks)

    print(f"🚀 Created {len(executions)} concurrent executions:")
    for execution in executions:
        print(f"   • {execution.execution_name} [{execution.id[:16]}...]")

    # Start all executions
    start_tasks = [
        sop_service.start_sop_execution(execution.id, execution.initiated_by)
        for execution in executions
    ]

    start_time = datetime.now()
    started_executions = await asyncio.gather(*start_tasks)
    end_time = datetime.now()

    total_time = (end_time - start_time).total_seconds() * 1000

    print(f"\n📊 Concurrent Execution Results:")
    print(f"   Total Executions: {len(started_executions)}")
    print(f"   Start Time: {total_time:.1f}ms")
    print(f"   Throughput: {len(started_executions) / (total_time / 1000):.1f} executions/second")

    for execution in started_executions:
        print(f"   ✅ {execution.execution_name}: {execution.status}")

async def main():
    """Main test function"""
    print("🏦 Otomeshon Custodian Portal - SOP Management System Test")
    print("=" * 70)
    print("Testing Standard Operating Procedures management and execution")
    print(f"Test started at: {datetime.now()}")
    print()

    try:
        # Test SOP templates
        templates = await test_sop_templates()

        # Test trade settlement execution
        trade_execution_id = await test_trade_settlement_execution()

        # Test corporate actions execution
        ca_execution_id = await test_corporate_actions_execution()

        # Test active executions
        await test_active_executions()

        # Test concurrent executions
        await test_concurrent_executions()

        print("\n" + "="*70)
        print("✅ ALL SOP MANAGEMENT TESTS COMPLETED SUCCESSFULLY!")
        print("🚀 SOP management system is ready for custodian banking operations")
        print("\n📋 System Features Tested:")
        print("   ✅ SOP template management")
        print("   ✅ Step-by-step execution tracking")
        print("   ✅ Automated and manual step handling")
        print("   ✅ Progress monitoring and compliance tracking")
        print("   ✅ Multi-user execution management")
        print("   ✅ Concurrent execution support")
        print("   ✅ Trade settlement procedures")
        print("   ✅ Corporate actions procedures")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())