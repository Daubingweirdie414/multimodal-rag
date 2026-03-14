"use client";

import { useState, useCallback } from "react";
import type { IngestionJob, SourceType } from "@/lib/types";
import { ingestFile, ingestText, detectSourceType } from "@/lib/api";

function uid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useIngest() {
  const [jobs, setJobs] = useState<IngestionJob[]>([]);

  const updateJob = useCallback(
    (id: string, update: Partial<IngestionJob>) => {
      setJobs((prev) => prev.map((j) => (j.id === id ? { ...j, ...update } : j)));
    },
    []
  );

  /** Upload a single file. */
  const uploadFile = useCallback(
    async (file: File) => {
      const sourceType = detectSourceType(file.name);
      if (!sourceType) {
        const id = uid();
        setJobs((prev) => [
          {
            id,
            filename: file.name,
            sourceType: "text" as SourceType,
            status: "error",
            message: `Unsupported file type: ${file.name}`,
          },
          ...prev,
        ]);
        return;
      }

      const id = uid();
      setJobs((prev) => [
        { id, filename: file.name, sourceType, status: "uploading" },
        ...prev,
      ]);

      try {
        updateJob(id, { status: "processing" });
        const result = await ingestFile(file, sourceType);
        updateJob(id, {
          status: "success",
          message: result.message,
          chunksIngested: result.chunks_ingested,
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Upload failed";
        updateJob(id, { status: "error", message: msg });
      }
    },
    [updateJob]
  );

  /** Upload multiple files. */
  const uploadFiles = useCallback(
    async (files: FileList | File[]) => {
      const fileArr = Array.from(files);
      await Promise.allSettled(fileArr.map((f) => uploadFile(f)));
    },
    [uploadFile]
  );

  /** Ingest raw text. */
  const submitText = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const id = uid();
      setJobs((prev) => [
        { id, filename: "raw_text", sourceType: "text", status: "processing" },
        ...prev,
      ]);

      try {
        const result = await ingestText(text);
        updateJob(id, {
          status: "success",
          message: result.message,
          chunksIngested: result.chunks_ingested,
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Text ingestion failed";
        updateJob(id, { status: "error", message: msg });
      }
    },
    [updateJob]
  );

  const clearJobs = useCallback(() => {
    setJobs([]);
  }, []);

  return { jobs, uploadFile, uploadFiles, submitText, clearJobs };
}
