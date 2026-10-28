/**
 * Client for the P5 Knowledge Worker API (FastAPI, see ../api).
 * Errors from the API have the shape { error, message, details }.
 */

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

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError("Can't reach the server. Check that the API is running.", 0);
  }

  const body = await readJson(response);
  if (!response.ok) {
    const err = (body ?? {}) as ErrorBody;
    const message =
      err.message ??
      (typeof err.detail === "string" ? err.detail : undefined) ??
      `Request failed (${response.status}).`;
    throw new ApiError(message, response.status, err.error, err.details ?? {});
  }
  return body as T;
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
// Auth (Phase 6)
// ---------------------------------------------------------------------------

/** Ask the API to email a password reset link. Auth endpoints arrive in Phase 6. */
export async function requestPasswordReset(email: string): Promise<string> {
  try {
    const body = await postJson<{ message?: string } | undefined>(
      `${API_V1}/auth/forgot-password`,
      { email },
    );
    return body?.message ?? "If that email exists, a reset link has been sent.";
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      throw new ApiError("Password reset isn't available yet.", 404);
    }
    throw error;
  }
}
