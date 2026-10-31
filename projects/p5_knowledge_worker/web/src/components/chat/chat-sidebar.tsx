"use client";

import type { Conversation } from "@/lib/api";
import { formatRelative } from "@/lib/format";

interface Props {
  conversations: Conversation[];
  loading: boolean;
  error: string | null;
  activeId: string | null;
  busy: boolean;
  onNew: () => void;
  onSelect: (id: string) => void;
  onDelete: (conversation: Conversation) => void;
}

/** Saved conversations, most recently active first. */
export function ChatSidebar({ conversations, loading, error, activeId, busy, onNew, onSelect, onDelete }: Props) {
  return (
    <div className="flex h-full flex-col">
      <div className="p-3">
        <button
          id="chat-new"
          type="button"
          onClick={onNew}
          className="flex w-full items-center justify-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2.5 text-sm font-medium text-zinc-800 shadow-sm transition-all hover:border-zinc-300 hover:shadow dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-100 dark:hover:border-zinc-700"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
            <path strokeLinecap="round" d="M12 5v14M5 12h14" />
          </svg>
          New chat
        </button>
      </div>

      <p className="px-4 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
        History
      </p>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-4" aria-label="Saved conversations">
        {loading &&
          Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="mx-2 my-2 h-8 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-900" />
          ))}

        {!loading && error && <p className="px-3 py-2 text-xs text-rose-600 dark:text-rose-400">{error}</p>}

        {!loading && !error && conversations.length === 0 && (
          <p className="px-3 py-2 text-xs leading-relaxed text-zinc-400 dark:text-zinc-500">
            Your conversations will appear here.
          </p>
        )}

        {conversations.map((c) => {
          const active = c.id === activeId;
          return (
            <div
              key={c.id}
              className={`group relative flex items-center rounded-lg transition-colors ${
                active
                  ? "bg-zinc-200/70 dark:bg-zinc-800"
                  : "hover:bg-zinc-100 dark:hover:bg-zinc-900"
              }`}
            >
              <button
                type="button"
                onClick={() => onSelect(c.id)}
                disabled={busy}
                aria-current={active ? "true" : undefined}
                className="min-w-0 flex-1 px-3 py-2 text-left disabled:cursor-not-allowed"
              >
                <p
                  className={`truncate text-sm ${
                    active ? "font-medium text-zinc-900 dark:text-zinc-50" : "text-zinc-700 dark:text-zinc-300"
                  }`}
                  title={c.title}
                >
                  {c.title}
                </p>
                <p className="text-[11px] text-zinc-400 dark:text-zinc-500">{formatRelative(c.updated_at)}</p>
              </button>
              <button
                type="button"
                onClick={() => onDelete(c)}
                disabled={busy}
                aria-label={`Delete "${c.title}"`}
                title="Delete"
                className="mr-1 shrink-0 rounded-md p-1.5 text-zinc-400 opacity-0 transition-all hover:bg-rose-50 hover:text-rose-600 focus-visible:opacity-100 group-hover:opacity-100 disabled:hidden dark:hover:bg-rose-500/10 dark:hover:text-rose-400"
              >
                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 7h14M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
                </svg>
              </button>
            </div>
          );
        })}
      </nav>
    </div>
  );
}
