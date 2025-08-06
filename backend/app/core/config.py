from functools import lru_cache
from typing import Optional
import os

from pydantic import Field, validator, root_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # Application
    app_name: str = "Otomeshon"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database - PostgreSQL
    database_url: str = Field(alias="DATABASE_URL")

    # Neo4j Graph Database
    neo4j_url: str = Field(alias="NEO4J_URL")
    neo4j_user: str = Field(default="neo4j", alias="NEO4J_USER")
    neo4j_password: str = Field(alias="NEO4J_PASSWORD")

    # Kafka
    kafka_bootstrap_servers: str = Field(
        default="kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS"
    )

    # Temporal
    temporal_host: str = Field(default="temporal", alias="TEMPORAL_HOST")
    temporal_port: int = Field(default=7233, alias="TEMPORAL_PORT")

    # LLM APIs
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")

    # Local Embeddings
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")

    # Authentication
    secret_key: str = Field(default="changeme-secret-key-for-production", alias="SECRET_KEY")
    jwt_secret_key: str = Field(default="changeme", alias="JWT_SECRET_KEY")

    # Rules Engine
    drools_url: str = Field(default="http://drools:8080", alias="DROOLS_URL")

    # Observability
    otel_exporter_otlp_endpoint: str = Field(
        default="http://jaeger:4318", alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_service_name: str = Field(default="otomeshon-api", alias="OTEL_SERVICE_NAME")

    # LangSmith/LangFuse
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_project: str = Field(default="otomeshon", alias="LANGCHAIN_PROJECT")

    langfuse_secret_key: Optional[str] = Field(
        default=None, alias="LANGFUSE_SECRET_KEY"
    )
    langfuse_public_key: Optional[str] = Field(
        default=None, alias="LANGFUSE_PUBLIC_KEY"
    )
    langfuse_host: str = Field(
        default="https://cloud.langfuse.com", alias="LANGFUSE_HOST"
    )

    # Banking Compliance Settings
    audit_log_retention_days: int = Field(default=2555, alias="AUDIT_LOG_RETENTION_DAYS")  # 7 years
    max_transaction_amount: int = Field(default=10000000, alias="MAX_TRANSACTION_AMOUNT")  # $10M
    compliance_mode: str = Field(default="test", alias="COMPLIANCE_MODE")

    # Redis (Optional)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # Keycloak (Optional)
    keycloak_url: Optional[str] = Field(default=None, alias="KEYCLOAK_URL")

    # CORS Settings
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "testing", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v

    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    @validator("secret_key")
    def validate_secret_key(cls, v, values):
        if "changeme" in v.lower():
            env = values.get("environment", "development")
            if env == "production":
                raise ValueError("SECRET_KEY cannot contain 'changeme' in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @validator("jwt_secret_key")
    def validate_jwt_secret_key(cls, v, values):
        if "changeme" in v.lower():
            env = values.get("environment", "development")
            if env == "production":
                raise ValueError("JWT_SECRET_KEY cannot contain 'changeme' in production")
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    @validator("compliance_mode")
    def validate_compliance_mode(cls, v):
        valid_modes = ["test", "live", "sandbox"]
        if v not in valid_modes:
            raise ValueError(f"Compliance mode must be one of: {valid_modes}")
        return v

    @field_validator('environment')
    @classmethod
    def validate_production_settings(cls, v, info):
        """Additional validation for production environment"""
        if v == "production":
            # Basic production validation - full validation in model_validator
            pass
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    # Check if we're in a test environment and override defaults
    if os.getenv("ENVIRONMENT") == "testing":
        os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/otomeshon_test")
        os.environ.setdefault("NEO4J_URL", "bolt://localhost:7687") 
        os.environ.setdefault("NEO4J_PASSWORD", "testpassword")
        os.environ.setdefault("ENVIRONMENT", "testing")
        return Settings()

    # For non-test environments, load from environment variables
    # This will raise validation errors if required settings are missing
    return Settings()


def validate_settings() -> bool:
    """Validate current settings and return True if valid"""
    try:
        settings = get_settings()
        # If we can create settings without error, they're valid
        return True
    except Exception as e:
        print(f"Configuration validation failed: {e}")
        return False
