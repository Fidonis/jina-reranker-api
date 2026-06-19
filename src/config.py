"""Application settings loaded from environment / .env file."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_SRC_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_SRC_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Inbound auth. When set, clients MUST present `Authorization: Bearer <api_key>`.
    # Left empty the endpoint is unauthenticated — this is intentional so the
    # service can run unprotected behind another auth layer (e.g. a reverse proxy).
    api_key: str = ""

    # Reranker backend (OpenAI-compatible: LiteLLM, vLLM, …).
    reranker_base_url: str = "http://0.0.0.0:4000"
    # Sent to the backend as `Authorization: Bearer <reranker_api_key>` when set.
    # Distinct from `api_key`: this authenticates *this service to the backend*,
    # never the other way around.
    reranker_api_key: str = ""
    # The model is fixed by configuration, not chosen by the caller, so a client
    # cannot route to an arbitrary backend model by changing the request body.
    reranker_model: str = "rerank-english-v3.0"
    # Hard cap on the number of documents forwarded to the backend.
    # LiteLLM enforces a limit of 1024; lower values reduce backend load.
    max_rerank_docs: int = 1024
    # Timeout in seconds for outgoing HTTP calls to the rerank backend.
    # Increase when reranking large document batches with slow models.
    backend_timeout: float = 60.0

    # Uvicorn bind address used by `python main.py`.
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached singleton settings instance."""
    return Settings()
