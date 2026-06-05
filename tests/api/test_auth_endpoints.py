import pytest
from httpx import AsyncClient
from models.user import User

@pytest.mark.anyio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "email": "register@example.com",
        "password": "SecurePassword1!",
        "confirm_password": "SecurePassword1!",
        "first_name": "New",
        "last_name": "User",
        "phone_number": "+254711223344",
        "username": "newuser"
    }
    
    response = await client.post("/api/v1/auth/user/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["email"] == "register@example.com"

@pytest.mark.anyio
async def test_register_user_password_mismatch(client: AsyncClient):
    payload = {
        "email": "mismatch@example.com",
        "password": "SecurePassword1!",
        "confirm_password": "DifferentPassword1!",
        "first_name": "New",
        "last_name": "User"
    }
    
    response = await client.post("/api/v1/auth/user/register", json=payload)
    assert response.status_code == 422
    assert "Passwords do not match" in str(response.json()["detail"])

@pytest.mark.anyio
async def test_register_user_duplicate_email(client: AsyncClient, create_test_user: User, sample_user_data: dict):
    payload = {
        "email": sample_user_data["email"],
        "password": "SecurePassword1!",
        "confirm_password": "SecurePassword1!",
        "first_name": "Duplicate",
        "last_name": "User",
        "username": "dupuser"
    }
    
    response = await client.post("/api/v1/auth/user/register", json=payload)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

@pytest.mark.anyio
async def test_login_user_success(client: AsyncClient, create_test_user: User, sample_user_data: dict):
    payload = {
        "email": sample_user_data["email"],
        "password": sample_user_data["password"]
    }
    
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == sample_user_data["email"]

@pytest.mark.anyio
async def test_login_user_invalid_credentials(client: AsyncClient, create_test_user: User, sample_user_data: dict):
    payload = {
        "email": sample_user_data["email"],
        "password": "wrongpassword"
    }
    
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]
