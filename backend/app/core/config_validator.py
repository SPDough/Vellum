"""
Configuration validation and health checks for Otomeshon Banking Platform
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import structlog
from pydantic import ValidationError

logger = structlog.get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration validation fails"""

    pass


class ConfigValidator:
    """Validates configuration settings for banking compliance and functionality"""

    def __init__(self, settings):
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> Tuple[bool, List[str], List[str]]:
        """Run all validation checks"""
        self.errors.clear()
        self.warnings.clear()

        # Core validation
        self._validate_environment()
        self._validate_security_settings()
        self._validate_database_config()

        # Optional feature validation
        if hasattr(self.settings, "neo4j_url"):
            self._validate_neo4j_config()

        if hasattr(self.settings, "openai_api_key"):
            self._validate_ai_config()

        if hasattr(self.settings, "keycloak_url"):
            self._validate_keycloak_config()

        # Banking-specific validation
        self._validate_banking_compliance()

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_environment(self):
        """Validate basic environment settings"""
        # Check environment is valid
        valid_environments = ["development", "testing", "staging", "production"]
        if self.settings.environment not in valid_environments:
            self.errors.append(
                f"Invalid environment '{self.settings.environment}'. Must be one of: {valid_environments}"
            )

        # Check log level is valid
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.settings.log_level.upper() not in valid_log_levels:
            self.errors.append(
                f"Invalid log level '{self.settings.log_level}'. Must be one of: {valid_log_levels}"
            )

        # Environment-specific checks
        if self.settings.environment == "production":
            if self.settings.log_level.upper() == "DEBUG":
                self.warnings.append(
                    "DEBUG logging enabled in production - consider using INFO or higher"
                )

    def _validate_security_settings(self):
        """Validate security configuration"""
        # Check secret keys are not default values
        insecure_keys = ["changeme", "your-secret-key", "secret", "password", "admin"]

        if hasattr(self.settings, "secret_key"):
            if any(
                insecure in self.settings.secret_key.lower()
                for insecure in insecure_keys
            ):
                self.errors.append("SECRET_KEY appears to be a default/insecure value")

            if len(self.settings.secret_key) < 32:
                self.errors.append("SECRET_KEY should be at least 32 characters long")

        if hasattr(self.settings, "jwt_secret_key"):
            if any(
                insecure in self.settings.jwt_secret_key.lower()
                for insecure in insecure_keys
            ):
                self.errors.append(
                    "JWT_SECRET_KEY appears to be a default/insecure value"
                )

            if len(self.settings.jwt_secret_key) < 32:
                self.errors.append(
                    "JWT_SECRET_KEY should be at least 32 characters long"
                )

        # Production security checks
        if self.settings.environment == "production":
            if hasattr(self.settings, "cors_origins"):
                if "*" in str(self.settings.cors_origins):
                    self.errors.append(
                        "CORS origins should not include '*' in production"
                    )

    def _validate_database_config(self):
        """Validate database configuration"""
        if hasattr(self.settings, "database_url"):
            parsed = urlparse(self.settings.database_url)

            # Check scheme
            if parsed.scheme not in ["postgresql", "postgresql+psycopg2"]:
                self.errors.append(f"Unsupported database scheme: {parsed.scheme}")

            # Check hostname
            if not parsed.hostname:
                self.errors.append("Database URL missing hostname")

            # Check database name
            if not parsed.path or parsed.path == "/":
                self.errors.append("Database URL missing database name")

            # Security checks
            if parsed.password and "changeme" in parsed.password.lower():
                self.warnings.append("Database password appears to be default value")

            # Production checks
            if self.settings.environment == "production":
                if parsed.hostname in ["localhost", "127.0.0.1"]:
                    self.warnings.append("Using localhost database in production")

    def _validate_neo4j_config(self):
        """Validate Neo4j configuration"""
        if hasattr(self.settings, "neo4j_url"):
            parsed = urlparse(self.settings.neo4j_url)

            if parsed.scheme not in ["bolt", "neo4j"]:
                self.errors.append(f"Invalid Neo4j scheme: {parsed.scheme}")

            if hasattr(self.settings, "neo4j_password"):
                if "changeme" in self.settings.neo4j_password.lower():
                    self.warnings.append("Neo4j password appears to be default value")

    def _validate_ai_config(self):
        """Validate AI/LLM configuration"""
        # OpenAI API key format validation
        if hasattr(self.settings, "openai_api_key") and self.settings.openai_api_key:
            if not self.settings.openai_api_key.startswith("sk-"):
                self.warnings.append(
                    "OpenAI API key format may be invalid (should start with 'sk-')"
                )

        # Anthropic API key format validation
        if (
            hasattr(self.settings, "anthropic_api_key")
            and self.settings.anthropic_api_key
        ):
            if not self.settings.anthropic_api_key.startswith("sk-ant-"):
                self.warnings.append(
                    "Anthropic API key format may be invalid (should start with 'sk-ant-')"
                )

    def _validate_keycloak_config(self):
        """Validate Keycloak configuration"""
        if hasattr(self.settings, "keycloak_url"):
            parsed = urlparse(self.settings.keycloak_url)

            if parsed.scheme not in ["http", "https"]:
                self.errors.append(f"Invalid Keycloak URL scheme: {parsed.scheme}")

            if self.settings.environment == "production" and parsed.scheme == "http":
                self.warnings.append(
                    "Using HTTP for Keycloak in production - consider HTTPS"
                )

    def _validate_banking_compliance(self):
        """Validate banking-specific compliance settings"""
        # Check audit logging is enabled in production
        if self.settings.environment == "production":
            if not hasattr(self.settings, "audit_log_retention_days"):
                self.warnings.append(
                    "Audit log retention not configured - required for banking compliance"
                )
            else:
                # Banking regulations typically require 7 years (2555 days)
                if self.settings.audit_log_retention_days < 2555:
                    self.warnings.append(
                        "Audit log retention less than 7 years - may not meet banking compliance"
                    )

        # Check transaction limits are set
        if hasattr(self.settings, "max_transaction_amount"):
            if self.settings.max_transaction_amount > 100000000:  # $100M
                self.warnings.append(
                    "Maximum transaction amount very high - consider risk controls"
                )


