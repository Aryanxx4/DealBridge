"""Application settings, read once from the repository-root .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"

REQUIRED_VARS = ("DATABASE_URL", "QDRANT_URL", "APP_SECRET_KEY")
SECRET_VARS = ("LLM_API_KEY", "QDRANT_API_KEY", "APP_SECRET_KEY")


class ConfigError(RuntimeError):
    """Raised when settings are missing or invalid; message lists every problem."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    # Application
    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_SECRET_KEY: str
    BACKEND_PORT: int = 8000
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"

    # PostgreSQL
    DATABASE_URL: str

    # Qdrant
    QDRANT_URL: str
    QDRANT_API_KEY: str = ""
    QDRANT_OFFICIAL_COLLECTION: str = "official_product_knowledge"
    QDRANT_RESOLVED_COLLECTION: str = "resolved_query_knowledge"

    # LLM (single provider: qwen via DashScope OpenAI-compatible API)
    LLM_PROVIDER: str = "qwen"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.8-max"
    LLM_FAST_MODEL: str = "qwen3.8-flash"
    LLM_TIMEOUT_SECONDS: float = 60
    LLM_FAST_TIMEOUT_SECONDS: float = 20
    LLM_MAX_RETRIES: int = 2
    # Test-only: selects the scripted FakeLLMClient. Refused outside APP_ENV=test.
    LLM_USE_FAKE: bool = False

    # Embeddings (local)
    EMBEDDING_PROVIDER: str = "fastembed"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    FASTEMBED_CACHE_DIR: str = "./.cache/fastembed"

    # Retrieval and answer thresholds
    RETRIEVAL_MIN_SCORE: float = 0.50
    RESOLVED_REUSE_MIN_SCORE: float = 0.80
    TOP_K_OFFICIAL: int = 6
    TOP_K_RESOLVED: int = 4
    TICKET_DUP_MIN_SCORE: float = 0.85
    ENABLE_FAITHFULNESS_CHECK: bool = True
    ALLOW_SELF_APPROVAL: bool = True

    # Files
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_MB: int = 20
    MAX_PDF_PAGES: int = 200

    # Knowledge
    OKF_BUNDLE_DIR: str = "./knowledge/official/iomete"

    # Rate limiting can be disabled for tests only.
    RATE_LIMIT_ENABLED: bool = True

    @field_validator("LLM_PROVIDER")
    @classmethod
    def _provider(cls, v: str) -> str:
        if v != "qwen":
            raise ValueError("LLM_PROVIDER must be 'qwen' (the only supported provider)")
        return v

    @field_validator("EMBEDDING_PROVIDER")
    @classmethod
    def _embedding_provider(cls, v: str) -> str:
        if v != "fastembed":
            raise ValueError("EMBEDDING_PROVIDER must be 'fastembed' (the only supported provider)")
        return v

    @field_validator("APP_SECRET_KEY", "DATABASE_URL", "QDRANT_URL")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be empty")
        return v

    # ---- derived helpers -------------------------------------------------
    def resolve_path(self, value: str) -> Path:
        p = Path(value)
        return p if p.is_absolute() else (REPO_ROOT / p).resolve()

    @property
    def upload_dir(self) -> Path:
        return self.resolve_path(self.UPLOAD_DIR)

    @property
    def bundle_dir(self) -> Path:
        return self.resolve_path(self.OKF_BUNDLE_DIR)

    @property
    def fastembed_cache_dir(self) -> Path:
        return self.resolve_path(self.FASTEMBED_CACHE_DIR)

    @property
    def llm_configured(self) -> bool:
        return bool(self.LLM_API_KEY.strip()) or (self.APP_ENV == "test" and self.LLM_USE_FAKE)

    def secret_values(self) -> list[str]:
        return [v for v in (self.LLM_API_KEY, self.QDRANT_API_KEY, self.APP_SECRET_KEY) if v and len(v) >= 8]


def load_settings(**overrides) -> Settings:
    """Build settings, converting validation errors into one readable ConfigError."""
    try:
        settings = Settings(**overrides)
    except ValidationError as exc:
        missing, invalid = [], []
        for err in exc.errors():
            name = str(err["loc"][0]) if err["loc"] else "?"
            (missing if err["type"] == "missing" else invalid).append(
                name if err["type"] == "missing" else f"{name}: {err['msg']}"
            )
        parts = []
        if missing:
            parts.append("Missing required environment variables: " + ", ".join(sorted(missing)))
        if invalid:
            parts.append("Invalid settings: " + "; ".join(invalid))
        raise ConfigError(". ".join(parts) + ". Copy .env.example to .env and fill them in.") from None
    if settings.LLM_USE_FAKE and settings.APP_ENV != "test":
        raise ConfigError("LLM_USE_FAKE=true is only allowed when APP_ENV=test.")
    return settings


@lru_cache
def get_settings() -> Settings:
    return load_settings()

