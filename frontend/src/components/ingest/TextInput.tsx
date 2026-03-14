"use client";

import { useState } from "react";

interface TextInputProps {
  onSubmit: (text: string) => void;
  disabled?: boolean;
}

export default function TextInput({ onSubmit, disabled }: TextInputProps) {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    if (!text.trim() || disabled) return;
    onSubmit(text.trim());
    setText("");
  };

  return (
    <div className="flex flex-col gap-3">
      <label className="text-sm font-medium text-zinc-300">
        Paste raw text
      </label>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste text content to ingest into the RAG system..."
        disabled={disabled}
        rows={5}
        className="resize-y rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 outline-none focus:border-indigo-500 disabled:opacity-50"
      />
      <button
        onClick={handleSubmit}
        disabled={disabled || !text.trim()}
        className="self-end rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-40"
      >
        Ingest Text
      </button>
    </div>
  );
}
