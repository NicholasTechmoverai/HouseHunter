from fastapi import  Request,HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import os
from urllib.parse import urlencode
import httpx
from core.logger import setup_logger
from core.settings import settings
from models.user.base_user import UserStatus
from services.login.index import login_response
from repositories.user import get_user_repo
from core.security import SecurityUtils,AuthDependencies
import json
from datetime import datetime
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import base64

class GoogleCredentialPayload(BaseModel):
    token: str  # The JWT sent from frontend

logger = setup_logger(__name__)




class GoogleOAuth:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

        # Base endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"

    def get_authorization_url(self, state: str = "login"):
        """Generate the Google OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code(self, code: str):
        """Exchange authorization code for tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.token_url, data={
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "grant_type": "authorization_code",
            })
            resp.raise_for_status()
            return resp.json()

    async def get_user_info(self, access_token: str):
        """Fetch user profile info using access token."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(self.userinfo_url, headers={
                "Authorization": f"Bearer {access_token}"
            })
            resp.raise_for_status()
            return resp.json()


google_auth = GoogleOAuth(settings.GOOGLE_CLIENT_ID, settings.GOOGLE_CLIENT_SECRET, settings.GOOGLE_REDIRECT_URI)


def login_google():
    """Redirect to Google login."""
    auth_url = google_auth.get_authorization_url()
    return RedirectResponse(auth_url)

async def create_or_login_user(user_info: dict, provider: str = "google") -> dict:
    """Unified function to create new user or login existing user."""
    user_repo = get_user_repo()
    
    email = user_info.get("email")
    if not email:
        raise ValueError("No email provided")
    
    user = await user_repo.get_by_email(email)
    
    if user:
        user_data = await login_response(await user_repo.to_dict(user))
    else:
        # Create new user based on provider
        user_payload = {
            "email": email,
            "first_name": user_info.get("given_name", ""),
            "status": 1,
            "activated_status_at": datetime.now(),
            "last_name": user_info.get("family_name", ""),
            "display_name": user_info.get("name", ""),
            "profile_picture": user_info.get("picture", ""),
            "profile_picture_thumbnail": user_info.get("picture", ""),
            "email_verified": user_info.get("email_verified", False),
            "oauth_providers": [
                {"provider": provider, f"{provider}_id": user_info.get("sub")}
            ]
        }
        
        user = await user_repo.register(
            user_payload["email"],
            user_payload["first_name"],
            **{k: v for k, v in user_payload.items() if k not in {"email", "first_name"}}
        )
        
        if isinstance(user, dict) and "success" in user and not user["success"]:
            raise HTTPException(
                status_code=400,
                detail=user.get("message", "Registration failed. Kindly try again in a few!")
            )
        
        user_data = await login_response(user.get('user'))
    
    if hasattr(user_data, "model_dump"):
        user_data = user_data.model_dump()
    
    return user_data


async def auth_callback(request: Request, code: str, state: str = None):
    """Handle Google OAuth callback, register/login user, and send info back to the popup."""
    
    try:
        tokens = await google_auth.exchange_code(code)
        
        user_info = await google_auth.get_user_info(tokens["access_token"])
        
        user_data = await create_or_login_user(user_info, provider="google")
        user_data.pop("time", None)

        
        encoded = base64.urlsafe_b64encode(json.dumps(user_data).encode()).decode()
        params = urlencode({"success": "1", "data": encoded})
        
        return RedirectResponse(url=f"{settings.SITE.SITE_URL}/auth/callback?{params}")
    
    except Exception as e:
        # Error handling
        error_html = f"""
        <html>
        <body style="font-family: sans-serif; text-align: center; padding: 40px;">
            <h3 style="color: #d32f2f;">Authentication Failed</h3>
            <p>{str(e)}</p>
            <button onclick="window.close()" 
                    style="background: #4285F4; color: white; border: none; 
                           padding: 10px 20px; border-radius: 4px; cursor: pointer;">
                Close Window
            </button>
            
            <script>
                window.opener.postMessage({{
                    type: "google-login-error",
                    error: "Authentication failed: {str(e)}"
                }}, "{settings.SITE.SITE_URL}");
            </script>
        </body>
        </html>
        """
        return HTMLResponse(content=error_html)


async def handleOneTapLogin(payload: GoogleCredentialPayload):
    """Handle Google One Tap login."""
    try:
        # Verify token
        id_info = id_token.verify_oauth2_token(
            payload.token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
        
        user_data = await create_or_login_user(id_info, provider="google")
        
        return {"success": True, "data": user_data}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"One Tap login failed: {str(e)}")
