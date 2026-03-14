# Multimodal RAG System — Project Instructions

> Production-grade multimodal RAG system.
> Processes text, PDFs, images, audio, and video in a unified vector space.

---

## Project Overview

This is a **Multimodal Retrieval-Augmented Generation (RAG)** system that processes **text, PDFs, documents, images, audio, and video** inputs. It embeds them using **Gemini Embedding 2 Preview** via the **Euri API**, stores vectors in **Pinecone**, and generates responses using **gpt-4o-mini** via the **Euri API**. The system has a **Next.js + TypeScript** frontend with a ChatGPT-like chat interface and a data ingestion dashboard.

---

## Tech Stack (LOCKED)

| Component | Technology |
|-----------|-----------|
| **Embedding Model** | Gemini Embedding 2 Preview (`gemini-embedding-2-preview`) via Euri API |
| **Vector Database** | Pinecone (serverless) |
| **LLM for Generation** | `gpt-4o-mini` via Euri API |
| **API Provider** | **Euri** (`https://api.euron.one/api/v1/euri`) — OpenAI SDK compatible |
| **Backend** | Python 3.11+ / FastAPI |
| **Frontend** | Next.js 15 (App Router) + TypeScript + Tailwind CSS |
| **Styling** | Tailwind CSS |

### Do NOT substitute:
- Embedding: Must be `gemini-embedding-2-preview` via Euri (NOT direct Google SDK, NOT OpenAI embeddings)
- Vector DB: Must be Pinecone (NOT pgvector, NOT Weaviate, NOT Qdrant)
- LLM: Must be `gpt-4o-mini` via Euri (NOT direct OpenAI endpoint)
- API Provider: Must be Euri (`api.euron.one`) for BOTH embedding and LLM

---

## Euri API — Unified Provider (CRITICAL)

Both embedding and LLM calls go through the **Euri API** using the **OpenAI Python SDK** with a custom `base_url`. This is the most important rule — do NOT use Google's SDK or OpenAI's default endpoint.

### Embedding Client Setup

```python
from openai import OpenAI

client = OpenAI(
    api_key=EURI_API_KEY,
    base_url="https://api.euron.one/api/v1/euri"
)

response = client.embeddings.create(
    model="gemini-embedding-2-preview",
    input="Your text here",
    dimensions=768
)

embedding = response.data[0].embedding  # list of 768 floats
```

### LLM Client Setup

```python
from openai import OpenAI

client = OpenAI(
    api_key=EURI_API_KEY,
    base_url="https://api.euron.one/api/v1/euri"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Your question here"}
    ],
    max_tokens=2048,
    temperature=0.3
)

answer = response.choices[0].message.content
```

### Key Rules
- **Single API key** (`EURI_API_KEY`) is used for BOTH embedding and LLM calls
- **Single base URL**: `https://api.euron.one/api/v1/euri` for everything
- Use the **OpenAI Python SDK** (`openai` package) — Euri is OpenAI-compatible
- Do NOT import or use `google-genai`, `google-generativeai`, or any Google SDK
- Do NOT use OpenAI's default endpoint — always override `base_url`

---

## Gemini Embedding 2 Preview — Capabilities & Constraints

All embedding calls go through the Euri endpoint. Respect these hard limits:

| Modality | Constraint |
|----------|-----------|
| **Text** | Up to **8,192 input tokens** per request |
| **Images** | Up to **6 images per request**; formats: **PNG, JPEG** only |
| **Video** | Up to **120 seconds**; formats: **MP4, MOV** only |
| **Audio** | Native audio ingestion — **no intermediate transcription needed** |
| **PDF** | Up to **6 pages** per request |

### Embedding Rules
- The embedding model produces **768-dimensional** vectors. Every Pinecone index MUST be configured with `dimension=768`
- Use `task_type` parameter: `RETRIEVAL_DOCUMENT` for indexing, `RETRIEVAL_QUERY` for search (10-15% precision improvement)
- For text longer than 8,192 tokens, implement **chunking** before embedding. Use `RecursiveCharacterTextSplitter` with `chunk_size=1024` tokens and `chunk_overlap=256` tokens
- For PDFs longer than 6 pages, split into batches of 6 pages each before embedding
- For videos longer than 120 seconds, segment into clips of 120 seconds or less before embedding
- For image batches larger than 6, split into groups of 6
- Audio is embedded natively — do NOT transcribe audio to text before embedding

