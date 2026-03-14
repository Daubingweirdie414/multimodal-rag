"""Pinecone vector store — upsert, query, delete with namespace-per-source-type strategy."""

import logging
from datetime import datetime, timezone

from pinecone import Pinecone

from app.config import settings

logger = logging.getLogger(__name__)

NAMESPACE_MAP = {
    "text": "ns_text",
    "pdf": "ns_pdf",
    "image": "ns_image",
    "audio": "ns_audio",
    "video": "ns_video",
}

UPSERT_BATCH_SIZE = 100


def _get_index():
    """Get Pinecone index (lazy init)."""
    pc = Pinecone(api_key=settings.pinecone_api_key)
    return pc.Index(settings.pinecone_index_name)


index = _get_index()


def upsert_vectors(
    vectors: list[dict],
    source_type: str,
) -> int:
    """Upsert vectors to Pinecone in batches of 100.

    Each vector dict must have: {"id": str, "values": list[float], "metadata": dict}
    Metadata is enriched with timestamp automatically.

    Returns total upserted count.
    """
    namespace = NAMESPACE_MAP.get(source_type, "ns_text")
    now = datetime.now(timezone.utc).isoformat()

    # Enrich metadata
    for v in vectors:
        v["metadata"]["source_type"] = source_type
        v["metadata"]["timestamp"] = now

    total = 0
    for i in range(0, len(vectors), UPSERT_BATCH_SIZE):
        batch = vectors[i : i + UPSERT_BATCH_SIZE]
        index.upsert(vectors=batch, namespace=namespace)
        total += len(batch)
        logger.info("Upserted batch %d-%d to namespace=%s", i, i + len(batch), namespace)

    return total


def query_vectors(
    query_vector: list[float],
    top_k: int = 5,
    source_type: str | None = None,
) -> list[dict]:
    """Query Pinecone for similar vectors.

    If source_type is provided, search only that namespace.
    Otherwise, search all namespaces and merge results.

    Returns list of {id, score, metadata} dicts sorted by score desc.
    """
    if source_type and source_type in NAMESPACE_MAP:
        namespace = NAMESPACE_MAP[source_type]
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )
        return _parse_matches(results)

    # Search all namespaces and merge
    all_matches = []
    for ns in NAMESPACE_MAP.values():
        try:
            results = index.query(
                vector=query_vector,
                top_k=top_k,
                namespace=ns,
                include_metadata=True,
            )
            all_matches.extend(_parse_matches(results))
        except Exception as e:
            logger.warning("Query failed for namespace=%s: %s", ns, e)

    # Sort by score descending and take top_k
    all_matches.sort(key=lambda x: x["score"], reverse=True)
    return all_matches[:top_k]


def delete_vectors(ids: list[str], source_type: str) -> None:
    """Delete vectors by ID from the appropriate namespace."""
    namespace = NAMESPACE_MAP.get(source_type, "ns_text")
    index.delete(ids=ids, namespace=namespace)
    logger.info("Deleted %d vectors from namespace=%s", len(ids), namespace)


def _parse_matches(results) -> list[dict]:
    """Parse Pinecone query response into a clean list."""
    matches = []
    for match in results.get("matches", []):
        matches.append({
            "id": match["id"],
            "score": match["score"],
            "metadata": match.get("metadata", {}),
        })
    return matches
