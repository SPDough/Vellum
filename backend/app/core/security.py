"""
Security utilities and hardening for Otomeshon Banking Platform
"""

import hashlib
import ipaddress
import json
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext

logger = structlog.get_logger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security constants
MIN_PASSWORD_LENGTH = 12
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30
SESSION_TIMEOUT_MINUTES = 480  # 8 hours


class SecurityValidator:
    """Security validation utilities for banking compliance"""

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validate password meets banking security requirements

        Returns:
            Dict with 'valid' bool and 'issues' list
        """
        issues = []

        # Length check
        if len(password) < MIN_PASSWORD_LENGTH:
            issues.append(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )

        # Character requirements
        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            issues.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            issues.append("Password must contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")

        # Common password patterns
        common_patterns = [
            r"password",
            r"123456",
            r"qwerty",
            r"admin",
            r"otomeshon",
            r"banking",
        ]

        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                issues.append(f"Password cannot contain common pattern: {pattern}")

        # Sequence checks
        if re.search(r"(.)\1{2,}", password):  # 3+ repeated characters
            issues.append("Password cannot contain 3 or more repeated characters")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "strength_score": max(0, 100 - len(issues) * 15),
        }

    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validate email format with banking domain restrictions"""
        email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

        if not email_pattern.match(email):
            return False

        # Additional banking-specific validations
        domain = email.split("@")[1].lower()

        # Block known public email domains for internal users
        blocked_domains = [
            "gmail.com",
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "tempmail.org",
            "10minutemail.com",
        ]

        if domain in blocked_domains:
            logger.warning("Public email domain used", email=email, domain=domain)
            return False

        return True

    @staticmethod
    def validate_ip_address(
        ip: str, allowed_ranges: Optional[List[str]] = None
    ) -> bool:
        """Validate IP address against allowed ranges"""
        try:
            ip_obj = ipaddress.ip_address(ip)

            # Default allowed ranges for banking (internal networks)
            if allowed_ranges is None:
                allowed_ranges = [
                    "10.0.0.0/8",  # Private Class A
                    "172.16.0.0/12",  # Private Class B
                    "192.168.0.0/16",  # Private Class C
                    "127.0.0.0/8",  # Loopback
                ]

            for range_str in allowed_ranges:
                if ip_obj in ipaddress.ip_network(range_str):
                    return True

            logger.warning("IP address outside allowed ranges", ip=ip)
            return False

        except ValueError:
            logger.error("Invalid IP address format", ip=ip)
            return False


class DataMasking:
    """Data masking utilities for sensitive information"""

    @staticmethod
    def mask_account_number(account: str) -> str:
        """Mask account number, showing only last 4 digits"""
        if len(account) <= 4:
            return "*" * len(account)
        return "*" * (len(account) - 4) + account[-4:]

    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN, showing only last 4 digits"""
        cleaned = re.sub(r"[^\d]", "", ssn)
        if len(cleaned) != 9:
            return "*" * len(ssn)
        return f"***-**-{cleaned[-4:]}"

    @staticmethod
    def mask_credit_card(card: str) -> str:
        """Mask credit card number, showing only last 4 digits"""
        cleaned = re.sub(r"[^\d]", "", card)
        if len(cleaned) < 13:
            return "*" * len(card)

        # Reconstruct with original formatting
        masked = "*" * (len(cleaned) - 4) + cleaned[-4:]

        # Apply original formatting
        result = ""
        mask_idx = 0
        for char in card:
            if char.isdigit():
                result += masked[mask_idx]
                mask_idx += 1
            else:
                result += char

        return result

    @staticmethod
    def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in a data dictionary"""
        sensitive_fields = {
            "account_number": DataMasking.mask_account_number,
            "ssn": DataMasking.mask_ssn,
            "social_security_number": DataMasking.mask_ssn,
            "credit_card": DataMasking.mask_credit_card,
            "card_number": DataMasking.mask_credit_card,
            "password": lambda x: "*" * len(x),
            "api_key": lambda x: (
                x[:8] + "*" * (len(x) - 8) if len(x) > 8 else "*" * len(x)
            ),
        }

        masked_data = {}
        for key, value in data.items():
            if isinstance(value, str) and key.lower() in sensitive_fields:
                masked_data[key] = sensitive_fields[key.lower()](value)
            elif isinstance(value, dict):
                masked_data[key] = DataMasking.mask_sensitive_data(value)
            else:
                masked_data[key] = value

        return masked_data


