"""Application settings, read from environment (.env supported). No hardcoded
secrets or connection strings — DATABASE_URL unset means Phase 1 in-memory repos;
set means Phase 2 Postgres repos (see api/deps.py)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PERMISSIONS_")

    database_url: str | None = None

    jwt_secret: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    jwt_issuer: str = "premissions-mock-adfs"
    jwt_audience: str = "permissions-server"

    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
