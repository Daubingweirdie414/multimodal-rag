"""PDF processor — splits PDFs into batches of 6 pages, embeds each batch."""

import io
import logging
import uuid

from PyPDF2 import PdfReader, PdfWriter

from app.services.embedding import embed_text, embed_texts
from app.processors.text_processor import splitter

logger = logging.getLogger(__name__)

MAX_PAGES_PER_BATCH = 6


def process_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    """Process a PDF file. Strategy:
    - <= 6 pages: extract text, chunk, embed as text
    - > 6 pages: split into 6-page batches, extract text from each, chunk, embed

    Returns list of Pinecone-ready vector dicts.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    total_pages = len(reader.pages)
    logger.info("Processing PDF: %s (%d pages)", filename, total_pages)

    # Extract text from all pages
    all_text_chunks = []
    for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            all_text_chunks.append((page_num + 1, page_text))

    if not all_text_chunks:
        logger.warning("No text extracted from PDF: %s", filename)
        return []

    # Combine and chunk the extracted text
    full_text = "\n\n".join(text for _, text in all_text_chunks)
    chunks = splitter.split_text(full_text)

    if not chunks:
        return []

    logger.info("Split PDF into %d text chunks (source=%s)", len(chunks), filename)

    embeddings = embed_texts(chunks)

    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": embedding,
            "metadata": {
                "source_file": filename,
                "chunk_index": i,
                "content_preview": chunk[:200],
                "total_pages": total_pages,
            },
        })

    return vectors
