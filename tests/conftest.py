import asyncio
import pytest
from typing import AsyncGenerator, Generator
from contextlib import asynccontextmanager

# Override settings BEFORE importing anything else
from core.settings import settings
settings.SECRET_KEY = "test-secret-key-at-least-32-chars-long-for-testing"
settings.DATABASE_URL = "sqlite://:memory:"
settings.ENVIRONMENT = "testing"

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from tortoise import Tortoise

from app import app as fastapi_app
from core.config import MODEL_PATHS
from core.security import SecurityUtils
from models.user import User

# Override FastAPI App Lifespan to prevent it from initializing the production MySQL/Redis DB
@asynccontextmanager
async def mock_lifespan(app: FastAPI):
    # Setup test database connections
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": MODEL_PATHS}
    )
    await Tortoise.generate_schemas()
    
    yield
    
    # Clean up test database connections
    await Tortoise.close_connections()

# Monkey-patch the lifespan context manager
fastapi_app.router.lifespan_context = mock_lifespan

@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"

@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator[None, None]:
    """
    Initializes a clean SQLite database in memory for each test function
    to prevent test-to-test contamination.
    """
    # Tortoise init
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": MODEL_PATHS}
    )
    await Tortoise.generate_schemas()
    
    try:
        yield
    finally:
        await Tortoise.close_connections()

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    HTTPX AsyncClient fixture for testing API endpoints.
    """
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# --- Sample Data Fixtures ---

@pytest.fixture
async def sample_user_data() -> dict:
    """Returns a dictionary containing sample user data."""
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "User",
        "phone_number": "+254712345678"
    }

@pytest.fixture
async def create_test_user(sample_user_data: dict) -> User:
    """Creates and returns a verified active user in the database."""
    user = await User.create(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        phone_number=sample_user_data["phone_number"],
        email_verified=True,
        phone_verified=True,
        status=1  # UserStatus.ACTIVE
    )
    user.set_password(sample_user_data["password"])
    await user.save()
    return user

@pytest.fixture
async def auth_headers(create_test_user: User) -> dict:
    """Returns headers with a valid JWT Bearer token for the test user."""
    token = SecurityUtils.create_access_token(subject=str(create_test_user.id))
    return {"Authorization": f"Bearer {token}"}
