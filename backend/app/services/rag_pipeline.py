"""RAG pipeline — orchestrates embed → retrieve → context assembly → generate."""

import json
import logging
from typing import Generator

from app.services.embedding import embed_text
from app.services.vectorstore import query_vectors
from app.services.llm import generate, generate_stream
from app.models.schemas import SourceReference

logger = logging.getLogger(__name__)


def _build_context(matches: list[dict]) -> tuple[str, list[SourceReference]]:
    """Build context string and source references from Pinecone matches."""
    context_parts = []
    sources = []

    for i, match in enumerate(matches):
        meta = match.get("metadata", {})
        preview = meta.get("content_preview", "")
        source_file = meta.get("source_file", "unknown")
        source_type = meta.get("source_type", "text")
        chunk_index = meta.get("chunk_index", 0)

        if preview:
            context_parts.append(f"[Source {i + 1}: {source_file}]\n{preview}")
        else:
            context_parts.append(f"[Source {i + 1}: {source_file} ({source_type})]")

        sources.append(SourceReference(
            source_type=source_type,
            source_file=source_file,
            chunk_index=chunk_index,
            content_preview=preview,
            score=round(match.get("score", 0.0), 4),
        ))

    context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."
    return context, sources


def query(question: str, source_type: str | None = None, top_k: int = 5) -> tuple[str, list[SourceReference]]:
    """Full RAG query: embed question → retrieve → generate answer.

    Returns (answer, sources).
    """
    logger.info("RAG query: question=%s, source_type=%s, top_k=%d", question[:80], source_type, top_k)

    # Step 1: Embed the question
    query_vector = embed_text(question)

    # Step 2: Retrieve from Pinecone
    matches = query_vectors(query_vector, top_k=top_k, source_type=source_type)
    logger.info("Retrieved %d matches from Pinecone", len(matches))

    # Step 3: Build context
    context, sources = _build_context(matches)

    # Step 4: Generate answer
    answer = generate(context, question)

    return answer, sources


def query_stream(question: str, source_type: str | None = None, top_k: int = 5) -> Generator[str, None, None]:
    """Streaming RAG query: embed → retrieve → stream answer via SSE.

    Yields SSE-formatted chunks:
      data: {"content": "token"}\n\n
      data: {"sources": [...]}\n\n
      data: [DONE]\n\n
    """
    logger.info("RAG stream: question=%s, source_type=%s, top_k=%d", question[:80], source_type, top_k)

    # Step 1: Embed the question
    query_vector = embed_text(question)

    # Step 2: Retrieve from Pinecone
    matches = query_vectors(query_vector, top_k=top_k, source_type=source_type)
    logger.info("Retrieved %d matches for streaming", len(matches))

    # Step 3: Build context
    context, sources = _build_context(matches)

    # Step 4: Stream LLM answer
    yield from generate_stream(context, question)

    # Step 5: Send sources after stream completes
    sources_data = [s.model_dump() for s in sources]
    yield f"data: {json.dumps({'sources': sources_data})}\n\n"

    # Step 6: Signal end of stream
    yield "data: [DONE]\n\n"
