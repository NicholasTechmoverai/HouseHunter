from fastapi import  HTTPException


from schemas.response.user import LoginResponse,Lv2_Profile,Lv1_Profile

from core.security import SecurityUtils,AuthDependencies

from core.logger import setup_logger
logger = setup_logger(__name__)

security_utils = SecurityUtils()
auth = AuthDependencies()


async def login_response(user, message="Login successful", success=True):
    """Create a standardized login response."""
    try:
        if not user:
            logger.error("NO user provided! !")
        
        subject = {
            "user_id": str(user.get("id")),
            "email": user.get("email"),
            "public_id": user.get("public_id")
        }
        token = security_utils.create_access_token(subject=subject)
        
        profile = Lv1_Profile(
            public_id=user.get("public_id"),
            username=user.get("username") or "",
            display_name=user.get("display_name"),
            profile_picture=user.get("profile_picture"),
            profile_picture_thumbnail=user.get("profile_picture_thumbnail"),
            email=user.get("email"),
            is_email_verified=user.get("is_email_verified"),
            status=user.get("status")
        )
        
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=profile,
            message=message,
            success=success
        )
    except Exception as e:
        logger.error(f"Error generating login response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating login response: {str(e)}"
        )
