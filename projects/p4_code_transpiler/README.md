# Project 4: High-Performance Code Transpiler (p4_code_transpiler)

Converts slow numerical Python into C++20 with an LLM, builds it with `g++ -O3 -fopenmp`, sends compiler errors back to the model until the code builds, then runs both programs and reports the speedup and whether their outputs match.

---

## 🏗️ Pipeline

```
[Next.js Workbench]  ──POST /api/v1/transpile──►  [FastAPI]
                                                     │
  1. Transpile   core/transpiler.py        LLM: Python → C++20 (+ OpenMP pragmas)
  2. Build       compiler/builder.py       g++ -std=c++20 -O3 -fopenmp
        │ fails?
        └─► 3. Self-correct  core/self_correction.py
               compiler stderr + failing C++ + original Python → LLM → rebuild
               (up to max_attempts rounds)
  4. Benchmark   benchmark/harness.py      run python.exe vs C++ binary, time both
  5. Verify      benchmark/metrics.py      speedup = python_ms / cpp_ms
                                           outputs_match = exact / numeric (1e-4) / line match
```

If the LLM can't be reached, the API returns **502** with a readable message. It never returns placeholder C++.

---

## 🌟 Features

| Feature | Where |
| :--- | :--- |
| Python → C++20 translation with HPC rules (contiguous memory, row-major loops, OpenMP `parallel for` / `reduction`) | [core/transpiler.py](core/transpiler.py) |
| Self-correction: compiler stderr is fed back to the model until the code builds | [core/self_correction.py](core/self_correction.py) |
| Build with selectable `-O0`…`-O3`, OpenMP on/off | [compiler/builder.py](compiler/builder.py) |
| Run with timeouts, stdout/stderr/exit-code capture | [compiler/runner.py](compiler/runner.py) |
| Speedup factor + output equivalence check (exact, numeric tolerance `1e-4`, timing lines ignored) | [benchmark/](benchmark/) |
| Web workbench: editor, C++ / Execution / Self-Correction / Benchmark tabs | [web/](web/) |

---

## 🛠️ Prerequisites

- Python 3.12+ and [uv](https://astral.sh/uv)
- Node.js 20+
- **g++ with C++20 and OpenMP**. On Windows, MinGW-w64 works (`scoop install mingw`). Check with `g++ --version`.
- An OpenAI-compatible API key (DeepSeek by default)

## ⚙️ Configuration

```powershell
cp .env.example .env
```

| Variable | Default | Meaning |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | — | LLM key |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | Any OpenAI-compatible endpoint |
| `LLM_MODEL` | `deepseek-chat` | Model used for both translation and repair |
| `CXX_COMPILER` | `g++` | Compiler binary |
| `EXECUTION_TIMEOUT_SECONDS` | `15` | Per-run timeout for Python and C++ |
| `ENABLE_OPENMP` | `true` | Global switch for `-fopenmp` |

The frontend reads `NEXT_PUBLIC_API_BASE_URL` from `web/.env.local` (default `http://localhost:8000`).

---

## 💻 How to Run

```powershell
cd projects/p4_code_transpiler

.\run.ps1 -Install    # uv sync (api/) + npm install (web/)
.\run.ps1             # backend :8000 + frontend :3000 in one terminal, Ctrl+C stops both
.\run.ps1 -Backend    # API only   → http://localhost:8000/docs
.\run.ps1 -Web        # UI only    → http://localhost:3000
.\run.ps1 -Stop       # free ports 8000 / 3000
```

### API

| Method | Path | Purpose |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness (polled by the UI header) |
| `GET` | `/api/v1/status` | Compiler and engine info |
| `GET` | `/api/v1/examples` | Sample programs from [examples/](examples/) |
| `POST` | `/api/v1/transpile` | Full pipeline (see the request/response contract in [web/README.md](web/README.md#api-contract)) |

```powershell
curl -X POST http://localhost:8000/api/v1/transpile -H "Content-Type: application/json" `
  -d '{"source": "print(sum(i*i for i in range(10_000_000)))", "optimization_level": "O3"}'
```

---

## 📊 Sample Results

Measured 2026-10-05 with `deepseek-chat`, MinGW g++ 16.1, Windows 11. Times include process startup.

| Example | Python | C++ | Speedup | Outputs match | Notes |
| :--- | ---: | ---: | ---: | :---: | :--- |
| [numerical_sim.py](examples/numerical_sim.py) (Monte Carlo π, 5M samples) | 2975 ms | 93 ms | **31.8×** | ❌ | Built on the 2nd attempt. The model parallelized the LCG with a skip-ahead that changes the random sequence, so π = 3.142454 instead of 3.142293. The equivalence check caught it. |
| [matrix_mul.py](examples/matrix_mul.py) (250×250 GEMM) | — | — | — | — | The LLM request timed out on this run. The API now returns 502 for this case (it used to return placeholder code). |

**Takeaway:** a big speedup alone means nothing. A result only counts when `outputs_match` is true. That's why the API always reports both.

---

## ⚠️ Limitations & Security

- **This runs arbitrary code.** The submitted Python and the generated C++ both run on the host with no sandbox. Use it only on your own machine and never expose port 8000 publicly. A container sandbox (no network, CPU and memory limits) is the next step before any shared deployment.
- Timing is wall-clock per process (startup included, single run). For short programs, startup and antivirus scans of new `.exe` files dominate.
- `storage/temp_py`, `storage/temp_cpp` and `storage/binaries` are never cleaned up automatically.
- CORS is `*` (local development only).

---

## 📂 Structure

```
p4_code_transpiler/
  api/main.py            FastAPI app, request/response schemas, endpoints
  core/                  transpiler, self-correction loop, code extraction
  compiler/              g++ builder, process runner
  benchmark/             harness (Python vs C++), metrics (speedup, equivalence)
  config/settings.py     pydantic-settings, storage paths
  examples/              sample numerical Python programs
  storage/               generated .py / .cpp / .exe (git-ignored)
  web/                   Next.js 16 workbench
  run.ps1                one-terminal runner
```
