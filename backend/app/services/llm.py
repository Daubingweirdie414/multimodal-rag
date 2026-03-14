"""LLM generation service — all LLM calls go through Euri API.

Model: gpt-4o-mini via Euri. Supports both sync and streaming responses.
"""

import json
import logging
from typing import Generator

from app.config import settings
from app.services.euri_client import euri_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful multimodal RAG assistant. You answer questions using the provided context which may include text documents, PDFs, image descriptions, audio transcriptions, and video descriptions.

Rules:
1. Answer using information from the context below. Do not use prior knowledge for factual claims.
2. If the context contains relevant information — even partial — use it to answer helpfully. Describe what you found.
3. For image/video/audio sources, describe what is depicted or contained based on the context provided.
4. Only say you don't have enough information if the context is truly unrelated to the question.
5. Cite your sources by referencing the source file name and type.
6. Be concise, accurate, and helpful.
7. If the context contains information from multiple sources and modalities, synthesize it clearly."""


def _build_messages(context: str, question: str) -> list[dict]:
    """Build the message array for the LLM call."""
    user_message = f"""Context (retrieved from knowledge base):
---
{context}
---

Question: {question}"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


def generate(context: str, question: str) -> str:
    """Generate a non-streaming response."""
    messages = _build_messages(context, question)
    response = euri_client.chat.completions.create(
        model=settings.euri_llm_model,
        messages=messages,
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content


def generate_stream(context: str, question: str) -> Generator[str, None, None]:
    """Generate a streaming response. Yields SSE-formatted data chunks.

    Format:
      data: {"content": "token"}\n\n     — for each token
      data: [DONE]\n\n                   — when complete
    """
    messages = _build_messages(context, question)
    stream = euri_client.chat.completions.create(
        model=settings.euri_llm_model,
        messages=messages,
        temperature=0.3,
        max_tokens=2048,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            yield f"data: {json.dumps({'content': delta.content})}\n\n"