---

## Pinecone — Vector Database Rules

- Use the **Pinecone Python client** (`pinecone` package, latest version)
- Connection via `PINECONE_API_KEY` env var
- Index dimension: **768** (must match Gemini Embedding 2 output)
- Metric: **cosine**
- Use **serverless** spec when creating indexes
- Store rich metadata with each vector:
  - `source_type`: one of `text`, `pdf`, `image`, `audio`, `video`
  - `source_file`: original filename or identifier
  - `chunk_index`: integer position within the source
  - `content_preview`: first 200 chars of text content (for text/pdf); empty string for other modalities
  - `timestamp`: ISO 8601 ingestion timestamp
- **Namespace strategy:** use one namespace per source type (e.g., `ns_text`, `ns_pdf`, `ns_audio`, `ns_video`, `ns_image`)
- Use `upsert` in batches of **100 vectors max** per call
- For queries, retrieve `top_k=5` results by default (configurable)

---

## LLM Generation Rules

- Use the **OpenAI Python SDK** (`openai` package) pointed at Euri's base URL
- API key via `EURI_API_KEY` env var
- Default model: `gpt-4o-mini`
- System prompt must instruct the model to answer **only** based on the retrieved context. If the context is insufficient, the model must say so — no hallucination
- Temperature: `0.3` (factual, low creativity)
- Max output tokens: `2048` default
- Always pass retrieved chunks as the `context` section inside the user message
- Support **streaming responses** for the chat interface — use `stream=True` and yield chunks via SSE to the frontend

---

## Environment Variables

All secrets and config are loaded from `.env` files. **Never hardcode secrets.**

### Backend (`backend/.env`)
```
EURI_API_KEY=your_euri_api_key
EURI_BASE_URL=https://api.euron.one/api/v1/euri
EURI_EMBEDDING_MODEL=gemini-embedding-2-preview
EURI_LLM_MODEL=gpt-4o-mini
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=rag-multimodal
```

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Use `python-dotenv` for backend. The `.env` files are in `.gitignore` — never commit them.

---

## Project Structure

```
multimodal-rag/
├── CLAUDE.md                       # This file — project rules & AI coding prompt
├── README.md                       # Public-facing docs with screenshots
├── .gitignore
├── docker-compose.yml              # One-command deployment
│
├── backend/                        # Python FastAPI backend
│   ├── .env.example                # Template for env vars
│   ├── Dockerfile                  # Python 3.13 slim + ffmpeg
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point (CORS configured)
│   │   ├── config.py               # Env var loading & validation
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── euri_client.py      # Shared Euri/OpenAI client (embedding + LLM)
│   │   │   ├── embedding.py        # Embedding operations via Euri
│   │   │   ├── vectorstore.py      # Pinecone operations
│   │   │   ├── llm.py              # LLM generation via Euri (streaming)
│   │   │   ├── vision.py           # Image description via GPT-4o-mini vision
│   │   │   ├── video_vision.py     # ffmpeg frame extraction + vision descriptions
│   │   │   ├── audio_transcription.py  # Whisper transcription via Euri
│   │   │   └── rag_pipeline.py     # Orchestrates embed → store → retrieve → generate
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── text_processor.py   # Text chunking & preparation
│   │   │   ├── pdf_processor.py    # PDF page splitting & preparation
│   │   │   ├── image_processor.py  # Image → vision description → embed
│   │   │   ├── audio_processor.py  # Audio → Whisper transcription → embed
│   │   │   └── video_processor.py  # Video → frame extraction → vision → embed
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── ingest.py           # POST endpoints for ingesting each modality
│   │       └── query.py            # POST endpoint for RAG queries (SSE streaming)
│   └── tests/
│       └── __init__.py
│
├── frontend/                       # Next.js + TypeScript frontend
│   ├── .env.example                # Template for env vars
│   ├── Dockerfile                  # Node 20 alpine
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          # Root layout with sidebar
│       │   ├── page.tsx            # Redirect to /chat
│       │   ├── chat/page.tsx       # Chat interface (main page)
│       │   └── ingest/page.tsx     # Data ingestion dashboard
│       ├── components/
│       │   ├── chat/               # ChatWindow, MessageBubble, ChatInput, SourceCard, StreamingText
│       │   ├── ingest/             # FileUploader, TextInput, IngestionStatus, IngestedFiles
│       │   └── layout/             # Sidebar, Header
│       ├── lib/
│       │   ├── api.ts              # API client — calls backend endpoints
│       │   └── types.ts            # TypeScript interfaces for API payloads
│       └── hooks/
│           ├── useChat.ts          # Chat state management + streaming
│           └── useIngest.ts        # Ingestion state management + upload
│
└── docs/
    └── screenshots/               # App screenshots for README
```

