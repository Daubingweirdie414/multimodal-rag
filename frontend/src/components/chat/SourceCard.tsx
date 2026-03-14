"use client";

import type { SourceReference } from "@/lib/types";

const TYPE_COLORS: Record<string, string> = {
  text: "bg-emerald-900/50 text-emerald-300 border-emerald-700",
  pdf: "bg-red-900/50 text-red-300 border-red-700",
  image: "bg-purple-900/50 text-purple-300 border-purple-700",
  audio: "bg-amber-900/50 text-amber-300 border-amber-700",
  video: "bg-blue-900/50 text-blue-300 border-blue-700",
};

interface SourceCardProps {
  source: SourceReference;
  index: number;
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const colorClass = TYPE_COLORS[source.source_type] ?? "bg-zinc-800 text-zinc-300 border-zinc-600";

  return (
    <div className="flex flex-col gap-1.5 rounded-lg border border-zinc-700 bg-zinc-800/50 p-3 text-sm">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-400">#{index + 1}</span>
          <span className={`rounded px-1.5 py-0.5 text-xs font-medium border ${colorClass}`}>
            {source.source_type.toUpperCase()}
          </span>
          <span className="truncate text-sm font-medium text-zinc-200">
            {source.source_file}
          </span>
        </div>
        <span className="whitespace-nowrap text-xs text-zinc-500">
          {(source.score * 100).toFixed(1)}% match
        </span>
      </div>
      {source.content_preview && (
        <p className="line-clamp-2 text-xs leading-relaxed text-zinc-400">
          {source.content_preview}
        </p>
      )}
    </div>
  );
}
