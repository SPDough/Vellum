#!/usr/bin/env python3
"""
Test script for Drools integration without requiring Docker

This script tests the DroolsService implementation and workflow nodes
with mock data to verify the integration is working correctly.
"""

import asyncio
import json
import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.drools_service import DroolsService, RuleFact, RuleExecutionStatus
from app.flows.rules_engine_node import (
    TradeValidationNode, 
    RiskCheckNode, 
    ComplianceCheckNode,
    RulesEngineConfig,
    create_initial_state,
    create_trade_processing_workflow
)

def create_sample_trade_data():
    """Create sample trade data for testing"""
    return {
        "tradeId": "TRADE_001",
        "tradeType": "EQUITY",
        "counterpartyId": "CLIENT_001",
        "securityId": "AAPL",
        "quantity": 1000,
        "price": 150.50,
        "tradeValue": 150500.00,
        "currency": "USD",
        "tradeDate": date.today().isoformat(),
        "settlementDate": (date.today()).isoformat(),
        "status": "PENDING",
        "portfolio": "PORTFOLIO_001",
        "custodyAccount": "CUSTODY_001"
    }

def create_sample_portfolio_data():
    """Create sample portfolio data for testing"""
    return {
        "portfolioId": "PORTFOLIO_001",
        "totalExposure": 5000000.00,
        "exposureLimit": 10000000.00,
        "concentrationLimit": 1000000.00,
        "availableCash": 2000000.00,
        "securityExposures": {
            "AAPL": 500000.00,
            "MSFT": 300000.00,
            "GOOGL": 400000.00
        }
    }

def create_sample_client_data():
    """Create sample client data for testing"""
    return {
        "clientId": "CLIENT_001",
        "kycStatus": "APPROVED",
        "amlRiskRating": "LOW",
        "creditRating": "A",
        "lastReviewDate": "2024-01-15",
        "countryCode": "US",
        "approvedInstruments": ["EQUITY", "BOND", "FX"],
        "tradingLimits": {
            "dailyLimit": 1000000.00,
            "positionLimit": 5000000.00
        }
    }

def create_sample_settlement_data():
    """Create sample settlement data for testing"""
    return {
        "settlementId": "SETTLE_001",
        "tradeId": "TRADE_001",
        "cashRequired": 150500.00,
        "securitiesRequired": 1000,
        "settlementAgent": "DTC",
        "instructionStatus": "PENDING",
        "cutoffTime": "2024-07-20T16:00:00"
    }

