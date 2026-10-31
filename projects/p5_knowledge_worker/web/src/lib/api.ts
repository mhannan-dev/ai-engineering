/**
 * Client for the P5 Knowledge Worker API (FastAPI, see ../api).
 * Errors from the API have the shape { error, message, details }.
 */

import { clearSession, getToken } from "@/lib/session";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const API_V1 = "/api/v1";

// ---------------------------------------------------------------------------
// Types (mirror api/src/knowledge_worker/schemas/document.py)
// ---------------------------------------------------------------------------

export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface DocumentOut {
  id: string;
  filename: string;
  format: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  language: string | null;
  section_count: number;
  chunk_count: number;
  created_at: string;
  indexed_at: string | null;
}

export interface ChunkOut {
  id: string;
  ordinal: number;
  page: number | null;
  heading: string | null;
  language: string;
  token_count: number;
  text: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type DocumentPage = Page<DocumentOut>;
export type ChunkPage = Page<ChunkOut>;

export interface HealthResponse {
  status: "ok";
  version: string;
}

// Mirror api/src/knowledge_worker/schemas/search.py

export interface SearchResultChunk {
  chunk_id: string;
  document_id: string;
  document_filename: string;
  page: number | null;
  heading: string | null;
  text: string;
  score: number;
  dense_rank: number | null;
  sparse_rank: number | null;
  fused_rank: number | null;
  rerank_rank: number | null;
}

export interface SearchRequest {
  query: string;
  limit?: number;
  rerank?: boolean;
  threshold?: number | null;
}

export interface SearchResponse {
  query: string;
  normalized_query: string;
  was_banglish: boolean;
  is_abstention: boolean;
  reranked: boolean;
  total: number;
  results: SearchResultChunk[];
}

export interface SearchDebugResponse {
  query: string;
  normalized_query: string;
  was_banglish: boolean;
  dense_hits: SearchResultChunk[];
  sparse_hits: SearchResultChunk[];
  fused_hits: SearchResultChunk[];
  reranked_hits: SearchResultChunk[];
}

// Mirror api/src/knowledge_worker/schemas/generation.py

export interface Citation {
  document_filename: string;
  page: number | null;
  heading: string | null;
  chunk_id: string | null;
  quoted_text: string | null;
}

export interface CitationValidation {
  is_valid: boolean;
  valid_citations?: Citation[];
  hallucinated_citations?: Citation[];
  unmatched_pages?: Citation[];
  warnings: string[];
}

export interface ChatRequest {
  query: string;
  top_k?: number;
  threshold?: number | null;
  temperature?: number | null;
  /** Continue a saved conversation; omit to start a new one. */
  conversation_id?: string | null;
}

// Mirror api/src/knowledge_worker/schemas/conversation.py

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export type ConversationPage = Page<Conversation>;

export interface StoredMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: Citation[] | null;
  sources: SearchResultChunk[] | null;
  validation: CitationValidation | null;
  is_abstention: boolean;
  created_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: StoredMessage[];
}

/** Events sent by POST /chat/stream (see generation/generator.py stream_events). */
export type ChatEvent =
  | { event: "status"; data: { stage: string; message: string } }
  | {
      event: "sources";
      data: {
        query: string;
        normalized_query: string;
        was_banglish: boolean;
        sources: SearchResultChunk[];
      };
    }
  | { event: "abstention"; data: { reason: string; answer: string } }
  /** Sent just before `done` once the turn is saved. */
  | { event: "conversation"; data: { id: string; title: string } }
  | { event: "token"; data: { token: string } }
  | { event: "validation"; data: CitationValidation }
  | {
      event: "done";
      data: {
        answer: string;
        citations: Citation[];
        is_abstention: boolean;
        abstention_reason?: string | null;
        validation: CitationValidation;
      };
    }
  | { event: "error"; data: { error: string } };

// ---------------------------------------------------------------------------
// Transport
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
    readonly details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ErrorBody {
  error?: string;
  message?: string;
  detail?: unknown;
  details?: Record<string, unknown>;
}

async function readJson(response: Response): Promise<unknown> {
  if (!response.headers.get("content-type")?.includes("application/json")) {
    return undefined;
  }
  try {
    return await response.json();
  } catch {
    return undefined;
  }
}

async function send(path: string, init: RequestInit): Promise<Response> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", ...init, headers });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError("Can't reach the server. Check that the API is running.", 0);
  }
  // A rejected token means the session is over: drop it so the app shows sign-in again.
  if (response.status === 401 && token) clearSession();
  if (!response.ok) {
    const err = ((await readJson(response)) ?? {}) as ErrorBody;
    const message =
      err.message ??
      (typeof err.detail === "string" ? err.detail : undefined) ??
      `Request failed (${response.status}).`;
    throw new ApiError(message, response.status, err.error, err.details ?? {});
  }
  return response;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await send(path, init);
  return (await readJson(response)) as T;
}

