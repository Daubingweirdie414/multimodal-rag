"""Video vision service — extracts frames and describes them with GPT-4o-mini."""

import logging
import subprocess
import tempfile
from pathlib import Path

from app.services.vision import describe_image

logger = logging.getLogger(__name__)

# Number of frames to extract for description
NUM_FRAMES = 3


def extract_frames(file_bytes: bytes, filename: str, num_frames: int = NUM_FRAMES) -> list[bytes]:
    """Extract evenly-spaced frames from a video using ffmpeg.

    Returns list of JPEG-encoded frame bytes.
    """
    frames: list[bytes] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        video_path = Path(tmpdir) / filename
        video_path.write_bytes(file_bytes)

        # Get video duration
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True, text=True, timeout=30,
        )
        try:
            duration = float(result.stdout.strip())
        except (ValueError, AttributeError):
            logger.warning("Could not determine video duration for %s, using single frame", filename)
            duration = 0.0
            num_frames = 1

        # Extract frames at evenly spaced timestamps
        timestamps = [duration * (i + 1) / (num_frames + 1) for i in range(num_frames)] if duration > 0 else [0.0]

        for i, ts in enumerate(timestamps):
            frame_path = Path(tmpdir) / f"frame_{i}.jpg"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-ss", str(ts),
                    "-i", str(video_path),
                    "-vframes", "1", "-q:v", "2",
                    str(frame_path),
                ],
                capture_output=True, timeout=30,
            )
            if frame_path.exists():
                frames.append(frame_path.read_bytes())

    return frames


def describe_video(file_bytes: bytes, filename: str) -> str:
    """Extract frames from video and describe them using GPT-4o-mini vision.

    Returns a combined description of the video content.
    """
    frames = extract_frames(file_bytes, filename)
    if not frames:
        logger.warning("No frames extracted from %s", filename)
        return ""

    descriptions: list[str] = []
    for i, frame_bytes in enumerate(frames):
        try:
            desc = describe_image(frame_bytes, f"{filename}_frame_{i}.jpg")
            if desc:
                descriptions.append(f"Frame {i + 1}: {desc}")
        except Exception:
            logger.exception("Failed to describe frame %d of %s", i, filename)

    if not descriptions:
        return ""

    combined = f"Video '{filename}' contains {len(frames)} analyzed frames.\n\n" + "\n\n".join(descriptions)
    logger.info("Video description for %s: %s", filename, combined[:100])
    return combined
