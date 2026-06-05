from typing import List
from pydantic import AnyHttpUrl, AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SiteInfo(BaseSettings):
    SITE_NAME: str = "House Hunter"
    SITE_DESCRIPTION: str = "Scalable backend service"
    # SITE_URL: str = "https://househunter.tera-in.top"
    SITE_URL: str = "http://localhost:3000"
    LOGO: str = f"{SITE_URL}/f_logo.png"  # Uppercase to match usage
    API_SITE_URL:str = "https://api.tera-in.top"
    FILE_READ_API:str = "https://api.tera-in.top/uploads"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )


class Settings(BaseSettings):
    PROJECT_NAME: str = "MyBackendAPI"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"

    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ALLOWED_ORIGINS: List[AnyHttpUrl] = [
    #     "http://localhost:5173",
    #     "http://localhost:3000",
    #     "https://househunter.tera-in.top",
    #     "https://www.househunter.tera-in.top",
    #     "https://api.tera-in.top",  # Add this if needed
    # ]
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://househunter.tera-in.top",
        "https://www.househunter.tera-in.top",
    ]

    ALLOWED_METHODS: List[str] = [
        "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"
    ]

    ALLOWED_HEADERS: List[str] = [
        "*",  # Or be more specific:
        # "Authorization",
        # "Content-Type",
        # "Accept",
        # "Origin",
        # "X-Requested-With",
        # "X-Request-ID",
        # "X-CSRF-Token",
        # "X-Client-Version",
        # "Access-Control-Request-Method",  # Added for preflight
        # "Access-Control-Request-Headers",  # Added for preflight
    ]

    EXPOSE_HEADERS: List[str] = [
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ]

    MAX_AGE: int = 3600

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    EMAIL: str | None = None
    EMAIL_PASSWORD: str | None = None
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 587

    DATABASE_URL: str | None = "mysql://root:root@localhost/house_hunter"
    REDIS_URL: str | None ="redis://localhost:6379/0"


    SITE: SiteInfo = SiteInfo()

    APARTMENT_STATS_RATE_LIMIT: str = "60/minute"
    APARTMENT_CREATE_RATE_LIMIT: str = "10/minute"
    APARTMENT_LIST_RATE_LIMIT: str = "120/minute"
    APARTMENT_SEARCH_RATE_LIMIT: str = "60/minute"
    APARTMENT_MY_LIST_RATE_LIMIT: str = "30/minute"
    APARTMENT_DETAIL_RATE_LIMIT: str = "60/minute"
    APARTMENT_UPDATE_RATE_LIMIT: str = "30/minute"
    APARTMENT_DELETE_RATE_LIMIT: str = "10/minute"
    APARTMENT_PUBLISH_RATE_LIMIT: str = "10/minute"
    APARTMENT_FEATURE_RATE_LIMIT: str = "15/minute"
    APARTMENT_APPROVE_RATE_LIMIT: str = "20/minute"
    APARTMENT_IMAGE_RATE_LIMIT: str = "20/minute"
    APARTMENT_ANALYTICS_RATE_LIMIT: str = "30/minute"
    APARTMENT_BULK_RATE_LIMIT: str = "5/minute"

    MAX_APARTMENTS_PER_USER: int = 10
    MAX_APARTMENT_IMAGES: int = 20
    MIN_APARTMENT_PRICE: float = 100.0
    MAX_APARTMENT_PRICE: float = 10000.0

    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        if isinstance(value, str):
            if value.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore", # CONTROL STRICTNESS TO .ENV , SWTCH TO 'forbid' IF STRICTNESS NEEDED
        case_sensitive=False
    )


settings = Settings()
