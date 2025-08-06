"""
Drools Rules Engine Service for Otomeshon Custodian Banking Platform

This service provides integration between Python workflows and Drools 9 rules engine
for custodian banking operations including trade validation, risk management,
compliance checks, and exception handling.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import httpx
from py4j.java_gateway import CallbackServerParameters, GatewayParameters, JavaGateway
from py4j.protocol import Py4JJavaError

from app.core.config import get_settings
from app.models.trade import ExceptionSeverity, Trade, TradeStatus, TradeType
from app.models.workflow import WorkflowExecution

logger = logging.getLogger(__name__)


class RuleExecutionStatus(str, Enum):
    """Rule execution status enumeration"""

    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"


@dataclass
class RuleFact:
    """Represents a fact object to be evaluated by rules"""

    fact_type: str
    fact_id: str
    data: Dict[str, Any]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factType": self.fact_type,
            "factId": self.fact_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RuleResult:
    """Represents the result of rule execution"""

    rule_name: str
    status: RuleExecutionStatus
    facts_processed: int
    rules_fired: List[str]
    actions_triggered: List[Dict[str, Any]]
    execution_time_ms: float
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DroolsService:
    """
    Service for integrating with Drools 9 rules engine via Kogito runtime.

    Provides functionality for:
    - Rule execution against trade and custodian banking facts
    - Rule deployment and management
    - Real-time decision making for trades
    - Compliance and risk rule evaluation
    """

    def __init__(self):
        self.settings = get_settings()
        self.drools_url = self.settings.drools_url
        self.gateway = None
        self.connected = False

        # HTTP client for REST API calls to Kogito
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0), limits=httpx.Limits(max_connections=10)
        )

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self) -> bool:
        """
        Establish connection to Drools/Kogito runtime

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Test HTTP connectivity to Kogito runtime
            health_url = f"{self.drools_url}/q/health"
            response = await self.http_client.get(health_url)

            if response.status_code == 200:
                logger.info(f"Connected to Drools runtime at {self.drools_url}")
                self.connected = True
                return True
            else:
                logger.error(f"Drools health check failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to Drools runtime: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from Drools runtime"""
        if self.gateway:
            try:
                self.gateway.shutdown()
                logger.info("Disconnected from Drools gateway")
            except Exception as e:
                logger.warning(f"Error during gateway shutdown: {str(e)}")

        await self.http_client.aclose()
        self.connected = False

    async def execute_rules(
        self, rule_set: str, facts: List[RuleFact], timeout_seconds: int = 30
    ) -> RuleResult:
        """
        Execute rules against provided facts

        Args:
            rule_set: Name of the rule set to execute
            facts: List of fact objects to evaluate
            timeout_seconds: Maximum execution time

        Returns:
            RuleResult: Execution results including fired rules and actions
        """
        start_time = datetime.now()

        try:
            if not self.connected:
                await self.connect()

            # Prepare facts payload for Kogito
            facts_payload = {
                "facts": [fact.to_dict() for fact in facts],
                "ruleSet": rule_set,
                "executionContext": {
                    "timestamp": start_time.isoformat(),
                    "source": "otomeshon-custodian-platform",
                },
            }

            # Execute rules via Kogito REST API
            execution_url = f"{self.drools_url}/rules/execute"

            response = await self.http_client.post(
                execution_url, json=facts_payload, timeout=timeout_seconds
            )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            if response.status_code == 200:
                result_data = response.json()

                return RuleResult(
                    rule_name=rule_set,
                    status=RuleExecutionStatus.SUCCESS,
                    facts_processed=len(facts),
                    rules_fired=result_data.get("rulesFired", []),
                    actions_triggered=result_data.get("actionsTriggered", []),
                    execution_time_ms=execution_time,
                )
            else:
                error_msg = (
                    f"Rule execution failed: {response.status_code} - {response.text}"
                )
                logger.error(error_msg)

                return RuleResult(
                    rule_name=rule_set,
                    status=RuleExecutionStatus.FAILED,
                    facts_processed=len(facts),
                    rules_fired=[],
                    actions_triggered=[],
                    execution_time_ms=execution_time,
                    error_message=error_msg,
                )

        except asyncio.TimeoutError:
            execution_time = timeout_seconds * 1000
            error_msg = f"Rule execution timed out after {timeout_seconds} seconds"
            logger.error(error_msg)

            return RuleResult(
                rule_name=rule_set,
                status=RuleExecutionStatus.TIMEOUT,
                facts_processed=len(facts),
                rules_fired=[],
                actions_triggered=[],
                execution_time_ms=execution_time,
                error_message=error_msg,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = f"Rule execution error: {str(e)}"
            logger.error(error_msg)

            return RuleResult(
                rule_name=rule_set,
                status=RuleExecutionStatus.FAILED,
                facts_processed=len(facts),
                rules_fired=[],
                actions_triggered=[],
                execution_time_ms=execution_time,
                error_message=error_msg,
            )

    async def validate_trade(self, trade: Trade) -> RuleResult:
        """
        Execute trade validation rules against a trade object

        Args:
            trade: Trade object to validate

        Returns:
            RuleResult: Validation results
        """
        # Convert trade to rule fact
        trade_fact = RuleFact(
            fact_type="Trade",
            fact_id=str(trade.id),
            data={
                "tradeId": trade.id,
                "tradeType": trade.trade_type.value,
                "counterpartyId": trade.counterparty_id,
                "securityId": trade.security_id,
                "quantity": float(trade.quantity),
                "price": float(trade.price),
                "tradeValue": float(trade.trade_value),
                "currency": trade.currency,
                "tradeDate": trade.trade_date.isoformat(),
                "settlementDate": (
                    trade.settlement_date.isoformat() if trade.settlement_date else None
                ),
                "status": trade.status.value,
                "portfolio": trade.portfolio,
                "custodyAccount": trade.custody_account,
            },
            timestamp=datetime.now(),
        )

        return await self.execute_rules("trade-validation", [trade_fact])

    async def check_risk_limits(
        self, trade: Trade, portfolio_data: Dict[str, Any]
    ) -> RuleResult:
        """
        Execute risk management rules for a trade

        Args:
            trade: Trade to check
            portfolio_data: Current portfolio positions and limits

        Returns:
            RuleResult: Risk check results
        """
        facts = [
            RuleFact(
                fact_type="Trade",
                fact_id=str(trade.id),
                data={
                    "tradeId": trade.id,
                    "tradeValue": float(trade.trade_value),
                    "counterpartyId": trade.counterparty_id,
                    "securityId": trade.security_id,
                    "portfolio": trade.portfolio,
                },
                timestamp=datetime.now(),
            ),
            RuleFact(
                fact_type="Portfolio",
                fact_id=trade.portfolio,
                data=portfolio_data,
                timestamp=datetime.now(),
            ),
        ]

        return await self.execute_rules("risk-management", facts)

    async def check_compliance(
        self, trade: Trade, client_data: Dict[str, Any]
    ) -> RuleResult:
        """
        Execute compliance rules for a trade

        Args:
            trade: Trade to check
            client_data: Client information and compliance status

        Returns:
            RuleResult: Compliance check results
        """
        facts = [
            RuleFact(
                fact_type="Trade",
                fact_id=str(trade.id),
                data={
                    "tradeId": trade.id,
                    "counterpartyId": trade.counterparty_id,
                    "tradeValue": float(trade.trade_value),
                    "currency": trade.currency,
                    "tradeDate": trade.trade_date.isoformat(),
                },
                timestamp=datetime.now(),
            ),
            RuleFact(
                fact_type="Client",
                fact_id=trade.counterparty_id,
                data=client_data,
                timestamp=datetime.now(),
            ),
        ]

        return await self.execute_rules("compliance-checks", facts)

    async def process_settlement_rules(
        self, trade: Trade, settlement_data: Dict[str, Any]
    ) -> RuleResult:
        """
        Execute settlement processing rules

        Args:
            trade: Trade to settle
            settlement_data: Settlement instructions and constraints

        Returns:
            RuleResult: Settlement processing results
        """
        facts = [
            RuleFact(
                fact_type="Trade",
                fact_id=str(trade.id),
                data={
                    "tradeId": trade.id,
                    "securityId": trade.security_id,
                    "quantity": float(trade.quantity),
                    "settlementDate": (
                        trade.settlement_date.isoformat()
                        if trade.settlement_date
                        else None
                    ),
                    "custodyAccount": trade.custody_account,
                },
                timestamp=datetime.now(),
            ),
            RuleFact(
                fact_type="Settlement",
                fact_id=f"settlement_{trade.id}",
                data=settlement_data,
                timestamp=datetime.now(),
            ),
        ]

        return await self.execute_rules("settlement-processing", facts)

    async def deploy_rules(self, rule_content: str, rule_name: str) -> bool:
        """
        Deploy new rules to the Drools runtime

        Args:
            rule_content: DRL rule content
            rule_name: Name of the rule set

        Returns:
            bool: True if deployment successful
        """
        try:
            deployment_url = f"{self.drools_url}/rules/deploy"

            payload = {
                "ruleName": rule_name,
                "ruleContent": rule_content,
                "deploymentTime": datetime.now().isoformat(),
            }

            response = await self.http_client.post(deployment_url, json=payload)

            if response.status_code in [200, 201]:
                logger.info(f"Successfully deployed rules: {rule_name}")
                return True
            else:
                logger.error(
                    f"Rule deployment failed: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error deploying rules: {str(e)}")
            return False

    async def get_rule_status(self) -> Dict[str, Any]:
        """
        Get status of deployed rules

        Returns:
            Dict: Rule status information
        """
        try:
            status_url = f"{self.drools_url}/rules/status"
            response = await self.http_client.get(status_url)

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get rule status: {response.status_code}"}

        except Exception as e:
            return {"error": f"Error getting rule status: {str(e)}"}

    async def validate_rule_syntax(self, rule_content: str) -> Dict[str, Any]:
        """
        Validate DRL rule syntax without deploying

        Args:
            rule_content: DRL rule content to validate

        Returns:
            Dict: Validation results
        """
        try:
            validation_url = f"{self.drools_url}/rules/validate"

            payload = {
                "ruleContent": rule_content,
                "validationTime": datetime.now().isoformat(),
            }

            response = await self.http_client.post(validation_url, json=payload)

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "valid": False,
                    "errors": [
                        f"Validation failed: {response.status_code} - {response.text}"
                    ],
                }

        except Exception as e:
            return {"valid": False, "errors": [f"Validation error: {str(e)}"]}


# Singleton instance for dependency injection
_drools_service_instance = None


def get_drools_service() -> DroolsService:
    """Get singleton DroolsService instance"""
    global _drools_service_instance
    if _drools_service_instance is None:
        _drools_service_instance = DroolsService()
    return _drools_service_instance
