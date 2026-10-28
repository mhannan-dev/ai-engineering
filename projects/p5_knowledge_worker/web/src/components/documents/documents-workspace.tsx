"use client";

import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
  SUPPORTED_EXTENSIONS,
  deleteDocument,
  listDocuments,
  reindexDocument,
  uploadDocument,
  type DocumentOut,
} from "@/lib/api";

import { ChunksDrawer } from "./chunks-drawer";
import { DocumentsTable } from "./documents-table";
import { isInFlight } from "./status-badge";
import { UploadDropzone } from "./upload-dropzone";

const POLL_MS = 2_000;
const MAX_BYTES = 25 * 1024 * 1024;

type Notice = { kind: "error" | "info"; text: string };

function errorMessage(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

/** Checks extension and size before upload; the API validates the content again. */
function rejectReason(file: File): string | null {
  const dot = file.name.lastIndexOf(".");
  const ext = dot >= 0 ? file.name.slice(dot).toLowerCase() : "";
  if (!SUPPORTED_EXTENSIONS.includes(ext)) return `${file.name}: unsupported file type.`;
  if (file.size > MAX_BYTES) return `${file.name}: larger than 25 MB.`;
  return null;
}

export function DocumentsWorkspace() {
  const [documents, setDocuments] = useState<DocumentOut[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [busyIds, setBusyIds] = useState<ReadonlySet<string>>(new Set());
  const [highlightId, setHighlightId] = useState<string | null>(null);
  const [viewing, setViewing] = useState<DocumentOut | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);

  // State is set only in the promise callbacks, so effects can call this without cascading renders.
  const refresh = useCallback(
    () =>
      listDocuments().then(
        (page) => {
          setDocuments(page.items);
          setTotal(page.total);
          setLoadError(null);
          setLoading(false);
        },
        (err: unknown) => {
          setLoadError(errorMessage(err, "Couldn't load documents."));
          setLoading(false);
        },
      ),
    [],
  );

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Indexing runs in a background worker, so poll while any document is still in flight.
  const hasInFlight = documents.some((doc) => isInFlight(doc.status));
  useEffect(() => {
    if (!hasInFlight) return;
    const timer = setInterval(() => void refresh(), POLL_MS);
    return () => clearInterval(timer);
  }, [hasInFlight, refresh]);

  function setBusy(id: string, busy: boolean) {
    setBusyIds((prev) => {
      const next = new Set(prev);
      if (busy) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  async function handleFiles(files: File[]) {
    const problems: Notice[] = [];
    const accepted = files.filter((file) => {
      const reason = rejectReason(file);
      if (reason) problems.push({ kind: "error", text: reason });
      return !reason;
    });

    setUploading(true);
    let lastId: string | null = null;
    // One at a time: the API indexes with a single worker anyway.
    for (const file of accepted) {
      try {
        const doc = await uploadDocument(file);
        lastId = doc.id;
      } catch (err) {
        problems.push({ kind: "error", text: `${file.name}: ${errorMessage(err, "upload failed.")}` });
      }
    }
    setUploading(false);
    setNotices(problems);
    if (lastId) setHighlightId(lastId);
    await refresh();
  }

  async function handleReindex(doc: DocumentOut) {
    setBusy(doc.id, true);
    try {
      await reindexDocument(doc.id);
      setHighlightId(doc.id);
      await refresh();
    } catch (err) {
      setNotices([{ kind: "error", text: `${doc.filename}: ${errorMessage(err, "re-index failed.")}` }]);
    } finally {
      setBusy(doc.id, false);
    }
  }

  async function handleDelete(doc: DocumentOut) {
    if (!window.confirm(`Delete "${doc.filename}" and all its chunks?`)) return;
    setBusy(doc.id, true);
    try {
      await deleteDocument(doc.id);
      setNotices([{ kind: "info", text: `Deleted ${doc.filename}.` }]);
      await refresh();
    } catch (err) {
      setNotices([{ kind: "error", text: `${doc.filename}: ${errorMessage(err, "delete failed.")}` }]);
    } finally {
      setBusy(doc.id, false);
    }
  }

  const closeDrawer = useCallback(() => setViewing(null), []);

  return (
    <div className="space-y-6">
      <UploadDropzone onFiles={(files) => void handleFiles(files)} busy={uploading} />

      {notices.length > 0 && (
        <div className="space-y-2">
          {notices.map((notice, i) => (
            <div
              key={i}
              role={notice.kind === "error" ? "alert" : "status"}
              className={`flex items-start justify-between gap-4 rounded-lg border p-3 text-sm ${
                notice.kind === "error"
                  ? "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200"
                  : "border-zinc-200 bg-zinc-50 text-zinc-700 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-300"
              }`}
            >
              <span>{notice.text}</span>
              <button
                type="button"
                aria-label="Dismiss"
                onClick={() => setNotices((prev) => prev.filter((_, j) => j !== i))}
                className="shrink-0 opacity-60 hover:opacity-100"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      <section aria-labelledby="documents-heading" className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 id="documents-heading" className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
            Documents
          </h2>
          {!loading && !loadError && (
            <span className="text-xs text-zinc-500 dark:text-zinc-400">
              {total} total{hasInFlight ? " · indexing…" : ""}
            </span>
          )}
        </div>

        {loadError && (
          <div
            role="alert"
            className="flex items-center justify-between gap-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200"
          >
            <span>{loadError}</span>
            <button
              id="documents-retry"
              type="button"
              onClick={() => {
                setLoading(true);
                void refresh();
              }}
              className="shrink-0 font-medium underline underline-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {loading && documents.length === 0 && (
          <div className="h-40 animate-pulse rounded-2xl bg-zinc-100 dark:bg-zinc-900" />
        )}

        {!loading && !loadError && documents.length === 0 && (
          <p className="rounded-2xl border border-zinc-200 bg-white py-12 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
            No documents yet. Upload one above to start indexing.
          </p>
        )}

        {documents.length > 0 && (
          <DocumentsTable
            documents={documents}
            highlightId={highlightId}
            busyIds={busyIds}
            onView={setViewing}
            onReindex={(doc) => void handleReindex(doc)}
            onDelete={(doc) => void handleDelete(doc)}
          />
        )}
      </section>

      {viewing && <ChunksDrawer key={viewing.id} doc={viewing} onClose={closeDrawer} />}
    </div>
  );
}