---

## Frontend — Chat Interface (ChatGPT-like)

### Chat Page (`/chat`)

- **ChatGPT-style layout**: sidebar on the left, main chat area in the center
- Messages displayed as bubbles — user on the right (colored), assistant on the left (neutral)
- **Streaming responses**: assistant messages stream in token-by-token via SSE from the backend
- After each assistant response, show **source cards** below the message listing retrieved documents (file name, source type, relevance score, content preview)
- Input bar fixed at the bottom with a text input and send button
- Support **Enter** to send, **Shift+Enter** for newline
- Optional: source type filter dropdown in the input bar (filter by text/pdf/image/audio/video or "all")
- Show a typing indicator while waiting for the stream to start
- Chat history persists within the session (client-side state, no database needed)

### Ingestion Page (`/ingest`)

- **Drag-and-drop file upload** area that accepts: `.txt`, `.pdf`, `.png`, `.jpg`, `.jpeg`, `.mp3`, `.wav`, `.mp4`, `.mov`
- Auto-detect modality from file extension and route to the correct backend endpoint
- Show **upload progress** per file
- After upload, show **ingestion status** (processing, success, error) for each file
- **Text input section**: a textarea for pasting raw text with a submit button
- **Ingested files list**: shows previously ingested files with their type, name, and timestamp

### UI/UX Rules
- Use **Tailwind CSS** for all styling — no CSS modules or styled-components
- **Dark theme by default** (similar to ChatGPT's dark mode)
- Responsive — must work on desktop and tablet
- Use `fetch` with `ReadableStream` for SSE streaming — no external libraries for this
- All API calls go through `src/lib/api.ts` — never call `fetch` directly from components
- Loading states and error states for every async operation

---

## Backend API Endpoints

### Ingestion

| Method | Path | Description | Accepts |
|--------|------|------------|---------|
| POST | `/ingest/text` | Ingest raw text | JSON body with `text` |
| POST | `/ingest/pdf` | Ingest a PDF file | Multipart file upload |
| POST | `/ingest/image` | Ingest image(s) | Multipart file upload(s) |
| POST | `/ingest/audio` | Ingest an audio file | Multipart file upload |
| POST | `/ingest/video` | Ingest a video file | Multipart file upload |

### Query

| Method | Path | Description | Accepts |
|--------|------|------------|---------|
| POST | `/query` | Ask a question (JSON response) | JSON body with `question`, optional `source_type` filter, optional `top_k` |
| POST | `/query/stream` | Ask a question (SSE streaming) | Same as `/query`, returns `text/event-stream` |

### Utility

| Method | Path | Description |
|--------|------|------------|
| GET | `/health` | Health check |
| GET | `/ingested` | List all ingested files with metadata |

### CORS
Backend must enable CORS for `http://localhost:3000` (Next.js dev server) and any configured production origin.

---

## Streaming Implementation

### Backend (FastAPI SSE)

```python
from fastapi.responses import StreamingResponse

async def generate_stream():
    # ... get context from Pinecone ...
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        if chunk.choices[0].delta.content:
            yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"
    yield f"data: {json.dumps({'sources': sources})}\n\n"
    yield "data: [DONE]\n\n"

return StreamingResponse(generate_stream(), media_type="text/event-stream")
```

### Frontend (SSE Consumer)

```typescript
const response = await fetch(`${API_URL}/query/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question, source_type, top_k }),
});

