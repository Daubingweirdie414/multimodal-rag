"use client";

import Header from "@/components/layout/Header";
import ChatWindow from "@/components/chat/ChatWindow";
import { useChat } from "@/hooks/useChat";

export default function ChatPage() {
  const { messages, isLoading, sendMessage, clearMessages } = useChat();

  return (
    <>
      <Header
        title="Chat"
        actions={
          messages.length > 0 ? (
            <button
              onClick={clearMessages}
              className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            >
              Clear Chat
            </button>
          ) : null
        }
      />
      <ChatWindow
        messages={messages}
        isLoading={isLoading}
        onSend={sendMessage}
      />
    </>
  );
}
