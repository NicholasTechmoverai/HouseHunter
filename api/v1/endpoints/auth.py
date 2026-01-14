from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from core.limiter import limiter
from schemas.request.user import Login as LoginRequest,UserCreate as UserCreateRequest
from schemas.request.auth import VerificationCodeRequest
from schemas.response.user import LoginResponse,Lv2_Profile,Lv1_Profile
from repositories.user import get_user_repo
from repositories.auth import get_verification_repo
from services.login.index import login_response
from core.security import SecurityUtils,AuthDependencies
from core.settings import settings
from services.login.google_login_services import login_google,auth_callback,GoogleCredentialPayload,handleOneTapLogin

from core.logger import setup_logger
logger = setup_logger(__name__)

security_utils = SecurityUtils()
auth = AuthDependencies()

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/onetap-google-login")
async def google_login(payload: GoogleCredentialPayload):
    try:
        if not payload:
            return {"success": False, "error": "No payload provided"}
        
        res = await handleOneTapLogin(payload)
        if not res.get("success"):
            return {"success": False, "error": "Login failed"}
        
        return {"success": True, "data": res.get("data")}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google login failed: {str(e)}")


@auth_router.get("/google_login")
@limiter.limit("10/minute")
async def google_login_start(request: Request):
    """Starts the Google OAuth login flow."""
    try:
        return login_google() 
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@auth_router.get("/google/callback")
@limiter.limit("10/minute")
async def google_login_callback(request: Request, code: str, state: str = None):
    """Handles the redirect after Google auth."""
    try:
        return await auth_callback(request, code, state)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    
    
# @auth_router.post("/refresh")
# @limiter.limit("5/minute")
# async def new_token(request: Request, data: RefreshRequest, auth: AuthService = Depends()):
#     try:
#         return await auth.renew_token(data.user_id)
#     except Exception as e:
#         raise HTTPException(status_code=401, detail=str(e))

# @auth_router.post("/login", response_model=LoginResponse)
# @limiter.limit("10/minute")
# async def exchange_token(request: Request, token: LoginRequest):
#     """Authenticate user and return login response."""
#     try:
#         # response = await 
#         # if not response["success"]:
#         #     raise HTTPException(
#         #         status_code=401, 
#         #         detail=response["message"]
#         #     )
                    
#         # return await login_response(response["user"])
   
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Login error: {str(e)}", exc_info=True)   
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Login error: {str(e)}"
#         )



@auth_router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
async def user_login(request: Request, data: LoginRequest):
    """Authenticate user and return login response."""
    try:
        response = await get_user_repo().authenticate(
            email=data.email, 
            password=data.password
        )
        
        if not response["success"]:
            raise HTTPException(
                status_code=401, 
                detail=response["message"]
            )
                    
        return await login_response(response["user"])
   
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)   
        raise HTTPException(
            status_code=500, 
            detail=f"Login error: {str(e)}"
        )


@auth_router.post("/user/register", response_model=LoginResponse)
@limiter.limit("10/minute")
async def user_register(request: Request, data: UserCreateRequest):
    """Register new user and return authentication response."""
    try:
        # Validate email existence
        if await get_user_repo().get_by_email(email=data.email):
            raise HTTPException(
                status_code=400, 
                detail="Email already registered"
            )
        
        if data.password != data.confirm_password:
            raise HTTPException(
                status_code=400, 
                detail="Passwords do not match"
            )
        
        user = await get_user_repo().register(
            email=data.email,
            first_name=data.first_name,
            password=data.password,
            **data.model_dump(exclude={"password", "confirm_password", "email", "first_name"})
        )
        
        if isinstance(user, dict) and "success" in user and not user["success"]:
            raise HTTPException(
                status_code=400, 
                detail=user.get("message", "Registration failed")
            )
        
        return await login_response(user, message="Registration successful")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Registration error: {str(e)}"
        )
        
        
        
        
@auth_router.post("/verification/send-code")
@limiter.limit("25/minute")
async def send_code(request: Request, data: VerificationCodeRequest):
    try:
        if data.type == "email":
            user_id = (await get_user_repo().get_by_email(data.identifier)).id
        elif data.type == "phone":
            user_id = (await get_user_repo().get_by_phone(data.identifier)).id
        else:
            raise HTTPException(status_code=400, detail="Invalid verification type")
        
        code =  await get_verification_repo().create_verification_code(
            user_id= user_id,
            code_type=data.type,
            identifier=request.client.host if request.client else None
        )
        return {"message": "Verification code sent", "code": code.code}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))




@auth_router.post("/verification/verify-code")
@limiter.limit("25/minute")
async def verify_code(request: Request, data: VerificationCodeRequest):
    try:
        logger.info(f"Received verification code request: {data}")

        if not data.code:
            raise HTTPException(status_code=400, detail="Verification code is required")
        
        
        if data.type == "email":
            user_id = (await get_user_repo().get_by_email(data.identifier)).id
        elif data.type == "phone":
            user_id = (await get_user_repo().get_by_phone(data.identifier)).id
        else:
            raise HTTPException(status_code=400, detail="Invalid verification type")
        
        res =  await get_verification_repo().verify_code(
            user_id=user_id,
            code=data.code,
            code_type=data.type
        )
        logger.info(f"Verification result: {res}")
        if not res["success"]:
            return {"message": res["message"], "success": False}
        
        return {"message": "Verification successful", "success": True}

    except Exception as e:
        logger.error(f"Verification error: {str(e)}", exc_info=True)
        # raise HTTPException(status_code=401, detail=str(e))        