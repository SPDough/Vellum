from sqlalchemy.orm import Session

from app.services.auth_service import AuthService

class AuthFactory:
    """Factory class to create authentication service instances"""
    
    @staticmethod
    def create_auth_service(db: Session) -> AuthService:
        """Create authentication service (simple auth only)"""
        return AuthService(db)