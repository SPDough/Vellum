from functools import lru_cache
from typing import Optional

from pydantic import Field
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
    keycloak_url: str = Field(default="http://keycloak:8080", alias="KEYCLOAK_URL")
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
