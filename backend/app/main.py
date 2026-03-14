"""FastAPI application — entry point with CORS, routers, and health check."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import HealthResponse
from app.routers import ingest, query

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Multimodal RAG System",
    description="RAG system with Gemini Embedding 2 + Pinecone + GPT-4o-mini via Euri API",
    version="1.0.0",
)

# CORS — allow all origins for dev (direct browser-to-backend uploads)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(ingest.router)
app.include_router(query.router)


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="ok", message="Multimodal RAG System is running")


@app.get("/ingested")
async def list_ingested():
    """List ingested files — placeholder for future implementation.

    In production, this would query Pinecone metadata or a local DB
    to return all ingested files with their metadata.
    """
    return {"files": [], "message": "Ingested files listing — connect to metadata store for full list"}
