from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Path .env relatif terhadap root proyek, bukan CWD proses
_ROOT_PROYEK = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT_PROYEK / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = "postgresql+asyncpg://echo:echo@localhost:5432/echo"
    ANTHROPIC_API_KEY: str = ""
    VOYAGE_API_KEY: str = ""
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3000"
    JWT_SECRET: str = "dev-secret-change-in-production"
    DEMO_RATE_LIMIT: str = "5/minute"


settings = Settings()
