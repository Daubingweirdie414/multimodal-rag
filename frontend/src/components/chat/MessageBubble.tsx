"use client";

import type { ChatMessage } from "@/lib/types";
import SourceCard from "./SourceCard";
import StreamingText from "./StreamingText";

interface MessageBubbleProps {
  message: ChatMessage;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`flex max-w-[75%] flex-col gap-2 rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-indigo-600 text-white"
            : "bg-zinc-800 text-zinc-200"
        }`}
      >
        {/* Role label */}
        <span
          className={`text-xs font-medium ${
            isUser ? "text-indigo-200" : "text-zinc-500"
          }`}
        >
          {isUser ? "You" : "Assistant"}
        </span>

        {/* Message content */}
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        ) : (
          <StreamingText
            content={message.content}
            isStreaming={message.isStreaming ?? false}
          />
        )}

        {/* Source cards */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 flex flex-col gap-2 border-t border-zinc-700 pt-2">
            <span className="text-xs font-medium text-zinc-500">Sources</span>
            {message.sources.map((src, i) => (
              <SourceCard key={`${src.source_file}-${src.chunk_index}-${i}`} source={src} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