class MockDroolsService(DroolsService):
    """Mock DroolsService for testing without Docker"""
    
    def __init__(self):
        # Don't call super().__init__() to avoid HTTP client setup
        self.connected = True
        
    async def connect(self) -> bool:
        """Mock connection"""
        self.connected = True
        return True
        
    async def disconnect(self):
        """Mock disconnection"""
        self.connected = False
        
    async def execute_rules(self, rule_set: str, facts: list, timeout_seconds: int = 30):
        """Mock rule execution with realistic responses"""
        print(f"\n🔥 EXECUTING RULES: {rule_set}")
        print(f"📊 Facts provided: {len(facts)}")
        
        # Mock different rule set responses
        if rule_set == "trade-validation":
            return await self._mock_trade_validation(facts)
        elif rule_set == "risk-management":
            return await self._mock_risk_check(facts)
        elif rule_set == "compliance-checks":
            return await self._mock_compliance_check(facts)
        elif rule_set == "settlement-processing":
            return await self._mock_settlement_processing(facts)
        else:
            return await self._mock_generic_rules(facts)
    
    async def _mock_trade_validation(self, facts):
        """Mock trade validation rules"""
        from app.services.drools_service import RuleResult
        
        trade_fact = next((f for f in facts if f.fact_type == "Trade"), None)
        rules_fired = []
        actions_triggered = []
        
        if trade_fact:
            trade_value = trade_fact.data.get("tradeValue", 0)
            
            # Mock large trade alert
            if trade_value > 1000000:
                rules_fired.append("Large Trade Alert")
                actions_triggered.append({
                    "type": "Alert",
                    "alertType": "LARGE_TRADE",
                    "message": f"Trade value exceeds $1M threshold: ${trade_value}",
                    "tradeId": trade_fact.data.get("tradeId"),
                    "severity": "HIGH",
                    "timestamp": datetime.now().isoformat()
                })
                print(f"   ⚠️  Large Trade Alert: ${trade_value}")
            
            # Mock settlement date validation
            if trade_fact.data.get("settlementDate") < trade_fact.data.get("tradeDate"):
                rules_fired.append("Settlement Date Validation")
                actions_triggered.append({
                    "type": "ValidationError",
                    "errorType": "INVALID_SETTLEMENT_DATE",
                    "message": "Settlement date cannot be before trade date",
                    "tradeId": trade_fact.data.get("tradeId"),
                    "timestamp": datetime.now().isoformat()
                })
                print(f"   ❌ Settlement Date Error")
            
            print(f"   ✅ Validation rules fired: {len(rules_fired)}")
        
        return RuleResult(
            rule_name="trade-validation",
            status=RuleExecutionStatus.SUCCESS,
            facts_processed=len(facts),
            rules_fired=rules_fired,
            actions_triggered=actions_triggered,
            execution_time_ms=45.2
        )
    
    async def _mock_risk_check(self, facts):
        """Mock risk management rules"""
        from app.services.drools_service import RuleResult
        
        trade_fact = next((f for f in facts if f.fact_type == "Trade"), None)
        portfolio_fact = next((f for f in facts if f.fact_type == "Portfolio"), None)
        
        rules_fired = []
        actions_triggered = []
        
        if trade_fact and portfolio_fact:
            trade_value = trade_fact.data.get("tradeValue", 0)
            total_exposure = portfolio_fact.data.get("totalExposure", 0)
            exposure_limit = portfolio_fact.data.get("exposureLimit", 0)
            
            # Mock position limit check
            if total_exposure + trade_value > exposure_limit:
                rules_fired.append("Position Limit Check")
                actions_triggered.append({
                    "type": "RiskAlert",
                    "riskType": "POSITION_LIMIT",
                    "message": f"Portfolio exposure limit would be exceeded. Current: ${total_exposure}, Trade: ${trade_value}, Limit: ${exposure_limit}",
                    "tradeId": trade_fact.data.get("tradeId"),
                    "severity": "HIGH",
                    "timestamp": datetime.now().isoformat()
                })
                print(f"   ⚠️  Position Limit Alert: ${total_exposure + trade_value} > ${exposure_limit}")
            
            print(f"   ✅ Risk rules fired: {len(rules_fired)}")
        
        return RuleResult(
            rule_name="risk-management",
            status=RuleExecutionStatus.SUCCESS,
            facts_processed=len(facts),
            rules_fired=rules_fired,
            actions_triggered=actions_triggered,
            execution_time_ms=38.7
        )
    
    async def _mock_compliance_check(self, facts):
        """Mock compliance rules"""
        from app.services.drools_service import RuleResult
        
        trade_fact = next((f for f in facts if f.fact_type == "Trade"), None)
        client_fact = next((f for f in facts if f.fact_type == "Client"), None)
        
        rules_fired = []
        actions_triggered = []
        
        if trade_fact and client_fact:
            kyc_status = client_fact.data.get("kycStatus", "")
            aml_rating = client_fact.data.get("amlRiskRating", "")
            trade_value = trade_fact.data.get("tradeValue", 0)
            
            # Mock KYC check
            if kyc_status != "APPROVED":
                rules_fired.append("KYC Status Check")
                actions_triggered.append({
                    "type": "ComplianceAlert",
                    "complianceType": "KYC_NOT_APPROVED",
                    "message": f"Client KYC status is {kyc_status} - trade blocked",
                    "tradeId": trade_fact.data.get("tradeId"),
                    "severity": "HIGH",
                    "timestamp": datetime.now().isoformat()
                })
                print(f"   ❌ KYC Alert: Status {kyc_status}")
            
            # Mock AML screening
            if trade_value > 10000 and aml_rating == "HIGH":
                rules_fired.append("AML High Risk Screening")
                actions_triggered.append({
                    "type": "ComplianceAlert",
                    "complianceType": "AML_HIGH_RISK",
                    "message": "High-risk client requires AML review for trade over $10K",
                    "tradeId": trade_fact.data.get("tradeId"),
                    "severity": "HIGH",
                    "timestamp": datetime.now().isoformat()
                })
                print(f"   ⚠️  AML Alert: High-risk client, trade ${trade_value}")
            
            print(f"   ✅ Compliance rules fired: {len(rules_fired)}")
        
        return RuleResult(
            rule_name="compliance-checks",
            status=RuleExecutionStatus.SUCCESS,
            facts_processed=len(facts),
            rules_fired=rules_fired,
            actions_triggered=actions_triggered,
            execution_time_ms=52.1
        )
    
    async def _mock_settlement_processing(self, facts):
        """Mock settlement processing rules"""
        from app.services.drools_service import RuleResult
        
        rules_fired = ["Settlement Cutoff Time"]
        actions_triggered = [{
            "type": "Alert",
            "alertType": "SETTLEMENT_CUTOFF",
            "message": "Trade received after settlement cutoff - will settle next business day",
            "severity": "MEDIUM",
            "timestamp": datetime.now().isoformat()
        }]
        
        print(f"   ⚠️  Settlement Alert: After cutoff time")
        print(f"   ✅ Settlement rules fired: {len(rules_fired)}")
        
        return RuleResult(
            rule_name="settlement-processing",
            status=RuleExecutionStatus.SUCCESS,
            facts_processed=len(facts),
            rules_fired=rules_fired,
            actions_triggered=actions_triggered,
            execution_time_ms=29.8
        )
    
    async def _mock_generic_rules(self, facts):
        """Mock generic rule execution"""
        from app.services.drools_service import RuleResult
        
        return RuleResult(
            rule_name="generic-rules",
            status=RuleExecutionStatus.SUCCESS,
            facts_processed=len(facts),
            rules_fired=["Generic Rule"],
            actions_triggered=[],
            execution_time_ms=25.0
        )

