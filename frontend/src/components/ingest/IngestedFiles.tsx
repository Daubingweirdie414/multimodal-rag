"use client";

import type { IngestionJob } from "@/lib/types";

interface IngestedFilesProps {
  jobs: IngestionJob[];
}

export default function IngestedFiles({ jobs }: IngestedFilesProps) {
  const successJobs = jobs.filter((j) => j.status === "success");

  if (successJobs.length === 0) return null;

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-sm font-medium text-zinc-300">
        Ingested Files ({successJobs.length})
      </h3>
      <div className="rounded-lg border border-zinc-700 bg-zinc-800/50">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-700 text-left text-xs text-zinc-500">
              <th className="px-3 py-2 font-medium">File</th>
              <th className="px-3 py-2 font-medium">Type</th>
              <th className="px-3 py-2 font-medium text-right">Chunks</th>
            </tr>
          </thead>
          <tbody>
            {successJobs.map((job) => (
              <tr key={job.id} className="border-b border-zinc-800 last:border-0">
                <td className="px-3 py-2 text-zinc-200">{job.filename}</td>
                <td className="px-3 py-2">
                  <span className="rounded bg-zinc-700 px-1.5 py-0.5 text-xs font-medium text-zinc-300">
                    {job.sourceType.toUpperCase()}
                  </span>
                </td>
                <td className="px-3 py-2 text-right text-zinc-400">
                  {job.chunksIngested ?? "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
