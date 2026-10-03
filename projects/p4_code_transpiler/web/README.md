# Py2Cpp Transpiler — Web

Next.js 16 frontend for the p4 Code Transpiler: paste Python, get optimized C++, see the self-correction loop and a Python vs C++ benchmark.

## Run

```bash
npm install
npm run dev        # http://localhost:3000
```

The backend URL comes from `.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The header shows **API online / offline** (it polls `GET /health` every 15 s). There is no mock mode: if the API is unreachable, the UI shows an error instead of fake results.

## Features

| UI | Backend module |
|---|---|
| Python editor with examples (Ctrl/Cmd+Enter to run) | `examples/` |
| C++ Output tab (copy, download `.cpp`) | `core/transpiler.py`, `core/optimizer.py` |
| Optimization level `-O0` … `-O3` | `compiler/builder.py` |
| Self-Correction tab (compile errors per attempt) | `core/self_correction.py` |
| Execution tab (stdout, stderr, exit code) | `compiler/runner.py` |
| Benchmark tab (speedup, outputs match) | `benchmark/harness.py`, `benchmark/metrics.py` |

## API contract

Defined in [`lib/api.ts`](lib/api.ts). The backend must implement:

**`GET /health`** → `200 { "status": "ok" }`

**`POST /api/v1/transpile`**

```json
{
  "source": "def main(): ...",
  "optimization_level": "O2",
  "self_correction": true,
  "max_attempts": 3,
  "run_benchmark": true
}
```

Response:

```json
{
  "cpp_code": "#include <iostream> ...",
  "compiled": true,
  "attempts": [{ "attempt": 1, "compiler_errors": "error: ...", "fixed": true }],
  "run": { "stdout": "...", "stderr": "", "exit_code": 0, "duration_ms": 12.4 },
  "benchmark": { "python_ms": 840.2, "cpp_ms": 9.1, "speedup": 92.3, "outputs_match": true }
}
```

- `attempts` is empty when the code compiled on the first try.
- `run` is `null` when the code did not compile; `benchmark` is `null` when `run_benchmark` is false.
- Errors return a non-2xx status with `{ "message": "..." }` (FastAPI's `{ "detail": "..." }` also works).
- CORS must allow `http://localhost:3000`.

## Structure

```
app/
  layout.tsx            header + footer
  page.tsx              transpiler workbench
  globals.css           design tokens, glass panels
components/
  site-header.tsx       logo + API status
  transpiler/
    code-editor.tsx     Python editor (line numbers, Tab indent)
    options-panel.tsx   optimization / self-correction / benchmark
    result-panel.tsx    C++, Execution, Self-Correction, Benchmark tabs
  ui/button.tsx
lib/
  api.ts                API client + types (the contract above)
  examples.ts           sample Python programs
```