function postJson<T>(path: string, payload: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function query(params: Record<string, number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>(`${API_V1}/health`);
}

// ---------------------------------------------------------------------------
// Documents
// ---------------------------------------------------------------------------

export const SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".md", ".markdown", ".txt", ".html", ".htm"];

/** Upload a file. The API returns 202 with status "pending"; poll getDocument for progress. */
export function uploadDocument(file: File): Promise<DocumentOut> {
  const form = new FormData();
  form.append("file", file);
  // No Content-Type header: the browser sets the multipart boundary.
  return request<DocumentOut>(`${API_V1}/documents`, { method: "POST", body: form });
}

export function listDocuments(limit = 50, offset = 0): Promise<DocumentPage> {
  return request<DocumentPage>(`${API_V1}/documents${query({ limit, offset })}`);
}

export function getDocument(id: string): Promise<DocumentOut> {
  return request<DocumentOut>(`${API_V1}/documents/${encodeURIComponent(id)}`);
}

export function listChunks(id: string, limit = 50, offset = 0): Promise<ChunkPage> {
  return request<ChunkPage>(
    `${API_V1}/documents/${encodeURIComponent(id)}/chunks${query({ limit, offset })}`,
  );
}

export function reindexDocument(id: string): Promise<DocumentOut> {
  return request<DocumentOut>(`${API_V1}/documents/${encodeURIComponent(id)}/reindex`, {
    method: "POST",
  });
}

export async function deleteDocument(id: string): Promise<void> {
  await request<undefined>(`${API_V1}/documents/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// Search
// ---------------------------------------------------------------------------

export function searchDocuments(payload: SearchRequest): Promise<SearchResponse> {
  return postJson<SearchResponse>(`${API_V1}/search`, payload);
}

/** Dense, BM25, RRF and reranked lists side by side, for comparing retrievers. */
export function searchDebug(query: string, limit = 10): Promise<SearchDebugResponse> {
  const params = new URLSearchParams({ query, limit: String(limit) });
  return request<SearchDebugResponse>(`${API_V1}/search/debug?${params}`);
}

// ---------------------------------------------------------------------------
// Chat (Server-Sent Events)
// ---------------------------------------------------------------------------

function parseSseBlock(block: string): ChatEvent | null {
  let event = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  if (data.length === 0) return null;
  try {
    return { event, data: JSON.parse(data.join("\n")) } as ChatEvent;
  } catch {
    return null;
  }
}

/**
 * Ask a question and receive the answer as it is generated. Uses fetch rather than
 * EventSource so the request can be a POST with a JSON body and can be aborted.
 */
export async function streamChat(
  payload: ChatRequest,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await send(`${API_V1}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.body) throw new ApiError("The server sent an empty response.", response.status);

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value.replace(/\r\n/g, "\n");
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const event = parseSseBlock(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      if (event) onEvent(event);
      boundary = buffer.indexOf("\n\n");
    }
  }
  const last = parseSseBlock(buffer);
  if (last) onEvent(last);
}

// ---------------------------------------------------------------------------
// Conversations (saved chat history)
// ---------------------------------------------------------------------------

export function listConversations(limit = 50, offset = 0): Promise<ConversationPage> {
  return request<ConversationPage>(`${API_V1}/chat/conversations${query({ limit, offset })}`);
}

export function getConversation(id: string): Promise<ConversationDetail> {
  return request<ConversationDetail>(`${API_V1}/chat/conversations/${encodeURIComponent(id)}`);
}

export async function deleteConversation(id: string): Promise<void> {
  await request<undefined>(`${API_V1}/chat/conversations/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

// ---------------------------------------------------------------------------
// Auth (Phase 6)
// ---------------------------------------------------------------------------

// Mirror api/src/knowledge_worker/schemas/auth.py

export interface User {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in_minutes: number;
  user: User;
}

/** Whether sign-in and local demo login are enabled. */
export interface AuthConfig {
  enabled: boolean;
  demo_login_enabled: boolean;
}

export async function getAuthConfig(): Promise<AuthConfig> {
  return request<AuthConfig>(`${API_V1}/auth/config`);
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return postJson<TokenResponse>(`${API_V1}/auth/login`, { email, password });
}

export function demoLogin(): Promise<TokenResponse> {
  return postJson<TokenResponse>(`${API_V1}/auth/demo`, {});
}

export function register(name: string, email: string, password: string): Promise<TokenResponse> {
  return postJson<TokenResponse>(`${API_V1}/auth/register`, { name, email, password });
}

export function getMe(): Promise<User> {
  return request<User>(`${API_V1}/auth/me`);
}
