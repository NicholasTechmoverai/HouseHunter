import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt
from core.security import SecurityUtils, TokenExpiredError, UnauthorizedError, TokenData
from core.settings import settings

def test_password_hashing():
    password = "MySecurePassword1!"
    hashed = SecurityUtils.hash_password(password)
    
    assert hashed != password
    assert SecurityUtils.verify_password(password, hashed) is True
    assert SecurityUtils.verify_password("wrongpassword", hashed) is False

def test_jwt_generation_and_decoding():
    subject = "user-12345"
    scopes = ["read", "write"]
    
    token = SecurityUtils.create_access_token(subject=subject, scopes=scopes)
    assert isinstance(token, str)
    
    decoded = SecurityUtils.decode_token(token)
    assert isinstance(decoded, TokenData)
    assert decoded.sub == subject
    assert decoded.scopes == scopes
    assert decoded.type == "access"

def test_jwt_refresh_token():
    subject = "user-54321"
    token = SecurityUtils.create_refresh_token(subject=subject)
    
    decoded = SecurityUtils.decode_token(token)
    assert decoded.sub == subject
    assert decoded.type == "refresh"

def test_jwt_expired_token():
    # Generate token with negative expiry
    token = SecurityUtils.create_access_token(subject="user", expires_delta_minutes=-5)
    
    # Decoding with expiry check should raise TokenExpiredError
    with pytest.raises(TokenExpiredError):
        SecurityUtils.decode_token(token, verify_exp=True)
        
    # Decoding without expiry check should succeed and return the token data
    decoded = SecurityUtils.decode_token(token, verify_exp=False)
    assert decoded.sub == "user"

def test_jwt_invalid_token():
    with pytest.raises(UnauthorizedError):
        SecurityUtils.decode_token("completely-invalid-token-string")

def test_jwt_dict_subject_handling():
    # Test backward compatibility where subject payload is encoded as a dict
    expire = datetime.now(timezone.utc) + timedelta(minutes=10)
    payload = {
        "sub": {"user_id": "999"},
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    decoded = SecurityUtils.decode_token(token)
    assert decoded.sub == "999"
