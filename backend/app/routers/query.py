"""Query endpoints — JSON response and SSE streaming."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import QueryRequest, QueryResponse
from app.services.rag_pipeline import query, query_stream

logger = logging.getLogger(__name__)

router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    """Ask a question — returns JSON with answer and sources."""
    try:
        loop = asyncio.get_event_loop()
        answer, sources = await loop.run_in_executor(
            None,
            lambda: query(
                question=request.question,
                source_type=request.source_type,
                top_k=request.top_k,
            ),
        )
        return QueryResponse(answer=answer, sources=sources)
    except Exception as e:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(e))


async def _async_stream(question: str, source_type: str | None, top_k: int) -> AsyncGenerator[str, None]:
    """Wrap the sync generator in an async generator using a queue.

    A background thread runs the sync generator and pushes chunks into an
    asyncio.Queue.  The async generator awaits the queue, yielding each
    chunk as it arrives.  This keeps the event loop free while preserving
    true token-by-token streaming.
    """
    queue: asyncio.Queue[str | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def _producer() -> None:
        try:
            gen = query_stream(question=question, source_type=source_type, top_k=top_k)
            for chunk in gen:
                loop.call_soon_threadsafe(queue.put_nowait, chunk)
        except Exception:
            logger.exception("Error during streaming generation")
            loop.call_soon_threadsafe(
                queue.put_nowait,
                f'data: {{"content": "\\n\\n[Error generating response]"}}\n\n',
            )
            loop.call_soon_threadsafe(
                queue.put_nowait, "data: [DONE]\n\n"
            )
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

    loop.run_in_executor(None, _producer)

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk


@router.post("/query/stream")
async def query_stream_endpoint(request: QueryRequest):
    """Ask a question — returns SSE stream with tokens and sources.

    SSE format:
      data: {"content": "token"}
      data: {"sources": [...]}
      data: [DONE]
    """
    try:
        return StreamingResponse(
            _async_stream(
                question=request.question,
                source_type=request.source_type,
                top_k=request.top_k,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.exception("Stream query failed")
        raise HTTPException(status_code=500, detail=str(e))
