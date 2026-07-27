from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    app_name: str = "День первокурсника 2026 API"
    environment: str = "development"
    database_url: str = "postgresql+asyncpg://freshman:freshman@db:5432/freshman"
    secret_key: str = "development-only-change-me"
    qr_pepper: str = "development-only-change-me"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    secure_cookies: bool = False
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    student_session_days: int = 2
    qr_ttl_minutes: int = 15
    login_rate_limit: int = 5
    login_rate_limit_window_seconds: int = 900
    max_upload_bytes: int = 20 * 1024 * 1024
    max_import_rows: int = 50_000
    upload_dir: str = "/data/uploads"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
