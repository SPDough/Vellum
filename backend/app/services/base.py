"""
Base service classes and interfaces for Otomeshon Banking Platform
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic, Protocol, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel


# Type variables for generic services
T = TypeVar('T')
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class ServiceError(Exception):
    """Base exception for service layer errors"""
    pass


class ValidationError(ServiceError):
    """Raised when data validation fails"""
    pass


class NotFoundError(ServiceError):
    """Raised when requested resource is not found"""
    pass


class PermissionError(ServiceError):
    """Raised when user lacks required permissions"""
    pass


class BusinessRuleError(ServiceError):
    """Raised when business rule validation fails"""
    pass


class AuditLevel(Enum):
    """Audit logging levels for banking compliance"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ServiceContext:
    """Context information for service operations"""
    user_id: str
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    transaction_id: Optional[str] = None
    audit_level: AuditLevel = AuditLevel.MEDIUM

    def __post_init__(self):
        if self.transaction_id is None:
            self.transaction_id = str(uuid.uuid4())


@dataclass
class OperationResult:
    """Result of a service operation with metadata"""
    success: bool
    data: Any = None
    message: Optional[str] = None
    errors: Optional[List[str]] = None
    audit_trail: Optional[List[Dict[str, Any]]] = None
    performance_metrics: Optional[Dict[str, float]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.audit_trail is None:
            self.audit_trail = []


class AuditableOperation(Protocol):
    """Protocol for operations that require audit logging"""

    def get_audit_data(self) -> Dict[str, Any]:
        """Return data to be logged for audit purposes"""
        ...


class BaseService(ABC, Generic[T]):
    """
    Base service class with common banking operations and audit support
    """

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    @abstractmethod
    async def create(self, data: CreateSchemaType, context: ServiceContext) -> OperationResult:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str, context: ServiceContext) -> OperationResult:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: UpdateSchemaType, context: ServiceContext) -> OperationResult:
        """Update an existing entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: str, context: ServiceContext) -> OperationResult:
        """Delete an entity (soft delete for compliance)"""
        pass

    async def audit_operation(
        self,
        context: ServiceContext,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log operation for audit compliance"""

        from app.services.audit_service import AuditService

        audit_service = AuditService(self.db)

        await audit_service.log_operation(
            user_id=context.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            session_id=context.session_id,
            ip_address=context.ip_address,
            user_agent=context.user_agent,
            before_state=before_state,
            after_state=after_state,
            success=success,
            error_message=error_message,
            additional_data=additional_data
        )

    def validate_permissions(self, context: ServiceContext, required_permission: str) -> bool:
        """Validate user permissions for operation"""
        # This would integrate with your permission system
        # For now, return True for admin users
        return context.user_id.endswith("admin@otomeshon.com")

    def validate_business_rules(self, data: Any, operation: str) -> List[str]:
        """Validate business rules - to be implemented by subclasses"""
        return []


