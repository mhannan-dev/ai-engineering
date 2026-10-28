"use client";

import { useEffect, useState, type ReactNode } from "react";

import type { DocumentOut } from "@/lib/api";
import { formatBytes, formatLanguage, formatRelative } from "@/lib/format";

import { StatusBadge, isInFlight } from "./status-badge";

const FORMAT_COLORS: Record<string, string> = {
  pdf: "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
  docx: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
  md: "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300",
  html: "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
  txt: "bg-zinc-200 text-zinc-700 dark:bg-zinc-700/50 dark:text-zinc-300",
};

/** Re-renders every 30 s so relative times ("2 minutes ago") stay current. */
function useNow(intervalMs = 30_000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);
  return now;
}

interface Props {
  documents: DocumentOut[];
  highlightId: string | null;
  busyIds: ReadonlySet<string>;
  onView: (doc: DocumentOut) => void;
  onReindex: (doc: DocumentOut) => void;
  onDelete: (doc: DocumentOut) => void;
}

export function DocumentsTable({ documents, highlightId, busyIds, onView, onReindex, onDelete }: Props) {
  const now = useNow();

  return (
    <div className="overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200 text-sm dark:divide-zinc-800">
          <thead className="bg-zinc-50 text-left text-xs font-medium uppercase tracking-wide text-zinc-500 dark:bg-zinc-900/80 dark:text-zinc-400">
            <tr>
              <th scope="col" className="px-5 py-3">Document</th>
              <th scope="col" className="px-5 py-3">Status</th>
              <th scope="col" className="px-5 py-3 text-right">Chunks</th>
              <th scope="col" className="px-5 py-3">Language</th>
              <th scope="col" className="px-5 py-3">Uploaded</th>
              <th scope="col" className="px-5 py-3 text-right">
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
            {documents.map((doc) => {
              const busy = busyIds.has(doc.id) || isInFlight(doc.status);
              return (
                <tr
                  key={doc.id}
                  id={`doc-row-${doc.id}`}
                  className={`transition-colors hover:bg-zinc-50/80 dark:hover:bg-zinc-800/40 ${
                    highlightId === doc.id ? "bg-amber-50 dark:bg-amber-400/10" : ""
                  }`}
                >
                  <td className="max-w-xs px-5 py-4">
                    <div className="flex items-center gap-3">
                      <span
                        className={`shrink-0 rounded-md px-1.5 py-0.5 font-mono text-[10px] font-semibold uppercase ${
                          FORMAT_COLORS[doc.format] ?? FORMAT_COLORS.txt
                        }`}
                      >
                        {doc.format}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate font-medium text-zinc-900 dark:text-zinc-100" title={doc.filename}>
                          {doc.filename}
                        </p>
                        <p className="text-xs text-zinc-500 dark:text-zinc-400">{formatBytes(doc.size_bytes)}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge status={doc.status} />
                    {doc.status === "failed" && doc.error_message && (
                      <p className="mt-1.5 max-w-xs text-xs leading-snug text-rose-700 dark:text-rose-300">
                        {doc.error_message}
                      </p>
                    )}
                  </td>
                  <td className="px-5 py-4 text-right tabular-nums text-zinc-700 dark:text-zinc-300">
                    {doc.status === "indexed" ? doc.chunk_count : "—"}
                  </td>
                  <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">{formatLanguage(doc.language)}</td>
                  <td className="whitespace-nowrap px-5 py-4 text-zinc-500 dark:text-zinc-400">
                    {formatRelative(doc.created_at, now)}
                  </td>
                  <td className="whitespace-nowrap px-5 py-4 text-right">
                    <div className="inline-flex items-center gap-1">
                      <ActionButton
                        id={`view-${doc.id}`}
                        label="View chunks"
                        disabled={doc.status !== "indexed"}
                        onClick={() => onView(doc)}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h10" />
                      </ActionButton>
                      <ActionButton
                        id={`reindex-${doc.id}`}
                        label="Re-index"
                        disabled={busy}
                        onClick={() => onReindex(doc)}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v6h6M20 20v-6h-6M5.5 15a7 7 0 0 0 12.4 2M18.5 9A7 7 0 0 0 6.1 7" />
                      </ActionButton>
                      <ActionButton
                        id={`delete-${doc.id}`}
                        label="Delete"
                        danger
                        disabled={busyIds.has(doc.id)}
                        onClick={() => onDelete(doc)}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 7h14M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
                      </ActionButton>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ActionButton({
  id,
  label,
  onClick,
  disabled,
  danger = false,
  children,
}: {
  id: string;
  label: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      id={id}
      type="button"
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className={`rounded-lg p-2 transition-colors disabled:cursor-not-allowed disabled:opacity-30 ${
        danger
          ? "text-zinc-500 hover:bg-rose-50 hover:text-rose-600 dark:text-zinc-400 dark:hover:bg-rose-500/10 dark:hover:text-rose-400"
          : "text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
      }`}
    >
      <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
        {children}
      </svg>
    </button>
  );
}
