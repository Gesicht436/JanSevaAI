"""
Application Configuration
Loads settings from environment variables and local .env file.
"""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    ADMIN_TOKEN: str = ""
    DATABASE_PATH: str = "backend/Datasets/schemes.db"

    # LLM Providers Configuration
    LLM_PROVIDER: str = "gemini"  # "gemini" or "openrouter"
    
    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # OpenRouter API (Alternative / failover)
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-4-31b-it:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Text-to-Speech (TTS) Configuration
    TTS_PROVIDER: str = "edge-tts"  # "edge-tts" or "google-cloud"
    GOOGLE_TTS_API_KEY: str = ""

    # Crawler Settings
    MYSCHEME_BASE_URL: str = "https://www.myscheme.gov.in"
    CRAWL_CONCURRENCY: int = 3
    CRAWL_DELAY_SECONDS: float = 0.35
    CRAWL_LIMIT: int = 200

    @property
    def resolved_database_path(self) -> Path:
        path = Path(self.DATABASE_PATH)
        if path.is_absolute() and path.is_file():
            return path
        candidates = [
            Path(__file__).resolve().parent.parent / "Datasets" / "schemes.db",
            PROJECT_ROOT / "backend" / "Datasets" / "schemes.db",
            Path.cwd() / "backend" / "Datasets" / "schemes.db",
            Path("/var/task/backend/Datasets/schemes.db"),
            PROJECT_ROOT / path,
            Path.cwd() / path,
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        raise FileNotFoundError(f"Canonical database not found. Checked: {[str(c) for c in candidates]}")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
