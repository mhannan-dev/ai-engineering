"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import {
  ApiError,
  deleteConversation,
  getConversation,
  listConversations,
  streamChat,
  type ChatEvent,
  type CitationValidation,
  type Conversation,
  type ConversationDetail,
  type SearchResultChunk,
} from "@/lib/api";

import { ChatSidebar } from "./chat-sidebar";

type Stage = "retrieving" | "generating" | "validating";

interface Turn {
  id: number;
  question: string;
  stage: Stage | null;
  normalizedQuery: string | null;
  sources: SearchResultChunk[];
  answer: string;
  abstention: string | null;
  validation: CitationValidation | null;
  error: string | null;
  done: boolean;
}

const SUGGESTIONS = [
  { title: "Annual leave", question: "How many days of annual leave do I get?" },
  { title: "দৈনিক ভাতা", question: "ঢাকার বাইরে জেলা সদরে গেলে দৈনিক ভাতা কত?" },
  { title: "Troubleshooting", question: "What does error code E-17 mean?" },
  { title: "Banglish", question: "probation koto mash?" },
];

const STAGES: { key: Stage; label: string }[] = [
  { key: "retrieving", label: "Searching" },
  { key: "generating", label: "Writing" },
  { key: "validating", label: "Checking citations" },
];

function applyEvent(turn: Turn, event: ChatEvent): Turn {
  switch (event.event) {
    case "status":
      return { ...turn, stage: event.data.stage as Stage };
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
        stage: null,
        done: true,
      };
    case "error":
      return { ...turn, error: event.data.error, stage: null, done: true };
    case "conversation":
      return turn; // handled by the workspace, which tracks the active conversation
  }
}

/** Rebuild finished turns from a saved conversation (user message, then its answer). */
function turnsFrom(detail: ConversationDetail): Turn[] {
  const turns: Turn[] = [];
  detail.messages.forEach((message, i) => {
    if (message.role !== "user") return;
    const next = detail.messages[i + 1];
    const answer = next?.role === "assistant" ? next : undefined;
    turns.push({
      id: -(i + 1), // stored turns get negative ids so they never clash with new Date.now() ids
      question: message.content,
      stage: null,
      normalizedQuery: null,
      sources: answer?.sources ?? [],
      answer: answer?.content ?? "",
      abstention: answer?.is_abstention ? "No passage was relevant enough to answer from." : null,
      validation: answer?.validation ?? null,
      error: null,
      done: true,
    });
  });
  return turns;
}

