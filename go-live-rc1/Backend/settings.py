"""
Centralized configuration for the SCIP backend.

This module consolidates environment variable access using Pydantic's
BaseSettings. Values are loaded from the environment at import time and
validated/coerced to the appropriate type. Providing a single settings
instance avoids repetitive calls to os.environ across modules and makes
default values explicit.
"""

from functools import lru_cache
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Configuration settings for the SCIP backend.

    Each attribute corresponds to an environment variable. Pydantic
    automatically reads from the environment, applies type coercion,
    and falls back to the default value if the variable is not set.
    """

    # Core environment configuration
    FRONTEND_URL: str = "http://localhost:3000"
    SCIP_ENV: str = "local"
    CORS_ALLOWED_ORIGINS: str = ""
    SCIP_AUTH_MODE: str = "jwt"
    SCIP_LOCAL_DEV_BYPASS: bool = False

    # Database and persistence
    SCIP_AUDIT_DB: str = ""

    # Observability
    SCIP_TELEMETRY_EVENT_LIMIT: int = 5000
    SCIP_CACHE_TTL_SECONDS: int = 300

    # Caching for data and action queues (Speed + UI patch)
    SCIP_DATA_CACHE_TTL_SECONDS: int = 900
    SCIP_ACTION_QUEUE_CACHE_TTL_SECONDS: int = 900
    SCIP_WARM_DATA_CACHE_ON_STARTUP: bool = False

    # Data source root
    SCIP_SOURCE_ROOT: str = "/tmp/scip/r-series"

    # Google drive bootstrap
    SCIP_GOOGLE_DRIVE_FOLDER_ID: str = ""
    SCIP_GOOGLE_DRIVE_FOLDER_URL: str = ""
    SCIP_RSERIES_BOOTSTRAP: bool = False

    # JWT / identity configuration
    SCIP_JWT_ISSUER: str = "https://identity.sobha.example/scip"
    SCIP_JWT_AUDIENCE: str = "scip-platform"
    SCIP_JWT_SECRET: str = "scip-local-dev-secret-change-me"

    @validator("CORS_ALLOWED_ORIGINS")
    def normalize_origins(cls, v: str) -> str:
        """Normalize whitespace in CORS origins.

        Splits the comma-separated origins string, trims whitespace
        from each origin, and rejoins them. An empty string remains
        unchanged.
        """
        return ",".join(o.strip() for o in v.split(",") if o.strip())

    class Config:
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Wrapping Settings() in an LRU cache avoids re-parsing environment
    variables on each import.
    """
    return Settings()


# Instantiate settings eagerly so modules can import directly
settings = get_settings()
