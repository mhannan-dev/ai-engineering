/**
 * Client for the p4 Code Transpiler API (FastAPI, see ../api).
 *
 * Contract the backend implements:
 *   GET  /health             -> { status: "ok", version }
 *   POST /api/v1/transpile   -> TranspileResult (body: TranspileRequest)
 * Errors use { error, message, details } (or FastAPI's { detail }).
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export type OptimizationLevel = 'O0' | 'O1' | 'O2' | 'O3';

export interface TranspileRequest {
  /** Python source to translate to C++ (core/transpiler.py). */
  source: string;
  /** Compiler optimization flag passed to the C++ build (compiler/builder.py). */
  optimization_level: OptimizationLevel;
  /** Let the LLM repair compile errors and retry (core/self_correction.py). */
  self_correction: boolean;
  /** Upper bound on compile/fix rounds when self_correction is on. */
  max_attempts: number;
  /** Time Python vs compiled C++ and compare outputs (benchmark/harness.py). */
  run_benchmark: boolean;
}

/** One compile round: the errors seen and whether the next round fixed them. */
export interface CorrectionAttempt {
  attempt: number;
  compiler_errors: string;
  fixed: boolean;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  duration_ms: number;
}

export interface BenchmarkResult {
  python_ms: number;
  cpp_ms: number;
  /** python_ms / cpp_ms */
  speedup: number;
  /** stdout of the Python and C++ programs were identical */
  outputs_match: boolean;
}

export interface TranspileResult {
  cpp_code: string;
  compiled: boolean;
  attempts: CorrectionAttempt[];
  run: RunResult | null;
  benchmark: BenchmarkResult | null;
}

async function readApiError(res: Response, fallback: string): Promise<string> {
  const err = await res.json().catch(() => null);
  return err?.message || (typeof err?.detail === 'string' ? err.detail : null) || fallback;
}

/** fetch() that turns network failures into a readable message (no silent mock fallback). */
async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  try {
    return await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    throw new Error(`Cannot reach the transpiler API at ${API_BASE_URL}. Is the backend running?`);
  }
}

export async function transpile(request: TranspileRequest, signal?: AbortSignal): Promise<TranspileResult> {
  const res = await apiFetch('/api/v1/transpile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  });
  if (!res.ok) throw new Error(await readApiError(res, `Transpilation failed (HTTP ${res.status}).`));
  return res.json();
}

/** True when the API answers its health check. */
export async function checkApiHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { signal });
    return res.ok;
  } catch {
    return false;
  }
}
