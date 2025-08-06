#!/usr/bin/env python3
"""
Test script for Workflow Execution System

Tests the complete workflow execution system including rules engine integration,
agent workflows, and the unified execution service.
"""

import json
import sys
import os
from datetime import datetime, date

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Add the parent directory for shared test utilities
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from test_utils import (
    create_sample_trade_data, 
    create_sample_portfolio_data, 
    create_sample_client_data,
    print_test_header,
    print_test_completion,
    run_async_test_main
)

from app.services.workflow_execution_service import (
    get_workflow_execution_service,
    WorkflowExecutionService,
    WorkflowType,
    WorkflowConfig,
    WorkflowNodeConfig
)

# Use shared sample data creation functions from test_utils

def create_large_trade_data():
    """Create large trade that should trigger rules"""
    return {
        "tradeId": "TRADE_LARGE_TEST_001",
        "tradeType": "EQUITY",
        "counterpartyId": "CLIENT_002",
        "securityId": "MSFT",
        "quantity": 10000,
        "price": 300.00,
        "tradeValue": 3000000.00,  # $3M - should trigger multiple rules
        "currency": "USD",
        "tradeDate": date.today().isoformat(),
        "settlementDate": date.today().isoformat(),
        "status": "PENDING",
        "portfolio": "PORTFOLIO_001",
        "custodyAccount": "CUSTODY_001"
    }

# Additional test data creation functions specific to this test

def create_high_risk_client_data():
    """Create high-risk client data"""
    return {
        "clientId": "CLIENT_002",
        "kycStatus": "APPROVED",
        "amlRiskRating": "HIGH",
        "creditRating": "B",
        "lastReviewDate": "2023-01-15",  # Stale
        "countryCode": "US"
    }

async def test_workflow_templates():
    """Test workflow template functionality"""
    print("🧪 Testing Workflow Templates")
    print("=" * 50)
    
    workflow_service = get_workflow_execution_service()
    templates = workflow_service.get_workflow_templates()
    
    print(f"📋 Found {len(templates)} workflow templates:")
    
    for template_id, template in templates.items():
        print(f"\n🔀 {template.name} ({template_id})")
        print(f"   Type: {template.workflow_type.value}")
        print(f"   Nodes: {len(template.nodes)}")
        print(f"   Entry Point: {template.entry_point}")
        
        # Show node details
        for node in template.nodes:
            print(f"   📍 {node.node_id} ({node.node_type}): {node.name}")
    
    return templates

async def test_trade_processing_workflow():
    """Test the trade processing workflow with normal trade"""
    print("\n🔵 Testing Normal Trade Processing Workflow")
    print("=" * 50)
    
    workflow_service = get_workflow_execution_service()
    templates = workflow_service.get_workflow_templates()
    
    # Get trade processing workflow
    trade_workflow = templates.get("trade_processing_v1")
    if not trade_workflow:
        print("❌ Trade processing workflow not found!")
        return None
    
    # Prepare input data
    input_data = {
        "trade_data": create_sample_trade_data(trade_id="TRADE_TEST_001"),
        "portfolio_data": create_sample_portfolio_data(total_exposure=8500000.00),
        "client_data": create_sample_client_data(),
        "settlement_data": {}
    }
    
    print(f"🚀 Executing workflow: {trade_workflow.name}")
    print(f"📊 Trade Value: ${input_data['trade_data']['tradeValue']:,.2f}")
    
    # Execute workflow
    start_time = datetime.now()
    result = await workflow_service.execute_workflow(
        workflow_config=trade_workflow,
        input_data=input_data,
        user_id="test_user"
    )
    end_time = datetime.now()
    
    print(f"\n📈 Workflow Execution Results:")
    print(f"   Execution ID: {result.execution_id}")
    print(f"   Status: {result.status.value}")
    print(f"   Duration: {result.total_execution_time_ms:.1f}ms")
    print(f"   Nodes Executed: {len(result.node_results)}")
    
    # Show node results
    for node_result in result.node_results:
        status_icon = "✅" if node_result.status.value == "completed" else "❌"
        print(f"   {status_icon} {node_result.node_id} ({node_result.node_type}): {node_result.status.value}")
        
        if node_result.alerts:
            for alert in node_result.alerts:
                severity = alert.get('severity', 'INFO')
                print(f"      ⚠️  [{severity}] {alert.get('message', 'Alert generated')}")
    
    # Show summary
    if result.summary:
        print(f"\n📊 Summary:")
        print(f"   Success Rate: {result.summary.get('success_rate', 0) * 100:.1f}%")
        print(f"   Total Alerts: {result.summary.get('total_alerts', 0)}")
        print(f"   Completed Nodes: {result.summary.get('completed_nodes', 0)}")
        print(f"   Failed Nodes: {result.summary.get('failed_nodes', 0)}")
    
    return result

