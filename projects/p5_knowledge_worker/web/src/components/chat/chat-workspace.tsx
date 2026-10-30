"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import {
  ApiError,
  streamChat,
  type ChatEvent,
  type CitationValidation,
  type SearchResultChunk,
} from "@/lib/api";

import { SourceCard } from "@/components/search/source-card";

interface Turn {
  id: number;
  question: string;
  status: string | null;
  normalizedQuery: string | null;
  sources: SearchResultChunk[];
  answer: string;
  abstention: string | null;
  validation: CitationValidation | null;
  error: string | null;
  done: boolean;
}

function applyEvent(turn: Turn, event: ChatEvent): Turn {
  switch (event.event) {
    case "status":
      return { ...turn, status: event.data.message };
    case "sources":
      return { ...turn, sources: event.data.sources, normalizedQuery: event.data.normalized_query };
    case "token":
      return { ...turn, answer: turn.answer + event.data.token };
    case "abstention":
      return { ...turn, answer: event.data.answer, abstention: event.data.reason };
    case "validation":
      return { ...turn, validation: event.data };
    case "done":
      return {
        ...turn,
        answer: event.data.answer,
        validation: turn.validation ?? event.data.validation,
        status: null,
        done: true,
      };
    case "error":
      return { ...turn, error: event.data.error, status: null, done: true };
  }
}

export function ChatWorkspace() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  function update(id: number, change: (turn: Turn) => Turn) {
    setTurns((prev) => prev.map((turn) => (turn.id === id ? change(turn) : turn)));
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    const text = question.trim();
    if (!text || running) return;

    const id = Date.now();
    setTurns((prev) => [
      ...prev,
      {
        id,
        question: text,
        status: "Connecting…",
        normalizedQuery: null,
        sources: [],
        answer: "",
        abstention: null,
        validation: null,
        error: null,
        done: false,
      },
    ]);
    setQuestion("");
    setRunning(true);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamChat({ query: text, top_k: 5 }, (evt) => update(id, (turn) => applyEvent(turn, evt)), controller.signal);
      update(id, (turn) => (turn.done ? turn : { ...turn, status: null, done: true }));
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === "AbortError"
          ? "Stopped."
          : err instanceof ApiError
            ? err.message
            : "Something went wrong while answering.";
      update(id, (turn) => ({ ...turn, error: message, status: null, done: true }));
    } finally {
      abortRef.current = null;
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      {turns.length === 0 && (
        <p className="rounded-2xl border border-zinc-200 bg-white px-6 py-10 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-400">
          Ask a question about your indexed documents. Answers cite the file and page they come from,
          and the assistant says so when the documents don&apos;t contain the answer.
        </p>
      )}

      {turns.map((turn) => (
        <TurnView key={turn.id} turn={turn} />
      ))}
      <div ref={bottomRef} />

      <form
        onSubmit={(event) => void ask(event)}
        className="sticky bottom-4 flex gap-2 rounded-2xl border border-zinc-200 bg-white p-2 shadow-lg dark:border-zinc-800 dark:bg-zinc-900"
      >
        <input
          id="chat-question"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask in English, বাংলা or Banglish…"
          maxLength={1000}
          className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-zinc-900 outline-none dark:text-zinc-100"
        />
        {running ? (
          <button
            id="chat-stop"
            type="button"
            onClick={() => abortRef.current?.abort()}
            className="rounded-xl border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
          >
            Stop
          </button>
        ) : (
          <button
            id="chat-submit"
            type="submit"
            disabled={!question.trim()}
            className="rounded-xl bg-zinc-900 px-5 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:opacity-50 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Ask
          </button>
        )}
      </form>
    </div>
  );
}

/** Splits the answer so bracketed citations like [handbook.md, Page 2] stand out. */
function AnswerText({ text }: { text: string }) {
  const parts = text.split(/(\[[^\]\n]+\])/g);
  return (
    <p className="whitespace-pre-wrap text-sm leading-relaxed text-zinc-800 dark:text-zinc-200">
      {parts.map((part, i) =>
        /^\[[^\]\n]+\]$/.test(part) ? (
          <span
            key={i}
            className="mx-0.5 rounded bg-sky-50 px-1 font-mono text-[12px] text-sky-800 dark:bg-sky-500/10 dark:text-sky-300"
          >
            {part}
          </span>
        ) : (
          part
        ),
      )}
    </p>
  );
}

function ValidationBadge({ validation }: { validation: CitationValidation }) {
  const bad = [...(validation.hallucinated_citations ?? []), ...(validation.unmatched_pages ?? [])];
  return (
    <div
      className={`rounded-lg border p-3 text-xs ${
        validation.is_valid
          ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"
          : "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200"
      }`}
    >
      <p className="font-medium">
        {validation.is_valid ? "✓ Every citation matches a retrieved passage" : "⚠ Some citations don't match the retrieved passages"}
      </p>
      {bad.length > 0 && (
        <ul className="mt-1 list-inside list-disc">
          {bad.map((c, i) => (
            <li key={i}>
              {c.document_filename}
              {c.page !== null ? `, Page ${c.page}` : ""}
            </li>
          ))}
        </ul>
      )}
      {validation.warnings.length > 0 && (
        <ul className="mt-1 list-inside list-disc opacity-80">
          {validation.warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function TurnView({ turn }: { turn: Turn }) {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-zinc-900 px-4 py-2.5 text-sm text-white dark:bg-zinc-100 dark:text-zinc-900">
          {turn.question}
        </p>
      </div>

      <div className="space-y-3 rounded-2xl rounded-bl-md border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        {turn.normalizedQuery && turn.normalizedQuery !== turn.question && (
          <p className="text-xs text-zinc-500 dark:text-zinc-400">
            Searched for <span className="font-medium text-zinc-700 dark:text-zinc-300">{turn.normalizedQuery}</span>
          </p>
        )}

        {turn.answer && <AnswerText text={turn.answer} />}

        {turn.status && (
          <p className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-sky-500" aria-hidden />
            {turn.status}
          </p>
        )}

        {turn.abstention && (
          <p className="rounded-lg border border-zinc-200 bg-zinc-50 p-3 text-xs text-zinc-600 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400">
            Not answered: {turn.abstention}
          </p>
        )}

        {turn.error && (
          <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-200">
            {turn.error}
          </p>
        )}

        {turn.done && !turn.abstention && !turn.error && turn.validation && (
          <ValidationBadge validation={turn.validation} />
        )}

        {turn.sources.length > 0 && (
          <div>
            <button
              type="button"
              onClick={() => setShowSources((v) => !v)}
              className="text-xs font-medium text-zinc-600 underline underline-offset-2 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100"
            >
              {showSources ? "Hide" : "Show"} {turn.sources.length} sources
            </button>
            {showSources && (
              <div className="mt-3 space-y-2">
                {turn.sources.map((chunk, i) => (
                  <SourceCard key={chunk.chunk_id} chunk={chunk} position={i + 1} compact />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
