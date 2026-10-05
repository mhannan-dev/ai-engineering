import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal, Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config.settings import settings
from compiler.runner import run_executable
from benchmark.harness import run_benchmark_comparison
from core.self_correction import transpile_with_feedback_loop
from core.transpiler import TranspilerUnavailableError

# ==============================================================================
# Pydantic Schemas (Aligned with web/lib/api.ts contract)
# ==============================================================================

OptimizationLevel = Literal["O0", "O1", "O2", "O3"]


class TranspileRequest(BaseModel):
    """Payload received from frontend web editor."""
    source: str = Field(..., description="Python source code to translate to C++20.")
    optimization_level: OptimizationLevel = Field(
        default="O3",
        description="Compiler optimization flag (-O0, -O1, -O2, -O3)."
    )
    self_correction: bool = Field(
        default=True,
        description="Enable compiler feedback and auto-debugging retry loop."
    )
    max_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum compile/fix attempts when self-correction is enabled."
    )
    run_benchmark: bool = Field(
        default=True,
        description="Benchmark execution time between Python baseline and C++ binary."
    )


class CorrectionAttempt(BaseModel):
    """Record of a single compile / fix iteration."""
    attempt: int
    compiler_errors: str = ""
    fixed: bool = True


class RunResult(BaseModel):
    """Output metrics from running the compiled C++ executable."""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0


class BenchmarkResult(BaseModel):
    """Execution timing and speedup comparison."""
    python_ms: float
    cpp_ms: float
    speedup: float
    outputs_match: bool


class TranspileResult(BaseModel):
    """Final result payload sent back to frontend."""
    cpp_code: str
    compiled: bool = True
    attempts: List[CorrectionAttempt] = []
    run: Optional[RunResult] = None
    benchmark: Optional[BenchmarkResult] = None


# ==============================================================================
# FastAPI Application Factory
# ==============================================================================

app = FastAPI(
    title="High-Performance Code Transpiler API",
    description="Transforms unoptimized numerical Python code into high-performance C++20 with OpenMP & SIMD.",
    version="0.1.0",
)

# Enable CORS for Next.js web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# Health & Status Endpoints
# ==============================================================================

@app.get("/")
def read_root():
    """Root endpoint returning API status and metadata."""
    return {
        "project": "p4_code_transpiler",
        "service": "High-Performance Code Transpiler API",
        "status": "online",
        "version": "0.1.0",
        "docs_url": "/docs",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
@app.get("/api/health")
def health_check():
    """Health check endpoint queried by frontend (web/lib/api.ts checkApiHealth)."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/v1/status")
def get_status():
    """Transpiler engine capabilities and runtime status."""
    return {
        "transpiler": "Python 3.12 -> C++20",
        "compiler": settings.cxx_compiler,
        "supported_optimizations": ["OpenMP", "SIMD", "g++ -O3"],
        "self_correction": "Compiler Feedback Loop Enabled",
        "status": "ready",
    }


@app.get("/api/v1/examples")
def list_examples():
    """Returns available sample Python numerical algorithms."""
    examples_dir = settings.project_root / "examples"
    res = {}
    if examples_dir.exists():
        for file in examples_dir.glob("*.py"):
            try:
                res[file.stem] = file.read_text(encoding="utf-8")
            except Exception:
                pass
    return res


# ==============================================================================
# Core Transpiler Endpoint
# ==============================================================================

@app.post("/api/v1/transpile", response_model=TranspileResult)
async def transpile_code(payload: TranspileRequest):
    """
    Full pipeline:
    1. Transpile Python to C++20 via LLM.
    2. Build with g++ (with self-correction feedback loop if syntax errors occur).
    3. Run benchmark comparing Python baseline vs compiled C++20 binary.
    """
    if not payload.source.strip():
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")

    try:
        # Step 1 & 2: Transpile and compile with iterative self-correction
        cpp_code, compiled, raw_attempts, binary_path = await transpile_with_feedback_loop(
            source_code=payload.source,
            optimization_level=payload.optimization_level,
            self_correction=payload.self_correction,
            max_attempts=payload.max_attempts,
            enable_openmp=settings.enable_openmp,
        )

        attempts = [CorrectionAttempt(**att) for att in raw_attempts]

        # Step 3: Execution and Benchmarking
        run_info: Optional[RunResult] = None
        bench_info: Optional[BenchmarkResult] = None

        if compiled and binary_path and binary_path.exists():
            if payload.run_benchmark:
                bench_data = run_benchmark_comparison(
                    python_source=payload.source,
                    binary_path=binary_path,
                    timeout_seconds=settings.execution_timeout_seconds,
                )
                run_info = RunResult(**bench_data["cpp_run"])
                bench_info = BenchmarkResult(
                    python_ms=bench_data["python_ms"],
                    cpp_ms=bench_data["cpp_ms"],
                    speedup=bench_data["speedup"],
                    outputs_match=bench_data["outputs_match"],
                )
            else:
                raw_run = run_executable(
                    binary_path=binary_path,
                    timeout_seconds=settings.execution_timeout_seconds,
                )
                run_info = RunResult(**raw_run)
        else:
            # Compilation failed even after attempts
            last_err = attempts[-1].compiler_errors if attempts else "Compilation failed"
            run_info = RunResult(
                stdout="",
                stderr=last_err,
                exit_code=1,
                duration_ms=0.0,
            )

        return TranspileResult(
            cpp_code=cpp_code,
            compiled=compiled,
            attempts=attempts,
            run=run_info,
            benchmark=bench_info,
        )

    except TranspilerUnavailableError as e:
        raise HTTPException(
            status_code=502,
            detail=f"The LLM provider did not respond, so no C++ was generated. Try again. ({e})",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transpilation pipeline error: {str(e)}")
