import { PageHeader } from "@/components/page-header";
import { DocumentsWorkspace } from "@/components/documents/documents-workspace";

// No sign-in until Phase 6 adds JWT auth; the API serves a single local user.
export default function DocumentsPage() {
  return (
    <main className="flex-1 font-sans">
      <div className="mx-auto w-full max-w-6xl space-y-8 px-4 py-10 sm:px-6">
        <PageHeader
          title="Knowledge base"
          description="Upload English and বাংলা documents. Each one is parsed, chunked and indexed for hybrid search."
        />
        <DocumentsWorkspace />
      </div>
    </main>
  );
}