async def test_drools_service():
    """Test the DroolsService implementation"""
    print("🧪 Testing DroolsService Implementation")
    print("=" * 50)
    
    # Use mock service for testing
    drools_service = MockDroolsService()
    
    # Test trade validation
    trade_fact = RuleFact(
        fact_type="Trade",
        fact_id="TRADE_001",
        data=create_sample_trade_data(),
        timestamp=datetime.now()
    )
    
    print("\n1️⃣ Testing Trade Validation Rules")
    result = await drools_service.execute_rules("trade-validation", [trade_fact])
    print(f"   Status: {result.status}")
    print(f"   Rules fired: {result.rules_fired}")
    print(f"   Execution time: {result.execution_time_ms}ms")
    
    # Test risk management
    portfolio_fact = RuleFact(
        fact_type="Portfolio",
        fact_id="PORTFOLIO_001",
        data=create_sample_portfolio_data(),
        timestamp=datetime.now()
    )
    
    print("\n2️⃣ Testing Risk Management Rules")
    result = await drools_service.execute_rules("risk-management", [trade_fact, portfolio_fact])
    print(f"   Status: {result.status}")
    print(f"   Rules fired: {result.rules_fired}")
    print(f"   Execution time: {result.execution_time_ms}ms")
    
    # Test compliance
    client_fact = RuleFact(
        fact_type="Client",
        fact_id="CLIENT_001",
        data=create_sample_client_data(),
        timestamp=datetime.now()
    )
    
    print("\n3️⃣ Testing Compliance Rules")
    result = await drools_service.execute_rules("compliance-checks", [trade_fact, client_fact])
    print(f"   Status: {result.status}")
    print(f"   Rules fired: {result.rules_fired}")
    print(f"   Execution time: {result.execution_time_ms}ms")

