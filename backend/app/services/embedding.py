"""Embedding service — all embedding calls go through Euri API.

Uses the OpenAI SDK with Euri base_url. Model: gemini-embedding-2-preview.
Output: 768-dimensional vectors.
"""

import base64
import logging
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.services.euri_client import euri_client

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 768


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def embed_text(text: str) -> list[float]:
    """Embed a text string. Returns 768-dim vector."""
    response = euri_client.embeddings.create(
        model=settings.euri_embedding_model,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response.data[0].embedding


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed multiple text strings in a single call. Returns list of 768-dim vectors."""
    response = euri_client.embeddings.create(
        model=settings.euri_embedding_model,
        input=texts,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return [item.embedding for item in response.data]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def embed_base64(b64_content: str) -> list[float]:
    """Embed base64-encoded content (image, audio, video, PDF).

    NOTE: The Euri API (OpenAI-compatible) only supports text embedding.
    For non-text modalities, we embed a text description of the file.
    Native multimodal embedding requires Google's direct Gemini API.
    """
    # The OpenAI-compatible endpoint doesn't support binary base64 input.
    # Fall back to embedding text description (caller should use embed_text instead).
    raise NotImplementedError(
        "Binary embedding via Euri's OpenAI-compatible endpoint is not supported. "
        "Use embed_text() with extracted text content instead."
    )


def embed_file(file_path: Path) -> list[float]:
    """Read a file, base64-encode it, and embed via Euri."""
    raw = file_path.read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    logger.info("Embedding file: %s (%d bytes)", file_path.name, len(raw))
    return embed_base64(b64)
