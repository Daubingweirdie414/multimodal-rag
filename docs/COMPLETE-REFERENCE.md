# Multimodal RAG System — Complete Technical Reference

> Exhaustive reference covering every file, function, component, API, data flow, and integration.
> Any AI or developer reading ONLY this document can fully understand the entire system.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Flow Diagrams](#2-data-flow-diagrams)
3. [Tech Stack](#3-tech-stack)
4. [Directory Structure](#4-directory-structure)
5. [Pages & Routes](#5-pages--routes)
6. [API Routes](#6-api-routes)
7. [Components](#7-components)
8. [Libraries & Utilities](#8-libraries--utilities)
9. [Database Schema (Vector Store)](#9-database-schema-vector-store)
10. [Background Jobs / Workers / Workflows](#10-background-jobs--workers--workflows)
11. [AI/ML System](#11-aiml-system)
12. [Authentication & Authorization](#12-authentication--authorization)
13. [Channels / Communication](#13-channels--communication)
14. [External Integrations](#14-external-integrations)
15. [Deployment & Infrastructure](#15-deployment--infrastructure)
16. [Pricing & Billing](#16-pricing--billing)
17. [Environment Variables](#17-environment-variables)
18. [Developer Quickstart](#18-developer-quickstart)

---

## 1. Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 15)                         │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │  /chat page   │  │ /ingest page │  │  / (redirect) │                │
│  │  ChatWindow   │  │ FileUploader │  │   → /chat     │                │
│  │  ChatInput    │  │ TextInput    │  └──────────────┘                 │
│  │  MessageBubble│  │ IngestionStat│                                    │
│  │  SourceCard   │  │ IngestedFiles│                                    │
│  │  StreamingText│  └──────────────┘                                    │
│  └──────┬───────┘         │                                             │
│         │                 │   (Next.js rewrites /api/* → backend:8000)  │
└─────────┼─────────────────┼─────────────────────────────────────────────┘
          │ SSE stream      │ Multipart upload / JSON
          ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI, Python 3.11+)                   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                         ROUTERS                              │       │
│  │  ingest.py: POST /ingest/{text|pdf|image|audio|video}       │       │
│  │  query.py:  POST /query, POST /query/stream                 │       │
│  │  main.py:   GET /health, GET /ingested                      │       │
│  └──────────┬──────────────────────────────┬────────────────────┘       │
│             │                              │                            │
│  ┌──────────▼──────────┐      ┌────────────▼────────────────┐          │
│  │     PROCESSORS      │      │      RAG PIPELINE           │          │
│  │  text_processor.py  │      │  rag_pipeline.py            │          │
│  │  pdf_processor.py   │      │  1. embed_text(question)    │          │
│  │  image_processor.py │      │  2. query_vectors(pinecone) │          │
│  │  audio_processor.py │      │  3. build_context(matches)  │          │
│  │  video_processor.py │      │  4. generate_stream(llm)    │          │
│  └──────────┬──────────┘      └──────────┬──────────────────┘          │
│             │                            │                              │
│  ┌──────────▼────────────────────────────▼──────────────────┐          │
│  │                       SERVICES                            │          │
│  │  euri_client.py  → Shared OpenAI client (Euri base_url)  │          │
│  │  embedding.py    → embed_text, embed_texts, embed_base64 │          │
│  │  vectorstore.py  → upsert_vectors, query_vectors, delete │          │
│  │  llm.py          → generate, generate_stream (SSE)       │          │
│  └──────────┬───────────────────────────┬───────────────────┘          │
└─────────────┼───────────────────────────┼──────────────────────────────┘
              │                           │
              ▼                           ▼
┌─────────────────────┐     ┌─────────────────────────┐
│    EURI API          │     │      PINECONE            │
│  api.euron.one       │     │  Serverless              │
│  /api/v1/euri        │     │  Index: rag-multimodal   │
│                      │     │  Dim: 768, Metric: cos   │
│  Models:             │     │  5 Namespaces:           │
│  - gemini-embed-2    │     │  ns_text, ns_pdf,        │
│    (embedding)       │     │  ns_image, ns_audio,     │
│  - gpt-4o-mini       │     │  ns_video                │
│    (generation)      │     │                           │
└──────────────────────┘     └───────────────────────────┘
```

### Layers

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Presentation** | React UI, user interaction, SSE consumption | `frontend/src/` |
| **API Gateway** | Next.js rewrites proxy `/api/*` → FastAPI | `frontend/next.config.ts` |
| **Routing** | FastAPI endpoint definitions, request validation | `backend/app/routers/` |
| **Processing** | Modality-specific data prep (chunk, split, validate) | `backend/app/processors/` |
| **Services** | Business logic: embedding, vector ops, LLM, RAG | `backend/app/services/` |
| **External** | Euri API (OpenAI-compatible), Pinecone cloud | Remote services |

---

## 2. Data Flow Diagrams

### Flow 1: RAG Query (Chat)

```
User types question in ChatInput
        │
        ▼
useChat.sendMessage(question, sourceType?, topK?)
        │
        ▼
api.ts → queryStream() → POST /api/query/stream
        │
        ▼  (Next.js rewrite)
FastAPI: query.py → query_stream_endpoint()
        │
        ▼
rag_pipeline.query_stream(question, source_type, top_k)
        │
        ├──[1]── embedding.embed_text(question)
        │            │
        │            ▼
        │        Euri API: POST /api/v1/euri/embeddings
        │        model=gemini-embedding-2-preview, dimensions=768
        │            │
        │            ▼
        │        Returns: list[float] (768 dims)
        │
        ├──[2]── vectorstore.query_vectors(vector, top_k, source_type)
        │            │
        │            ▼
        │        Pinecone: query(vector, top_k, namespace, include_metadata)
        │        If source_type given → search that namespace only
        │        Else → search ALL 5 namespaces, merge, sort by score, take top_k
        │            │
        │            ▼
        │        Returns: list[{id, score, metadata}]
        │
        ├──[3]── _build_context(matches)
        │            │
        │            ▼
        │        For each match: extract content_preview, source_file, source_type
        │        Build context string: "[Source 1: file.pdf]\npreview text"
        │        Build SourceReference objects for frontend
        │
        ├──[4]── llm.generate_stream(context, question)
        │            │
        │            ▼
        │        Euri API: POST /api/v1/euri/chat/completions
        │        model=gpt-4o-mini, stream=True, temp=0.3, max_tokens=2048
        │        System prompt: answer ONLY from context, cite sources
        │            │
        │            ▼
        │        Yields SSE chunks: data: {"content": "token"}\n\n
        │
        └──[5]── After stream ends:
                     yield data: {"sources": [SourceReference, ...]}\n\n
                     (no data: [DONE] — that comes from llm.generate_stream)
        │
        ▼
FastAPI StreamingResponse(media_type="text/event-stream")
        │
        ▼
Frontend: useChat reads stream via ReadableStream
  - "content" events → append to assistant message
  - "sources" event → attach to assistant message
  - "[DONE]" → mark streaming complete
        │
        ▼
MessageBubble renders answer + SourceCards below
```

### Flow 2: Document Ingestion (File Upload)

```
User drops file on FileUploader (or clicks browse)
        │
        ▼
useIngest.uploadFiles(files)
  → detectSourceType(filename) from extension
  → Creates IngestionJob {id, filename, sourceType, status: "uploading"}
        │
        ▼
api.ts → ingestFile(file, sourceType)
  → FormData with file → POST /api/ingest/{sourceType}
        │
        ▼  (Next.js rewrite)
FastAPI: ingest.py → ingest_{text|pdf|image|audio|video}()
  → Validates file extension
  → Reads file bytes: await file.read()
        │
        ▼
Processor (varies by modality):
  ┌─ TEXT: text_processor.process_text(text, filename)
  │    1. RecursiveCharacterTextSplitter(chunk_size=1024, overlap=256)
  │    2. embedding.embed_texts(chunks) → batch embed all chunks
  │    3. Build vector dicts: {id: uuid, values: [768 floats], metadata: {...}}
  │
  ├─ PDF: pdf_processor.process_pdf(bytes, filename)
  │    1. PdfReader → extract text from all pages
  │    2. Combine text → RecursiveCharacterTextSplitter
  │    3. embedding.embed_texts(chunks)
  │    4. Build vector dicts with total_pages in metadata
  │
  ├─ IMAGE: image_processor.process_image(bytes, filename)
  │    1. Validate extension (.png, .jpg, .jpeg)
  │    2. base64.b64encode(bytes)
  │    3. embedding.embed_base64(b64) → single 768-dim vector
  │    4. metadata: content_preview="" (no text for images)
  │
  ├─ AUDIO: audio_processor.process_audio(bytes, filename)
  │    1. Validate extension (.mp3, .wav)
  │    2. base64.b64encode(bytes) — NO transcription
  │    3. embedding.embed_base64(b64)
  │    4. metadata: content_preview=""
  │
  └─ VIDEO: video_processor.process_video(bytes, filename)
       1. Validate extension (.mp4, .mov)
       2. base64.b64encode(bytes) — native embedding
       3. embedding.embed_base64(b64)
       4. metadata: content_preview=""
        │
        ▼
vectorstore.upsert_vectors(vectors, source_type)
  → Namespace: NAMESPACE_MAP[source_type] (e.g., "ns_pdf")
  → Enriches metadata: adds source_type + timestamp (ISO 8601)
  → Batches of 100 vectors max per Pinecone upsert call
        │
        ▼
Returns IngestResponse: {status, source_type, source_file, chunks_ingested, message}
        │
        ▼
Frontend: useIngest updates job status → "success"
  → IngestionStatus shows green badge
  → IngestedFiles table adds row
```

### Flow 3: Text Ingestion (Paste)

```
User types text in TextInput → clicks "Ingest Text"
        │
        ▼
useIngest.submitText(text)
  → Creates IngestionJob {filename: "raw_text", sourceType: "text", status: "processing"}
        │
        ▼
api.ts → ingestText(text)
  → POST /api/ingest/text with JSON body: {text: "..."}
        │
        ▼
ingest.py → ingest_text(TextIngestRequest)
  → process_text(request.text, source_file="raw_text")
  → upsert_vectors(vectors, source_type="text")
  → Returns IngestResponse
```

---

## 3. Tech Stack

| Component | Technology | Version | Why |
|-----------|-----------|---------|-----|
| **Frontend framework** | Next.js (App Router) | ^15.2.0 | Server Components, file-based routing, API rewrites |
| **UI library** | React | ^19.0.0 | Component model, hooks |
| **Language (FE)** | TypeScript | ^5.7.0 | Type safety, no `any` |
| **Styling** | Tailwind CSS | ^4.0.0 | Utility-first, dark theme |
| **Build tool** | Turbopack | built-in | Fast HMR via `next dev --turbopack` |
| **Backend framework** | FastAPI | >=0.115.0 | Async Python, auto-docs, Pydantic |
| **ASGI server** | Uvicorn | >=0.34.0 | Production ASGI server |
| **Language (BE)** | Python | 3.11+ | Type hints, dataclasses |
| **Embedding model** | Gemini Embedding 2 Preview | via Euri | Natively multimodal (text+image+audio+video+PDF), 768-dim |
| **LLM** | GPT-4o-mini | via Euri | Cost-effective generation, good RAG citation quality |
| **API provider** | Euri | api.euron.one | OpenAI SDK-compatible wrapper for both embedding + LLM |
| **OpenAI SDK** | openai (Python) | >=1.68.0 | Client for Euri API (custom base_url) |
| **Vector database** | Pinecone Serverless | >=6.0.0 | Managed, zero-ops, cosine similarity, namespace isolation |
| **PDF parsing** | PyPDF2 | >=3.0.0 | Text extraction from PDF pages |
| **Image validation** | Pillow | >=11.0.0 | Image format validation |
| **Text chunking** | langchain-text-splitters | >=0.3.0 | RecursiveCharacterTextSplitter |
| **Retry logic** | tenacity | >=9.0.0 | Exponential backoff on API failures |
| **SSE (backend)** | sse-starlette | >=2.2.0 | Server-Sent Events for FastAPI |
| **Validation** | Pydantic | >=2.10.0 | Request/response models |
| **File uploads** | python-multipart | >=0.0.20 | Multipart form data parsing |
| **Env vars** | python-dotenv | >=1.1.0 | Load .env files |
| **Testing** | pytest + pytest-asyncio | >=8.3.0, >=0.25.0 | Async test support |
| **HTTP client (test)** | httpx | >=0.28.0 | Async HTTP for test client |
| **Font** | Inter (Google Fonts) | — | Clean sans-serif, loaded via `next/font` |

---

## 4. Directory Structure

```
Multimodal-RAG-System/
├── CLAUDE.md                           # Project rules & instructions
├── .gitignore                          # Ignore .env, __pycache__, node_modules, .next
├── .env.example                        # Template for backend env vars
│
├── backend/                            # Python FastAPI backend
│   ├── .env                            # Secrets (git-ignored)
│   ├── requirements.txt                # 15 Python dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI app, CORS, routers, /health, /ingested
│   │   ├── config.py                   # Settings dataclass, env var loading
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── schemas.py              # 7 Pydantic models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── euri_client.py          # Singleton OpenAI client → Euri
│   │   │   ├── embedding.py            # embed_text, embed_texts, embed_base64, embed_file
│   │   │   ├── vectorstore.py          # upsert_vectors, query_vectors, delete_vectors
│   │   │   ├── llm.py                  # generate, generate_stream (SSE)
│   │   │   └── rag_pipeline.py         # query, query_stream (full RAG orchestration)
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   ├── text_processor.py       # Text chunking (1024/256)
│   │   │   ├── pdf_processor.py        # PDF text extraction + chunking
│   │   │   ├── image_processor.py      # Image validation + base64 embedding
│   │   │   ├── audio_processor.py      # Audio validation + native embedding
│   │   │   └── video_processor.py      # Video validation + native embedding
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── ingest.py               # 5 POST endpoints (text, pdf, image, audio, video)
│   │       └── query.py                # 2 POST endpoints (query, query/stream)
│   └── tests/
│       └── __init__.py                 # Test stubs (not yet implemented)
│
├── frontend/                           # Next.js 15 + TypeScript frontend
│   ├── .env.local                      # NEXT_PUBLIC_API_URL (git-ignored)
│   ├── package.json                    # 3 deps + 6 devDeps
│   ├── tsconfig.json                   # TypeScript config
│   ├── next.config.ts                  # API rewrites (/api/* → backend)
│   ├── postcss.config.mjs              # PostCSS with Tailwind
│   ├── next-env.d.ts                   # Next.js type declarations
│   └── src/
│       ├── app/
│       │   ├── globals.css             # Tailwind import + scrollbar + blink animation
│       │   ├── layout.tsx              # Root layout: dark theme, Inter font, Sidebar
│       │   ├── page.tsx                # Root redirect → /chat
│       │   ├── chat/
│       │   │   └── page.tsx            # Chat page (useChat hook)
│       │   └── ingest/
│       │       └── page.tsx            # Ingest page (useIngest hook)
│       ├── components/
│       │   ├── chat/
│       │   │   ├── ChatWindow.tsx      # Main chat container + EmptyState
│       │   │   ├── ChatInput.tsx       # Textarea + source filter + send button
│       │   │   ├── MessageBubble.tsx   # User/assistant message with sources
│       │   │   ├── SourceCard.tsx      # Source reference card (color-coded by type)
│       │   │   └── StreamingText.tsx   # Text with blinking cursor during stream
│       │   ├── ingest/
│       │   │   ├── FileUploader.tsx    # Drag-and-drop file upload
│       │   │   ├── TextInput.tsx       # Textarea for raw text ingestion
│       │   │   ├── IngestionStatus.tsx # Job status list (uploading/processing/success/error)
│       │   │   └── IngestedFiles.tsx   # Table of successfully ingested files
│       │   └── layout/
│       │       ├── Sidebar.tsx         # Left nav: Chat, Ingest links + logo
│       │       └── Header.tsx          # Top bar: title + action buttons
│       ├── hooks/
│       │   ├── useChat.ts             # Chat state + SSE stream reading
│       │   └── useIngest.ts           # Ingestion state + file upload orchestration
│       └── lib/
│           ├── api.ts                  # API client: query, queryStream, ingestText, ingestFile, healthCheck, detectSourceType
│           └── types.ts                # 8 TypeScript interfaces
│
├── context/                            # Reference documentation
│   ├── CLASS-NOTES.md                  # Euron AI Architect Mastery Class 3 notes
│   ├── FINAI-REFERENCE.md             # FinAI project reference (same architecture)
│   └── RAG-DECISIONS.md               # 6 architecture decisions with trade-offs
│
└── docs/                               # Project documentation
    └── COMPLETE-REFERENCE.md           # This file
```

---

## 5. Pages & Routes

### Frontend Pages

| Route | File | Purpose | Key Components | Client/Server |
|-------|------|---------|---------------|---------------|
| `/` | `src/app/page.tsx` | Redirect to `/chat` | — | Server (redirect) |
| `/chat` | `src/app/chat/page.tsx` | Main chat interface | `Header`, `ChatWindow` (→ `MessageBubble`, `ChatInput`, `StreamingText`, `SourceCard`) | Client (`"use client"`) |
| `/ingest` | `src/app/ingest/page.tsx` | Data ingestion dashboard | `Header`, `FileUploader`, `TextInput`, `IngestionStatus`, `IngestedFiles` | Client (`"use client"`) |

### Root Layout

| File | Purpose |
|------|---------|
| `src/app/layout.tsx` | Wraps all pages. Sets dark theme (`className="dark"`), Inter font, `bg-zinc-950`, includes `<Sidebar />` on the left. |
| `src/app/globals.css` | Imports Tailwind, custom scrollbar styles (dark), `.animate-blink` keyframe for streaming cursor. |

---

## 6. API Routes

### Backend Endpoints (FastAPI)

#### Ingestion Group (prefix: `/ingest`)

| Method | Path | Handler | Request | Response | Description |
|--------|------|---------|---------|----------|-------------|
| POST | `/ingest/text` | `ingest_text` | JSON: `{"text": "..."}` (`TextIngestRequest`) | `IngestResponse` | Chunks text (1024/256), embeds, upserts to `ns_text` |
| POST | `/ingest/pdf` | `ingest_pdf` | Multipart: `file` (.pdf) | `IngestResponse` | Extracts text from all pages, chunks, embeds, upserts to `ns_pdf` |
| POST | `/ingest/image` | `ingest_image` | Multipart: `file` (.png/.jpg/.jpeg) | `IngestResponse` | Base64-encodes, embeds natively, upserts to `ns_image` |
| POST | `/ingest/audio` | `ingest_audio` | Multipart: `file` (.mp3/.wav) | `IngestResponse` | Base64-encodes, embeds natively (NO transcription), upserts to `ns_audio` |
| POST | `/ingest/video` | `ingest_video` | Multipart: `file` (.mp4/.mov) | `IngestResponse` | Base64-encodes, embeds natively, upserts to `ns_video` |

#### Query Group

| Method | Path | Handler | Request | Response | Description |
|--------|------|---------|---------|----------|-------------|
| POST | `/query` | `query_endpoint` | JSON: `{"question": "...", "source_type?": "...", "top_k?": 5}` (`QueryRequest`) | `QueryResponse` | Full RAG: embed → retrieve → generate (non-streaming) |
| POST | `/query/stream` | `query_stream_endpoint` | JSON: same as `/query` | `text/event-stream` (SSE) | Full RAG with streaming. Events: `{"content": "token"}`, `{"sources": [...]}`, `[DONE]` |

#### Utility

| Method | Path | Handler | Response | Description |
|--------|------|---------|----------|-------------|
| GET | `/health` | `health_check` | `{"status": "ok", "message": "..."}` | Health check |
| GET | `/ingested` | `list_ingested` | `{"files": [], "message": "..."}` | Placeholder — returns empty list (no metadata store yet) |

### Request/Response Schemas (Pydantic)

| Schema | Fields | Used By |
|--------|--------|---------|
| `TextIngestRequest` | `text: str` (min_length=1) | POST `/ingest/text` |
| `IngestResponse` | `status, source_type, source_file, chunks_ingested, message` | All `/ingest/*` responses |
| `QueryRequest` | `question: str`, `source_type?: str`, `top_k?: int` (1-20, default 5) | POST `/query`, `/query/stream` |
| `QueryResponse` | `answer: str`, `sources: list[SourceReference]` | POST `/query` |
| `SourceReference` | `source_type, source_file, chunk_index, content_preview, score` | Embedded in QueryResponse and SSE |
| `IngestedFileInfo` | `source_type, source_file, chunk_count, timestamp` | Future: GET `/ingested` |
| `HealthResponse` | `status: str`, `message: str` | GET `/health` |

### CORS Configuration

- Origins: loaded from `CORS_ORIGINS` env var (default: `http://localhost:3000`)
- Methods: `["*"]`
- Headers: `["*"]`
- Credentials: `True`

### API Proxy (Next.js Rewrites)

Frontend calls `/api/*` which Next.js rewrites to `BACKEND_URL/*`:

```typescript
// next.config.ts
rewrites: [{ source: "/api/:path*", destination: "http://localhost:8000/:path*" }]
```

This eliminates CORS issues in development since the browser sees same-origin requests.

---

## 7. Components

### Chat Components (`src/components/chat/`)

| Component | File | Props | Purpose |
|-----------|------|-------|---------|
| `ChatWindow` | `ChatWindow.tsx` | `messages: ChatMessage[]`, `isLoading: boolean`, `onSend: fn` | Main chat container. Renders messages list or EmptyState. Auto-scrolls on new messages. Contains `ChatInput` at bottom. |
| `ChatInput` | `ChatInput.tsx` | `onSend: fn`, `disabled?: boolean` | Textarea with auto-resize (max 160px), source type filter dropdown (All/Text/PDF/Image/Audio/Video), send button. Enter=send, Shift+Enter=newline. |
| `MessageBubble` | `MessageBubble.tsx` | `message: ChatMessage` | Renders single message. User=right/indigo, Assistant=left/zinc. Shows role label, content (via `StreamingText` for assistant), and `SourceCard` list below. |
| `SourceCard` | `SourceCard.tsx` | `source: SourceReference`, `index: number` | Color-coded by type (text=emerald, pdf=red, image=purple, audio=amber, video=blue). Shows type badge, filename, match % score, content preview (if text/pdf). |
| `StreamingText` | `StreamingText.tsx` | `content: string`, `isStreaming: boolean` | Renders text with blinking cursor animation while `isStreaming=true`. |
| `EmptyState` | (inside `ChatWindow.tsx`) | — | Centered icon + title + description shown when no messages. |

### Ingest Components (`src/components/ingest/`)

| Component | File | Props | Purpose |
|-----------|------|-------|---------|
| `FileUploader` | `FileUploader.tsx` | `onFilesSelected: fn`, `disabled?: boolean` | Drag-and-drop zone with hidden file input. Accepts: `.txt,.pdf,.png,.jpg,.jpeg,.mp3,.wav,.mp4,.mov`. Visual feedback on drag hover (indigo border). |
| `TextInput` | `TextInput.tsx` | `onSubmit: fn`, `disabled?: boolean` | Textarea (5 rows) + "Ingest Text" button for raw text paste. |
| `IngestionStatus` | `IngestionStatus.tsx` | `jobs: IngestionJob[]` | Shows all ingestion jobs with status badges: uploading (blue), processing (amber+pulse), success (emerald), error (red). Type icon: T/P/I/A/V. |
| `IngestedFiles` | `IngestedFiles.tsx` | `jobs: IngestionJob[]` | Table of successfully ingested files. Columns: File, Type (badge), Chunks count. Filters to `status === "success"` only. |

### Layout Components (`src/components/layout/`)

| Component | File | Props | Purpose |
|-----------|------|-------|---------|
| `Sidebar` | `Sidebar.tsx` | — | 240px left sidebar. Logo ("R" in indigo square + "Multimodal RAG"). Nav links: Chat, Ingest (with inline SVG icons). Active state highlighting. Footer: "Euron AI Architect Mastery". |
| `Header` | `Header.tsx` | `title: string`, `actions?: ReactNode` | 56px top bar with title and optional action buttons (e.g., "Clear Chat", "Clear History"). Glassmorphic blur background. |

---

## 8. Libraries & Utilities

### Frontend: `src/lib/api.ts`

| Export | Type | Purpose |
|--------|------|---------|
| `query(req)` | `async (QueryRequest) → QueryResponse` | Non-streaming RAG query via POST `/api/query` |
| `queryStream(req)` | `async (QueryRequest) → Response` | Streaming RAG query via POST `/api/query/stream`. Returns raw Response for ReadableStream consumption. |
| `ingestText(text)` | `async (string) → IngestResponse` | POST `/api/ingest/text` with JSON body |
| `ingestFile(file, sourceType)` | `async (File, SourceType) → IngestResponse` | POST `/api/ingest/{sourceType}` with FormData |
| `healthCheck()` | `async () → HealthResponse` | GET `/api/health` |
| `detectSourceType(filename)` | `(string) → SourceType \| null` | Maps file extension to source type. Returns null for unsupported. |
| `ACCEPTED_EXTENSIONS` | `string` | Comma-separated list of accepted extensions for file input. |

Internal: `fetchJSON<T>(path, init?)` — generic JSON fetcher with error handling. All API calls go through this (except `queryStream` which needs raw Response).

**API base URL:** `/api` (proxied via Next.js rewrites to backend).

### Frontend: `src/lib/types.ts`

| Type | Fields | Purpose |
|------|--------|---------|
| `SourceType` | `"text" \| "pdf" \| "image" \| "audio" \| "video"` | Source type union |
| `SourceReference` | `source_type, source_file, chunk_index, content_preview, score` | RAG source citation |
| `QueryResponse` | `answer, sources` | /query response |
| `QueryRequest` | `question, source_type?, top_k?` | /query request |
| `TextIngestRequest` | `text` | /ingest/text request |
| `IngestResponse` | `status, source_type, source_file, chunks_ingested, message` | Ingestion result |
| `HealthResponse` | `status, message` | Health check |
| `ChatMessage` | `id, role, content, sources?, isStreaming?` | UI chat message |
| `IngestionJob` | `id, filename, sourceType, status, progress?, message?, chunksIngested?` | UI ingestion tracking |

### Frontend: `src/hooks/useChat.ts`

| Export | Returns | Purpose |
|--------|---------|---------|
| `useChat()` | `{ messages, isLoading, sendMessage, clearMessages, stopStreaming }` | Chat state management. Handles SSE stream reading, message accumulation, error handling. |

**Key behavior:**
- `sendMessage(question, sourceType?, topK?)` — adds user msg + empty assistant msg, reads SSE stream, appends content tokens, attaches sources when received
- SSE parsing: splits on `\n`, looks for `data: ` prefix, parses JSON for `content` or `sources` events
- Error handling: sets assistant message content to `"Error: {message}"`
- `clearMessages()` — resets to empty array

### Frontend: `src/hooks/useIngest.ts`

| Export | Returns | Purpose |
|--------|---------|---------|
| `useIngest()` | `{ jobs, uploadFile, uploadFiles, submitText, clearJobs }` | Ingestion state management. Tracks upload jobs with status transitions. |

**Key behavior:**
- `uploadFiles(files)` — processes all files in parallel via `Promise.allSettled`
- `uploadFile(file)` — detects source type, creates job, calls `ingestFile`, updates status
- `submitText(text)` — creates job, calls `ingestText`, updates status
- Job status flow: `uploading → processing → success/error`

### Backend: `backend/app/config.py`

| Export | Type | Purpose |
|--------|------|---------|
| `settings` | `Settings` (frozen dataclass) | Singleton config loaded at import time. |
| `Settings` | dataclass | Fields: `euri_api_key, euri_base_url, euri_embedding_model, euri_llm_model, pinecone_api_key, pinecone_index_name, cors_origins, log_level` |
| `load_settings()` | `() → Settings` | Reads env vars, validates required ones exist. |
| `_require(key)` | `(str) → str` | Gets env var or raises `RuntimeError`. |

### Backend: `backend/app/services/euri_client.py`

| Export | Type | Purpose |
|--------|------|---------|
| `euri_client` | `OpenAI` | Singleton OpenAI client with `base_url=settings.euri_base_url` and `api_key=settings.euri_api_key`. Used by both embedding.py and llm.py. |
| `get_euri_client()` | `() → OpenAI` | Factory function (called once at module load). |

### Backend: `backend/app/services/embedding.py`

| Export | Signature | Purpose |
|--------|-----------|---------|
| `embed_text(text)` | `(str) → list[float]` | Embed single text string. Returns 768-dim vector. Retries 3x with exponential backoff. |
| `embed_texts(texts)` | `(list[str]) → list[list[float]]` | Embed multiple texts in one API call. Returns list of 768-dim vectors. |
| `embed_base64(b64)` | `(str) → list[float]` | Embed base64-encoded content (image/audio/video/PDF). |
| `embed_file(file_path)` | `(Path) → list[float]` | Read file, base64-encode, embed. |
| `EMBEDDING_DIMENSIONS` | `int = 768` | Constant for vector dimensions. |

### Backend: `backend/app/services/vectorstore.py`

| Export | Signature | Purpose |
|--------|-----------|---------|
| `upsert_vectors(vectors, source_type)` | `(list[dict], str) → int` | Upsert to Pinecone in batches of 100. Enriches metadata with `source_type` and `timestamp`. Returns count. |
| `query_vectors(query_vector, top_k, source_type)` | `(list[float], int, str\|None) → list[dict]` | Query Pinecone. If source_type given, search that namespace. Else search ALL namespaces, merge, sort by score, return top_k. |
| `delete_vectors(ids, source_type)` | `(list[str], str) → None` | Delete vectors by ID from namespace. |
| `NAMESPACE_MAP` | `dict` | `{"text": "ns_text", "pdf": "ns_pdf", "image": "ns_image", "audio": "ns_audio", "video": "ns_video"}` |
| `UPSERT_BATCH_SIZE` | `int = 100` | Max vectors per Pinecone upsert call. |
| `index` | `Pinecone.Index` | Singleton Pinecone index connection (lazy init). |

### Backend: `backend/app/services/llm.py`

| Export | Signature | Purpose |
|--------|-----------|---------|
| `generate(context, question)` | `(str, str) → str` | Non-streaming LLM call. Returns full answer string. |
| `generate_stream(context, question)` | `(str, str) → Generator[str]` | Streaming LLM call. Yields SSE-formatted chunks: `data: {"content": "token"}\n\n` and `data: [DONE]\n\n`. |
| `SYSTEM_PROMPT` | `str` | Instructs LLM to answer ONLY from context, cite sources, say "I don't have enough information" when context is insufficient. |

### Backend: `backend/app/services/rag_pipeline.py`

| Export | Signature | Purpose |
|--------|-----------|---------|
| `query(question, source_type, top_k)` | `(str, str\|None, int) → (str, list[SourceReference])` | Full RAG: embed → retrieve → generate. Returns (answer, sources). |
| `query_stream(question, source_type, top_k)` | `(str, str\|None, int) → Generator[str]` | Streaming RAG: embed → retrieve → stream. Yields SSE content chunks + sources event at end. |

### Backend: Processors

| File | Key Exports | Purpose |
|------|-------------|---------|
| `text_processor.py` | `process_text(text, source_file) → list[dict]` | Chunks text with `RecursiveCharacterTextSplitter(1024, 256)`, embeds via `embed_texts`, returns Pinecone-ready vectors. |
| `pdf_processor.py` | `process_pdf(bytes, filename) → list[dict]` | Extracts text from all PDF pages via `PdfReader`, chunks, embeds. Stores `total_pages` in metadata. |
| `image_processor.py` | `validate_image(filename) → bool`, `process_image(bytes, filename) → list[dict]`, `process_images(files) → list[dict]` | Validates .png/.jpg/.jpeg, base64-encodes, embeds. Empty `content_preview`. |
| `audio_processor.py` | `validate_audio(filename) → bool`, `process_audio(bytes, filename) → list[dict]` | Validates .mp3/.wav, base64-encodes, embeds natively (NO transcription). |
| `video_processor.py` | `validate_video(filename) → bool`, `process_video(bytes, filename) → list[dict]` | Validates .mp4/.mov, base64-encodes, embeds natively. Note: segmentation for >120s must be done before calling. |

---

## 9. Database Schema (Vector Store)

This system has **no relational database**. All persistence is in **Pinecone** (vector store).

### Pinecone Index Configuration

| Property | Value |
|----------|-------|
| **Index name** | `rag-multimodal` |
| **Dimensions** | 768 |
| **Metric** | Cosine similarity |
| **Type** | Serverless |
| **Cloud** | Configured via Pinecone dashboard |

### Namespace Strategy

| Source Type | Namespace | Description |
|------------|-----------|-------------|
| Text | `ns_text` | Raw text and text file chunks |
| PDF | `ns_pdf` | PDF page text chunks |
| Image | `ns_image` | Image embeddings (1 vector per image) |
| Audio | `ns_audio` | Audio embeddings (1 vector per file, native) |
| Video | `ns_video` | Video embeddings (1 vector per clip, native) |

### Vector Metadata Schema

Every vector stored in Pinecone has this metadata:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `source_type` | string | One of: text, pdf, image, audio, video | `"pdf"` |
| `source_file` | string | Original filename or identifier | `"report.pdf"` |
| `chunk_index` | int | Position within the source document | `3` |
| `content_preview` | string | First 200 chars of text content (empty for non-text) | `"The quarterly revenue..."` |
| `timestamp` | string (ISO 8601) | Ingestion timestamp (UTC) | `"2026-03-14T12:30:00+00:00"` |
| `total_pages` | int (PDF only) | Total pages in the source PDF | `12` |

### Vector ID Strategy

- Each vector gets a UUID v4 (`str(uuid.uuid4())`)
- IDs are unique across all namespaces
- No collision possible between different source types

### Query Behavior

- **With source_type filter:** searches only the matching namespace
- **Without filter (default):** searches ALL 5 namespaces, merges results, sorts by score descending, returns top_k
- Default `top_k = 5` (configurable 1-20)

### Batch Limits

- **Upsert:** max 100 vectors per batch (Pinecone limit)
- **Query:** single query per namespace per call

---

## 10. Background Jobs / Workers / Workflows

This system has **no background jobs, crons, or queue workers**. All operations are synchronous request-response:

| Operation | Trigger | Execution |
|-----------|---------|-----------|
| Ingestion | User uploads file or submits text | Synchronous: process → embed → upsert → respond |
| RAG query | User sends chat message | Synchronous (streaming): embed → retrieve → generate → stream SSE |

### Future Considerations

The `/ingested` endpoint currently returns an empty list. In production, options include:
1. A metadata store (Postgres/SQLite) tracking ingested files
2. Pinecone metadata queries to list all unique `source_file` values
3. A background job to periodically sync Pinecone metadata

---

## 11. AI/ML System

### Models Used

| Model | Provider | Via | Purpose | Dimensions | Cost |
|-------|----------|-----|---------|-----------|------|
| `gemini-embedding-2-preview` | Google | Euri API | Embedding (all modalities) | 768 | ~$0.20/MTok |
| `gpt-4o-mini` | OpenAI | Euri API | Answer generation | — | ~$0.15/MTok in, $0.60/MTok out |

### Embedding Architecture

```
                   ┌─────────────────────────────┐
                   │    Euri API                  │
                   │    base_url: api.euron.one   │
                   │    /api/v1/euri/embeddings   │
                   └──────────────┬──────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
   embed_text()            embed_texts()            embed_base64()
   Single string           Batch strings            Base64 content
        │                         │                         │
   Used by:                Used by:                  Used by:
   - RAG query             - text_processor          - image_processor
   - embed_file            - pdf_processor           - audio_processor
                                                     - video_processor
```

All embedding functions use `tenacity` retry with:
- Max 3 attempts
- Exponential backoff: min=1s, max=10s

### LLM Generation

**System Prompt (enforced on every call):**
```
You are a helpful assistant that answers questions based ONLY on the provided context.

Rules:
1. Answer ONLY using information from the context below. Do not use prior knowledge.
2. If the context does not contain enough information, say: "I don't have enough
   information to answer that based on the available documents."
3. Cite your sources by referencing the source file name and type when possible.
4. Be concise, accurate, and helpful.
5. If the context contains information from multiple sources, synthesize it clearly.
```

**LLM Parameters:**
- Temperature: `0.3` (factual, low creativity)
- Max tokens: `2048`
- Streaming: `True` for chat, `False` for non-streaming endpoint

### Prompt Construction

```
[System] → SYSTEM_PROMPT (above)

[User] →
  Context (retrieved from knowledge base):
  ---
  [Source 1: report.pdf]
  The quarterly revenue increased by 15%...

  ---

  [Source 2: notes.txt]
  Meeting decided to expand into new markets...
  ---

  Question: What was the revenue growth?
```

### Provider Abstraction

The Euri API is an OpenAI-compatible proxy. The entire system uses `openai.OpenAI` client with a custom `base_url`:

```python
client = OpenAI(api_key=EURI_API_KEY, base_url="https://api.euron.one/api/v1/euri")
```

To switch to direct OpenAI, change `base_url` to `https://api.openai.com/v1` and update the API key. No code changes needed.

### Modality Constraints (Gemini Embedding 2)

| Modality | Max per Request | Chunking Strategy |
|----------|----------------|-------------------|
| Text | 8,192 tokens | RecursiveCharacterTextSplitter (1024/256) |
| PDF | 6 pages | Extract text → chunk (text splitting) |
| Image | 6 images | Base64 encode, 1 vector per image |
| Audio | Native | Base64 encode, 1 vector per file |
| Video | 120 seconds | Base64 encode, 1 vector per clip |

---

## 12. Authentication & Authorization

**This system has NO authentication or authorization.**

- All endpoints are publicly accessible
- No user accounts, sessions, or API keys for consumers
- No tenant isolation — all data goes into the same Pinecone index
- CORS is the only access control (restricted to configured origins)

### API Key Security

| Key | Where Stored | Access Scope |
|-----|-------------|-------------|
| `EURI_API_KEY` | `backend/.env` | Server-side only. Never exposed to frontend. |
| `PINECONE_API_KEY` | `backend/.env` | Server-side only. Never exposed to frontend. |

The frontend communicates with the backend via Next.js rewrites. No API keys are ever sent to the browser.

---

## 13. Channels / Communication

### SSE (Server-Sent Events) — Primary Communication Channel

The streaming chat response uses SSE over HTTP:

| Direction | Protocol | Endpoint | Content-Type |
|-----------|----------|----------|-------------|
| Frontend → Backend | HTTP POST (JSON) | `/query/stream` | `application/json` |
| Backend → Frontend | SSE (chunked response) | — | `text/event-stream` |

**SSE Event Format:**

```
data: {"content": "token text"}\n\n       ← LLM token (repeated)
data: {"sources": [{...}, {...}]}\n\n     ← Source references (once, after content)
data: [DONE]\n\n                          ← Stream end signal
```

**SSE Headers:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### REST — Standard Request/Response

All non-streaming endpoints use standard REST:
- Ingestion: JSON or multipart/form-data → JSON response
- Query (non-stream): JSON → JSON
- Health: GET → JSON

---

## 14. External Integrations

### Integration 1: Euri API

| Property | Value |
|----------|-------|
| **Service** | Euri (by Euron) |
| **Base URL** | `https://api.euron.one/api/v1/euri` |
| **Protocol** | REST (OpenAI-compatible) |
| **Auth method** | Bearer token via OpenAI SDK (`api_key` parameter) |
| **Env var** | `EURI_API_KEY` |
| **Used for** | Embedding (gemini-embedding-2-preview) + LLM generation (gpt-4o-mini) |
| **SDK** | `openai` Python package with custom `base_url` |
| **Rate limiting** | Handled via `tenacity` (3 retries, exponential backoff) |

**Endpoints called:**
1. `POST /embeddings` — embedding calls (`client.embeddings.create`)
2. `POST /chat/completions` — LLM calls (`client.chat.completions.create`)

### Integration 2: Pinecone

| Property | Value |
|----------|-------|
| **Service** | Pinecone Serverless |
| **Protocol** | gRPC/REST via Python SDK |
| **Auth method** | API key via `Pinecone(api_key=...)` |
| **Env var** | `PINECONE_API_KEY` |
| **Index** | `rag-multimodal` (768 dims, cosine metric) |
| **Used for** | Vector storage, similarity search |
| **SDK** | `pinecone` Python package |

**Operations:**
1. `index.upsert(vectors, namespace)` — store vectors
2. `index.query(vector, top_k, namespace, include_metadata)` — similarity search
3. `index.delete(ids, namespace)` — remove vectors

---

## 15. Deployment & Infrastructure

### Current Setup (Development)

| Component | Host | Port | Command |
|-----------|------|------|---------|
| Backend | localhost | 8000 | `uvicorn app.main:app --reload --port 8000` |
| Frontend | localhost | 3000 | `npm run dev` (Turbopack) |

### Frontend → Backend Proxy

Next.js rewrites handle the proxy in development:
```
/api/* → http://localhost:8000/*
```
This eliminates CORS issues and keeps API keys server-side.

### Production Deployment Options

| Platform | Frontend | Backend | Notes |
|----------|----------|---------|-------|
| **Vercel + Render** | Vercel (Next.js native) | Render (Python) | Set `NEXT_PUBLIC_API_URL` to Render URL |
| **Vercel + AWS Lambda** | Vercel | Lambda via Mangum | Serverless backend |
| **Docker Compose** | Node container | Python container | Single machine deployment |

### CI/CD

Not configured. Manual deployment.

### Git Ignored Files

```
.env                # Backend secrets
__pycache__/        # Python bytecode
*.pyc
.pytest_cache/
node_modules/       # npm packages
.next/              # Next.js build output
dist/
*.egg-info/
.venv/ / venv/      # Python virtual environments
```

---

## 16. Pricing & Billing

### No User-Facing Billing

This is a course project — no pricing tiers, subscriptions, or billing system.

### Operational Costs

| Service | Pricing Model | Estimated Cost |
|---------|--------------|----------------|
| **Euri API (Embedding)** | ~$0.20/MTok | Depends on ingestion volume |
| **Euri API (LLM)** | ~$0.15/MTok input, ~$0.60/MTok output | Depends on query volume |
| **Pinecone Serverless** | $0.0025/1K queries, storage varies | Low for development |
| **Vercel** (if deployed) | Free tier (hobby) | $0 for low traffic |

### Cost Optimization

- GPT-4o-mini chosen over GPT-4o for 10x cost reduction
- 768-dim vectors (not 3072) reduce Pinecone storage
- Batch embedding (`embed_texts`) reduces API calls
- `top_k=5` limits retrieval cost

---

## 17. Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `EURI_API_KEY` | **Yes** | — | API key for Euri (used for both embedding and LLM calls) |
| `EURI_BASE_URL` | No | `https://api.euron.one/api/v1/euri` | Euri API base URL |
| `EURI_EMBEDDING_MODEL` | No | `gemini-embedding-2-preview` | Embedding model name |
| `EURI_LLM_MODEL` | No | `gpt-4o-mini` | LLM model name |
| `PINECONE_API_KEY` | **Yes** | — | Pinecone API key |
| `PINECONE_INDEX_NAME` | No | `rag-multimodal` | Pinecone index name |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `LOG_LEVEL` | No | `INFO` | Python logging level (DEBUG/INFO/WARNING/ERROR) |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000` | Backend URL for API rewrites |

### Startup Validation

Backend validates at startup via `config.py`:
- `EURI_API_KEY` — **fails fast** with `RuntimeError` if missing
- `PINECONE_API_KEY` — **fails fast** with `RuntimeError` if missing
- All other vars have sensible defaults

---

## 18. Developer Quickstart

### Prerequisites

- Python 3.11+
- Node.js 18+ / npm
- Euri API key (from euron.one)
- Pinecone API key (from pinecone.io)
- Pinecone index created: name=`rag-multimodal`, dimensions=`768`, metric=`cosine`, serverless

### Step 1: Clone & Setup Backend

```bash
cd Multimodal-RAG-System/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env — add your EURI_API_KEY and PINECONE_API_KEY

# Start backend
uvicorn app.main:app --reload --port 8000
```

Verify: `curl http://localhost:8000/health` → `{"status":"ok","message":"Multimodal RAG System is running"}`

### Step 2: Setup Frontend

```bash
cd Multimodal-RAG-System/frontend

# Install dependencies
npm install

# Configure environment (optional — defaults to localhost:8000)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend
npm run dev
```

Open: `http://localhost:3000` → redirects to `/chat`

### Step 3: Ingest Data

1. Go to `http://localhost:3000/ingest`
2. Drag & drop files (PDF, images, audio, video) or paste text
3. Watch ingestion status go from "Processing..." → "Success"

### Step 4: Query

1. Go to `http://localhost:3000/chat`
2. Type a question about your ingested data
3. See streaming response with source citations

### Running Tests

```bash
cd backend
pytest -v
```

### API Documentation

FastAPI auto-generates docs:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
