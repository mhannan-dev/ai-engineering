import type { Metadata } from "next";

import { ChatWorkspace } from "@/components/chat/chat-workspace";
import { PageHeader } from "@/components/page-header";

export const metadata: Metadata = {
  title: "Ask · Enterprise Knowledge Worker",
};

export default function ChatPage() {
  return (
    <main className="flex-1 font-sans">
      <div className="mx-auto w-full max-w-3xl space-y-8 px-4 py-10 sm:px-6">
        <PageHeader
          title="Ask your documents"
          description="Answers are generated only from your indexed documents, with citations checked against the retrieved passages."
        />
        <ChatWorkspace />
      </div>
    </main>
  );
}