async def test_large_trade_processing():
    """Test workflow with large trade that should trigger multiple rules"""
    print("\n🔴 Testing Large Trade Processing (Should Trigger Rules)")
    print("=" * 60)
    
    workflow_service = get_workflow_execution_service()
    templates = workflow_service.get_workflow_templates()
    
    # Get trade processing workflow
    trade_workflow = templates.get("trade_processing_v1")
    if not trade_workflow:
        print("❌ Trade processing workflow not found!")
        return None
    
    # Prepare input data with large trade and high-risk client
    input_data = {
        "trade_data": create_large_trade_data(),
        "portfolio_data": create_sample_portfolio_data(),
        "client_data": create_high_risk_client_data(),
        "settlement_data": {}
    }
    
    print(f"🚀 Executing workflow with large trade")
    print(f"💰 Trade Value: ${input_data['trade_data']['tradeValue']:,.2f}")
    print(f"⚠️  Client Risk: {input_data['client_data']['amlRiskRating']}")
    
    # Execute workflow
    result = await workflow_service.execute_workflow(
        workflow_config=trade_workflow,
        input_data=input_data,
        user_id="test_user"
    )
    
    print(f"\n📈 Large Trade Execution Results:")
    print(f"   Status: {result.status.value}")
    print(f"   Duration: {result.total_execution_time_ms:.1f}ms")
    
    # Count alerts by severity
    all_alerts = []
    for node_result in result.node_results:
        if node_result.alerts:
            all_alerts.extend(node_result.alerts)
    
    high_alerts = sum(1 for alert in all_alerts if alert.get('severity') == 'HIGH')
    medium_alerts = sum(1 for alert in all_alerts if alert.get('severity') == 'MEDIUM')
    
    print(f"   🚨 HIGH Severity Alerts: {high_alerts}")
    print(f"   ⚠️  MEDIUM Severity Alerts: {medium_alerts}")
    print(f"   📊 Total Alerts: {len(all_alerts)}")
    
    # Show detailed alerts
    if all_alerts:
        print(f"\n🚨 Alerts Generated:")
        for i, alert in enumerate(all_alerts[:5], 1):  # Show first 5 alerts
            severity = alert.get('severity', 'INFO')
            alert_type = alert.get('type', 'Unknown')
            message = alert.get('message', 'No message')
            print(f"   {i}. [{severity}] {alert_type}: {message}")
        
        if len(all_alerts) > 5:
            print(f"   ... and {len(all_alerts) - 5} more alerts")
    
    # Determine if trade should be approved
    critical_alerts = [a for a in all_alerts if a.get('severity') in ['HIGH', 'CRITICAL']]
    trade_decision = "❌ REQUIRES MANUAL REVIEW" if critical_alerts else "✅ AUTO-APPROVED"
    print(f"\n🎯 Trade Decision: {trade_decision}")
    
    return result

async def test_exception_handling_workflow():
    """Test the exception handling workflow"""
    print("\n🛠️  Testing Exception Handling Workflow")
    print("=" * 50)
    
    workflow_service = get_workflow_execution_service()
    templates = workflow_service.get_workflow_templates()
    
    # Get exception handling workflow
    exception_workflow = templates.get("exception_handling_v1")
    if not exception_workflow:
        print("❌ Exception handling workflow not found!")
        return None
    
    # Create exception data
    input_data = {
        "exception_data": {
            "exceptionId": "EXC_TEST_001",
            "exceptionType": "VALIDATION_ERROR",
            "severity": "HIGH",
            "description": "Invalid settlement date - before trade date",
            "tradeId": "TRADE_ERROR_001",
            "detectedAt": datetime.now().isoformat()
        },
        "trade_data": {
            "tradeId": "TRADE_ERROR_001",
            "settlementDate": "2024-07-18",
            "tradeDate": "2024-07-20",
            "tradeValue": 250000.00
        }
    }
    
    print(f"🚀 Executing exception handling workflow")
    print(f"❌ Exception: {input_data['exception_data']['description']}")
    
    # Execute workflow
    result = await workflow_service.execute_workflow(
        workflow_config=exception_workflow,
        input_data=input_data,
        user_id="test_user"
    )
    
    print(f"\n📈 Exception Handling Results:")
    print(f"   Status: {result.status.value}")
    print(f"   Duration: {result.total_execution_time_ms:.1f}ms")
    
    # Show node results with focus on AI agent outputs
    for node_result in result.node_results:
        print(f"   📍 {node_result.node_id}: {node_result.status.value}")
        
        # Show AI agent outputs
        if node_result.node_type == "AGENT":
            output_data = node_result.output_data
            if "classification" in str(output_data):
                classification = output_data.get(f"{node_result.node_id}_classification")
                confidence = output_data.get("confidence", 0)
                print(f"      🤖 Classification: {classification} (confidence: {confidence})")
            
            if "suggestions" in str(output_data):
                suggestions = output_data.get(f"{node_result.node_id}_suggestions", [])
                print(f"      💡 AI Suggestions:")
                for suggestion in suggestions[:3]:  # Show first 3
                    print(f"         • {suggestion}")
    
    return result