class ConfigHealthChecker:
    """Performs runtime health checks for configuration-dependent services"""

    def __init__(self, settings):
        self.settings = settings

    async def check_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all configured services"""
        results = {}

        # Database connectivity
        if hasattr(self.settings, "database_url"):
            results["database"] = await self._check_database()

        # Neo4j connectivity
        if hasattr(self.settings, "neo4j_url"):
            results["neo4j"] = await self._check_neo4j()

        # Redis connectivity
        if hasattr(self.settings, "redis_url"):
            results["redis"] = await self._check_redis()

        # External API availability
        if hasattr(self.settings, "openai_api_key") and self.settings.openai_api_key:
            results["openai"] = await self._check_openai()

        if (
            hasattr(self.settings, "anthropic_api_key")
            and self.settings.anthropic_api_key
        ):
            results["anthropic"] = await self._check_anthropic()

        return results

    async def _check_database(self) -> Dict[str, Any]:
        """Check PostgreSQL database connectivity"""
        try:
            import asyncpg

            parsed = urlparse(self.settings.database_url)

            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip("/"),
                timeout=5.0,
            )

            # Test basic query
            result = await conn.fetchval("SELECT version()")
            await conn.close()

            return {
                "status": "healthy",
                "message": "Database connection successful",
                "version": result,
                "response_time_ms": 0,  # Would need timing logic
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Database connection failed: {str(e)}",
                "error": str(e),
            }

    async def _check_neo4j(self) -> Dict[str, Any]:
        """Check Neo4j database connectivity"""
        try:
            from neo4j import AsyncGraphDatabase

            driver = AsyncGraphDatabase.driver(
                self.settings.neo4j_url,
                auth=(self.settings.neo4j_user, self.settings.neo4j_password),
            )

            async with driver.session() as session:
                result = await session.run("RETURN 'Neo4j connected' as message")
                record = await result.single()
                message = record["message"] if record else "No response"

            await driver.close()

            return {"status": "healthy", "message": message, "response_time_ms": 0}

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Neo4j connection failed: {str(e)}",
                "error": str(e),
            }

    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            import redis.asyncio as redis

            r = redis.from_url(self.settings.redis_url)
            await r.ping()
            info = await r.info()
            await r.close()

            return {
                "status": "healthy",
                "message": "Redis connection successful",
                "version": info.get("redis_version"),
                "response_time_ms": 0,
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Redis connection failed: {str(e)}",
                "error": str(e),
            }

    async def _check_openai(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
                    timeout=5.0,
                )

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "message": "OpenAI API accessible",
                        "response_time_ms": 0,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"OpenAI API returned {response.status_code}",
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"OpenAI API check failed: {str(e)}",
                "error": str(e),
            }

    async def _check_anthropic(self) -> Dict[str, Any]:
        """Check Anthropic API connectivity"""
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                # Anthropic doesn't have a models endpoint, so we'll just check auth
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Authorization": f"Bearer {self.settings.anthropic_api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                    timeout=5.0,
                )

                if response.status_code in [200, 400]:  # 400 is OK for validation
                    return {
                        "status": "healthy",
                        "message": "Anthropic API accessible",
                        "response_time_ms": 0,
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"Anthropic API returned {response.status_code}",
                        "error": response.text,
                    }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"Anthropic API check failed: {str(e)}",
                "error": str(e),
            }


def validate_config_cli():
    """CLI tool for configuration validation"""
    try:
        from app.core.config import get_settings

        settings = get_settings()

        validator = ConfigValidator(settings)
        is_valid, errors, warnings = validator.validate_all()

        print("🏦 Otomeshon Banking Platform - Configuration Validation")
        print("=" * 60)
        print(f"Environment: {settings.environment}")
        print(f"App Name: {settings.app_name}")
        print()

        if errors:
            print("❌ ERRORS:")
            for error in errors:
                print(f"  • {error}")
            print()

        if warnings:
            print("⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  • {warning}")
            print()

        if is_valid:
            print("✅ Configuration validation passed!")

            # Run health checks if requested
            if "--health-check" in sys.argv:
                print("\n🔍 Running health checks...")
                health_checker = ConfigHealthChecker(settings)
                results = asyncio.run(health_checker.check_all_services())

                for service, result in results.items():
                    status_icon = "✅" if result["status"] == "healthy" else "❌"
                    print(f"  {status_icon} {service}: {result['message']}")
        else:
            print("❌ Configuration validation failed!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    validate_config_cli()
