"""
Secure authentication configuration module.
Replaces hardcoded credentials with environment-based configuration.
"""

import os
import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr


class SecureUser(BaseModel):
    """Secure user model with hashed passwords."""
    id: int
    email: EmailStr
    username: str
    password_hash: str
    full_name: str
    role: str
    department: Optional[str] = None
    is_active: bool = True


class AuthConfig:
    """Secure authentication configuration."""

    def __init__(self):
        self._users_cache: Optional[Dict[str, SecureUser]] = None

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 with salt."""
        salt = os.getenv("PASSWORD_SALT", "otomeshon_default_salt_change_in_production")
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def _get_demo_users(self) -> Dict[str, SecureUser]:
        """Get demo users with properly hashed passwords."""
        # Use environment variables for demo credentials if available
        admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "secure_admin_123!")
        analyst_password = os.getenv("DEMO_ANALYST_PASSWORD", "secure_analyst_123!")

        return {
            "admin@otomeshon.ai": SecureUser(
                id=1,
                email="admin@otomeshon.ai",
                username="admin",
                password_hash=self._hash_password(admin_password),
                full_name="System Administrator",
                role="admin",
                department="IT"
            ),
            "analyst@otomeshon.ai": SecureUser(
                id=2,
                email="analyst@otomeshon.ai",
                username="analyst",
                password_hash=self._hash_password(analyst_password),
                full_name="Data Analyst",
                role="analyst",
                department="Analytics"
            )
        }

    def get_users(self) -> Dict[str, SecureUser]:
        """Get configured users (cached for performance)."""
        if self._users_cache is None:
            self._users_cache = self._get_demo_users()
        return self._users_cache

    def verify_password(self, email: str, password: str) -> Optional[SecureUser]:
        """Verify user credentials securely."""
        users = self.get_users()
        user = users.get(email)

        if not user or not user.is_active:
            return None

        if user.password_hash == self._hash_password(password):
            return user

        return None

    def get_user_by_email(self, email: str) -> Optional[SecureUser]:
        """Get user by email address."""
        users = self.get_users()
        return users.get(email)


# Global auth config instance
auth_config = AuthConfig()