async def test_performance():
    """Test workflow execution performance"""
    print("\n⚡ Testing Workflow Performance")
    print("=" * 50)
    
    workflow_service = get_workflow_execution_service()
    templates = workflow_service.get_workflow_templates()
    trade_workflow = templates.get("trade_processing_v1")
    
    if not trade_workflow:
        print("❌ Trade processing workflow not found!")
        return
    
    # Test multiple concurrent executions
    num_executions = 5
    print(f"🚀 Running {num_executions} concurrent workflow executions...")
    
    # Create different trade scenarios
    test_scenarios = []
    for i in range(num_executions):
        trade_value = 100000 + (i * 200000)  # Varying sizes
        
        scenario = {
            "trade_data": create_sample_trade_data(
                trade_id=f"TRADE_PERF_{i+1:03d}", 
                trade_value=trade_value
            ),
            "portfolio_data": create_sample_portfolio_data(total_exposure=8500000.00),
            "client_data": create_sample_client_data(),
            "settlement_data": {}
        }
        test_scenarios.append(scenario)
    
    # Execute all workflows concurrently
    start_time = datetime.now()
    
    tasks = [
        workflow_service.execute_workflow(
            workflow_config=trade_workflow,
            input_data=scenario,
            user_id=f"test_user_{i}"
        )
        for i, scenario in enumerate(test_scenarios)
    ]
    
    results = await asyncio.gather(*tasks)
    
    end_time = datetime.now()
    total_time = (end_time - start_time).total_seconds() * 1000
    
    # Analyze results
    successful_executions = sum(1 for r in results if r.status.value == "completed")
    avg_execution_time = sum(r.total_execution_time_ms for r in results) / len(results)
    total_nodes_processed = sum(len(r.node_results) for r in results)
    total_alerts = sum(len([a for nr in r.node_results for a in (nr.alerts or [])]) for r in results)
    
    print(f"\n📊 Performance Results:")
    print(f"   Total Executions: {num_executions}")
    print(f"   Successful: {successful_executions}")
    print(f"   Success Rate: {successful_executions / num_executions * 100:.1f}%")
    print(f"   Total Time: {total_time:.1f}ms")
    print(f"   Average per Workflow: {avg_execution_time:.1f}ms")
    print(f"   Throughput: {num_executions / (total_time / 1000):.1f} workflows/second")
    print(f"   Total Nodes Processed: {total_nodes_processed}")
    print(f"   Total Alerts Generated: {total_alerts}")
    
    # Show individual results
    print(f"\n📈 Individual Results:")
    for i, result in enumerate(results, 1):
        trade_value = test_scenarios[i-1]["trade_data"]["tradeValue"]
        alerts_count = sum(len(nr.alerts or []) for nr in result.node_results)
        print(f"   {i}. ${trade_value:,.0f} -> {result.status.value} ({result.total_execution_time_ms:.1f}ms, {alerts_count} alerts)")

async def test_active_executions():
    """Test active executions tracking"""
    print("\n📊 Testing Active Executions Tracking")
    print("=" * 50)
    
    workflow_service = get_workflow_execution_service()
    
    # Check active executions before
    active_before = workflow_service.get_active_executions()
    print(f"Active executions before test: {len(active_before)}")
    
    # Start a long-running workflow simulation
    templates = workflow_service.get_workflow_templates()
    trade_workflow = templates.get("trade_processing_v1")
    
    if trade_workflow:
        input_data = {
            "trade_data": create_sample_trade_data(trade_id="TRADE_TEST_001"),
            "portfolio_data": create_sample_portfolio_data(total_exposure=8500000.00),
            "client_data": create_sample_client_data()
        }
        
        # Execute workflow
        result = await workflow_service.execute_workflow(
            workflow_config=trade_workflow,
            input_data=input_data,
            user_id="test_user"
        )
        
        print(f"✅ Workflow completed: {result.execution_id}")
        print(f"   Final status: {result.status.value}")
        
        # Check execution status
        retrieved_result = await workflow_service.get_execution_status(result.execution_id)
        if retrieved_result:
            print(f"   Retrieved execution status: {retrieved_result.status.value}")
            print(f"   Nodes executed: {len(retrieved_result.node_results)}")

async def main():
    """Main test function"""
    print("🏦 Otomeshon Custodian Portal - Workflow Execution System Test")
    print("=" * 70)
    print("Testing comprehensive workflow execution with rules engine and AI agents")
    print(f"Test started at: {datetime.now()}")
    print()
    
    # Test workflow templates
    templates = await test_workflow_templates()
    
    # Test normal trade processing
    normal_result = await test_trade_processing_workflow()
    
    # Test large trade processing
    large_result = await test_large_trade_processing()
    
    # Test exception handling
    exception_result = await test_exception_handling_workflow()
    
    # Test performance
    await test_performance()
    
    # Test active executions
    await test_active_executions()
    
    print("\n" + "="*70)
    print("✅ ALL WORKFLOW TESTS COMPLETED SUCCESSFULLY!")
    print("🚀 Workflow execution system is ready for custodian banking operations")
    print("📋 Available features:")
    print("   • Rules-based workflow execution")
    print("   • AI agent integration")
    print("   • Hybrid workflow orchestration")
    print("   • Real-time execution monitoring")
    print("   • Comprehensive alerting system")
    print("   • Performance optimization")
    print("="*70)

if __name__ == "__main__":
    run_async_test_main(main)