class CRUDService(BaseService[T]):
    """
    Extended CRUD service with banking-specific features
    """

    def __init__(self, db_session: AsyncSession, model_class: type):
        super().__init__(db_session)
        self.model_class = model_class

    async def list(
        self,
        context: ServiceContext,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> OperationResult:
        """List entities with filtering and pagination"""

        try:
            # Apply filters and pagination
            from sqlalchemy import select
            from sqlalchemy.sql import Select
            query: Select = select(self.model_class)

            if filters:
                for key, value in filters.items():
                    if hasattr(self.model_class, key):
                        query = query.where(getattr(self.model_class, key) == value)

            if sort_by and hasattr(self.model_class, sort_by):
                query = query.order_by(getattr(self.model_class, sort_by))

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            result = await self.db.execute(query)
            items = result.scalars().all()

            # Audit the list operation
            await self.audit_operation(
                context=context,
                action="list",
                resource_type=self.model_class.__name__,
                additional_data={
                    "filters": filters,
                    "page": page,
                    "page_size": page_size,
                    "result_count": len(items)
                }
            )

            return OperationResult(
                success=True,
                data=items,
                message=f"Retrieved {len(items)} {self.model_class.__name__} records"
            )

        except Exception as e:
            await self.audit_operation(
                context=context,
                action="list",
                resource_type=self.model_class.__name__,
                success=False,
                error_message=str(e)
            )

            return OperationResult(
                success=False,
                errors=[f"Failed to list {self.model_class.__name__}: {str(e)}"]
            )

    async def soft_delete(self, entity_id: str, context: ServiceContext) -> OperationResult:
        """Soft delete for banking compliance (maintains audit trail)"""

        try:
            entity = await self.db.get(self.model_class, entity_id)

            if not entity:
                return OperationResult(
                    success=False,
                    errors=[f"{self.model_class.__name__} not found"]
                )

            # Store before state for audit
            before_state = {
                "id": entity.id,
                "status": getattr(entity, 'status', None),
                "is_active": getattr(entity, 'is_active', None)
            }

            # Perform soft delete
            if hasattr(entity, 'is_active'):
                entity.is_active = False
            if hasattr(entity, 'status'):
                entity.status = 'DELETED'
            if hasattr(entity, 'deleted_at'):
                entity.deleted_at = datetime.utcnow()

            await self.db.commit()

            # Audit the deletion
            await self.audit_operation(
                context=context,
                action="soft_delete",
                resource_type=self.model_class.__name__,
                resource_id=entity_id,
                before_state=before_state,
                after_state={"status": "DELETED", "is_active": False}
            )

            return OperationResult(
                success=True,
                data=entity,
                message=f"{self.model_class.__name__} soft deleted successfully"
            )

        except Exception as e:
            await self.db.rollback()

            await self.audit_operation(
                context=context,
                action="soft_delete",
                resource_type=self.model_class.__name__,
                resource_id=entity_id,
                success=False,
                error_message=str(e)
            )

            return OperationResult(
                success=False,
                errors=[f"Failed to delete {self.model_class.__name__}: {str(e)}"]
            )


class TransactionalService(CRUDService[T]):
    """
    Service with transaction management for complex banking operations
    """

    async def execute_transaction(
        self,
        context: ServiceContext,
        operations: List[Callable],
        rollback_on_error: bool = True
    ) -> OperationResult:
        """Execute multiple operations in a transaction"""

        transaction_start = datetime.utcnow()
        results = []

        try:
            # Begin transaction
            await self.db.begin()

            # Execute all operations
            for operation in operations:
                result = await operation()
                results.append(result)

                if not result.success and rollback_on_error:
                    raise BusinessRuleError(f"Operation failed: {result.errors}")

            # Commit transaction
            await self.db.commit()

            # Audit successful transaction
            await self.audit_operation(
                context=context,
                action="transaction",
                resource_type="multi_operation",
                additional_data={
                    "operation_count": len(operations),
                    "duration_ms": (datetime.utcnow() - transaction_start).total_seconds() * 1000,
                    "success": True
                }
            )

            return OperationResult(
                success=True,
                data=results,
                message=f"Transaction completed successfully with {len(operations)} operations"
            )

        except Exception as e:
            await self.db.rollback()

            # Audit failed transaction
            await self.audit_operation(
                context=context,
                action="transaction",
                resource_type="multi_operation",
                success=False,
                error_message=str(e),
                additional_data={
                    "operation_count": len(operations),
                    "duration_ms": (datetime.utcnow() - transaction_start).total_seconds() * 1000
                }
            )

            return OperationResult(
                success=False,
                errors=[f"Transaction failed: {str(e)}"],
                data=results
            )


class BankingComplianceService(TransactionalService[T]):
    """
    Service with banking compliance features
    """

    def __init__(self, db_session: AsyncSession, model_class: type):
        super().__init__(db_session, model_class)
        self.compliance_rules: List[Callable] = []

    def add_compliance_rule(self, rule: Callable):
        """Add a compliance rule to be checked on operations"""
        self.compliance_rules.append(rule)

    async def validate_compliance(self, data: Any, operation: str, context: ServiceContext) -> List[str]:
        """Validate all compliance rules"""
        errors = []

        for rule in self.compliance_rules:
            try:
                result = await rule(data, operation, context)
                if not result:
                    errors.append(f"Compliance rule failed for {operation}")
            except Exception as e:
                errors.append(f"Compliance validation error: {str(e)}")

        return errors

    async def create_with_compliance(
        self,
        data: CreateSchemaType,
        context: ServiceContext
    ) -> OperationResult:
        """Create entity with full compliance validation"""

        # Validate compliance first
        compliance_errors = await self.validate_compliance(data, "create", context)
        if compliance_errors:
            return OperationResult(
                success=False,
                errors=compliance_errors
            )

        # Proceed with creation
        return await self.create(data, context)

    async def get_audit_trail(self, entity_id: str, context: ServiceContext) -> OperationResult:
        """Get complete audit trail for an entity"""

        try:
            from app.services.audit_service import AuditService

            audit_service = AuditService(self.db)
            audit_records = await audit_service.get_entity_audit_trail(
                resource_type=self.model_class.__name__,
                resource_id=entity_id
            )

            return OperationResult(
                success=True,
                data=audit_records,
                message=f"Retrieved audit trail for {self.model_class.__name__} {entity_id}"
            )

        except Exception as e:
            return OperationResult(
                success=False,
                errors=[f"Failed to retrieve audit trail: {str(e)}"]
            )