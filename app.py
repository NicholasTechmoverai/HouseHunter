import os
import time
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from tortoise import Tortoise
import socketio

from api.v1.endpoints.auth import auth_router
from api.v1.endpoints.user import user_router
from api.v1.endpoints.rentals import rental_router
from api.v1.endpoints.ui_utilities import ui_utilities_router
from api.v1.endpoints.agent import agent_router
from api.v1.endpoints.admin.use_admin import as_admin_router
from api.v1.endpoints.apartments import apartment_router


from websocket.main import MainNamespace
from websocket.map import MapNamespace

from core.limiter import limiter
from core.settings import settings
from core.config import Config

load_dotenv()
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    max_request_size=50 * 1024 * 1024,  # 10MB limit instead of default 1MB
    title=settings.PROJECT_NAME,
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
    expose_headers=settings.EXPOSE_HEADERS,
    max_age=settings.MAX_AGE,
)

app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    reset_time = int(time.time() + 60)
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": 429,
                "message": "Rate limit exceeded. Please try again later.",
                "retry_after": 60,
            }
        },
        headers={
            "X-RateLimit-Limit": str(getattr(exc, "limit", "unknown")),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(reset_time),
            "Retry-After": "60",
        },
    )



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"error": {"code": 500, "message": "Internal server error"}},
    )


@app.get("/health", tags=["Health"])
async def health_check():
    status = {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time(),
    }
    try:
        from models.user import User
        await User.all().count()
        status["database"] = "connected"
    except Exception:
        status["database"] = "disconnected"
        status["status"] = "unhealthy"
    return status


@app.get("/ready", tags=["Health"])
async def readiness_check():
    return {"status": "ready", "timestamp": time.time()}


@app.get("/live", tags=["Health"])
async def liveness_check():
    return {"status": "live", "timestamp": time.time()}


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
    }


sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.ALLOWED_ORIGINS,
)

sio.register_namespace(MainNamespace("/main"))
sio.register_namespace(MapNamespace("/map"))

socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="/ws/socket.io",
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(user_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(rental_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(apartment_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(ui_utilities_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(agent_router, prefix=f"/api/{settings.API_VERSION}")
app.include_router(as_admin_router, prefix=f"/api/{settings.API_VERSION}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    try:
        await Config.init_db(app)
        logger.info("Database connected successfully")
    except Exception as e:
        logger.error(f"Database connection failed: {e}", exc_info=True)

    yield

    logger.info("Closing database connections...")
    await Tortoise.close_connections()
    logger.info("Database closed")


app.router.lifespan_context = lifespan


# uvicorn app:socket_app --host 0.0.0.0 --port 8000 --reload
