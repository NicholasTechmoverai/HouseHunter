from datetime import datetime, timezone
from typing import Dict, Any
import random
from pydantic import BaseModel, Field, validator

from fastapi import HTTPException

from schemas.response.user import LoginResponse, Lv1_Profile
from core.security import SecurityUtils
from core.logger import setup_logger

logger = setup_logger(__name__)

security_utils = SecurityUtils()

def secure_log_email(email: str) -> str:
    """Secure email for logging purposes."""
    if not email or "@" not in email:
        return "invalid_email"
    
    try:
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            return f"{local[0]}***@{domain}"
        return f"{local[:2]}***{local[-2:]}@{domain}"
    except:
        return "email_masked"


class TokenSubject(BaseModel):
    """Pydantic model for JWT token subject."""
    user_id: str = Field(..., description="User ID")
    email: str = Field("", description="User email")
    public_id: str = Field("", description="Public identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v or not v.strip():
            raise ValueError("User ID cannot be empty")
        return str(v)


async def login_response(
    user: Dict[str, Any], 
    message: str = "Login successful", 
    success: bool = True
) -> LoginResponse:
    """
    Create a standardized login response with JWT token.
    
    Args:
        user: User data dictionary
        message: Optional success message
        success: Operation success flag
        
    Returns:
        LoginResponse with access token and user profile
    """
    # Validate required fields
    required_fields = ['id', 'email', 'public_id']
    missing_fields = [field for field in required_fields if not user.get(field)]
    
    if missing_fields:
        logger.error(f"Missing required fields: {missing_fields}")
        raise HTTPException(
            status_code=400,
            detail=f"Missing required user fields: {', '.join(missing_fields)}"
        )
    
    try:
        # Create token subject with validation
        subject_data = TokenSubject(
            user_id=str(user["id"]),
            email=user["email"],
            public_id=user["public_id"]
        )
        
        # Generate access token
        token = security_utils.create_access_token(subject=subject_data.dict())
        
        # Generate secure random codes
        special_codes = [f"{random.randint(1000, 9999):04d}" for _ in range(4)]
        
        # Create user profile with safe defaults
        profile_data = {
            "public_id": user["public_id"],
            "username": user.get("username", ""),
            "display_name": user.get("display_name", user.get("username", "")),
            "profile_picture": user.get("profile_picture"),
            "profile_picture_thumbnail": user.get("profile_picture_thumbnail"),
            "email":secure_log_email( user["email"]),
            "is_email_verified": user.get("is_email_verified", False),
            "status": user.get("status", "active"),
            "special_code": special_codes,
            # "time": datetime.now(timezone.utc).isoformat()
        }
        
        profile = Lv1_Profile(**profile_data)
        
        # Return standardized response
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=profile,
            message=message,
            success=success
        )
        
    except ValueError as e:
        logger.warning(f"Data validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in login_response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during login"
        )