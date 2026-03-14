import type {
  QueryRequest,
  QueryResponse,
  TextIngestRequest,
  IngestResponse,
  HealthResponse,
  SourceType,
} from "./types";

// Proxied through Next.js rewrites (/api/* -> backend:8000) — no CORS issues
const API_URL = "/api";

// Direct backend URL for large file uploads (bypasses Next.js body size limits)
const BACKEND_DIRECT = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Generic JSON fetcher with error handling. */
async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<T>;
}

// ─── Query ───────────────────────────────────────────────────────────

/** Non-streaming query. */
export async function query(req: QueryRequest): Promise<QueryResponse> {
  return fetchJSON<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

/** Streaming query — calls backend directly to avoid Next.js SSE buffering.
 *  CORS is configured to allow all origins. */
export async function queryStream(req: QueryRequest): Promise<Response> {
  const res = await fetch(`${BACKEND_DIRECT}/query/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res;
}

// ─── Ingestion ───────────────────────────────────────────────────────

/** Ingest raw text. */
export async function ingestText(text: string): Promise<IngestResponse> {
  return fetchJSON<IngestResponse>("/ingest/text", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text } satisfies TextIngestRequest),
  });
}

/** Ingest a file (pdf, image, audio, video).
 *  Uploads directly to backend to bypass Next.js body size limits for large files. */
export async function ingestFile(
  file: File,
  sourceType: SourceType
): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${BACKEND_DIRECT}/ingest/${sourceType}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json() as Promise<IngestResponse>;
}

// ─── Utility ─────────────────────────────────────────────────────────

/** Health check. */
export async function healthCheck(): Promise<HealthResponse> {
  return fetchJSON<HealthResponse>("/health");
}

// ─── Helpers ─────────────────────────────────────────────────────────

const EXTENSION_MAP: Record<string, SourceType> = {
  ".txt": "text",
  ".pdf": "pdf",
  ".png": "image",
  ".jpg": "image",
  ".jpeg": "image",
  ".mp3": "audio",
  ".wav": "audio",
  ".mp4": "video",
  ".mov": "video",
};

/** Detect source type from file extension. Returns null if unsupported. */
export function detectSourceType(filename: string): SourceType | null {
  const ext = filename.slice(filename.lastIndexOf(".")).toLowerCase();
  return EXTENSION_MAP[ext] ?? null;
}

/** Accepted file extensions for the upload input. */
export const ACCEPTED_EXTENSIONS = Object.keys(EXTENSION_MAP).join(",");
