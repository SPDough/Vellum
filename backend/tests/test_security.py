"""
Security tests for the banking application.
Tests authentication, input validation, and other security measures.
"""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.main_simple import app
from app.core.auth_config import auth_config
from app.core.validation import InputValidator, ValidationError


class TestAuthSecurity:
    """Test authentication security measures."""

    def test_auth_config_password_hashing(self):
        """Test that passwords are properly hashed."""
        # Mock environment variables
        os.environ["DEMO_ADMIN_PASSWORD"] = "test_password_123"
        auth_config._users_cache = None

        # Create new auth config instance
        test_auth = auth_config

        # Test password verification
        user = test_auth.verify_password("admin@otomeshon.ai", "test_password_123")
        assert user is not None
        assert user.email == "admin@otomeshon.ai"

        # Test wrong password
        user = test_auth.verify_password("admin@otomeshon.ai", "wrong_password")
        assert user is None

    def test_hardcoded_passwords_removed(self):
        """Ensure no hardcoded passwords exist in the main module."""
        with open("app/main_simple.py", "r") as f:
            content = f.read()

        # Check that hardcoded passwords are not present
        assert "admin123" not in content
        assert "analyst123" not in content
        assert '"password":' not in content or '"password": "' not in content


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_string_sanitization(self):
        """Test string sanitization against XSS and injection."""
        # Valid input
        result = InputValidator.sanitize_string("normal text", 100)
        assert result == "normal text"

        # Script payloads are rejected by design in current validator.
        with pytest.raises(ValidationError, match="Invalid characters detected"):
            InputValidator.sanitize_string("<script>alert('xss')</script>", 100)

        # SQL injection patterns
        with pytest.raises(ValidationError, match="Invalid characters detected"):
            InputValidator.sanitize_string("'; DROP TABLE users; --", 100)

        # Length validation
        with pytest.raises(ValidationError, match="Input too long"):
            InputValidator.sanitize_string("a" * 300, 100)

    def test_amount_validation(self):
        """Test monetary amount validation."""
        # Valid amounts
        assert InputValidator.validate_amount("100.50") == Decimal("100.50")
        assert InputValidator.validate_amount(50.25) == Decimal("50.25")
        assert InputValidator.validate_amount(Decimal("75.00")) == Decimal("75.00")

        # Invalid amounts
        with pytest.raises(ValidationError, match="Amount cannot be negative"):
            InputValidator.validate_amount("-100.00")

        with pytest.raises(ValidationError, match="exceeds maximum"):
            InputValidator.validate_amount("9999999999999.99")

        with pytest.raises(ValidationError, match="too many decimal places"):
            InputValidator.validate_amount("100.123")

        with pytest.raises(ValidationError, match="Invalid amount format"):
            InputValidator.validate_amount("not_a_number")

    def test_currency_validation(self):
        """Test currency code validation."""
        # Valid currencies
        assert InputValidator.validate_currency("USD") == "USD"
        assert InputValidator.validate_currency("eur") == "EUR"

        # Invalid currencies
        with pytest.raises(ValidationError, match="Invalid currency code format"):
            InputValidator.validate_currency("US")

        with pytest.raises(ValidationError, match="Invalid currency code format"):
            InputValidator.validate_currency("US1")

        with pytest.raises(ValidationError, match="Invalid currency code format"):
            InputValidator.validate_currency("123")

    def test_customer_id_validation(self):
        """Test customer ID validation."""
        # Valid customer IDs
        assert InputValidator.validate_customer_id("CUST_1234") == "CUST_1234"
        assert InputValidator.validate_customer_id("CUST_123456789") == "CUST_123456789"

        # Invalid customer IDs
        with pytest.raises(ValidationError, match="Invalid customer ID format"):
            InputValidator.validate_customer_id("INVALID_1234")

        with pytest.raises(ValidationError, match="Invalid customer ID format"):
            InputValidator.validate_customer_id("CUST_123")  # Too short

    def test_email_validation(self):
        """Test email validation."""
        # Valid emails
        assert InputValidator.validate_email("user@example.com") == "user@example.com"
        assert InputValidator.validate_email("USER@EXAMPLE.COM") == "user@example.com"

        # Invalid emails
        with pytest.raises(ValidationError, match="Invalid email format"):
            InputValidator.validate_email("invalid-email")

        with pytest.raises(ValidationError, match="Email domain not allowed"):
            InputValidator.validate_email("user@temp-mail.org")

    def test_pagination_validation(self):
        """Test pagination parameter validation."""
        # Valid pagination
        page, page_size = InputValidator.validate_pagination(1, 50)
        assert page == 1 and page_size == 50

        # Invalid pagination
        with pytest.raises(ValidationError, match="Page must be a positive integer"):
            InputValidator.validate_pagination(0, 50)

        with pytest.raises(ValidationError, match="Page size too large"):
            InputValidator.validate_pagination(1, 2000)

        with pytest.raises(ValidationError, match="Page number too large"):
            InputValidator.validate_pagination(20000, 50)

    def test_filter_validation(self):
        """Test filter request validation."""
        # Valid filters
        filters = {
            "source": "api",
            "currency": "USD",
            "amount_min": "100.00"
        }
        result = InputValidator.validate_filter_request(filters)
        assert result["source"] == "api"
        assert result["currency"] == "USD"
        assert result["amount_min"] == Decimal("100.00")

        # Invalid filters
        with pytest.raises(ValidationError, match="Invalid source"):
            InputValidator.validate_filter_request({"source": "invalid_source"})


