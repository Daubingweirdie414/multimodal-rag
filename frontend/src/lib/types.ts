/** Source types supported by the RAG system. */
export type SourceType = "text" | "pdf" | "image" | "audio" | "video";

/** A single source reference returned from the RAG pipeline. */
export interface SourceReference {
  source_type: SourceType;
  source_file: string;
  chunk_index: number;
  content_preview: string;
  score: number;
}

/** Response from /query endpoint. */
export interface QueryResponse {
  answer: string;
  sources: SourceReference[];
}

/** Request body for /query and /query/stream. */
export interface QueryRequest {
  question: string;
  source_type?: SourceType | null;
  top_k?: number;
}

/** Request body for /ingest/text. */
export interface TextIngestRequest {
  text: string;
}

/** Response from any /ingest/* endpoint. */
export interface IngestResponse {
  status: string;
  source_type: SourceType;
  source_file: string;
  chunks_ingested: number;
  message: string;
}

/** Health check response. */
export interface HealthResponse {
  status: string;
  message: string;
}

/** A chat message in the UI. */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
  isStreaming?: boolean;
}

/** Ingestion job tracked in the UI. */
export interface IngestionJob {
  id: string;
  filename: string;
  sourceType: SourceType;
  status: "uploading" | "processing" | "success" | "error";
  progress?: number;
  message?: string;
  chunksIngested?: number;
}
