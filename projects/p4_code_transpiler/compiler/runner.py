"""
Executable Runner Subsystem
Executes Python and C++ binaries with high-resolution timing, timeouts, and output capture.
"""

import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from config.settings import settings


def run_executable(
    binary_path: Path,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes a compiled C++ binary and measures performance.

    Returns:
        dict containing stdout, stderr, exit_code, duration_ms
    """
    if timeout_seconds is None:
        timeout_seconds = settings.execution_timeout_seconds

    if not binary_path.exists():
        return {
            "stdout": "",
            "stderr": f"Executable not found at {binary_path}",
            "exit_code": -1,
            "duration_ms": 0.0,
        }

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [str(binary_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        duration_ms = (time.perf_counter() - start) * 1000.0

        return {
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "exit_code": proc.returncode,
            "duration_ms": round(duration_ms, 2),
        }
    except subprocess.TimeoutExpired:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return {
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_seconds}s",
            "exit_code": 124,
            "duration_ms": round(duration_ms, 2),
        }
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return {
            "stdout": "",
            "stderr": f"Execution error: {str(e)}",
            "exit_code": -1,
            "duration_ms": round(duration_ms, 2),
        }


def run_python_source(
    python_source: str,
    source_id: Optional[str] = None,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes Python source code in a standalone subprocess.

    Returns:
        dict containing stdout, stderr, exit_code, duration_ms
    """
    if timeout_seconds is None:
        timeout_seconds = settings.execution_timeout_seconds

    if not source_id:
        source_id = f"py_{uuid.uuid4().hex[:8]}"

    py_path = settings.temp_py_dir / f"{source_id}.py"
    py_path.write_text(python_source, encoding="utf-8")

    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, str(py_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            encoding="utf-8",
            errors="replace",
        )
        duration_ms = (time.perf_counter() - start) * 1000.0

        return {
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "exit_code": proc.returncode,
            "duration_ms": round(duration_ms, 2),
        }
    except subprocess.TimeoutExpired:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return {
            "stdout": "",
            "stderr": f"Python execution timed out after {timeout_seconds}s",
            "exit_code": 124,
            "duration_ms": round(duration_ms, 2),
        }
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000.0
        return {
            "stdout": "",
            "stderr": f"Python execution error: {str(e)}",
            "exit_code": -1,
            "duration_ms": round(duration_ms, 2),
        }
