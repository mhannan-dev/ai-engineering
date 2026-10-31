import type { Metadata } from "next";

import { ChatWorkspace } from "@/components/chat/chat-workspace";

export const metadata: Metadata = {
  title: "Ask · Enterprise Knowledge Worker",
};

export default function ChatPage() {
  return (
    <main className="flex flex-1 flex-col font-sans">
      <ChatWorkspace />
    </main>
  );
}
