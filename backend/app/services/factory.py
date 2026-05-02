"""
Service factory implementation for Otomeshon Banking Platform.

Concrete services that are not yet implemented are satisfied by stubs in
`banking_stub_services` so imports and DI never fail at module load time.
"""

from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.services.banking_stub_services import (
    StubAuditService,
    StubComplianceService,
    StubRiskService,
    StubSOPService,
    StubTradeService,
    StubUserService,
)
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
    """Creates service instances for the async SQLAlchemy session."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.settings = get_settings()
        self._service_cache: dict[str, Any] = {}

    def create_trade_service(self) -> ITradeService:
        if "trade_service" not in self._service_cache:
            self._service_cache["trade_service"] = StubTradeService()
        return self._service_cache["trade_service"]

    def create_sop_service(self) -> ISOPService:
        if "sop_service" not in self._service_cache:
            self._service_cache["sop_service"] = StubSOPService()
        return self._service_cache["sop_service"]

    def create_risk_service(self) -> IRiskService:
        if "risk_service" not in self._service_cache:
            self._service_cache["risk_service"] = StubRiskService()
        return self._service_cache["risk_service"]

    def create_compliance_service(self) -> IComplianceService:
        if "compliance_service" not in self._service_cache:
            self._service_cache["compliance_service"] = StubComplianceService()
        return self._service_cache["compliance_service"]

    def create_user_service(self) -> IUserService:
        if "user_service" not in self._service_cache:
            self._service_cache["user_service"] = StubUserService()
        return self._service_cache["user_service"]

    def create_audit_service(self) -> IAuditService:
        if "audit_service" not in self._service_cache:
            self._service_cache["audit_service"] = StubAuditService()
        return self._service_cache["audit_service"]

    def get_service(self, service_name: str):
        service_creators = {
            "trade": self.create_trade_service,
            "sop": self.create_sop_service,
            "risk": self.create_risk_service,
            "compliance": self.create_compliance_service,
            "user": self.create_user_service,
            "audit": self.create_audit_service,
        }
        creator = service_creators.get(service_name)
        if creator:
            return creator()
        raise ValueError(f"Unknown service: {service_name}")

    def clear_cache(self) -> None:
        self._service_cache.clear()


class BankingServiceRegistry:
    """Registry for banking-specific service factory instances."""

    def __init__(self) -> None:
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

    def register_factory(self, environment: str, factory: ServiceFactory) -> None:
        self._factories[environment] = factory

    def get_factory(self, environment: str) -> ServiceFactory:
        factory = self._factories.get(environment)
        if factory is None:
            raise ValueError(f"No factory registered for environment: {environment}")
        return factory

    def get_environment_config(self, environment: str) -> dict[str, Any]:
        return self._environment_configs.get(environment, {})


class ServiceLocator:
    """Service locator for dependency injection (optional global wiring)."""

    _instance: Optional["ServiceLocator"] = None
    _factory: Optional[ServiceFactory] = None

    def __new__(cls) -> "ServiceLocator":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, factory: ServiceFactory) -> None:
        cls._factory = factory

    @classmethod
    def get_trade_service(cls) -> ITradeService:
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_trade_service()

    @classmethod
    def get_sop_service(cls) -> ISOPService:
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_sop_service()

    @classmethod
    def get_risk_service(cls) -> IRiskService:
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_risk_service()

    @classmethod
    def get_compliance_service(cls) -> IComplianceService:
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_compliance_service()

    @classmethod
    def get_user_service(cls) -> IUserService:
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_user_service()

    @classmethod
    def get_audit_service(cls) -> IAuditService:
        if cls._factory is None:
            raise RuntimeError("ServiceLocator not initialized")
        return cls._factory.create_audit_service()


def get_service_factory(db_session: AsyncSession) -> ServiceFactory:
    return ServiceFactory(db_session)


def get_banking_services(db_session: AsyncSession) -> dict[str, Any]:
    factory = ServiceFactory(db_session)
    return {
        "trade": factory.create_trade_service(),
        "sop": factory.create_sop_service(),
        "risk": factory.create_risk_service(),
        "compliance": factory.create_compliance_service(),
        "user": factory.create_user_service(),
        "audit": factory.create_audit_service(),
    }


async def get_trade_service_dependency(
    db_session: AsyncSession | None = None,
) -> ITradeService:
    if db_session is None:
        from app.core.database import get_async_session

        async for session in get_async_session():
            db_session = session
            break
    return ServiceFactory(db_session).create_trade_service()


async def get_sop_service_dependency(
    db_session: AsyncSession | None = None,
) -> ISOPService:
    if db_session is None:
        from app.core.database import get_async_session

        async for session in get_async_session():
            db_session = session
            break
    return ServiceFactory(db_session).create_sop_service()


async def get_risk_service_dependency(
    db_session: AsyncSession | None = None,
) -> IRiskService:
    if db_session is None:
        from app.core.database import get_async_session

        async for session in get_async_session():
            db_session = session
            break
    return ServiceFactory(db_session).create_risk_service()
