"""Pydantic request/response models for all API endpoints."""

from pydantic import BaseModel, Field


# ── Ingestion ────────────────────────────────────────────────

class TextIngestRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Raw text to ingest")


class IngestResponse(BaseModel):
    status: str  # "success" | "error"
    source_type: str
    source_file: str
    chunks_ingested: int
    message: str


# ── Query ────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    source_type: str | None = Field(None, description="Filter by source type: text|pdf|image|audio|video")
    top_k: int = Field(5, ge=1, le=20, description="Number of results to retrieve")


class SourceReference(BaseModel):
    source_type: str
    source_file: str
    chunk_index: int
    content_preview: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]


# ── Utility ──────────────────────────────────────────────────

class IngestedFileInfo(BaseModel):
    source_type: str
    source_file: str
    chunk_count: int
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    message: str
