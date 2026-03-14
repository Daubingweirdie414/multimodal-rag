"""Shared Euri/OpenAI client — single client for both embedding and LLM calls."""

from openai import OpenAI

from app.config import settings


def get_euri_client() -> OpenAI:
    """Create OpenAI client pointed at Euri's base URL."""
    return OpenAI(
        api_key=settings.euri_api_key,
        base_url=settings.euri_base_url,
    )


# Singleton client — reused across services
euri_client = get_euri_client()
