from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas import UserResponse
from app.services.auth_factory import AuthFactory

router = APIRouter(prefix="/auth", tags=["Unified Authentication"])
security = HTTPBearer()


# Pydantic models for request/response
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: int
    user: Dict[str, Any]
    auth_provider: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# UserResponse now imported from app.schemas


class AuthProvidersResponse(BaseModel):
    current: str


def get_client_info(request: Request) -> Dict[str, str]:
    """Extract client information from request"""
    return {

        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", ""),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user using simple auth"""

    auth_service = AuthFactory.create_auth_service(db)

    # Handle both sync and async auth services
    if hasattr(auth_service, "get_user_by_token"):
        if hasattr(auth_service.get_user_by_token, "__call__"):
            # Check if it's async
            import inspect

            if inspect.iscoroutinefunction(auth_service.get_user_by_token):
                user = await auth_service.get_user_by_token(credentials.credentials)
            else:
                user = auth_service.get_user_by_token(credentials.credentials)
        else:
            user = None
    else:
        user = None

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


@router.get("/providers", response_model=AuthProvidersResponse)
async def get_auth_providers():
    """Get authentication provider info"""

    return AuthProvidersResponse(current="simple")


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest, request: Request, db: Session = Depends(get_db)
):
    """Authenticate user using specified or default auth provider"""

    client_info = get_client_info(request)
    auth_service = AuthFactory.create_auth_service(db)

    try:
        # Handle both sync and async auth services
        if hasattr(auth_service, "authenticate_user"):
            if hasattr(auth_service.authenticate_user, "__call__"):
                import inspect

                if inspect.iscoroutinefunction(auth_service.authenticate_user):
                    result = await auth_service.authenticate_user(
                        email=login_data.email,
                        password=login_data.password,
                        ip_address=client_info["ip_address"],
                        user_agent=client_info["user_agent"],
                    )
                else:
                    result = auth_service.authenticate_user(
                        email=login_data.email,
                        password=login_data.password,
                        ip_address=client_info["ip_address"],
                        user_agent=client_info["user_agent"],
                    )
            else:
                result = None
        else:
            result = None

        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Add provider info to response
        result["auth_provider"] = "simple"
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication service error: {str(e)}",
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
):
    """Refresh access token using specified or default auth provider"""

    auth_service = AuthFactory.create_auth_service(db)

    # Handle both sync and async auth services
    if hasattr(auth_service, "refresh_access_token"):
        if hasattr(auth_service.refresh_access_token, "__call__"):
            import inspect

            if inspect.iscoroutinefunction(auth_service.refresh_access_token):
                result = await auth_service.refresh_access_token(
                    refresh_data.refresh_token
                )
            else:
                result = auth_service.refresh_access_token(refresh_data.refresh_token)
        else:
            result = None
    else:
        result = None

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return result


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Logout user using specified or default auth provider"""

    client_info = get_client_info(request)
    auth_service = AuthFactory.create_auth_service(db)

    # For simple auth, use session token; for Keycloak, would need refresh token
    session_token = "current_session"  # Simplified

    # Handle both sync and async auth services
    if hasattr(auth_service, "logout_user"):
        if hasattr(auth_service.logout_user, "__call__"):
            import inspect

            if inspect.iscoroutinefunction(auth_service.logout_user):
                success = await auth_service.logout_user(
                    session_token=session_token,
                    ip_address=client_info["ip_address"],
                    user_agent=client_info["user_agent"],
                )
            else:
                success = auth_service.logout_user(
                    session_token=session_token,
                    ip_address=client_info["ip_address"],
                    user_agent=client_info["user_agent"],
                )
        else:
            success = True
    else:
        success = True

    return {"message": "Successfully logged out", "provider": "simple"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""

    response_data = UserResponse.model_validate(current_user)
    response_data.auth_provider = getattr(
        current_user, "external_auth_provider", "simple"
    )

    return response_data


@router.get("/config")
async def get_auth_config():
    """Get authentication configuration and endpoints"""

    config = {
        "current_provider": "simple",
        "simple": {
            "enabled": True,
            "name": "Simple JWT Authentication",
            "description": "Basic username/password authentication with JWT tokens",
            "demo_accounts": [
                {
                    "email": "admin@otomeshon.com",
                    "password": "admin123",
                    "role": "Admin",
                },
                {
                    "email": "manager@otomeshon.com",
                    "password": "manager123",
                    "role": "Manager",
                },
                {"email": "user@otomeshon.com", "password": "user123", "role": "User"},
            ],
        },
        "endpoints": {
            "login": "/api/auth/login",
            "refresh": "/api/auth/refresh",
            "logout": "/api/auth/logout",
            "me": "/api/auth/me",
            "providers": "/api/auth/providers",
        },
    }


    return config
