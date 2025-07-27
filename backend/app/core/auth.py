from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer()


class User(BaseModel):
    """User model for authentication."""

    id: str
    email: str
    name: str
    preferred_username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    roles: list[str] = []
    groups: list[str] = []

    # SSO provider information
    identity_provider: Optional[str] = None  # "google", "microsoft", "keycloak"
    provider_id: Optional[str] = None

    # Bank-specific attributes
    employee_id: Optional[str] = None
    department: Optional[str] = None
    business_unit: Optional[str] = None
    clearance_level: Optional[str] = None


class KeycloakAuth:
    """Keycloak authentication service with SSO support."""

    def __init__(self) -> None:
        self.keycloak_url = settings.keycloak_url
        self.realm = "otomeshon"
        self.client_id = "otomeshon-client"
        self.client_secret = None  # Will be configured in Keycloak

        # Cache for Keycloak public key
        self._public_key_cache: Optional[str] = None
        self._public_key_expires: Optional[datetime] = None

    async def get_public_key(self) -> str:
        """Get Keycloak public key for JWT validation."""
        now = datetime.utcnow()

        # Use cached key if still valid
        if (
            self._public_key_cache
            and self._public_key_expires
            and now < self._public_key_expires
        ):
            return str(self._public_key_cache)

        # Fetch new public key
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.keycloak_url}/realms/{self.realm}/protocol/openid_connect/certs"
            )
            response.raise_for_status()

            certs = response.json()
            # Extract the public key (simplified - in production, handle multiple keys)
            if certs.get("keys"):
                key_data = certs["keys"][0]
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                self._public_key_cache = str(public_key)
                self._public_key_expires = now + timedelta(hours=1)
                return str(public_key)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to fetch Keycloak public key",
            )

    async def validate_token(self, token: str) -> User:
        """Validate JWT token and extract user information."""
        try:
            # Get public key for validation
            public_key = await self.get_public_key()

            # Decode and validate JWT
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=self.client_id,
                issuer=f"{self.keycloak_url}/realms/{self.realm}",
            )

            # Extract user information
            user_data = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "name": payload.get("name", ""),
                "preferred_username": payload.get("preferred_username"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "roles": payload.get("realm_access", {}).get("roles", []),
                "groups": payload.get("groups", []),
            }

            # Extract SSO provider information
            identity_provider = payload.get("identity_provider")
            if identity_provider:
                user_data["identity_provider"] = identity_provider
                user_data["provider_id"] = payload.get("provider_id")

            # Extract custom bank attributes
            user_data["employee_id"] = payload.get("employee_id")
            user_data["department"] = payload.get("department")
            user_data["business_unit"] = payload.get("business_unit")
            user_data["clearance_level"] = payload.get("clearance_level")

            return User(**user_data)

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    async def get_user_info(self, token: str) -> Dict[str, Any]:
        """Get detailed user information from Keycloak userinfo endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.keycloak_url}/realms/{self.realm}/protocol/openid_connect/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            result = response.json()
            return dict(result) if result else {}


# Global auth instance
keycloak_auth = KeycloakAuth()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    return await keycloak_auth.validate_token(token)


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to get current user with admin privileges."""
    if (
        "admin" not in current_user.roles
        and "otomeshon-admin" not in current_user.roles
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required"
        )
    return current_user


async def get_current_trader_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency to get current user with trader privileges."""
    trader_roles = ["trader", "senior-trader", "portfolio-manager", "admin"]
    if not any(role in current_user.roles for role in trader_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Trader privileges required"
        )
    return current_user


def require_clearance_level(min_level: str) -> Callable[[Any], Any]:
    """Decorator to require minimum clearance level."""
    clearance_hierarchy = {
        "PUBLIC": 0,
        "INTERNAL": 1,
        "CONFIDENTIAL": 2,
        "RESTRICTED": 3,
        "SECRET": 4,
    }

    def check_clearance(current_user: User = Depends(get_current_user)) -> User:
        user_level = clearance_hierarchy.get(
            current_user.clearance_level or "PUBLIC", 0
        )
        required_level = clearance_hierarchy.get(min_level, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Clearance level {min_level} required",
            )
        return current_user

    return check_clearance
