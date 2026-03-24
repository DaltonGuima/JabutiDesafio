from enum import StrEnum

from pydantic_settings import BaseSettings


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    REDIS_CACHE_TTL: int = 300  # 5 minutos

    CORS_ORIGINS: list[str] = [
        "http://localhost:8000",
        "http://fastapi-app:8000",
    ]
    CORS_ALLOW_METHODS: list[str] = ["GET", "POST", "PUT", "DELETE"]
    CORS_ALLOW_HEADERS: list[str] = ["Content-Type", "Accept"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
