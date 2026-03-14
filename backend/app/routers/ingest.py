"""Ingestion endpoints — one per modality."""

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import IngestResponse, TextIngestRequest
from app.processors.text_processor import process_text
from app.processors.pdf_processor import process_pdf
from app.processors.image_processor import process_image, validate_image
from app.processors.audio_processor import process_audio, validate_audio
from app.processors.video_processor import process_video, validate_video
from app.services.vectorstore import upsert_vectors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingestion"])


@router.post("/text", response_model=IngestResponse)
async def ingest_text(request: TextIngestRequest) -> IngestResponse:
    """Ingest raw text — chunks and embeds."""
    try:
        vectors = process_text(request.text, source_file="raw_text")
        count = upsert_vectors(vectors, source_type="text")
        return IngestResponse(
            status="success",
            source_type="text",
            source_file="raw_text",
            chunks_ingested=count,
            message=f"Ingested {count} text chunks",
        )
    except Exception as e:
        logger.exception("Text ingestion failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest a PDF file."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted")
    try:
        contents = await file.read()
        vectors = process_pdf(contents, file.filename)
        count = upsert_vectors(vectors, source_type="pdf")
        return IngestResponse(
            status="success",
            source_type="pdf",
            source_file=file.filename,
            chunks_ingested=count,
            message=f"Ingested {count} chunks from {file.filename}",
        )
    except Exception as e:
        logger.exception("PDF ingestion failed: %s", file.filename)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image", response_model=IngestResponse)
async def ingest_image(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest an image file (PNG, JPEG)."""
    if not file.filename or not validate_image(file.filename):
        raise HTTPException(status_code=400, detail="Only .png, .jpg, .jpeg files are accepted")
    try:
        contents = await file.read()
        vectors = process_image(contents, file.filename)
        count = upsert_vectors(vectors, source_type="image")
        return IngestResponse(
            status="success",
            source_type="image",
            source_file=file.filename,
            chunks_ingested=count,
            message=f"Ingested image: {file.filename}",
        )
    except Exception as e:
        logger.exception("Image ingestion failed: %s", file.filename)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audio", response_model=IngestResponse)
async def ingest_audio(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest an audio file (MP3, WAV) — embedded natively, no transcription."""
    if not file.filename or not validate_audio(file.filename):
        raise HTTPException(status_code=400, detail="Only .mp3, .wav files are accepted")
    try:
        contents = await file.read()
        vectors = process_audio(contents, file.filename)
        count = upsert_vectors(vectors, source_type="audio")
        return IngestResponse(
            status="success",
            source_type="audio",
            source_file=file.filename,
            chunks_ingested=count,
            message=f"Ingested audio: {file.filename}",
        )
    except Exception as e:
        logger.exception("Audio ingestion failed: %s", file.filename)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video", response_model=IngestResponse)
async def ingest_video(file: UploadFile = File(...)) -> IngestResponse:
    """Ingest a video file (MP4, MOV) — embedded natively."""
    if not file.filename or not validate_video(file.filename):
        raise HTTPException(status_code=400, detail="Only .mp4, .mov files are accepted")
    try:
        contents = await file.read()
        vectors = process_video(contents, file.filename)
        count = upsert_vectors(vectors, source_type="video")
        return IngestResponse(
            status="success",
            source_type="video",
            source_file=file.filename,
            chunks_ingested=count,
            message=f"Ingested video: {file.filename}",
        )
    except Exception as e:
        logger.exception("Video ingestion failed: %s", file.filename)
        raise HTTPException(status_code=500, detail=str(e))