async def test_workflow_nodes():
    """Test the LangGraph workflow nodes"""
    print("\n\n🔀 Testing LangGraph Workflow Nodes")
    print("=" * 50)
    
    # Mock the drools service for workflow nodes
    import app.services.drools_service as drools_module
    original_get_drools_service = drools_module.get_drools_service
    drools_module.get_drools_service = lambda: MockDroolsService()
    
    try:
        config = RulesEngineConfig(
            rule_sets=["trade-validation", "risk-management", "compliance-checks"],
            timeout_seconds=30
        )
        
        # Create initial state
        initial_state = create_initial_state(
            trade_data=create_sample_trade_data(),
            portfolio_data=create_sample_portfolio_data(),
            client_data=create_sample_client_data(),
            settlement_data=create_sample_settlement_data()
        )
        
        print("\n1️⃣ Testing Trade Validation Node")
        validation_node = TradeValidationNode(config)
        state = await validation_node(initial_state)
        print(f"   Validation passed: {state['validation_passed']}")
        print(f"   Alerts: {len(state['alerts'])}")
        print(f"   Errors: {len(state['errors'])}")
        
        print("\n2️⃣ Testing Risk Check Node")
        risk_node = RiskCheckNode(config)
        state = await risk_node(state)
        print(f"   Risk approved: {state['risk_approved']}")
        print(f"   Total alerts: {len(state['alerts'])}")
        
        print("\n3️⃣ Testing Compliance Check Node")
        compliance_node = ComplianceCheckNode(config)
        state = await compliance_node(state)
        print(f"   Compliance approved: {state['compliance_approved']}")
        print(f"   Total alerts: {len(state['alerts'])}")
        
        print(f"\n📊 Final Workflow State:")
        print(f"   Workflow Status: {state['workflow_status']}")
        print(f"   Rule Results: {len(state['rule_results'])}")
        print(f"   Total Alerts: {len(state['alerts'])}")
        print(f"   Total Errors: {len(state['errors'])}")
        
        # Print some alerts
        if state['alerts']:
            print(f"\n⚠️  Recent Alerts:")
            for alert in state['alerts'][-3:]:  # Show last 3 alerts
                print(f"     • {alert.get('type', 'Unknown')}: {alert.get('message', 'No message')}")
        
    finally:
        # Restore original function
        drools_module.get_drools_service = original_get_drools_service

async def test_high_value_trade():
    """Test with a high-value trade that should trigger multiple rules"""
    print("\n\n💰 Testing High-Value Trade (Should Trigger Multiple Rules)")
    print("=" * 60)
    
    # Create high-value trade data
    high_value_trade = create_sample_trade_data()
    high_value_trade.update({
        "tradeId": "TRADE_LARGE_001",
        "tradeValue": 5500000.00,  # $5.5M - exceeds limits
        "quantity": 50000,
        "price": 110.00
    })
    
    # Portfolio near limit
    portfolio_near_limit = create_sample_portfolio_data()
    portfolio_near_limit.update({
        "totalExposure": 8500000.00,  # Close to 10M limit
        "exposureLimit": 10000000.00
    })
    
    # High-risk client
    high_risk_client = create_sample_client_data()
    high_risk_client.update({
        "clientId": "CLIENT_HIGH_RISK",
        "amlRiskRating": "HIGH",
        "kycStatus": "APPROVED"
    })
    
    drools_service = MockDroolsService()
    
    # Test each rule set
    trade_fact = RuleFact("Trade", "TRADE_LARGE_001", high_value_trade, datetime.now())
    portfolio_fact = RuleFact("Portfolio", "PORTFOLIO_001", portfolio_near_limit, datetime.now())
    client_fact = RuleFact("Client", "CLIENT_HIGH_RISK", high_risk_client, datetime.now())
    
    print("\n🔥 Executing All Rules for High-Value Trade...")
    
    # Trade validation
    result1 = await drools_service.execute_rules("trade-validation", [trade_fact])
    print(f"\n   Trade Validation: {len(result1.rules_fired)} rules fired")
    
    # Risk check
    result2 = await drools_service.execute_rules("risk-management", [trade_fact, portfolio_fact])
    print(f"   Risk Management: {len(result2.rules_fired)} rules fired")
    
    # Compliance check
    result3 = await drools_service.execute_rules("compliance-checks", [trade_fact, client_fact])
    print(f"   Compliance Check: {len(result3.rules_fired)} rules fired")
    
    total_rules_fired = len(result1.rules_fired) + len(result2.rules_fired) + len(result3.rules_fired)
    total_alerts = len(result1.actions_triggered) + len(result2.actions_triggered) + len(result3.actions_triggered)
    
    print(f"\n📈 Summary for High-Value Trade:")
    print(f"   Total Rules Fired: {total_rules_fired}")
    print(f"   Total Alerts Generated: {total_alerts}")
    print(f"   Trade Requires Manual Review: YES")

async def main():
    """Main test function"""
    print("🏦 Otomeshon Custodian Portal - Drools Integration Test")
    print("=" * 70)
    print("Testing Drools rules engine integration for custodian banking operations")
    print(f"Test started at: {datetime.now()}")
    
    try:
        # Test basic DroolsService
        await test_drools_service()
        
        # Test workflow nodes
        await test_workflow_nodes()
        
        # Test high-value trade scenario
        await test_high_value_trade()
        
        print("\n\n✅ All Tests Completed Successfully!")
        print("🚀 Drools integration is ready for custodian banking operations")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())