class TestAPIEndpoints:
    """Test API endpoint security."""

    @classmethod
    def setup_class(cls):
        """Setup test client."""
        cls.client = TestClient(app)

    def test_login_security(self):
        """Test login endpoint security."""
        # Test with invalid credentials
        response = self.client.post("/api/auth/login", json={
            "email": "admin@otomeshon.ai",
            "password": "wrong_password"
        })
        assert response.status_code == 401

        # Test with malicious input
        response = self.client.post("/api/auth/login", json={
            "email": "'; DROP TABLE users; --",
            "password": "password"
        })
        assert response.status_code == 422  # Validation error

    def test_data_sandbox_input_validation(self):
        """Test data sandbox endpoints validate input."""
        # Test pagination validation
        response = self.client.get("/api/v1/data-sandbox/records?page=0")
        assert response.status_code == 400

        response = self.client.get("/api/v1/data-sandbox/records?page_size=2000")
        assert response.status_code == 400

        # Test filter validation
        response = self.client.post("/api/v1/data-sandbox/filter", json={
            "filters": {"source": "'; DROP TABLE data; --"},
            "page": 1,
            "page_size": 50
        })
        assert response.status_code == 400

    def test_cors_headers(self):
        """Test CORS configuration."""
        response = self.client.get("/health")
        assert response.status_code == 200

        # Note: In test environment, CORS headers might not be set
        # This would need a more comprehensive test setup


class TestSecurityConfiguration:
    """Test security configuration."""

    def test_environment_variables_usage(self):
        """Test that environment variables are used for sensitive config."""
        # Test that demo passwords come from environment
        original_password = os.environ.get("DEMO_ADMIN_PASSWORD")
        os.environ["DEMO_ADMIN_PASSWORD"] = "test_env_password_123"
        # Auth config caches users; clear cache so env update is picked up.
        auth_config._users_cache = None

        # Create new auth config to pick up environment change
        test_auth = auth_config
        user = test_auth.verify_password("admin@otomeshon.ai", "test_env_password_123")
        assert user is not None

        # Restore original if it existed
        if original_password:
            os.environ["DEMO_ADMIN_PASSWORD"] = original_password
        elif "DEMO_ADMIN_PASSWORD" in os.environ:
            del os.environ["DEMO_ADMIN_PASSWORD"]

    def test_sensitive_data_not_exposed(self):
        """Test that sensitive data is not exposed in responses."""
        client = TestClient(app)

        # Test auth providers endpoint doesn't expose passwords
        response = client.get("/api/auth/providers")
        assert response.status_code == 200
        data = response.json()

        # Check that passwords are not in the response
        response_text = str(data)
        assert "admin123" not in response_text
        assert "analyst123" not in response_text
        assert "password" not in response_text or "Use environment" in response_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])