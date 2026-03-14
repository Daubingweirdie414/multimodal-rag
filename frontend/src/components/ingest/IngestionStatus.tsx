"use client";

import type { IngestionJob } from "@/lib/types";

const STATUS_STYLES: Record<IngestionJob["status"], { bg: string; text: string; label: string }> = {
  uploading: { bg: "bg-blue-900/30", text: "text-blue-400", label: "Uploading..." },
  processing: { bg: "bg-amber-900/30", text: "text-amber-400", label: "Processing..." },
  success: { bg: "bg-emerald-900/30", text: "text-emerald-400", label: "Success" },
  error: { bg: "bg-red-900/30", text: "text-red-400", label: "Error" },
};

const TYPE_ICONS: Record<string, string> = {
  text: "T",
  pdf: "P",
  image: "I",
  audio: "A",
  video: "V",
};

interface IngestionStatusProps {
  jobs: IngestionJob[];
}

export default function IngestionStatus({ jobs }: IngestionStatusProps) {
  if (jobs.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-zinc-300">Recent Ingestions</h3>
      <div className="flex flex-col gap-2">
        {jobs.map((job) => {
          const style = STATUS_STYLES[job.status];
          return (
            <div
              key={job.id}
              className={`flex items-center gap-3 rounded-lg border border-zinc-700 px-3 py-2.5 ${style.bg}`}
            >
              {/* Type badge */}
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-zinc-700 text-xs font-bold text-zinc-300">
                {TYPE_ICONS[job.sourceType] ?? "?"}
              </span>

              {/* File info */}
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="truncate text-sm font-medium text-zinc-200">
                  {job.filename}
                </span>
                {job.message && (
                  <span className="truncate text-xs text-zinc-500">{job.message}</span>
                )}
              </div>

              {/* Status */}
              <div className="flex items-center gap-1.5">
                {(job.status === "uploading" || job.status === "processing") && (
                  <span className="h-2 w-2 animate-pulse rounded-full bg-amber-400" />
                )}
                <span className={`text-xs font-medium ${style.text}`}>
                  {style.label}
                </span>
                {job.chunksIngested !== undefined && (
                  <span className="text-xs text-zinc-500">
                    ({job.chunksIngested} chunks)
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
