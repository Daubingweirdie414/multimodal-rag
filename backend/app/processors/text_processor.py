"""Text processor — chunking with RecursiveCharacterTextSplitter."""

import logging
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.services.embedding import embed_texts

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024
CHUNK_OVERLAP = 256

splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def process_text(text: str, source_file: str = "raw_text") -> list[dict]:
    """Chunk text and embed each chunk. Returns list of Pinecone-ready vector dicts."""
    chunks = splitter.split_text(text)
    if not chunks:
        return []

    logger.info("Split text into %d chunks (source=%s)", len(chunks), source_file)

    embeddings = embed_texts(chunks)

    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "source_file": source_file,
                "chunk_index": i,
                "content_preview": chunk[:200],
            },
        })

    return vectors
