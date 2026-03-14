"""Image processor — uses GPT-4o-mini vision to describe images, then embeds the description.

Since the Euri embeddings endpoint only supports text input, we first use
GPT-4o-mini's vision capability to generate a rich text description of the
image, then embed that description for semantic search.
"""

import logging
import uuid

from app.services.embedding import embed_text
from app.services.vision import describe_image

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
MAX_IMAGES_PER_BATCH = 6


def validate_image(filename: str) -> bool:
    """Check if file extension is a supported image format."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def process_image(file_bytes: bytes, filename: str) -> list[dict]:
    """Process a single image: describe with vision LLM, then embed the description."""
    if not validate_image(filename):
        raise ValueError(f"Unsupported image format: {filename}. Allowed: {ALLOWED_EXTENSIONS}")

    size_kb = len(file_bytes) / 1024
    logger.info("Processing image: %s (%.0f KB) — generating vision description", filename, size_kb)

    # Use GPT-4o-mini vision to describe the image content
    description = describe_image(file_bytes, filename)
    if not description:
        description = f"Image file: {filename}. Format: {filename.rsplit('.', 1)[-1].upper()}."

    # Prefix with filename for context
    full_description = f"[Image: {filename}] {description}"

    embedding = embed_text(full_description)

    return [{
        "id": str(uuid.uuid4()),
        "values": embedding,
        "metadata": {
            "source_file": filename,
            "chunk_index": 0,
            "content_preview": full_description[:200],
        },
    }]


def process_images(files: list[tuple[bytes, str]]) -> list[dict]:
    """Process multiple images."""
    vectors = []
    for file_bytes, filename in files:
        vectors.extend(process_image(file_bytes, filename))
    return vectors
