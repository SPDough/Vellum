"""
Azure-specific configuration for Otomeshon platform.
"""

import os
from typing import Optional
from functools import lru_cache

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .config import Settings


class AzureSettings(BaseSettings):
    """Azure-specific application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Azure Core Configuration
    azure_tenant_id: Optional[str] = Field(default=None, alias="AZURE_TENANT_ID")
    azure_client_id: Optional[str] = Field(default=None, alias="AZURE_CLIENT_ID")
    azure_client_secret: Optional[str] = Field(default=None, alias="AZURE_CLIENT_SECRET")

    # Azure Key Vault
    azure_key_vault_url: Optional[str] = Field(default=None, alias="AZURE_KEY_VAULT_URL")
    azure_key_vault_tenant_id: Optional[str] = Field(default=None, alias="AZURE_KEY_VAULT_TENANT_ID")
    azure_key_vault_client_id: Optional[str] = Field(default=None, alias="AZURE_KEY_VAULT_CLIENT_ID")
    azure_key_vault_client_secret: Optional[str] = Field(default=None, alias="AZURE_KEY_VAULT_CLIENT_SECRET")

    # Azure Storage
    azure_storage_connection_string: Optional[str] = Field(default=None, alias="AZURE_STORAGE_CONNECTION_STRING")
    azure_storage_account_name: Optional[str] = Field(default=None, alias="AZURE_STORAGE_ACCOUNT_NAME")
    azure_storage_account_key: Optional[str] = Field(default=None, alias="AZURE_STORAGE_ACCOUNT_KEY")

    # Azure Monitor / Application Insights
    applicationinsights_connection_string: Optional[str] = Field(default=None, alias="APPLICATIONINSIGHTS_CONNECTION_STRING")
    applicationinsights_instrumentation_key: Optional[str] = Field(default=None, alias="APPLICATIONINSIGHTS_INSTRUMENTATION_KEY")

    # Azure Container Registry
    acr_login_server: Optional[str] = Field(default=None, alias="ACR_LOGIN_SERVER")
    acr_username: Optional[str] = Field(default=None, alias="ACR_USERNAME")
    acr_password: Optional[str] = Field(default=None, alias="ACR_PASSWORD")

    # Azure Database for PostgreSQL
    azure_postgres_server: Optional[str] = Field(default=None, alias="AZURE_POSTGRES_SERVER")
    azure_postgres_database: Optional[str] = Field(default=None, alias="AZURE_POSTGRES_DATABASE")
    azure_postgres_user: Optional[str] = Field(default=None, alias="AZURE_POSTGRES_USER")
    azure_postgres_password: Optional[str] = Field(default=None, alias="AZURE_POSTGRES_PASSWORD")

    # Azure Cache for Redis
    azure_redis_host: Optional[str] = Field(default=None, alias="AZURE_REDIS_HOST")
    azure_redis_port: int = Field(default=6380, alias="AZURE_REDIS_PORT")
    azure_redis_password: Optional[str] = Field(default=None, alias="AZURE_REDIS_PASSWORD")
    azure_redis_ssl: bool = Field(default=True, alias="AZURE_REDIS_SSL")

    # Azure Service Bus (for Kafka replacement)
    azure_service_bus_connection_string: Optional[str] = Field(default=None, alias="AZURE_SERVICE_BUS_CONNECTION_STRING")
    azure_service_bus_namespace: Optional[str] = Field(default=None, alias="AZURE_SERVICE_BUS_NAMESPACE")

    # Azure Cosmos DB (for Neo4j replacement)
    azure_cosmos_db_endpoint: Optional[str] = Field(default=None, alias="AZURE_COSMOS_DB_ENDPOINT")
    azure_cosmos_db_key: Optional[str] = Field(default=None, alias="AZURE_COSMOS_DB_KEY")
    azure_cosmos_db_database: Optional[str] = Field(default=None, alias="AZURE_COSMOS_DB_DATABASE")

    @validator("azure_key_vault_url")
    def validate_key_vault_url(cls, v):
        if v and not v.startswith("https://"):
            raise ValueError("Azure Key Vault URL must start with https://")
        return v

    @validator("azure_storage_connection_string")
    def validate_storage_connection_string(cls, v):
        if v and not v.startswith("DefaultEndpointsProtocol="):
            raise ValueError("Invalid Azure Storage connection string format")
        return v

    @property
    def is_azure_environment(self) -> bool:
        """Check if running in Azure environment."""
        return bool(
            self.azure_tenant_id or
            self.azure_key_vault_url or
            self.azure_storage_connection_string or
            self.applicationinsights_connection_string
        )

    @property
    def azure_database_url(self) -> Optional[str]:
        """Generate Azure PostgreSQL connection URL."""
        if not all([self.azure_postgres_server, self.azure_postgres_database, self.azure_postgres_user, self.azure_postgres_password]):
            return None
        
        return (
            f"postgresql://{self.azure_postgres_user}:{self.azure_postgres_password}"
            f"@{self.azure_postgres_server}.postgres.database.azure.com:5432/{self.azure_postgres_database}"
            "?sslmode=require"
        )

    @property
    def azure_redis_url(self) -> Optional[str]:
        """Generate Azure Redis connection URL."""
        if not all([self.azure_redis_host, self.azure_redis_password]):
            return None
        
        protocol = "rediss" if self.azure_redis_ssl else "redis"
        return f"{protocol}://:{self.azure_redis_password}@{self.azure_redis_host}:{self.azure_redis_port}/0?ssl={str(self.azure_redis_ssl).lower()}"


@lru_cache()
def get_azure_settings() -> AzureSettings:
    """Get Azure settings singleton."""
    return AzureSettings()


class AzureKeyVault:
    """Azure Key Vault integration for secrets management."""

    def __init__(self, vault_url: str, tenant_id: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.vault_url = vault_url
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._client = None

    def _get_client(self):
        """Get Azure Key Vault client."""
        if self._client is None:
            try:
                from azure.identity import DefaultAzureCredential, ClientSecretCredential
                from azure.keyvault.secrets import SecretClient

                if all([self.tenant_id, self.client_id, self.client_secret]):
                    credential = ClientSecretCredential(
                        tenant_id=self.tenant_id,
                        client_id=self.client_id,
                        client_secret=self.client_secret
                    )
                else:
                    credential = DefaultAzureCredential()

                self._client = SecretClient(vault_url=self.vault_url, credential=credential)
            except ImportError:
                raise ImportError("azure-identity and azure-keyvault-secrets packages are required for Azure Key Vault integration")
        
        return self._client

    def get_secret(self, secret_name: str) -> str:
        """Get secret from Azure Key Vault."""
        client = self._get_client()
        return client.get_secret(secret_name).value

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        """Set secret in Azure Key Vault."""
        client = self._get_client()
        client.set_secret(secret_name, secret_value)


class AzureStorage:
    """Azure Blob Storage integration."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._client = None

    def _get_client(self):
        """Get Azure Blob Storage client."""
        if self._client is None:
            try:
                from azure.storage.blob import BlobServiceClient
                self._client = BlobServiceClient.from_connection_string(self.connection_string)
            except ImportError:
                raise ImportError("azure-storage-blob package is required for Azure Storage integration")
        
        return self._client

    def upload_blob(self, container_name: str, blob_name: str, data: bytes) -> str:
        """Upload blob to Azure Storage."""
        client = self._get_client()
        container_client = client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(data, overwrite=True)
        return blob_client.url

    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download blob from Azure Storage."""
        client = self._get_client()
        container_client = client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        return blob_client.download_blob().readall()


class AzureMonitor:
    """Azure Monitor / Application Insights integration."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self._tracer = None

    def _get_tracer(self):
        """Get Azure Monitor tracer."""
        if self._tracer is None:
            try:
                from opencensus.ext.azure.trace_exporter import AzureExporter
                from opencensus.trace.tracer import Tracer
                from opencensus.trace.samplers import ProbabilitySampler

                exporter = AzureExporter(connection_string=self.connection_string)
                self._tracer = Tracer(exporter=exporter, sampler=ProbabilitySampler(1.0))
            except ImportError:
                raise ImportError("opencensus-ext-azure package is required for Azure Monitor integration")
        
        return self._tracer

    def trace_operation(self, operation_name: str):
        """Trace an operation with Azure Monitor."""
        tracer = self._get_tracer()
        return tracer.span(name=operation_name)

    def log_event(self, event_name: str, properties: dict = None):
        """Log custom event to Azure Monitor."""
        try:
            from opencensus.ext.azure.log_exporter import AzureLogHandler
            import logging

            logger = logging.getLogger(__name__)
            handler = AzureLogHandler(connection_string=self.connection_string)
            logger.addHandler(handler)
            logger.info(f"Event: {event_name}", extra=properties or {})
        except ImportError:
            # Fallback to standard logging if Azure logging not available
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Azure Event: {event_name} - {properties}")


def get_azure_key_vault() -> Optional[AzureKeyVault]:
    """Get Azure Key Vault instance if configured."""
    settings = get_azure_settings()
    if settings.azure_key_vault_url:
        return AzureKeyVault(
            vault_url=settings.azure_key_vault_url,
            tenant_id=settings.azure_key_vault_tenant_id,
            client_id=settings.azure_key_vault_client_id,
            client_secret=settings.azure_key_vault_client_secret
        )
    return None


def get_azure_storage() -> Optional[AzureStorage]:
    """Get Azure Storage instance if configured."""
    settings = get_azure_settings()
    if settings.azure_storage_connection_string:
        return AzureStorage(settings.azure_storage_connection_string)
    return None


def get_azure_monitor() -> Optional[AzureMonitor]:
    """Get Azure Monitor instance if configured."""
    settings = get_azure_settings()
    if settings.applicationinsights_connection_string:
        return AzureMonitor(settings.applicationinsights_connection_string)
    return None
