"""
Service factory implementation for Otomeshon Banking Platform
"""

from typing import Any, Dict, Optional, Type

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.interfaces import (
    IAuditService,
    IComplianceService,
    IRiskService,
    IServiceFactory,
    ISOPService,
    ITradeService,
    IUserService,
)


class ServiceFactory(IServiceFactory):
    """
    Concrete service factory implementation

    This factory creates service instances with proper dependency injection
    and configuration based on the current environment.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.settings = get_settings()

        self._service_cache: dict[str, Any] = {}

    def create_trade_service(self) -> ITradeService:
        """Create trade service instance"""
        if "trade_service" not in self._service_cache:
            from app.services.trade_service import TradeService

            self._service_cache["trade_service"] = TradeService(
                db_session=self.db_session
            )
        return self._service_cache["trade_service"]

    def create_sop_service(self) -> ISOPService:
        """Create SOP service instance"""

        if "sop_service" not in self._service_cache:
            from app.services.sop_service import SOPService

            self._service_cache["sop_service"] = SOPService(db_session=self.db_session)
        return self._service_cache["sop_service"]

    def create_risk_service(self) -> IRiskService:
        """Create risk service instance"""
        if "risk_service" not in self._service_cache:
            from app.services.risk_service import RiskService

            self._service_cache["risk_service"] = RiskService(
                db_session=self.db_session,
                config={
                    "var_confidence_level": 0.95,
                    "position_limit_threshold": 1000000,
                    "concentration_limit": 0.10,
                },
            )
        return self._service_cache["risk_service"]

    def create_compliance_service(self) -> IComplianceService:
        """Create compliance service instance"""
        if "compliance_service" not in self._service_cache:
            from app.services.compliance_service import ComplianceService

            self._service_cache["compliance_service"] = ComplianceService(
                db_session=self.db_session,
                regulatory_config={
                    "aml_threshold": 10000,
                    "kyc_renewal_days": 365,
                    "suspicious_activity_threshold": 50000,
                },
            )
        return self._service_cache["compliance_service"]

    def create_user_service(self) -> IUserService:
        """Create user service instance"""
        if "user_service" not in self._service_cache:
            from app.services.user_service import UserService

            self._service_cache["user_service"] = UserService(
                db_session=self.db_session
            )
        return self._service_cache["user_service"]

    def create_audit_service(self) -> IAuditService:
        """Create audit service instance"""
        if "audit_service" not in self._service_cache:
            from app.services.audit_service import AuditService

            self._service_cache["audit_service"] = AuditService(
                db_session=self.db_session
            )
        return self._service_cache["audit_service"]

    def create_data_service(self):
        """Create data service instance"""
        if "data_service" not in self._service_cache:
            from app.services.data_service import DataService

            self._service_cache["data_service"] = DataService(
                db_session=self.db_session
            )
        return self._service_cache["data_service"]

    def create_workflow_service(self):
        """Create workflow service instance"""
        if "workflow_service" not in self._service_cache:
            from app.services.workflow_service import WorkflowService

            self._service_cache["workflow_service"] = WorkflowService(
                db_session=self.db_session
            )
        return self._service_cache["workflow_service"]

    def create_notification_service(self):
        """Create notification service instance"""
        if "notification_service" not in self._service_cache:
            from app.services.notification_service import NotificationService

            self._service_cache["notification_service"] = NotificationService(
                db_session=self.db_session,
                config={
                    "email_enabled": self.settings.features.notifications_enabled,
                    "slack_enabled": self.settings.features.slack_integration_enabled,
                    "sms_enabled": False,  # Disabled by default
                },
            )
        return self._service_cache["notification_service"]

    def get_service(self, service_name: str):
        """Get service by name"""
        service_creators = {
            "trade": self.create_trade_service,
            "sop": self.create_sop_service,
            "risk": self.create_risk_service,
            "compliance": self.create_compliance_service,
            "user": self.create_user_service,
            "audit": self.create_audit_service,
            "data": self.create_data_service,
            "workflow": self.create_workflow_service,
            "notification": self.create_notification_service,
        }

        creator = service_creators.get(service_name)
        if creator:
            return creator()
        else:
            raise ValueError(f"Unknown service: {service_name}")

    def clear_cache(self):
        """Clear service cache (useful for testing)"""
        self._service_cache.clear()


class BankingServiceRegistry:
    """
    Registry for banking-specific service configurations and instances
    """

    def __init__(self):
        self._factories: dict[str, ServiceFactory] = {}
        self._environment_configs = {
            "development": {
                "cache_enabled": True,
                "audit_level": "medium",
                "performance_monitoring": True,
                "mock_external_services": True,
            },
            "testing": {
                "cache_enabled": False,
                "audit_level": "high",
                "performance_monitoring": False,
                "mock_external_services": True,
            },
            "production": {
                "cache_enabled": True,
                "audit_level": "critical",
                "performance_monitoring": True,
                "mock_external_services": False,
            },
        }

    def register_factory(self, environment: str, factory: ServiceFactory):
        """Register a service factory for an environment"""
        self._factories[environment] = factory

    def get_factory(self, environment: str) -> ServiceFactory:
        """Get service factory for environment"""

        factory = self._factories.get(environment)
        if factory is None:
            raise ValueError(f"No factory registered for environment: {environment}")
        return factory

    def get_environment_config(self, environment: str) -> dict[str, Any]:
        """Get configuration for environment"""
        return self._environment_configs.get(environment, {})


class ServiceLocator:
    """
    Service locator pattern implementation for dependency injection
    """

    _instance = None
    _factory: Optional[ServiceFactory] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, factory: ServiceFactory):
        """Initialize the service locator with a factory"""
        cls._factory = factory

    @classmethod
    def get_trade_service(cls) -> ITradeService:
        """Get trade service instance"""
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_trade_service()

    @classmethod
    def get_sop_service(cls) -> ISOPService:
        """Get SOP service instance"""
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_sop_service()

    @classmethod
    def get_risk_service(cls) -> IRiskService:
        """Get risk service instance"""
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_risk_service()

    @classmethod
    def get_compliance_service(cls) -> IComplianceService:
        """Get compliance service instance"""
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_compliance_service()

    @classmethod
    def get_user_service(cls) -> IUserService:
        """Get user service instance"""
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_user_service()

    @classmethod
    def get_audit_service(cls) -> IAuditService:
        """Get audit service instance"""
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_audit_service()


# Dependency injection helper functions


def get_service_factory(db_session: AsyncSession) -> ServiceFactory:
    """Get a configured service factory instance"""
    return ServiceFactory(db_session)


def get_banking_services(db_session: AsyncSession) -> dict[str, Any]:
    """Get all banking services in a dictionary"""
    factory = ServiceFactory(db_session)

    return {
        "trade": factory.create_trade_service(),
        "sop": factory.create_sop_service(),
        "risk": factory.create_risk_service(),
        "compliance": factory.create_compliance_service(),
        "user": factory.create_user_service(),
        "audit": factory.create_audit_service(),
        "data": factory.create_data_service(),
        "workflow": factory.create_workflow_service(),
        "notification": factory.create_notification_service(),
    }


# FastAPI dependency functions


async def get_trade_service_dependency(
    db_session: AsyncSession = None,
) -> ITradeService:
    """FastAPI dependency for trade service"""
    if db_session is None:
        from app.core.database import get_async_session

        async for session in get_async_session():
            db_session = session
            break

    factory = ServiceFactory(db_session)
    return factory.create_trade_service()


async def get_sop_service_dependency(db_session: AsyncSession = None) -> ISOPService:
    """FastAPI dependency for SOP service"""
    if db_session is None:
        from app.core.database import get_async_session

        async for session in get_async_session():
            db_session = session
            break

    factory = ServiceFactory(db_session)
    return factory.create_sop_service()


async def get_risk_service_dependency(db_session: AsyncSession = None) -> IRiskService:
    """FastAPI dependency for risk service"""
    if db_session is None:
        from app.core.database import get_async_session

        async for session in get_async_session():
            db_session = session
            break

    factory = ServiceFactory(db_session)
    return factory.create_risk_service()