class AuditLogger:
    """Secure audit logging for banking compliance"""

    def __init__(self):
        self.logger = structlog.get_logger("audit")

    def log_authentication_event(
        self,
        user_id: str,
        event_type: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        additional_data: Optional[Dict] = None,
    ):
        """Log authentication events"""
        self.logger.info(
            "Authentication event",
            user_id=user_id,
            event_type=event_type,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow().isoformat(),
            additional_data=additional_data or {},
        )

    def log_transaction_event(
        self,
        user_id: str,
        transaction_id: str,
        transaction_type: str,
        amount: float,
        currency: str,
        status: str,
        additional_data: Optional[Dict] = None,
    ):
        """Log transaction events"""
        masked_data = DataMasking.mask_sensitive_data(additional_data or {})

        self.logger.info(
            "Transaction event",
            user_id=user_id,
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            additional_data=masked_data,
        )

    def log_access_event(
        self,
        user_id: str,
        resource: str,
        action: str,
        success: bool,
        ip_address: str,
        additional_data: Optional[Dict] = None,
    ):
        """Log resource access events"""
        self.logger.info(
            "Access event",
            user_id=user_id,
            resource=resource,
            action=action,
            success=success,
            ip_address=ip_address,
            timestamp=datetime.utcnow().isoformat(),
            additional_data=additional_data or {},
        )


class SessionManager:
    """Secure session management"""

    def __init__(self, redis_client=None):
        self.redis = redis_client
        self.sessions = {}  # In-memory fallback if Redis unavailable

    async def create_session(
        self, user_id: str, ip_address: str, user_agent: str
    ) -> str:
        """Create a new secure session"""
        session_id = secrets.token_urlsafe(32)

        session_data = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "last_activity": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow() + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
            ).isoformat(),
        }

        if self.redis:
            try:
                await self.redis.setex(
                    f"session:{session_id}",
                    SESSION_TIMEOUT_MINUTES * 60,
                    json.dumps(session_data),
                )
            except Exception as e:
                logger.error("Failed to store session in Redis", error=str(e))
                self.sessions[session_id] = session_data
        else:
            self.sessions[session_id] = session_data

        return session_id

    async def validate_session(
        self, session_id: str, ip_address: str
    ) -> Optional[Dict[str, Any]]:
        """Validate session and check for security violations"""
        session_data = None

        if self.redis:
            try:
                data = await self.redis.get(f"session:{session_id}")
                if data:
                    session_data = json.loads(data)
            except Exception as e:
                logger.error("Failed to retrieve session from Redis", error=str(e))

        if not session_data and session_id in self.sessions:
            session_data = self.sessions[session_id]

        if not session_data:
            return None

        # Check expiration
        expires_at = datetime.fromisoformat(session_data["expires_at"])
        if datetime.utcnow() > expires_at:
            await self.invalidate_session(session_id)
            return None

        # Check IP address consistency (basic session hijacking protection)
        if session_data["ip_address"] != ip_address:
            logger.warning(
                "Session IP address mismatch",
                session_id=session_id,
                original_ip=session_data["ip_address"],
                current_ip=ip_address,
            )
            # In strict mode, we could invalidate the session here
            # For now, just log the warning

        # Update last activity
        session_data["last_activity"] = datetime.utcnow().isoformat()

        if self.redis:
            try:
                await self.redis.setex(
                    f"session:{session_id}",
                    SESSION_TIMEOUT_MINUTES * 60,
                    json.dumps(session_data),
                )
            except Exception:
                pass

        return session_data

    async def invalidate_session(self, session_id: str):
        """Invalidate a session"""
        if self.redis:
            try:
                await self.redis.delete(f"session:{session_id}")
            except Exception:
                pass

        if session_id in self.sessions:
            del self.sessions[session_id]


class SecurityHeaders:
    """Security headers for banking compliance"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers for banking applications"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bool(pwd_context.verify(plain_password, hashed_password))


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    return secrets.token_urlsafe(length)


def create_audit_hash(data: Dict[str, Any]) -> str:
    """Create a hash for audit trail integrity"""
    # Sort keys for consistent hashing
    sorted_data = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(sorted_data.encode()).hexdigest()


# Global instances
audit_logger = AuditLogger()
security_validator = SecurityValidator()
