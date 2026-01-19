from datetime import datetime, timezone, timedelta
from typing import Optional, Callable, Union, Dict, Any
import json

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from core.settings import settings
from models.user import User
from repositories.admin import AdminRepository, get_admin_repo
from .logger import setup_logger

logger = setup_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    sub: str  # Always a string after processing
    exp: int  # Unix timestamp
    iat: int  # Unix timestamp
    type: str = "access"
    scopes: list[str] = []


class AuthError(HTTPException):
    def __init__(self, detail: str = "Authentication failed", status_code: int = 401):
        super().__init__(status_code=status_code, detail=detail)


class UnauthorizedError(AuthError):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(detail=detail)


class TokenExpiredError(AuthError):
    def __init__(self):
        super().__init__(detail="Token has expired")


class UserNotFoundError(AuthError):
    def __init__(self):
        super().__init__(detail="User not found")


class UnverifiedUserError(AuthError):
    def __init__(self):
        super().__init__(detail="User not verified,Kindly verify your Email or phone number")


class SecurityUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        subject: str,  # MUST be a string, not a dict
        scopes: list[str] = None,
        expires_delta_minutes: Optional[int] = None
    ) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=expires_delta_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        payload = {
            "sub": subject,  # String, not dict!
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "scopes": scopes or []
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def create_refresh_token(subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        payload = {
            "sub": subject,  # String, not dict!
            "exp": expire,
            "iat": datetime.now(timezone.utc),  
            "type": "refresh"
        }
        
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def decode_token(token: str, verify_exp: bool = True) -> TokenData:
        """
        Decode a JWT token.
        
        Args:
            token: The JWT token to decode
            verify_exp: If True, raises TokenExpiredError for expired tokens.
                        If False, returns TokenData even for expired tokens.
        """
        try:
            # Decode WITHOUT validation first
            unverified_payload = jwt.get_unverified_claims(token)
            
            # Decode with configurable expiration check
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                options={
                    "verify_exp": verify_exp,  # <-- Configurable!
                    "verify_sub": False,
                    "verify_aud": False,
                    "verify_iss": False,
                    "verify_nbf": False,
                    "verify_iat": False,
                    "verify_jti": False
                }
            )
            
            sub = payload.get("sub")
            exp = payload.get("exp")
            iat = payload.get("iat")
            token_type = payload.get("type", "access")
            scopes = payload.get("scopes", [])
            
            # Handle the dict sub case
            if isinstance(sub, dict):
                user_id = sub.get("user_id")
                if not user_id:
                    raise UnauthorizedError("No user_id found in token subject")
                
                return TokenData(
                    sub=str(user_id),
                    exp=exp,
                    iat=iat,
                    type=token_type,
                    scopes=scopes
                )
            else:
                return TokenData(
                    sub=str(sub),
                    exp=exp,
                    iat=iat,
                    type=token_type,
                    scopes=scopes
                )
                
        except ExpiredSignatureError:
            if verify_exp:
                logger.warning("Token expired and expiration verification enabled")
                raise TokenExpiredError()
            else:
                # Decode again without expiration check
                logger.warning("Token expired but decoding anyway")
                return SecurityUtils.decode_token(token, verify_exp=False)
                
        except (JWTError, ValidationError) as e:
            logger.warning(f"Token validation failed: {e}")
            raise UnauthorizedError()


class AuthDependencies:
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> User:
        if not credentials:
            logger.warning("Missing authentication credentials")
            raise UnauthorizedError("Missing authentication credentials")

        try:

            token_data = SecurityUtils.decode_token(str(credentials.credentials))
            
            if token_data.type != "access":
                logger.warning(f"Invalid token type: {token_data.type}")
                raise UnauthorizedError("Invalid token type")

            user = await User.get_or_none(id=token_data.sub)
            if not user:
                logger.warning(f"User not found: {token_data.sub}")
                raise UserNotFoundError()

            if not user.is_authenticated:
                logger.warning(f"User not verified: {user.id}")
                raise UnverifiedUserError()

            logger.debug(f"User authenticated: {user.id}")
            return user

        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            raise UnauthorizedError()



    @staticmethod
    async def get_optional_current_user(
        credentials: HTTPAuthorizationCredentials = Security(security)
    ) -> User | None:
        if not credentials:
            logger.warning("Missing authentication credentials")
            return None

        try:

            token_data = SecurityUtils.decode_token(str(credentials.credentials))
            
            if token_data.type != "access":
                logger.warning(f"Invalid token type: {token_data.type}")
                return None

            user = await User.get_or_none(id=token_data.sub)
            if not user:
                return None
            
            return user
        
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            return None
        
    @staticmethod
    async def get_optional_current_user_no_expiry_check(
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> User | None:
        """
        Same as get_optional_current_user but doesn't check token expiry.
        Useful for refresh token endpoints.
        """
        if not credentials:
            return None

        try:
            token_data = SecurityUtils.decode_token(credentials.credentials, verify_exp=False)
            
            if token_data.type != "access":
                return None
            
            user = await User.get_or_none(id=token_data.sub)
            return user

        except (JWTError, ValidationError) as e:
            logger.debug(f"Invalid token: {e}")
            return None

        
            
            
    @staticmethod
    async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
        if not user.is_active:
            logger.warning(f"Inactive user attempted access: {user.id}")
            raise AuthError("Inactive user", status_code=status.HTTP_403_FORBIDDEN)
        return user

    @staticmethod
    async def get_current_superuser(user: User = Depends(get_current_active_user)) -> User:
        if not user.is_superuser:
            logger.warning(f"Non-superuser attempted superuser access: {user.id}")
            raise AuthError(
                "Insufficient permissions",
                status_code=status.HTTP_403_FORBIDDEN
            )
        logger.debug(f"Superuser authenticated: {user.id}")
        return user
    
    @staticmethod
    async def get_current_admin(user: User = Depends(get_current_active_user)) -> User:
        if not hasattr(user, 'admin_profile') or not user.admin_profile:
            logger.warning(f"Non-admin user attempted admin access: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        admin_profile = user.admin_profile
        if not admin_profile.is_active or admin_profile.is_suspended:
            logger.warning(f"Inactive/suspended admin attempted access: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account is not active"
            )
        
        logger.debug(f"Admin authenticated: {user.id}, level: {admin_profile.admin_level}")
        return user


class PermissionDependencies:
    @staticmethod
    def require_permission(module: str, action: str) -> Callable:
        async def _permission_checker(
            admin: User = Depends(AuthDependencies.get_current_admin),
            admin_repo: AdminRepository = Depends(get_admin_repo)
        ) -> User:
            admin_profile = admin.admin_profile
            
            if admin_profile.admin_level == 3:  # SUPER_ADMIN
                return admin
            
            has_perm = await admin_profile.has_permission(module, action)
            if not has_perm:
                logger.warning(
                    f"Permission denied for admin {admin.id}: {module}.{action}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {module}.{action}"
                )
            
            logger.debug(
                f"Permission granted for admin {admin.id}: {module}.{action}"
            )
            return admin
        
        return _permission_checker

    @staticmethod
    def require_admin_level(min_level: int) -> Callable:
        async def _level_checker(
            admin: User = Depends(AuthDependencies.get_current_admin)
        ) -> User:
            admin_profile = admin.admin_profile
            
            if admin_profile.admin_level < min_level:
                logger.warning(
                    f"Insufficient admin level for {admin.id}: "
                    f"required {min_level}, has {admin_profile.admin_level}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required admin level: {min_level}"
                )
            
            return admin
        
        return _level_checker

    @staticmethod
    def require_scope(required_scope: str) -> Callable:
        async def _scope_checker(
            user: User = Depends(AuthDependencies.get_current_user)
        ) -> User:
            user_scopes = getattr(user, "scopes", [])
            
            if required_scope not in user_scopes and "admin:*" not in user_scopes:
                logger.warning(
                    f"Scope missing for user {user.id}: required {required_scope}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required scope: {required_scope}"
                )
            
            return user
        
        return _scope_checker


def require_scope_dependency(scope: str) -> Callable:
    return PermissionDependencies.require_scope(scope)


def require_permission_dependency(module: str, action: str) -> Callable:
    return PermissionDependencies.require_permission(module, action)


def require_admin_level_dependency(level: int) -> Callable:
    return PermissionDependencies.require_admin_level(level)


# Export commonly used dependencies for easy import
get_current_user = AuthDependencies.get_current_user
get_optional_current_user = AuthDependencies.get_optional_current_user
get_optional_current_user_no_expiry_check = AuthDependencies.get_optional_current_user_no_expiry_check
get_current_active_user = AuthDependencies.get_current_active_user
get_current_superuser = AuthDependencies.get_current_superuser
get_current_admin = AuthDependencies.get_current_admin
require_permission = PermissionDependencies.require_permission
require_scope = PermissionDependencies.require_scope
require_admin_level = PermissionDependencies.require_admin_level




"""
from core.security import (
    get_current_user,
    get_current_admin,
    require_permission,
    require_admin_level,
    require_scope
)

# Basic user auth
@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)):
    pass

# Admin auth
@router.get("/admin/dashboard")
async def admin_dashboard(admin: User = Depends(get_current_admin)):
    pass

# Permission-based auth
@router.get("/admin/users")
async def manage_users(
    admin: User = Depends(require_permission("user_management", "view"))
):
    pass

# Admin level-based auth
@router.get("/admin/settings")
async def system_settings(
    admin: User = Depends(require_admin_level(2))  # Requires ADMIN level or higher
):
    pass

# Scope-based auth
@router.get("/premium")
async def premium_content(user: User = Depends(require_scope("premium"))):
    pass"""