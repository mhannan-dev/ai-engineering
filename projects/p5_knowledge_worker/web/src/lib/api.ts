/**
 * Client for the P5 Knowledge Worker API (FastAPI, see ../api).
 * Errors from the API have the shape { error, message, details }.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function readMessage(response: Response): Promise<string | undefined> {
  if (!response.headers.get("content-type")?.includes("application/json")) {
    return undefined;
  }
  const body = (await response.json()) as { message?: string; detail?: unknown };
  return body.message ?? (typeof body.detail === "string" ? body.detail : undefined);
}

async function postJson(path: string, payload: unknown): Promise<string | undefined> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError("Can't reach the server. Check that the API is running.", 0);
  }

  const message = await readMessage(response);
  if (!response.ok) {
    throw new ApiError(message ?? `Request failed (${response.status}).`, response.status);
  }
  return message;
}

/** Ask the API to email a password reset link. Auth endpoints arrive in Phase 6. */
export async function requestPasswordReset(email: string): Promise<string> {
  try {
    const message = await postJson("/api/v1/auth/forgot-password", { email });
    return message ?? "If that email exists, a reset link has been sent.";
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      throw new ApiError("Password reset isn't available yet.", 404);
    }
    throw error;
  }
}
