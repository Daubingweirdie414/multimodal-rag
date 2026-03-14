"use client";

import Header from "@/components/layout/Header";
import FileUploader from "@/components/ingest/FileUploader";
import TextInput from "@/components/ingest/TextInput";
import IngestionStatus from "@/components/ingest/IngestionStatus";
import IngestedFiles from "@/components/ingest/IngestedFiles";
import { useIngest } from "@/hooks/useIngest";

export default function IngestPage() {
  const { jobs, uploadFiles, submitText, clearJobs } = useIngest();

  return (
    <>
      <Header
        title="Ingest Data"
        actions={
          jobs.length > 0 ? (
            <button
              onClick={clearJobs}
              className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            >
              Clear History
            </button>
          ) : null
        }
      />
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto flex max-w-2xl flex-col gap-6">
          {/* File upload */}
          <FileUploader onFilesSelected={uploadFiles} />

          {/* Text input */}
          <TextInput onSubmit={submitText} />

          {/* Status */}
          <IngestionStatus jobs={jobs} />

          {/* Ingested files table */}
          <IngestedFiles jobs={jobs} />
        </div>
      </div>
    </>
  );
}
