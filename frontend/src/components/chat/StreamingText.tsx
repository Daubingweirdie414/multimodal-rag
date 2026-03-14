"use client";

interface StreamingTextProps {
  content: string;
  isStreaming: boolean;
}

export default function StreamingText({ content, isStreaming }: StreamingTextProps) {
  return (
    <div className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-200">
      {content}
      {isStreaming && (
        <span className="animate-blink ml-0.5 inline-block h-4 w-1.5 bg-zinc-400" />
      )}
    </div>
  );
}