const reader = response.body!.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const text = decoder.decode(value);
  // Parse SSE events and update state
}
```

---

## RAG Pipeline Flow

```
User sends message in Chat UI
    |
    v
[1] Frontend sends POST to /query/stream
    |
    v
[2] Backend embeds query via Euri (model=gemini-embedding-2-preview, dimensions=768)
    |
    v
[3] Search Pinecone (cosine similarity, top_k=5)
    |
    v
[4] Retrieve matched chunks + metadata
    |
    v
[5] Build prompt: system instruction + retrieved context + user question
    |
    v
[6] Call Euri LLM (model=gpt-4o-mini, stream=True)
    |
    v
[7] Stream tokens back to frontend via SSE
    |
    v
[8] After stream ends, send source references
    |
    v
[9] Frontend displays answer + source cards
```

---

## Ingestion Pipeline

```
Document Upload (any modality)
    |
    v
Auto-detect modality from file extension
    |
    v
Route to appropriate processor:
    +-- Text  -> RecursiveCharacterTextSplitter (chunk_size=1024, overlap=256)
    +-- PDF   -> Page extraction + chunking
    +-- Image -> GPT-4o-mini vision description -> text embedding
    +-- Audio -> Whisper transcription -> text embedding
    +-- Video -> ffmpeg frame extraction -> vision description per frame -> text embedding
    |
    v
Embed via Euri (model=gemini-embedding-2-preview, dimensions=768)
    |
    v
Upsert to Pinecone (vector + metadata, namespace per source_type)
    |
    v
Return ingestion status to frontend
```

---

## Embedding Service Implementation

The embedding service (`backend/app/services/embedding.py`) must:
- Use the **OpenAI SDK** pointed at Euri's base URL for all embedding calls
- Call `client.embeddings.create(model="gemini-embedding-2-preview", input=..., dimensions=768)`
- For non-text modalities (images, audio, video, PDF), convert file content to **base64** and pass via the API
- Handle rate limiting with exponential backoff (max 3 retries, use `tenacity`)
- Return a list of `float` vectors (length 768)
- All modalities use the **same** model and endpoint — no separate clients

---

## Engineering Rules

### Backend (Python/FastAPI)
1. **Type hints everywhere** — all functions must have full type annotations
2. **Pydantic models** for all request/response schemas
3. **Async by default** — all I/O-bound operations must be `async`
4. **Error handling** — wrap all external API calls in try/except. Use FastAPI's `HTTPException`
5. **Logging** — use Python's `logging` module. Include modality and file name in log messages
6. **No hardcoded values** — all configurable values come from `config.py`
7. **Input validation** — validate file types, sizes, and counts before processing
8. **Dependency injection** — use FastAPI's `Depends()`

### Frontend (TypeScript/Next.js)
1. **Strict TypeScript** — no `any` types. Define interfaces for all API payloads in `types.ts`
2. **React Server Components** where possible — use `"use client"` only when needed (interactivity, hooks)
3. **Custom hooks** for state management — `useChat` and `useIngest`
4. **No external state library** — use React's built-in `useState`/`useReducer`
5. **Error boundaries** — wrap pages in error boundaries
6. **Accessible** — proper ARIA labels, keyboard navigation, focus management
7. All API calls go through `src/lib/api.ts` — never call `fetch` directly from components
8. **Dark theme by default** — ChatGPT-style dark mode

### RAG System
- **Separate** ingestion from retrieval from generation — distinct pipelines
- **Chunk metadata is mandatory** — source_type, source_file, chunk_index, content_preview, timestamp
- **No hallucination** — system prompt enforces answer ONLY from retrieved context
- **Citation in every answer** — reference source file and chunk
- **No-context handling** — "I don't have enough information to answer that."
- **Streaming required** — SSE for chat responses

### Security
- No hardcoded secrets. All from `.env`
- Validate and sanitize ALL user inputs (especially file uploads)
- Prompt injection resistance on every LLM call
- Rate limiting on embedding and LLM endpoints
- File upload validation: type, size limits
- CORS configured for allowed origins only

### Testing
- Use `pytest` with `pytest-asyncio` for backend async tests
- Mock Euri API calls in unit tests
- Test each processor independently with sample files
- Test the full RAG pipeline end-to-end with a small set of test data
- Keep test files small (tiny PDFs, short audio clips, small images)

---

## Dependencies

### Backend (`backend/requirements.txt`)

```
fastapi>=0.115.0
uvicorn>=0.34.0
python-dotenv>=1.1.0
openai>=1.68.0
pinecone>=6.0.0
pydantic>=2.10.0
python-multipart>=0.0.20
PyPDF2>=3.0.0
Pillow>=11.0.0
pytest>=8.3.0
pytest-asyncio>=0.25.0
httpx>=0.28.0
tenacity>=9.0.0
sse-starlette>=2.2.0
langchain-text-splitters>=0.3.0
```

### Frontend (`frontend/package.json` key deps)
```
next >= 15
react >= 19
typescript >= 5
tailwindcss >= 4
```

---

## Running the Project

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev    # runs on http://localhost:3000
```

