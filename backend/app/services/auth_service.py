from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import ipaddress

from app.models.user import User, UserSession, UserAuditLog, UserRole, UserStatus
from app.core.config import get_settings

settings = get_settings()

class AuthService:
    """Authentication and authorization service for banking platform"""

    def __init__(self, db: Session):
        self.db = db
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow()
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "iat": datetime.utcnow()
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Verify token type
            if payload.get("type") != token_type:
                return None

            # Check if token is expired
            if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
                return None

            return payload
        except jwt.PyJWTError:
            return None

    def authenticate_user(self, email: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""

        # Get user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            self._log_audit(None, "login_attempt", f"Failed login for {email}", "failure", ip_address, user_agent)
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            self._log_audit(user.id, "login_attempt", "Account locked", "failure", ip_address, user_agent)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked until {user.locked_until}"
            )

        # Check account status
        if user.status != UserStatus.ACTIVE:
            self._log_audit(user.id, "login_attempt", f"Account status: {user.status}", "failure", ip_address, user_agent)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}"
            )

        # Verify password
        if not self.verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1

            # Lock account if too many failures
            if user.failed_login_attempts >= self.max_failed_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
                self._log_audit(user.id, "account_locked", f"Too many failed attempts", "success", ip_address, user_agent)

            self.db.commit()
            self._log_audit(user.id, "login_attempt", "Invalid password", "failure", ip_address, user_agent)
            return None

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()

        # Create tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": str(user.id)})

        # Create session
        session = UserSession(
            user_id=user.id,
            session_token=secrets.token_urlsafe(32),
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        )

        self.db.add(session)
        self.db.commit()

        self._log_audit(user.id, "login", "Successful login", "success", ip_address, user_agent, session.session_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "department": user.department,
                "must_change_password": user.must_change_password
            }
        }

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""

        # Verify refresh token
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        # Check if session exists and is active
        session = self.db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.utcnow()
        ).first()

        if not session:
            return None

        # Get user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or user.status != UserStatus.ACTIVE:
            return None

        # Create new access token
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "full_name": user.full_name
        }

        access_token = self.create_access_token(token_data)

        # Update session activity
        session.last_activity = datetime.utcnow()
        self.db.commit()

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.access_token_expire_minutes * 60
        }

    def logout_user(self, session_token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Logout user and invalidate session"""

        session = self.db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.is_active == True
        ).first()

        if not session:
            return False

        # Deactivate session
        session.is_active = False
        session.logged_out_at = datetime.utcnow()
        self.db.commit()

        self._log_audit(session.user_id, "logout", "User logged out", "success", ip_address, user_agent, session_token)
        return True

    def create_user(self, email: str, password: str, full_name: str, role: UserRole = UserRole.VIEWER, **kwargs) -> User:
        """Create new user account"""

        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Generate username from email if not provided
        username = kwargs.get('username') or email.split('@')[0]

        # Ensure username is unique
        counter = 1
        original_username = username
        while self.db.query(User).filter(User.username == username).first():
            username = f"{original_username}{counter}"
            counter += 1

        # Create user
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=self.hash_password(password),
            role=role,
            status=UserStatus.PENDING,
            **kwargs
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._log_audit(user.id, "user_created", f"User account created", "success")
        return user

    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Verify current password
        if not self.verify_password(current_password, user.hashed_password):
            self._log_audit(user_id, "password_change", "Invalid current password", "failure")
            return False

        # Update password
        user.hashed_password = self.hash_password(new_password)
        user.password_changed_at = datetime.utcnow()
        user.must_change_password = False

        # Invalidate all existing sessions
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({"is_active": False, "logged_out_at": datetime.utcnow()})

        self.db.commit()

        self._log_audit(user_id, "password_changed", "Password changed successfully", "success")
        return True

    def has_permission(self, user: User, resource: str, action: str) -> bool:
        """Check if user has permission for resource and action"""

        # Admin has all permissions
        if user.role == UserRole.ADMIN:
            return True

        # Define role-based permissions
        permissions = {
            UserRole.MANAGER: {
                "data_sandbox": ["read", "write", "export"],
                "workflows": ["read", "write"],
                "analytics": ["read", "write"],
                "users": ["read"],
                "reports": ["read", "write"]
            },
            UserRole.ANALYST: {
                "data_sandbox": ["read", "write", "export"],
                "workflows": ["read"],
                "analytics": ["read", "write"],
                "reports": ["read", "write"]
            },
            UserRole.TRADER: {
                "data_sandbox": ["read", "export"],
                "workflows": ["read"],
                "trading": ["read", "write"],
                "reports": ["read"]
            },
            UserRole.COMPLIANCE: {
                "data_sandbox": ["read", "export"],
                "workflows": ["read"],
                "analytics": ["read"],
                "audit": ["read", "write"],
                "reports": ["read", "write"]
            },
            UserRole.VIEWER: {
                "data_sandbox": ["read"],
                "workflows": ["read"],
                "analytics": ["read"],
                "reports": ["read"]
            }
        }

        user_permissions = permissions.get(user.role, {})
        resource_permissions = user_permissions.get(resource, [])

        return action in resource_permissions


    def _log_audit(self, user_id: Optional[int], action: str, details: str, result: str, 
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None, session_id: Optional[str] = None):
        """Log user action for audit trail"""

        audit_log = UserAuditLog(
            user_id=user_id,
            action=action,
            details=details,
            result=result,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id
        )

        self.db.add(audit_log)
        # Note: Don't commit here as it might be part of a larger transaction

    def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user from access token"""

        payload = self.verify_token(token, "access")
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = self.db.query(User).filter(User.id == user_id).first()
        return user if user and user.status == UserStatus.ACTIVE else None
