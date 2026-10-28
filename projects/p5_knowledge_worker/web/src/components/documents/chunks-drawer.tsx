"use client";

import { useEffect, useState } from "react";

import { ApiError, listChunks, type ChunkOut, type DocumentOut } from "@/lib/api";
import { formatLanguage } from "@/lib/format";

const PAGE_SIZE = 25;

/** Side panel listing the passages retrieval will search. Mount with key={doc.id} to reset. */
export function ChunksDrawer({ doc, onClose }: { doc: DocumentOut; onClose: () => void }) {
  const [chunks, setChunks] = useState<ChunkOut[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // State is set only in the promise callbacks, so the mount effect can call this safely.
  function load(offset: number) {
    return listChunks(doc.id, PAGE_SIZE, offset).then(
      (page) => {
        setChunks((prev) => (offset === 0 ? page.items : [...prev, ...page.items]));
        setTotal(page.total);
        setError(null);
        setLoading(false);
      },
      (err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Couldn't load chunks.");
        setLoading(false);
      },
    );
  }

  useEffect(() => {
    void load(0);
    // load only depends on doc.id, and the drawer is re-mounted per document.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [doc.id]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-labelledby="chunks-title">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-zinc-950/40 backdrop-blur-sm animate-[fade-in_150ms_ease-out]"
      />
      <aside className="relative flex h-full w-full max-w-2xl flex-col border-l border-zinc-200 bg-white shadow-2xl animate-[slide-in_200ms_ease-out] dark:border-zinc-800 dark:bg-zinc-950">
        <header className="flex items-start justify-between gap-4 border-b border-zinc-200 px-6 py-5 dark:border-zinc-800">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">Chunks</p>
            <h2 id="chunks-title" className="mt-1 truncate text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              {doc.filename}
            </h2>
            <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
              {total} passages · {doc.section_count} sections · {formatLanguage(doc.language)}
            </p>
          </div>
          <button
            id="chunks-close"
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path strokeLinecap="round" d="M6 6l12 12M18 6 6 18" />
            </svg>
          </button>
        </header>

        <div className="flex-1 space-y-3 overflow-y-auto px-6 py-5">
          {error && (
            <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
              {error}
            </p>
          )}

          {loading && chunks.length === 0 &&
            Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-xl bg-zinc-100 dark:bg-zinc-900" />
            ))}

          {!loading && !error && chunks.length === 0 && (
            <p className="py-10 text-center text-sm text-zinc-500 dark:text-zinc-400">
              No chunks yet. They appear once the document is indexed.
            </p>
          )}

          {chunks.map((chunk) => (
            <article
              key={chunk.id}
              className="rounded-xl border border-zinc-200 bg-zinc-50/60 p-4 transition-colors hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/60 dark:hover:border-zinc-700"
            >
              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
                <span className="rounded-md bg-zinc-900 px-1.5 py-0.5 font-mono text-[11px] text-white dark:bg-zinc-100 dark:text-zinc-900">
                  #{chunk.ordinal}
                </span>
                {chunk.page !== null && <span>Page {chunk.page}</span>}
                {chunk.heading && (
                  <span className="max-w-[18rem] truncate font-medium text-zinc-700 dark:text-zinc-300" title={chunk.heading}>
                    {chunk.heading}
                  </span>
                )}
                <span className="ml-auto">
                  {formatLanguage(chunk.language)} · {chunk.token_count} tokens
                </span>
              </div>
              <p
                lang={chunk.language === "bn" ? "bn" : undefined}
                className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-800 dark:text-zinc-200"
              >
                {chunk.text}
              </p>
            </article>
          ))}
        </div>

        {chunks.length < total && (
          <footer className="border-t border-zinc-200 px-6 py-4 dark:border-zinc-800">
            <button
              id="chunks-load-more"
              type="button"
              disabled={loading}
              onClick={() => {
                setLoading(true);
                void load(chunks.length);
              }}
              className="w-full rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-800 transition-colors hover:bg-zinc-50 disabled:opacity-60 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-900"
            >
              {loading ? "Loading…" : `Load more (${chunks.length} of ${total})`}
            </button>
          </footer>
        )}
      </aside>
    </div>
  );
}