### Docker
```bash
cp backend/.env.example backend/.env    # Add your API keys
cp frontend/.env.example frontend/.env.local
docker compose up --build
```

---

## Build Order

1. `app/config.py` — Env var loading & validation (EURI_API_KEY, PINECONE_API_KEY, etc.)
2. `app/services/euri_client.py` — Shared OpenAI client pointed at Euri base URL
3. `app/services/embedding.py` — Embedding via Euri (gemini-embedding-2-preview, 768 dims)
4. `app/services/vectorstore.py` — Pinecone upsert/query/delete with namespace strategy
5. `app/services/llm.py` — LLM generation via Euri (gpt-4o-mini, streaming)
6. `app/services/vision.py` — Image description via GPT-4o-mini vision
7. `app/services/video_vision.py` — ffmpeg frame extraction + vision descriptions
8. `app/services/audio_transcription.py` — Whisper transcription via Euri
9. `app/processors/text_processor.py` — Text chunking (1024 size, 256 overlap)
10. `app/processors/pdf_processor.py` — PDF page splitting
11. `app/processors/image_processor.py` — Image → vision description → embed
12. `app/processors/audio_processor.py` — Audio → Whisper transcription → embed
13. `app/processors/video_processor.py` — Video → frame extraction → vision → embed
14. `app/services/rag_pipeline.py` — Orchestrate embed → store → retrieve → generate
15. `app/models/schemas.py` — Pydantic request/response models
16. `app/routers/ingest.py` — Ingestion endpoints (text, pdf, image, audio, video)
17. `app/routers/query.py` — Query endpoints (JSON + SSE streaming)
18. `app/main.py` — FastAPI app with CORS, routers, health check
19. Frontend: layout, sidebar, chat page, ingest page
20. Frontend: ChatWindow, MessageBubble, ChatInput, StreamingText, SourceCard
21. Frontend: FileUploader, TextInput, IngestionStatus, IngestedFiles
22. Frontend: api.ts, types.ts, useChat.ts, useIngest.ts
23. Tests — unit + integration

---

## Key Reminders

- **Euri is the sole API provider** — both embedding (`gemini-embedding-2-preview`) and LLM (`gpt-4o-mini`) use `https://api.euron.one/api/v1/euri` via the OpenAI SDK. Do NOT use Google SDK or OpenAI's default endpoint
- **Single API key** — `EURI_API_KEY` is used for everything
- **768 dimensions** — this is non-negotiable for the Pinecone index
- **Audio goes directly to the embedding model** — no speech-to-text step
- **Streaming is required** for the chat interface — use SSE
- **Dark theme** — the chat UI must default to a dark theme like ChatGPT
- **Never commit `.env`** — always use environment variables
- **Namespace per source type** — `ns_text`, `ns_pdf`, `ns_audio`, `ns_video`, `ns_image`
- **Upsert batches of 100 max** — Pinecone batch limit
- **top_k=5 default** — configurable per query
