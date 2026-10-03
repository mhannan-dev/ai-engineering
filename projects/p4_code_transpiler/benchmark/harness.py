"""
Benchmarking Harness
Runs both Python baseline and compiled C++ executable, comparing execution times and outputs.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from compiler.runner import run_executable, run_python_source
from benchmark.metrics import calculate_speedup, check_outputs_match


def run_benchmark_comparison(
    python_source: str,
    binary_path: Path,
    source_id: Optional[str] = None,
    timeout_seconds: int = 15,
) -> Dict[str, Any]:
    """
    Executes Python baseline and C++ binary under identical environment constraints.

    Returns:
        dict containing:
            python_ms: float
            cpp_ms: float
            speedup: float
            outputs_match: bool
            py_run: dict (stdout, stderr, exit_code, duration_ms)
            cpp_run: dict (stdout, stderr, exit_code, duration_ms)
    """
    # 1. Run Python baseline
    py_result = run_python_source(
        python_source=python_source,
        source_id=source_id,
        timeout_seconds=timeout_seconds,
    )

    # 2. Run compiled C++ executable
    cpp_result = run_executable(
        binary_path=binary_path,
        timeout_seconds=timeout_seconds,
    )

    py_ms = py_result.get("duration_ms", 0.0)
    cpp_ms = cpp_result.get("duration_ms", 0.0)

    # 3. Compute speedup
    speedup = calculate_speedup(py_ms, cpp_ms)

    # 4. Verify output equivalence
    outputs_match = check_outputs_match(
        py_stdout=py_result.get("stdout", ""),
        cpp_stdout=cpp_result.get("stdout", "")
    )

    return {
        "python_ms": py_ms,
        "cpp_ms": cpp_ms,
        "speedup": speedup,
        "outputs_match": outputs_match,
        "py_run": py_result,
        "cpp_run": cpp_result,
    }
