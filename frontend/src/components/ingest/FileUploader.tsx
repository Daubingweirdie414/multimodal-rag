"use client";

import { useState, useCallback, useRef } from "react";
import { ACCEPTED_EXTENSIONS } from "@/lib/api";

interface FileUploaderProps {
  onFilesSelected: (files: FileList | File[]) => void;
  disabled?: boolean;
}

export default function FileUploader({ onFilesSelected, disabled }: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      if (disabled || !e.dataTransfer.files.length) return;
      onFilesSelected(e.dataTransfer.files);
    },
    [onFilesSelected, disabled]
  );

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files?.length) {
        onFilesSelected(e.target.files);
        e.target.value = "";
      }
    },
    [onFilesSelected]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors ${
        isDragging
          ? "border-indigo-500 bg-indigo-500/10"
          : "border-zinc-700 bg-zinc-900/50 hover:border-zinc-600 hover:bg-zinc-900"
      } ${disabled ? "pointer-events-none opacity-50" : ""}`}
      role="button"
      tabIndex={0}
      aria-label="Upload files"
    >
      <svg
        className={`mb-3 h-10 w-10 ${isDragging ? "text-indigo-400" : "text-zinc-500"}`}
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth={1.5}
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z"
        />
      </svg>
      <p className="mb-1 text-sm font-medium text-zinc-300">
        {isDragging ? "Drop files here" : "Drag & drop files, or click to browse"}
      </p>
      <p className="text-xs text-zinc-500">
        Supports: PDF, TXT, PNG, JPG, MP3, WAV, MP4, MOV
      </p>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXTENSIONS}
        onChange={handleChange}
        className="hidden"
      />
    </div>
  );
}
