"""Application configuration loaded from environment variables."""

from __future__ import annotations
from pydantic import model_validator
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_DB_PATH = (_BACKEND_DIR / "meeting_intelligence.db").as_posix()


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────
    # Default to SQLite for development without Docker.
    # Set DATABASE_URL in .env to use PostgreSQL in production.
    database_url: str = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"
    database_url_sync: str = f"sqlite:///{_DEFAULT_DB_PATH}"

    # ── Hindsight (Vectorize) ─────────────────────────────────
    hindsight_api_key: str = ""
    hindsight_base_url: str = "https://api.hindsight.vectorize.io"
    hindsight_memory_bank_id: str = "meeting-intelligence"

    # ── LLM ───────────────────────────────────────────────────
    groq_api_key: str = ""
    llm_model: str = "qwen/qwen3.8-27b"
    llm_provider: str = "groq"  # groq | openai | mock

    openai_api_key: str = ""
    openai_base_url: str = ""

    # ── App ───────────────────────────────────────────────────
    app_env: str = "development"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:3005,http://127.0.0.1:3000,http://127.0.0.1:3005"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @model_validator(mode="after")
    def _normalize_sqlite_url(self) -> Settings:
        prefix = "sqlite+aiosqlite:///"
        if self.database_url.startswith(prefix):
            path_part = self.database_url[len(prefix):]
            if not Path(path_part).is_absolute() and not (len(path_part) > 2 and path_part[1] == ":"):
                clean_path = path_part.lstrip("./").lstrip(".\\")
                abs_path = (_BACKEND_DIR / clean_path).resolve().as_posix()
                self.database_url = f"{prefix}{abs_path}"

        sync_prefix = "sqlite:///"
        if self.database_url_sync.startswith(sync_prefix):
            path_part = self.database_url_sync[len(sync_prefix):]
            if not Path(path_part).is_absolute() and not (len(path_part) > 2 and path_part[1] == ":"):
                clean_path = path_part.lstrip("./").lstrip(".\\")
                abs_path = (_BACKEND_DIR / clean_path).resolve().as_posix()
                self.database_url_sync = f"{sync_prefix}{abs_path}"

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
