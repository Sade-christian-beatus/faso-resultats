from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    cors_origins: str = "http://localhost:8080"

    database_url: str = "postgresql+asyncpg://faso:faso_secret@db:5432/faso_resultats"

    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 300

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Profil candidat (plateforme, transversal aux tenants) — docs/PROFIL_CANDIDAT_UNIFIE.md
    candidat_jwt_expire_minutes: int = 60 * 24 * 30  # session 30 jours (§ 4.2)
    candidat_encryption_key: str = "OgXLPUp9gH0vXWzvXG2zxQx0n4XJEwxbUBEKsbhBzlE="
    candidat_hash_pepper: str = "change-me-in-production"
    candidat_otp_expire_minutes: int = 5
    candidat_otp_max_tentatives: int = 3

    rate_limit_public: str = "30/minute"
    rate_limit_login: str = "5/minute"

    uploads_dir: str = "/app/uploads"
    max_upload_size_mb: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
