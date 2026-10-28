import { ApiHealth } from "@/components/documents/api-health";
import { DocumentsWorkspace } from "@/components/documents/documents-workspace";

// No sign-in until Phase 6 adds JWT auth; the API serves a single local user.
export default function DocumentsPage() {
  return (
    <main className="flex-1 bg-zinc-50 font-sans dark:bg-black">
      <div className="mx-auto w-full max-w-5xl space-y-8 px-4 py-10 sm:px-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
              Knowledge base
            </h1>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Upload English and বাংলা documents. Each one is parsed, chunked and indexed for
              hybrid search.
            </p>
          </div>
          <ApiHealth />
        </header>
        <DocumentsWorkspace />
      </div>
    </main>
  );
}