export function ChatWorkspace() {
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [running, setRunning] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  // State is set only in the promise callbacks, so the mount effect can call this safely.
  const refreshHistory = useCallback(
    () =>
      listConversations().then(
        (page) => {
          setConversations(page.items);
          setHistoryError(null);
          setHistoryLoading(false);
        },
        (err: unknown) => {
          setHistoryError(err instanceof ApiError ? err.message : "Couldn't load history.");
          setHistoryLoading(false);
        },
      ),
    [],
  );

  useEffect(() => {
    void refreshHistory();
  }, [refreshHistory]);

  function newChat() {
    abortRef.current?.abort();
    setTurns([]);
    setActiveId(null);
    setDrawerOpen(false);
    inputRef.current?.focus();
  }

  async function openConversation(id: string) {
    if (id === activeId) {
      setDrawerOpen(false);
      return;
    }
    abortRef.current?.abort();
    setOpening(true);
    setDrawerOpen(false);
    try {
      const detail = await getConversation(id);
      setTurns(turnsFrom(detail));
      setActiveId(id);
    } catch (err) {
      setHistoryError(err instanceof ApiError ? err.message : "Couldn't open that conversation.");
      void refreshHistory();
    } finally {
      setOpening(false);
    }
  }

  async function removeConversation(conversation: Conversation) {
    if (!window.confirm(`Delete "${conversation.title}"?`)) return;
    try {
      await deleteConversation(conversation.id);
      if (conversation.id === activeId) newChat();
    } catch (err) {
      setHistoryError(err instanceof ApiError ? err.message : "Couldn't delete that conversation.");
    }
    void refreshHistory();
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns]);

  function update(id: number, change: (turn: Turn) => Turn) {
    setTurns((prev) => prev.map((turn) => (turn.id === id ? change(turn) : turn)));
  }

  function resizeInput() {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed || running) return;

    const id = Date.now();
    setTurns((prev) => [
      ...prev,
      {
        id,
        question: trimmed,
        stage: "retrieving",
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
    requestAnimationFrame(resizeInput);
    setRunning(true);

    const controller = new AbortController();
    abortRef.current = controller;
    try {
      await streamChat(
        { query: trimmed, top_k: 5, conversation_id: activeId },
        (evt) => {
          if (evt.event === "conversation") {
            // The turn is saved: follow-ups now continue this conversation.
            setActiveId(evt.data.id);
            void refreshHistory();
          }
          update(id, (turn) => applyEvent(turn, evt));
        },
        controller.signal,
      );
      update(id, (turn) => (turn.done ? turn : { ...turn, stage: null, done: true }));
    } catch (err) {
      const message =
        err instanceof DOMException && err.name === "AbortError"
          ? "Stopped."
          : err instanceof ApiError
            ? err.message
            : "Something went wrong while answering.";
      update(id, (turn) => ({ ...turn, error: message, stage: null, done: true }));
    } finally {
      abortRef.current = null;
      setRunning(false);
      inputRef.current?.focus();
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void ask(question);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter adds a line; ignore Enter while an IME is composing Bangla.
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void ask(question);
    }
  }

  const sidebar = (
    <ChatSidebar
      conversations={conversations}
      loading={historyLoading}
      error={historyError}
      activeId={activeId}
      busy={opening}
      onNew={newChat}
      onSelect={(id) => void openConversation(id)}
      onDelete={(c) => void removeConversation(c)}
    />
  );

  return (
    <div className="flex flex-1">
      {/* Desktop: a fixed column below the app header. */}
      <aside className="hidden w-72 shrink-0 border-r border-zinc-200 bg-zinc-50/60 lg:sticky lg:top-14 lg:block lg:h-[calc(100dvh-3.5rem)] dark:border-zinc-800 dark:bg-zinc-950/60">
        {sidebar}
      </aside>

      {/* Mobile: a drawer. */}
      {drawerOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Chat history">
          <button
            type="button"
            aria-label="Close history"
            onClick={() => setDrawerOpen(false)}
            className="absolute inset-0 bg-zinc-950/40 backdrop-blur-sm animate-[fade-in_150ms_ease-out]"
          />
          <aside className="relative h-full w-72 max-w-[85%] border-r border-zinc-200 bg-zinc-50 shadow-2xl dark:border-zinc-800 dark:bg-zinc-950">
            {sidebar}
          </aside>
        </div>
      )}

      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 pt-4 sm:px-6">
        <div className="mb-2 flex items-center gap-2 lg:hidden">
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
          >
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
              <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h10" />
            </svg>
            History
          </button>
          {turns.length > 0 && (
            <button
              type="button"
              onClick={newChat}
              className="ml-auto rounded-lg px-2.5 py-1.5 text-sm font-medium text-zinc-600 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
            >
              New chat
            </button>
          )}
        </div>

        <div className="flex-1">
          {opening ? (
            <div className="flex justify-center py-24" aria-busy="true">
              <span className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-zinc-100" />
            </div>
          ) : turns.length === 0 ? (
            <EmptyState onPick={(q) => void ask(q)} />
          ) : (
            <div className="space-y-10 pb-8 pt-2">
              {turns.map((turn) => (
                <TurnView key={turn.id} turn={turn} />
              ))}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="sticky bottom-0 -mx-4 bg-linear-to-t from-zinc-50 via-zinc-50 to-transparent px-4 pb-5 pt-6 sm:-mx-6 sm:px-6 dark:from-black dark:via-black">
          <form
            onSubmit={onSubmit}
            className="group relative flex items-end gap-2 rounded-3xl border border-zinc-200 bg-white p-2 pl-5 shadow-[0_8px_30px_rgb(0,0,0,0.06)] transition-all focus-within:border-zinc-300 focus-within:shadow-[0_8px_30px_rgb(0,0,0,0.10)] dark:border-zinc-800 dark:bg-zinc-900 dark:shadow-none dark:focus-within:border-zinc-700"
          >
            <label htmlFor="chat-question" className="sr-only">
              Ask a question
            </label>
            <textarea
              ref={inputRef}
              id="chat-question"
              rows={1}
              value={question}
              onChange={(event) => {
                setQuestion(event.target.value);
                resizeInput();
              }}
              onKeyDown={onKeyDown}
              placeholder="Ask anything about your documents…"
              maxLength={1000}
              className="max-h-50 min-h-11 flex-1 resize-none bg-transparent py-3 text-[15px] leading-6 text-zinc-900 outline-none placeholder:text-zinc-400 dark:text-zinc-100 dark:placeholder:text-zinc-500"
            />
            {running ? (
              <button
                id="chat-stop"
                type="button"
                onClick={() => abortRef.current?.abort()}
                aria-label="Stop generating"
                title="Stop"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-zinc-900 text-white transition-transform hover:scale-105 dark:bg-zinc-100 dark:text-zinc-900"
              >
                <span className="h-3 w-3 rounded-[3px] bg-current" aria-hidden />
              </button>
            ) : (
              <button
                id="chat-submit"
                type="submit"
                disabled={!question.trim()}
                aria-label="Send"
                title="Send (Enter)"
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-linear-to-br from-indigo-500 to-violet-600 text-white shadow-md shadow-indigo-500/25 transition-all hover:scale-105 hover:shadow-lg hover:shadow-indigo-500/30 disabled:scale-100 disabled:from-zinc-200 disabled:to-zinc-200 disabled:text-zinc-400 disabled:shadow-none dark:disabled:from-zinc-800 dark:disabled:to-zinc-800 dark:disabled:text-zinc-600"
              >
                <svg className="h-4.5 w-4.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m0 0-6 6m6-6 6 6" />
                </svg>
              </button>
            )}
          </form>
          <p className="mt-2.5 text-center text-[11px] text-zinc-400 dark:text-zinc-500">
            Answers come only from your indexed documents, with citations checked against the sources.
            <span className="hidden sm:inline"> Shift + Enter for a new line.</span>
          </p>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onPick }: { onPick: (question: string) => void }) {
  return (
    <div className="flex flex-col items-center px-2 pb-10 pt-10 text-center sm:pt-16">
      <div className="relative">
        <div className="absolute inset-0 rounded-2xl bg-linear-to-br from-indigo-500 to-violet-600 opacity-40 blur-xl" aria-hidden />
        <div className="relative flex h-14 w-14 items-center justify-center rounded-2xl bg-linear-to-br from-indigo-500 to-violet-600 text-white shadow-lg">
          <SparkIcon className="h-7 w-7" />
        </div>
      </div>
      <h1 className="mt-6 text-3xl font-semibold tracking-tight text-zinc-900 sm:text-4xl dark:text-zinc-50">
        Ask your documents
      </h1>
      <p className="mt-3 max-w-md text-[15px] leading-relaxed text-zinc-500 dark:text-zinc-400">
        Grounded answers in English, বাংলা or Banglish. Every claim points to the file and page it
        came from.
      </p>

      <div className="mt-10 grid w-full max-w-2xl gap-3 sm:grid-cols-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s.question}
            type="button"
            onClick={() => onPick(s.question)}
            className="group rounded-2xl border border-zinc-200 bg-white p-4 text-left transition-all hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-[0_8px_30px_rgb(0,0,0,0.06)] dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-indigo-500/40"
          >
            <p className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">
              {s.title}
            </p>
            <p className="mt-1.5 flex items-start justify-between gap-3 text-sm leading-snug text-zinc-700 dark:text-zinc-300">
              <span>{s.question}</span>
              <span className="text-zinc-300 transition-all group-hover:translate-x-0.5 group-hover:text-indigo-500 dark:text-zinc-600" aria-hidden>
                →
              </span>
            </p>
          </button>
        ))}
      </div>
    </div>
  );
}

function SparkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M12 3v3m0 12v3M3 12h3m12 0h3M7.5 7.5 9 9m6 6 1.5 1.5m0-9L15 9m-6 6-1.5 1.5M12 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5Z"
      />
    </svg>
  );
}

const CITATION = /(\[[^\]\n]+\])/g;
const IS_CITATION = /^\[[^\]\n]+\]$/;

/** Renders the answer with bracketed citations like [handbook.md, Page 2] as compact chips. */
function AnswerText({ text, streaming }: { text: string; streaming: boolean }) {
  const parts = text.split(CITATION);
  return (
    <div className="whitespace-pre-wrap text-[15px] leading-7 text-zinc-800 dark:text-zinc-200">
      {parts.map((part, i) =>
        IS_CITATION.test(part) ? (
          <CitationChip key={i} label={part.slice(1, -1)} />
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
      {streaming && (
        <span className="ml-0.5 inline-block h-[1.1em] w-0.5 translate-y-0.75 animate-pulse rounded-full bg-indigo-500" aria-hidden />
      )}
    </div>
  );
}

function CitationChip({ label }: { label: string }) {
  const [file, ...rest] = label.split(",");
  return (
    <span
      title={label}
      className="mx-0.5 inline-flex max-w-[16rem] -translate-y-px items-center gap-1 rounded-md border border-indigo-100 bg-indigo-50/70 px-1.5 py-px align-middle text-[11px] font-medium leading-5 text-indigo-700 dark:border-indigo-500/20 dark:bg-indigo-500/10 dark:text-indigo-300"
    >
      <svg className="h-3 w-3 shrink-0 opacity-70" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Zm0 0v5h5" />
      </svg>
      <span className="truncate">{file.trim()}</span>
      {rest.length > 0 && <span className="shrink-0 opacity-70">· {rest.join(",").trim()}</span>}
    </span>
  );
}

function StageProgress({ stage }: { stage: Stage }) {
  const current = STAGES.findIndex((s) => s.key === stage);
  return (
    <ol className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs" aria-live="polite">
      {STAGES.map((s, i) => {
        const state = i < current ? "done" : i === current ? "active" : "todo";
        return (
          <li key={s.key} className="flex items-center gap-2">
            {i > 0 && <span className="h-px w-4 bg-zinc-200 dark:bg-zinc-700" aria-hidden />}
            <span
              className={`flex items-center gap-1.5 ${
                state === "active"
                  ? "font-medium text-zinc-900 dark:text-zinc-100"
                  : state === "done"
                    ? "text-zinc-500 dark:text-zinc-400"
                    : "text-zinc-300 dark:text-zinc-600"
              }`}
            >
              {state === "done" ? (
                <svg className="h-3.5 w-3.5 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m5 12 5 5L20 7" />
                </svg>
              ) : state === "active" ? (
                <span className="relative flex h-2 w-2" aria-hidden>
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-indigo-500" />
                </span>
              ) : (
                <span className="h-2 w-2 rounded-full bg-zinc-200 dark:bg-zinc-700" aria-hidden />
              )}
              {s.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function ValidationPill({ validation }: { validation: CitationValidation }) {
  const flagged = [...(validation.hallucinated_citations ?? []), ...(validation.unmatched_pages ?? [])];
  const detail = [
    ...flagged.map((c) => `${c.document_filename}${c.page !== null ? `, Page ${c.page}` : ""}`),
    ...validation.warnings,
  ].join("\n");

  return validation.is_valid ? (
    <Pill tone="good" title="Every citation matches a retrieved passage">
      <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
      </svg>
      Citations verified
    </Pill>
  ) : (
    <Pill tone="warn" title={detail || "Some citations don't match the retrieved passages"}>
      <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
      </svg>
      {flagged.length > 0 ? `${flagged.length} citation${flagged.length > 1 ? "s" : ""} unverified` : "Check citations"}
    </Pill>
  );
}

function Pill({ tone, title, children }: { tone: "good" | "warn"; title: string; children: ReactNode }) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        tone === "good"
          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
          : "bg-amber-50 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300"
      }`}
    >
      {children}
    </span>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
    >
      <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
        {copied ? (
          <path strokeLinecap="round" strokeLinejoin="round" d="m5 12 5 5L20 7" />
        ) : (
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 8V5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-3M5 8h9a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-9a2 2 0 0 1 2-2Z" />
        )}
      </svg>
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

const FORMAT_BADGE: Record<string, string> = {
  pdf: "bg-rose-100 text-rose-700 dark:bg-rose-500/15 dark:text-rose-300",
  docx: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
  md: "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300",
  html: "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
};

function SourceCard({ chunk, index }: { chunk: SearchResultChunk; index: number }) {
  const ext = chunk.document_filename.split(".").pop()?.toLowerCase() ?? "";
  return (
    <article className="flex min-w-0 flex-col rounded-xl border border-zinc-200 bg-white p-3.5 transition-colors hover:border-zinc-300 dark:border-zinc-800 dark:bg-zinc-900 dark:hover:border-zinc-700">
      <div className="flex items-center gap-2">
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-[10px] font-semibold text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
          {index}
        </span>
        <span
          className={`shrink-0 rounded px-1.5 py-px font-mono text-[10px] font-semibold uppercase ${
            FORMAT_BADGE[ext] ?? "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300"
          }`}
        >
          {ext || "doc"}
        </span>
        <span className="truncate text-xs font-medium text-zinc-800 dark:text-zinc-200" title={chunk.document_filename}>
          {chunk.document_filename}
        </span>
        {chunk.page !== null && (
          <span className="ml-auto shrink-0 text-[11px] text-zinc-400">p. {chunk.page}</span>
        )}
      </div>
      {chunk.heading && (
        <p className="mt-2 truncate text-xs font-medium text-zinc-500 dark:text-zinc-400" title={chunk.heading}>
          {chunk.heading}
        </p>
      )}
      <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-zinc-600 dark:text-zinc-400">{chunk.text}</p>
    </article>
  );
}

function TurnView({ turn }: { turn: Turn }) {
  const [showSources, setShowSources] = useState(false);
  const streaming = !turn.done && turn.stage === "generating";
  const finished = turn.done && !turn.error;

  return (
    <div className="space-y-5">
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-3xl rounded-br-lg bg-zinc-900 px-5 py-3 text-[15px] leading-6 text-white shadow-sm dark:bg-zinc-100 dark:text-zinc-900">
          {turn.question}
        </p>
      </div>

      <div className="flex gap-3 sm:gap-4">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-linear-to-br from-indigo-500 to-violet-600 text-white shadow-sm shadow-indigo-500/20" aria-hidden>
          <SparkIcon className="h-4 w-4" />
        </div>

        <div className="min-w-0 flex-1 space-y-4">
          {turn.stage && <StageProgress stage={turn.stage} />}

          {turn.normalizedQuery && turn.normalizedQuery !== turn.question && (
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Searched for{" "}
              <span className="rounded-md bg-zinc-100 px-1.5 py-0.5 font-medium text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                {turn.normalizedQuery}
              </span>
            </p>
          )}

          {turn.abstention ? (
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-[15px] font-medium text-zinc-900 dark:text-zinc-100">
                I couldn&apos;t find this in your documents.
              </p>
              <p className="mt-1 text-sm leading-relaxed text-zinc-500 dark:text-zinc-400">
                Rather than guess, the assistant only answers when a passage is relevant enough.{" "}
                {turn.abstention}
              </p>
            </div>
          ) : (
            turn.answer && <AnswerText text={turn.answer} streaming={streaming} />
          )}

          {turn.error && (
            <div role="alert" className="flex items-start gap-2.5 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200">
              <svg className="mt-0.5 h-4 w-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
              </svg>
              {turn.error}
            </div>
          )}

          {(finished || turn.sources.length > 0) && (
            <div className="flex flex-wrap items-center gap-1.5">
              {finished && !turn.abstention && turn.validation && <ValidationPill validation={turn.validation} />}
              {turn.sources.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowSources((v) => !v)}
                  aria-expanded={showSources}
                  className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium text-zinc-500 transition-colors hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100"
                >
                  <svg className={`h-3.5 w-3.5 transition-transform ${showSources ? "rotate-90" : ""}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m9 6 6 6-6 6" />
                  </svg>
                  {turn.sources.length} source{turn.sources.length > 1 ? "s" : ""}
                </button>
              )}
              {finished && !turn.abstention && turn.answer && <CopyButton text={turn.answer} />}
            </div>
          )}

          {showSources && (
            <div className="grid gap-2 sm:grid-cols-2">
              {turn.sources.map((chunk, i) => (
                <SourceCard key={chunk.chunk_id} chunk={chunk} index={i + 1} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
