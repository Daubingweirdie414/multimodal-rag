"""Vision service — uses GPT-4o-mini via Euri to describe images for embedding."""

import base64
import logging

from app.services.euri_client import euri_client
from app.config import settings

logger = logging.getLogger(__name__)


def describe_image(file_bytes: bytes, filename: str) -> str:
    """Use GPT-4o-mini vision to generate a detailed text description of an image.

    The description is used for text-based embedding since the Euri embeddings
    endpoint only supports text input.
    """
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    ext = filename.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"

    response = euri_client.chat.completions.create(
        model=settings.euri_llm_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe this image in detail. Include: what is shown, "
                            "people (appearance, expression, clothing), objects, colors, "
                            "setting/background, text visible, and overall mood. "
                            "Be thorough — this description will be used for search retrieval."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime};base64,{b64}",
                        },
                    },
                ],
            }
        ],
        max_tokens=512,
        temperature=0.2,
    )

    description = response.choices[0].message.content or ""
    logger.info("Vision description for %s: %s", filename, description[:100])
    return description
