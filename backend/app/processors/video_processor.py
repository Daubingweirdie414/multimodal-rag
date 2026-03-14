"""Video processor — extracts frames, describes with GPT-4o-mini vision, then embeds.

Uses ffmpeg to extract key frames, GPT-4o-mini vision to describe them,
and embeds the combined description for semantic search.
"""

import logging
import uuid

from app.services.embedding import embed_text
from app.services.video_vision import describe_video

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp4", ".mov"}
MAX_DURATION_SECONDS = 120


def validate_video(filename: str) -> bool:
    """Check if file extension is a supported video format."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def process_video(file_bytes: bytes, filename: str) -> list[dict]:
    """Process a video file: extract frames, describe with vision, embed.

    Returns list with one Pinecone-ready vector dict.
    """
    if not validate_video(filename):
        raise ValueError(f"Unsupported video format: {filename}. Allowed: {ALLOWED_EXTENSIONS}")

    size_mb = len(file_bytes) / (1024 * 1024)
    logger.info("Processing video: %s (%.1f MB) — extracting frames for vision", filename, size_mb)

    # Use vision to describe video frames
    description = describe_video(file_bytes, filename)
    if not description:
        description = (
            f"Video file: {filename}. "
            f"Size: {size_mb:.1f} MB. "
            f"Format: {filename.rsplit('.', 1)[-1].upper()}."
        )

    full_description = f"[Video: {filename}] {description}"
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
