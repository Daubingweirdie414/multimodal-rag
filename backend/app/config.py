"""Application configuration — loads and validates all env vars at startup."""

import os
import logging
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    # Euri API (unified provider for embedding + LLM)
    euri_api_key: str
    euri_base_url: str
    euri_embedding_model: str
    euri_llm_model: str

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str

    # App
    cors_origins: list[str]
    log_level: str


def _require(key: str) -> str:
    """Get a required env var or fail fast."""
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def load_settings() -> Settings:
    """Load and validate all settings from environment. Fail fast on missing vars."""
    settings = Settings(
        euri_api_key=_require("EURI_API_KEY"),
        euri_base_url=os.getenv("EURI_BASE_URL", "https://api.euron.one/api/v1/euri"),
        euri_embedding_model=os.getenv("EURI_EMBEDDING_MODEL", "gemini-embedding-2-preview"),
        euri_llm_model=os.getenv("EURI_LLM_MODEL", "gpt-4o-mini"),
        pinecone_api_key=_require("PINECONE_API_KEY"),
        pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "rag-multimodal"),
        cors_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,*").split(","),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
    logger.info(
        "Settings loaded: euri_base_url=%s, embedding_model=%s, llm_model=%s, pinecone_index=%s",
        settings.euri_base_url,
        settings.euri_embedding_model,
        settings.euri_llm_model,
        settings.pinecone_index_name,
    )
    return settings


# Singleton — imported across the app
settings = load_settings()
