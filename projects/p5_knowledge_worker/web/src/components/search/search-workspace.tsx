"use client";

import { useState, type FormEvent } from "react";

import {
  ApiError,
  searchDebug,
  searchDocuments,
  type SearchDebugResponse,
  type SearchResponse,
  type SearchResultChunk,
} from "@/lib/api";

import { SourceCard } from "./source-card";

type Mode = "search" | "compare";

type Result =
  | { mode: "search"; data: SearchResponse }
  | { mode: "compare"; data: SearchDebugResponse };

const EXAMPLES = [
  "How many days of annual leave do I get?",
  "ছুটি কত দিন?",
  "travel allowance outside Dhaka",
  "chuti koto din",
];

export function SearchWorkspace() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<Mode>("search");
  const [rerank, setRerank] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  async function run(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    setLoading(true);
    setError(null);
    try {
      setResult(
        mode === "compare"
          ? { mode, data: await searchDebug(trimmed) }
          : { mode, data: await searchDocuments({ query: trimmed, rerank, limit: 10 }) },
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void run(query);
  }

  return (
    <div className="space-y-6">
      <form onSubmit={onSubmit} className="space-y-3">
        <div className="flex gap-2">
          <input
            id="search-query"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask in English, বাংলা or Banglish…"
            maxLength={1000}
            className="min-w-0 flex-1 rounded-xl border border-zinc-300 bg-white px-4 py-2.5 text-sm text-zinc-900 shadow-sm outline-none focus:border-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:border-zinc-300"
          />
          <button
            id="search-submit"
            type="submit"
            disabled={loading || !query.trim()}
            className="rounded-xl bg-zinc-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-zinc-600 dark:text-zinc-400">
          <div className="inline-flex rounded-lg border border-zinc-200 p-0.5 dark:border-zinc-800" role="radiogroup" aria-label="Mode">
            {(["search", "compare"] as const).map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={mode === value}
                onClick={() => setMode(value)}
                className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                  mode === value
                    ? "bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900"
                    : "hover:text-zinc-900 dark:hover:text-zinc-100"
                }`}
              >
                {value === "search" ? "Hybrid search" : "Compare retrievers"}
              </button>
            ))}
          </div>
          {mode === "search" && (
            <label className="inline-flex items-center gap-2">
              <input
                id="search-rerank"
                type="checkbox"
                checked={rerank}
                onChange={(event) => setRerank(event.target.checked)}
                className="h-4 w-4 rounded border-zinc-300"
              />
              Rerank with cross-encoder
            </label>
          )}
        </div>

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => {
                setQuery(example);
                void run(example);
              }}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1 text-xs text-zinc-600 transition-colors hover:border-zinc-300 hover:text-zinc-900 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
            >
              {example}
            </button>
          ))}
        </div>
      </form>

      {error && (
        <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
          {error}
        </p>
      )}

      {result && <QueryInfo normalized={result.data.normalized_query} query={result.data.query} banglish={result.data.was_banglish} />}
      {result?.mode === "search" && <SearchResults data={result.data} />}
      {result?.mode === "compare" && <CompareResults data={result.data} />}
    </div>
  );
}

function QueryInfo({ query, normalized, banglish }: { query: string; normalized: string; banglish: boolean }) {
  if (!banglish && normalized === query) return null;
  return (
    <p className="text-xs text-zinc-500 dark:text-zinc-400">
      {banglish ? "Banglish detected. " : ""}Searched for{" "}
      <span className="font-medium text-zinc-800 dark:text-zinc-200">{normalized}</span>
    </p>
  );
}

function SearchResults({ data }: { data: SearchResponse }) {
  if (data.results.length === 0) {
    return (
      <p className="rounded-2xl border border-zinc-200 bg-white py-10 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
        No matching passages.
      </p>
    );
  }
  return (
    <div className="space-y-3">
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        {data.total} passages · {data.reranked ? "RRF + cross-encoder rerank" : "RRF (dense + BM25)"}
      </p>
      {/* The API still returns the best passages when it abstains, so they stay visible for inspection. */}
      {data.is_abstention && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
          No passage scored above the relevance threshold, so chat would answer &quot;I don&apos;t
          know&quot; for this query. The closest passages are shown below.
        </p>
      )}
      {data.results.map((chunk, i) => (
        <SourceCard key={chunk.chunk_id} chunk={chunk} position={i + 1} />
      ))}
    </div>
  );
}

const COLUMNS: { key: keyof Pick<SearchDebugResponse, "dense_hits" | "sparse_hits" | "fused_hits" | "reranked_hits">; title: string; hint: string }[] = [
  { key: "dense_hits", title: "Dense", hint: "Meaning (embeddings)" },
  { key: "sparse_hits", title: "BM25", hint: "Exact words" },
  { key: "fused_hits", title: "RRF", hint: "Dense + BM25 by rank" },
  { key: "reranked_hits", title: "Reranked", hint: "Cross-encoder" },
];

/** The four stages side by side. Hovering a passage highlights it in every column. */
function CompareResults({ data }: { data: SearchDebugResponse }) {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {COLUMNS.map((column) => {
        const hits: SearchResultChunk[] = data[column.key];
        return (
          <section key={column.key} className="min-w-0 space-y-2">
            <header>
              <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">{column.title}</h2>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">{column.hint}</p>
            </header>
            {hits.length === 0 && (
              <p className="rounded-xl border border-dashed border-zinc-300 py-6 text-center text-xs text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
                No hits
              </p>
            )}
            {hits.map((chunk, i) => (
              <div
                key={chunk.chunk_id}
                onMouseEnter={() => setHovered(chunk.chunk_id)}
                onMouseLeave={() => setHovered(null)}
                className={`rounded-xl transition-shadow ${
                  hovered === chunk.chunk_id ? "ring-2 ring-amber-400" : ""
                }`}
              >
                <SourceCard chunk={chunk} position={i + 1} compact />
              </div>
            ))}
          </section>
        );
      })}
    </div>
  );
}
