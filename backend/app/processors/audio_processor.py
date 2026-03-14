"""Audio processor — transcribes audio with Whisper, then embeds the transcript.

Uses OpenAI Whisper API via Euri for transcription, then embeds the text
for semantic search.
"""

import logging
import uuid

from app.services.embedding import embed_text
from app.services.audio_transcription import transcribe_audio

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".mp3", ".wav"}


def validate_audio(filename: str) -> bool:
    """Check if file extension is a supported audio format."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


def process_audio(file_bytes: bytes, filename: str) -> list[dict]:
    """Process an audio file: transcribe with Whisper, then embed.

    Returns list with one Pinecone-ready vector dict.
    """
    if not validate_audio(filename):
        raise ValueError(f"Unsupported audio format: {filename}. Allowed: {ALLOWED_EXTENSIONS}")

    size_mb = len(file_bytes) / (1024 * 1024)
    logger.info("Processing audio: %s (%.1f MB) — transcribing with Whisper", filename, size_mb)

    # Transcribe audio
    transcript = transcribe_audio(file_bytes, filename)
    if not transcript:
        transcript = (
            f"Audio file: {filename}. "
            f"Size: {size_mb:.1f} MB. "
            f"Format: {filename.rsplit('.', 1)[-1].upper()}."
        )

    full_description = f"[Audio: {filename}] {transcript}"
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
