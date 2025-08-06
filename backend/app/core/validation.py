"""
Input validation and sanitization module for banking operations.
Provides security-focused validation for financial data.
"""

import re
import html
from typing import Any, Dict, Optional, Union
from decimal import Decimal, InvalidOperation
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error for banking operations."""
    pass


class InputValidator:
    """Secure input validator for banking operations."""

    # Banking-specific patterns
    CURRENCY_PATTERN = re.compile(r'^[A-Z]{3}$')  # ISO 4217 currency codes
    CUSTOMER_ID_PATTERN = re.compile(r'^CUST_[0-9]{4,10}$')
    TRANSACTION_ID_PATTERN = re.compile(r'^[A-Za-z0-9\-_]{8,64}$')

    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\\')|(;)|(--)|(\s*(union|select|insert|update|delete|drop|create|alter)\s+))",
        r"(\b(exec|execute|sp_|xp_)\b)",
        r"(\b(script|javascript|vbscript|onload|onerror|onclick)\b)"
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input to prevent XSS and injection attacks."""
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        # Check for SQL injection patterns
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value.lower()):
                logger.warning(f"Potential injection attempt detected: {value[:50]}...")
                raise ValidationError("Invalid characters detected in input")

        # HTML escape and limit length
        sanitized = html.escape(value.strip())
        if len(sanitized) > max_length:
            raise ValidationError(f"Input too long. Maximum {max_length} characters allowed")

        return sanitized

    @staticmethod
    def validate_amount(amount: Union[str, float, Decimal]) -> Decimal:
        """Validate and normalize monetary amounts."""
        try:
            decimal_amount = Decimal(str(amount))

            # Banking validation rules
            if decimal_amount < 0:
                raise ValidationError("Amount cannot be negative")

            if decimal_amount > Decimal('999999999999.99'):  # 1 trillion limit
                raise ValidationError("Amount exceeds maximum allowed value")

            # Check for reasonable decimal places (2 for most currencies)
            exponent = decimal_amount.as_tuple().exponent
            if isinstance(exponent, int) and exponent < -2:
                raise ValidationError("Amount has too many decimal places")

            return decimal_amount.quantize(Decimal('0.01'))

        except (InvalidOperation, ValueError):
            raise ValidationError("Invalid amount format")

    @staticmethod
    def validate_currency(currency: str) -> str:
        """Validate ISO 4217 currency codes."""
        currency = InputValidator.sanitize_string(currency, 3).upper()

        if not InputValidator.CURRENCY_PATTERN.match(currency):
            raise ValidationError("Invalid currency code format")

        # Common currency whitelist for banking
        allowed_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'SGD', 'HKD'}
        if currency not in allowed_currencies:
            logger.warning(f"Uncommon currency code used: {currency}")

        return currency

    @staticmethod
    def validate_customer_id(customer_id: str) -> str:
        """Validate customer ID format."""
        customer_id = InputValidator.sanitize_string(customer_id, 20)

        if not InputValidator.CUSTOMER_ID_PATTERN.match(customer_id):
            raise ValidationError("Invalid customer ID format")

        return customer_id

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address with banking domain restrictions."""
        email = InputValidator.sanitize_string(email, 100).lower()

        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValidationError("Invalid email format")

        # Block suspicious domains
        suspicious_domains = ['temp-mail.org', '10minutemail.com', 'guerrillamail.com']
        domain = email.split('@')[1]
        if domain in suspicious_domains:
            raise ValidationError("Email domain not allowed")

        return email

    @staticmethod
    def validate_filter_request(filters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize filter request parameters."""
        if not isinstance(filters, dict):
            raise ValidationError("Filters must be a dictionary")

        validated_filters = {}

        for key, value in filters.items():
            # Sanitize filter keys
            clean_key = InputValidator.sanitize_string(key, 50)

            # Validate specific filter types
            if clean_key == "source":
                allowed_sources = ["workflow", "api", "mcp", "manual"]
                if value not in allowed_sources:
                    raise ValidationError(f"Invalid source. Must be one of: {allowed_sources}")
                validated_filters[clean_key] = value

            elif clean_key in ["date_from", "date_to"]:
                try:
                    # Validate date format
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                    validated_filters[clean_key] = value
                except ValueError:
                    raise ValidationError(f"Invalid date format for {clean_key}")

            elif clean_key == "amount_min" or clean_key == "amount_max":
                validated_filters[clean_key] = InputValidator.validate_amount(value)

            elif clean_key == "currency":
                validated_filters[clean_key] = InputValidator.validate_currency(value)

            elif clean_key == "customer_id":
                validated_filters[clean_key] = InputValidator.validate_customer_id(value)

            else:
                # Generic string validation for other filters
                if isinstance(value, str):
                    validated_filters[clean_key] = InputValidator.sanitize_string(value, 100)
                elif isinstance(value, (int, float, bool)):
                    validated_filters[clean_key] = value
                else:
                    logger.warning(f"Unexpected filter value type for {clean_key}: {type(value)}")

        return validated_filters

    @staticmethod
    def validate_pagination(page: int, page_size: int) -> tuple[int, int]:
        """Validate pagination parameters."""
        if not isinstance(page, int) or page < 1:
            raise ValidationError("Page must be a positive integer")

        if not isinstance(page_size, int) or page_size < 1:
            raise ValidationError("Page size must be a positive integer")

        # Prevent excessive page sizes that could impact performance
        if page_size > 1000:
            raise ValidationError("Page size too large. Maximum 1000 records per page")

        # Prevent excessive page numbers that could indicate pagination abuse
        if page > 10000:
            raise ValidationError("Page number too large")

        return page, page_size